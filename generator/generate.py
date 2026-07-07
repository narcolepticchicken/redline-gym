from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import re
import shutil
import subprocess
import sys
import tempfile
from string import Formatter
from typing import Any

from baselines import grep_bot
from env import Episode
from validators.checks import run_all, write_report


ROOT = Path(__file__).resolve().parents[1]
GENERATOR_DIR = Path(__file__).resolve().parent
ALLOWED_MECHANISMS = {
    "T1": {"direct_term_swap"},
    "T2": {"direct_term_swap", "cross_ref_override", "defined_term_shift", "omission"},
}
DEVIATION_COUNT = {"T1": 4, "T2": 5}
T2_GREP_RECALL_MAX = 0.2
GREP_GATE_SEED_STEP = 1000
GREP_GATE_MAX_ATTEMPTS = 5


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a Redline Gym task instance.")
    parser.add_argument("--playbook", type=Path, required=True)
    parser.add_argument("--tier", choices=["T1", "T2"], required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        log = generate_instance(args.playbook, args.tier, args.seed, args.out)
    except GenerationError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 1
    for line in log:
        print(line)
    return 0


def generate_instance(playbook_path: Path, tier: str, seed: int, out_dir: Path) -> list[str]:
    playbook_path = _repo_path(playbook_path)
    out_dir = _repo_path(out_dir)
    playbook = _load_json(playbook_path)
    playbook_id = playbook["playbook_id"]
    base = _load_json(GENERATOR_DIR / "bases" / f"{playbook_id}.json")
    recipe_book = _load_json(GENERATOR_DIR / "recipes" / f"{playbook_id}.json")
    attempts = GREP_GATE_MAX_ATTEMPTS if tier == "T2" else 1
    grep_logs: list[str] = []
    last_leaking_rules: list[str] = []

    for attempt_index in range(attempts):
        attempt_seed = seed + attempt_index * GREP_GATE_SEED_STEP
        try:
            deviations, grep_result, coherence_detail = _generate_candidate(
                playbook_path=playbook_path,
                playbook=playbook,
                base=base,
                recipe_entries=recipe_book["entries"],
                tier=tier,
                seed=seed,
                attempt_seed=attempt_seed,
                out_dir=out_dir,
            )
        except GrepGateError as exc:
            grep_logs.append(
                f"grep_bot attempt_seed={attempt_seed} recall={exc.recall:.6f} matched_rule_ids={','.join(exc.rule_ids) or 'none'}"
            )
            last_leaking_rules = exc.rule_ids
            continue
        grep_logs.append(
            f"grep_bot attempt_seed={attempt_seed} recall={grep_result['recall']:.6f} matched_rule_ids={','.join(grep_result['matched_rule_ids']) or 'none'}"
        )
        task_id = _task_id(playbook_id, tier, seed)
        return [
            f"Generated {task_id} at {out_dir.relative_to(ROOT)}",
            *grep_logs,
            f"Coherence: {coherence_detail}",
            f"Deviations: {', '.join(d['deviation_id'] + ':' + d['rule_id'] + '/' + d['mechanism'] for d in deviations)}",
            f"Validators: PASS with model-backed checks marked STUBBED where applicable",
        ]

    detail = "; ".join(grep_logs)
    leaking = ", ".join(last_leaking_rules) if last_leaking_rules else "none"
    raise GenerationError(
        f"T2 grep_bot recall exceeded {T2_GREP_RECALL_MAX:.1f} after {attempts} attempts; "
        f"leaking rule_ids: {leaking}; attempts: {detail}"
    )


def _generate_candidate(
    *,
    playbook_path: Path,
    playbook: dict[str, Any],
    base: dict[str, Any],
    recipe_entries: list[dict[str, Any]],
    tier: str,
    seed: int,
    attempt_seed: int,
    out_dir: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any], str]:
    rng = random.Random(attempt_seed)
    playbook_id = playbook["playbook_id"]
    params = _surface_params(base, rng, seed)
    task_id = _task_id(playbook_id, tier, seed)
    doc_text, section_map = _render_base(base, params, rng)
    selected = _select_recipes(recipe_entries, tier, rng)

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    try:
        (out_dir / "docs").mkdir()
        deviations: list[dict[str, Any]] = []
        generation_log = [
            f"seed={seed}",
            f"attempt_seed={attempt_seed}",
            f"playbook={playbook_id}",
            f"tier={tier}",
            f"task_id={task_id}",
        ]
        for index, recipe in enumerate(selected, start=1):
            rendered = _render_recipe(recipe, params, rng, section_map)
            original = rendered["original_text"]
            mutated = rendered["mutated_text"]
            if original not in doc_text:
                raise GenerationError(f"{recipe['recipe_id']} original_text not found in base")
            doc_text = doc_text.replace(original, mutated, 1)
            deviation = {
                "deviation_id": f"D-{index:03d}",
                "rule_id": recipe["rule_id"],
                "doc_id": "DOC-01",
                "clause_anchor": {
                    "section": section_map[str(recipe["section"])],
                    "span": mutated,
                },
                "original_text": original,
                "mutated_text": mutated,
                "mechanism": recipe["mechanism"],
                "severity": recipe["severity"],
                "expected_action": recipe["expected_action"],
            }
            deviations.append(deviation)
            generation_log.append(
                f"{deviation['deviation_id']} {recipe['recipe_id']} {recipe['mechanism']} applied to {recipe['rule_id']}"
            )

        coherence_detail = _validate_document_coherence(doc_text, deviations)
        generation_log.append(f"coherence_check {coherence_detail}")

        doc_path = out_dir / "docs" / base["filename"]
        doc_path.write_text(doc_text)
        manifest = {
            "documents": [
                {
                    "doc_id": "DOC-01",
                    "title": _render(base["title_template"], params),
                    "type": base["doc_type"],
                    "path": f"docs/{base['filename']}",
                    "sha256": hashlib.sha256(doc_path.read_bytes()).hexdigest(),
                    "is_distractor": False,
                }
            ]
        }
        planted = {
            "deviations": deviations,
            "distractors": _render_entries(base["distractors"], params),
            "missing_info": _render_entries(base["missing_info"], params),
            "generation_log": generation_log,
        }
        task = {
            "task_id": task_id,
            "practice_area": playbook["practice_area"],
            "client_context": _render(base["client_context_template"], params),
            "instruction": _render(base["instruction_template"], params),
            "deliverable": {"card_schema_id": "redline-gym.issue-card.v1"},
            "turn_cap": 25,
            "difficulty_tier": tier,
            "playbook_ref": str(playbook_path.relative_to(ROOT)),
        }
        _dump_json(out_dir / "task.json", task)
        _dump_json(out_dir / "documents_manifest.json", manifest)
        _dump_json(out_dir / "planted_deviations.json", planted)

        completed = subprocess.run(
            ["python3", "scripts/derive.py", str(out_dir.relative_to(ROOT))],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise GenerationError(f"derive failed: {completed.stderr.strip() or completed.stdout.strip()}")

        results = run_all(out_dir)
        write_report(out_dir, results)
        failures = [r for r in results if r.status == "FAIL"]
        if failures:
            detail = "; ".join(f"{r.code}: {r.detail}" for r in failures)
            raise GenerationError(f"validator failure: {detail}")

        grep_result = measure_grep_bot_recall(out_dir)
        _append_grep_report(out_dir, tier, grep_result, coherence_detail)
        if tier == "T2" and grep_result["recall"] > T2_GREP_RECALL_MAX:
            raise GrepGateError(grep_result["recall"], grep_result["matched_rule_ids"])
    except Exception:
        if out_dir.exists():
            shutil.rmtree(out_dir)
        raise

    return deviations, grep_result, coherence_detail


def measure_grep_bot_recall(task_dir: Path) -> dict[str, Any]:
    task_dir = _repo_path(task_dir)
    with tempfile.TemporaryDirectory(prefix="redline-grep-bot-") as tmp:
        episode = Episode(task_dir, seed=0, run_dir=Path(tmp) / "grep_bot")
        episode.reset()
        grep_bot.drive(episode)
        score = json.loads(episode.score_path.read_text())
    planted = _load_json(task_dir / "planted_deviations.json")
    rule_by_deviation = {dev["deviation_id"]: dev["rule_id"] for dev in planted["deviations"]}
    matched_ids = score.get("matched_deviation_ids", [])
    matched_rule_ids = sorted({rule_by_deviation[dev_id] for dev_id in matched_ids if dev_id in rule_by_deviation})
    return {
        "recall": float(score["channels"]["recall"]),
        "matched_deviation_ids": sorted(matched_ids),
        "matched_rule_ids": matched_rule_ids,
    }


def _append_grep_report(
    task_dir: Path,
    tier: str,
    grep_result: dict[str, Any],
    coherence_detail: str,
) -> None:
    path = task_dir / "verification_report.md"
    text = path.read_text()
    gate = "unconstrained" if tier == "T1" else f"<= {T2_GREP_RECALL_MAX:.1f}"
    lines = [
        "## Emit-Time Baseline Gate",
        "",
        f"- grep_bot recall: {grep_result['recall']:.6f}",
        f"- tier threshold: {gate}",
        f"- matched deviation ids: {', '.join(grep_result['matched_deviation_ids']) or 'none'}",
        f"- matched rule ids: {', '.join(grep_result['matched_rule_ids']) or 'none'}",
        f"- coherence check: {coherence_detail}",
        "",
    ]
    marker = "Human sign-off:"
    index = text.find(marker)
    if index == -1:
        path.write_text(text.rstrip() + "\n\n" + "\n".join(lines))
        return
    path.write_text(text[:index] + "\n".join(lines) + text[index:])


def _repo_path(path: Path) -> Path:
    path = path if path.is_absolute() else ROOT / path
    resolved = path.resolve()
    try:
        resolved.relative_to(ROOT)
    except ValueError as exc:
        raise GenerationError(f"path must be under repo root: {path}") from exc
    return resolved


def _surface_params(base: dict[str, Any], rng: random.Random, seed: int) -> dict[str, str]:
    params = {key: str(rng.choice(values)) for key, values in base["surface_slots"].items()}
    params.update(
        {
            "seed": str(seed),
            "discloser_role": "Discloser",
            "recipient_role": "Recipient",
            "customer_role": "Customer",
            "vendor_role": "Vendor",
        }
    )
    return params


def _render_base(base: dict[str, Any], params: dict[str, str], rng: random.Random) -> tuple[str, dict[str, str]]:
    sections = {section["id"]: section for section in base["sections"]}
    order = rng.choice(base["section_order_variants"])
    section_map = {section_id: str(index) for index, section_id in enumerate(order, start=1)}
    lines = [_render(base["heading_template"], params), "", _render(base["preamble_template"], params), ""]
    for section_id in order:
        section = sections[section_id]
        lines.append(f"## {section_map[section_id]}. {_render(section['heading'], params)}")
        lines.append("")
        lines.extend(_rewrite_section_refs(_render(paragraph, params), section_map) for paragraph in section["paragraphs"])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n", section_map


def _select_recipes(entries: list[dict[str, Any]], tier: str, rng: random.Random) -> list[dict[str, Any]]:
    allowed = ALLOWED_MECHANISMS[tier]
    candidates = [entry for entry in entries if entry["mechanism"] in allowed]
    if tier == "T1":
        return rng.sample(candidates, DEVIATION_COUNT[tier])
    selected: list[dict[str, Any]] = []
    used_rules: set[str] = set()
    for mechanism in sorted(allowed):
        bucket = [entry for entry in candidates if entry["mechanism"] == mechanism and entry["rule_id"] not in used_rules]
        if not bucket:
            raise GenerationError(f"no recipe for required mechanism {mechanism}")
        pick = rng.choice(bucket)
        selected.append(pick)
        used_rules.add(pick["rule_id"])
    remaining = [entry for entry in candidates if entry["rule_id"] not in used_rules]
    selected.extend(rng.sample(remaining, DEVIATION_COUNT[tier] - len(selected)))
    rng.shuffle(selected)
    return selected


def _render_recipe(
    recipe: dict[str, Any],
    params: dict[str, str],
    rng: random.Random,
    section_map: dict[str, str],
) -> dict[str, str]:
    scoped = dict(params)
    for key, values in recipe.get("slots", {}).items():
        scoped[key] = str(rng.choice(values))
    templates = recipe["templates"]
    return {
        "original_text": _rewrite_section_refs(_render(templates["original_text"], scoped), section_map),
        "mutated_text": _rewrite_section_refs(_render(templates["mutated_text"], scoped), section_map),
    }


def _render_entries(entries: list[dict[str, Any]], params: dict[str, str]) -> list[dict[str, Any]]:
    rendered = []
    for entry in entries:
        rendered.append(_render_value(entry, params))
    return rendered


def _render_value(value: Any, params: dict[str, str]) -> Any:
    if isinstance(value, str):
        return _render(value, params)
    if isinstance(value, list):
        return [_render_value(item, params) for item in value]
    if isinstance(value, dict):
        return {key: _render_value(item, params) for key, item in value.items()}
    return value


def _render(template: str, params: dict[str, str]) -> str:
    needed = {field_name for _, field_name, _, _ in Formatter().parse(template) if field_name}
    missing = sorted(name for name in needed if name not in params)
    if missing:
        raise GenerationError(f"missing template params: {', '.join(missing)}")
    return template.format(**params)


def _rewrite_section_refs(text: str, section_map: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        source_section = match.group(1)
        if source_section not in section_map:
            raise GenerationError(f"cross-reference points to missing source section {source_section}")
        return f"Section {section_map[source_section]}"

    return re.sub(r"\bSection\s+([0-9]+)\b", replace, text)


def _validate_document_coherence(doc_text: str, deviations: list[dict[str, Any]]) -> str:
    section_numbers = [int(match.group(1)) for match in re.finditer(r"^##\s+([0-9]+)\.", doc_text, re.MULTILINE)]
    expected = list(range(1, len(section_numbers) + 1))
    if section_numbers != expected:
        raise GenerationError(f"section numbering not sequential: found {section_numbers}, expected {expected}")

    section_ids = {str(number) for number in section_numbers}
    unresolved = sorted(
        {
            match.group(1)
            for match in re.finditer(r"\bSection\s+([0-9]+)\b", doc_text)
            if match.group(1) not in section_ids
        },
        key=int,
    )
    if unresolved:
        raise GenerationError(f"unresolved section cross-references: {', '.join(unresolved)}")

    missing_anchors = [
        f"{dev['deviation_id']}->{dev['clause_anchor']['section']}"
        for dev in deviations
        if dev["clause_anchor"]["section"] not in section_ids
    ]
    if missing_anchors:
        raise GenerationError(f"deviation anchors point to missing sections: {', '.join(missing_anchors)}")
    return f"PASS sections={len(section_numbers)} cross_refs_resolved=yes anchors_resolved=yes"


def _task_id(playbook_id: str, tier: str, seed: int) -> str:
    subject = playbook_id.split("-")[1]
    return f"{tier}-{subject}-{seed:03d}"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n")


class GenerationError(RuntimeError):
    pass


class GrepGateError(GenerationError):
    def __init__(self, recall: float, rule_ids: list[str]) -> None:
        super().__init__(f"grep_bot recall {recall:.6f} matched rule_ids {', '.join(rule_ids) or 'none'}")
        self.recall = recall
        self.rule_ids = rule_ids
