# DRAFT-INSTANCES / UNSIGNED-FAMILIES — machine-drafted, model-reviewed families; not a release gate.

## Base inventory (structural authoring-coverage finding)

| Area | Base | Mixed eligible | Reason | Mixed generated | All-concessions |
|---|---|---|---|---:|---|
| ai | T2-AI-1302 | False | only 0 counter-family rule match(es); needs two | 0 | True |
| ai | T2-AI-1303 | False | only 1 counter-family rule match(es); needs two | 0 | False |
| crypto | T2-CRYPTO-1502 | False | only 0 counter-family rule match(es); needs two | 0 | False |
| crypto | T2-CRYPTO-1503 | False | only 1 counter-family rule match(es); needs two | 0 | False |
| privacy | T2-DPA-302 | True | usable: two counter-family rule matches | 14 | False |
| privacy | T2-DPA-303 | False | only 0 counter-family rule match(es); needs two | 0 | False |
| privacy | T2-DPA-312 | False | only 0 counter-family rule match(es); needs two | 0 | False |
| employment | T2-EMP-702 | False | only 0 counter-family rule match(es); needs two | 0 | True |
| employment | T2-EMP-703 | False | only 0 counter-family rule match(es); needs two | 0 | False |
| employment | T2-EMP-712 | False | only 1 counter-family rule match(es); needs two | 0 | False |
| governance | T2-GOV-902 | False | only 0 counter-family rule match(es); needs two | 0 | True |
| governance | T2-GOV-903 | False | only 0 counter-family rule match(es); needs two | 0 | False |
| governance | T2-GOV-912 | False | only 0 counter-family rule match(es); needs two | 0 | False |
| ma | T2-MA-1102 | False | only 0 counter-family rule match(es); needs two | 0 | False |
| ma | T2-MA-1103 | False | only 0 counter-family rule match(es); needs two | 0 | False |
| contracts | T2-MSA-104 | True | usable: two counter-family rule matches | 14 | False |
| contracts | T2-MSA-106 | False | only 0 counter-family rule match(es); needs two | 0 | False |
| contracts | T2-MSA-122 | False | only 0 counter-family rule match(es); needs two | 0 | False |
| contracts | T2-NDA-102 | False | one seeded deviation has expected_action=escalate, not redline_with_fallback | 0 | False |
| contracts | T2-NDA-112 | False | only 0 counter-family rule match(es); needs two | 0 | False |

## Mechanical battery

| Strategy | Predicted | Min | Mean | Max (worst) | GAMED | Cause |
|---|---:|---:|---:|---:|---:|---|
| accept_all | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0 | Measured across 28 mixed draft instances. |
| accept_all_but_1_harm | 0.200000 | 0.000000 | 0.000000 | 0.000000 | 0 | Measured across 28 mixed draft instances. |
| accept_all_but_2_harms | 0.200000 | 0.000000 | 0.000000 | 0.000000 | 0 | Measured across 28 mixed draft instances. |
| always_reject_counter | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0 | TRANCHE-GATED: {"metrics": {"status": "EVALUATED", "RA": 0.0, "RU": 1.0, "Jmacro": 0.0, "acceptable_n": 28, "unacceptable_n": 28}, "gated": {"status": "EVALUATED", "composite": 0.0, "mean_E": 0.0, "counter_gate_pass": false}} |
| before_text_quoter | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0 | Measured across 28 mixed draft instances. |
| blanket_position_then_clause_match | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0 | Measured across 28 mixed draft instances. |
| cheapest_harm_oracle | 0.200000 | 0.000000 | 0.000000 | 0.000000 | 0 | Measured across 28 mixed draft instances. |
| common_threshold_lookup | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0 | TRANCHE-GATED: {"metrics": {"status": "EVALUATED", "RA": 1.0, "RU": 0.0, "Jmacro": 0.0, "acceptable_n": 28, "unacceptable_n": 28}, "gated": {"status": "EVALUATED", "composite": 0.0, "mean_E": 0.0, "counter_gate_pass": false}} |
| duplicate_action_washer | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 28 | Measured across 28 mixed draft instances. |
| phase1_only | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0 | Measured across 28 mixed draft instances. |
| prior_location_replayer | 0.200000 | 0.000000 | 0.000000 | 0.000000 | 0 | Measured across 28 mixed draft instances. |
| reject_all_nearest_rule | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 28 | Measured across 28 mixed draft instances. |
| slot_extractor_counter | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0 | TRANCHE-GATED: {"metrics": {"status": "EVALUATED", "RA": 0.17857142857142858, "RU": 0.6785714285714286, "Jmacro": 0.17857142857142858, "acceptable_n": 28, "unacceptable_n": 28}, "gated": {"status": "EVALUATED", "composite": 0.0, "mean_E": 0.0, "counter_gate_pass": false}} |
| turn2_only | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0 | Measured across 28 mixed draft instances. |
| unit_normalizing_slot_extractor | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0 | TRANCHE-GATED: {"metrics": {"status": "EVALUATED", "RA": 0.17857142857142858, "RU": 0.6785714285714286, "Jmacro": 0.17857142857142858, "acceptable_n": 28, "unacceptable_n": 28}, "gated": {"status": "EVALUATED", "composite": 0.0, "mean_E": 0.0, "counter_gate_pass": false}} |

## Tranche statistical gates

```json
{
  "lookup": {
    "code": "V10-T2N-2",
    "name": "one-level lookup classifiers",
    "status": "PASS",
    "detail": "ok"
  },
  "permutation_mi": {
    "code": "V10-T2N-3",
    "name": "permutation mutual information",
    "status": "PASS",
    "detail": "ok"
  },
  "quota_batch_attacker": {
    "code": "V10-T2N-4",
    "name": "quota-constrained batch attacker",
    "status": "FAIL",
    "detail": "heuristic=max_slot_value; quota={'acceptable': 28, 'unacceptable': 28}; balanced accuracy=0.821429; balanced accuracy 0.821 >=0.60"
  },
  "counter_macro_gate": {
    "metrics": {
      "status": "EVALUATED",
      "RA": 1.0,
      "RU": 1.0,
      "Jmacro": 1.0,
      "acceptable_n": 28,
      "unacceptable_n": 28
    },
    "gated": {
      "status": "EVALUATED",
      "composite": 0.9873397172404481,
      "mean_E": 0.9873397172404481,
      "counter_gate_pass": true
    }
  }
}
```

This is a genuine measured FAIL on the current 28-instance/2-area/4-family draft; it does not by itself establish whether the underlying counter families are gameable at real-release scale (many areas/families, proper held-out split) or whether it is an artifact of the draft's narrow base-inventory-constrained construction documented above; this remains open for the next step.

All concessions: [{'label': 'T2N-AI-1302-AC-S9001', 'composite': 1.0, 'gate_pass': True}, {'label': 'T2N-EMP-702-AC-S9002', 'composite': 1.0, 'gate_pass': True}, {'label': 'T2N-GOV-902-AC-S9003', 'composite': 1.0, 'gate_pass': True}]; 9*3 <= 28 is True; 9*4 <= 28 is False.
