# T2 Gate Results — dev-set, bounce harness (final, 2026-07-07)

Harness: episode driver with one-time empty-submission confirmation bounce
(env commit `cfee1a3`), strict scorer, DeepSeek fallback tiebreak post-hoc.
Model: GLM-5.2, temperature 0, n=5 seeds per honest arm. All prior honest-arm
tables (no-bounce harness) are superseded and retained only in git history /
`runs_prebounce_2026-07-07/`.

## Honest arms (GLM-5.2, n=5)

| Task | Episodes (deterministic) | Mean | Judged mean | Band 0.40–0.80 |
|---|---|---:|---:|---|
| T2-MSA-001 (hand-built) | 0.0, 0.79, 0.79, 0.86, 0.91 | 0.671 | 0.680 | **PASS** |
| T2-DPA-302 | 0.0, 0.75, 0.84, 0.89, 1.0 | 0.695 | 0.701 | **PASS** |
| T2-EMP-702 | 0.0, 0.91, 0.94, 0.97, 0.97 | 0.758 | 0.770 | **PASS** |

Footnote (empty-confirm mode): each arm contains exactly one 0.0 episode in
which the model confirmed an empty submission past the bounce (rate 1/5,
down from 3/5 pre-bounce on DPA). Engaged-episode-only means: MSA 0.84,
DPA 0.87, EMP 0.95. Reported means include the zeros; the quit mode is model
behavior the environment measures, not harness failure.

## Gaming (mechanical ceilings, deterministic, seed 0)

| Task | blanket | canary_citer | fabricator | playbook_parrot | Max vs honest |
|---|---:|---:|---:|---:|---|
| T2-MSA-001 | 0.409 | 0.25 (GAMED) | 0.10 | 0.10 (GAMED) | 0.409 < 0.671 **PASS** |
| T2-DPA-302 | 0.469 | 0.25 (GAMED) | 0.10 | 0.10 (GAMED) | 0.469 < 0.695 **PASS** |
| T2-EMP-702 | 0.578 | 0.25 (GAMED) | 0.10 | 0.10 (GAMED) | 0.578 < 0.758 **PASS** |

Footnote (prompted-LLM cheater): across two days, GLM-5.2 under adversarial
"cheat" instructions did not produce gaming behavior — it either fabricated
(scored ≤0.1) or performed an honest review. Prompted-LLM cheating is
therefore reported qualitatively; the gaming gate is carried by the
deterministic mechanical strategies above.

## Do-nothing / keyword-bot

| Task | Null | Grep composite / recall | Grep ÷ honest | Gate ≤60% |
|---|---:|---:|---:|---|
| T2-MSA-001 | 0.0 | 0.250 / 0.0 | 37% | **PASS** |
| T2-DPA-302 | 0.0 | 0.250 / 0.0 | 36% | **PASS** |
| T2-EMP-702 | 0.0 | 0.365 / 0.2 | 48% | **PASS** |

## Measured spend (this table only)

Bounce-harness honest arms: 1,059,920 GLM tokens (15 episodes + retries).
Judge tiebreak rescore: logged in judge usage files. Superseded pre-bounce
batches (~2.2M GLM) documented in git history; not part of this table.

## Status vs SPEC §8 / §0.1-R4 (dev-set portion)

null ≈ 0 PASS · grep ≤ 60% PASS · gaming < honest PASS · honest in band PASS
(3/3). Held-out eval-mode run: NOT yet executed — fires once, after human
sign-offs lock (scripts/run_heldout_eval.sh, marker-guarded). Stronger-vs-
weaker model ranking: not measured (v0.2 scope; single-model lane).

---

# Held-out one-shot addendum (2026-07-08, marker burned — final)

8 instances, never touched in development, scored once (n=3 honest arms).
Strategy gates: null 0/8 failures; grep + mechanical-gaming gates PASS on 6/8
— the 2 failures (DPA-607, MSA-603) are arithmetic collapse of the honest
denominator, not strategy success (honest means 0.28/0.29 from the empty-
confirm quit mode striking 2/3 episodes; engaged episodes scored 0.84/0.87).

Honest band 0.40–0.80: FAILS on 7/8 as calibrated. Engaged GLM-5.2 runs
0.82–0.93 on held-out T2. Finding, stated plainly: the tier is easier for an
engaged frontier-lane model than the band assumed; the environment's
discriminative claims (reading beats null/grep/gaming) hold; its difficulty
calibration for strong models does not. v0.2 work: harder tier calibration
(T3 multi-document), band re-derivation, quit-mode study.

---

# Correction (2026-07-08, scorer-v2 finding) — the "empty-confirm quit mode" was misdiagnosed

v0.1 scoring credited only findings raised via interactive flag_issue actions.
Rescoring the same transcripts under v0.2 union semantics (action flags ∪
final-card issues; scripts/rescore_v2.py) shows every honest-arm 0.0 in the
tables above carried a populated findings card (4–6 matched findings each;
e.g. DPA-302 seed0: v1 0.0 → v2 0.55). The correct characterization is
WRONG-CHANNEL FILING, not quitting; v1-scored honest means understate the
models. The published v0.1 tables stand as measured under v1 semantics with
this correction attached; v0.2 will publish union-scored tables and a
recalibrated difficulty band (which this correction pushes further above the
v0.1 honest band). The confirmation-bounce message ("card is empty") was also
miscalibrated to v1 semantics — models with populated cards reasonably
confirmed it.

---

# Post-M2 mechanical re-derivation (2026-07-09 — tiered fallback scoring)

Dev instances regenerated with `expected_redline_text` (documents byte-identical;
`tasks/contracts/T2-MSA-001` hand-built, not regenerated, scores v1). Mechanical
baselines re-run deterministically, seed 0. Honest arms NOT re-run (spend-gated;
v0.2 tables will publish them under tiered semantics).

| Task | Baseline | Old | New | Δ |
|---|---|---:|---:|---|
| T2-MSA-001 (v1 path) | blanket | 0.409 | 0.4086 | ~0 (rounding) |
| T2-DPA-302 (tiered_v2) | blanket | 0.469 | 0.4088 | **−0.060** |
| T2-EMP-702 (tiered_v2) | blanket | 0.578 | 0.5256 | **−0.052** |
| T2-EMP-702 (tiered_v2) | grep-bot | 0.365 | 0.3575 | −0.008 |

All other mechanical baselines (null, cheater_empty, canary_citer, fabricator,
playbook_parrot) bit-identical to the prior table; canary_citer and
playbook_parrot still GAMED. Mechanism: blanket's verbatim-playbook-fallback
proposals are now graded against the drafted expected redline text and mostly
miss the exact/span/containment tiers, so its fallback contribution collapses —
the gaming ceilings move DOWN, widening every gate margin. Grep-bot loses a
small measured amount on EMP-702 for the same reason.

Clean-instance row (draft T1-MSA-9001, task_type=clean): all 7 mechanical
baselines score exactly 0.000000 — none performs read_doc/search, so the
engagement gate zeroes every channel. The do-nothing strategy on clean tasks
is measured at 0.0, not assumed. Note: cheater_empty is presently
code-identical to null_agent (both finalize empty and confirm); it exists as a
named battery entry for the clean-task gate.

---

# v0.2 honest arms (2026-07-09/10 — v2 union + tiered fallback, GLM-5.2)

Measured spend: 2.72M GLM tokens (36 scored episodes + 3 discarded pre-fix EMP
episodes, 263 calls). Live-scored under v2 union semantics with tiered
redline-text matching (fallback_scoring: tiered_v2 on regenerated instances).

## Clean instances (n=3 seeds × 7 instances)

Overall mean 0.857; 18/21 episodes scored a perfect 1.0; zero GAMED; zero
over-flagging episodes against defect-free instances. The three non-perfect
episodes were all ENGAGEMENT-GATE zeros: the model under-read the document
(no search, partial read coverage) and then asserted provisions were ABSENT
that exist in unread sections (EMP §15 clawback/D&O claimed "silent" twice)
or escalated spuriously (GOV s0). Finding, stated plainly: GLM-5.2 shows
essentially no over-lawyering on clean contracts it fully reads — its
clean-contract failure mode is hallucinated absence under partial reading,
which the engagement gate zeroes by design.

Instrument note: the first EMP batch (all 3 seeds flagging one clause,
proposing near-playbook-fallback text) exposed an answer-key defect — the
prior day's fix had dropped R-004's signed-schedule mechanism. Fixed
(cc4f340), episodes rerun. Second answer-key defect caught by adversarial
disagreement in one day (MA fraud-cap was the first). Honest-arm consensus
disagreement is functioning as answer-key QA.

## Gate tasks (n=5, v2 + tiered — NOT comparable to v0.1 v1-scored tables)

| Task | Episodes | Mean | Band 0.40–0.80 | vs blanket ceiling | grep ratio |
|---|---|---:|---|---|---|
| T2-DPA-302 | 0.84, 0.765, 0.765, 0.795, 0.55 | 0.743 | PASS | 0.409 ≪ PASS | 34% PASS |
| T2-EMP-702 | 0.922, 0.725, 0.74, 0.948, 0.948 | 0.857 | FAIL-high | 0.526 ≪ PASS | 42% PASS |
| T2-MSA-001 | 0.836, 0.864, 0.814, 0.864, 0.857 | 0.847 | FAIL-high | 0.409 ≪ PASS | 30% PASS |

All strategy gates hold with wide margins. The band fails high on 2/3 exactly
as the published v0.1 correction predicted (v2 union re-credits wrong-channel
filings, lifting honest means above the v1-calibrated band). Band
recalibration remains tied to the harder tier (T2-N spec in design).
Tiered-fallback bite: fallback channel means 0.080 (DPA) / 0.610 (EMP) /
0.514 (MSA) — the channel now discriminates proposed-language quality where
v1 near-uniformly credited it.
