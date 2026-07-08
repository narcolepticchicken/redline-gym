# Redline Gym

**A verifiable-reward RL environment for transactional legal work — playbook-driven contract review and redlining.**

Aaron · aaron@litil.ai · July 2026

## The gap

Legal is one of the highest-value agent domains with almost no RL environment coverage. The closest public work, LegalWorld (arXiv 2606.18728, June 2026), covers Chinese civil *litigation* and scores almost entirely by LLM judge. Nothing public covers transactional work — contract review, the single highest-volume legal AI use case — with programmatic rewards. Redline Gym does.

## The core trick: ground truth as a byproduct of generation

Instances are manufactured, not annotated. Start from a clean, playbook-compliant contract; a mutation engine plants deviations against a 14-rule playbook (liability caps, care standards, use restrictions, notice obligations…) and writes the answer key **in the same operation as each edit** — span-level, mechanism-tagged, with the prescribed fallback edit. No model ever decides correctness after documents exist. Rewards are computed from that record:

- **recall / precision** on planted deviations (span + cited-rule match)
- **grounding** — every flag must exact-quote the shipped document
- **fallback match** — proposed redline vs. the playbook's prescribed edit
- **schema conformance** of the work product; **abstention** on deliberate gaps (e.g. personal data flows but the NDA is silent on privacy — agent must escalate, not invent)
- **honeypots** — canary rules the contract complies with; a flag citing one marks the episode GAMED and zeroes precision

No LLM judge in the reward path. A subscription-CLI judge exists only as a post-hoc tiebreak on fallback wording, never inside an episode.

## The legitimacy protocol (the part we think matters most)

Every instance passes 11 validators (mutation anti-drift, round-trip detectability, realism scoring, cross-tranche leakage scan, canary-emptiness), then tri-model QA — GPT-5.5 drafts, Claude Opus reviews, DeepSeek adjudicates disagreements — then a human lawyer signs off. Environment-level gates run before any score is believed: **null agent ≤ 0.05, cheater < honest, grep-bot as a published upper bound on keyword-detectability**.

These gates have already earned their keep. In week one they caught: a scorer paying a do-nothing agent 0.55 composite via vacuous defaults (precision=1.0 when nothing is claimed); the honeypot label "Canary:" leaking into agent-visible rule text; and a baseline with an answer-key string hardcoded in. All fixed, all documented. This follows from prior work on agent-eval measurement validity (the "harness floor" paper — scores that come from scaffold, not skill).

## Status & trajectory

Working today: episode loop (gym-style reset/step, JSONL transcripts), a seeded
generator with refuse-to-emit gates (keyword-leakage, structural coherence,
answer-key anchoring, distractor-span integrity), 36 dev + 8 held-out instances
across 7 practice areas (NDA, MSA, DPA/privacy, employment, corporate
governance, M&A, AI services, digital-asset custody), five scripted baselines
plus a four-strategy mechanical gaming suite, multi-sampled model-backed
validators (clean-base, round-trip detectability, gap-finding, register
battery) with metered judge spend, per-channel score decomposition, HTML
graded-redline reports, and one-command reproducibility (fresh clone →
identical gate table, proven). Measured on the discriminating tier with
GLM-5.2: keyword-bot ≤ 57% of honest everywhere; mechanical gaming ceilings
0.41–0.58 vs honest engaged performance 0.81–0.97; do-nothing scores exactly
0. Every gate number ships with its measured token cost; unmeasured gates say
UNMEASURED. Human sign-off runs through a single-attorney review sitting with
span-level walkthroughs; the validity report states coverage and limits
plainly. A verifiers-compatible wrapper for hub publication is v0.2.

**Ask:** feedback on the design, and interest in the Hub as a home for the first transactional-legal environment.
