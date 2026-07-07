# Gate Table

Composite / recall are reported for deterministic baselines. Honest and model-cheater comparisons are UNMEASURED until model-backed runs are executed in the lab lane.

| Task | Validators | Null comp/recall | Null gate | Random comp/recall | Random gate | Grep comp/recall | Grep gate | Mechanical max | Model gates |
|---|---|---:|---|---:|---|---:|---|---:|---|
| tasks/contracts/T1-NDA-001 | PASS | 0.000000 / 0.000000 | PASS | 0.250000 / 0.000000 | UNMEASURED | 0.541250 / 0.500000 | UNMEASURED | 0.814286 (blanket, OK) | honest SKIPPED (no key); cheater SKIPPED (no key); judge SKIPPED (no key) |
| tasks/contracts/T2-MSA-001 | PASS | 0.000000 / 0.000000 | PASS | 0.250000 / 0.000000 | UNMEASURED | 0.250000 / 0.000000 | UNMEASURED | 0.408647 (blanket, OK) | honest SKIPPED (no key); cheater SKIPPED (no key); judge SKIPPED (no key) |
| tasks/generated/T1-MSA-105 | PASS | 0.000000 / 0.000000 | PASS | 0.250000 / 0.000000 | UNMEASURED | 0.250000 / 0.000000 | UNMEASURED | UNMEASURED | honest SKIPPED (no key); cheater SKIPPED (no key); judge SKIPPED (no key) |
| tasks/generated/T1-NDA-101 | PASS | 0.000000 / 0.000000 | PASS | 0.250000 / 0.000000 | UNMEASURED | 0.356250 / 0.250000 | UNMEASURED | UNMEASURED | honest SKIPPED (no key); cheater SKIPPED (no key); judge SKIPPED (no key) |
| tasks/generated/T1-NDA-103 | PASS | 0.000000 / 0.000000 | PASS | 0.250000 / 0.000000 | UNMEASURED | 0.567857 / 0.500000 | UNMEASURED | UNMEASURED | honest SKIPPED (no key); cheater SKIPPED (no key); judge SKIPPED (no key) |
| tasks/generated/T2-MSA-104 | PASS | 0.000000 / 0.000000 | PASS | 0.250000 / 0.000000 | UNMEASURED | 0.250000 / 0.000000 | UNMEASURED | UNMEASURED | honest SKIPPED (no key); cheater SKIPPED (no key); judge SKIPPED (no key) |
| tasks/generated/T2-MSA-106 | PASS | 0.000000 / 0.000000 | PASS | 0.250000 / 0.000000 | UNMEASURED | 0.366667 / 0.200000 | UNMEASURED | UNMEASURED | honest SKIPPED (no key); cheater SKIPPED (no key); judge SKIPPED (no key) |
| tasks/generated/T2-NDA-102 | PASS | 0.000000 / 0.000000 | PASS | 0.250000 / 0.000000 | UNMEASURED | 0.250000 / 0.000000 | UNMEASURED | UNMEASURED | honest SKIPPED (no key); cheater SKIPPED (no key); judge SKIPPED (no key) |

## Gate Notes

- Computable deterministic gates: validators must not FAIL; null composite must be <= 0.05.
- Random precision noise floor, grep <= 60% of honest, honest saturation band, and model cheater < honest are UNMEASURED without honest/model-cheater lab-lane runs.
- Deterministic failures: none.
