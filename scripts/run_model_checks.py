#!/usr/bin/env python3
"""Run model-backed validators and write raw plus strict JSON outputs.

Usage:
    REDLINE_JUDGE_ENABLED=1 python3 scripts/run_model_checks.py [task_dir]
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from typing import Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from scoring.judge_deepseek import DeepSeekJudge  # noqa: E402


SCHEMA_INSTRUCTIONS = {
    "V3_clean_base": (
        'Return STRICT JSON only, matching this schema exactly: '
        '{"verdict":"PASS|FAIL","violations":[{"rule_id":"R-###","section":"...","quote":"..."}]}. '
        "Use PASS only if there are no violations."
    ),
    "V4_round_trip": (
        'Return STRICT JSON only, matching this schema exactly: '
        '{"found":[{"rule_id":"R-###","section":"...","quote":"..."}]}. '
        "Include every playbook violation you can support from the text."
    ),
    "V7_semantic": (
        'Return STRICT JSON only, matching this schema exactly: {"gaps":["topic",...]}. '
        "Each gap should be a concise material missing-information topic."
    ),
    "V11_realism": (
        'Return STRICT JSON only, matching this schema exactly: {"score":0-10,"weakest":["...",...]}. '
        "Score PROSE REGISTER AND STRUCTURAL COHERENCE ONLY. Aggressive, one-sided, "
        "or customer-unfavorable substantive terms are EXPECTED content and must not reduce the score. "
        "Deduct only for unnatural phrasing, drafting-register anomalies, broken numbering or "
        "cross-references, or internal incoherence."
    ),
}


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    task_dir = pathlib.Path(args[0] if args else "tasks/contracts/T1-NDA-001")
    out_dir = task_dir / "model_checks"
    out_dir.mkdir(exist_ok=True)

    task = json.loads((task_dir / "task.json").read_text())
    pdv = json.loads((task_dir / "planted_deviations.json").read_text())
    doc_path = next((task_dir / "docs").glob("*.md"))
    shipped = doc_path.read_text()

    pb_ref = task["playbook_ref"]
    pb_path = pathlib.Path(pb_ref)
    if not pb_path.exists():
        pb_path = (task_dir / "../../.." / pb_ref).resolve()
    pb = json.loads(pb_path.read_text())

    # Agent-visible playbook rendering only (rule_id, position, fallback, severity).
    pb_text = "\n".join(
        f'{r["rule_id"]} [{r.get("severity","")}]\nPosition: {r["position"]}\nFallback: {r["fallback"]}'
        for r in pb["rules"]
    )

    clean = shipped
    for d in pdv["deviations"]:
        if clean.count(d["mutated_text"]) != 1:
            sys.exit(f'cannot revert {d["deviation_id"]}: span count {clean.count(d["mutated_text"])}')
        clean = clean.replace(d["mutated_text"], d["original_text"], 1)

    judge = DeepSeekJudge()
    prompts = {
        "V3_clean_base": (
            "This is the CLEAN BASE contract. Check it against the playbook. "
            "Use each rule's fallback text as the compliance reference. Text that matches or is more "
            "protective than the fallback is COMPLIANT and must not be listed; list a violation only "
            "where the text clearly contradicts the rule position. It should contain ZERO playbook "
            "violations. List any violation you find with section + quote.\n\n"
            + clean
        ),
        "V4_round_trip": (
            "This is the SHIPPED contract. Independently list EVERY playbook violation you can find. "
            "For each: section number, exact quote, violated rule_id. Be thorough; do not guess beyond the text.\n\n"
            + shipped
        ),
        "V7_semantic": (
            f"Client context: {task['client_context']}\n\n"
            "Given this context, name any material topic this contract is SILENT on that a careful reviewer "
            "should escalate. Cite why.\n\n"
            + shipped
        ),
        "V11_realism": (
            "Score this contract 0-10 on whether it reads as a coherent, professionally drafted agreement "
            "in prose register and structure. Do not grade the business favorability of the terms.\n\n"
            + shipped
        ),
    }
    calls = {
        "V3_clean_base": judge.clean_base_judge_pass,
        "V4_round_trip": judge.round_trip_extractor,
        "V7_semantic": judge.missing_info_semantic_search,
        "V11_realism": judge.realism_judge,
    }

    for name, call in calls.items():
        prompt = _with_schema(prompts[name], SCHEMA_INSTRUCTIONS[name])
        raw_text = call(prompt, pb_text)
        parsed, final_text = _parse_validate_or_reprompt(name, raw_text, prompt, pb_text, call, out_dir)
        if parsed is None:
            print(f"=== {name} ===\nERROR: invalid JSON after corrective retry; see {out_dir / f'{name}.error'}\n")
            continue
        (out_dir / f"{name}.json").write_text(json.dumps(parsed, indent=2, sort_keys=True) + "\n")
        print(f"=== {name} ===\n{final_text.strip()[:1200]}\n")
    print("written to", out_dir)
    return 0


def _with_schema(prompt: str, schema_instruction: str) -> str:
    return f"{prompt}\n\n{schema_instruction}\nDo not include markdown, commentary, or text outside the JSON object."


def _parse_validate_or_reprompt(
    name: str,
    raw_text: str,
    prompt: str,
    playbook_text: str,
    call: Any,
    out_dir: pathlib.Path,
) -> tuple[dict[str, Any] | None, str]:
    try:
        parsed = parse_json_response(raw_text)
        _validate_shape(name, parsed)
        (out_dir / f"{name}.txt").write_text(raw_text)
        return parsed, raw_text
    except (json.JSONDecodeError, ValueError) as first_exc:
        corrective_prompt = (
            f"{prompt}\n\nPrevious invalid output:\n{raw_text}\n\n"
            "That was not valid JSON matching the schema; return ONLY the JSON object."
        )
        retry_text = call(corrective_prompt, playbook_text)
        (out_dir / f"{name}.txt").write_text(retry_text)
        try:
            parsed = parse_json_response(retry_text)
            _validate_shape(name, parsed)
            return parsed, retry_text
        except (json.JSONDecodeError, ValueError) as second_exc:
            (out_dir / f"{name}.error").write_text(
                f"initial_error: {first_exc}\nretry_error: {second_exc}\n"
            )
            return None, retry_text


def parse_json_response(text: str) -> dict[str, Any]:
    stripped = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        stripped = fenced.group(1)
    elif not stripped.startswith("{"):
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise ValueError("model response did not contain a JSON object")
        stripped = stripped[start : end + 1]
    parsed = json.loads(stripped)
    if not isinstance(parsed, dict):
        raise ValueError("model response JSON must be an object")
    return parsed


def _validate_shape(name: str, payload: dict[str, Any]) -> None:
    if name == "V3_clean_base":
        _require_keys(name, payload, {"verdict", "violations"})
        if payload["verdict"] not in {"PASS", "FAIL"}:
            raise ValueError("V3 verdict must be PASS or FAIL")
        _require_list(name, payload["violations"])
    elif name == "V4_round_trip":
        _require_keys(name, payload, {"found"})
        _require_list(name, payload["found"])
    elif name == "V7_semantic":
        _require_keys(name, payload, {"gaps"})
        _require_list(name, payload["gaps"])
    elif name == "V11_realism":
        _require_keys(name, payload, {"score", "weakest"})
        if not isinstance(payload["score"], (int, float)) or not 0 <= payload["score"] <= 10:
            raise ValueError("V11 score must be a number from 0 to 10")
        _require_list(name, payload["weakest"])


def _require_keys(name: str, payload: dict[str, Any], keys: set[str]) -> None:
    missing = sorted(keys - payload.keys())
    if missing:
        raise ValueError(f"{name} JSON missing keys: {', '.join(missing)}")


def _require_list(name: str, value: Any) -> None:
    if not isinstance(value, list):
        raise ValueError(f"{name} expected list field")


if __name__ == "__main__":
    raise SystemExit(main())
