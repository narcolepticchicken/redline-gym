# Verification Report

Status: AWAITING HUMAN SIGN-OFF

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

## Emit-Time Baseline Gate

- grep_bot recall: 0.000000
- tier threshold: <= 0.2
- matched deviation ids: none
- matched rule ids: none
- coherence check: PASS sections=13 cross_refs_resolved=yes anchors_resolved=yes
Human sign-off: name ____________________ date __________
