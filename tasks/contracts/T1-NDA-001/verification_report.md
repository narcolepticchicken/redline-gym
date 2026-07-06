# Verification Report

Status: HUMAN SIGNED-OFF (model-stubbed validators V3/V4/V7-semantic/V11 still pending lab-lane run)

| Validator | Status | Detail |
|---|---|---|
| V1 rubric citations | PASS | ok |
| V2 mutation anti-drift | PASS | ok |
| V3 clean-base check | STUBBED | requires lab serving lane -- do not run from build tooling |
| V4 round-trip detectability | STUBBED | requires lab serving lane -- do not run from build tooling |
| V5 issue/deviation mapping | PASS | ok |
| V6 distractor integrity rule scan | PASS | ok |
| V7 missing-info string search | PASS | ok |
| V7-semantic missing-info semantic search | STUBBED | requires lab serving lane -- do not run from build tooling |
| V8 schema and hashes | PASS | ok |
| V9 canary rules empty | PASS | ok |
| V10 tranche leakage scan | PASS | single task; variance gate not applicable |
| V11 realism/coherence judge | STUBBED | requires lab serving lane -- do not run from build tooling |

Model-stubbed validators: V3, V4, V7-semantic, V11.

Human sign-off: name Aaron (aaron@litil.ai) date 2026-07-06
Scope: 18/18 review confirmations via guided red-pen walkthrough (playbook rules,
6 planted deviations, canaries/distractors/missing-info, full read-through).
Review pass also produced two fixes before signing: D-005 expected_action
redline→escalate (tiebreak Ruling 2) and "Canary:" labels stripped from
agent-visible rule text.
