import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from consequence import (
    LedgerError, assess, close, commit_episode, connect, create_episode, due,
    edit_draft, episode, export_jsonl, init_db, observe, policy, reopen, verify,
)

SPEC = {
    "title": "Trial", "situation": "Decision delayed", "decision": "Run trial",
    "baseline": "Ten days", "intervention": "One reversible trial",
    "authority": "Operator may act", "resources": "Four hours",
    "horizon": "2026-01-01T00:00:00+00:00", "prediction": "Five days",
    "rival_prediction": "Ten days", "success_criterion": "At most five days",
    "rollback": "Restore prior process", "baseline_value": 10,
    "target_value": 5, "direction": "decrease",
}
ASSESSMENT = {
    "actual_observation": "Four days", "actual_value": 4, "verdict": "SUCCESS",
    "unintended_effects": "None", "actual_cost": "Three hours", "delay": "None",
    "causal_confidence": 0.8, "transferred": "Gate transferred", "failed": "Nothing",
}

class ConsequenceTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = connect(Path(self.temp.name) / "ledger.db")
        init_db(self.db)

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_incomplete_draft_cannot_commit(self):
        identifier = create_episode(self.db, {"title": "Incomplete"})
        with self.assertRaisesRegex(LedgerError, "missing commit fields"):
            commit_episode(self.db, identifier)

    def test_patch_then_commit_and_freeze(self):
        identifier = create_episode(self.db, {"title": "Trial"})
        patch = dict(SPEC)
        patch.pop("title")
        edit_draft(self.db, identifier, patch)
        commit_episode(self.db, identifier)
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE episodes SET spec_json='{}' WHERE id=?", (identifier,))

    def test_observation_is_append_only(self):
        identifier = create_episode(self.db, SPEC)
        commit_episode(self.db, identifier)
        observation_id = observe(self.db, identifier, "Observed", "artifact://1", 7)
        self.assertEqual(episode(self.db, identifier)["state"], "OBSERVING")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("DELETE FROM observations WHERE id=?", (observation_id,))

    def test_assessment_numeric_result(self):
        identifier = create_episode(self.db, SPEC)
        commit_episode(self.db, identifier)
        result = assess(self.db, identifier, ASSESSMENT)
        self.assertTrue(result["numeric_result"]["target_met"])
        self.assertEqual(result["numeric_result"]["delta"], -6)

    def test_close_requires_policy_and_reopen_condition(self):
        identifier = create_episode(self.db, SPEC)
        commit_episode(self.db, identifier)
        assess(self.db, identifier, ASSESSMENT)
        with self.assertRaisesRegex(LedgerError, "closure requires"):
            close(self.db, identifier)
        policy(self.db, identifier, "Adopt gate", "Reopen above five days")
        close(self.db, identifier)
        self.assertEqual(episode(self.db, identifier)["state"], "CLOSED")

    def test_reopen_requires_witness(self):
        identifier = create_episode(self.db, SPEC)
        commit_episode(self.db, identifier)
        assess(self.db, identifier, ASSESSMENT)
        policy(self.db, identifier, "Adopt", "Above five")
        close(self.db, identifier)
        reopen(self.db, identifier, "Observed six days")
        self.assertEqual(episode(self.db, identifier)["state"], "OBSERVING")

    def test_due_normalizes_offsets(self):
        spec = dict(SPEC)
        spec["horizon"] = "2026-01-01T02:00:00+02:00"
        identifier = create_episode(self.db, spec, "overdue")
        commit_episode(self.db, identifier)
        self.assertEqual(episode(self.db, identifier)["spec"]["horizon"], "2026-01-01T00:00:00+00:00")
        self.assertEqual([x["id"] for x in due(self.db, "2026-01-02T00:00:00Z")], ["overdue"])

    def test_naive_horizon_rejected(self):
        spec = dict(SPEC)
        spec["horizon"] = "2026-01-01T00:00:00"
        with self.assertRaisesRegex(LedgerError, "timezone"):
            create_episode(self.db, spec)

    def test_event_chain_verifies_and_rejects_mutation(self):
        identifier = create_episode(self.db, SPEC)
        commit_episode(self.db, identifier)
        self.assertEqual(verify(self.db, identifier), [])
        event_id = episode(self.db, identifier)["events"][0]["id"]
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE events SET payload_json='{}' WHERE id=?", (event_id,))

    def test_export_contains_complete_episode(self):
        create_episode(self.db, SPEC, "exported")
        output = Path(self.temp.name) / "out.jsonl"
        self.assertEqual(export_jsonl(self.db, output), 1)
        self.assertEqual(json.loads(output.read_text())["id"], "exported")

    def test_partial_numeric_trio_rejected(self):
        spec = dict(SPEC)
        spec.pop("target_value")
        identifier = create_episode(self.db, spec)
        with self.assertRaisesRegex(LedgerError, "numeric trio"):
            commit_episode(self.db, identifier)

if __name__ == "__main__":
    unittest.main()
