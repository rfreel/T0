from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATES = {"DRAFT", "COMMITTED", "OBSERVING", "ASSESSED", "CLOSED", "ABORTED"}
OPEN_STATES = {"COMMITTED", "OBSERVING"}
REQUIRED_SPEC = (
    "title", "situation", "decision", "baseline", "intervention", "authority",
    "resources", "horizon", "prediction", "rival_prediction",
    "success_criterion", "rollback",
)
REQUIRED_ASSESSMENT = (
    "actual_observation", "verdict", "unintended_effects", "actual_cost",
    "delay", "causal_confidence", "transferred", "failed",
)
VERDICTS = {"SUCCESS", "PARTIAL", "FAILURE", "INCONCLUSIVE"}

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS episodes (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  state TEXT NOT NULL CHECK(state IN ('DRAFT','COMMITTED','OBSERVING','ASSESSED','CLOSED','ABORTED')),
  spec_json TEXT NOT NULL,
  committed_at TEXT,
  assessment_json TEXT,
  assessed_at TEXT,
  policy_change TEXT,
  reopen_condition TEXT,
  closed_at TEXT,
  abort_reason TEXT,
  aborted_at TEXT
);
CREATE TABLE IF NOT EXISTS observations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  episode_id TEXT NOT NULL REFERENCES episodes(id),
  observed_at TEXT NOT NULL,
  metric_value REAL,
  note TEXT NOT NULL,
  evidence_ref TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  episode_id TEXT NOT NULL REFERENCES episodes(id),
  event_type TEXT NOT NULL,
  occurred_at TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  prev_hash TEXT NOT NULL,
  event_hash TEXT NOT NULL UNIQUE
);
CREATE INDEX IF NOT EXISTS idx_episode_state ON episodes(state);
CREATE INDEX IF NOT EXISTS idx_observation_episode ON observations(episode_id,id);
CREATE INDEX IF NOT EXISTS idx_event_episode ON events(episode_id,id);
CREATE TRIGGER IF NOT EXISTS freeze_committed_spec
BEFORE UPDATE OF spec_json ON episodes WHEN OLD.state <> 'DRAFT'
BEGIN SELECT RAISE(ABORT, 'committed episode spec is immutable'); END;
CREATE TRIGGER IF NOT EXISTS append_only_observation_update
BEFORE UPDATE ON observations BEGIN SELECT RAISE(ABORT, 'observations are append-only'); END;
CREATE TRIGGER IF NOT EXISTS append_only_observation_delete
BEFORE DELETE ON observations BEGIN SELECT RAISE(ABORT, 'observations are append-only'); END;
CREATE TRIGGER IF NOT EXISTS append_only_event_update
BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT, 'events are append-only'); END;
CREATE TRIGGER IF NOT EXISTS append_only_event_delete
BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT, 'events are append-only'); END;
"""


class LedgerError(ValueError):
    pass


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def instant(value: str, field: str) -> str:
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise LedgerError(f"{field} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise LedgerError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def canon(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def connect(path: str | Path) -> sqlite3.Connection:
    db = sqlite3.connect(str(path))
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    db.execute("PRAGMA journal_mode = WAL")
    return db


def init_db(db: sqlite3.Connection) -> None:
    db.executescript(SCHEMA)
    db.commit()


def row(db: sqlite3.Connection, episode_id: str) -> sqlite3.Row:
    value = db.execute("SELECT * FROM episodes WHERE id=?", (episode_id,)).fetchone()
    if value is None:
        raise LedgerError(f"unknown episode: {episode_id}")
    return value


def event_hash(episode_id: str, kind: str, at: str, payload: str, previous: str) -> str:
    return hashlib.sha256(canon([episode_id, kind, at, payload, previous]).encode()).hexdigest()


def append_event(db: sqlite3.Connection, episode_id: str, kind: str, payload: Any, at: str | None = None) -> None:
    timestamp = at or now()
    body = canon(payload)
    prior = db.execute(
        "SELECT event_hash FROM events WHERE episode_id=? ORDER BY id DESC LIMIT 1",
        (episode_id,),
    ).fetchone()
    previous = prior["event_hash"] if prior else "0" * 64
    digest = event_hash(episode_id, kind, timestamp, body, previous)
    db.execute(
        "INSERT INTO events(episode_id,event_type,occurred_at,payload_json,prev_hash,event_hash) VALUES(?,?,?,?,?,?)",
        (episode_id, kind, timestamp, body, previous, digest),
    )


def normalize_spec(spec: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(spec, dict):
        raise LedgerError("episode spec must be a JSON object")
    clean = dict(spec)
    if clean.get("horizon"):
        clean["horizon"] = instant(str(clean["horizon"]), "horizon")
    if "direction" in clean and clean["direction"] not in {"increase", "decrease", "target"}:
        raise LedgerError("direction must be increase, decrease, or target")
    for key in ("baseline_value", "target_value"):
        if key in clean and clean[key] is not None:
            clean[key] = float(clean[key])
    return clean


def missing_spec(spec: dict[str, Any]) -> list[str]:
    missing = [key for key in REQUIRED_SPEC if not str(spec.get(key, "")).strip()]
    trio = [spec.get("baseline_value"), spec.get("target_value"), spec.get("direction")]
    if any(value is not None for value in trio) and not all(value is not None for value in trio):
        missing.append("numeric trio: baseline_value, target_value, direction")
    return missing


def create_episode(db: sqlite3.Connection, spec: dict[str, Any], episode_id: str | None = None) -> str:
    clean = normalize_spec(spec)
    identifier = episode_id or uuid.uuid4().hex[:12]
    timestamp = now()
    db.execute(
        "INSERT INTO episodes(id,created_at,updated_at,state,spec_json) VALUES(?,?,?,?,?)",
        (identifier, timestamp, timestamp, "DRAFT", canon(clean)),
    )
    append_event(db, identifier, "CREATED", {"spec": clean}, timestamp)
    db.commit()
    return identifier


def edit_draft(db: sqlite3.Connection, episode_id: str, patch: dict[str, Any]) -> None:
    current = row(db, episode_id)
    if current["state"] != "DRAFT":
        raise LedgerError("only drafts can be edited")
    spec = json.loads(current["spec_json"])
    spec.update(patch)
    spec = normalize_spec(spec)
    timestamp = now()
    db.execute("UPDATE episodes SET spec_json=?,updated_at=? WHERE id=?", (canon(spec), timestamp, episode_id))
    append_event(db, episode_id, "DRAFT_EDITED", {"patch": patch}, timestamp)
    db.commit()


def commit_episode(db: sqlite3.Connection, episode_id: str) -> None:
    current = row(db, episode_id)
    if current["state"] != "DRAFT":
        raise LedgerError("only drafts can be committed")
    spec = json.loads(current["spec_json"])
    missing = missing_spec(spec)
    if missing:
        raise LedgerError("missing commit fields: " + ", ".join(missing))
    timestamp = now()
    db.execute("UPDATE episodes SET state='COMMITTED',committed_at=?,updated_at=? WHERE id=?", (timestamp, timestamp, episode_id))
    append_event(db, episode_id, "COMMITTED", {"spec": spec}, timestamp)
    db.commit()


def observe(db: sqlite3.Connection, episode_id: str, note: str, evidence_ref: str = "", metric_value: float | None = None, observed_at: str | None = None) -> int:
    current = row(db, episode_id)
    if current["state"] not in OPEN_STATES:
        raise LedgerError("observations require a committed or observing episode")
    if not note.strip():
        raise LedgerError("observation note is required")
    timestamp = instant(observed_at, "observed_at") if observed_at else now()
    cursor = db.execute(
        "INSERT INTO observations(episode_id,observed_at,metric_value,note,evidence_ref) VALUES(?,?,?,?,?)",
        (episode_id, timestamp, metric_value, note.strip(), evidence_ref.strip()),
    )
    db.execute("UPDATE episodes SET state='OBSERVING',updated_at=? WHERE id=?", (now(), episode_id))
    append_event(db, episode_id, "OBSERVED", {"observation_id": cursor.lastrowid, "observed_at": timestamp, "metric_value": metric_value, "note": note.strip(), "evidence_ref": evidence_ref.strip()})
    db.commit()
    return int(cursor.lastrowid)


def normalize_assessment(value: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise LedgerError("assessment must be a JSON object")
    assessment = dict(value)
    missing = [key for key in REQUIRED_ASSESSMENT if assessment.get(key) in {None, ""}]
    if missing:
        raise LedgerError("missing assessment fields: " + ", ".join(missing))
    assessment["verdict"] = str(assessment["verdict"]).upper()
    if assessment["verdict"] not in VERDICTS:
        raise LedgerError("invalid verdict")
    confidence = float(assessment["causal_confidence"])
    if not 0 <= confidence <= 1:
        raise LedgerError("causal_confidence must be between 0 and 1")
    assessment["causal_confidence"] = confidence
    if assessment.get("actual_value") is not None:
        actual = float(assessment["actual_value"])
        assessment["actual_value"] = actual
        trio = [spec.get("baseline_value"), spec.get("target_value"), spec.get("direction")]
        if all(item is not None for item in trio):
            baseline, target, direction = float(trio[0]), float(trio[1]), trio[2]
            met = actual >= target if direction == "increase" else actual <= target if direction == "decrease" else actual == target
            assessment["numeric_result"] = {"baseline_value": baseline, "target_value": target, "actual_value": actual, "delta": actual - baseline, "direction": direction, "target_met": met}
    return assessment


def assess(db: sqlite3.Connection, episode_id: str, assessment: dict[str, Any]) -> dict[str, Any]:
    current = row(db, episode_id)
    if current["state"] not in OPEN_STATES:
        raise LedgerError("assessment requires a committed or observing episode")
    clean = normalize_assessment(assessment, json.loads(current["spec_json"]))
    timestamp = now()
    db.execute("UPDATE episodes SET state='ASSESSED',assessment_json=?,assessed_at=?,updated_at=? WHERE id=?", (canon(clean), timestamp, timestamp, episode_id))
    append_event(db, episode_id, "ASSESSED", clean, timestamp)
    db.commit()
    return clean


def policy(db: sqlite3.Connection, episode_id: str, change: str, reopen_condition: str) -> None:
    current = row(db, episode_id)
    if current["state"] != "ASSESSED":
        raise LedgerError("policy update requires an assessed episode")
    if not change.strip() or not reopen_condition.strip():
        raise LedgerError("policy change and reopen condition are required")
    timestamp = now()
    db.execute("UPDATE episodes SET policy_change=?,reopen_condition=?,updated_at=? WHERE id=?", (change.strip(), reopen_condition.strip(), timestamp, episode_id))
    append_event(db, episode_id, "POLICY_RECORDED", {"policy_change": change.strip(), "reopen_condition": reopen_condition.strip()}, timestamp)
    db.commit()


def close(db: sqlite3.Connection, episode_id: str) -> None:
    current = row(db, episode_id)
    if current["state"] != "ASSESSED":
        raise LedgerError("only assessed episodes can be closed")
    if not current["policy_change"] or not current["reopen_condition"]:
        raise LedgerError("closure requires policy change and reopen condition")
    timestamp = now()
    db.execute("UPDATE episodes SET state='CLOSED',closed_at=?,updated_at=? WHERE id=?", (timestamp, timestamp, episode_id))
    append_event(db, episode_id, "CLOSED", {}, timestamp)
    db.commit()


def reopen(db: sqlite3.Connection, episode_id: str, witness: str) -> None:
    current = row(db, episode_id)
    if current["state"] != "CLOSED":
        raise LedgerError("only closed episodes can be reopened")
    if not witness.strip():
        raise LedgerError("reopen witness is required")
    timestamp = now()
    db.execute("UPDATE episodes SET state='OBSERVING',policy_change=NULL,closed_at=NULL,updated_at=? WHERE id=?", (timestamp, episode_id))
    append_event(db, episode_id, "REOPENED", {"witness": witness.strip(), "prior_condition": current["reopen_condition"]}, timestamp)
    db.commit()


def abort(db: sqlite3.Connection, episode_id: str, reason: str) -> None:
    current = row(db, episode_id)
    if current["state"] in {"CLOSED", "ABORTED"}:
        raise LedgerError("closed or aborted episodes cannot be aborted")
    if not reason.strip():
        raise LedgerError("abort reason is required")
    timestamp = now()
    db.execute("UPDATE episodes SET state='ABORTED',abort_reason=?,aborted_at=?,updated_at=? WHERE id=?", (reason.strip(), timestamp, timestamp, episode_id))
    append_event(db, episode_id, "ABORTED", {"reason": reason.strip()}, timestamp)
    db.commit()


def episode(db: sqlite3.Connection, episode_id: str) -> dict[str, Any]:
    current = dict(row(db, episode_id))
    current["spec"] = json.loads(current.pop("spec_json"))
    current["assessment"] = json.loads(current.pop("assessment_json")) if current["assessment_json"] else None
    current["observations"] = [dict(item) for item in db.execute("SELECT * FROM observations WHERE episode_id=? ORDER BY id", (episode_id,))]
    current["events"] = []
    for item in db.execute("SELECT * FROM events WHERE episode_id=? ORDER BY id", (episode_id,)):
        event = dict(item)
        event["payload"] = json.loads(event.pop("payload_json"))
        current["events"].append(event)
    return current


def list_episodes(db: sqlite3.Connection, states: list[str] | None = None) -> list[dict[str, Any]]:
    values = [state.upper() for state in states or []]
    if any(state not in STATES for state in values):
        raise LedgerError("unknown state filter")
    sql, params = "SELECT id,state,created_at,updated_at,spec_json FROM episodes", []
    if values:
        sql += " WHERE state IN (" + ",".join("?" for _ in values) + ")"
        params = values
    result = []
    for item in db.execute(sql + " ORDER BY created_at DESC,id DESC", params):
        spec = json.loads(item["spec_json"])
        result.append({"id": item["id"], "state": item["state"], "title": spec.get("title", ""), "horizon": spec.get("horizon", ""), "created_at": item["created_at"], "updated_at": item["updated_at"]})
    return result


def due(db: sqlite3.Connection, as_of: str | None = None) -> list[dict[str, Any]]:
    cutoff = instant(as_of, "as_of") if as_of else now()
    return [item for item in list_episodes(db, list(OPEN_STATES)) if item["horizon"] and item["horizon"] <= cutoff]


def verify(db: sqlite3.Connection, episode_id: str) -> list[str]:
    current = row(db, episode_id)
    errors, previous = [], "0" * 64
    events = list(db.execute("SELECT * FROM events WHERE episode_id=? ORDER BY id", (episode_id,)))
    if not events:
        errors.append("event chain is empty")
    for item in events:
        if item["prev_hash"] != previous:
            errors.append(f"event {item['id']} prev_hash mismatch")
        expected = event_hash(item["episode_id"], item["event_type"], item["occurred_at"], item["payload_json"], item["prev_hash"])
        if item["event_hash"] != expected:
            errors.append(f"event {item['id']} hash mismatch")
        previous = item["event_hash"]
    spec = json.loads(current["spec_json"])
    if current["state"] != "DRAFT" and missing_spec(spec):
        errors.append("non-draft has incomplete commitment spec")
    if current["state"] in {"ASSESSED", "CLOSED"} and not current["assessment_json"]:
        errors.append("assessed episode lacks assessment")
    if current["state"] == "CLOSED" and (not current["policy_change"] or not current["reopen_condition"]):
        errors.append("closed episode lacks policy or reopen condition")
    if current["state"] == "ABORTED" and not current["abort_reason"]:
        errors.append("aborted episode lacks reason")
    return errors


def export_jsonl(db: sqlite3.Connection, path: str | Path) -> int:
    ids = [item["id"] for item in db.execute("SELECT id FROM episodes ORDER BY created_at,id")]
    with Path(path).open("w", encoding="utf-8") as handle:
        for episode_id in ids:
            handle.write(canon(episode(db, episode_id)) + "\n")
    return len(ids)


def load_object(path: str) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise LedgerError("JSON file must contain an object")
    return value


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="consequence")
    root.add_argument("--db", default="consequence.db")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("init")
    new = commands.add_parser("new")
    new.add_argument("--spec", required=True)
    new.add_argument("--id")
    edit = commands.add_parser("edit")
    edit.add_argument("episode_id")
    edit.add_argument("--patch", required=True)
    for name in ("commit", "close", "show"):
        commands.add_parser(name).add_argument("episode_id")
    obs = commands.add_parser("observe")
    obs.add_argument("episode_id")
    obs.add_argument("--note", required=True)
    obs.add_argument("--evidence-ref", default="")
    obs.add_argument("--metric-value", type=float)
    obs.add_argument("--observed-at")
    ass = commands.add_parser("assess")
    ass.add_argument("episode_id")
    ass.add_argument("--assessment", required=True)
    pol = commands.add_parser("policy")
    pol.add_argument("episode_id")
    pol.add_argument("--change", required=True)
    pol.add_argument("--reopen-condition", required=True)
    reo = commands.add_parser("reopen")
    reo.add_argument("episode_id")
    reo.add_argument("--witness", required=True)
    ab = commands.add_parser("abort")
    ab.add_argument("episode_id")
    ab.add_argument("--reason", required=True)
    listing = commands.add_parser("list")
    listing.add_argument("--state", action="append", dest="states")
    overdue = commands.add_parser("due")
    overdue.add_argument("--as-of")
    check = commands.add_parser("verify")
    check.add_argument("episode_id", nargs="?")
    out = commands.add_parser("export")
    out.add_argument("--output", required=True)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    db = connect(args.db)
    try:
        init_db(db)
        command = args.command
        result: Any = None
        if command == "init":
            result = {"status": "initialized", "db": args.db}
        elif command == "new":
            result = {"episode_id": create_episode(db, load_object(args.spec), args.id), "state": "DRAFT"}
        elif command == "edit":
            edit_draft(db, args.episode_id, load_object(args.patch))
            result = {"episode_id": args.episode_id, "state": "DRAFT"}
        elif command == "commit":
            commit_episode(db, args.episode_id)
            result = {"episode_id": args.episode_id, "state": "COMMITTED"}
        elif command == "observe":
            result = {"episode_id": args.episode_id, "observation_id": observe(db, args.episode_id, args.note, args.evidence_ref, args.metric_value, args.observed_at)}
        elif command == "assess":
            result = {"episode_id": args.episode_id, "state": "ASSESSED", "assessment": assess(db, args.episode_id, load_object(args.assessment))}
        elif command == "policy":
            policy(db, args.episode_id, args.change, args.reopen_condition)
            result = {"episode_id": args.episode_id, "policy_recorded": True}
        elif command == "close":
            close(db, args.episode_id)
            result = {"episode_id": args.episode_id, "state": "CLOSED"}
        elif command == "reopen":
            reopen(db, args.episode_id, args.witness)
            result = {"episode_id": args.episode_id, "state": "OBSERVING"}
        elif command == "abort":
            abort(db, args.episode_id, args.reason)
            result = {"episode_id": args.episode_id, "state": "ABORTED"}
        elif command == "show":
            result = episode(db, args.episode_id)
        elif command == "list":
            result = list_episodes(db, args.states)
        elif command == "due":
            result = due(db, args.as_of)
        elif command == "verify":
            if args.episode_id:
                errors = verify(db, args.episode_id)
                result = {"episode_id": args.episode_id, "valid": not errors, "errors": errors}
            else:
                failures = {item["id"]: verify(db, item["id"]) for item in db.execute("SELECT id FROM episodes")}
                failures = {key: value for key, value in failures.items() if value}
                result = {"valid": not failures, "failures": failures}
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0 if result["valid"] else 1
        elif command == "export":
            result = {"episodes": export_jsonl(db, args.output), "output": args.output}
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (LedgerError, sqlite3.Error, OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
