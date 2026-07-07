#!/usr/bin/env python3
"""Third-model tiebreak (tri-model pipeline, step 3 of 3), via GLM.

Usage: GLM_API_KEY=... python3 scripts/tiebreak_instance.py <task_dir>
Reads <task_dir>/qa/review_deepseek.md (section e, contested items), asks GLM to
rule on each, writes <task_dir>/qa/tiebreak_glm.md and prints it.
"""
import json
import os
import pathlib
import sys
import urllib.request

task_dir = pathlib.Path(sys.argv[1])
review = (task_dir / "qa" / "review_deepseek.md").read_text()

api_key = os.getenv("GLM_API_KEY")
if not api_key:
    sys.exit("GLM_API_KEY not set; tiebreak is gated on the lab serving lane")

prompt = f"""You are the third-family tiebreaker in a tri-model QA pipeline for an RL-environment
task instance (drafter: GPT-5.5, reviewer: DeepSeek). Below is the reviewer's full report.
Rule ONLY on its CONTESTED ITEMS section: for each numbered item, output the item number,
a ruling (side with DRAFTER or REVIEWER, or a specific third resolution), and <=3 sentences
of rationale. Favor rulings that keep the answer key unambiguous, machine-checkable, and the
document realistic. If the contested list is empty, say NO CONTESTED ITEMS.

REVIEWER REPORT:
{review}
"""

payload = {"model": "glm-5.2", "messages": [{"role": "user", "content": prompt}],
           "temperature": 0, "max_tokens": 3000}
request = urllib.request.Request(
    "https://api.z.ai/api/coding/paas/v4/chat/completions",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(request, timeout=180) as response:
    data = json.loads(response.read().decode("utf-8"))
ruling = data["choices"][0]["message"]["content"]
(task_dir / "qa" / "tiebreak_glm.md").write_text(ruling)
print(ruling)
print(f"\nwritten to {task_dir / 'qa' / 'tiebreak_glm.md'}")
