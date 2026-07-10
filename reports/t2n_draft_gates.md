# DRAFT-INSTANCES / UNSIGNED-FAMILIES — machine-drafted v2 families; attorney line-item review pending; not a release gate.

## Base inventory and generated distribution

| Area | Base | Playbook | Mixed eligible | Reason | Mixed generated | All-concessions |
|---|---|---|---|---|---:|---|
| ai | T2-AI-1302 | PB-AI-001 | True | usable: 4 authored rule overlaps ['R-001', 'R-002', 'R-009', 'R-012'] | 2 | True |
| ai | T2-AI-1303 | PB-AI-001 | True | usable: 4 authored rule overlaps ['R-001', 'R-002', 'R-009', 'R-012'] | 2 | False |
| crypto | T2-CRYPTO-1502 | PB-CRYPTO-001 | True | usable: 4 authored rule overlaps ['R-002', 'R-003', 'R-006', 'R-008'] | 2 | False |
| crypto | T2-CRYPTO-1503 | PB-CRYPTO-001 | True | usable: 4 authored rule overlaps ['R-002', 'R-003', 'R-006', 'R-008'] | 2 | False |
| privacy | T2-DPA-302 | PB-DPA-001 | True | usable: 2 authored rule overlaps ['R-002', 'R-006'] | 2 | False |
| privacy | T2-DPA-303 | PB-DPA-001 | True | usable: 2 authored rule overlaps ['R-001', 'R-002'] | 1 | False |
| privacy | T2-DPA-312 | PB-DPA-001 | True | usable: 2 authored rule overlaps ['R-001', 'R-003'] | 1 | False |
| employment | T2-EMP-702 | PB-EMP-001 | True | usable: 3 authored rule overlaps ['R-002', 'R-004', 'R-007'] | 2 | True |
| employment | T2-EMP-703 | PB-EMP-001 | True | usable: 3 authored rule overlaps ['R-002', 'R-004', 'R-007'] | 1 | False |
| employment | T2-EMP-712 | PB-EMP-001 | True | usable: 3 authored rule overlaps ['R-002', 'R-006', 'R-007'] | 1 | False |
| governance | T2-GOV-902 | PB-GOV-001 | True | usable: 4 authored rule overlaps ['R-002', 'R-006', 'R-007', 'R-013'] | 2 | True |
| governance | T2-GOV-903 | PB-GOV-001 | True | usable: 3 authored rule overlaps ['R-002', 'R-006', 'R-013'] | 1 | False |
| governance | T2-GOV-912 | PB-GOV-001 | True | usable: 3 authored rule overlaps ['R-002', 'R-007', 'R-013'] | 1 | False |
| ma | T2-MA-1102 | PB-MA-001 | True | usable: 4 authored rule overlaps ['R-001', 'R-006', 'R-008', 'R-011'] | 2 | False |
| ma | T2-MA-1103 | PB-MA-001 | True | usable: 4 authored rule overlaps ['R-001', 'R-006', 'R-008', 'R-011'] | 2 | False |
| contracts | T2-MSA-104 | PB-MSA-001 | True | usable: 3 authored rule overlaps ['R-001', 'R-003', 'R-006'] | 1 | False |
| contracts | T2-MSA-106 | PB-MSA-001 | True | usable: 3 authored rule overlaps ['R-003', 'R-006', 'R-008'] | 1 | False |
| contracts | T2-MSA-122 | PB-MSA-001 | True | usable: 2 authored rule overlaps ['R-003', 'R-008'] | 1 | False |
| contracts | T2-NDA-102 | PB-NDA-001 | False | one seeded deviation has expected_action=escalate and no expected_redline_text | 0 | False |
| contracts | T2-NDA-112 | PB-NDA-001 | True | usable: 2 authored rule overlaps ['R-002', 'R-007'] | 1 | False |

## Mechanical battery

| Strategy | Predicted | Min | Mean | Max (worst) | GAMED | Worst instances |
|---|---:|---:|---:|---:|---:|---|
| accept_all | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0 | T2N-V2-AI-01-S21238, T2N-V2-AI-02-S21171, T2N-V2-AI-03-S21308, T2N-V2-AI-04-S21139, T2N-V2-CRYPTO-01-S21287, T2N-V2-CRYPTO-02-S21305, T2N-V2-CRYPTO-03-S21255, T2N-V2-CRYPTO-04-S21239, T2N-V2-PRIVACY-01-S21302, T2N-V2-PRIVACY-02-S21405, T2N-V2-PRIVACY-03-S21474, T2N-V2-PRIVACY-04-S21237, T2N-V2-EMPLOYMENT-01-S21623, T2N-V2-EMPLOYMENT-02-S21403, T2N-V2-EMPLOYMENT-03-S21523, T2N-V2-EMPLOYMENT-04-S21575, T2N-V2-GOVERNANCE-01-S21689, T2N-V2-GOVERNANCE-02-S21554, T2N-V2-GOVERNANCE-03-S21640, T2N-V2-GOVERNANCE-04-S21471, T2N-V2-MA-01-S21687, T2N-V2-MA-02-S21637, T2N-V2-MA-03-S21502, T2N-V2-MA-04-S21707, T2N-V2-CONTRACTS-01-S21634, T2N-V2-CONTRACTS-02-S21788, T2N-V2-CONTRACTS-03-S21670, T2N-V2-CONTRACTS-04-S21756 |
| accept_all_but_1_harm | 0.200000 | 0.000000 | 0.000000 | 0.000000 | 0 | T2N-V2-AI-01-S21238, T2N-V2-AI-02-S21171, T2N-V2-AI-03-S21308, T2N-V2-AI-04-S21139, T2N-V2-CRYPTO-01-S21287, T2N-V2-CRYPTO-02-S21305, T2N-V2-CRYPTO-03-S21255, T2N-V2-CRYPTO-04-S21239, T2N-V2-PRIVACY-01-S21302, T2N-V2-PRIVACY-02-S21405, T2N-V2-PRIVACY-03-S21474, T2N-V2-PRIVACY-04-S21237, T2N-V2-EMPLOYMENT-01-S21623, T2N-V2-EMPLOYMENT-02-S21403, T2N-V2-EMPLOYMENT-03-S21523, T2N-V2-EMPLOYMENT-04-S21575, T2N-V2-GOVERNANCE-01-S21689, T2N-V2-GOVERNANCE-02-S21554, T2N-V2-GOVERNANCE-03-S21640, T2N-V2-GOVERNANCE-04-S21471, T2N-V2-MA-01-S21687, T2N-V2-MA-02-S21637, T2N-V2-MA-03-S21502, T2N-V2-MA-04-S21707, T2N-V2-CONTRACTS-01-S21634, T2N-V2-CONTRACTS-02-S21788, T2N-V2-CONTRACTS-03-S21670, T2N-V2-CONTRACTS-04-S21756 |
| accept_all_but_2_harms | 0.200000 | 0.000000 | 0.000000 | 0.000000 | 0 | T2N-V2-AI-01-S21238, T2N-V2-AI-02-S21171, T2N-V2-AI-03-S21308, T2N-V2-AI-04-S21139, T2N-V2-CRYPTO-01-S21287, T2N-V2-CRYPTO-02-S21305, T2N-V2-CRYPTO-03-S21255, T2N-V2-CRYPTO-04-S21239, T2N-V2-PRIVACY-01-S21302, T2N-V2-PRIVACY-02-S21405, T2N-V2-PRIVACY-03-S21474, T2N-V2-PRIVACY-04-S21237, T2N-V2-EMPLOYMENT-01-S21623, T2N-V2-EMPLOYMENT-02-S21403, T2N-V2-EMPLOYMENT-03-S21523, T2N-V2-EMPLOYMENT-04-S21575, T2N-V2-GOVERNANCE-01-S21689, T2N-V2-GOVERNANCE-02-S21554, T2N-V2-GOVERNANCE-03-S21640, T2N-V2-GOVERNANCE-04-S21471, T2N-V2-MA-01-S21687, T2N-V2-MA-02-S21637, T2N-V2-MA-03-S21502, T2N-V2-MA-04-S21707, T2N-V2-CONTRACTS-01-S21634, T2N-V2-CONTRACTS-02-S21788, T2N-V2-CONTRACTS-03-S21670, T2N-V2-CONTRACTS-04-S21756 |
| always_reject_counter | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0 | T2N-V2-AI-01-S21238, T2N-V2-AI-02-S21171, T2N-V2-AI-03-S21308, T2N-V2-AI-04-S21139, T2N-V2-CRYPTO-01-S21287, T2N-V2-CRYPTO-02-S21305, T2N-V2-CRYPTO-03-S21255, T2N-V2-CRYPTO-04-S21239, T2N-V2-PRIVACY-01-S21302, T2N-V2-PRIVACY-02-S21405, T2N-V2-PRIVACY-03-S21474, T2N-V2-PRIVACY-04-S21237, T2N-V2-EMPLOYMENT-01-S21623, T2N-V2-EMPLOYMENT-02-S21403, T2N-V2-EMPLOYMENT-03-S21523, T2N-V2-EMPLOYMENT-04-S21575, T2N-V2-GOVERNANCE-01-S21689, T2N-V2-GOVERNANCE-02-S21554, T2N-V2-GOVERNANCE-03-S21640, T2N-V2-GOVERNANCE-04-S21471, T2N-V2-MA-01-S21687, T2N-V2-MA-02-S21637, T2N-V2-MA-03-S21502, T2N-V2-MA-04-S21707, T2N-V2-CONTRACTS-01-S21634, T2N-V2-CONTRACTS-02-S21788, T2N-V2-CONTRACTS-03-S21670, T2N-V2-CONTRACTS-04-S21756 |
| before_text_quoter | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0 | T2N-V2-AI-01-S21238, T2N-V2-AI-02-S21171, T2N-V2-AI-03-S21308, T2N-V2-AI-04-S21139, T2N-V2-CRYPTO-01-S21287, T2N-V2-CRYPTO-02-S21305, T2N-V2-CRYPTO-03-S21255, T2N-V2-CRYPTO-04-S21239, T2N-V2-PRIVACY-01-S21302, T2N-V2-PRIVACY-02-S21405, T2N-V2-PRIVACY-03-S21474, T2N-V2-PRIVACY-04-S21237, T2N-V2-EMPLOYMENT-01-S21623, T2N-V2-EMPLOYMENT-02-S21403, T2N-V2-EMPLOYMENT-03-S21523, T2N-V2-EMPLOYMENT-04-S21575, T2N-V2-GOVERNANCE-01-S21689, T2N-V2-GOVERNANCE-02-S21554, T2N-V2-GOVERNANCE-03-S21640, T2N-V2-GOVERNANCE-04-S21471, T2N-V2-MA-01-S21687, T2N-V2-MA-02-S21637, T2N-V2-MA-03-S21502, T2N-V2-MA-04-S21707, T2N-V2-CONTRACTS-01-S21634, T2N-V2-CONTRACTS-02-S21788, T2N-V2-CONTRACTS-03-S21670, T2N-V2-CONTRACTS-04-S21756 |
| blanket_position_then_clause_match | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0 | T2N-V2-AI-01-S21238, T2N-V2-AI-02-S21171, T2N-V2-AI-03-S21308, T2N-V2-AI-04-S21139, T2N-V2-CRYPTO-01-S21287, T2N-V2-CRYPTO-02-S21305, T2N-V2-CRYPTO-03-S21255, T2N-V2-CRYPTO-04-S21239, T2N-V2-PRIVACY-01-S21302, T2N-V2-PRIVACY-02-S21405, T2N-V2-PRIVACY-03-S21474, T2N-V2-PRIVACY-04-S21237, T2N-V2-EMPLOYMENT-01-S21623, T2N-V2-EMPLOYMENT-02-S21403, T2N-V2-EMPLOYMENT-03-S21523, T2N-V2-EMPLOYMENT-04-S21575, T2N-V2-GOVERNANCE-01-S21689, T2N-V2-GOVERNANCE-02-S21554, T2N-V2-GOVERNANCE-03-S21640, T2N-V2-GOVERNANCE-04-S21471, T2N-V2-MA-01-S21687, T2N-V2-MA-02-S21637, T2N-V2-MA-03-S21502, T2N-V2-MA-04-S21707, T2N-V2-CONTRACTS-01-S21634, T2N-V2-CONTRACTS-02-S21788, T2N-V2-CONTRACTS-03-S21670, T2N-V2-CONTRACTS-04-S21756 |
| cheapest_harm_oracle | 0.200000 | 0.000000 | 0.000000 | 0.000000 | 0 | T2N-V2-AI-01-S21238, T2N-V2-AI-02-S21171, T2N-V2-AI-03-S21308, T2N-V2-AI-04-S21139, T2N-V2-CRYPTO-01-S21287, T2N-V2-CRYPTO-02-S21305, T2N-V2-CRYPTO-03-S21255, T2N-V2-CRYPTO-04-S21239, T2N-V2-PRIVACY-01-S21302, T2N-V2-PRIVACY-02-S21405, T2N-V2-PRIVACY-03-S21474, T2N-V2-PRIVACY-04-S21237, T2N-V2-EMPLOYMENT-01-S21623, T2N-V2-EMPLOYMENT-02-S21403, T2N-V2-EMPLOYMENT-03-S21523, T2N-V2-EMPLOYMENT-04-S21575, T2N-V2-GOVERNANCE-01-S21689, T2N-V2-GOVERNANCE-02-S21554, T2N-V2-GOVERNANCE-03-S21640, T2N-V2-GOVERNANCE-04-S21471, T2N-V2-MA-01-S21687, T2N-V2-MA-02-S21637, T2N-V2-MA-03-S21502, T2N-V2-MA-04-S21707, T2N-V2-CONTRACTS-01-S21634, T2N-V2-CONTRACTS-02-S21788, T2N-V2-CONTRACTS-03-S21670, T2N-V2-CONTRACTS-04-S21756 |
| common_threshold_lookup | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0 | T2N-V2-AI-01-S21238, T2N-V2-AI-02-S21171, T2N-V2-AI-03-S21308, T2N-V2-AI-04-S21139, T2N-V2-CRYPTO-01-S21287, T2N-V2-CRYPTO-02-S21305, T2N-V2-CRYPTO-03-S21255, T2N-V2-CRYPTO-04-S21239, T2N-V2-PRIVACY-01-S21302, T2N-V2-PRIVACY-02-S21405, T2N-V2-PRIVACY-03-S21474, T2N-V2-PRIVACY-04-S21237, T2N-V2-EMPLOYMENT-01-S21623, T2N-V2-EMPLOYMENT-02-S21403, T2N-V2-EMPLOYMENT-03-S21523, T2N-V2-EMPLOYMENT-04-S21575, T2N-V2-GOVERNANCE-01-S21689, T2N-V2-GOVERNANCE-02-S21554, T2N-V2-GOVERNANCE-03-S21640, T2N-V2-GOVERNANCE-04-S21471, T2N-V2-MA-01-S21687, T2N-V2-MA-02-S21637, T2N-V2-MA-03-S21502, T2N-V2-MA-04-S21707, T2N-V2-CONTRACTS-01-S21634, T2N-V2-CONTRACTS-02-S21788, T2N-V2-CONTRACTS-03-S21670, T2N-V2-CONTRACTS-04-S21756 |
| duplicate_action_washer | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 28 | T2N-V2-AI-01-S21238, T2N-V2-AI-02-S21171, T2N-V2-AI-03-S21308, T2N-V2-AI-04-S21139, T2N-V2-CRYPTO-01-S21287, T2N-V2-CRYPTO-02-S21305, T2N-V2-CRYPTO-03-S21255, T2N-V2-CRYPTO-04-S21239, T2N-V2-PRIVACY-01-S21302, T2N-V2-PRIVACY-02-S21405, T2N-V2-PRIVACY-03-S21474, T2N-V2-PRIVACY-04-S21237, T2N-V2-EMPLOYMENT-01-S21623, T2N-V2-EMPLOYMENT-02-S21403, T2N-V2-EMPLOYMENT-03-S21523, T2N-V2-EMPLOYMENT-04-S21575, T2N-V2-GOVERNANCE-01-S21689, T2N-V2-GOVERNANCE-02-S21554, T2N-V2-GOVERNANCE-03-S21640, T2N-V2-GOVERNANCE-04-S21471, T2N-V2-MA-01-S21687, T2N-V2-MA-02-S21637, T2N-V2-MA-03-S21502, T2N-V2-MA-04-S21707, T2N-V2-CONTRACTS-01-S21634, T2N-V2-CONTRACTS-02-S21788, T2N-V2-CONTRACTS-03-S21670, T2N-V2-CONTRACTS-04-S21756 |
| phase1_only | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0 | T2N-V2-AI-01-S21238, T2N-V2-AI-02-S21171, T2N-V2-AI-03-S21308, T2N-V2-AI-04-S21139, T2N-V2-CRYPTO-01-S21287, T2N-V2-CRYPTO-02-S21305, T2N-V2-CRYPTO-03-S21255, T2N-V2-CRYPTO-04-S21239, T2N-V2-PRIVACY-01-S21302, T2N-V2-PRIVACY-02-S21405, T2N-V2-PRIVACY-03-S21474, T2N-V2-PRIVACY-04-S21237, T2N-V2-EMPLOYMENT-01-S21623, T2N-V2-EMPLOYMENT-02-S21403, T2N-V2-EMPLOYMENT-03-S21523, T2N-V2-EMPLOYMENT-04-S21575, T2N-V2-GOVERNANCE-01-S21689, T2N-V2-GOVERNANCE-02-S21554, T2N-V2-GOVERNANCE-03-S21640, T2N-V2-GOVERNANCE-04-S21471, T2N-V2-MA-01-S21687, T2N-V2-MA-02-S21637, T2N-V2-MA-03-S21502, T2N-V2-MA-04-S21707, T2N-V2-CONTRACTS-01-S21634, T2N-V2-CONTRACTS-02-S21788, T2N-V2-CONTRACTS-03-S21670, T2N-V2-CONTRACTS-04-S21756 |
| prior_location_replayer | 0.200000 | 0.000000 | 0.000000 | 0.000000 | 0 | T2N-V2-AI-01-S21238, T2N-V2-AI-02-S21171, T2N-V2-AI-03-S21308, T2N-V2-AI-04-S21139, T2N-V2-CRYPTO-01-S21287, T2N-V2-CRYPTO-02-S21305, T2N-V2-CRYPTO-03-S21255, T2N-V2-CRYPTO-04-S21239, T2N-V2-PRIVACY-01-S21302, T2N-V2-PRIVACY-02-S21405, T2N-V2-PRIVACY-03-S21474, T2N-V2-PRIVACY-04-S21237, T2N-V2-EMPLOYMENT-01-S21623, T2N-V2-EMPLOYMENT-02-S21403, T2N-V2-EMPLOYMENT-03-S21523, T2N-V2-EMPLOYMENT-04-S21575, T2N-V2-GOVERNANCE-01-S21689, T2N-V2-GOVERNANCE-02-S21554, T2N-V2-GOVERNANCE-03-S21640, T2N-V2-GOVERNANCE-04-S21471, T2N-V2-MA-01-S21687, T2N-V2-MA-02-S21637, T2N-V2-MA-03-S21502, T2N-V2-MA-04-S21707, T2N-V2-CONTRACTS-01-S21634, T2N-V2-CONTRACTS-02-S21788, T2N-V2-CONTRACTS-03-S21670, T2N-V2-CONTRACTS-04-S21756 |
| reject_all_nearest_rule | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 28 | T2N-V2-AI-01-S21238, T2N-V2-AI-02-S21171, T2N-V2-AI-03-S21308, T2N-V2-AI-04-S21139, T2N-V2-CRYPTO-01-S21287, T2N-V2-CRYPTO-02-S21305, T2N-V2-CRYPTO-03-S21255, T2N-V2-CRYPTO-04-S21239, T2N-V2-PRIVACY-01-S21302, T2N-V2-PRIVACY-02-S21405, T2N-V2-PRIVACY-03-S21474, T2N-V2-PRIVACY-04-S21237, T2N-V2-EMPLOYMENT-01-S21623, T2N-V2-EMPLOYMENT-02-S21403, T2N-V2-EMPLOYMENT-03-S21523, T2N-V2-EMPLOYMENT-04-S21575, T2N-V2-GOVERNANCE-01-S21689, T2N-V2-GOVERNANCE-02-S21554, T2N-V2-GOVERNANCE-03-S21640, T2N-V2-GOVERNANCE-04-S21471, T2N-V2-MA-01-S21687, T2N-V2-MA-02-S21637, T2N-V2-MA-03-S21502, T2N-V2-MA-04-S21707, T2N-V2-CONTRACTS-01-S21634, T2N-V2-CONTRACTS-02-S21788, T2N-V2-CONTRACTS-03-S21670, T2N-V2-CONTRACTS-04-S21756 |
| slot_extractor_counter | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0 | T2N-V2-AI-01-S21238, T2N-V2-AI-02-S21171, T2N-V2-AI-03-S21308, T2N-V2-AI-04-S21139, T2N-V2-CRYPTO-01-S21287, T2N-V2-CRYPTO-02-S21305, T2N-V2-CRYPTO-03-S21255, T2N-V2-CRYPTO-04-S21239, T2N-V2-PRIVACY-01-S21302, T2N-V2-PRIVACY-02-S21405, T2N-V2-PRIVACY-03-S21474, T2N-V2-PRIVACY-04-S21237, T2N-V2-EMPLOYMENT-01-S21623, T2N-V2-EMPLOYMENT-02-S21403, T2N-V2-EMPLOYMENT-03-S21523, T2N-V2-EMPLOYMENT-04-S21575, T2N-V2-GOVERNANCE-01-S21689, T2N-V2-GOVERNANCE-02-S21554, T2N-V2-GOVERNANCE-03-S21640, T2N-V2-GOVERNANCE-04-S21471, T2N-V2-MA-01-S21687, T2N-V2-MA-02-S21637, T2N-V2-MA-03-S21502, T2N-V2-MA-04-S21707, T2N-V2-CONTRACTS-01-S21634, T2N-V2-CONTRACTS-02-S21788, T2N-V2-CONTRACTS-03-S21670, T2N-V2-CONTRACTS-04-S21756 |
| turn2_only | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0 | T2N-V2-AI-01-S21238, T2N-V2-AI-02-S21171, T2N-V2-AI-03-S21308, T2N-V2-AI-04-S21139, T2N-V2-CRYPTO-01-S21287, T2N-V2-CRYPTO-02-S21305, T2N-V2-CRYPTO-03-S21255, T2N-V2-CRYPTO-04-S21239, T2N-V2-PRIVACY-01-S21302, T2N-V2-PRIVACY-02-S21405, T2N-V2-PRIVACY-03-S21474, T2N-V2-PRIVACY-04-S21237, T2N-V2-EMPLOYMENT-01-S21623, T2N-V2-EMPLOYMENT-02-S21403, T2N-V2-EMPLOYMENT-03-S21523, T2N-V2-EMPLOYMENT-04-S21575, T2N-V2-GOVERNANCE-01-S21689, T2N-V2-GOVERNANCE-02-S21554, T2N-V2-GOVERNANCE-03-S21640, T2N-V2-GOVERNANCE-04-S21471, T2N-V2-MA-01-S21687, T2N-V2-MA-02-S21637, T2N-V2-MA-03-S21502, T2N-V2-MA-04-S21707, T2N-V2-CONTRACTS-01-S21634, T2N-V2-CONTRACTS-02-S21788, T2N-V2-CONTRACTS-03-S21670, T2N-V2-CONTRACTS-04-S21756 |
| unit_normalizing_slot_extractor | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0 | T2N-V2-AI-01-S21238, T2N-V2-AI-02-S21171, T2N-V2-AI-03-S21308, T2N-V2-AI-04-S21139, T2N-V2-CRYPTO-01-S21287, T2N-V2-CRYPTO-02-S21305, T2N-V2-CRYPTO-03-S21255, T2N-V2-CRYPTO-04-S21239, T2N-V2-PRIVACY-01-S21302, T2N-V2-PRIVACY-02-S21405, T2N-V2-PRIVACY-03-S21474, T2N-V2-PRIVACY-04-S21237, T2N-V2-EMPLOYMENT-01-S21623, T2N-V2-EMPLOYMENT-02-S21403, T2N-V2-EMPLOYMENT-03-S21523, T2N-V2-EMPLOYMENT-04-S21575, T2N-V2-GOVERNANCE-01-S21689, T2N-V2-GOVERNANCE-02-S21554, T2N-V2-GOVERNANCE-03-S21640, T2N-V2-GOVERNANCE-04-S21471, T2N-V2-MA-01-S21687, T2N-V2-MA-02-S21637, T2N-V2-MA-03-S21502, T2N-V2-MA-04-S21707, T2N-V2-CONTRACTS-01-S21634, T2N-V2-CONTRACTS-02-S21788, T2N-V2-CONTRACTS-03-S21670, T2N-V2-CONTRACTS-04-S21756 |

## Tranche statistical gates

```json
{
  "lookup": {
    "code": "V10-T2N-2",
    "name": "one-level lookup classifiers",
    "status": "PASS",
    "detail": "balanced_accuracy: task_ordinal[heldout=0]=0.500000, event_ordinal[heldout=0]=0.428571, section_bucket[heldout=0]=0.142857, operation[heldout=0]=0.500000, surface_template_hash[heldout=0]=0.500000, playbook_rule[heldout=0]=0.214286, family_split[heldout=0]=0.000000, task_ordinal[heldout=1]=0.500000, event_ordinal[heldout=1]=0.428571, section_bucket[heldout=1]=0.285714, operation[heldout=1]=0.500000, surface_template_hash[heldout=1]=0.500000, playbook_rule[heldout=1]=0.071429, family_split[heldout=1]=0.071429, task_ordinal[heldout=2]=0.500000, event_ordinal[heldout=2]=0.214286, section_bucket[heldout=2]=0.214286, operation[heldout=2]=0.500000, surface_template_hash[heldout=2]=0.500000, playbook_rule[heldout=2]=0.428571, family_split[heldout=2]=0.142857, task_ordinal[heldout=3]=0.500000, event_ordinal[heldout=3]=0.500000, section_bucket[heldout=3]=0.142857, operation[heldout=3]=0.500000, surface_template_hash[heldout=3]=0.500000, playbook_rule[heldout=3]=0.357143, family_split[heldout=3]=0.285714"
  },
  "permutation_mi": {
    "code": "V10-T2N-3",
    "name": "permutation mutual information",
    "status": "PASS",
    "detail": "event_ordinal:holm_p=1.000000,normalized_mi=0.027110; task_ordinal:holm_p=1.000000,normalized_mi=0.000000; section_bucket:holm_p=1.000000,normalized_mi=0.048161"
  },
  "quota_batch_attackers": {
    "max_slot_value": {
      "code": "V10-T2N-4",
      "name": "quota-constrained batch attacker",
      "status": "PASS",
      "detail": "heuristic=max_slot_value; quota={'acceptable': 28, 'unacceptable': 28}; balanced accuracy=0.392857"
    },
    "min_slot_value": {
      "code": "V10-T2N-4",
      "name": "quota-constrained batch attacker",
      "status": "PASS",
      "detail": "heuristic=min_slot_value; quota={'acceptable': 28, 'unacceptable': 28}; balanced accuracy=0.500000"
    },
    "sum_slots": {
      "code": "V10-T2N-4",
      "name": "quota-constrained batch attacker",
      "status": "PASS",
      "detail": "heuristic=sum_slots; quota={'acceptable': 28, 'unacceptable': 28}; balanced accuracy=0.428571"
    },
    "mean_slots": {
      "code": "V10-T2N-4",
      "name": "quota-constrained batch attacker",
      "status": "PASS",
      "detail": "heuristic=mean_slots; quota={'acceptable': 28, 'unacceptable': 28}; balanced accuracy=0.428571"
    },
    "single_threshold_per_slot": {
      "code": "V10-T2N-4",
      "name": "quota-constrained batch attacker",
      "status": "PASS",
      "detail": "heuristic=single_threshold_per_slot; quota={'acceptable': 28, 'unacceptable': 28}; balanced accuracy=0.535714; best_slot=decoy_values.1; acceptable_direction=high"
    },
    "single_slot_logistic": {
      "code": "V10-T2N-4",
      "name": "quota-constrained batch attacker",
      "status": "PASS",
      "detail": "heuristic=single_slot_logistic; quota={'acceptable': 28, 'unacceptable': 28}; balanced accuracy=0.535714; best_slot=decoy_values.0; coefficient=0.188117"
    }
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
      "composite": 0.9972870822658103,
      "mean_E": 0.9972870822658103,
      "counter_gate_pass": true
    }
  },
  "family_heldout_split": {
    "status": "PASS",
    "playbooks": [
      {
        "playbook_id": "PB-AI-001",
        "train_family_ids": [
          "CF-AI-CUSTOM-ASSETS-V2",
          "CF-AI-EXIT-V2",
          "CF-AI-POLICY-CHANGE-V2"
        ],
        "heldout_family_ids": [
          "CF-AI-TRAINING-V2"
        ],
        "evaluation_family_ids": [
          "CF-AI-TRAINING-V2"
        ],
        "train_heldout_disjoint": true
      },
      {
        "playbook_id": "PB-CRYPTO-001",
        "train_family_ids": [
          "CF-CRYPTO-ASSET-USE-V2",
          "CF-CRYPTO-ASSURANCE-V2",
          "CF-CRYPTO-DISTRIBUTIONS-V2"
        ],
        "heldout_family_ids": [
          "CF-CRYPTO-ESTATE-V2"
        ],
        "evaluation_family_ids": [
          "CF-CRYPTO-ESTATE-V2"
        ],
        "train_heldout_disjoint": true
      },
      {
        "playbook_id": "PB-DPA-001",
        "train_family_ids": [
          "CF-DPA-INSTRUCTIONS-V2",
          "CF-DPA-SUBPROCESSOR-V2",
          "CF-DPA-SUPPORT-V2"
        ],
        "heldout_family_ids": [
          "CF-DPA-USE-BOUNDARY-V2"
        ],
        "evaluation_family_ids": [
          "CF-DPA-USE-BOUNDARY-V2"
        ],
        "train_heldout_disjoint": true
      },
      {
        "playbook_id": "PB-EMP-001",
        "train_family_ids": [
          "CF-EMP-BONUS-V2",
          "CF-EMP-CAUSE-V2",
          "CF-EMP-EQUITY-V2"
        ],
        "heldout_family_ids": [
          "CF-EMP-INVENTIONS-V2"
        ],
        "evaluation_family_ids": [
          "CF-EMP-INVENTIONS-V2"
        ],
        "train_heldout_disjoint": true
      },
      {
        "playbook_id": "PB-GOV-001",
        "train_family_ids": [
          "CF-GOV-PROTECTIVE-V2",
          "CF-GOV-ROFR-V2",
          "CF-GOV-THRESHOLD-V2"
        ],
        "heldout_family_ids": [
          "CF-GOV-TRANSFER-V2"
        ],
        "evaluation_family_ids": [
          "CF-GOV-TRANSFER-V2"
        ],
        "train_heldout_disjoint": true
      },
      {
        "playbook_id": "PB-MA-001",
        "train_family_ids": [
          "CF-MA-ASSUMPTION-V2",
          "CF-MA-FRAUD-V2",
          "CF-MA-MAE-V2"
        ],
        "heldout_family_ids": [
          "CF-MA-WORKFORCE-V2"
        ],
        "evaluation_family_ids": [
          "CF-MA-WORKFORCE-V2"
        ],
        "train_heldout_disjoint": true
      },
      {
        "playbook_id": "PB-MSA-001",
        "train_family_ids": [
          "CF-MSA-DISCLAIMER-V2",
          "CF-MSA-LIABILITY-V2",
          "CF-MSA-TERMINATION-V2"
        ],
        "heldout_family_ids": [
          "CF-MSA-WORK-PRODUCT-V2"
        ],
        "evaluation_family_ids": [
          "CF-MSA-WORK-PRODUCT-V2"
        ],
        "train_heldout_disjoint": true
      },
      {
        "playbook_id": "PB-NDA-001",
        "train_family_ids": [
          "CF-NDA-AFFILIATES-V2",
          "CF-NDA-RETURN-V2",
          "CF-NDA-SURVIVAL-V2"
        ],
        "heldout_family_ids": [
          "CF-NDA-COMPELLED-V2"
        ],
        "evaluation_family_ids": [
          "CF-NDA-COMPELLED-V2"
        ],
        "train_heldout_disjoint": true
      }
    ]
  }
}
```

All concessions: [{'label': 'T2N-V2-AI-AC-S29001', 'composite': 1.0, 'gate_pass': True}, {'label': 'T2N-V2-EMPLOYMENT-AC-S29002', 'composite': 1.0, 'gate_pass': True}, {'label': 'T2N-V2-GOVERNANCE-AC-S29003', 'composite': 1.0, 'gate_pass': True}]; 9*3 <= 28 is True; 9*4 <= 28 is False.
