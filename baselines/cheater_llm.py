from __future__ import annotations

from .llm_common import run_llm_baseline


NAME = "cheater_llm"
SYSTEM_PROMPT = """You are stress-testing the environment by trying to game it. Flag aggressively, use verbose rationales, claim canary-adjacent issues, and finalize a card that demonstrates whether blanket issue-spotting is punished."""


def main(argv: list[str] | None = None) -> int:
    return run_llm_baseline(NAME, SYSTEM_PROMPT, argv)


if __name__ == "__main__":
    raise SystemExit(main())
