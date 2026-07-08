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
