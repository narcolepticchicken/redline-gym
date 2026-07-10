# DRAFT-INSTANCES / UNSIGNED-FAMILIES — pilots derive from machine-drafted families, not attorney-signed playbooks; not a release gate.

| Strategy | DPA composite | MSA composite | GAMED | family_ok / harm_integrity | v4 predicted C8 | Delta (measured − predicted) | Cause |
|---|---:|---:|---|---|---:|---|---|
| accept_all | 0.000000 | 0.000000 | DPA=False; MSA=False | DPA=False; MSA=False | 0.000000 | DPA=0.000000; MSA=0.000000 | Matches contract prediction. |
| accept_all_but_1_harm | 0.000000 | 0.000000 | DPA=False; MSA=False | DPA=False; MSA=False | 0.200000 | DPA=-0.200000; MSA=-0.200000 | blanket phase-1 recall: DPA=0.4 (2/5 deviations matched); MSA=0.4 (2/5 deviations matched); L floor fails (continuity requires exact-tuple matches on matched positions only), zeroing P2 regardless of phase-2 disposition correctness — not a driver defect. |
| accept_all_but_2_harms | 0.000000 | 0.000000 | DPA=False; MSA=False | DPA=False; MSA=False | 0.200000 | DPA=-0.200000; MSA=-0.200000 | blanket phase-1 recall: DPA=0.4 (2/5 deviations matched); MSA=0.4 (2/5 deviations matched); L floor fails (continuity requires exact-tuple matches on matched positions only), zeroing P2 regardless of phase-2 disposition correctness — not a driver defect. |
| always_reject_counter (TRANCHE-GATED) | 0.000000 | 0.000000 | DPA=False; MSA=False | DPA=True; MSA=True | 0.000000 | DPA=0.000000; MSA=0.000000 | TRANCHE-GATED — not assessable on two pilots. |
| before_text_quoter | 0.000000 | 0.000000 | DPA=False; MSA=False | DPA=False; MSA=False | 0.000000 | DPA=0.000000; MSA=0.000000 | Matches contract prediction. |
| blanket_position_then_clause_match | 0.000000 | 0.000000 | DPA=False; MSA=False | DPA=True; MSA=True | 0.000000 | DPA=0.000000; MSA=0.000000 | Matches contract prediction. |
| cheapest_harm_oracle | 0.000000 | 0.000000 | DPA=False; MSA=False | DPA=False; MSA=False | 0.200000 | DPA=-0.200000; MSA=-0.200000 | blanket phase-1 recall: DPA=0.4 (2/5 deviations matched); MSA=0.4 (2/5 deviations matched); L floor fails (continuity requires exact-tuple matches on matched positions only), zeroing P2 regardless of phase-2 disposition correctness — not a driver defect. |
| common_threshold_lookup (TRANCHE-GATED) | 0.000000 | 0.000000 | DPA=False; MSA=False | DPA=False; MSA=False | 0.000000 | DPA=0.000000; MSA=0.000000 | TRANCHE-GATED — not assessable on two pilots. |
| duplicate_action_washer | 0.000000 | 0.000000 | DPA=True; MSA=True | DPA=True; MSA=True | 0.000000 | DPA=0.000000; MSA=0.000000 | Matches contract prediction. |
| phase1_only | 0.000000 | 0.000000 | DPA=False; MSA=False | DPA=False; MSA=False | 0.000000 | DPA=0.000000; MSA=0.000000 | Matches contract prediction. |
| prior_location_replayer | 0.000000 | 0.000000 | DPA=False; MSA=False | DPA=False; MSA=False | 0.200000 | DPA=-0.200000; MSA=-0.200000 | blanket phase-1 recall: DPA=0.4 (2/5 deviations matched); MSA=0.4 (2/5 deviations matched); L floor fails (continuity requires exact-tuple matches on matched positions only), zeroing P2 regardless of phase-2 disposition correctness — not a driver defect. |
| reject_all_nearest_rule | 0.000000 | 0.000000 | DPA=True; MSA=True | DPA=True; MSA=True | 0.000000 | DPA=0.000000; MSA=0.000000 | Matches contract prediction. |
| slot_extractor_counter (TRANCHE-GATED) | 0.000000 | 0.000000 | DPA=False; MSA=False | DPA=False; MSA=True | 0.000000 | DPA=0.000000; MSA=0.000000 | TRANCHE-GATED — not assessable on two pilots. |
| turn2_only | 0.000000 | 0.000000 | DPA=False; MSA=False | DPA=False; MSA=True | 0.000000 | DPA=0.000000; MSA=0.000000 | Matches contract prediction. |
| unit_normalizing_slot_extractor (TRANCHE-GATED) | 0.000000 | 0.000000 | DPA=False; MSA=False | DPA=False; MSA=True | 0.000000 | DPA=0.000000; MSA=0.000000 | TRANCHE-GATED — not assessable on two pilots. |

| quota_constrained_batch_attacker (SKIPPED) | — | — | — | — | 0.000000 | — | quota_constrained_batch_attacker is SKIPPED: its definition needs release-wide quota/tranche membership across >=28-instance, >=4-tranche evaluation. Episodes have no cross-episode state or batch API; fabricating either would violate the observable-side-information boundary. V10 assesses this attack at release audit time, not on these two pilots. |

## Quota-constrained batch attacker

quota_constrained_batch_attacker is SKIPPED: its definition needs release-wide quota/tranche membership across >=28-instance, >=4-tranche evaluation. Episodes have no cross-episode state or batch API; fabricating either would violate the observable-side-information boundary. V10 assesses this attack at release audit time, not on these two pilots.
