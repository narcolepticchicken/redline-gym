from __future__ import annotations

import json
from pathlib import Path
import random
import shutil

from generator.generate import _render_recipe
from scoring.core import _fallback_score, _tiered_redline_match, score_episode
from validators.checks import v12_redline_text_consistency


ROOT = Path(__file__).resolve().parents[1]
OLD_SAMPLE = ROOT / "tasks/contracts/T1-NDA-001"
REGENERATED_SAMPLE = ROOT / "tasks/generated/T1-NDA-101"


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def _dump(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n")


def test_tiered_redline_match_exact_normalizes_quotes_whitespace_and_punctuation() -> None:
    expected = 'Customer “shall pay” within thirty days, after invoice.'
    proposed = ' customer  "shall pay" within thirty days , after invoice. '
    assert _tiered_redline_match(proposed, expected, ["Customer"]) == 1.0


def test_tiered_redline_match_span_preserves_expected_token_order() -> None:
    expected = "Acme shall pay invoices within thirty days after receiving a valid invoice."
    proposed = "For clarity, Acme shall pay invoices within thirty days after receiving a valid invoice."
    assert _tiered_redline_match(proposed, expected, ["Acme", "thirty days"]) == 0.75


def test_tiered_redline_match_containment_allows_reordered_tokens() -> None:
    expected = "alpha beta gamma delta epsilon zeta eta theta iota kappa"
    proposed = "kappa iota theta eta zeta epsilon delta gamma beta alpha"
    assert _tiered_redline_match(proposed, expected, []) == 0.50


def test_tiered_redline_match_none_for_unrelated_text() -> None:
    assert _tiered_redline_match("unrelated words only", "alpha beta gamma delta", []) == 0.0


def test_fallback_score_selects_tiered_only_when_every_required_deviation_has_text() -> None:
    first = {
        "deviation_id": "D-001",
        "rule_id": "R-001",
        "expected_action": "redline_with_fallback",
        "expected_redline_text": "Alpha shall pay within thirty days.",
        "expected_redline_key_slots": ["Alpha"],
    }
    second = {
        "deviation_id": "D-002",
        "rule_id": "R-002",
        "expected_action": "redline_with_fallback",
        "expected_redline_text": "Beta may terminate on written notice.",
        "expected_redline_key_slots": ["Beta"],
    }
    findings = [{"proposed_redline": first["expected_redline_text"]}]
    matches = [first]
    rules = {
        "R-001": {"fallback": first["expected_redline_text"]},
        "R-002": {"fallback": second["expected_redline_text"]},
    }

    value, label = _fallback_score([first, second], findings, matches, rules, None, False)
    assert (value, label) == (0.5, "tiered_v2")

    second_without_text = {key: value for key, value in second.items() if not key.startswith("expected_redline_")}
    value, label = _fallback_score(
        [first, second_without_text], findings, matches, rules, None, False
    )
    assert (value, label) == (0.5, "v1")


def test_score_episode_labels_old_and_regenerated_task_formats() -> None:
    old = score_episode(OLD_SAMPLE, [], [], {})
    regenerated = score_episode(REGENERATED_SAMPLE, [], [], {})

    assert old["task_type"] == "seeded"
    assert old["fallback_scoring"] == "v1"
    assert regenerated["task_type"] == "seeded"
    assert regenerated["fallback_scoring"] == "tiered_v2"


def test_v12_passes_good_field_and_noops_without_field(tmp_path: Path) -> None:
    task_dir = tmp_path / OLD_SAMPLE.name
    shutil.copytree(OLD_SAMPLE, task_dir)
    planted_path = task_dir / "planted_deviations.json"
    planted = _load(planted_path)

    assert v12_redline_text_consistency(task_dir).status == "PASS"

    playbook = _load(ROOT / _load(task_dir / "task.json")["playbook_ref"])
    rules = {rule["rule_id"]: rule for rule in playbook["rules"]}
    dev = planted["deviations"][0]
    dev["expected_redline_text"] = rules[dev["rule_id"]]["fallback"]
    dev["expected_redline_key_slots"] = []
    _dump(planted_path, planted)
    assert v12_redline_text_consistency(task_dir).status == "PASS"


def test_v12_fails_empty_or_mutated_redline_text(tmp_path: Path) -> None:
    task_dir = tmp_path / OLD_SAMPLE.name
    shutil.copytree(OLD_SAMPLE, task_dir)
    planted_path = task_dir / "planted_deviations.json"
    planted = _load(planted_path)
    dev = planted["deviations"][0]

    dev["expected_redline_text"] = ""
    _dump(planted_path, planted)
    empty = v12_redline_text_consistency(task_dir)
    assert empty.status == "FAIL"
    assert "is empty" in empty.detail

    dev["expected_redline_text"] = dev["mutated_text"]
    _dump(planted_path, planted)
    equal = v12_redline_text_consistency(task_dir)
    assert equal.status == "FAIL"
    assert "equals mutated_text" in equal.detail


def test_render_recipe_records_deduplicated_original_template_slot_values() -> None:
    recipe = {
        "slots": {"days": ["thirty"]},
        "templates": {
            "original_text": "{party} pays in {days} days; {party} receives notice.",
            "mutated_text": "{party} pays immediately.",
        },
    }
    rendered = _render_recipe(recipe, {"party": "Acme"}, random.Random(0), {})
    assert rendered["expected_redline_key_slots"] == ["Acme", "thirty"]
