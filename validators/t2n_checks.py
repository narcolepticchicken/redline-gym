"""Standalone T2-N validators. Deliberately not registered in checks.run_all()."""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from math import log
from pathlib import Path
import random
import re
import subprocess
import sys
from typing import Any, Mapping, Sequence

from jsonschema import Draft202012Validator

from scoring.t2n_contract import LEGAL_TRANSITION_TRIPLES
from validators.checks import ValidationResult


ROOT = Path(__file__).resolve().parents[1]
T2N_SCHEMA_DIR = ROOT / "schema" / "t2n"
FORBIDDEN_LEAKAGE_FIELDS = {
    "permutation_seed", "pre_permutation_index", "tranche_membership", "quota",
    "generator_attempt_number", "family_id", "family_hash", "counter_class",
}


def _result(code: str, name: str, errors: list[str]) -> ValidationResult:
    return ValidationResult(code, name, "FAIL" if errors else "PASS", "; ".join(errors) if errors else "ok")


def replay_ledger(canonical: bytes, patches: Sequence[Mapping[str, Any]]) -> bytes:
    """Replay canonical-coordinate patches in ascending order (v3 §9)."""
    ordered = sorted(patches, key=lambda p: (p["start_offset"], p["end_offset"]))
    cursor = 0
    output = bytearray()
    previous_end = -1
    previous_insert_at: int | None = None
    for patch in ordered:
        start, end = patch["start_offset"], patch["end_offset"]
        op = patch["op"]
        if start > end or end > len(canonical):
            raise ValueError(f"{patch['change_id']} offset outside canonical document")
        is_insert = op in {"insert_before", "insert_after"}
        if (start < previous_end) or (is_insert and previous_insert_at == start):
            raise ValueError(f"{patch['change_id']} overlaps another patch in canonical offset space")
        before = patch["before_text"].encode()
        actual = canonical[start:end]
        if actual != before:
            raise ValueError(f"{patch['change_id']} before_text/offset precondition mismatch")
        if hashlib.sha256(actual).hexdigest() != patch["precondition_sha256"]:
            raise ValueError(f"{patch['change_id']} precondition hash mismatch")
        output.extend(canonical[cursor:start])
        after = patch["after_text"].encode()
        if op == "replace": output.extend(after)
        elif op == "delete": pass
        elif op == "insert_before": output.extend(after)
        elif op == "insert_after":
            output.extend(actual)
            output.extend(after)
        else: raise ValueError(f"{patch['change_id']} unknown operation {op}")
        cursor = end
        previous_end = max(previous_end, end)
        previous_insert_at = start if is_insert else None
    output.extend(canonical[cursor:])
    return bytes(output)


def v14_t2n_ledger(*, canonical_document: bytes, phase2_document: bytes,
                    ledger: Mapping[str, Any], turn_events: Mapping[str, Any],
                    rendered_change_ids: Sequence[str],
                    reviews_by_change_id: Mapping[str, Mapping[str, Any]] | None = None,
                    card_changes: Sequence[Mapping[str, Any]] | None = None) -> ValidationResult:
    """V14 replay, cardinality, origin/action, and v4 §§1.4-1.5 checks."""
    errors: list[str] = []
    patches = list(ledger.get("patches", []))
    try:
        rendered = replay_ledger(canonical_document, patches)
        if rendered != phase2_document:
            errors.append("ledger replay does not equal shipped phase-2 document bytes")
    except (KeyError, TypeError, ValueError) as exc:
        errors.append(str(exc))
    patch_ids = [p.get("change_id") for p in patches]
    if len(patch_ids) != len(set(patch_ids)):
        errors.append("child patch change_ids are not unique")
    if Counter(patch_ids) != Counter(rendered_change_ids):
        errors.append("rendered blocks and child patches are not exact 1:1")
    parents = {e.get("event_id"): e for e in turn_events.get("events", [])}
    for patch in patches:
        parent = parents.get(patch.get("event_id"))
        if not parent or parent.get("event_type") != patch.get("event_type"):
            errors.append(f"{patch.get('change_id')} has invalid child-to-parent event mapping")
        triple = (patch.get("event_type"), patch.get("child_role"), patch.get("origin"))
        if triple not in LEGAL_TRANSITION_TRIPLES:
            errors.append(f"{patch.get('change_id')} unlisted transition tuple {triple}")
        elif patch.get("transition_row_id") != LEGAL_TRANSITION_TRIPLES[triple]:
            errors.append(f"{patch.get('change_id')} transition_row_id does not match its tuple")
        if reviews_by_change_id is not None:
            review = reviews_by_change_id.get(str(patch.get("change_id")), {})
            has_prior = bool(review.get("prior_position_id"))
            if patch.get("origin") == "prior_position" and not has_prior:
                errors.append(f"{patch.get('change_id')} prior_position requires prior_position_id")
            if patch.get("origin") != "prior_position" and has_prior:
                errors.append(f"{patch.get('change_id')} non-prior origin forbids prior_position_id")
    for event_id, parent in parents.items():
        declared_ids = [c.get("change_id") for c in parent.get("children", [])]
        ledger_ids = [p.get("change_id") for p in patches if p.get("event_id") == event_id]
        if Counter(declared_ids) != Counter(ledger_ids):
            errors.append(f"{event_id} parent children do not exactly match ledger child mapping")
        if parent.get("event_type") == "sneaky_reinsert" and Counter(
            c.get("child_role") for c in parent.get("children", [])
        ) != Counter(("source_cleanup", "inserted_effect")):
            errors.append(f"{event_id} sneaky parent must own source_cleanup and inserted_effect children")
    counts = turn_events.get("expected_child_counts", {})
    total = len(patches)
    if total == 7 or counts.get("total") == 7:
        errors.append("7-child fixture invalid: would require only four of five seeded deviations to receive a response")
    if total not in (8, 9):
        errors.append(f"expected exactly 8 canonical or 9 expanded children, found {total}")
    origin_counts = Counter(p.get("origin") for p in patches)
    expected_origins = {8: (6, 1, 1), 9: (7, 1, 1)}.get(total)
    if expected_origins and (origin_counts["prior_position"], origin_counts["novel_insertion"], origin_counts["canary_probe"]) != expected_origins:
        errors.append(f"origin counts do not match v4 C{total} accounting {expected_origins}")
    type_counts = Counter(p.get("event_type") for p in patches)
    role_counts = Counter((p.get("event_type"), p.get("child_role")) for p in patches)
    counter_n = type_counts["counter_proposal"]
    valid_shape = (total == 8 and type_counts["concession"] == 1 and type_counts["regression"] == 1
                   and role_counts[("sneaky_reinsert", "source_cleanup")] == 1
                   and role_counts[("sneaky_reinsert", "inserted_effect")] == 1 and counter_n == 2
                   and type_counts["new_deviation"] == 1 and type_counts["benign_canary_change"] == 1)
    valid_shape |= (total == 9 and type_counts["concession"] == 1 and type_counts["regression"] == 1
                    and role_counts[("sneaky_reinsert", "source_cleanup")] == 2
                    and role_counts[("sneaky_reinsert", "inserted_effect")] == 2 and counter_n == 1
                    and type_counts["new_deviation"] == 1 and type_counts["benign_canary_change"] == 1)
    if total in (8, 9) and not valid_shape:
        errors.append(f"C{total} child composition does not match v4 §1.5")
    harmful = sum(p.get("expected_disposition") == "reject" for p in patches)
    declared = (counts.get("total"), counts.get("harmful"), counts.get("benign"), counts.get("prior"), counts.get("novel"), counts.get("canary"))
    actual = (total, harmful, total - harmful, origin_counts["prior_position"], origin_counts["novel_insertion"], origin_counts["canary_probe"])
    if declared != actual:
        errors.append(f"expected_child_counts {declared} does not equal actual {actual}")
    if card_changes is not None and reviews_by_change_id is not None:
        card_map = {c.get("change_id"): c for c in card_changes}
        if card_map != dict(reviews_by_change_id):
            errors.append("interactive review_change map and card changes are not exactly equal")
    return _result("V14", "T2-N ledger replay and child accounting", errors)


def v9_ext_t2n_canary_turn_events(turn_events: Mapping[str, Any], canary_rule_ids: set[str]) -> ValidationResult:
    """Extend V9 over T2-N turn truth (v3 §7)."""
    errors: list[str] = []
    canary_children = []
    for event in turn_events.get("events", []):
        for child in event.get("children", []):
            if child.get("rule_id") in canary_rule_ids and child.get("expected_disposition") == "reject":
                errors.append(f"canary rule {child.get('rule_id')} owns harmful change {child.get('change_id')}")
            if event.get("event_type") == "benign_canary_change":
                canary_children.append(child)
    if len(canary_children) != 1:
        errors.append(f"mixed task requires exactly one benign canary child, found {len(canary_children)}")
    elif canary_children[0].get("origin") != "canary_probe" or canary_children[0].get("expected_disposition") != "accept":
        errors.append("benign canary child must be canary_probe/accept")
    return _result("V9-T2N", "canary turn-event integrity", errors)


def v10_t2n_forbidden_fields(records: Sequence[Mapping[str, Any]]) -> ValidationResult:
    """Executable v4 §1.6 item 1."""
    errors = []
    for i, record in enumerate(records):
        public_id = str(record.get("public_task_id", ""))
        for field in FORBIDDEN_LEAKAGE_FIELDS:
            if field in record.get("observation", {}) or field in public_id.lower():
                errors.append(f"record {i} exposes forbidden field {field}")
    return _result("V10-T2N-1", "forbidden observation fields", errors)


def _balanced_accuracy(labels: list[str], predictions: list[str]) -> float:
    classes = sorted(set(labels))
    return sum(sum(y == c and p == c for y, p in zip(labels, predictions)) / sum(y == c for y in labels) for c in classes) / len(classes)


def v10_t2n_lookup_classifiers(tranches: Sequence[Sequence[Mapping[str, Any]]],
                               features: Sequence[str]) -> ValidationResult:
    """Three-tranche lookup/one held-out execution of v4 §1.6 item 2."""
    if len(tranches) < 4:
        return ValidationResult("V10-T2N-2", "one-level lookup classifiers", "STUBBED", "insufficient data: requires at least four independently seeded tranches")
    errors = []
    for heldout_i in range(len(tranches)):
        train = [r for i, t in enumerate(tranches) if i != heldout_i for r in t]
        heldout = list(tranches[heldout_i])
        for feature in features:
            cells: dict[Any, Counter[str]] = defaultdict(Counter)
            for r in train: cells[r.get(feature)][str(r["label"])] += 1
            for value, counts in cells.items():
                if sum(counts.values()) >= 4 and len(counts) < 2:
                    errors.append(f"{feature} cell {value!r} size>=4 lacks both labels")
            global_label = Counter(str(r["label"]) for r in train).most_common(1)[0][0]
            pred = [cells[r.get(feature)].most_common(1)[0][0] if cells[r.get(feature)] else global_label for r in heldout]
            score = _balanced_accuracy([str(r["label"]) for r in heldout], pred)
            if score >= .60: errors.append(f"{feature} heldout {heldout_i} balanced accuracy {score:.3f} >=0.60")
    return _result("V10-T2N-2", "one-level lookup classifiers", errors)


def _mutual_information(xs: Sequence[Any], ys: Sequence[Any]) -> float:
    n = len(xs); cx, cy, joint = Counter(xs), Counter(ys), Counter(zip(xs, ys))
    return sum(v / n * log((v * n) / (cx[x] * cy[y])) for (x, y), v in joint.items())


def v10_t2n_permutation_mi(records: Sequence[Mapping[str, Any]], features: Sequence[str],
                           *, permutations: int = 10_000, seed: int = 0) -> ValidationResult:
    """Permutation MI with Holm correction and NMI<.05 (v4 §1.6 item 3)."""
    if len(records) < 56:
        return ValidationResult("V10-T2N-3", "permutation mutual information", "STUBBED", "insufficient data: requires at least 28 records per label")
    labels = [str(r["label"]) for r in records]
    if min(Counter(labels).values()) < 28:
        return ValidationResult("V10-T2N-3", "permutation mutual information", "STUBBED", "insufficient data: requires at least 28 records per label")
    rng = random.Random(seed); results = []
    hy = _mutual_information(labels, labels)
    for feature in features:
        xs = [r.get(feature) for r in records]
        observed = _mutual_information(xs, labels)
        exceed = 0
        perm = labels.copy()
        for _ in range(permutations):
            rng.shuffle(perm)
            exceed += _mutual_information(xs, perm) >= observed
        results.append((feature, (exceed + 1) / (permutations + 1), 0.0 if hy == 0 else observed / hy))
    errors = []
    running_adjusted = 0.0
    for rank, (feature, p, nmi) in enumerate(sorted(results, key=lambda x: x[1])):
        running_adjusted = max(running_adjusted, min(1.0, (len(results) - rank) * p))
        if running_adjusted < .05: errors.append(f"{feature} Holm-corrected p={running_adjusted:.6f} < 0.05")
        if nmi >= .05: errors.append(f"{feature} normalized MI {nmi:.6f} >=0.05")
    return _result("V10-T2N-3", "permutation mutual information", errors)


def v10_t2n_quota_batch_attacker(*_: Any, **__: Any) -> ValidationResult:
    """v4 §1.6 item 4 needs the later observation-serving/env integration."""
    raise NotImplementedError("v4 §1.6 item 4 quota-constrained batch attacker requires the env observation-serving integration step")


def v10_t2n_fresh_process_isolation() -> ValidationResult:
    """Fresh-process sentinel state unit test (v4 §1.6 item 5)."""
    key = "_T2N_SENTINEL_STATE"
    writer = f"import builtins; builtins.{key}='secret'"
    reader = f"import builtins,sys; sys.exit(1 if hasattr(builtins,'{key}') else 0)"
    first = subprocess.run([sys.executable, "-c", writer], check=False)
    second = subprocess.run([sys.executable, "-c", reader], check=False)
    return _result("V10-T2N-5", "fresh-process isolation", [] if first.returncode == second.returncode == 0 else ["sentinel state crossed process boundary"])


def run_all_t2n(task_dir: Path) -> list[ValidationResult]:
    """Load only new T2-N artifacts; never invoked by the legacy registry."""
    task_dir = Path(task_dir)
    ledger = json.loads((task_dir / "patch_ledger.json").read_text())
    events = json.loads((task_dir / "turn_events.json").read_text())
    canonical = (task_dir / "phase1_document.txt").read_bytes()
    phase2 = (task_dir / "phase2_document.txt").read_bytes()
    rendered = json.loads((task_dir / "rendered_change_ids.json").read_text())
    reviews_path = task_dir / "reviews_by_change_id.json"
    card_path = task_dir / "card_t2n.json"
    reviews = json.loads(reviews_path.read_text()) if reviews_path.exists() else None
    card_changes = json.loads(card_path.read_text()).get("changes", []) if card_path.exists() else None
    schema_errors = []
    for name, instance in (("patch_ledger", ledger), ("turn_events", events)):
        schema = json.loads((T2N_SCHEMA_DIR / f"{name}.schema.json").read_text())
        schema_errors.extend(f"{name}: {e.message}" for e in Draft202012Validator(schema).iter_errors(instance))
    schema_result = _result("V8-T2N", "T2-N artifact schemas", schema_errors)
    return [schema_result, v14_t2n_ledger(canonical_document=canonical, phase2_document=phase2,
                                         ledger=ledger, turn_events=events, rendered_change_ids=rendered,
                                         reviews_by_change_id=reviews, card_changes=card_changes)]
