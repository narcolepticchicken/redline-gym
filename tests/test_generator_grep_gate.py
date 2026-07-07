from __future__ import annotations

from pathlib import Path
import random
import shutil

import pytest

import generator.generate as generate_module
from generator.generate import GenerationError, T2_GREP_RECALL_MAX, generate_instance, measure_grep_bot_recall


ROOT = Path(__file__).resolve().parents[1]


def test_t2_generation_reseeds_when_grep_recall_exceeds_threshold(monkeypatch) -> None:
    calls: list[Path] = []

    def fake_measure(task_dir: Path) -> dict:
        calls.append(task_dir)
        if len(calls) == 1:
            return {
                "recall": 1.0,
                "matched_deviation_ids": ["D-001"],
                "matched_rule_ids": ["R-001"],
            }
        return {
            "recall": 0.0,
            "matched_deviation_ids": [],
            "matched_rule_ids": [],
        }

    monkeypatch.setattr(generate_module, "measure_grep_bot_recall", fake_measure)
    out_dir = ROOT / "runs/pytest-grep-gate/T2-NDA-997"
    shutil.rmtree(out_dir.parent, ignore_errors=True)
    try:
        log = generate_instance(
            ROOT / "playbooks/contracts/PB-NDA-001.json",
            "T2",
            997,
            out_dir,
        )
        assert len(calls) == 2
        assert any("grep_bot attempt_seed=997 recall=1.000000 matched_rule_ids=R-001" == line for line in log)
        assert any("grep_bot attempt_seed=1997 recall=0.000000 matched_rule_ids=none" == line for line in log)
        assert (out_dir / "task.json").exists()
    finally:
        shutil.rmtree(out_dir.parent, ignore_errors=True)


def test_render_base_renumbers_sections_and_cross_refs() -> None:
    base = {
        "heading_template": "# Test",
        "preamble_template": "Preamble.",
        "section_order_variants": [["2", "1"]],
        "sections": [
            {"id": "1", "heading": "One", "paragraphs": ["See Section 2."]},
            {"id": "2", "heading": "Two", "paragraphs": ["Controls."]},
        ],
    }
    text, section_map = generate_module._render_base(base, {}, random.Random(0))

    assert "## 1. Two" in text
    assert "## 2. One" in text
    assert "See Section 1." in text
    assert section_map == {"2": "1", "1": "2"}


def test_missing_info_gap_guard_refuses_topic_present_in_document() -> None:
    missing_info = [
        {
            "missing_info_id": "M-777",
            "match_keywords": ["approval process"],
        }
    ]
    doc_text = "# Agreement\n\n## 6. Equity Awards\n\nThe equity approval process is complete.\n"
    playbook = {"rules": []}

    with pytest.raises(GenerationError, match="M-777.*approval process.*6\\. Equity Awards.*mis-typed"):
        generate_module._validate_missing_info_gap_integrity(missing_info, doc_text, playbook)


def test_missing_info_gap_guard_refuses_rule_covered_topic() -> None:
    missing_info = [
        {
            "missing_info_id": "M-778",
            "match_keywords": ["excise tax"],
        }
    ]
    doc_text = "# Agreement\n\n## 8. Termination\n\nSeverance is six months of salary.\n"
    playbook = {
        "rules": [
            {
                "rule_id": "R-099",
                "position": "The agreement should allocate excise tax exposure.",
                "fallback": "Escalate tax exposure.",
            }
        ]
    }

    with pytest.raises(GenerationError, match="M-778.*excise tax.*R-099.*rule-covered"):
        generate_module._validate_missing_info_gap_integrity(missing_info, doc_text, playbook)


def test_registered_distractor_guard_refuses_phantom_span() -> None:
    doc_text = "# Agreement\n\nThis clause is present once.\n"
    distractors = [
        {
            "distractor_id": "X-999",
            "doc_id": "DOC-01",
            "span": "This clause is absent.",
            "why_benign": "Fixture benign text.",
        }
    ]

    with pytest.raises(GenerationError, match="X-999 distractor span appears 0 times"):
        generate_module._validate_registered_distractors(doc_text, distractors)


def test_generated_t2_tranche_is_grep_resistant() -> None:
    task_dirs = sorted((ROOT / "tasks/generated").glob("T2-*"))
    assert task_dirs
    failures = []
    for task_dir in task_dirs:
        result = measure_grep_bot_recall(task_dir)
        if result["recall"] > T2_GREP_RECALL_MAX:
            failures.append(f"{task_dir.name}: {result['recall']:.6f} {result['matched_rule_ids']}")
    assert failures == []
