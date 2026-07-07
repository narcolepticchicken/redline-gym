from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import shutil
import subprocess
import sys
from string import Formatter
from typing import Any

from validators.checks import run_all, write_report


ROOT = Path(__file__).resolve().parents[1]
GENERATOR_DIR = Path(__file__).resolve().parent
ALLOWED_MECHANISMS = {
    "T1": {"direct_term_swap"},
    "T2": {"direct_term_swap", "cross_ref_override", "defined_term_shift", "omission"},
}
DEVIATION_COUNT = {"T1": 4, "T2": 5}


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
    rng = random.Random(seed)
    playbook_path = _repo_path(playbook_path)
    out_dir = _repo_path(out_dir)
    playbook = _load_json(playbook_path)
    playbook_id = playbook["playbook_id"]
    base = _load_json(GENERATOR_DIR / "bases" / f"{playbook_id}.json")
    recipe_book = _load_json(GENERATOR_DIR / "recipes" / f"{playbook_id}.json")
    params = _surface_params(base, rng, seed)
    task_id = _task_id(playbook_id, tier, seed)
    doc_text = _render_base(base, params, rng)
    selected = _select_recipes(recipe_book["entries"], tier, rng)

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    try:
        (out_dir / "docs").mkdir()
        deviations: list[dict[str, Any]] = []
        generation_log = [
            f"seed={seed}",
            f"playbook={playbook_id}",
            f"tier={tier}",
            f"task_id={task_id}",
        ]
        for index, recipe in enumerate(selected, start=1):
            rendered = _render_recipe(recipe, params, rng)
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
                    "section": str(recipe["section"]),
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
    except Exception:
        if out_dir.exists():
            shutil.rmtree(out_dir)
        raise

    return [
        f"Generated {task_id} at {out_dir.relative_to(ROOT)}",
        f"Deviations: {', '.join(d['deviation_id'] + ':' + d['rule_id'] + '/' + d['mechanism'] for d in deviations)}",
        f"Validators: PASS with model-backed checks marked STUBBED where applicable",
    ]


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


def _render_base(base: dict[str, Any], params: dict[str, str], rng: random.Random) -> str:
    sections = {section["id"]: section for section in base["sections"]}
    order = rng.choice(base["section_order_variants"])
    lines = [_render(base["heading_template"], params), "", _render(base["preamble_template"], params), ""]
    for section_id in order:
        section = sections[section_id]
        lines.append(f"## {section['id']}. {_render(section['heading'], params)}")
        lines.append("")
        lines.extend(_render(paragraph, params) for paragraph in section["paragraphs"])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


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


def _render_recipe(recipe: dict[str, Any], params: dict[str, str], rng: random.Random) -> dict[str, str]:
    scoped = dict(params)
    for key, values in recipe.get("slots", {}).items():
        scoped[key] = str(rng.choice(values))
    templates = recipe["templates"]
    return {
        "original_text": _render(templates["original_text"], scoped),
        "mutated_text": _render(templates["mutated_text"], scoped),
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


def _task_id(playbook_id: str, tier: str, seed: int) -> str:
    subject = playbook_id.split("-")[1]
    return f"{tier}-{subject}-{seed:03d}"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n")


class GenerationError(RuntimeError):
    pass

