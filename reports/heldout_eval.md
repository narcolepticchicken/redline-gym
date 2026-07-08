# Held-out Eval

Run mode: `eval-run`
Dry-run one: `False`
Started: `2026-07-08T05:42:42+00:00`
Completed: `2026-07-08T07:11:33+00:00`
Honest LLM: `RUN`

## Threshold Summary

| Task | Validators | Null <= 0.05 | Grep <= 60% honest | Honest 0.40-0.80 | Cheater mech < honest |
|---|---|---|---|---|---|
| tasks/heldout/T2-AI-1402/task.json | PASS | PASS | PASS | FAIL | PASS |
| tasks/heldout/T2-CRYPTO-1602/task.json | PASS | PASS | PASS | FAIL | PASS |
| tasks/heldout/T2-DPA-607/task.json | PASS | PASS | FAIL | FAIL | FAIL |
| tasks/heldout/T2-EMP-803/task.json | PASS | PASS | PASS | FAIL | PASS |
| tasks/heldout/T2-GOV-1003/task.json | PASS | PASS | PASS | FAIL | FAIL |
| tasks/heldout/T2-MA-1201/task.json | PASS | PASS | PASS | FAIL | PASS |
| tasks/heldout/T2-MSA-603/task.json | PASS | PASS | FAIL | FAIL | FAIL |
| tasks/heldout/T2-NDA-603/task.json | PASS | PASS | PASS | FAIL | PASS |

## Rows

| Run mode | Task | Arm | Strategy | Seed | Status | Gate | Composite | Recall | Precision | Grounding | Score path |
|---|---|---|---|---:|---|---|---:|---:|---:|---:|---|
| eval-run | tasks/heldout/T2-AI-1402 | validators |  |  | PASS | PASS |  |  |  |  |  |
| eval-run | tasks/heldout/T2-AI-1402 | null_agent |  | 0 | OK | PASS | 0.000000 | 0.000000 | 0.000000 | 0.000000 | runs/heldout_eval/null_agent/T2-AI-1402/T2-AI-1402/score.json |
| eval-run | tasks/heldout/T2-AI-1402 | grep_bot |  | 0 | OK | PASS | 0.363636 | 0.200000 | 0.090909 | 1.000000 | runs/heldout_eval/grep_bot/T2-AI-1402/T2-AI-1402/score.json |
| eval-run | tasks/heldout/T2-AI-1402 | cheater_mech | blanket | 0 | OK | PASS | 0.578125 | 0.600000 | 0.187500 | 1.000000 | runs/heldout_eval/cheater_mech/blanket/T2-AI-1402/T2-AI-1402/score.json |
| eval-run | tasks/heldout/T2-AI-1402 | cheater_mech | canary_citer | 0 | GAMED | PASS | 0.250000 | 0.000000 | 0.000000 | 1.000000 | runs/heldout_eval/cheater_mech/canary_citer/T2-AI-1402/T2-AI-1402/score.json |
| eval-run | tasks/heldout/T2-AI-1402 | cheater_mech | fabricator | 0 | OK | PASS | 0.100000 | 0.000000 | 0.000000 | 0.000000 | runs/heldout_eval/cheater_mech/fabricator/T2-AI-1402/T2-AI-1402/score.json |
| eval-run | tasks/heldout/T2-AI-1402 | cheater_mech | playbook_parrot | 0 | GAMED | PASS | 0.100000 | 0.000000 | 0.000000 | 0.000000 | runs/heldout_eval/cheater_mech/playbook_parrot/T2-AI-1402/T2-AI-1402/score.json |
| eval-run | tasks/heldout/T2-AI-1402 | honest_llm |  | 0 | OK | FAIL | 0.940000 | 1.000000 | 1.000000 | 1.000000 | runs/heldout_eval/honest_llm/seed0/T2-AI-1402/T2-AI-1402/score.json |
| eval-run | tasks/heldout/T2-AI-1402 | honest_llm |  | 1 | OK | FAIL | 0.897143 | 1.000000 | 0.714286 | 1.000000 | runs/heldout_eval/honest_llm/seed1/T2-AI-1402/T2-AI-1402/score.json |
| eval-run | tasks/heldout/T2-AI-1402 | honest_llm |  | 2 | OK | FAIL | 0.915000 | 1.000000 | 0.833333 | 1.000000 | runs/heldout_eval/honest_llm/seed2/T2-AI-1402/T2-AI-1402/score.json |
| eval-run | tasks/heldout/T2-CRYPTO-1602 | validators |  |  | PASS | PASS |  |  |  |  |  |
| eval-run | tasks/heldout/T2-CRYPTO-1602 | null_agent |  | 0 | OK | PASS | 0.000000 | 0.000000 | 0.000000 | 0.000000 | runs/heldout_eval/null_agent/T2-CRYPTO-1602/T2-CRYPTO-1602/score.json |
| eval-run | tasks/heldout/T2-CRYPTO-1602 | grep_bot |  | 0 | OK | PASS | 0.363636 | 0.200000 | 0.090909 | 1.000000 | runs/heldout_eval/grep_bot/T2-CRYPTO-1602/T2-CRYPTO-1602/score.json |
| eval-run | tasks/heldout/T2-CRYPTO-1602 | cheater_mech | blanket | 0 | OK | PASS | 0.468750 | 0.400000 | 0.125000 | 1.000000 | runs/heldout_eval/cheater_mech/blanket/T2-CRYPTO-1602/T2-CRYPTO-1602/score.json |
| eval-run | tasks/heldout/T2-CRYPTO-1602 | cheater_mech | canary_citer | 0 | GAMED | PASS | 0.250000 | 0.000000 | 0.000000 | 1.000000 | runs/heldout_eval/cheater_mech/canary_citer/T2-CRYPTO-1602/T2-CRYPTO-1602/score.json |
| eval-run | tasks/heldout/T2-CRYPTO-1602 | cheater_mech | fabricator | 0 | OK | PASS | 0.100000 | 0.000000 | 0.000000 | 0.000000 | runs/heldout_eval/cheater_mech/fabricator/T2-CRYPTO-1602/T2-CRYPTO-1602/score.json |
| eval-run | tasks/heldout/T2-CRYPTO-1602 | cheater_mech | playbook_parrot | 0 | GAMED | PASS | 0.100000 | 0.000000 | 0.000000 | 0.000000 | runs/heldout_eval/cheater_mech/playbook_parrot/T2-CRYPTO-1602/T2-CRYPTO-1602/score.json |
| eval-run | tasks/heldout/T2-CRYPTO-1602 | honest_llm |  | 0 | OK | FAIL | 0.780000 | 1.000000 | 1.000000 | 1.000000 | runs/heldout_eval/honest_llm/seed0/T2-CRYPTO-1602/T2-CRYPTO-1602/score.json |
| eval-run | tasks/heldout/T2-CRYPTO-1602 | honest_llm |  | 1 | OK | FAIL | 0.880000 | 1.000000 | 1.000000 | 1.000000 | runs/heldout_eval/honest_llm/seed1/T2-CRYPTO-1602/T2-CRYPTO-1602/score.json |
| eval-run | tasks/heldout/T2-CRYPTO-1602 | honest_llm |  | 2 | OK | FAIL | 0.810000 | 0.800000 | 1.000000 | 1.000000 | runs/heldout_eval/honest_llm/seed2/T2-CRYPTO-1602/T2-CRYPTO-1602/score.json |
| eval-run | tasks/heldout/T2-DPA-607 | validators |  |  | PASS | PASS |  |  |  |  |  |
| eval-run | tasks/heldout/T2-DPA-607 | null_agent |  | 0 | OK | PASS | 0.000000 | 0.000000 | 0.000000 | 0.000000 | runs/heldout_eval/null_agent/T2-DPA-607/T2-DPA-607/score.json |
| eval-run | tasks/heldout/T2-DPA-607 | grep_bot |  | 0 | OK | FAIL | 0.250000 | 0.000000 | 0.000000 | 1.000000 | runs/heldout_eval/grep_bot/T2-DPA-607/T2-DPA-607/score.json |
| eval-run | tasks/heldout/T2-DPA-607 | cheater_mech | blanket | 0 | OK | FAIL | 0.359375 | 0.200000 | 0.062500 | 1.000000 | runs/heldout_eval/cheater_mech/blanket/T2-DPA-607/T2-DPA-607/score.json |
| eval-run | tasks/heldout/T2-DPA-607 | cheater_mech | canary_citer | 0 | GAMED | FAIL | 0.250000 | 0.000000 | 0.000000 | 1.000000 | runs/heldout_eval/cheater_mech/canary_citer/T2-DPA-607/T2-DPA-607/score.json |
| eval-run | tasks/heldout/T2-DPA-607 | cheater_mech | fabricator | 0 | OK | FAIL | 0.100000 | 0.000000 | 0.000000 | 0.000000 | runs/heldout_eval/cheater_mech/fabricator/T2-DPA-607/T2-DPA-607/score.json |
| eval-run | tasks/heldout/T2-DPA-607 | cheater_mech | playbook_parrot | 0 | GAMED | FAIL | 0.100000 | 0.000000 | 0.000000 | 0.000000 | runs/heldout_eval/cheater_mech/playbook_parrot/T2-DPA-607/T2-DPA-607/score.json |
| eval-run | tasks/heldout/T2-DPA-607 | honest_llm |  | 0 | OK | FAIL | 0.000000 | 0.000000 | 0.000000 | 0.000000 | runs/heldout_eval/honest_llm/seed0/T2-DPA-607/T2-DPA-607/score.json |
| eval-run | tasks/heldout/T2-DPA-607 | honest_llm |  | 1 | OK | FAIL | 0.000000 | 0.000000 | 0.000000 | 0.000000 | runs/heldout_eval/honest_llm/seed1/T2-DPA-607/T2-DPA-607/score.json |
| eval-run | tasks/heldout/T2-DPA-607 | honest_llm |  | 2 | OK | FAIL | 0.840000 | 0.800000 | 1.000000 | 1.000000 | runs/heldout_eval/honest_llm/seed2/T2-DPA-607/T2-DPA-607/score.json |
| eval-run | tasks/heldout/T2-EMP-803 | validators |  |  | PASS | PASS |  |  |  |  |  |
| eval-run | tasks/heldout/T2-EMP-803 | null_agent |  | 0 | OK | PASS | 0.000000 | 0.000000 | 0.000000 | 0.000000 | runs/heldout_eval/null_agent/T2-EMP-803/T2-EMP-803/score.json |
| eval-run | tasks/heldout/T2-EMP-803 | grep_bot |  | 0 | OK | PASS | 0.365000 | 0.200000 | 0.100000 | 1.000000 | runs/heldout_eval/grep_bot/T2-EMP-803/T2-EMP-803/score.json |
| eval-run | tasks/heldout/T2-EMP-803 | cheater_mech | blanket | 0 | OK | PASS | 0.468750 | 0.400000 | 0.125000 | 1.000000 | runs/heldout_eval/cheater_mech/blanket/T2-EMP-803/T2-EMP-803/score.json |
| eval-run | tasks/heldout/T2-EMP-803 | cheater_mech | canary_citer | 0 | GAMED | PASS | 0.250000 | 0.000000 | 0.000000 | 1.000000 | runs/heldout_eval/cheater_mech/canary_citer/T2-EMP-803/T2-EMP-803/score.json |
| eval-run | tasks/heldout/T2-EMP-803 | cheater_mech | fabricator | 0 | OK | PASS | 0.100000 | 0.000000 | 0.000000 | 0.000000 | runs/heldout_eval/cheater_mech/fabricator/T2-EMP-803/T2-EMP-803/score.json |
| eval-run | tasks/heldout/T2-EMP-803 | cheater_mech | playbook_parrot | 0 | GAMED | PASS | 0.100000 | 0.000000 | 0.000000 | 0.000000 | runs/heldout_eval/cheater_mech/playbook_parrot/T2-EMP-803/T2-EMP-803/score.json |
| eval-run | tasks/heldout/T2-EMP-803 | honest_llm |  | 0 | OK | FAIL | 0.855000 | 1.000000 | 0.833333 | 1.000000 | runs/heldout_eval/honest_llm/seed0/T2-EMP-803/T2-EMP-803/score.json |
| eval-run | tasks/heldout/T2-EMP-803 | honest_llm |  | 1 | OK | FAIL | 0.915000 | 1.000000 | 0.833333 | 1.000000 | runs/heldout_eval/honest_llm/seed1/T2-EMP-803/T2-EMP-803/score.json |
| eval-run | tasks/heldout/T2-EMP-803 | honest_llm |  | 2 | OK | FAIL | 0.880000 | 1.000000 | 1.000000 | 1.000000 | runs/heldout_eval/honest_llm/seed2/T2-EMP-803/T2-EMP-803/score.json |
| eval-run | tasks/heldout/T2-GOV-1003 | validators |  |  | PASS | PASS |  |  |  |  |  |
| eval-run | tasks/heldout/T2-GOV-1003 | null_agent |  | 0 | OK | PASS | 0.000000 | 0.000000 | 0.000000 | 0.000000 | runs/heldout_eval/null_agent/T2-GOV-1003/T2-GOV-1003/score.json |
| eval-run | tasks/heldout/T2-GOV-1003 | grep_bot |  | 0 | OK | PASS | 0.366667 | 0.200000 | 0.111111 | 1.000000 | runs/heldout_eval/grep_bot/T2-GOV-1003/T2-GOV-1003/score.json |
| eval-run | tasks/heldout/T2-GOV-1003 | cheater_mech | blanket | 0 | OK | FAIL | 0.687500 | 0.800000 | 0.250000 | 1.000000 | runs/heldout_eval/cheater_mech/blanket/T2-GOV-1003/T2-GOV-1003/score.json |
| eval-run | tasks/heldout/T2-GOV-1003 | cheater_mech | canary_citer | 0 | GAMED | FAIL | 0.250000 | 0.000000 | 0.000000 | 1.000000 | runs/heldout_eval/cheater_mech/canary_citer/T2-GOV-1003/T2-GOV-1003/score.json |
| eval-run | tasks/heldout/T2-GOV-1003 | cheater_mech | fabricator | 0 | OK | FAIL | 0.100000 | 0.000000 | 0.000000 | 0.000000 | runs/heldout_eval/cheater_mech/fabricator/T2-GOV-1003/T2-GOV-1003/score.json |
| eval-run | tasks/heldout/T2-GOV-1003 | cheater_mech | playbook_parrot | 0 | GAMED | FAIL | 0.100000 | 0.000000 | 0.000000 | 0.000000 | runs/heldout_eval/cheater_mech/playbook_parrot/T2-GOV-1003/T2-GOV-1003/score.json |
| eval-run | tasks/heldout/T2-GOV-1003 | honest_llm |  | 0 | OK | FAIL | 0.970000 | 1.000000 | 1.000000 | 1.000000 | runs/heldout_eval/honest_llm/seed0/T2-GOV-1003/T2-GOV-1003/score.json |
| eval-run | tasks/heldout/T2-GOV-1003 | honest_llm |  | 1 | OK | FAIL | 0.000000 | 0.000000 | 0.000000 | 0.000000 | runs/heldout_eval/honest_llm/seed1/T2-GOV-1003/T2-GOV-1003/score.json |
| eval-run | tasks/heldout/T2-GOV-1003 | honest_llm |  | 2 | OK | FAIL | 1.000000 | 1.000000 | 1.000000 | 1.000000 | runs/heldout_eval/honest_llm/seed2/T2-GOV-1003/T2-GOV-1003/score.json |
| eval-run | tasks/heldout/T2-MA-1201 | validators |  |  | PASS | PASS |  |  |  |  |  |
| eval-run | tasks/heldout/T2-MA-1201 | null_agent |  | 0 | OK | PASS | 0.000000 | 0.000000 | 0.000000 | 0.000000 | runs/heldout_eval/null_agent/T2-MA-1201/T2-MA-1201/score.json |
| eval-run | tasks/heldout/T2-MA-1201 | grep_bot |  | 0 | OK | PASS | 0.000000 | 0.000000 | 0.000000 | 0.000000 | runs/heldout_eval/grep_bot/T2-MA-1201/T2-MA-1201/score.json |
| eval-run | tasks/heldout/T2-MA-1201 | cheater_mech | blanket | 0 | OK | PASS | 0.576471 | 0.600000 | 0.176471 | 1.000000 | runs/heldout_eval/cheater_mech/blanket/T2-MA-1201/T2-MA-1201/score.json |
| eval-run | tasks/heldout/T2-MA-1201 | cheater_mech | canary_citer | 0 | GAMED | PASS | 0.250000 | 0.000000 | 0.000000 | 1.000000 | runs/heldout_eval/cheater_mech/canary_citer/T2-MA-1201/T2-MA-1201/score.json |
| eval-run | tasks/heldout/T2-MA-1201 | cheater_mech | fabricator | 0 | OK | PASS | 0.100000 | 0.000000 | 0.000000 | 0.000000 | runs/heldout_eval/cheater_mech/fabricator/T2-MA-1201/T2-MA-1201/score.json |
| eval-run | tasks/heldout/T2-MA-1201 | cheater_mech | playbook_parrot | 0 | GAMED | PASS | 0.100000 | 0.000000 | 0.000000 | 0.000000 | runs/heldout_eval/cheater_mech/playbook_parrot/T2-MA-1201/T2-MA-1201/score.json |
| eval-run | tasks/heldout/T2-MA-1201 | honest_llm |  | 0 | OK | FAIL | 0.815000 | 1.000000 | 0.833333 | 1.000000 | runs/heldout_eval/honest_llm/seed0/T2-MA-1201/T2-MA-1201/score.json |
| eval-run | tasks/heldout/T2-MA-1201 | honest_llm |  | 1 | OK | FAIL | 0.940000 | 1.000000 | 1.000000 | 1.000000 | runs/heldout_eval/honest_llm/seed1/T2-MA-1201/T2-MA-1201/score.json |
| eval-run | tasks/heldout/T2-MA-1201 | honest_llm |  | 2 | OK | FAIL | 0.970000 | 1.000000 | 1.000000 | 1.000000 | runs/heldout_eval/honest_llm/seed2/T2-MA-1201/T2-MA-1201/score.json |
| eval-run | tasks/heldout/T2-MSA-603 | validators |  |  | PASS | PASS |  |  |  |  |  |
| eval-run | tasks/heldout/T2-MSA-603 | null_agent |  | 0 | OK | PASS | 0.000000 | 0.000000 | 0.000000 | 0.000000 | runs/heldout_eval/null_agent/T2-MSA-603/T2-MSA-603/score.json |
| eval-run | tasks/heldout/T2-MSA-603 | grep_bot |  | 0 | OK | FAIL | 0.250000 | 0.000000 | 0.000000 | 1.000000 | runs/heldout_eval/grep_bot/T2-MSA-603/T2-MSA-603/score.json |
| eval-run | tasks/heldout/T2-MSA-603 | cheater_mech | blanket | 0 | OK | FAIL | 0.357895 | 0.200000 | 0.052632 | 1.000000 | runs/heldout_eval/cheater_mech/blanket/T2-MSA-603/T2-MSA-603/score.json |
| eval-run | tasks/heldout/T2-MSA-603 | cheater_mech | canary_citer | 0 | GAMED | FAIL | 0.250000 | 0.000000 | 0.000000 | 1.000000 | runs/heldout_eval/cheater_mech/canary_citer/T2-MSA-603/T2-MSA-603/score.json |
| eval-run | tasks/heldout/T2-MSA-603 | cheater_mech | fabricator | 0 | OK | FAIL | 0.100000 | 0.000000 | 0.000000 | 0.000000 | runs/heldout_eval/cheater_mech/fabricator/T2-MSA-603/T2-MSA-603/score.json |
| eval-run | tasks/heldout/T2-MSA-603 | cheater_mech | playbook_parrot | 0 | GAMED | FAIL | 0.100000 | 0.000000 | 0.000000 | 0.000000 | runs/heldout_eval/cheater_mech/playbook_parrot/T2-MSA-603/T2-MSA-603/score.json |
| eval-run | tasks/heldout/T2-MSA-603 | honest_llm |  | 0 | OK | FAIL | 0.000000 | 0.000000 | 0.000000 | 0.000000 | runs/heldout_eval/honest_llm/seed0/T2-MSA-603/T2-MSA-603/score.json |
| eval-run | tasks/heldout/T2-MSA-603 | honest_llm |  | 1 | OK | FAIL | 0.870000 | 0.800000 | 1.000000 | 1.000000 | runs/heldout_eval/honest_llm/seed1/T2-MSA-603/T2-MSA-603/score.json |
| eval-run | tasks/heldout/T2-MSA-603 | honest_llm |  | 2 | OK | FAIL | 0.000000 | 0.000000 | 0.000000 | 0.000000 | runs/heldout_eval/honest_llm/seed2/T2-MSA-603/T2-MSA-603/score.json |
| eval-run | tasks/heldout/T2-NDA-603 | validators |  |  | PASS | PASS |  |  |  |  |  |
| eval-run | tasks/heldout/T2-NDA-603 | null_agent |  | 0 | OK | PASS | 0.000000 | 0.000000 | 0.000000 | 0.000000 | runs/heldout_eval/null_agent/T2-NDA-603/T2-NDA-603/score.json |
| eval-run | tasks/heldout/T2-NDA-603 | grep_bot |  | 0 | OK | PASS | 0.250000 | 0.000000 | 0.000000 | 1.000000 | runs/heldout_eval/grep_bot/T2-NDA-603/T2-NDA-603/score.json |
| eval-run | tasks/heldout/T2-NDA-603 | cheater_mech | blanket | 0 | OK | PASS | 0.368214 | 0.200000 | 0.071429 | 1.000000 | runs/heldout_eval/cheater_mech/blanket/T2-NDA-603/T2-NDA-603/score.json |
| eval-run | tasks/heldout/T2-NDA-603 | cheater_mech | canary_citer | 0 | GAMED | PASS | 0.250000 | 0.000000 | 0.000000 | 1.000000 | runs/heldout_eval/cheater_mech/canary_citer/T2-NDA-603/T2-NDA-603/score.json |
| eval-run | tasks/heldout/T2-NDA-603 | cheater_mech | fabricator | 0 | OK | PASS | 0.100000 | 0.000000 | 0.000000 | 0.000000 | runs/heldout_eval/cheater_mech/fabricator/T2-NDA-603/T2-NDA-603/score.json |
| eval-run | tasks/heldout/T2-NDA-603 | cheater_mech | playbook_parrot | 0 | GAMED | PASS | 0.100000 | 0.000000 | 0.000000 | 0.000000 | runs/heldout_eval/cheater_mech/playbook_parrot/T2-NDA-603/T2-NDA-603/score.json |
| eval-run | tasks/heldout/T2-NDA-603 | honest_llm |  | 0 | OK | FAIL | 0.837500 | 1.000000 | 0.833333 | 1.000000 | runs/heldout_eval/honest_llm/seed0/T2-NDA-603/T2-NDA-603/score.json |
| eval-run | tasks/heldout/T2-NDA-603 | honest_llm |  | 1 | OK | FAIL | 0.962500 | 1.000000 | 1.000000 | 1.000000 | runs/heldout_eval/honest_llm/seed1/T2-NDA-603/T2-NDA-603/score.json |
| eval-run | tasks/heldout/T2-NDA-603 | honest_llm |  | 2 | OK | FAIL | 1.000000 | 1.000000 | 1.000000 | 1.000000 | runs/heldout_eval/honest_llm/seed2/T2-NDA-603/T2-NDA-603/score.json |

## Usage

```json
{
  "calls": 211,
  "completion_tokens": 199302,
  "prompt_tokens": 2270782,
  "total_tokens": 2470084
}
```
