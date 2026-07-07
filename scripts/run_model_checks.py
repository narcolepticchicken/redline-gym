#!/usr/bin/env python3
"""Run the four model-backed validators (V3, V4, V7-semantic, V11) on a task
via the Claude subscription judge. Writes outputs to <task_dir>/model_checks/.

Usage: REDLINE_JUDGE_ENABLED=1 python3 scripts/run_model_checks.py [task_dir]
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from scoring.judge_deepseek import DeepSeekJudge  # noqa: E402

task_dir = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "tasks/contracts/T1-NDA-001")
out_dir = task_dir / "model_checks"
out_dir.mkdir(exist_ok=True)

task = json.loads((task_dir / "task.json").read_text())
pdv = json.loads((task_dir / "planted_deviations.json").read_text())
doc_path = next((task_dir / "docs").glob("*.md"))
shipped = doc_path.read_text()

pb_ref = task["playbook_ref"]
pb = json.loads((task_dir / "../../.." / pb_ref).resolve().read_text()) if not pathlib.Path(pb_ref).exists() else json.loads(pathlib.Path(pb_ref).read_text())

# Agent-visible playbook rendering only (rule_id, position, fallback, severity).
pb_text = "\n".join(
    f'{r["rule_id"]} [{r.get("severity","")}]\nPosition: {r["position"]}\nFallback: {r["fallback"]}'
    for r in pb["rules"]
)

# Reconstruct the clean pre-mutation base by reverting each recorded mutation.
clean = shipped
for d in pdv["deviations"]:
    if clean.count(d["mutated_text"]) != 1:
        sys.exit(f'cannot revert {d["deviation_id"]}: span count {clean.count(d["mutated_text"])}')
    clean = clean.replace(d["mutated_text"], d["original_text"], 1)

judge = DeepSeekJudge()
results = {}

results["V3_clean_base"] = judge.clean_base_judge_pass(
    "This is the CLEAN BASE contract. Check it against the playbook. "
    "It should contain ZERO playbook violations. List any violation you find with section + quote; "
    "if none, say PASS: no violations.\n\n" + clean,
    pb_text,
)

results["V4_round_trip"] = judge.round_trip_extractor(
    "This is the SHIPPED contract. Independently list EVERY playbook violation you can find. "
    "For each: section number, exact quote, violated rule_id. Be thorough; do not guess beyond the text.\n\n"
    + shipped,
    pb_text,
)

results["V7_semantic"] = judge.missing_info_semantic_search(
    f"Client context: {task['client_context']}\n\n"
    "Given this context, name any material topic this contract is SILENT on that a careful reviewer "
    "should escalate. Cite why. If none, say none.\n\n" + shipped,
    pb_text,
)

results["V11_realism"] = judge.realism_judge(
    "Score this contract 0-10 on reading as a coherent, professionally drafted agreement "
    "(consistent defined terms, natural clause wording, no passages that sound artificial or planted). "
    "Gate is >=8. Give the score first, then up to three weakest passages.\n\n" + shipped,
    pb_text,
)

for name, text in results.items():
    (out_dir / f"{name}.txt").write_text(text)
    print(f"=== {name} ===\n{text.strip()[:1200]}\n")
print("written to", out_dir)
