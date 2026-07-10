from __future__ import annotations

import argparse
from collections import OrderedDict
import hashlib
import json
from pathlib import Path
import random
import re
import sys
from typing import Any, Iterable, Mapping

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
if __package__ in {None, ""}:
    sys.path.insert(0, str(ROOT))

from scoring.t2n_contract import CONTRACT_ID, validate_counter_family
from validators.t2n_checks import replay_ledger, run_all_t2n, v9_ext_t2n_canary_turn_events


SCHEMA_DIR = ROOT / "schema" / "t2n"


class ResponseGenerationError(RuntimeError):
    pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a deterministic T2-N response layer.")
    parser.add_argument("--instance", type=Path, required=True, help="Existing seeded T2 instance directory")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--families", type=Path, required=True, help="T2-N area family JSON")
    parser.add_argument("--out", type=Path, required=True, help="Output T2-N fixture directory")
    args = parser.parse_args(argv)
    try:
        summary = generate_response(args.instance, args.seed, args.families, args.out)
    except ResponseGenerationError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 1
    for line in summary:
        print(line)
    return 0


def generate_response(
    instance_dir: Path,
    seed: int,
    family_file: Path,
    out_dir: Path,
) -> list[str]:
    """Create the v4 canonical eight-child response fixture.

    All selection uses one ``random.Random(seed)`` instance. Ledger offsets are
    UTF-8 byte offsets into the mechanically accepted phase-1 document.
    """
    instance_dir = Path(instance_dir).resolve()
    family_file = Path(family_file).resolve()
    out_dir = Path(out_dir).resolve()
    rng = random.Random(seed)

    task = _load_json(instance_dir / "task.json")
    manifest = _load_json(instance_dir / "documents_manifest.json")
    planted = _load_json(instance_dir / "planted_deviations.json")
    deviations = sorted(planted.get("deviations", []), key=lambda d: d["deviation_id"])
    if len(deviations) != 5:
        raise ResponseGenerationError(f"T2-N canonical response requires exactly five seeded deviations, found {len(deviations)}")
    if any(d.get("expected_action") != "redline_with_fallback" or not d.get("expected_redline_text") for d in deviations):
        raise ResponseGenerationError("all five seeded deviations must carry redline_with_fallback answer-key text")

    documents = manifest.get("documents", [])
    if len(documents) != 1:
        raise ResponseGenerationError(f"T2-N requires one canonical document, found {len(documents)}")
    document_record = documents[0]
    seeded_path = instance_dir / document_record["path"]
    canonical_text = _derive_canonical(seeded_path.read_text(encoding="utf-8"), deviations)
    canonical = canonical_text.encode("utf-8")
    paragraphs = _paragraphs(canonical_text)

    playbook_path = ROOT / task["playbook_ref"]
    playbook = _load_json(playbook_path)
    playbook_id = playbook["playbook_id"]
    family_data = _load_json(family_file)
    if family_data.get("_status") != "machine-drafted v2, model-reviewed (gpt-5.6-sol), line-item reviewed 2026-07-10 (claude-sonnet, review delegated by owner)":
        raise ResponseGenerationError("family file is missing the required machine-drafted signing-gate status")
    try:
        bundle = family_data[playbook_id]
    except KeyError as exc:
        raise ResponseGenerationError(f"family file does not cover {playbook_id}") from exc
    families = sorted(bundle.get("counter_families", []), key=lambda f: f["counter_family_id"])
    for family in families:
        errors = validate_counter_family(family)
        if errors:
            raise ResponseGenerationError(f"counter family {family.get('counter_family_id')} invalid: {'; '.join(errors)}")

    rule_by_id = {rule["rule_id"]: rule for rule in playbook.get("rules", [])}
    canary_rule_ids = {rule_id for rule_id, rule in rule_by_id.items() if rule.get("is_canary") is True}
    # family_design_v2 §6: choose within each matching rule before choosing two
    # distinct seeded deviations.  The old sorted-first walk made later family
    # variants unreachable and prevented a meaningful family-held-out split.
    distinct: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for deviation in deviations:
        candidates = [family for family in families if family["rule_id"] == deviation["rule_id"]]
        if candidates:
            distinct.append((rng.choice(candidates), deviation))
    if len(distinct) < 2:
        raise ResponseGenerationError(
            f"{playbook_id} needs two different counter families matching two of the five seeded rules; found {len(distinct)}"
        )
    rng.shuffle(distinct)
    counter_assignments = distinct[:2]
    counter_classes = ["acceptable", "unacceptable"]
    rng.shuffle(counter_classes)

    response_deviations = [d for d in deviations if d["deviation_id"] not in {x[1]["deviation_id"] for x in counter_assignments}]
    rng.shuffle(response_deviations)
    concession_dev, regression_dev, sneak_dev = response_deviations
    deviation_anchors = {d["deviation_id"]: _deviation_anchor(canonical_text, canonical, paragraphs, d) for d in deviations}

    patches: list[dict[str, Any]] = []
    event_inputs: dict[str, dict[str, Any]] = {}

    concession_after = concession_dev["expected_redline_text"] + " The counterparty confirms that this requirement is accepted without qualification."
    patches.append(_prior_replace(
        canonical, concession_dev, deviation_anchors[concession_dev["deviation_id"]],
        event_id="EV-CONCESSION", change_id="CH-CONCESSION", event_type="concession",
        child_role="sole", after_text=concession_after, disposition="accept", transition="TR-01",
        edit_required=False,
    ))

    patches.append(_prior_replace(
        canonical, regression_dev, deviation_anchors[regression_dev["deviation_id"]],
        event_id="EV-REGRESSION", change_id="CH-REGRESSION", event_type="regression",
        child_role="sole", after_text=regression_dev["mutated_text"], disposition="reject", transition="TR-02",
        edit_required=True, expected_redline_text=regression_dev["expected_redline_text"],
    ))

    sneak_source_anchor = deviation_anchors[sneak_dev["deviation_id"]]
    patches.append(_prior_replace(
        canonical, sneak_dev, sneak_source_anchor,
        event_id="EV-SNEAK", change_id="CH-SNEAK-SOURCE", event_type="sneaky_reinsert",
        child_role="source_cleanup", after_text=sneak_dev["expected_redline_text"], disposition="accept",
        transition="TR-03", edit_required=False,
    ))
    destination_candidates = [
        deviation_anchors[d["deviation_id"]]
        for d in deviations
        if d["deviation_id"] != sneak_dev["deviation_id"]
    ]
    sneak_destination = _choose_sneak_destination(sneak_dev, destination_candidates, rng)
    adapted_harm = _adapt_sneak_language(sneak_dev["mutated_text"], sneak_dev["expected_redline_text"], sneak_destination.text)
    sneak_insert = "\n\nFor purposes of this clause, the following additional term applies: " + adapted_harm
    patches.append(_prior_insert(
        canonical, sneak_dev, sneak_source_anchor, sneak_destination,
        event_id="EV-SNEAK", change_id="CH-SNEAK-INSERTED", after_text=sneak_insert,
    ))

    # One private pool index is shared by the AU pair. This couples only the
    # nuisance route/decoy draw, never either label, and makes a task contribute
    # matched marginal mass to both classes. The prose variant still varies by
    # seed because the index is drawn from the episode RNG.
    render_pool_index = rng.randrange(min(
        len(family["render_pools"][counter_class])
        for (family, _), counter_class in zip(counter_assignments, counter_classes)
    ))
    for index, ((family, deviation), counter_class) in enumerate(zip(counter_assignments, counter_classes), start=1):
        pool = family["render_pools"][counter_class]
        render = pool[render_pool_index % len(pool)]
        event_id = f"EV-COUNTER-{index}"
        patch = _prior_replace(
            canonical, deviation, deviation_anchors[deviation["deviation_id"]],
            event_id=event_id, change_id=f"CH-COUNTER-{index}", event_type="counter_proposal",
            child_role="sole", after_text=render["text"],
            disposition="accept" if counter_class == "acceptable" else "reject", transition="TR-05",
            edit_required=counter_class == "unacceptable", expected_redline_text=family["expected_redline_text"] if counter_class == "unacceptable" else None,
            counter_family=family, counter_class=counter_class,
        )
        patches.append(patch)
        event_inputs[event_id] = {
            "counter_family_id": family["counter_family_id"],
            "counter_class": counter_class,
            "counter_text_slots": render["counter_text_slots"],
            "phase1_context_slots": render["phase1_context_slots"],
            "decoy_values": render["decoy_values"],
        }

    insertion_points = {p["start_offset"] for p in patches if p["op"] in {"insert_before", "insert_after"}}
    novel_template = _choose_template(bundle.get("novel_deviation_templates", []), rule_by_id, rng, "novel deviation")
    novel_destination = _find_template_anchor(paragraphs, novel_template.get("destination_terms", []), insertion_points)
    novel_insert = "\n\n" + novel_template["text"]
    patches.append(_nonprior_insert(
        canonical, novel_destination, event_id="EV-NEW-DEVIATION", change_id="CH-NEW-DEVIATION",
        event_type="new_deviation", origin="novel_insertion", after_text=novel_insert,
        disposition="reject", rule_id=novel_template["rule_id"], transition="TR-06", edit_required=True,
        expected_redline_text=rule_by_id[novel_template["rule_id"]]["fallback"],
    ))
    insertion_points.add(novel_destination.end_byte)

    canary_templates = [t for t in bundle.get("benign_change_templates", []) if t.get("rule_id") in canary_rule_ids]
    canary_template = _choose_template(canary_templates, rule_by_id, rng, "benign canary")
    if canary_template.get("anchor_text"):
        canary_anchor = _text_anchor(canonical_text, canonical, paragraphs, canary_template["anchor_text"])
        canary_after = canary_anchor.text + " " + canary_template["text"]
        patches.append(_nonprior_replace(
            canonical, canary_anchor, event_id="EV-CANARY", change_id="CH-CANARY",
            event_type="benign_canary_change", origin="canary_probe", after_text=canary_after,
            disposition="accept", rule_id=canary_template["rule_id"], transition="TR-07", edit_required=False,
        ))
    else:
        canary_destination = _find_template_anchor(paragraphs, canary_template.get("anchor_terms", []), insertion_points)
        canary_insert = "\n\n" + canary_template["text"]
        patches.append(_nonprior_insert(
            canonical, canary_destination, event_id="EV-CANARY", change_id="CH-CANARY",
            event_type="benign_canary_change", origin="canary_probe", after_text=canary_insert,
            disposition="accept", rule_id=canary_template["rule_id"], transition="TR-07", edit_required=False,
        ))

    patches.sort(key=lambda p: (p["start_offset"], p["end_offset"], p["change_id"]))
    ledger = {"contract_id": CONTRACT_ID, "patches": patches}
    turn_events = _turn_events(patches, event_inputs)
    rendered_change_ids = [patch["change_id"] for patch in patches]
    phase2 = replay_ledger(canonical, patches)
    reviews, card = _answer_actions(patches)

    _validate_schema("patch_ledger", ledger)
    _validate_schema("turn_events", turn_events)
    _validate_schema("card_t2n", card)
    action_schema = _load_json(SCHEMA_DIR / "review_action.schema.json")
    action_errors = [
        f"{change_id}: {error.message}"
        for change_id, action in reviews.items()
        for error in Draft202012Validator(action_schema).iter_errors(action)
    ]
    if action_errors:
        raise ResponseGenerationError("review action schema failure: " + "; ".join(action_errors))

    out_dir.mkdir(parents=True, exist_ok=True)
    _dump_json(out_dir / "patch_ledger.json", ledger)
    _dump_json(out_dir / "turn_events.json", turn_events)
    (out_dir / "phase1_document.txt").write_bytes(canonical)
    (out_dir / "phase2_document.txt").write_bytes(phase2)
    _dump_json(out_dir / "rendered_change_ids.json", rendered_change_ids)
    _dump_json(out_dir / "reviews_by_change_id.json", reviews)
    _dump_json(out_dir / "card_t2n.json", card)
    (out_dir / "phase2_tracked_changes.md").write_text(_tracked_markdown(canonical, patches), encoding="utf-8")

    results = run_all_t2n(out_dir)
    canary_result = v9_ext_t2n_canary_turn_events(turn_events, canary_rule_ids)
    failures = [result for result in [*results, canary_result] if result.status != "PASS"]
    if failures:
        detail = "; ".join(f"{result.code}: {result.detail}" for result in failures)
        raise ResponseGenerationError(f"generated fixture failed validation: {detail}")
    return [
        f"Generated canonical C8-AU T2-N fixture at {out_dir}",
        f"Base: {task['task_id']} ({playbook_id}); seed={seed}",
        "Children: 8 (prior=6, novel=1, canary=1; harmful=4, benign=4)",
        "Validators: " + ", ".join(f"{result.code}={result.status}" for result in [*results, canary_result]),
    ]


class _Paragraph:
    def __init__(self, section: str, ordinal: int, text: str, start_char: int, end_char: int, full_text: str):
        self.section = section
        self.ordinal = ordinal
        self.text = text
        self.start_char = start_char
        self.end_char = end_char
        self.start_byte = len(full_text[:start_char].encode("utf-8"))
        self.end_byte = len(full_text[:end_char].encode("utf-8"))

    @property
    def clause_id(self) -> str:
        return f"{self.section}:p{self.ordinal}"


class _Anchor:
    def __init__(self, paragraph: _Paragraph, start_byte: int, end_byte: int, text: str):
        self.paragraph = paragraph
        self.start_byte = start_byte
        self.end_byte = end_byte
        self.text = text

    @property
    def section(self) -> str:
        return self.paragraph.section

    @property
    def clause_id(self) -> str:
        return self.paragraph.clause_id


def _derive_canonical(seeded_text: str, deviations: Iterable[Mapping[str, Any]]) -> str:
    canonical = seeded_text
    for deviation in deviations:
        mutated = deviation["mutated_text"]
        count = canonical.count(mutated)
        if count != 1:
            raise ResponseGenerationError(
                f"{deviation['deviation_id']} mutated_text must appear exactly once while deriving phase 1; found {count}"
            )
        canonical = canonical.replace(mutated, deviation["expected_redline_text"], 1)
    return canonical


def _paragraphs(text: str) -> list[_Paragraph]:
    paragraphs: list[_Paragraph] = []
    section = "0"
    ordinals: dict[str, int] = {}
    position = 0
    for line in text.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        heading = re.match(r"^##\s+([0-9]+)\.\s+", content)
        if heading:
            section = heading.group(1)
        elif content.strip() and not content.startswith("#"):
            ordinals[section] = ordinals.get(section, 0) + 1
            paragraphs.append(_Paragraph(section, ordinals[section], content, position, position + len(content), text))
        position += len(line)
    if not paragraphs:
        raise ResponseGenerationError("canonical document contains no paragraphs")
    return paragraphs


def _deviation_anchor(text: str, canonical: bytes, paragraphs: list[_Paragraph], deviation: Mapping[str, Any]) -> _Anchor:
    span = deviation["expected_redline_text"]
    if text.count(span) != 1:
        raise ResponseGenerationError(f"{deviation['deviation_id']} expected redline span must appear exactly once in canonical phase 1")
    start_char = text.index(span)
    end_char = start_char + len(span)
    paragraph = next((p for p in paragraphs if p.start_char <= start_char and end_char <= p.end_char), None)
    if paragraph is None:
        raise ResponseGenerationError(f"{deviation['deviation_id']} expected redline span crosses a paragraph boundary")
    if paragraph.section != str(deviation["clause_anchor"]["section"]):
        raise ResponseGenerationError(f"{deviation['deviation_id']} canonical section does not match planted clause anchor")
    start_byte = len(text[:start_char].encode("utf-8"))
    end_byte = len(text[:end_char].encode("utf-8"))
    if canonical[start_byte:end_byte] != span.encode("utf-8"):
        raise ResponseGenerationError(f"{deviation['deviation_id']} UTF-8 byte offset derivation failed")
    return _Anchor(paragraph, start_byte, end_byte, span)


def _text_anchor(text: str, canonical: bytes, paragraphs: list[_Paragraph], span: str) -> _Anchor:
    if text.count(span) != 1:
        raise ResponseGenerationError(f"template anchor_text must appear exactly once in canonical phase 1; found {text.count(span)}")
    start_char = text.index(span)
    end_char = start_char + len(span)
    paragraph = next((p for p in paragraphs if p.start_char <= start_char and end_char <= p.end_char), None)
    if paragraph is None:
        raise ResponseGenerationError("template anchor_text crosses a paragraph boundary")
    start_byte = len(text[:start_char].encode("utf-8"))
    end_byte = len(text[:end_char].encode("utf-8"))
    if canonical[start_byte:end_byte] != span.encode("utf-8"):
        raise ResponseGenerationError("template anchor_text UTF-8 byte offset derivation failed")
    return _Anchor(paragraph, start_byte, end_byte, span)


def _base_patch(canonical: bytes, *, change_id: str, event_id: str, event_type: str, child_role: str,
                origin: str, op: str, start: int, end: int, before: str, after: str,
                disposition: str, rule_id: str, clause_id: str, section: str,
                transition: str, edit_required: bool, expected_redline_text: str | None = None) -> dict[str, Any]:
    patch: dict[str, Any] = {
        "change_id": change_id, "event_id": event_id, "event_type": event_type,
        "child_role": child_role, "origin": origin, "op": op,
        "precondition_sha256": hashlib.sha256(canonical[start:end]).hexdigest(),
        "doc_id": "DOC-01", "section_ref": section, "start_offset": start, "end_offset": end,
        "before_text": before, "after_text": after, "expected_disposition": disposition,
        "expected_rule_id": rule_id, "expected_clause_id": clause_id,
        "ground_span": after, "edit_required": edit_required, "transition_row_id": transition,
    }
    if expected_redline_text:
        patch["expected_redline_text"] = expected_redline_text
    return patch


def _plant_position(deviation: Mapping[str, Any], source: _Anchor, comparator: str | None = None) -> dict[str, Any]:
    plant = {
        "source_deviation_id": deviation["deviation_id"], "phase1_decision": "reject",
        "rule_id": deviation["rule_id"], "clause_id": source.clause_id,
        "fallback_text": deviation["expected_redline_text"],
    }
    if comparator is not None:
        plant["comparator_record_id"] = comparator
    return plant


def _prior_replace(canonical: bytes, deviation: Mapping[str, Any], anchor: _Anchor, *, event_id: str,
                   change_id: str, event_type: str, child_role: str, after_text: str,
                   disposition: str, transition: str, edit_required: bool,
                   expected_redline_text: str | None = None,
                   counter_family: Mapping[str, Any] | None = None,
                   counter_class: str | None = None) -> dict[str, Any]:
    patch = _base_patch(
        canonical, change_id=change_id, event_id=event_id, event_type=event_type, child_role=child_role,
        origin="prior_position", op="replace", start=anchor.start_byte, end=anchor.end_byte,
        before=anchor.text, after=after_text, disposition=disposition, rule_id=deviation["rule_id"],
        clause_id=anchor.clause_id, section=anchor.section, transition=transition,
        edit_required=edit_required, expected_redline_text=expected_redline_text,
    )
    comparator = counter_family["counter_guard_id"] if counter_family else None
    patch.update({
        "source_clause_id": anchor.clause_id,
        "prior_source_deviation_id": deviation["deviation_id"],
        "plant_position": _plant_position(deviation, anchor, comparator),
    })
    if counter_family:
        patch.update({
            "counter_family_id": counter_family["counter_family_id"],
            "counter_class": counter_class,
            "counter_guard_id": counter_family["counter_guard_id"],
        })
    return patch


def _prior_insert(canonical: bytes, deviation: Mapping[str, Any], source: _Anchor, destination: _Anchor,
                  *, event_id: str, change_id: str, after_text: str) -> dict[str, Any]:
    patch = _base_patch(
        canonical, change_id=change_id, event_id=event_id, event_type="sneaky_reinsert",
        child_role="inserted_effect", origin="prior_position", op="insert_after",
        start=destination.paragraph.end_byte, end=destination.paragraph.end_byte, before="", after=after_text,
        disposition="reject", rule_id=deviation["rule_id"], clause_id=destination.clause_id,
        section=destination.section, transition="TR-04", edit_required=True,
        expected_redline_text=deviation["expected_redline_text"],
    )
    patch.update({
        "source_clause_id": source.clause_id,
        "prior_source_deviation_id": deviation["deviation_id"],
        "plant_position": _plant_position(deviation, source),
    })
    return patch


def _nonprior_insert(canonical: bytes, destination: _Paragraph, *, event_id: str, change_id: str,
                     event_type: str, origin: str, after_text: str, disposition: str, rule_id: str,
                     transition: str, edit_required: bool, expected_redline_text: str | None = None) -> dict[str, Any]:
    return _base_patch(
        canonical, change_id=change_id, event_id=event_id, event_type=event_type, child_role="sole",
        origin=origin, op="insert_after", start=destination.end_byte, end=destination.end_byte,
        before="", after=after_text, disposition=disposition, rule_id=rule_id,
        clause_id=destination.clause_id, section=destination.section, transition=transition,
        edit_required=edit_required, expected_redline_text=expected_redline_text,
    )


def _nonprior_replace(canonical: bytes, anchor: _Anchor, *, event_id: str, change_id: str,
                      event_type: str, origin: str, after_text: str, disposition: str, rule_id: str,
                      transition: str, edit_required: bool) -> dict[str, Any]:
    return _base_patch(
        canonical, change_id=change_id, event_id=event_id, event_type=event_type, child_role="sole",
        origin=origin, op="replace", start=anchor.start_byte, end=anchor.end_byte,
        before=anchor.text, after=after_text, disposition=disposition, rule_id=rule_id,
        clause_id=anchor.clause_id, section=anchor.section, transition=transition,
        edit_required=edit_required,
    )


def _subject(text: str) -> str | None:
    match = re.match(r"^(Each party|Vendor|Customer|Custodian|Recipient|Executive|Company|Buyer|Seller)\b", text)
    return match.group(1) if match else None


def _choose_sneak_destination(deviation: Mapping[str, Any], candidates: list[_Anchor], rng: random.Random) -> _Anchor:
    source_subject = _subject(deviation["mutated_text"]) or _subject(deviation["expected_redline_text"])
    scored = []
    for candidate in candidates:
        destination_subject = _subject(candidate.text)
        score = 0 if source_subject and destination_subject == source_subject else 1 if destination_subject else 2
        scored.append((score, candidate.section, candidate.paragraph.ordinal, candidate))
    best = min(item[0] for item in scored)
    bucket = [item[3] for item in sorted(scored, key=lambda item: (item[1], item[2])) if item[0] == best]
    return rng.choice(bucket)


def _adapt_sneak_language(harmful: str, compliant: str, destination_text: str) -> str:
    source_subject = _subject(harmful) or _subject(compliant)
    destination_subject = _subject(destination_text)
    if source_subject and destination_subject and source_subject != destination_subject and harmful.startswith(source_subject):
        harmful = destination_subject + harmful[len(source_subject):]
    return harmful


def _choose_template(templates: list[Mapping[str, Any]], rule_by_id: Mapping[str, Any],
                     rng: random.Random, label: str) -> Mapping[str, Any]:
    eligible = sorted((t for t in templates if t.get("rule_id") in rule_by_id), key=lambda t: t["template_id"])
    if not eligible:
        raise ResponseGenerationError(f"no eligible {label} template")
    return rng.choice(eligible)


def _find_template_anchor(paragraphs: list[_Paragraph], terms: Iterable[str], used_points: set[int]) -> _Paragraph:
    lowered = [str(term).casefold() for term in terms]
    matching = [p for p in paragraphs if all(term in p.text.casefold() for term in lowered) and p.end_byte not in used_points]
    if not matching:
        matching = [p for p in paragraphs if any(term in p.text.casefold() for term in lowered) and p.end_byte not in used_points]
    if not matching:
        matching = [p for p in paragraphs if p.end_byte not in used_points]
    if not matching:
        raise ResponseGenerationError("could not find a non-overlapping insertion anchor")
    return sorted(matching, key=lambda p: (int(p.section), p.ordinal))[0]


def _turn_events(patches: list[Mapping[str, Any]], event_inputs: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    parents: OrderedDict[str, dict[str, Any]] = OrderedDict()
    for patch in patches:
        parent = parents.setdefault(patch["event_id"], {
            "event_id": patch["event_id"], "event_type": patch["event_type"], "children": [],
        })
        parent["children"].append({
            "change_id": patch["change_id"], "child_role": patch["child_role"],
            "origin": patch["origin"], "expected_disposition": patch["expected_disposition"],
            "rule_id": patch["expected_rule_id"],
        })
        if patch["event_id"] in event_inputs:
            parent["counter_inputs"] = dict(event_inputs[patch["event_id"]])
    harmful = sum(p["expected_disposition"] == "reject" for p in patches)
    origins = {origin: sum(p["origin"] == origin for p in patches) for origin in ("prior_position", "novel_insertion", "canary_probe")}
    return {
        "expected_child_counts": {
            "total": len(patches), "harmful": harmful, "benign": len(patches) - harmful,
            "prior": origins["prior_position"], "novel": origins["novel_insertion"], "canary": origins["canary_probe"],
        },
        "events": list(parents.values()),
    }


def _answer_actions(patches: list[Mapping[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    reviews: OrderedDict[str, dict[str, Any]] = OrderedDict()
    for patch in patches:
        action: dict[str, Any] = {
            "action": "review_change", "change_id": patch["change_id"],
            "origin": patch["origin"], "decision": patch["expected_disposition"],
        }
        if patch["origin"] == "prior_position":
            source = patch["prior_source_deviation_id"].replace("-", "")
            action["prior_position_id"] = f"POS-{source}"
        if patch["expected_disposition"] == "reject":
            action.update({"rule_id": patch["expected_rule_id"], "exact_quote": patch["ground_span"]})
            if patch.get("expected_redline_text"):
                action["proposed_redline"] = patch["expected_redline_text"]
        reviews[patch["change_id"]] = action
    card = {"changes": list(reviews.values()), "escalations": [], "summary": "All eight T2-N response children reviewed against the v4 answer key."}
    return dict(reviews), card


def _tracked_markdown(canonical: bytes, patches: list[Mapping[str, Any]]) -> str:
    # Convention: deleted/replaced text is struck through and inserted text is bold;
    # an HTML comment carries the canonical child ID for human inspection.
    cursor = 0
    output: list[str] = []
    for patch in patches:
        start, end = patch["start_offset"], patch["end_offset"]
        output.append(canonical[cursor:start].decode("utf-8"))
        output.append(f"<!-- {patch['change_id']} -->")
        before, after = patch["before_text"], patch["after_text"]
        if patch["op"] == "replace":
            if before == after:
                output.append(f"**[accepted unchanged]** {after}")
            else:
                output.append(f"~~{before}~~ **{after}**")
        elif patch["op"] == "delete":
            output.append(f"~~{before}~~")
        else:
            output.append(f"**{after}**")
        cursor = end
    output.append(canonical[cursor:].decode("utf-8"))
    return "".join(output)


def _validate_schema(name: str, instance: Mapping[str, Any]) -> None:
    schema = _load_json(SCHEMA_DIR / f"{name}.schema.json")
    errors = sorted(Draft202012Validator(schema).iter_errors(instance), key=lambda e: list(e.path))
    if errors:
        raise ResponseGenerationError(f"{name} schema failure: " + "; ".join(error.message for error in errors))


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ResponseGenerationError(f"could not load {path}: {exc}") from exc


def _dump_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
