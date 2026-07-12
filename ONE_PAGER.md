# Redline Gym

**A verifiable-reward RL environment for transactional legal work — playbook-driven contract review and redlining.**

Aaron · aaron@litil.ai · July 2026

## The gap

Legal is one of the highest-value agent domains with almost no RL environment coverage. The closest public work, LegalWorld (arXiv 2606.18728, June 2026), covers Chinese civil *litigation* and scores almost entirely by LLM judge. Nothing public covers transactional work — contract review, the single highest-volume legal AI use case — with programmatic rewards. Redline Gym does.

## The core trick: ground truth as a byproduct of generation

Instances are manufactured, not annotated. Start from a clean, playbook-compliant contract; a mutation engine plants deviations against a 14-rule playbook (liability caps, care standards, use restrictions, notice obligations…) and writes the answer key **in the same operation as each edit** — span-level, mechanism-tagged, with the prescribed fallback edit. No model ever decides correctness after documents exist. Rewards are computed from that record:

- **recall / precision** on planted deviations (span + cited-rule match)
- **grounding** — every flag must exact-quote the shipped document
- **fallback match** — the proposed redline text graded deterministically
  against the expected edit emitted at plant time (exact / span / containment
  tiers — no judge)
- **schema conformance** of the work product; **abstention** on deliberate gaps (e.g. personal data flows but the NDA is silent on privacy — agent must escalate, not invent)
- **honeypots** — canary rules the contract complies with; a flag citing one marks the episode GAMED and zeroes precision
- **clean-document instances** — contracts where the right answer is "sign it";
  credit requires demonstrably reading the documents first, so restraint is
  measured, not presumed (the do-nothing agent scores exactly 0 on these too)

No LLM judge in the reward path. A subscription-CLI judge exists only as a post-hoc tiebreak on fallback wording, never inside an episode.

## The legitimacy protocol (the part we think matters most)

Every instance passes 13 validators (mutation anti-drift, round-trip detectability, realism scoring, cross-tranche leakage scan, canary-emptiness, redline-text consistency, clean-instance integrity), then tri-model QA — GPT-5.5 drafts, an independent second model reviews, a third adjudicates disagreements — then a human lawyer signs off. Environment-level gates run before any score is believed: **null agent ≤ 0.05, cheater < honest, grep-bot as a published upper bound on keyword-detectability**.

These gates have already earned their keep. In week one they caught: a scorer paying a do-nothing agent 0.55 composite via vacuous defaults (precision=1.0 when nothing is claimed); the honeypot label "Canary:" leaking into agent-visible rule text; and a baseline with an answer-key string hardcoded in. All fixed, all documented. This follows from prior work on agent-eval measurement validity (the "harness floor" paper — scores that come from scaffold, not skill).

## Status & trajectory

Working today: episode loop (gym-style reset/step, JSONL transcripts), a seeded
generator with refuse-to-emit gates (keyword-leakage, structural coherence,
answer-key anchoring, distractor-span integrity), 43 dev + 8 held-out instances
across 7 practice areas (NDA, MSA, DPA/privacy, employment, corporate
governance, M&A, AI services, digital-asset custody) including 7 clean-document
instances, five scripted baselines plus a five-strategy mechanical gaming
suite, multi-sampled model-backed validators (clean-base, round-trip
detectability, gap-finding, register battery) with metered judge spend,
per-channel score decomposition plus reporting-only review-style telemetry
(duplicate-finding density, per-category recall), HTML graded-redline reports,
and one-command reproducibility (fresh clone → identical gate table, proven).
Measured on the discriminating tier with GLM-5.2: keyword-bot ≤ 57% of honest
everywhere; mechanical gaming ceilings 0.41–0.53 (re-derived after redline-text
scoring landed — tightening the scorer moved every ceiling DOWN) vs honest
engaged performance 0.81–0.97; do-nothing scores exactly 0. Every gate number
ships with its measured token cost; unmeasured gates say UNMEASURED. Human
sign-off runs through a single-attorney review sitting with span-level
walkthroughs; the validity report states coverage and limits plainly. A
verifiers-compatible wrapper is packaged on the Prime Environments Hub
(deterministic rubric, no API keys needed to score).

## It trains models

A Qwen3.5-9B trained on 670 examples distilled inside this environment, evaluated
against the untuned base on the same lane (n=10 sampled, replication verified):
**0.352 → 0.691 across 12 tasks, every one improved.** Gains are largest on tasks
the model never trained on (+0.368) — no memorization signature. The base model
abandons the review (empty finalize, no reading) in 24/120 episodes; the trained
model in 1/120. Reliability is the mechanism.

The negotiation tier (two-phase: the counterparty answers your redline) discriminates
as designed — 15 mechanical strategies score 0.000–0.20, an engaged frontier model
averages 0.611 with 21/28 instances inside the pre-registered 0.40–0.80 band.

**Ask:** feedback on the design, and interest in the Hub as a home for the first transactional-legal environment.
