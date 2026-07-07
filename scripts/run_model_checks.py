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
from collections import Counter
from typing import Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from scoring.judge_deepseek import DeepSeekJudge  # noqa: E402


V11_QUESTION_IDS = ("q1", "q2", "q3", "q4", "q5", "q6")
V11_QUESTIONS = {
    "q1": "section numbering is sequential and cross-references resolve",
    "q2": "defined terms are defined once and used consistently",
    "q3": 'no vague or non-commercial time/quantity phrasing, e.g. "the next quarter" or "a reasonable while"',
    "q4": "no archaic or out-of-register legal diction relative to the rest of the document",
    "q5": "no sentence reads as internally contradictory or grammatically broken",
    "q6": "clause phrasing register is consistent across sections, with no section reading like a different author mid-document",
}


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
        "Each gap should be a concise material missing-information topic. Report ONLY topics that have "
        "NO clause at all in the document. If a topic is addressed by an existing clause, even a defective "
        "or weak clause, it is out of scope for this check; that is a playbook violation, not a gap."
    ),
    "V11_realism": (
        'Return STRICT JSON only, matching this schema exactly: '
        '{"answers":{"q1":true|false,"q2":true|false,"q3":true|false,"q4":true|false,"q5":true|false,"q6":true|false},'
        '"evidence":{"q1":"quote or empty","q2":"quote or empty","q3":"quote or empty","q4":"quote or empty","q5":"quote or empty","q6":"quote or empty"}}. '
        "Answer true when the register check is healthy. Answer false only for prose register or structural coherence defects. "
        "One-sided, aggressive, or customer-unfavorable SUBSTANCE is expected and must not affect any answer."
    ),
}


def _print_judge_usage() -> None:
    totals = DeepSeekJudge.usage_totals()
    print(
        f"judge usage: {totals['prompt_tokens']} prompt + "
        f"{totals['completion_tokens']} completion tokens across {totals['calls']} calls"
    )


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
            "should escalate. Report ONLY topics with NO clause at all in the document. Do not report topics "
            "covered by an existing clause, even if the clause is defective, weak, too narrow, too slow, or "
            "customer-unfavorable; those are violations for V4, not missing-information gaps for V7.\n\n"
            + shipped
        ),
        "V11_realism": (
            "Answer this fixed battery of register and structural-coherence questions for the contract below. "
            "Each yes/true answer means healthy. One-sided or aggressive SUBSTANCE is expected in these fixtures "
            "and must not affect any answer; judge only prose register and structural coherence.\n\n"
            + "\n".join(f"{qid}: {question}" for qid, question in V11_QUESTIONS.items())
            + "\n\n"
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
        sample_count = 3 if name in {"V4_round_trip", "V7_semantic", "V11_realism"} else 1
        samples: list[dict[str, Any]] = []
        final_texts: list[str] = []
        for sample_idx in range(1, sample_count + 1):
            raw_text = call(prompt, pb_text)
            output_name = name if sample_count == 1 else f"{name}.sample{sample_idx}"
            parsed, final_text = _parse_validate_or_reprompt(
                name, raw_text, prompt, pb_text, call, out_dir, output_name=output_name
            )
            if parsed is None:
                print(
                    f"=== {output_name} ===\n"
                    f"ERROR: invalid JSON after corrective retry; see {out_dir / f'{output_name}.error'}\n"
                )
                continue
            (out_dir / f"{output_name}.json").write_text(json.dumps(parsed, indent=2, sort_keys=True) + "\n")
            samples.append(parsed)
            final_texts.append(final_text)

        if sample_count > 1:
            aggregate = write_aggregate_from_samples(name, samples, out_dir, shipped)
            if aggregate is None:
                print(f"=== {name} ===\nERROR: 0/{sample_count} valid samples; aggregate not written\n")
                continue
            if len(samples) != sample_count:
                print(f"=== {name} ===\nWARNING: only {len(samples)}/{sample_count} valid samples; aggregate written\n")
            print(f"=== {name} ===\n{json.dumps(aggregate, indent=2, sort_keys=True)[:1200]}\n")
        elif samples:
            print(f"=== {name} ===\n{final_texts[0].strip()[:1200]}\n")
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
    output_name: str | None = None,
) -> tuple[dict[str, Any] | None, str]:
    output_name = output_name or name
    try:
        parsed = parse_json_response(raw_text)
        _validate_shape(name, parsed)
        (out_dir / f"{output_name}.txt").write_text(raw_text)
        return parsed, raw_text
    except (json.JSONDecodeError, ValueError) as first_exc:
        corrective_prompt = (
            f"{prompt}\n\nPrevious invalid output:\n{raw_text}\n\n"
            "That was not valid JSON matching the schema; return ONLY the JSON object."
        )
        retry_text = call(corrective_prompt, playbook_text)
        (out_dir / f"{output_name}.txt").write_text(retry_text)
        try:
            parsed = parse_json_response(retry_text)
            _validate_shape(name, parsed)
            return parsed, retry_text
        except (json.JSONDecodeError, ValueError) as second_exc:
            (out_dir / f"{output_name}.error").write_text(
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
        _require_keys(name, payload, {"answers", "evidence"})
        if not isinstance(payload["answers"], dict):
            raise ValueError("V11 answers must be an object")
        if not isinstance(payload["evidence"], dict):
            raise ValueError("V11 evidence must be an object")
        _require_keys(name, payload["answers"], set(V11_QUESTION_IDS))
        _require_keys(name, payload["evidence"], set(V11_QUESTION_IDS))
        for qid in V11_QUESTION_IDS:
            if not isinstance(payload["answers"][qid], bool):
                raise ValueError(f"V11 {qid} answer must be true or false")
            if not isinstance(payload["evidence"][qid], str):
                raise ValueError(f"V11 {qid} evidence must be a string")


def aggregate_v4_samples(samples: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate V4 samples by normalized rule_id + section."""
    first_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    sample_presence: Counter[tuple[str, str]] = Counter()
    for sample in samples:
        seen_in_sample: set[tuple[str, str]] = set()
        for item in sample.get("found", []):
            if not isinstance(item, dict):
                continue
            key = _v4_item_key(item)
            if not key[0] or not key[1]:
                continue
            first_by_key.setdefault(key, item)
            seen_in_sample.add(key)
        sample_presence.update(seen_in_sample)

    found_union = [first_by_key[key] for key in first_by_key]
    found_stable = [first_by_key[key] for key in first_by_key if sample_presence[key] >= 2]
    return {"found_union": found_union, "found_stable": found_stable}


def write_aggregate_from_samples(
    name: str,
    samples: list[dict[str, Any]],
    out_dir: pathlib.Path,
    shipped: str,
) -> dict[str, Any] | None:
    if not samples:
        (out_dir / f"{name}.error").write_text("all samples failed to parse; aggregate not written\n")
        return None
    if name == "V4_round_trip":
        aggregate = aggregate_v4_samples(samples)
    elif name == "V7_semantic":
        aggregate = aggregate_v7_samples(samples)
    elif name == "V11_realism":
        aggregate = aggregate_v11_samples(samples, mechanical_q1=_mechanical_v11_q1(shipped))
    else:
        raise ValueError(f"unsupported aggregate check: {name}")
    (out_dir / f"{name}.json").write_text(json.dumps(aggregate, indent=2, sort_keys=True) + "\n")
    return aggregate


def aggregate_v7_samples(samples: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate V7 samples as a normalized union of missing-information gaps."""
    gaps_union: list[str] = []
    seen: set[str] = set()
    for sample in samples:
        for gap in sample.get("gaps", []):
            text = str(gap).strip()
            if not text:
                continue
            key = _norm_item(text)
            if key in seen:
                continue
            gaps_union.append(text)
            seen.add(key)
    return {"gaps_union": gaps_union}


def aggregate_v11_samples(samples: list[dict[str, Any]], mechanical_q1: bool | None = None) -> dict[str, Any]:
    per_question: dict[str, dict[str, Any]] = {}
    failing_evidence: dict[str, list[str]] = {}

    for qid in V11_QUESTION_IDS:
        votes = [sample["answers"][qid] for sample in samples if isinstance(sample.get("answers", {}).get(qid), bool)]
        if not votes:
            raise ValueError(f"V11 samples did not contain boolean answers for {qid}")
        yes_votes = sum(1 for vote in votes if vote)
        no_votes = len(votes) - yes_votes
        passed = yes_votes > no_votes
        per_question[qid] = {
            "passed": passed,
            "yes_votes": yes_votes,
            "no_votes": no_votes,
        }
        if not passed:
            failing_evidence[qid] = _v11_failing_evidence(samples, qid)

    passed_count = sum(1 for result in per_question.values() if result["passed"])
    aggregate: dict[str, Any] = {
        "passed": passed_count,
        "total": len(V11_QUESTION_IDS),
        "per_question": per_question,
        "failing_evidence": failing_evidence,
    }
    if mechanical_q1 is not None:
        judge_q1 = bool(per_question["q1"]["passed"])
        aggregate["mechanical_agreement"] = {
            "q1": {
                "mechanical_passed": mechanical_q1,
                "judge_passed": judge_q1,
                "agrees": mechanical_q1 == judge_q1,
            }
        }
    return aggregate


def _v11_failing_evidence(samples: list[dict[str, Any]], qid: str) -> list[str]:
    evidence: list[str] = []
    seen: set[str] = set()
    for sample in samples:
        if sample.get("answers", {}).get(qid) is not False:
            continue
        text = str(sample.get("evidence", {}).get(qid, "")).strip()
        key = text.lower()
        if text and key not in seen:
            evidence.append(text)
            seen.add(key)
    return evidence


def _mechanical_v11_q1(doc_text: str) -> bool:
    section_numbers = [int(match.group(1)) for match in re.finditer(r"^##\s+([0-9]+)\.", doc_text, re.MULTILINE)]
    expected = list(range(1, len(section_numbers) + 1))
    if section_numbers != expected:
        return False
    section_ids = {str(number) for number in section_numbers}
    return not any(
        match.group(1) not in section_ids
        for match in re.finditer(r"\bSection\s+([0-9]+)\b", doc_text)
    )


def _v4_item_key(item: dict[str, Any]) -> tuple[str, str]:
    return (_norm_item(item.get("rule_id", "")), _norm_item(item.get("section", "")))


def _require_keys(name: str, payload: dict[str, Any], keys: set[str]) -> None:
    missing = sorted(keys - payload.keys())
    if missing:
        raise ValueError(f"{name} JSON missing keys: {', '.join(missing)}")


def _require_list(name: str, value: Any) -> None:
    if not isinstance(value, list):
        raise ValueError(f"{name} expected list field")


def _norm_item(value: Any) -> str:
    return str(value).strip().lower()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    finally:
        _print_judge_usage()
