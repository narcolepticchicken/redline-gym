# Validity Report

This report is assembled from repository artifacts only. It excludes the held-out split unless a formal evaluation protocol opts in.

## Instance Inventory

| Task | Practice area | Tier | Source | QA artifacts | Human sign-off |
|---|---|---|---|---|---|
| tasks/contracts/T1-NDA-001 | contracts | T1 | handbuilt | verification_report.md, model_checks | HUMAN SIGNED-OFF (model-stubbed validators V3/V4/V7-semantic/V11 still pending lab-lane run); Aaron (aaron@litil.ai) |
| tasks/contracts/T2-MSA-001 | contracts | T2 | handbuilt | verification_report.md, qa | AWAITING HUMAN SIGN-OFF |
| tasks/generated/T1-MSA-105 | contracts | T1 | generated | verification_report.md | AWAITING HUMAN SIGN-OFF |
| tasks/generated/T1-NDA-101 | contracts | T1 | generated | verification_report.md | AWAITING HUMAN SIGN-OFF |
| tasks/generated/T1-NDA-103 | contracts | T1 | generated | verification_report.md | AWAITING HUMAN SIGN-OFF |
| tasks/generated/T2-MSA-104 | contracts | T2 | generated | verification_report.md | AWAITING HUMAN SIGN-OFF |
| tasks/generated/T2-MSA-106 | contracts | T2 | generated | verification_report.md | AWAITING HUMAN SIGN-OFF |
| tasks/generated/T2-NDA-102 | contracts | T2 | generated | verification_report.md | AWAITING HUMAN SIGN-OFF |

## Gate Table

| Task | Validators | Null gate | Random gate | Grep gate | Mechanical ceiling |
|---|---|---|---|---|---:|
| tasks/contracts/T1-NDA-001 | PASS | PASS | UNMEASURED | UNMEASURED | 0.814286 (blanket) |
| tasks/contracts/T2-MSA-001 | PASS | PASS | UNMEASURED | UNMEASURED | 0.408647 (blanket) |
| tasks/generated/T1-MSA-105 | PASS | PASS | UNMEASURED | UNMEASURED | UNMEASURED |
| tasks/generated/T1-NDA-101 | PASS | PASS | UNMEASURED | UNMEASURED | UNMEASURED |
| tasks/generated/T1-NDA-103 | PASS | PASS | UNMEASURED | UNMEASURED | UNMEASURED |
| tasks/generated/T2-MSA-104 | PASS | PASS | UNMEASURED | UNMEASURED | UNMEASURED |
| tasks/generated/T2-MSA-106 | PASS | PASS | UNMEASURED | UNMEASURED | UNMEASURED |
| tasks/generated/T2-NDA-102 | PASS | PASS | UNMEASURED | UNMEASURED | UNMEASURED |

## Known Limits

- UNMEASURED gates: tasks/contracts/T1-NDA-001 cheater_llm; tasks/contracts/T1-NDA-001 deepseek_judge; tasks/contracts/T1-NDA-001 grep; tasks/contracts/T1-NDA-001 honest_llm; tasks/contracts/T1-NDA-001 random; tasks/contracts/T2-MSA-001 cheater_llm; tasks/contracts/T2-MSA-001 deepseek_judge; tasks/contracts/T2-MSA-001 grep; tasks/contracts/T2-MSA-001 honest_llm; tasks/contracts/T2-MSA-001 random; tasks/generated/T1-MSA-105 cheater_llm; tasks/generated/T1-MSA-105 deepseek_judge; tasks/generated/T1-MSA-105 grep; tasks/generated/T1-MSA-105 honest_llm; tasks/generated/T1-MSA-105 mechanical_ceiling; tasks/generated/T1-MSA-105 random; tasks/generated/T1-NDA-101 cheater_llm; tasks/generated/T1-NDA-101 deepseek_judge; tasks/generated/T1-NDA-101 grep; tasks/generated/T1-NDA-101 honest_llm; tasks/generated/T1-NDA-101 mechanical_ceiling; tasks/generated/T1-NDA-101 random; tasks/generated/T1-NDA-103 cheater_llm; tasks/generated/T1-NDA-103 deepseek_judge; tasks/generated/T1-NDA-103 grep; tasks/generated/T1-NDA-103 honest_llm; tasks/generated/T1-NDA-103 mechanical_ceiling; tasks/generated/T1-NDA-103 random; tasks/generated/T2-MSA-104 cheater_llm; tasks/generated/T2-MSA-104 deepseek_judge; tasks/generated/T2-MSA-104 grep; tasks/generated/T2-MSA-104 honest_llm; tasks/generated/T2-MSA-104 mechanical_ceiling; tasks/generated/T2-MSA-104 random; tasks/generated/T2-MSA-106 cheater_llm; tasks/generated/T2-MSA-106 deepseek_judge; tasks/generated/T2-MSA-106 grep; tasks/generated/T2-MSA-106 honest_llm; tasks/generated/T2-MSA-106 mechanical_ceiling; tasks/generated/T2-MSA-106 random; tasks/generated/T2-NDA-102 cheater_llm; tasks/generated/T2-NDA-102 deepseek_judge; tasks/generated/T2-NDA-102 grep; tasks/generated/T2-NDA-102 honest_llm; tasks/generated/T2-NDA-102 mechanical_ceiling; tasks/generated/T2-NDA-102 random.
- Attorney-agreement status: 1 attorney(s), 1 of 8 non-held-out instance(s) signed.
- Validator stubs not yet run for tasks/contracts/T1-NDA-001: V3 clean-base check, V4 round-trip detectability, V7-semantic missing-info semantic search, V11 realism/coherence judge.
- Validator stubs not yet run for tasks/contracts/T2-MSA-001: V3 clean-base check, V4 round-trip detectability, V7-semantic missing-info semantic search, V11 realism/coherence judge.
- Validator stubs not yet run for tasks/generated/T1-MSA-105: V3 clean-base check, V4 round-trip detectability, V7-semantic missing-info semantic search, V11 realism/coherence judge.
- Validator stubs not yet run for tasks/generated/T1-NDA-101: V3 clean-base check, V4 round-trip detectability, V7-semantic missing-info semantic search, V11 realism/coherence judge.
- Validator stubs not yet run for tasks/generated/T1-NDA-103: V3 clean-base check, V4 round-trip detectability, V7-semantic missing-info semantic search, V11 realism/coherence judge.
- Validator stubs not yet run for tasks/generated/T2-MSA-104: V3 clean-base check, V4 round-trip detectability, V7-semantic missing-info semantic search, V11 realism/coherence judge.
- Validator stubs not yet run for tasks/generated/T2-MSA-106: V3 clean-base check, V4 round-trip detectability, V7-semantic missing-info semantic search, V11 realism/coherence judge.
- Validator stubs not yet run for tasks/generated/T2-NDA-102: V3 clean-base check, V4 round-trip detectability, V7-semantic missing-info semantic search, V11 realism/coherence judge.
