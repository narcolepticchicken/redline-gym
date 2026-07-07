#!/usr/bin/env python3
"""Adjudicate model-reported extra violations without mutating answer keys."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scoring.judge_deepseek import DeepSeekJudge  # noqa: E402
from scripts.run_model_checks import parse_json_response  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "reports" / "answer_key_defects.md"


def _print_judge_usage() -> None:
    totals = DeepSeekJudge.usage_totals()
    print(
        f"judge usage: {totals['prompt_tokens']} prompt + "
        f"{totals['completion_tokens']} completion tokens across {totals['calls']} calls"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Adjudicate V3/V4 extra reported violations for a task.")
    parser.add_argument("task_dir", type=Path)
    args = parser.parse_args(argv)

    result = adjudicate_task(args.task_dir)
    print(f"wrote {result['output_path']}")
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("DeepSeek adjudication: SKIPPED (no key)")
    return 0


def adjudicate_task(task_dir: Path) -> dict[str, Any]:
    task_dir = _repo_path(task_dir)
    items = collect_adjudication_items(task_dir)
    judge = DeepSeekJudge() if os.getenv("DEEPSEEK_API_KEY") else None
    adjudications = []
    for item in items:
        entry = dict(item)
        if judge is None:
            entry["adjudication"] = {"status": "SKIPPED", "genuine": None, "reason": "DEEPSEEK_API_KEY not set"}
        else:
            raw = judge._chat(item["prompt"])
            parsed = parse_json_response(raw)
            genuine = parsed.get("genuine")
            reason = parsed.get("reason")
            if not isinstance(genuine, bool) or not isinstance(reason, str):
                raise ValueError("adjudication response must match {'genuine': bool, 'reason': str}")
            entry["raw_response"] = raw
            entry["adjudication"] = {"status": "DONE", "genuine": genuine, "reason": reason}
        adjudications.append(entry)

    out_dir = task_dir / "model_checks"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "adjudications.json"
    payload = {
        "task": _display_path(task_dir),
        "items": adjudications,
    }
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    genuine_items = [item for item in adjudications if item["adjudication"].get("genuine") is True]
    if genuine_items:
        append_defect_report(task_dir, genuine_items)
    return {"output_path": str(out_path.relative_to(ROOT)), "items": adjudications}


def collect_adjudication_items(task_dir: Path) -> list[dict[str, Any]]:
    task_dir = _repo_path(task_dir)
    task = _load_json(task_dir / "task.json")
    planted = _load_json(task_dir / "planted_deviations.json")
    playbook_path = ROOT / task["playbook_ref"]
    playbook = _load_json(playbook_path)
    rules = {rule["rule_id"]: rule for rule in playbook["rules"]}
    shipped_doc = _single_doc_text(task_dir)
    clean_doc = _clean_doc_text(shipped_doc, planted)

    items: list[dict[str, Any]] = []
    checks = task_dir / "model_checks"
    v3_path = checks / "V3_clean_base.json"
    if v3_path.exists():
        for index, violation in enumerate(_load_json(v3_path).get("violations", []), start=1):
            item = _item_from_report(
                task_dir=task_dir,
                source="V3_clean_base",
                index=index,
                report_item=violation,
                rules=rules,
                doc_text=clean_doc,
            )
            if item:
                items.append(item)

    v4_path = checks / "V4_round_trip.json"
    if v4_path.exists():
        planted_keys = {
            (_norm(dev["rule_id"]), _norm(dev["clause_anchor"]["section"]))
            for dev in planted["deviations"]
        }
        extras = [
            found
            for found in _load_json(v4_path).get("found", [])
            if (_norm(found.get("rule_id", "")), _norm(found.get("section", ""))) not in planted_keys
        ]
        for index, found in enumerate(extras, start=1):
            item = _item_from_report(
                task_dir=task_dir,
                source="V4_round_trip_extra",
                index=index,
                report_item=found,
                rules=rules,
                doc_text=shipped_doc,
            )
            if item:
                items.append(item)
    return items


def build_adjudication_prompt(rule: dict[str, Any], section_text: str) -> str:
    return (
        "Redline Gym answer-key defect adjudication.\n"
        "Given the rule position, fallback, and the contract section text, decide whether the section "
        "contains a GENUINE violation of the rule. Treat text that matches or is more protective than "
        "the fallback as compliant. Return STRICT JSON only: {\"genuine\": true|false, \"reason\": \"...\"}.\n\n"
        f"Rule {rule['rule_id']} position:\n{rule['position']}\n\n"
        f"Fallback:\n{rule['fallback']}\n\n"
        f"Section text:\n{section_text}\n"
    )


def append_defect_report(task_dir: Path, genuine_items: list[dict[str, Any]], report_path: Path = REPORT_PATH) -> None:
    report_path.parent.mkdir(exist_ok=True)
    lines = []
    if report_path.exists():
        lines.append(report_path.read_text().rstrip())
        lines.append("")
    else:
        lines.extend(["# Answer-Key Defects", ""])
    lines.append(f"## {_display_path(task_dir)}")
    lines.append("")
    for item in genuine_items:
        adjudication = item["adjudication"]
        lines.extend(
            [
                f"- {item['source']} {item['rule_id']} section {item['section']}: {adjudication['reason']}",
                f"  Quote: {item.get('quote', '')}",
            ]
        )
    report_path.write_text("\n".join(lines).rstrip() + "\n")


def _item_from_report(
    *,
    task_dir: Path,
    source: str,
    index: int,
    report_item: dict[str, Any],
    rules: dict[str, dict[str, Any]],
    doc_text: str,
) -> dict[str, Any] | None:
    rule_id = str(report_item.get("rule_id", "")).strip()
    rule = rules.get(rule_id)
    if rule is None:
        return None
    section = str(report_item.get("section", "")).strip()
    section_text = extract_section_text(doc_text, section)
    prompt = build_adjudication_prompt(rule, section_text)
    return {
        "id": f"{source}-{index:03d}",
        "task": _display_path(task_dir),
        "source": source,
        "rule_id": rule_id,
        "section": section,
        "quote": str(report_item.get("quote", "")),
        "section_text": section_text,
        "prompt": prompt,
    }


def extract_section_text(doc_text: str, section: str) -> str:
    section_id = _section_id(section)
    if not section_id:
        return doc_text.strip()
    pattern = re.compile(
        rf"^##\s+{re.escape(section_id)}\.\s+.*?(?=^##\s+\d+\.|\Z)",
        flags=re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(doc_text)
    return (match.group(0) if match else doc_text).strip()


def _section_id(section: str) -> str:
    match = re.search(r"\d+", section)
    return match.group(0) if match else ""


def _clean_doc_text(shipped_doc: str, planted: dict[str, Any]) -> str:
    clean = shipped_doc
    for dev in planted["deviations"]:
        clean = clean.replace(dev["mutated_text"], dev["original_text"], 1)
    return clean


def _single_doc_text(task_dir: Path) -> str:
    manifest = _load_json(task_dir / "documents_manifest.json")
    docs = manifest["documents"]
    if len(docs) != 1:
        raise ValueError("adjudication harness currently expects a single document")
    return (task_dir / docs[0]["path"]).read_text()


def _repo_path(path: Path) -> Path:
    path = path if path.is_absolute() else ROOT / path
    return path.resolve()


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _norm(value: Any) -> str:
    return str(value).strip().lower()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    finally:
        _print_judge_usage()
