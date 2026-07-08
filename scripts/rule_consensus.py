#!/usr/bin/env python3
"""Collect out-of-domain provider endorsement for playbook rules."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
from typing import Any
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
PLAYBOOKS_DIR = ROOT / "playbooks"
TASKS_DIR = ROOT / "tasks"
REPORTS_DIR = ROOT / "reports"
JSON_REPORT = REPORTS_DIR / "rule_consensus.json"
MD_REPORT = REPORTS_DIR / "rule_consensus.md"

PROVIDERS: dict[str, dict[str, str]] = {
    "deepseek": {
        "base": "https://api.deepseek.com",
        "model": "deepseek-v4-pro",
        "env": "DEEPSEEK_API_KEY",
    },
    "glm": {
        "base": "https://api.z.ai/api/coding/paas/v4",
        "model": "glm-5.2",
        "env": "GLM_API_KEY",
    },
    "minimax": {
        "base": "https://api.minimax.io/v1",
        "model": "MiniMax-M3",
        "env": "MINIMAX_API_KEY",
    },
}

RESPONDED_STATUS = "DONE"
SKIPPED_STATUS = "SKIPPED"
ERROR_STATUS = "ERROR"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect attorney rule consensus from independent providers.")
    parser.add_argument("--dry-run", action="store_true", help="Print one example prompt and make no network calls.")
    args = parser.parse_args(argv)

    playbooks = load_playbooks()
    exemplars = load_exemplar_tasks()
    if args.dry_run:
        playbook_path, playbook = playbooks[0]
        exemplar = exemplar_for_playbook(playbook_path, exemplars)
        print(build_rule_prompt(playbook, playbook["rules"][0], exemplar))
        return 0

    report = collect_consensus(playbooks, exemplars)
    write_reports(report)
    print_summary(report)
    return 0


def collect_consensus(
    playbooks: list[tuple[Path, dict[str, Any]]],
    exemplars: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    playbook_results = []
    total_rules = 0
    endorsed = 0
    dissent = 0
    dissent_list = []

    for playbook_path, playbook in playbooks:
        exemplar = exemplar_for_playbook(playbook_path, exemplars)
        rows = []
        for rule in playbook["rules"]:
            prompt = build_rule_prompt(playbook, rule, exemplar)
            provider_results = {
                provider_name: query_provider(provider_name, spec, prompt)
                for provider_name, spec in PROVIDERS.items()
            }
            verdict = consensus_verdict(provider_results)
            total_rules += 1
            if verdict == "ENDORSED":
                endorsed += 1
            else:
                dissent += 1
                dissent_list.append(f"{playbook['playbook_id']}:{rule['rule_id']}")
            rows.append(
                {
                    "rule_id": rule["rule_id"],
                    "rule": {
                        "position": rule["position"],
                        "fallback": rule["fallback"],
                        "severity": rule["severity"],
                        "is_canary": rule["is_canary"],
                    },
                    "providers": provider_results,
                    "verdict": verdict,
                }
            )
        playbook_results.append(
            {
                "path": display_path(playbook_path),
                "playbook_id": playbook["playbook_id"],
                "practice_area": playbook["practice_area"],
                "title": playbook["title"],
                "exemplar_task": {
                    "task_id": exemplar["task_id"],
                    "path": exemplar.get("_path", ""),
                    "client_context": exemplar["client_context"],
                },
                "rules": rows,
            }
        )

    return {
        "providers": PROVIDERS,
        "summary": {
            "total_rules": total_rules,
            "endorsed_count": endorsed,
            "dissent_count": dissent,
            "dissent_list": dissent_list,
        },
        "playbooks": playbook_results,
    }


def query_provider(provider_name: str, spec: dict[str, str], prompt: str) -> dict[str, Any]:
    api_key = os.getenv(spec["env"])
    if not api_key:
        return {"status": SKIPPED_STATUS, "agree": None, "reason": f"{spec['env']} not set"}

    try:
        raw = chat_once(spec, api_key, prompt)
    except OSError as first_exc:
        try:
            raw = chat_once(spec, api_key, prompt)
        except OSError as second_exc:
            return {
                "status": ERROR_STATUS,
                "agree": None,
                "reason": f"network error after retry: {second_exc}",
                "first_error": str(first_exc),
            }

    try:
        parsed = parse_provider_json(raw, strip_think_prefix=(provider_name == "minimax"))
        return provider_done_result(parsed, raw)
    except (json.JSONDecodeError, ValueError) as first_exc:
        corrective_prompt = (
            f"{prompt}\n\nPrevious invalid output:\n{raw}\n\n"
            'Return ONLY strict JSON matching {"agree": true|false, "reason": "<=2 sentences citing standard practice"}.'
        )
        try:
            retry_raw = chat_once(spec, api_key, corrective_prompt)
        except OSError as exc:
            return {
                "status": ERROR_STATUS,
                "agree": None,
                "reason": f"network error during parse retry: {exc}",
                "parse_error": str(first_exc),
                "raw_response": raw,
            }
        try:
            parsed = parse_provider_json(retry_raw, strip_think_prefix=(provider_name == "minimax"))
            result = provider_done_result(parsed, retry_raw)
            result["initial_parse_error"] = str(first_exc)
            result["initial_raw_response"] = raw
            return result
        except (json.JSONDecodeError, ValueError) as second_exc:
            return {
                "status": ERROR_STATUS,
                "agree": None,
                "reason": f"parse error after corrective retry: {second_exc}",
                "initial_parse_error": str(first_exc),
                "raw_response": retry_raw,
                "initial_raw_response": raw,
            }


def chat_once(spec: dict[str, str], api_key: str, prompt: str, max_tokens: int = 400) -> str:
    payload = {
        "model": spec["model"],
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": max_tokens,
    }
    request = urllib.request.Request(
        f"{spec['base'].rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        data = json.loads(response.read().decode("utf-8"))
    content = str(data["choices"][0]["message"].get("content") or "")
    if not content.strip() and max_tokens < 8000:
        # Reasoning models can burn the whole budget thinking (empty-content-
        # on-length class): escalate the cap and retry once per level.
        return chat_once(spec, api_key, prompt, max_tokens=max_tokens * 5)
    return content


def parse_provider_json(text: str, *, strip_think_prefix: bool = False) -> dict[str, Any]:
    stripped = text.strip()
    if strip_think_prefix:
        stripped = re.sub(r"^\s*<think>.*?</think>\s*", "", stripped, count=1, flags=re.DOTALL | re.IGNORECASE)
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
    if not isinstance(parsed.get("agree"), bool):
        raise ValueError("provider JSON must contain boolean agree")
    if not isinstance(parsed.get("reason"), str):
        raise ValueError("provider JSON must contain string reason")
    return {"agree": parsed["agree"], "reason": parsed["reason"].strip()}


def provider_done_result(parsed: dict[str, Any], raw: str) -> dict[str, Any]:
    return {
        "status": RESPONDED_STATUS,
        "agree": parsed["agree"],
        "reason": parsed["reason"],
        "raw_response": raw,
    }


def consensus_verdict(provider_results: dict[str, dict[str, Any]]) -> str:
    responded = [
        result
        for result in provider_results.values()
        if result.get("status") == RESPONDED_STATUS and isinstance(result.get("agree"), bool)
    ]
    if len(responded) >= 2 and all(result["agree"] is True for result in responded):
        return "ENDORSED"
    return "DISSENT"


def build_rule_prompt(playbook: dict[str, Any], rule: dict[str, Any], exemplar: dict[str, Any]) -> str:
    return (
        "You are an independent attorney reviewing an out-of-domain endorsement request for a "
        "Redline Gym playbook rule. The drafter model is excluded from this review by design.\n\n"
        "Question: does this rule state a realistic position a real company in this client context "
        "would take?\n\n"
        f"Practice area: {playbook['practice_area']}\n"
        f"Playbook: {playbook['playbook_id']} - {playbook['title']}\n"
        f"Exemplar task: {exemplar['task_id']}\n"
        f"Client context: {exemplar['client_context']}\n\n"
        f"Rule id: {rule['rule_id']}\n"
        f"Position: {rule['position']}\n"
        f"Fallback: {rule['fallback']}\n"
        f"Severity: {rule['severity']}\n"
        f"is_canary: {str(rule['is_canary']).lower()}\n\n"
        'Return STRICT JSON only: {"agree": true|false, "reason": "<=2 sentences citing standard practice"}'
    )


def write_reports(report: dict[str, Any]) -> None:
    REPORTS_DIR.mkdir(exist_ok=True)
    JSON_REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    MD_REPORT.write_text(render_markdown(report))


def render_markdown(report: dict[str, Any]) -> str:
    lines = ["# Rule Consensus", ""]
    summary = report["summary"]
    lines.extend(
        [
            f"- Total rules: {summary['total_rules']}",
            f"- Endorsed: {summary['endorsed_count']}",
            f"- Dissent: {summary['dissent_count']}",
            "",
        ]
    )
    for playbook in report["playbooks"]:
        lines.extend(
            [
                f"## {playbook['playbook_id']} - {playbook['title']}",
                "",
                f"Practice area: {playbook['practice_area']}",
                f"Exemplar: {playbook['exemplar_task']['task_id']}",
                "",
                "| rule_id | deepseek | glm | minimax | verdict |",
                "|---|---|---|---|---|",
            ]
        )
        dissent_reasons = []
        for row in playbook["rules"]:
            lines.append(
                "| {rule_id} | {deepseek} | {glm} | {minimax} | {verdict} |".format(
                    rule_id=row["rule_id"],
                    deepseek=format_provider_cell(row["providers"]["deepseek"]),
                    glm=format_provider_cell(row["providers"]["glm"]),
                    minimax=format_provider_cell(row["providers"]["minimax"]),
                    verdict=row["verdict"],
                )
            )
            for provider_name, result in row["providers"].items():
                if result.get("status") == RESPONDED_STATUS and result.get("agree") is False:
                    dissent_reasons.append((row["rule_id"], provider_name, result.get("reason", "")))
        lines.append("")
        lines.append("Dissenting reasons:")
        if dissent_reasons:
            for rule_id, provider_name, reason in dissent_reasons:
                lines.append(f'- {rule_id} {provider_name}: "{reason}"')
        else:
            lines.append("- None")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def format_provider_cell(result: dict[str, Any]) -> str:
    if result.get("status") == SKIPPED_STATUS:
        return "SKIPPED"
    if result.get("status") == ERROR_STATUS:
        return "ERROR"
    if result.get("agree") is True:
        return "AGREE"
    if result.get("agree") is False:
        return "DISAGREE"
    return "ERROR"


def print_summary(report: dict[str, Any]) -> None:
    summary = report["summary"]
    print(f"total rules: {summary['total_rules']}")
    print(f"endorsed count: {summary['endorsed_count']}")
    print(f"dissent count: {summary['dissent_count']}")
    print("dissent list:")
    if summary["dissent_list"]:
        for item in summary["dissent_list"]:
            print(f"- {item}")
    else:
        print("- none")
    print(f"wrote {display_path(MD_REPORT)}")
    print(f"wrote {display_path(JSON_REPORT)}")


def load_playbooks() -> list[tuple[Path, dict[str, Any]]]:
    playbooks = []
    for path in sorted(PLAYBOOKS_DIR.glob("*/*.json")):
        playbooks.append((path, load_json(path)))
    if not playbooks:
        raise RuntimeError("no playbooks found under playbooks/*/*.json")
    return playbooks


def load_exemplar_tasks() -> dict[str, dict[str, Any]]:
    exemplars: dict[str, dict[str, Any]] = {}
    for path in sorted(TASKS_DIR.glob("**/task.json")):
        task = load_json(path)
        ref = task.get("playbook_ref")
        if isinstance(ref, str) and ref not in exemplars:
            task["_path"] = display_path(path)
            exemplars[ref] = task
    return exemplars


def exemplar_for_playbook(playbook_path: Path, exemplars: dict[str, dict[str, Any]]) -> dict[str, Any]:
    ref = display_path(playbook_path)
    exemplar = exemplars.get(ref)
    if exemplar is None:
        raise RuntimeError(f"no exemplar task found with playbook_ref {ref}")
    return exemplar


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
