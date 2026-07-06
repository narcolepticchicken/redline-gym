from __future__ import annotations

from pathlib import Path

from scripts.derive import derive
from validators.checks import v1_rubric_citations, v5_issue_deviation_mapping, v8_schema_and_hashes


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "tasks/contracts/T1-NDA-001"


def test_sample_schema_roundtrip_after_derivation() -> None:
    derive(SAMPLE)
    assert v8_schema_and_hashes(SAMPLE).status == "PASS"
    assert v1_rubric_citations(SAMPLE).status == "PASS"
    assert v5_issue_deviation_mapping(SAMPLE).status == "PASS"
