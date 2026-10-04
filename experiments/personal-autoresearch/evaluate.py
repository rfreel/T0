#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent


class EvaluationError(ValueError):
    pass


@dataclass(frozen=True)
class InventoryRow:
    service_id: str
    current_option_id: str
    required_features: tuple[str, ...]
    feature_weights: tuple[float, ...]
    min_feature_coverage: float
    allow_cancel: bool


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise EvaluationError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise EvaluationError(f"invalid JSON in {path}: {exc}") from exc


def _finite_nonnegative(value: Any, label: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise EvaluationError(f"{label} must be numeric")
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise EvaluationError(f"{label} must be finite and nonnegative")
    return number


def load_inventory(path: Path) -> list[InventoryRow]:
    rows: list[InventoryRow] = []
    try:
        handle = path.open("r", encoding="utf-8", newline="")
    except FileNotFoundError as exc:
        raise EvaluationError(f"missing inventory: {path}") from exc

    with handle:
        reader = csv.DictReader(handle)
        required_columns = {
            "service_id",
            "current_option_id",
            "required_features",
            "feature_weights",
            "min_feature_coverage",
            "allow_cancel",
        }
        if set(reader.fieldnames or ()) != required_columns:
            raise EvaluationError(
                f"inventory columns must be exactly {sorted(required_columns)}"
            )
        seen: set[str] = set()
        for line_number, raw in enumerate(reader, start=2):
            service_id = (raw["service_id"] or "").strip()
            current_option_id = (raw["current_option_id"] or "").strip()
            if not service_id or not current_option_id:
                raise EvaluationError(f"inventory line {line_number}: empty identifier")
            if service_id in seen:
                raise EvaluationError(f"duplicate inventory service_id: {service_id}")
            seen.add(service_id)

            features = tuple(x.strip() for x in raw["required_features"].split("|") if x.strip())
            try:
                weights = tuple(float(x.strip()) for x in raw["feature_weights"].split("|"))
                threshold = float(raw["min_feature_coverage"])
            except ValueError as exc:
                raise EvaluationError(f"inventory line {line_number}: invalid number") from exc
            if not features or len(features) != len(weights):
                raise EvaluationError(
                    f"inventory line {line_number}: feature/weight length mismatch"
                )
            if any(not math.isfinite(x) or x < 0 for x in weights):
                raise EvaluationError(f"inventory line {line_number}: invalid weights")
            if not math.isclose(sum(weights), 1.0, abs_tol=1e-6):
                raise EvaluationError(
                    f"inventory line {line_number}: feature weights must sum to 1.0"
                )
            if not 0 <= threshold <= 1:
                raise EvaluationError(
                    f"inventory line {line_number}: min_feature_coverage outside [0,1]"
                )
            allow_cancel_raw = raw["allow_cancel"].strip().lower()
            if allow_cancel_raw not in {"true", "false"}:
                raise EvaluationError(
                    f"inventory line {line_number}: allow_cancel must be true or false"
                )
            rows.append(
                InventoryRow(
                    service_id=service_id,
                    current_option_id=current_option_id,
                    required_features=features,
                    feature_weights=weights,
                    min_feature_coverage=threshold,
                    allow_cancel=allow_cancel_raw == "true",
                )
            )
    if not rows:
        raise EvaluationError("inventory contains no services")
    return rows


def load_catalog(path: Path) -> dict[str, dict[str, dict[str, Any]]]:
    raw = _load_json(path)
    if not isinstance(raw, dict) or raw.get("version") != 1:
        raise EvaluationError("catalog must be an object with version=1")
    services = raw.get("services")
    if not isinstance(services, dict) or not services:
        raise EvaluationError("catalog.services must be a nonempty object")

    normalized: dict[str, dict[str, dict[str, Any]]] = {}
    for service_id, service in services.items():
        if not isinstance(service_id, str) or not service_id:
            raise EvaluationError("catalog service identifiers must be nonempty strings")
        if not isinstance(service, dict) or not isinstance(service.get("options"), list):
            raise EvaluationError(f"catalog service {service_id}: options must be a list")
        options: dict[str, dict[str, Any]] = {}
        for option in service["options"]:
            if not isinstance(option, dict):
                raise EvaluationError(f"catalog service {service_id}: option must be an object")
            option_id = option.get("option_id")
            if not isinstance(option_id, str) or not option_id:
                raise EvaluationError(f"catalog service {service_id}: invalid option_id")
            if option_id in options:
                raise EvaluationError(f"duplicate catalog option_id: {option_id}")
            if option.get("mode") not in {"keep", "replace", "rebuild", "cancel"}:
                raise EvaluationError(f"catalog option {option_id}: invalid mode")
            for field in (
                "monthly_cost",
                "migration_hours",
                "maintenance_hours_monthly",
                "privacy",
                "reliability",
            ):
                number = _finite_nonnegative(option.get(field), f"{option_id}.{field}")
                if field in {"privacy", "reliability"} and number > 1:
                    raise EvaluationError(f"{option_id}.{field} must be within [0,1]")
            coverage = option.get("feature_coverage")
            if not isinstance(coverage, dict):
                raise EvaluationError(f"{option_id}.feature_coverage must be an object")
            for feature, value in coverage.items():
                if not isinstance(feature, str) or not feature:
                    raise EvaluationError(f"{option_id}: invalid feature name")
                number = _finite_nonnegative(value, f"{option_id}.{feature}")
                if number > 1:
                    raise EvaluationError(f"{option_id}.{feature} must be within [0,1]")
            options[option_id] = option
        normalized[service_id] = options
    return normalized


def _load_candidate(path: Path) -> list[dict[str, str]]:
    raw = _load_json(path)
    if not isinstance(raw, dict) or set(raw) != {"version", "decisions"}:
        raise EvaluationError("candidate must contain exactly version and decisions")
    if raw["version"] != 1 or not isinstance(raw["decisions"], list):
        raise EvaluationError("candidate version must be 1 and decisions must be a list")
    decisions: list[dict[str, str]] = []
    for index, decision in enumerate(raw["decisions"]):
        if not isinstance(decision, dict) or set(decision) != {"service_id", "option_id"}:
            raise EvaluationError(
                f"candidate decision {index} must contain exactly service_id and option_id"
            )
        service_id = decision["service_id"]
        option_id = decision["option_id"]
        if not isinstance(service_id, str) or not service_id:
            raise EvaluationError(f"candidate decision {index}: invalid service_id")
        if not isinstance(option_id, str) or not option_id:
            raise EvaluationError(f"candidate decision {index}: invalid option_id")
        decisions.append({"service_id": service_id, "option_id": option_id})
    return decisions


def evaluate_candidate(
    candidate_path: Path,
    *,
    root: Path = ROOT,
    inventory_path: Path | None = None,
    catalog_path: Path | None = None,
) -> dict[str, Any]:
    config = _load_json(root / "config.json")
    inventory = load_inventory(
        inventory_path or (root / config["inventory_file"])
    )
    catalog = load_catalog(catalog_path or (root / config["catalog_file"]))
    decisions = _load_candidate(candidate_path)

    hard_failures: list[str] = []
    decision_map: dict[str, str] = {}
    for decision in decisions:
        service_id = decision["service_id"]
        if service_id in decision_map:
            hard_failures.append(f"duplicate decision for service {service_id}")
        decision_map[service_id] = decision["option_id"]

    inventory_ids = {row.service_id for row in inventory}
    for unknown in sorted(set(decision_map) - inventory_ids):
        hard_failures.append(f"decision for unknown service {unknown}")
    for missing in sorted(inventory_ids - set(decision_map)):
        hard_failures.append(f"missing decision for service {missing}")

    baseline_cost = 0.0
    selected_cost = 0.0
    total_migration = 0.0
    total_maintenance = 0.0
    coverage_values: list[float] = []
    privacy_values: list[float] = []
    reliability_values: list[float] = []
    details: list[dict[str, Any]] = []

    for row in inventory:
        service_catalog = catalog.get(row.service_id)
        if service_catalog is None:
            raise EvaluationError(f"catalog missing inventory service {row.service_id}")
        current = service_catalog.get(row.current_option_id)
        if current is None:
            raise EvaluationError(
                f"catalog missing current option {row.current_option_id} for {row.service_id}"
            )
        baseline_cost += float(current["monthly_cost"])

        option_id = decision_map.get(row.service_id)
        option = service_catalog.get(option_id) if option_id is not None else None
        if option_id is None:
            continue
        if option is None:
            hard_failures.append(
                f"unknown option {option_id} for service {row.service_id}"
            )
            continue
        if option["mode"] == "cancel" and not row.allow_cancel:
            hard_failures.append(f"service {row.service_id} may not be cancelled")

        coverage_map = option["feature_coverage"]
        missing_features = [f for f in row.required_features if f not in coverage_map]
        if missing_features:
            hard_failures.append(
                f"option {option_id} lacks coverage values for {','.join(missing_features)}"
            )
            coverage = 0.0
        else:
            coverage = sum(
                float(coverage_map[feature]) * weight
                for feature, weight in zip(row.required_features, row.feature_weights)
            )
        if coverage + 1e-12 < row.min_feature_coverage:
            hard_failures.append(
                f"service {row.service_id} feature coverage {coverage:.4f} "
                f"below {row.min_feature_coverage:.4f}"
            )

        cost = float(option["monthly_cost"])
        migration = float(option["migration_hours"])
        maintenance = float(option["maintenance_hours_monthly"])
        selected_cost += cost
        total_migration += migration
        total_maintenance += maintenance
        coverage_values.append(coverage)
        privacy_values.append(float(option["privacy"]))
        reliability_values.append(float(option["reliability"]))
        details.append(
            {
                "service_id": row.service_id,
                "option_id": option_id,
                "mode": option["mode"],
                "monthly_cost": cost,
                "feature_coverage": round(coverage, 6),
                "privacy": float(option["privacy"]),
                "reliability": float(option["reliability"]),
                "migration_hours": migration,
                "maintenance_hours_monthly": maintenance,
            }
        )

    if selected_cost > baseline_cost + 1e-9:
        hard_failures.append(
            f"monthly cost {selected_cost:.2f} exceeds baseline {baseline_cost:.2f}"
        )

    count = len(inventory)
    complete_metrics = (
        len(coverage_values) == count
        and len(privacy_values) == count
        and len(reliability_values) == count
    )
    if complete_metrics:
        savings_ratio = max(0.0, min(1.0, (baseline_cost - selected_cost) / baseline_cost))
        cost_score = 50.0 + 50.0 * savings_ratio
        feature_score = 100.0 * sum(coverage_values) / count
        privacy_score = 100.0 * sum(privacy_values) / count
        reliability_score = 100.0 * sum(reliability_values) / count
        migration_penalty = min(15.0, 0.5 * total_migration)
        maintenance_penalty = min(15.0, 2.0 * total_maintenance)
        raw_score = (
            0.40 * cost_score
            + 0.30 * feature_score
            + 0.15 * privacy_score
            + 0.15 * reliability_score
            - migration_penalty
            - maintenance_penalty
        )
        outcome_score = max(0.0, min(100.0, raw_score))
    else:
        savings_ratio = 0.0
        cost_score = feature_score = privacy_score = reliability_score = 0.0
        migration_penalty = maintenance_penalty = 0.0
        outcome_score = 0.0

    return {
        "target": config["target_name"],
        "outcome_score": round(outcome_score, 6),
        "instrument_integrity_score": 100.0,
        "hard_failures": hard_failures,
        "accepted_by_evaluator": not hard_failures,
        "metrics": {
            "baseline_monthly_cost": round(baseline_cost, 2),
            "selected_monthly_cost": round(selected_cost, 2),
            "monthly_savings": round(baseline_cost - selected_cost, 2),
            "savings_ratio": round(savings_ratio, 6),
            "cost_score": round(cost_score, 6),
            "feature_score": round(feature_score, 6),
            "privacy_score": round(privacy_score, 6),
            "reliability_score": round(reliability_score, 6),
            "migration_hours": round(total_migration, 2),
            "maintenance_hours_monthly": round(total_maintenance, 2),
            "migration_penalty": round(migration_penalty, 6),
            "maintenance_penalty": round(maintenance_penalty, 6),
        },
        "decisions": details,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a service replacement candidate")
    parser.add_argument("--candidate", type=Path, default=None)
    parser.add_argument("--inventory", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    config = _load_json(ROOT / "config.json")
    candidate = args.candidate or (ROOT / config["candidate_file"])
    try:
        result = evaluate_candidate(candidate, inventory_path=args.inventory)
    except EvaluationError as exc:
        print(f"evaluation_error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"outcome_score:              {result['outcome_score']:.6f}")
        print(f"instrument_integrity_score: {result['instrument_integrity_score']:.1f}")
        print(f"hard_failures:              {len(result['hard_failures'])}")
        print(f"monthly_cost:               {result['metrics']['selected_monthly_cost']:.2f}")
        print(f"monthly_savings:            {result['metrics']['monthly_savings']:.2f}")
        print(f"feature_score:              {result['metrics']['feature_score']:.6f}")
        print(f"privacy_score:              {result['metrics']['privacy_score']:.6f}")
        print(f"reliability_score:          {result['metrics']['reliability_score']:.6f}")
        for failure in result["hard_failures"]:
            print(f"failure: {failure}")
    return 0 if result["accepted_by_evaluator"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
