# Redline Gym

**A practice world with an automatic grader for AI contract-reviewers — where every score can be checked by a skeptical lawyer, because every planted mistake is on the record.**

Redline Gym generates realistic legal contracts with **known, deliberately planted problems**, gives an AI agent the documents plus the client's playbook, and mechanically scores whether the agent found the problems, quoted the right clauses, proposed the right fixes, and raised the right questions. No LLM judge decides correctness. The answer key exists before the agent ever sees the document — because we wrote the mistakes in ourselves.

- **44 task instances** across 7 practice areas: NDAs, vendor MSAs, data-processing agreements, executive employment, stockholders' agreements, M&A asset purchases, AI vendor agreements, digital-asset custody
- **Deterministic span-level rewards** — recall/precision on planted mistakes, exact-quote grounding, fallback-edit matching, schema conformance, abstention on deliberate gaps
- **Built-in honeypots and baselines** that catch bluffing, keyword-matching, and doing nothing
- **One command reproduces the published gate table** from a fresh clone
- Apache-2.0

---

## The idea in one example

Every instance starts from a clean, playbook-compliant contract. A mutation engine plants mistakes and writes the answer key *in the same operation*:

> **The client's playbook says:** Confidential Information covers all non-public information disclosed by either party — oral, visual, written, electronic — whether or not marked.
>
> **The planted contract says:** *"Confidential Information" means information disclosed by or on behalf of a Discloser that is **marked confidential at the time of disclosure** or confirmed as confidential in writing **within ten days** after disclosure.*

That clause isn't gibberish — it's what opposing counsel actually sends you. An agent scores by flagging it, quoting it exactly, and proposing the playbook's fix. Mistakes here are never typos; they're **terms that hurt the client**, findable only by reading. The hard tier buries them in poisoned definitions and innocent-looking "Notwithstanding…" clauses several sections away.

## How we know the scores mean anything

Anyone can claim their benchmark measures skill. Redline Gym ships the evidence:

| Check | What it catches | Result (published table) |
|---|---|---|
| **Do-nothing agent** | Scores paid out by scaffolding | 0.000 everywhere |
| **Keyword bot** (given the scoring keywords!) | Instances solvable by Ctrl-F | ≤ 57% of honest, 0% recall on the hard tier |
| **Four mechanical cheating strategies** | Blanket-flagging, canary-citing, quote fabrication, playbook parroting | All lose or get branded GAMED |
| **Honeypot rules** | Agents inventing violations | Episode marked GAMED, precision zeroed |
| **Honest frontier model** (GLM-5.2, n=5/task) | Whether reading actually wins | 0.67–0.76 on dev T2; **0.82–0.93 on held-out** |
| **Fresh-clone reproduction** | "Works on my machine" | Gate table byte-identical |

Every instance also passes 11 programmatic validators (mutation anti-drift, keyword-leakage scans, structural coherence, answer-key anchoring), an adversarial three-model QA pipeline (draft → independent review → tiebreak), and an attorney review protocol — coverage stated exactly in [`reports/attorney_signoff_v01.md`](reports/attorney_signoff_v01.md).

## What we found (including against ourselves)

The held-out one-shot evaluation ran once, after the ground truth locked, and its results are published as measured ([`reports/gate_results_t2.md`](reports/gate_results_t2.md)):

- **Strategy gates hold.** Doing nothing, grepping, and every gaming strategy lose on instances no development process ever touched.
- **The difficulty band failed high.** An engaged frontier-lane model scores 0.82–0.93 on the hard tier — the tier is easier for strong models than our calibration assumed. This is a real negative finding and it ships on the label; recalibration (multi-document T3 tier) is the v0.2 headline.
- **Models sometimes just… quit.** GLM-5.2 occasionally submits an empty review even after a confirmation bounce (~1 in 5 episodes; worse on some instance families). The environment scores this honestly as zero — it's a reliability behavior the environment measures, not noise we hide.

During three days of construction, this verification stack caught (in our own work): a scorer paying 55% for doing nothing, honeypot labels visible to the agent, answer-key items graders couldn't reach, phantom distractor spans, unreliable single-sample judging, and a generator emitting out-of-order sections. Every one is in the commit history. **The pipeline that catches defects is the product; the contracts are the demo.**

## Quickstart

```bash
git clone https://github.com/narcolepticchicken/redline-gym
cd redline-gym
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
./scripts/run_gates.sh          # reproduces the deterministic gate table, no API keys needed
python3 scripts/make_validity_report.py
```

With no API keys, every deterministic result reproduces and model-backed steps print `SKIPPED` rather than silently passing. To run live agents or the model-backed validators, export `GLM_API_KEY` / `DEEPSEEK_API_KEY` (any OpenAI-compatible endpoints; see `baselines/llm_common.py`).

Run one episode yourself:

```bash
python3 -m baselines.grep_bot --task tasks/generated/T2-DPA-302 --seed 0    # watch keyword-matching fail
python3 -m baselines.honest_llm --task tasks/generated/T2-DPA-302 --seed 0  # needs GLM_API_KEY
```

## What's in the box

| Path | What it is |
|---|---|
| `tasks/` | 36 dev instances + 8 held-out (never touched in development; scored once) |
| `playbooks/` | 7 practice-area playbooks — the client positions that define ground truth |
| `generator/` | Seeded mutation engine; refuses to emit instances failing any integrity gate |
| `env/` | Gym-style episode loop (read, search, flag, escalate, finalize) |
| `scoring/` | Seven deterministic reward channels + honeypot gating |
| `baselines/` | Null, random, grep-bot, mechanical cheaters, honest/cheater LLM drivers |
| `validators/` | The 11-check instance validator stack |
| `reports/` | Gate tables, validity report, attorney sign-off record, consensus results |
| `SPEC.md` | The full design contract, including the release checklist this repo shipped against |

## Known limits (v0.1)

Stated plainly, per the project's own rules: single-attorney review with declared partial coverage (record in `reports/`); difficulty band miscalibrated for frontier models (see above); one model lane measured (no stronger-vs-weaker ranking yet); English-only, US-market conventions; 44 instances is a pilot-scale distribution.

## Roadmap

**v0.1.1** — remaining attorney review items, two deferred rule adjudications. **v0.2** — T3 multi-document tier and band recalibration, multi-model rankings, quit-mode study, `verifiers`-compatible wrapper for hub publication. **v1.0** — 35+ instances per area, RL training runs.

## Citation

```bibtex
@software{redline_gym_2026,
  title  = {Redline Gym: a verifiable RL environment for playbook-driven contract review},
  author = {Aaron and contributors},
  year   = {2026},
  url    = {https://github.com/narcolepticchicken/redline-gym},
  license = {Apache-2.0}
}
```

Built in the open, defects and all. If you find a mistake we didn't plant — file an issue; that's the point.
