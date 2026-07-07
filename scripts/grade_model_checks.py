#!/usr/bin/env python3
"""Grade structured model-check outputs for a task instance."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = ROOT / "reports" / "model_checks_summary.md"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Grade structured model-check JSON outputs.")
    parser.add_argument("task_dir", type=Path)
    args = parser.parse_args(argv)

    row = grade_task(args.task_dir)
    print(_format_row(row))
    update_summary(row)
    return 0


def grade_task(task_dir: Path) -> dict[str, Any]:
    task_dir = task_dir.resolve()
    checks = task_dir / "model_checks"
    planted = _load_json(task_dir / "planted_deviations.json")
    task = _load_json(task_dir / "task.json")

    v3 = _load_json(checks / "V3_clean_base.json")
    v4 = _load_json(checks / "V4_round_trip.json")
    v7 = _load_json(checks / "V7_semantic.json")
    v11 = _load_json(checks / "V11_realism.json")

    planted_keys = {
        (_norm_item(dev["rule_id"]), _norm_item(dev["clause_anchor"]["section"]))
        for dev in planted["deviations"]
    }
    found_items = v4.get("found", [])
    found_keys = [(_norm_item(item.get("rule_id", "")), _norm_item(item.get("section", ""))) for item in found_items]
    matched = planted_keys & set(found_keys)
    recall = len(matched) / len(planted_keys) if planted_keys else 1.0
    extra_count = sum(1 for key in found_keys if key not in planted_keys)

    gaps = [str(gap) for gap in v7.get("gaps", [])]
    uncovered_topics = []
    for item in planted.get("missing_info", []):
        keywords = [str(keyword).lower() for keyword in item.get("match_keywords", [])]
        if not keywords:
            keywords = [str(item.get("topic", "")).lower()]
        if not any(any(keyword in gap.lower() for keyword in keywords) for gap in gaps):
            uncovered_topics.append(item.get("topic", ""))

    score = v11.get("score")
    v4_gate = _v4_gate(task.get("difficulty_tier", ""), recall)
    try:
        rel_task = str(task_dir.relative_to(ROOT))
    except ValueError:
        rel_task = str(task_dir)

    return {
        "task": rel_task,
        "v3": "PASS" if not v3.get("violations", []) else "FAIL",
        "v4_recall": recall,
        "v4_matched": len(matched),
        "v4_total": len(planted_keys),
        "v4_extra": extra_count,
        "v4_gate": v4_gate,
        "v7": "PASS" if not uncovered_topics else "FAIL",
        "v7_uncovered": uncovered_topics,
        "v11": "PASS" if isinstance(score, (int, float)) and score >= 8 else "FAIL",
        "v11_score": score,
    }


def update_summary(row: dict[str, Any], summary_path: Path = SUMMARY_PATH) -> None:
    summary_path.parent.mkdir(exist_ok=True)
    rows = _read_existing_rows(summary_path)
    rows[row["task"]] = row

    lines = [
        "# Model Checks Summary",
        "",
        "| Task | V3 clean base | V4 recall | V4 reported gate | V4 found-but-not-planted | V7 missing info | V11 score |",
        "|---|---|---:|---|---:|---|---:|",
    ]
    for task in sorted(rows):
        lines.append(_format_markdown_row(rows[task]))
    summary_path.write_text("\n".join(lines) + "\n")


def _read_existing_rows(summary_path: Path) -> dict[str, dict[str, Any]]:
    if not summary_path.exists():
        return {}
    rows: dict[str, dict[str, Any]] = {}
    for line in summary_path.read_text().splitlines():
        if not line.startswith("| tasks/"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) not in {6, 7}:
            continue
        recall_parts = cells[2].split("/")
        matched, total = int(recall_parts[0]), int(recall_parts[1])
        if len(cells) == 7:
            v4_gate = cells[3]
            v4_extra = int(cells[4])
            v7 = cells[5]
            score_text = cells[6]
        else:
            v4_gate = "PASS"
            v4_extra = int(cells[3])
            v7 = cells[4]
            score_text = cells[5]
        rows[cells[0]] = {
            "task": cells[0],
            "v3": cells[1],
            "v4_recall": matched / total if total else 1.0,
            "v4_matched": matched,
            "v4_total": total,
            "v4_extra": v4_extra,
            "v4_gate": v4_gate,
            "v7": v7,
            "v7_uncovered": [],
            "v11": "PASS" if float(score_text) >= 8 else "FAIL",
            "v11_score": float(score_text),
        }
    return rows


def _format_row(row: dict[str, Any]) -> str:
    return (
        f"{row['task']}: V3={row['v3']} "
        f"V4={row['v4_matched']}/{row['v4_total']} gate={row['v4_gate']} extra={row['v4_extra']} "
        f"V7={row['v7']} V11={row['v11']} score={row['v11_score']}"
    )


def _format_markdown_row(row: dict[str, Any]) -> str:
    return (
        f"| {row['task']} | {row['v3']} | {row['v4_matched']}/{row['v4_total']} | "
        f"{row['v4_gate']} | {row['v4_extra']} | {row['v7']} | {float(row['v11_score']):.1f} |"
    )


def _v4_gate(tier: str, recall: float) -> str:
    if tier == "T1":
        threshold = 1.0
    elif tier == "T2":
        threshold = 0.6
    else:
        threshold = 0.6
    return "PASS" if recall >= threshold else "FAIL"


def _norm_item(value: Any) -> str:
    return str(value).strip().lower()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


if __name__ == "__main__":
    raise SystemExit(main())
