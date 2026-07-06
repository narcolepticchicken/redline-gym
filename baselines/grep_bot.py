from __future__ import annotations

import re
from typing import Any

from env import Episode

from .common import doc_lines_with_headings, finalize_card, non_canary_rules, run_baseline


NAME = "grep_bot"
STOPWORDS = {
    "about",
    "after",
    "also",
    "and",
    "any",
    "are",
    "because",
    "been",
    "before",
    "between",
    "confidential",
    "confidentiality",
    "disclose",
    "disclosed",
    "disclosure",
    "each",
    "from",
    "information",
    "into",
    "only",
    "party",
    "recipient",
    "should",
    "that",
    "their",
    "this",
    "under",
    "when",
    "where",
    "with",
}


def drive(episode: Episode) -> None:
    rows = doc_lines_with_headings(episode)
    flags: list[dict[str, Any]] = []
    seen: set[tuple[str, str, int]] = set()
    for rule in non_canary_rules(episode):
        hints = _rule_hints(rule)
        for row in rows:
            if not _matches(row["text"], hints):
                continue
            key = (rule["rule_id"], row["doc_id"], row["line"])
            if key in seen:
                continue
            seen.add(key)
            action = {
                "action": "flag_issue",
                "rule_id": rule["rule_id"],
                "doc_id": row["doc_id"],
                "clause_ref": row["clause_ref"],
                "exact_quote": row["text"],
                "severity": rule["severity"],
                "proposed_redline": rule["fallback"],
                "rationale": "Lexical hint matched by grep baseline.",
            }
            flags.append({k: v for k, v in action.items() if k != "action"})
            episode.step(action)
            break
    episode.step(
        {
            "action": "finalize",
            "card": finalize_card(flags, [], "Lexical playbook scan completed."),
        }
    )


def _rule_hints(rule: dict[str, Any]) -> list[str]:
    checks = rule.get("deterministic_checks", {})
    explicit = checks.get("must_not_contain", []) if isinstance(checks, dict) else []
    if explicit:
        return [str(item).lower() for item in explicit if str(item).strip()]
    text = f"{rule.get('position', '')} {rule.get('fallback', '')}"
    tokens = [
        token
        for token in re.split(r"\W+", text.lower())
        if len(token) > 4 and token not in STOPWORDS
    ]
    return tokens[:5]


def _matches(text: str, hints: list[str]) -> bool:
    lower = text.lower()
    if not hints:
        return False
    if any(" " in hint and hint in lower for hint in hints):
        return True
    hits = sum(1 for hint in hints if hint in lower)
    return hits >= min(2, len(hints))


def main(argv: list[str] | None = None) -> int:
    return run_baseline(NAME, argv, drive)


if __name__ == "__main__":
    raise SystemExit(main())
