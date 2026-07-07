# Validity Report

This report is assembled from repository artifacts only. It excludes the held-out split unless a formal evaluation protocol opts in.

## Instance Inventory

| Task | Practice area | Tier | Source | QA artifacts | Human sign-off |
|---|---|---|---|---|---|
| tasks/contracts/T1-NDA-001 | contracts | T1 | handbuilt | verification_report.md, model_checks | HUMAN SIGNED-OFF (model-stubbed validators V3/V4/V7-semantic/V11 still pending lab-lane run); Aaron (aaron@litil.ai) |
| tasks/contracts/T2-MSA-001 | contracts | T2 | handbuilt | verification_report.md, model_checks, qa | AWAITING HUMAN SIGN-OFF |
| tasks/generated/T1-DPA-301 | privacy | T1 | generated | verification_report.md, model_checks | AWAITING HUMAN SIGN-OFF |
| tasks/generated/T1-DPA-311 | privacy | T1 | generated | verification_report.md, model_checks | AWAITING HUMAN SIGN-OFF |
| tasks/generated/T1-EMP-701 | employment | T1 | generated | verification_report.md, model_checks | AWAITING HUMAN SIGN-OFF |
| tasks/generated/T1-MSA-105 | contracts | T1 | generated | verification_report.md, model_checks | AWAITING HUMAN SIGN-OFF |
| tasks/generated/T1-MSA-121 | contracts | T1 | generated | verification_report.md, model_checks | AWAITING HUMAN SIGN-OFF |
| tasks/generated/T1-NDA-101 | contracts | T1 | generated | verification_report.md, model_checks | AWAITING HUMAN SIGN-OFF |
| tasks/generated/T1-NDA-103 | contracts | T1 | generated | verification_report.md, model_checks | AWAITING HUMAN SIGN-OFF |
| tasks/generated/T1-NDA-111 | contracts | T1 | generated | verification_report.md, model_checks | AWAITING HUMAN SIGN-OFF |
| tasks/generated/T2-DPA-302 | privacy | T2 | generated | verification_report.md, model_checks | AWAITING HUMAN SIGN-OFF |
| tasks/generated/T2-DPA-303 | privacy | T2 | generated | verification_report.md, model_checks | AWAITING HUMAN SIGN-OFF |
| tasks/generated/T2-DPA-312 | privacy | T2 | generated | verification_report.md, model_checks | AWAITING HUMAN SIGN-OFF |
| tasks/generated/T2-EMP-702 | employment | T2 | generated | verification_report.md, model_checks | AWAITING HUMAN SIGN-OFF |
| tasks/generated/T2-EMP-703 | employment | T2 | generated | verification_report.md, model_checks | AWAITING HUMAN SIGN-OFF |
| tasks/generated/T2-MSA-104 | contracts | T2 | generated | verification_report.md, model_checks | AWAITING HUMAN SIGN-OFF |
| tasks/generated/T2-MSA-106 | contracts | T2 | generated | verification_report.md, model_checks | AWAITING HUMAN SIGN-OFF |
| tasks/generated/T2-MSA-122 | contracts | T2 | generated | verification_report.md, model_checks | AWAITING HUMAN SIGN-OFF |
| tasks/generated/T2-NDA-102 | contracts | T2 | generated | verification_report.md, model_checks | AWAITING HUMAN SIGN-OFF |
| tasks/generated/T2-NDA-112 | contracts | T2 | generated | verification_report.md, model_checks | AWAITING HUMAN SIGN-OFF |

## Gate Table

| Task | Validators | Null gate | Random gate | Grep gate | Mechanical ceiling |
|---|---|---|---|---|---:|
| tasks/contracts/T1-NDA-001 | PASS | PASS | UNMEASURED | UNMEASURED | 0.814286 (blanket) |
| tasks/contracts/T2-MSA-001 | PASS | PASS | UNMEASURED | UNMEASURED | 0.408647 (blanket) |
| tasks/generated/T1-DPA-301 | PASS | PASS | UNMEASURED | UNMEASURED | UNMEASURED |
| tasks/generated/T1-DPA-311 | PASS | PASS | UNMEASURED | UNMEASURED | UNMEASURED |
| tasks/generated/T1-EMP-701 | PASS | PASS | UNMEASURED | UNMEASURED | UNMEASURED |
| tasks/generated/T1-MSA-105 | PASS | PASS | UNMEASURED | UNMEASURED | UNMEASURED |
| tasks/generated/T1-MSA-121 | PASS | PASS | UNMEASURED | UNMEASURED | UNMEASURED |
| tasks/generated/T1-NDA-101 | PASS | PASS | UNMEASURED | UNMEASURED | UNMEASURED |
| tasks/generated/T1-NDA-103 | PASS | PASS | UNMEASURED | UNMEASURED | UNMEASURED |
| tasks/generated/T1-NDA-111 | PASS | PASS | UNMEASURED | UNMEASURED | UNMEASURED |
| tasks/generated/T2-DPA-302 | PASS | PASS | UNMEASURED | UNMEASURED | UNMEASURED |
| tasks/generated/T2-DPA-303 | PASS | PASS | UNMEASURED | UNMEASURED | UNMEASURED |
| tasks/generated/T2-DPA-312 | PASS | PASS | UNMEASURED | UNMEASURED | UNMEASURED |
| tasks/generated/T2-EMP-702 | PASS | PASS | UNMEASURED | UNMEASURED | UNMEASURED |
| tasks/generated/T2-EMP-703 | PASS | PASS | UNMEASURED | UNMEASURED | UNMEASURED |
| tasks/generated/T2-MSA-104 | PASS | PASS | UNMEASURED | UNMEASURED | UNMEASURED |
| tasks/generated/T2-MSA-106 | PASS | PASS | UNMEASURED | UNMEASURED | UNMEASURED |
| tasks/generated/T2-MSA-122 | PASS | PASS | UNMEASURED | UNMEASURED | UNMEASURED |
| tasks/generated/T2-NDA-102 | PASS | PASS | UNMEASURED | UNMEASURED | UNMEASURED |
| tasks/generated/T2-NDA-112 | PASS | PASS | UNMEASURED | UNMEASURED | UNMEASURED |

## Known Limits

- UNMEASURED gates: tasks/contracts/T1-NDA-001 cheater_llm; tasks/contracts/T1-NDA-001 deepseek_judge; tasks/contracts/T1-NDA-001 grep; tasks/contracts/T1-NDA-001 honest_llm; tasks/contracts/T1-NDA-001 random; tasks/contracts/T2-MSA-001 cheater_llm; tasks/contracts/T2-MSA-001 deepseek_judge; tasks/contracts/T2-MSA-001 grep; tasks/contracts/T2-MSA-001 honest_llm; tasks/contracts/T2-MSA-001 random; tasks/generated/T1-DPA-301 cheater_llm; tasks/generated/T1-DPA-301 deepseek_judge; tasks/generated/T1-DPA-301 grep; tasks/generated/T1-DPA-301 honest_llm; tasks/generated/T1-DPA-301 mechanical_ceiling; tasks/generated/T1-DPA-301 random; tasks/generated/T1-DPA-311 cheater_llm; tasks/generated/T1-DPA-311 deepseek_judge; tasks/generated/T1-DPA-311 grep; tasks/generated/T1-DPA-311 honest_llm; tasks/generated/T1-DPA-311 mechanical_ceiling; tasks/generated/T1-DPA-311 random; tasks/generated/T1-EMP-701 cheater_llm; tasks/generated/T1-EMP-701 deepseek_judge; tasks/generated/T1-EMP-701 grep; tasks/generated/T1-EMP-701 honest_llm; tasks/generated/T1-EMP-701 mechanical_ceiling; tasks/generated/T1-EMP-701 random; tasks/generated/T1-MSA-105 cheater_llm; tasks/generated/T1-MSA-105 deepseek_judge; tasks/generated/T1-MSA-105 grep; tasks/generated/T1-MSA-105 honest_llm; tasks/generated/T1-MSA-105 mechanical_ceiling; tasks/generated/T1-MSA-105 random; tasks/generated/T1-MSA-121 cheater_llm; tasks/generated/T1-MSA-121 deepseek_judge; tasks/generated/T1-MSA-121 grep; tasks/generated/T1-MSA-121 honest_llm; tasks/generated/T1-MSA-121 mechanical_ceiling; tasks/generated/T1-MSA-121 random; tasks/generated/T1-NDA-101 cheater_llm; tasks/generated/T1-NDA-101 deepseek_judge; tasks/generated/T1-NDA-101 grep; tasks/generated/T1-NDA-101 honest_llm; tasks/generated/T1-NDA-101 mechanical_ceiling; tasks/generated/T1-NDA-101 random; tasks/generated/T1-NDA-103 cheater_llm; tasks/generated/T1-NDA-103 deepseek_judge; tasks/generated/T1-NDA-103 grep; tasks/generated/T1-NDA-103 honest_llm; tasks/generated/T1-NDA-103 mechanical_ceiling; tasks/generated/T1-NDA-103 random; tasks/generated/T1-NDA-111 cheater_llm; tasks/generated/T1-NDA-111 deepseek_judge; tasks/generated/T1-NDA-111 grep; tasks/generated/T1-NDA-111 honest_llm; tasks/generated/T1-NDA-111 mechanical_ceiling; tasks/generated/T1-NDA-111 random; tasks/generated/T2-DPA-302 cheater_llm; tasks/generated/T2-DPA-302 deepseek_judge; tasks/generated/T2-DPA-302 grep; tasks/generated/T2-DPA-302 honest_llm; tasks/generated/T2-DPA-302 mechanical_ceiling; tasks/generated/T2-DPA-302 random; tasks/generated/T2-DPA-303 cheater_llm; tasks/generated/T2-DPA-303 deepseek_judge; tasks/generated/T2-DPA-303 grep; tasks/generated/T2-DPA-303 honest_llm; tasks/generated/T2-DPA-303 mechanical_ceiling; tasks/generated/T2-DPA-303 random; tasks/generated/T2-DPA-312 cheater_llm; tasks/generated/T2-DPA-312 deepseek_judge; tasks/generated/T2-DPA-312 grep; tasks/generated/T2-DPA-312 honest_llm; tasks/generated/T2-DPA-312 mechanical_ceiling; tasks/generated/T2-DPA-312 random; tasks/generated/T2-EMP-702 cheater_llm; tasks/generated/T2-EMP-702 deepseek_judge; tasks/generated/T2-EMP-702 grep; tasks/generated/T2-EMP-702 honest_llm; tasks/generated/T2-EMP-702 mechanical_ceiling; tasks/generated/T2-EMP-702 random; tasks/generated/T2-EMP-703 cheater_llm; tasks/generated/T2-EMP-703 deepseek_judge; tasks/generated/T2-EMP-703 grep; tasks/generated/T2-EMP-703 honest_llm; tasks/generated/T2-EMP-703 mechanical_ceiling; tasks/generated/T2-EMP-703 random; tasks/generated/T2-MSA-104 cheater_llm; tasks/generated/T2-MSA-104 deepseek_judge; tasks/generated/T2-MSA-104 grep; tasks/generated/T2-MSA-104 honest_llm; tasks/generated/T2-MSA-104 mechanical_ceiling; tasks/generated/T2-MSA-104 random; tasks/generated/T2-MSA-106 cheater_llm; tasks/generated/T2-MSA-106 deepseek_judge; tasks/generated/T2-MSA-106 grep; tasks/generated/T2-MSA-106 honest_llm; tasks/generated/T2-MSA-106 mechanical_ceiling; tasks/generated/T2-MSA-106 random; tasks/generated/T2-MSA-122 cheater_llm; tasks/generated/T2-MSA-122 deepseek_judge; tasks/generated/T2-MSA-122 grep; tasks/generated/T2-MSA-122 honest_llm; tasks/generated/T2-MSA-122 mechanical_ceiling; tasks/generated/T2-MSA-122 random; tasks/generated/T2-NDA-102 cheater_llm; tasks/generated/T2-NDA-102 deepseek_judge; tasks/generated/T2-NDA-102 grep; tasks/generated/T2-NDA-102 honest_llm; tasks/generated/T2-NDA-102 mechanical_ceiling; tasks/generated/T2-NDA-102 random; tasks/generated/T2-NDA-112 cheater_llm; tasks/generated/T2-NDA-112 deepseek_judge; tasks/generated/T2-NDA-112 grep; tasks/generated/T2-NDA-112 honest_llm; tasks/generated/T2-NDA-112 mechanical_ceiling; tasks/generated/T2-NDA-112 random.
- Attorney-agreement status: 1 attorney(s), 1 of 20 non-held-out instance(s) signed.
- Validator stubs not yet run for tasks/contracts/T1-NDA-001: V3 clean-base check, V4 round-trip detectability, V7-semantic missing-info semantic search, V11 realism/coherence judge.
- Validator stubs not yet run for tasks/contracts/T2-MSA-001: V3 clean-base check, V4 round-trip detectability, V7-semantic missing-info semantic search, V11 realism/coherence judge.
- Validator stubs not yet run for tasks/generated/T1-DPA-301: V3 clean-base check, V4 round-trip detectability, V7-semantic missing-info semantic search, V11 realism/coherence judge.
- Validator stubs not yet run for tasks/generated/T1-DPA-311: V3 clean-base check, V4 round-trip detectability, V7-semantic missing-info semantic search, V11 realism/coherence judge.
- Validator stubs not yet run for tasks/generated/T1-EMP-701: V3 clean-base check, V4 round-trip detectability, V7-semantic missing-info semantic search, V11 realism/coherence judge.
- Validator stubs not yet run for tasks/generated/T1-MSA-105: V3 clean-base check, V4 round-trip detectability, V7-semantic missing-info semantic search, V11 realism/coherence judge.
- Validator stubs not yet run for tasks/generated/T1-MSA-121: V3 clean-base check, V4 round-trip detectability, V7-semantic missing-info semantic search, V11 realism/coherence judge.
- Validator stubs not yet run for tasks/generated/T1-NDA-101: V3 clean-base check, V4 round-trip detectability, V7-semantic missing-info semantic search, V11 realism/coherence judge.
- Validator stubs not yet run for tasks/generated/T1-NDA-103: V3 clean-base check, V4 round-trip detectability, V7-semantic missing-info semantic search, V11 realism/coherence judge.
- Validator stubs not yet run for tasks/generated/T1-NDA-111: V3 clean-base check, V4 round-trip detectability, V7-semantic missing-info semantic search, V11 realism/coherence judge.
- Validator stubs not yet run for tasks/generated/T2-DPA-302: V3 clean-base check, V4 round-trip detectability, V7-semantic missing-info semantic search, V11 realism/coherence judge.
- Validator stubs not yet run for tasks/generated/T2-DPA-303: V3 clean-base check, V4 round-trip detectability, V7-semantic missing-info semantic search, V11 realism/coherence judge.
- Validator stubs not yet run for tasks/generated/T2-DPA-312: V3 clean-base check, V4 round-trip detectability, V7-semantic missing-info semantic search, V11 realism/coherence judge.
- Validator stubs not yet run for tasks/generated/T2-EMP-702: V3 clean-base check, V4 round-trip detectability, V7-semantic missing-info semantic search, V11 realism/coherence judge.
- Validator stubs not yet run for tasks/generated/T2-EMP-703: V3 clean-base check, V4 round-trip detectability, V7-semantic missing-info semantic search, V11 realism/coherence judge.
- Validator stubs not yet run for tasks/generated/T2-MSA-104: V3 clean-base check, V4 round-trip detectability, V7-semantic missing-info semantic search, V11 realism/coherence judge.
- Validator stubs not yet run for tasks/generated/T2-MSA-106: V3 clean-base check, V4 round-trip detectability, V7-semantic missing-info semantic search, V11 realism/coherence judge.
- Validator stubs not yet run for tasks/generated/T2-MSA-122: V3 clean-base check, V4 round-trip detectability, V7-semantic missing-info semantic search, V11 realism/coherence judge.
- Validator stubs not yet run for tasks/generated/T2-NDA-102: V3 clean-base check, V4 round-trip detectability, V7-semantic missing-info semantic search, V11 realism/coherence judge.
- Validator stubs not yet run for tasks/generated/T2-NDA-112: V3 clean-base check, V4 round-trip detectability, V7-semantic missing-info semantic search, V11 realism/coherence judge.
