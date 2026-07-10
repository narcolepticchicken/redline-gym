from __future__ import annotations

from collections import Counter
import json
from math import ceil
from pathlib import Path

import pytest

from generator.t2n_response import generate_response
from scoring.t2n_contract import validate_counter_family, validate_family_pool_diversity
from validators.t2n_checks import run_all_t2n, v14_t2n_ledger


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "tasks" / "generated" / "T2-DPA-302"
FAMILIES = ROOT / "generator" / "t2n_families" / "privacy.json"
AREA_FILES = ("ai", "contracts", "crypto", "employment", "governance", "ma", "privacy")
PLAYBOOK_PATHS = {
    "PB-AI-001": ROOT / "playbooks" / "ai" / "PB-AI-001.json",
    "PB-MSA-001": ROOT / "playbooks" / "contracts" / "PB-MSA-001.json",
    "PB-NDA-001": ROOT / "playbooks" / "contracts" / "PB-NDA-001.json",
    "PB-CRYPTO-001": ROOT / "playbooks" / "crypto" / "PB-CRYPTO-001.json",
    "PB-EMP-001": ROOT / "playbooks" / "employment" / "PB-EMP-001.json",
    "PB-GOV-001": ROOT / "playbooks" / "governance" / "PB-GOV-001.json",
    "PB-MA-001": ROOT / "playbooks" / "ma" / "PB-MA-001.json",
    "PB-DPA-001": ROOT / "playbooks" / "privacy" / "PB-DPA-001.json",
}


def load(path: Path):
    return json.loads(path.read_text())


@pytest.fixture(scope="module")
def generated(tmp_path_factory):
    out = tmp_path_factory.mktemp("t2n-generated")
    generate_response(BASE, 7302, FAMILIES, out)
    return out


def test_generator_is_byte_deterministic(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    generate_response(BASE, 7302, FAMILIES, first)
    generate_response(BASE, 7302, FAMILIES, second)
    for name in ("patch_ledger.json", "turn_events.json", "phase1_document.txt", "phase2_document.txt"):
        assert (first / name).read_bytes() == (second / name).read_bytes(), name


def test_generated_fixture_passes_full_t2n_round_trip(generated):
    results = run_all_t2n(generated)
    assert [(result.code, result.status) for result in results] == [("V8-T2N", "PASS"), ("V14", "PASS")]


def test_exact_c8_au_coverage_matrix(generated):
    ledger = load(generated / "patch_ledger.json")
    patches = ledger["patches"]
    assert len(patches) == 8
    assert Counter(p["origin"] for p in patches) == Counter({"prior_position": 6, "novel_insertion": 1, "canary_probe": 1})
    rows = Counter(p["transition_row_id"] for p in patches)
    assert rows == Counter({"TR-01": 1, "TR-02": 1, "TR-03": 1, "TR-04": 1,
                            "TR-05": 2, "TR-06": 1, "TR-07": 1})
    counters = [p for p in patches if p["transition_row_id"] == "TR-05"]
    assert {p["counter_class"] for p in counters} == {"acceptable", "unacceptable"}
    assert len({p["counter_family_id"] for p in counters}) == 2


def test_all_area_families_validate_and_meet_playbook_quotas():
    covered = set()
    all_families = []
    for area in AREA_FILES:
        data = load(ROOT / "generator" / "t2n_families" / f"{area}.json")
        assert data["_status"] == "machine-drafted v2 scheme, unreviewed — review pass + Aaron line-item pending"
        for playbook_id, bundle in data.items():
            if playbook_id.startswith("_"):
                continue
            covered.add(playbook_id)
            families = bundle["counter_families"]
            all_families.extend(families)
            assert len(families) == 4
            for family in families:
                assert validate_counter_family(family) == [], family["counter_family_id"]
            quota = ceil(len(families) / 3)
            assert sum(bool(f.get("has_qualitative_decisive_input")) for f in families) >= quota
            assert sum(bool(f.get("has_arithmetic_interaction")) for f in families) >= quota
    assert covered == set(PLAYBOOK_PATHS)
    assert validate_family_pool_diversity(all_families) == []


def test_canary_benignity_uses_actual_signed_canary(generated):
    events = load(generated / "turn_events.json")["events"]
    canary_children = [child for event in events if event["event_type"] == "benign_canary_change" for child in event["children"]]
    assert len(canary_children) == 1
    assert canary_children[0]["expected_disposition"] != "reject"
    playbook = load(PLAYBOOK_PATHS["PB-DPA-001"])
    actual_canaries = {rule["rule_id"] for rule in playbook["rules"] if rule["is_canary"] is True}
    assert canary_children[0]["rule_id"] in actual_canaries


def test_sneak_two_child_integrity(generated):
    patches = [p for p in load(generated / "patch_ledger.json")["patches"] if p["event_type"] == "sneaky_reinsert"]
    assert len(patches) == 2
    assert len({p["event_id"] for p in patches}) == 1
    by_role = {p["child_role"]: p for p in patches}
    assert set(by_role) == {"source_cleanup", "inserted_effect"}
    assert by_role["source_cleanup"]["expected_disposition"] == "accept"
    assert by_role["inserted_effect"]["expected_disposition"] == "reject"
    assert by_role["inserted_effect"]["source_clause_id"] != by_role["inserted_effect"]["expected_clause_id"]


def test_v14_detects_tampered_phase2_bytes(generated):
    ledger = load(generated / "patch_ledger.json")
    events = load(generated / "turn_events.json")
    rendered = load(generated / "rendered_change_ids.json")
    reviews = load(generated / "reviews_by_change_id.json")
    card = load(generated / "card_t2n.json")
    tampered = bytearray((generated / "phase2_document.txt").read_bytes())
    tampered[-2] ^= 1
    result = v14_t2n_ledger(
        canonical_document=(generated / "phase1_document.txt").read_bytes(),
        phase2_document=bytes(tampered), ledger=ledger, turn_events=events,
        rendered_change_ids=rendered, reviews_by_change_id=reviews, card_changes=card["changes"],
    )
    assert result.status == "FAIL"
    assert "bytes" in result.detail
