from __future__ import annotations

import json
import shutil
from pathlib import Path

from scripts.adjudicate_extras import build_adjudication_prompt, collect_adjudication_items, extract_section_text


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "tasks/contracts/T1-NDA-001"


def test_collects_v3_and_v4_extra_items_without_api(tmp_path: Path) -> None:
    task_dir = tmp_path / "T1-NDA-001"
    shutil.copytree(SAMPLE, task_dir)
    checks = task_dir / "model_checks"
    checks.mkdir(exist_ok=True)
    _dump(
        checks / "V3_clean_base.json",
        {
            "verdict": "FAIL",
            "violations": [
                {
                    "rule_id": "R-001",
                    "section": "1",
                    "quote": "Confidential Information means all non-public information.",
                }
            ],
        },
    )
    _dump(
        checks / "V4_round_trip.json",
        {
            "found": [
                {"rule_id": "R-001", "section": "1", "quote": "planted item"},
                {"rule_id": "R-014", "section": "13", "quote": "New York"},
            ]
        },
    )

    items = collect_adjudication_items(task_dir)

    assert [item["source"] for item in items] == ["V3_clean_base", "V4_round_trip_extra"]
    assert all("STRICT JSON" in item["prompt"] for item in items)
    assert "Fallback:" in items[0]["prompt"]
    assert "## 1." in items[0]["section_text"]
    assert items[1]["rule_id"] == "R-014"


def test_extract_section_text_by_section_number() -> None:
    doc = "# Title\n\n## 1. First\n\nAlpha\n\n## 2. Second\n\nBeta\n"

    assert extract_section_text(doc, "Section 2") == "## 2. Second\n\nBeta"


def test_build_adjudication_prompt_includes_rule_and_section() -> None:
    prompt = build_adjudication_prompt(
        {"rule_id": "R-001", "position": "Required stance", "fallback": "Fallback text"},
        "## 1. Section\n\nClause text.",
    )

    assert "Required stance" in prompt
    assert "Fallback text" in prompt
    assert '{"genuine": true|false, "reason": "..."}' in prompt


def _dump(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n")
