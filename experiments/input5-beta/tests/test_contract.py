from __future__ import annotations

import json
from pathlib import Path

import pytest

from identifiers.normalize import UnsafeIdentifier, normalize_identifier


CONTRACT = json.loads(
    (Path(__file__).parents[1] / "contract-v1.0.0.json").read_text(encoding="utf-8")
)


def test_contract_identity_and_status() -> None:
    assert CONTRACT["contract_id"] == "rfreel.T0.normalize_identifier"
    assert CONTRACT["version"] == "1.0.0"
    assert CONTRACT["status"] == "active"


def test_contract_examples() -> None:
    for example in CONTRACT["examples"]:
        assert normalize_identifier(example["input"]) == example["output"]


def test_contract_rejections() -> None:
    for example in CONTRACT["rejections"]:
        raw = example["input_escape"].encode("utf-8").decode("unicode_escape")
        with pytest.raises(UnsafeIdentifier):
            normalize_identifier(raw)
