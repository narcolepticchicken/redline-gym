#!/usr/bin/env python3
"""Second-model QA review of a task instance (tri-model pipeline, step 2 of 3:
GPT-5.5 drafts -> DeepSeek reviews -> third-family tiebreak -> human red-pen).

Usage: DEEPSEEK_API_KEY=... python3 scripts/review_instance.py <task_dir>
Writes <task_dir>/qa/review_deepseek.md and prints it.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from scoring.judge_deepseek import DeepSeekJudge  # noqa: E402


def _print_judge_usage() -> None:
    totals = DeepSeekJudge.usage_totals()
    print(
        f"judge usage: {totals['prompt_tokens']} prompt + "
        f"{totals['completion_tokens']} completion tokens across {totals['calls']} calls"
    )


try:
    task_dir = pathlib.Path(sys.argv[1])
    task = json.loads((task_dir / "task.json").read_text())
    pdv = json.loads((task_dir / "planted_deviations.json").read_text())
    pb_path = pathlib.Path(task["playbook_ref"])
    pb = json.loads(pb_path.read_text() if pb_path.exists()
                    else (task_dir / "../../.." / task["playbook_ref"]).resolve().read_text())
    docs = "\n\n".join(f"--- {p.name} ---\n{p.read_text()}" for p in sorted((task_dir / "docs").glob("*.md")))

    prompt = f"""You are the independent second-model reviewer in a tri-model QA pipeline for an
RL-environment task instance (drafter: GPT-5.5; you must be adversarial, not polite).
The instance: a contract with planted playbook deviations; an agent is scored on finding
them. Ground truth must be unambiguous, machine-scorable, and realistic.

CLIENT CONTEXT: {task['client_context']}
INSTRUCTION: {task['instruction']}

PLAYBOOK (rules; is_canary marks honeypots the doc must comply with):
{json.dumps(pb['rules'], indent=1)}

DOCUMENTS (as shipped, mutations already applied):
{docs}

ANSWER KEY (planted deviations, distractors, missing_info):
{json.dumps(pdv, indent=1)}

REVIEW — output these sections in order, be specific, cite sections/quotes:
(a) PER-RULE: for each rule, CONCUR or DISSENT with one-line reason (legal soundness of
    position+fallback+severity; would a real company hold this stance?).
(b) PER-DEVIATION: for each planted deviation, VALID / QUESTIONABLE / INVALID — does the
    mutated text genuinely violate the cited rule? Would a competent human reviewer find it?
    Does it read as natural drafting (nothing that sounds planted)?
(c) DISTRACTORS: does each stay fully playbook-compliant? CANARIES: truly deviation-free in
    the doc AND tempting to over-flag? MISSING-INFO: genuinely absent AND clearly
    escalation-worthy given the client context?
(d) KEYWORD LEAKAGE: do any mutated spans share distinctive keywords with playbook rule text
    or deterministic_checks (would a grep bot catch them)? List any.
(e) CONTESTED ITEMS: a numbered list of crisp yes/no questions where you dissent from the
    drafter, formulated so a third model can adjudicate each independently.
(f) OVERALL: FIT FOR HUMAN RED-PEN AS-IS, or NEEDS REVISION FIRST (say exactly what).
"""

    judge = DeepSeekJudge()
    review = judge._chat(prompt, max_tokens=5000)
    out = task_dir / "qa"
    out.mkdir(exist_ok=True)
    (out / "review_deepseek.md").write_text(review)
    print(review)
    print(f"\nwritten to {out / 'review_deepseek.md'}")
finally:
    _print_judge_usage()
