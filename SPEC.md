# Redline Gym — Build Spec v0.1 (2026-07-06)

An RL environment for playbook-driven contract review. One world, five reward
channels. Instances are manufactured by a forward-generation pipeline (Aaron's
reconstructed dataset-creator design) so every task ships with a perfect,
machine-written answer key. The environment wraps those instances with an
episode loop, deterministic scoring, and a legitimacy harness.

**Two-layer legitimacy** (the organizing idea):
- **Instance-level** — every generated task passes cross-referential validators
  and emits a `verification_report.md` (Aaron's design).
- **Environment-level** — the whole env passes baseline gates (null / grep-bot /
  cheater / honest) before any score from it is believed or trained on.

---

## 1. Design invariants (non-negotiable)

1. **Ground truth is a byproduct of generation, never a post-hoc annotation.**
   The mutation engine writes `planted_deviations.json` *as it edits*. No model
   ever "decides correctness" after documents exist. (The Ferrari gets an
   engine first.)
2. **Validators are written before the generator.** The schema + validators are
   the contract; the generator must satisfy them, not vice versa.
3. **Deterministic world in v1.** Document store only — no model-driven
   counterparty. Reproducible episodes, pinned seeds.
4. **Deterministic-first reward.** Span matches, schema checks, string-verified
   quotes. An LLM judge appears only as a tiebreak on fallback-edit correctness,
   never as the primary reward source.
5. **Harness isolation.** Agent rollouts run through the lab's own serving/eval
   scripts only — never through Claude Code's or Codex's harness. Judge
   tiebreaks are post-hoc scoring of static transcripts (subscription
   `claude -p`, invoked by eval scripts after the episode ends) — never inside
   a live episode. Codex builds code; it does not execute experiments.
6. **Observability from hour one.** Every episode logs full transcript +
   per-channel reward breakdown. No composite score without its decomposition.
7. **Legitimacy gates precede use.** No training run, no reported number, until
   §8 gates pass. Measured cost units only; spend gated on Aaron's console.

---

## 2. Repo layout (greenfield in labs1/)

```
redline-gym/
  schema/          # JSON Schemas for every artifact in §3
  validators/      # §5 checks; runnable as `python -m validators <task_dir>`
  generator/       # playbook authoring, base-doc prep, mutation engine
  env/             # episode loop, tools, observation/action handling
  scoring/         # §7 reward channels + composite
  baselines/       # null, random, grep-bot, honest, cheater runners
  report/          # HTML graded-redline renderer (per-episode + tranche)
  tasks/           # generated instances: tasks/<practice_area>/<task_id>/
  playbooks/       # one playbook per practice area
  scripts/         # run_episode.py, run_baselines.py, make_tranche.py
```

---

## 3. Instance schema (per-task artifact contract)

Each `tasks/<area>/<task_id>/` contains exactly:

- **task.json** — task_id, practice_area, client_context, instruction
  (≤300 chars), deliverable spec (card schema id), turn_cap, difficulty tier.
- **documents_manifest.json** — per doc: doc_id (DOC-##), title, type
  (msa|sow|nda|addendum|exhibit), path, sha256, is_distractor flag.
- **playbook ref** — pointer to `playbooks/<area>/<playbook_id>.json`; per rule:
  rule_id (R-###), position (the required stance), fallback (prescribed edit
  text), severity, escalation_trigger. Includes **canary rules** (see §7.7).
- **planted_deviations.json** — the answer key, written by the mutator at edit
  time. Per deviation: deviation_id (D-###), rule_id, doc_id, clause_anchor
  (section + exact span), original_text, mutated_text, mechanism (enum:
  direct_term_swap | cross_ref_override | defined_term_shift | omission |
  off_playbook_addition | cross_doc_override), severity, expected_action
  (redline_with_fallback | flag_only | escalate).
- **issue_matrix.json** — derived mechanically: issue_id ↔ deviation_id(s) ↔
  rule_id ↔ doc_id(s); plus intentional missing_info items and distractor
  registry (distractor_id, doc_id, span, why_benign).
- **rubric.json** — derived mechanically from issue_matrix + card schema:
  per-channel weights and per-issue points. Never hand-edited.
- **verification_report.md** — validator output + generation log digest +
  human sign-off line (name, date). A task without a signed report is not in
  the eval set.

Derivation order is one-way: playbook → base docs → mutations (writes
deviations) → issue_matrix → rubric. Any regeneration restarts from the break
point; no downstream artifact is ever edited by hand.

---

## 4. Generation pipeline

1. **Playbook authoring** — 12–15 rules per practice area. Drafted by model,
   red-penned by Aaron (the human gate). Frozen before doc generation.
2. **Base documents** — clean, playbook-COMPLIANT contracts. Source: open
   permissively-licensed forms (oneNDA, Bonterms, Common Paper) adapted to the
   client_context. Validator V3 proves the clean base scores zero issues.
3. **Mutation engine** — sample K deviations (mechanisms weighted by difficulty
   tier), D distractors, M missing-info items; apply edits; log each to
   `planted_deviations.json` in the same operation as the edit.
4. **Mechanical derivation** — issue_matrix.json, rubric.json.
5. **Validators** (§5) — all must pass; emit verification_report.md.
6. **Human spot-check** — Aaron signs the report (~15 min/task).

Difficulty tiers: T1 = single doc, direct swaps only. T2 = single doc,
cross_ref_override + defined_term_shift + omission in play. T3 = multi-doc
(MSA + SOW + addendum), cross_doc_override in play.

Generator rules (tiebreak-settled 2026-07-06): cross_ref_override sections get
innocuous headings — never "override"-style tells. Playbook escalation_triggers
use generic language; they must never describe a planted mechanism. Canary
(honeypot) detection is by cited rule_id only: a flag citing a canary rule ⇒
GAMED; a flag on the same span citing another/no rule ⇒ ordinary false flag.
expected_action must be mechanically consistent with the rule's
escalation_trigger (a term past an escalation threshold ⇒ escalate).

---

## 5. Instance validators (all must pass; each is a runnable check)

V1. Every rubric criterion cites doc_ids and deviation_ids that exist.
V2. Every planted deviation's mutated_text appears verbatim at its recorded
    clause_anchor in the shipped doc (anti-drift).
V3. Clean-base check: pre-mutation docs score ZERO issues against the playbook
    (programmatic scan + one judge pass).
V4. Round-trip detectability: an independent extractor model, given docs +
    playbook (NOT the answer key), locates ≥ threshold of planted deviations —
    catches mutations that got mangled or are undetectable-in-principle.
V5. Every issue maps to ≥1 deviation; every deviation maps to exactly 1 rule.
V6. Distractor integrity: no distractor span violates any playbook rule.
V7. Missing-info items are provably absent (string + semantic search over docs).
V8. Instruction ≤300 chars; all artifacts schema-valid; all sha256s match.
V9. Canary rules have zero planted deviations (honeypots stay empty).
V10. Leakage scan across the tranche: deviation positions, section numbers, and
    surface phrasings are not constant (shortcut-feature check).
V11. Realism/coherence: a judge scores each shipped doc 0–10 on "reads as a
    coherent, professionally drafted contract"; gate ≥8. Prevents the shortcut
    where mutated clauses sound "off" and the model learns to flag weird prose
    instead of playbook violations. (Adapted from LegalWorld's
    stage-authenticity preflight.)

---

## 6. Environment wrapper

- **reset(task_dir, seed)** → observation: instruction, client_context, doc
  manifest (titles only), full playbook. Agent-visible playbook rendering shows
  rule_id, position, fallback, severity ONLY — never is_canary or any other
  answer-key metadata, and rule text must never contain trap language
  (tiebreak-adjacent fix 2026-07-06: "Canary:" prefixes stripped from positions).
- **Actions** (JSON): `list_docs` · `read_doc(doc_id, start, end)` ·
  `search(query)` (lexical, over doc store) · `flag_issue(rule_id, doc_id,
  clause_ref, exact_quote, severity, proposed_redline, rationale)` ·
  `escalate(topic, reason)` · `finalize(card)`.
- **Episode ends** on `finalize` or turn_cap (default 25). No auto-finalize
  credit: an episode that times out scores only what was already flagged, and
  conformance scores zero (no card = no card).
- Full transcript persisted per episode: `runs/<run_id>/<task_id>/episode.jsonl`.
- Interface kept gym-like (reset/step) behind an adapter so a `verifiers`-style
  wrapper can be added without touching env internals. (Final call pends the
  LegalWorld/verifiers read — see §11.)

---

## 7. Scoring channels (terminal, with logged decomposition)

| # | Channel      | Default wt | Computation |
|---|--------------|-----------|-------------|
| 1 | recall       | 0.35 | planted deviations correctly flagged (rule_id + doc_id + anchor overlap) |
| 2 | precision    | 0.15 | 1 − false_flags/total_flags (flags not matching any deviation) |
| 3 | grounding    | 0.15 | flagged exact_quote string-matches the shipped doc at claimed anchor |
| 4 | fallback     | 0.15 | proposed_redline matches playbook fallback (normalized exact → judge tiebreak) |
| 5 | conformance  | 0.10 | deterministic card-schema validator pass (binary per field group) |
| 6 | abstention   | 0.10 | missing_info items escalated, playbook-silent items not answered |
| 7 | **honeypot** | gate | flagging a canary rule ⇒ precision channel zeroed + episode marked GAMED |

Weights are defaults, tunable per experiment; the decomposition is always
reported. No reward for verbosity anywhere; rationale text is unscored in v1.

**Vacuous-credit rule (2026-07-06 null-gate postmortem — null agent scored
0.55 from empty-work defaults):** no channel may award credit for absence of
work. Zero flags ⇒ precision, grounding, and fallback = 0 (skill must be
demonstrated, not presumed). Fallback = fraction of correctly-flagged
redline_with_fallback deviations whose proposed edit matches; none flagged ⇒ 0.
Conformance requires a schema-valid card AND ≥1 substantive action (flag_issue
or escalate); an empty card earns nothing. Baselines must never contain
answer-key strings (grep-bot's keyword source is the playbook only; its
privileged use of deterministic_checks makes it an UPPER-BOUND grep-ability
diagnostic, and it never escalates).

---

## 8. Environment-level legitimacy gates (run before any use)

Baselines (all via lab serving scripts, never Claude Code/Codex harness):
- **null** — finalizes immediately. Gate: composite ≤ 0.05. If higher, the env
  is paying out for scaffold, not agent (harness-floor test).
- **random-flagger** — flags random clauses. Gate: ≈ precision noise floor.
- **grep-bot** — keyword-matches playbook terms, no reading. Gate: ≤ 60% of
  honest composite. Measures how much of the env is grep-able; drives more
  cross_ref_override instances if too high.
- **honest** — strong model, straight prompt. Gate: composite in 0.40–0.80
  (not floored, not saturated).
- **cheater** — explicitly prompted to game (verbose flags, blanket flagging,
  canary claims). Gate: strictly < honest. (Institutionalizes the 0.51-vs-0.81
  bypass finding: gaming must lose.)

Also: seed-variance across ≥3 generation seeds reported; per-channel breakdown
for every baseline; **judge-alignment sampling** — for any channel using an LLM
judge (fallback tiebreaks, V11 realism), sample ≥20 judged decisions per tranche
for human agreement, report mean diff + within-one-point rate (LegalWorld §4.2
protocol, miniaturized); ops note — pgrep for concurrent sessions before any
paid run; measured cost per rollout on 10 episodes before scaling anything
(target ≤30K tokens/episode — LegalWorld's ~500K/case is the anti-pattern).

---

## 9. Report renderer

Static HTML per episode: the contract with planted deviations highlighted —
caught (green), missed (red), false flag (yellow), canary claim (black) — plus
the per-channel score bar and the agent's card. Tranche page: grid of episodes ×
channels. This artifact is the demo: legible to a non-ML viewer in ten seconds.

---

## 10. Build order & scope

- **Phase 1 (day 1):** schema/ + validators/ + scoring core. Hand-assemble one
  T1 NDA instance through the pipeline in manual mode (smoke test).
- **Phase 2 (day 2):** env wrapper + baselines + report renderer. Build the
  showpiece T3 instance: vendor MSA + SOW + security addendum, crypto client
  (Aaron's sample task). Run all §8 gates on the two instances.
- **Phase 3:** mutation engine fully automated; generate the 7-task tranche
  (one per practice area: contracts, corporate governance, employment,
  cybersecurity/privacy, M&A, AI law, crypto law). Aaron signs 7 reports.
- **Phase 4:** scale 7 → 35 (5/area) → 350; difficulty curriculum; optional
  verifiers-compat wrapper + Environments Hub packaging.

---

## 11. Open items

**LegalWorld read — resolved 2026-07-06** (repo: github.com/chidaic/Legal-world;
study notes in scratchpad legalworld-study/REPORT.md): Chinese civil-litigation
lifecycle, ~entirely LLM-judge-scored, no English / transactional / programmatic
rewards — gap confirmed. Adopted: environment-validity preflight (→ V11 + §8
judge-alignment sampling); manifest-gated tool access pattern noted for later
phases. Interface: gym-like reset/step behind an adapter; verifiers-compat
wrapper deferred to Phase 4.

**Decisions locked 2026-07-06 (Aaron):**
1. Reconstructed dataset-creator code: existence unknown — Aaron checking
   another machine. Building fresh to this spec; if the code surfaces, diff it
   against generator/ before Phase 3.
2. Playbook QA pipeline: draft (GPT-5.5 via codex) → independent review by a
   Claude-family subagent (different family than the drafter) → disagreements
   tie-broken by a third family (GLM/DeepSeek token-plan lane) → Aaron red-pens
   (final human gate, ~30 min/area).
3. Base docs: open-source forms approved (oneNDA / Bonterms / Common Paper),
   adapted per instance. The Phase 1 NDA was written from scratch.
4. Baseline serving lane: GLM-5.2 (token-plan lane). All §8 baselines on the
   same lane; never compare scores across lanes; cost measured on 10 episodes
   before scaling.
5. Judge tiebreaks (channel 4, V11): Sonnet via subscription ONLY — headless
   `claude -p` invoked by eval scripts, post-hoc on static transcripts. No
   Anthropic API keys anywhere. Never inside a live episode (invariant 5).
6. Aaron signs verification reports (~15 min/task).
7. Repo home: labs1/redline-gym (git-inited; commits only on Aaron's say-so).
