"""Deterministic five-child all-concessions T2-N fixture generator."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from generator.t2n_response import (
    ROOT, ResponseGenerationError, _answer_actions, _derive_canonical, _deviation_anchor,
    _dump_json, _load_json, _paragraphs, _prior_replace, _tracked_markdown, _turn_events,
)
from scoring.t2n_contract import CONTRACT_ID
from validators.t2n_checks import replay_ledger


def generate_all_concessions(instance_dir: Path, seed: int, out_dir: Path) -> list[str]:
    """Write deterministic TR-01 responses for every planted deviation.

    ``seed`` is intentionally accepted for a parallel, stable interface even
    though the all-concession construction has no random choices.
    """
    del seed
    instance_dir, out_dir = Path(instance_dir).resolve(), Path(out_dir).resolve()
    manifest = _load_json(instance_dir / "documents_manifest.json")
    planted = _load_json(instance_dir / "planted_deviations.json")
    deviations = sorted(planted.get("deviations", []), key=lambda d: d["deviation_id"])
    if len(deviations) != 5:
        raise ResponseGenerationError(f"T2-N all-concessions requires exactly five seeded deviations, found {len(deviations)}")
    if any(d.get("expected_action") != "redline_with_fallback" or not d.get("expected_redline_text") for d in deviations):
        raise ResponseGenerationError("all five seeded deviations must carry redline_with_fallback answer-key text")
    documents = manifest.get("documents", [])
    if len(documents) != 1:
        raise ResponseGenerationError(f"T2-N requires one canonical document, found {len(documents)}")
    canonical_text = _derive_canonical((instance_dir / documents[0]["path"]).read_text(encoding="utf-8"), deviations)
    canonical = canonical_text.encode("utf-8")
    paragraphs = _paragraphs(canonical_text)
    patches: list[dict[str, Any]] = []
    for ordinal, deviation in enumerate(deviations, 1):
        anchor = _deviation_anchor(canonical_text, canonical, paragraphs, deviation)
        patches.append(_prior_replace(
            canonical, deviation, anchor, event_id=f"EV-CONCESSION-{ordinal}",
            change_id=f"CH-CONCESSION-{ordinal}", event_type="concession", child_role="sole",
            after_text=deviation["expected_redline_text"] + " The counterparty confirms that this requirement is accepted without qualification.",
            disposition="accept", transition="TR-01", edit_required=False,
        ))
    patches.sort(key=lambda p: (p["start_offset"], p["end_offset"], p["change_id"]))
    ledger = {"contract_id": CONTRACT_ID, "patches": patches}
    events = _turn_events(patches, {})  # telemetry only: mixed event schema intentionally does not apply.
    reviews, card = _answer_actions(patches)
    schemas = ROOT / "schema" / "t2n"
    for name, instance in (("patch_ledger", ledger), ("card_t2n", card)):
        errors = list(Draft202012Validator(_load_json(schemas / f"{name}.schema.json")).iter_errors(instance))
        if errors: raise ResponseGenerationError(f"{name} schema failure: " + "; ".join(e.message for e in errors))
    review_schema = Draft202012Validator(_load_json(schemas / "review_action.schema.json"))
    errors = [f"{key}: {e.message}" for key, action in reviews.items() for e in review_schema.iter_errors(action)]
    if errors: raise ResponseGenerationError("review action schema failure: " + "; ".join(errors))
    phase2 = replay_ledger(canonical, patches)
    out_dir.mkdir(parents=True, exist_ok=True)
    _dump_json(out_dir / "patch_ledger.json", ledger); _dump_json(out_dir / "turn_events.json", events)
    (out_dir / "phase1_document.txt").write_bytes(canonical); (out_dir / "phase2_document.txt").write_bytes(phase2)
    _dump_json(out_dir / "rendered_change_ids.json", [p["change_id"] for p in patches])
    _dump_json(out_dir / "reviews_by_change_id.json", reviews); _dump_json(out_dir / "card_t2n.json", card)
    (out_dir / "phase2_tracked_changes.md").write_text(_tracked_markdown(canonical, patches), encoding="utf-8")
    return [f"Generated all-concessions T2-N fixture at {out_dir}", "Children: 5 concessions"]
