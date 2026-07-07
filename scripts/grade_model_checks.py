#!/usr/bin/env python3
"""Grade structured model-check outputs for a task instance."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = ROOT / "reports" / "model_checks_summary.md"
V11_TOTAL = 6


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

    v3 = _load_json_optional(checks / "V3_clean_base.json")
    v4 = _load_json_optional(checks / "V4_round_trip.json")
    v7 = _load_json_optional(checks / "V7_semantic.json")
    v11 = _load_json_optional(checks / "V11_realism.json")

    planted_deviations = planted.get("deviations", [])
    v4_graded = v4 is not None
    found_union = v4.get("found_union", v4.get("found", [])) if v4_graded else []
    found_stable = v4.get("found_stable", v4.get("found", [])) if v4_graded else []
    matched_indexes = _matched_planted_indexes(found_union, planted_deviations)
    if v4_graded:
        recall = len(matched_indexes) / len(planted_deviations) if planted_deviations else 1.0
    else:
        recall = None
    extra_count = sum(1 for item in found_stable if not _matches_any_planted(item, planted_deviations))

    gaps = [str(gap) for gap in v7.get("gaps_union", v7.get("gaps", []))] if v7 is not None else []
    uncovered_topics = []
    if v7 is not None:
        for item in planted.get("missing_info", []):
            keywords = [str(keyword).lower() for keyword in item.get("match_keywords", [])]
            if not keywords:
                keywords = [str(item.get("topic", "")).lower()]
            if not any(any(keyword in gap.lower() for keyword in keywords) for gap in gaps):
                uncovered_topics.append(item.get("topic", ""))

    passed, total, failing_questions = _v11_result(v11) if v11 is not None else (0, V11_TOTAL, [])
    v4_gate = _v4_gate(task.get("difficulty_tier", ""), recall) if recall is not None else "UNGRADED"
    v11_status = _v11_status(passed) if v11 is not None else "UNGRADED"
    try:
        rel_task = str(task_dir.relative_to(ROOT))
    except ValueError:
        rel_task = str(task_dir)

    return {
        "task": rel_task,
        "v3": "PASS" if v3 is not None and not v3.get("violations", []) else ("FAIL" if v3 is not None else "UNGRADED"),
        "v4_recall": recall,
        "v4_matched": len(matched_indexes),
        "v4_total": len(planted_deviations),
        "v4_extra": extra_count,
        "v4_gate": v4_gate,
        "v4_graded": v4_graded,
        "v7": "PASS" if v7 is not None and not uncovered_topics else ("FAIL" if v7 is not None else "UNGRADED"),
        "v7_uncovered": uncovered_topics,
        "v11": v11_status,
        "v11_passed": passed,
        "v11_total": total,
        "v11_failing_questions": failing_questions,
        "v11_score": passed,
    }


def update_summary(row: dict[str, Any], summary_path: Path = SUMMARY_PATH) -> None:
    summary_path.parent.mkdir(exist_ok=True)
    rows = _read_existing_rows(summary_path)
    rows[row["task"]] = row

    lines = [
        "# Model Checks Summary",
        "",
        "| Task | V3 clean base | V4 recall | V4 reported gate | V4 found-but-not-planted | V7 missing info | V11 register |",
        "|---|---|---:|---|---:|---|---|",
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
        if cells[2] == "UNGRADED":
            matched, total = 0, 0
            v4_recall = None
            v4_graded = False
        else:
            recall_parts = cells[2].split("/")
            matched, total = int(recall_parts[0]), int(recall_parts[1])
            v4_recall = matched / total if total else 1.0
            v4_graded = True
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
        v11_fields = _parse_v11_cell(score_text)
        rows[cells[0]] = {
            "task": cells[0],
            "v3": cells[1],
            "v4_recall": v4_recall,
            "v4_matched": matched,
            "v4_total": total,
            "v4_extra": v4_extra,
            "v4_gate": v4_gate,
            "v4_graded": v4_graded,
            "v7": v7,
            "v7_uncovered": [],
            **v11_fields,
        }
    return rows


def _format_row(row: dict[str, Any]) -> str:
    return (
        f"{row['task']}: V3={row['v3']} "
        f"V4={_format_v4_recall_cell(row)} gate={row['v4_gate']} extra={row['v4_extra']} "
        f"V7={row['v7']} V11={row['v11']} reg={row.get('v11_passed', 0)}/{row.get('v11_total', V11_TOTAL)} "
        f"failing={','.join(row.get('v11_failing_questions', [])) or 'none'}"
    )


def _format_markdown_row(row: dict[str, Any]) -> str:
    return (
        f"| {row['task']} | {row['v3']} | {_format_v4_recall_cell(row)} | "
        f"{row['v4_gate']} | {row['v4_extra']} | {row['v7']} | {_format_v11_cell(row)} |"
    )


def _format_v4_recall_cell(row: dict[str, Any]) -> str:
    if row.get("v4_graded") is False or row.get("v4_recall") is None:
        return "UNGRADED"
    return f"{row['v4_matched']}/{row['v4_total']}"


def _v4_gate(tier: str, recall: float) -> str:
    if tier == "T1":
        threshold = 1.0
    elif tier == "T2":
        threshold = 0.6
    else:
        threshold = 0.6
    return "PASS" if recall >= threshold else "FAIL"


def _matched_planted_indexes(found_items: list[dict[str, Any]], planted_deviations: list[dict[str, Any]]) -> set[int]:
    matched: set[int] = set()
    for item in found_items:
        for idx, deviation in enumerate(planted_deviations):
            if _matches_planted(item, deviation):
                matched.add(idx)
                break
    return matched


def _matches_any_planted(item: dict[str, Any], planted_deviations: list[dict[str, Any]]) -> bool:
    return any(_matches_planted(item, deviation) for deviation in planted_deviations)


def _matches_planted(item: dict[str, Any], deviation: dict[str, Any]) -> bool:
    if _norm_item(item.get("rule_id", "")) != _norm_item(deviation.get("rule_id", "")):
        return False
    return _section_matches(item.get("section", ""), deviation) or _quote_overlaps_mutated_text(
        item.get("quote", ""), deviation.get("mutated_text", "")
    )


def _section_matches(found_section: Any, deviation: dict[str, Any]) -> bool:
    anchor = deviation.get("clause_anchor", {}).get("section", "")
    return bool(_section_tokens(found_section) & _section_tokens(anchor))


def _section_tokens(value: Any) -> set[str]:
    text = _norm_item(value)
    tokens = {text} if text else set()
    tokens.update(token for token in re.split(r"[^a-z0-9]+", text) if token)
    return tokens


def _quote_overlaps_mutated_text(quote: Any, mutated_text: Any, threshold: int = 20) -> bool:
    quote_text = _norm_chars(quote)
    mutated = _norm_chars(mutated_text)
    if not quote_text or not mutated:
        return False
    return _longest_common_substring_len(quote_text, mutated) >= threshold


def _longest_common_substring_len(left: str, right: str) -> int:
    if len(left) > len(right):
        left, right = right, left
    previous = [0] * (len(left) + 1)
    best = 0
    for r_char in right:
        current = [0]
        for idx, l_char in enumerate(left, start=1):
            value = previous[idx - 1] + 1 if l_char == r_char else 0
            current.append(value)
            if value > best:
                best = value
        previous = current
    return best


def _v11_result(v11: dict[str, Any]) -> tuple[int, int, list[str]]:
    if isinstance(v11.get("passed"), int):
        passed = int(v11["passed"])
        total = int(v11.get("total", V11_TOTAL))
        return passed, total, _v11_failing_questions(v11.get("per_question", {}))

    legacy_score = v11.get("median", v11.get("score", 0))
    passed = V11_TOTAL if isinstance(legacy_score, (int, float)) and legacy_score >= 8 else 0
    return passed, V11_TOTAL, []


def _v11_failing_questions(per_question: Any) -> list[str]:
    if not isinstance(per_question, dict):
        return []
    failing: list[str] = []
    for qid in sorted(per_question):
        value = per_question[qid]
        passed = value.get("passed") if isinstance(value, dict) else value
        if passed is False:
            failing.append(str(qid))
    return failing


def _v11_status(passed: Any) -> str:
    if isinstance(passed, int) and passed >= 5:
        return "PASS"
    return "FAIL"


def _format_v11_cell(row: dict[str, Any]) -> str:
    if row.get("v11") == "UNGRADED":
        return "UNGRADED"
    if "v11_legacy_cell" in row:
        return f"legacy {row['v11_legacy_cell']}"
    passed = int(row.get("v11_passed", 0))
    total = int(row.get("v11_total", V11_TOTAL))
    failing = list(row.get("v11_failing_questions", []))
    suffix = ",".join(failing) if failing else "none"
    return f"V11 reg {passed}/{total} failing {suffix}"


def _parse_v11_cell(cell: str) -> dict[str, Any]:
    reg_match = re.search(r"(\d+)\s*/\s*(\d+)", cell)
    if reg_match:
        passed = int(reg_match.group(1))
        total = int(reg_match.group(2))
        failing_match = re.search(r"failing\s+([A-Za-z0-9_, -]+)", cell, flags=re.IGNORECASE)
        failing_questions: list[str] = []
        if failing_match:
            failing_text = failing_match.group(1).strip()
            if failing_text.lower() != "none":
                failing_questions = [item for item in re.split(r"[\s,]+", failing_text) if item]
        return {
            "v11": _v11_status(passed),
            "v11_passed": passed,
            "v11_total": total,
            "v11_failing_questions": failing_questions,
            "v11_score": passed,
        }

    numbers = [float(match) for match in re.findall(r"\d+(?:\.\d+)?", cell)]
    legacy_score = numbers[0] if numbers else 0.0
    passed = V11_TOTAL if legacy_score >= 8 else 0
    return {
        "v11": _v11_status(passed),
        "v11_passed": passed,
        "v11_total": V11_TOTAL,
        "v11_failing_questions": [],
        "v11_score": passed,
        "v11_legacy_cell": cell,
    }


def _norm_item(value: Any) -> str:
    return str(value).strip().lower()


def _norm_chars(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _load_json_optional(path: Path) -> dict[str, Any] | None:
    try:
        return _load_json(path)
    except FileNotFoundError:
        return None


if __name__ == "__main__":
    raise SystemExit(main())
