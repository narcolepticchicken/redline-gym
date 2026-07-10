# T2-N v2 counter-family attorney-stand-in review

Date: 2026-07-10  
Model label required by dispatcher: `gpt-5.6-sol`  
Scope: all 32 v2 counter families and all 256 realized acceptable/unacceptable renders in the seven `generator/t2n_families/*.json` files, checked against every rule in the eight live playbooks. The playbooks were read in full and were not edited.

The source of truth for every substantive correction was `scripts/build_t2n_family_v2.py`; generated family JSON and tranche artifacts were regenerated from that source. The coordinated status now reads exactly `machine-drafted v2, model-reviewed 2026-07-10 (gpt-5.6-sol), Aaron pre-authorized — attorney line-item review pending` in the builder, all seven generated family files, the runtime gate, and the authorized test assertion.

## AI — PB-AI-001

- **CF-AI-TRAINING-V2 / R-001 — applied boundary correction.** Live `escalation_trigger`: “Escalate if Vendor can use Customer materials or service activity for model or service improvement without Customer's express opt-in.” Live `deterministic_checks`: `{}`. The former predicate rejected a written opt-in covering all service activity even though the trigger rejects use *without* express opt-in. Changed the boundary to `training_scope == 'none' or written_opt_in`; the broad-use acceptable render now says the opt-in is prior, express, and written. Oral/implied or absent consent remains unacceptable.
- **CF-AI-CUSTOM-ASSETS-V2 / R-002 — applied boundary correction.** Live `escalation_trigger`: “Escalate if Vendor can reuse, share, or deny Customer portability for Customer-specific fine-tuned artifacts.” Live `deterministic_checks`: `{}`. Removed the invented 30-day portability cutoff, under which materially identical exclusive-use/export rights at 35 or 45 days were rejected without a signed threshold. The final predicate requires assigned or exclusive control plus an actually available complete export; nonexclusive reuse or export denial is unacceptable.
- **CF-AI-POLICY-CHANGE-V2 / R-009 — applied boundary correction.** Live `escalation_trigger`: “Escalate if Vendor can unilaterally expand safety or acceptable-use obligations without bounds or notice.” Live `deterministic_checks`: `{}`. Replaced the unsupported 15-day rejection line with the signed combination: legal/objective-safety basis plus advance notice. Realized acceptable notices remain 15–45 days; the unacceptable timing cases now provide no advance notice, while commercial-discretion changes remain unacceptable even with notice.
- **CF-AI-EXIT-V2 / R-012 — applied boundary and render-realism corrections.** Live `escalation_trigger`: “Escalate if Customer cannot export fine-tunes, embeddings, or operational data needed to transition away from Vendor.” Live `deterministic_checks`: `{}`. Removed the invented 20-hour minimum; the final boundary requires complete portable coverage and actual transition assistance, with zero-assistance and data-only cases rejected. Reworded the decoy so a zero-assistance render no longer referred to checkpoints “while assistance is active.”

All 32 final AI renders were reread after regeneration. Every acceptable render also preserves the R-001 training restriction, R-002 artifact control/portability, and R-012 exit coverage applicable to its subject; no acceptable text creates an R-003 output-ownership, R-004 indemnity, R-005 benchmarking, R-008 retention/residency, R-010 subprocessor, or R-011 cap conflict.

Borderline items: none.

## MSA — PB-MSA-001

- **CF-MSA-LIABILITY-V2 / R-001 — reviewed without substantive change.** Live `escalation_trigger`: “Escalate if high-risk claim categories are financially limited after negotiation.” Live `deterministic_checks`: `{}`. All acceptable renders preserve confidentiality, data-protection, indemnification, infringement, fraud, willful-misconduct, and gross-negligence carveouts; this cures the sibling-rule/confidentiality defect class identified in the predecessor review. The ordinary cap remains at no more than 12 months.
- **CF-MSA-WORK-PRODUCT-V2 / R-003 — reviewed without change.** Live `escalation_trigger`: “Escalate if Customer cannot own or freely use project-specific work product.” Live `deterministic_checks`: `{}`. Acceptable renders assign 100% of project-specific deliverables and grant a perpetual embedded-material license. Partial assignment, expiring licenses, and revocable licenses remain unacceptable.
- **CF-MSA-TERMINATION-V2 / R-006 — reviewed without change.** Live `escalation_trigger`: “Escalate if optional exit requires a material penalty or payment for unused services.” Live `deterministic_checks`: `{}`. Acceptable renders require no more than 30 days' notice and zero unused-service charge; every unacceptable render fails at least one signed component.
- **CF-MSA-DISCLAIMER-V2 / R-008 — reviewed without change.** Live `escalation_trigger`: “Escalate if disclaimer language erases express promises or core remedies.” Live `deterministic_checks`: `{}`. Acceptable renders preserve express warranties, service levels, data protection, confidentiality, indemnity, and express remedies. The two decisive inputs are conjunctive and legally coherent.

All 32 final MSA renders were checked against the full playbook. No acceptable liability render caps the R-004 incident duty or R-005 data-processing duties; no work-product render creates an R-009 unilateral amendment or R-010 assignment right; no disclaimer render erases an R-002 indemnity or other core remedy.

Borderline item: **CF-MSA-LIABILITY-V2**. The position says ordinary exposure “should sit at annual spend,” while the predicate accepts 6- and 9-month caps as well as 12 months. The trigger is limited to financially limiting high-risk categories, so the current “12 months as a ceiling” reading is defensible for customer exposure, but a customer-side attorney may instead want 12 months to be a floor for Vendor ordinary liability. Recommendation: Aaron should decide whether the ordinary cap is a ceiling only or an exact/floor annual-spend position.

## NDA — PB-NDA-001

- **CF-NDA-AFFILIATES-V2 / R-002 — applied boundary and render correction.** Live `escalation_trigger`: “Escalate affiliate coverage gaps if the transaction requires affiliate participation.” Live `deterministic_checks`: `{}`. Removed the predicate path that treated current nonparticipation as sufficient despite a dormant future coverage gap. The final boundary requires both affiliate coverage and contracting-party responsibility. Reworded the coverage-gap render so it no longer made a party “responsible for affiliate compliance” while simultaneously declaring that the affiliate had no NDA duty.
- **CF-NDA-COMPELLED-V2 / R-007 — applied boundary/polarity correction.** Live `escalation_trigger`: “Escalate any carve-out from notice or cooperation obligations.” Live `deterministic_checks`: `{"must_not_contain":["without prior notice"]}`. The former expression used an unsupported 24-hour threshold and, because the prose measured hours *before* disclosure, labeled 36–48 hours of advance notice worse than 12–24 hours. Replaced it with prompt advance notice when legally permitted, or prompt notice after a legal prohibition ends, plus reasonable cooperation. No render contains the banned literal.
- **CF-NDA-RETURN-V2 / R-008 — applied controlling-trigger correction.** Live `escalation_trigger`: “Escalate if the return/destruction period exceeds 30 days or retained copies are unprotected.” Live `deterministic_checks`: `{"must_not_contain":["ninety days"]}`. The former v2 expression incorrectly accepted 31–45 days when combined with certification and a narrow carveout. Certification does not override the exact “exceeds 30 days” trigger. The final predicate is `return_days <= 30 and retained_copies_protected`; 35- and 45-day periods are unacceptable even with protected copies, and 15- or 30-day periods are unacceptable if retained copies lose continuing restrictions. Certification was removed as a decisive condition because the live rule does not require it.
- **CF-NDA-SURVIVAL-V2 / R-009 — reviewed boundary; applied render cleanup.** Live `escalation_trigger`: “Escalate if survival is shorter than three years or trade secrets expire automatically.” Live `deterministic_checks`: `{}`. The predicate remains the exact conjunction of at least three years and an indefinite trade-secret tail. Corrected “1 years” and clarified that the administrative review decoy does not itself change the stated legal term.

All 32 final NDA renders were checked against R-001 through R-014. No acceptable render includes any sibling deterministic ban (`marked confidential`, `internal business purpose`, `slight care`, or `without prior notice`), creates a residuals clause, grants an IP license, or removes equitable relief.

Borderline items: none.

## CRYPTO — PB-CRYPTO-001

- **CF-CRYPTO-ASSET-USE-V2 / R-002 — applied boundary correction.** Live `escalation_trigger`: “Escalate if the custodian can use, lend, pledge, transfer, or encumber customer assets without written customer consent.” Live `deterministic_checks`: `{}`. The former predicate rejected a broad but express prior written consent even though the trigger turns on absence of written consent. The final boundary accepts no use or use covered by prior written consent; oral/implied and no-consent cases remain unacceptable.
- **CF-CRYPTO-ESTATE-V2 / R-003 — reviewed boundary; applied render correction.** Live `escalation_trigger`: “Escalate if estate-treatment language is missing or suggests customer assets become custodian property.” Live `deterministic_checks`: `{}`. The ownership-plus-estate predicate remains correct. Replaced internally contradictory unacceptable prose saying the Custodian held “legal and beneficial title” while the same assets were excluded from its estate; the final text coherently states that Customer ownership is not acknowledged even though an estate assertion is made.
- **CF-CRYPTO-ASSURANCE-V2 / R-006 — applied boundary and render correction.** Live `escalation_trigger`: “Escalate if the customer has no recurring controls evidence or no reasonable path to follow up after material control events.” Live `deterministic_checks`: `{}`. Retained the exact annual-or-more-frequent SOC boundary, but replaced the invented 72-hour material-failure cutoff with the live qualitative requirement of prompt notice. Changed the follow-up decoy to run after Customer's request so it no longer implied earlier notice in a render that deliberately deferred failure notice to the next routine report.
- **CF-CRYPTO-DISTRIBUTIONS-V2 / R-008 — reviewed without change.** Live `escalation_trigger`: “Escalate if network distributions are retained by the custodian by default or excluded from customer entitlement without a narrow legal or support basis.” Live `deterministic_checks`: `{}`. The final predicate gives Customer 100% absent an exception and permits zero credit only for express Customer decline or legal prohibition with zero Custodian retention. No acceptable render relabels operational discretion as a narrow exception.

All 32 final custody renders were checked against the full playbook. Acceptable asset-use clauses retain beneficial ownership; estate clauses do not defeat R-001 segregation; assurance clauses preserve incident follow-up; distribution clauses do not create staking, freeze, subcustody, or termination rights inconsistent with sibling rules.

Borderline items: none.

## DPA — PB-DPA-001

- **CF-DPA-INSTRUCTIONS-V2 / R-001 — applied boundary correction.** Live `escalation_trigger`: “Escalate if the vendor can act outside documented customer directions.” Live `deterministic_checks`: `{}`. Removed the invented five-day notice condition and the unsupported premise that legally required processing becomes unacceptable solely because notice is omitted. The final predicate permits processing required by law or processing on documented instructions within the agreed services; instructions purporting to authorize unrelated activity and Vendor-discretion processing are unacceptable.
- **CF-DPA-USE-BOUNDARY-V2 / R-002 — reviewed without change.** Live `escalation_trigger`: “Escalate if the vendor can repurpose protected material for independent business benefit.” Live `deterministic_checks`: `{}`. Customer-directed service use remains acceptable, while independent use is acceptable only after irreversible anonymization. This was also checked against R-011: pseudonymized, derived, telemetry, and combined personal data remain inside the DPA and are not mislabeled acceptable.
- **CF-DPA-SUBPROCESSOR-V2 / R-003 — applied boundary correction.** Live `escalation_trigger`: “Escalate if downstream providers can handle protected data without approval controls, equivalent written duties, or vendor responsibility.” Live `deterministic_checks`: `{}`. Removed the unsupported 30-day minimum. The final expression requires pass-through duties and either prior approval or a genuine advance notice-and-objection process; zero advance notice is rejected, while the realized notice-route acceptable cases remain 30 and 45 days. Prior-approval renders now expressly state when approval is requested, so every decisive value appears in the realized prose.
- **CF-DPA-SUPPORT-V2 / R-006 — applied boundary and render correction.** Live `escalation_trigger`: “Escalate if the customer lacks practical support for rights requests or official inquiries.” Live `deterministic_checks`: `{}`. Removed invented 10/15-day response thresholds under which every render still promised reasonable assistance. The final boundary requires practical support across the fallback's three express categories: data-subject requests, regulator inquiries, and privacy assessments. Unacceptable cases omit regulator support or disclaim practical assistance. Automated portal-status decoys no longer contradict a no-assistance clause.

All 32 final DPA renders were checked against the full playbook. In particular, acceptable R-002 independent-use text also satisfies R-011's irreversible-anonymization perimeter; acceptable subprocessor text preserves equivalent duties and Vendor responsibility; none of the acceptable clauses creates a breach-notice, transfer, exit, audit, personnel, liability, or term conflict.

Borderline items: none.

## EMP — PB-EMP-001

- **CF-EMP-CAUSE-V2 / R-002 — applied boundary correction.** Live `escalation_trigger`: “Escalate if Company can end employment for cause only after an unusually narrow event.” Live `deterministic_checks`: `{}`. Removed the unsupported 10-day cure threshold and the backwards rejection of broader Cause based on a minor-event theory not stated in the playbook. The final predicate requires both serious-misconduct coverage and material duty/policy/agreement-breach coverage. Corrected singular day grammar in the adjacent notice decoy.
- **CF-EMP-INVENTIONS-V2 / R-004 — reviewed without change.** Live `escalation_trigger`: “Escalate if company information or employment-created intellectual property is not protected.” Live `deterministic_checks`: `{}`. Employment-created assets remain assigned; prior inventions are excluded only when listed on a signed schedule; an employment-created improvement cannot be swept into the prior-invention exclusion.
- **CF-EMP-BONUS-V2 / R-006 — applied boundary correction.** Live `escalation_trigger`: “Escalate if the agreement promises an automatic or guaranteed bonus.” Live `deterministic_checks`: `{}`. Removed the invented 30% ceiling. Any positive target is acceptable when the signed written plan states objective metrics, approval requirements, and payment timing; positive automatic bonuses without that plan remain unacceptable; discretionary/no-entitlement text remains acceptable.
- **CF-EMP-EQUITY-V2 / R-007 — applied boundary and realism correction.** Live `escalation_trigger`: “Escalate if a side clause gives equity rights beyond the plan or award documents.” Live `deterministic_checks`: `{}`. Removed the impossible 125% acceleration render and the redundant percentage ceiling. The final boundary is no extra acceleration or acceleration actually authorized by the plan and signed award; every nonzero extra-plan acceleration is unacceptable.

All 32 final employment renders were checked against the full playbook. Acceptable Cause language does not create fixed employment, severance, good-reason, or tax rights; inventions text preserves confidentiality; bonus/equity text does not defeat clawback or create extra-plan rights.

Borderline items: none.

## GOV — PB-GOV-001

- **CF-GOV-PROTECTIVE-V2 / R-002 — reviewed without change.** Live `escalation_trigger`: “Escalate if investors receive approval rights over unspecified, discretionary, or open-ended matters.” Live `deterministic_checks`: `{}`. The predicate accepts a closed enumerated matter or a separately signed Company covenant and rejects an Investor-defined open-ended materiality veto.
- **CF-GOV-ROFR-V2 / R-006 — reviewed without change.** Live `escalation_trigger`: “Escalate if investors can buy offered shares before Company has the first purchase right.” Live `deterministic_checks`: `{}`. Investor purchase is permitted only after Company declines or the Company-first period expires. The timing polarity is correct: more investor delay is not treated as worse.
- **CF-GOV-TRANSFER-V2 / R-007 — reviewed boundary; applied render/decoy correction.** Live `escalation_trigger`: “Escalate if transfer limits omit customary permitted-transferee carve-outs or fail to bind recipients.” Live `deterministic_checks`: `{}`. The predicate remains customary transferee plus written joinder. Replaced the “executed joinder” decoy, which contradicted unacceptable renders saying the recipient did not agree in writing, with a ministerial transfer record; corrected singular day grammar and renamed the decoy metadata accordingly.
- **CF-GOV-THRESHOLD-V2 / R-013 — reviewed boundary; applied render/metadata correction.** Live `escalation_trigger`: “Escalate if definitions lower investor approval thresholds or let a small holder exercise consent rights.” Live `deterministic_checks`: `{}`. The predicate correctly requires more than 50% Series A approval and at least 1,000,000 shares. Higher approval/share thresholds are not labeled harmful. Corrected the decoy ID from “notice_record_days” to `consent_record_years` to match the rendered unit and added standard thousands separators to share counts.

All 32 final governance renders were checked against the full playbook. No acceptable protective provision imports an ordinary-course veto under R-003; no transfer/ROFR render creates an information, confidentiality, MFN, termination, or threshold conflict.

Borderline items: none.

## MA — PB-MA-001

- **CF-MA-ASSUMPTION-V2 / R-001 — applied boundary and render correction.** Live `escalation_trigger`: “Escalate if the assumed-liability language captures unspecified, ordinary-course, or catch-all seller liabilities.” Live `deterministic_checks`: `{"must_not_contain":["unreviewed assumption marker"]}`. Removed the invented five-section ceiling. The final boundary accepts a closed enumerated agreement list or identified obligations in a signed amendment only when there are zero catch-all categories; unsigned addenda and any ordinary-course/unspecified catch-all remain unacceptable. Reworded catch-all renders so “only” no longer contradicted an additional catch-all assumption.
- **CF-MA-FRAUD-V2 / R-006 — reviewed boundary; applied render correction.** Live `escalation_trigger`: “Escalate if no-reliance language can be read to waive or limit fraud-based claims.” Live `deterministic_checks`: `{"must_not_contain":["unreviewed reliance marker"]}`. The predicate remains preservation of fraud claims plus exclusion from the cap. Fixed an internally contradictory unacceptable render that referred to “those preserved claims” immediately after barring them.
- **CF-MA-WORKFORCE-V2 / R-008 — reviewed without change.** Live `escalation_trigger`: “Escalate if Buyer must hire all employees, match all terms, or admit successor liability.” Live `deterministic_checks`: `{"must_not_contain":["unreviewed workforce marker"]}`. Acceptable renders have zero mandatory-offer percentage, Buyer-set terms, and no successor-liability admission. Every unacceptable render introduces a mandatory percentage or admission.
- **CF-MA-MAE-V2 / R-011 — applied boundary and render correction.** Live `escalation_trigger`: “Escalate if Buyer must close despite a material adverse effect.” Live `deterministic_checks`: `{"must_not_contain":["unreviewed condition marker"]}`. The former predicate treated the current factual absence of an MAE as a substitute for a contractual closing condition and even labeled Buyer “unconditionally obligated to close” acceptable when no MAE had yet occurred. The final family requires the closing condition to cover both Purchased Assets and the acquired business; omission of either scope is unacceptable. Corrected singular day grammar in the notice decoy.

All 32 final M&A renders were checked against all 15 rules and all deterministic markers. No acceptable render contains any `unreviewed ... marker`, undermines excluded liabilities, survival, cap/basket, escrow, consents, restrictive covenants, adjustment mechanics, schedules, or technology-asset coverage.

Borderline items: none.

## Precedent-corrections audit

### Governance reporting cadence

PB-GOV-001 R-008 remains untargeted. Its exact live `escalation_trigger` is: “Escalate if investors receive monthly reporting, unrestricted inspection, or access beyond reasonable confidentiality and sensitivity limits.” Its live `deterministic_checks` is absent (`{}`). The only final governance targets are R-002, R-006, R-007, and R-013. None reintroduces an R-008-shaped polarity error:

- R-002 uses closed enumeration/separate signed agreement, not cadence.
- R-006 treats investor purchase delay at least as long as the Company ROFR period as acceptable; a longer delay preserves, rather than harms, Company priority.
- R-007 is categorical permitted-transferee status plus written binding.
- R-013 rejects *lower* approval and Major Investor thresholds; higher thresholds are not mislabeled harmful.

The predecessor correction is therefore still honored.

### NDA return/destruction timing

PB-NDA-001 R-008's exact live fields are:

- `position`: “Return or destruction should occur promptly upon request, with archival and legal-hold copies remaining protected.”
- `fallback`: “Upon request, Recipient will promptly return or destroy Confidential Information, except archival or legal-hold copies retained under continuing confidentiality obligations.”
- `escalation_trigger`: “Escalate if the return/destruction period exceeds 30 days or retained copies are unprotected.”
- `deterministic_checks`: `{"must_not_contain":["ninety days"]}`.

The design memo's claim that 31–45 days become acceptable with certified destruction and a narrow carveout is not supported by the live trigger; “exceeds 30 days” is unconditional. That discrepancy was fixed at source. The final predicate is `return_days <= 30 and retained_copies_protected`. Across all eight final R-008 renders, the banned literal appears zero times in both pools. The backup-cycle decoy never equals `return_days` in the same render (zero collisions). The precedent lesson is therefore honored after correction, not merely assumed from the design memo.

## Final verification

- **Baseline:** before edits, the requested family validator returned `families: 32 bad: []`, diversity returned `[]`, the standalone restricted-AST predicate evaluator returned `families: 32 renders: 256 mismatches: []`, all 32 copied grounding records matched the live playbooks, and `python3 -m pytest -q` returned **170 passed, 0 failed**.
- **Final mechanical validation:** `validate_counter_family()` returned `[]` for all 32 families; `validate_family_pool_diversity()` returned `[]`.
- **Final predicate evaluation:** every expression was parsed through an AST allowlist limited to boolean/comparison/name/constant/set operations and evaluated with `__builtins__` removed against merged counter/context slots. Result: **256/256 correct**, zero mismatches (all 128 acceptable true; all 128 unacceptable false).
- **Grounding and deterministic scans:** all 32 `playbook_grounding` copies remain exact matches to the live playbooks. Whole-playbook banned-literal scan found zero hits. Same-render numeric decoy/decisive collision scan found zero hits. Singular-unit scan found zero `1 days/years/hours/months` defects.
- **Tranche regeneration:** `python3 scripts/run_t2n_tranche_gates.py` exited 0. Final tranche inventory is 28 mixed plus 3 all-concession instances, with 28 acceptable and 28 unacceptable counters; all recorded per-instance validator statuses are PASS. Four all-concession episodes remain noncompliant as designed.
- **Determinism:** two consecutive unchanged tranche regenerations produced identical SHA-256 manifests for **251 files** (`cmp` exit 0).
- **Legacy gates:** `bash scripts/run_t2n_gates.sh` exited 0 and its internal pytest run returned **170 passed**. As documented by the request, it then clobbered `reports/t2n_draft_gates.json`/`.md` into the legacy two-pilot strategy-report shape. No tracked `runs/t2n_gates/` bytes changed.
- **Final tests:** a separate final `python3 -m pytest -q` returned **170 passed, 0 failed**. Only the expressly authorized exact `_status` assertion changed; no substantive test assertion was weakened.
- **Byte-diff summary:** 116 tracked files differ from HEAD: 7 generated family JSON files; the builder and runtime gate (2); 3 reports; 103 regenerated `tasks/t2n_draft/T2N-V2-*` artifacts; and 1 authorized test file. The pre-tranche content set was 10 tracked files (7 family JSONs, builder, runtime gate, authorized test). The 3 reports and 103 instance artifacts are deterministic consequences of regeneration. `runs/t2n_gates/` has zero tracked diffs.
- **Repository hygiene:** `git diff --check` passes. Cached/staged diff count is zero. No commit was created; HEAD remained `5cc1b91`. No file under `playbooks/**`, `adapters/`, `data/`, `runs_v02_nohup.log`, `SPEC.md`, or `docs/t2n/family_design_v2.md` was edited. The three pre-existing untracked paths remain untouched.

## Fix totals

- **Boundary-correctness:** 17 family-level corrections — AI 4; CRYPTO 2; DPA 3; EMP 3; NDA 3; MA 2; MSA 0; GOV 0.
- **Render-realism:** 13 issue clusters corrected, including contradictory title/estate, assistance/decoy, joinder/decoy, fraud-cap, affiliate-duty, MAE/fact, and “only”/catch-all language; impossible 125% acceleration; singular-unit defects; decoy-unit metadata; and share-number formatting. Some overlap the 17 boundary redesigns and are counted here because they were independently defective prose.
- **Cross-rule-consistency:** 0 new cross-rule fixes were required after the final whole-playbook pass. All 128 acceptable renders were checked against sibling rules; the important inherited safeguards (MSA cap carveouts and DPA irreversible-anonymization perimeter) are present.
- **Mechanical:** 1 coordinated dependency change — the exact required `_status` string across builder, seven generated files, runtime gate, and authorized test assertion. Validator-driven slot/render-form/twin metadata changes were regenerated as part of the substantive family corrections and are not double-counted.

## Borderline items

Count: **1**.

1. **CF-MSA-LIABILITY-V2 / PB-MSA-001 R-001:** decide whether 12 months of fees is only a ceiling on ordinary mutual exposure (current predicate) or also a floor for Vendor ordinary liability. The position and customer-side economics can support the latter; the exact escalation trigger expressly focuses on capping high-risk categories and supports the current former reading.

---

## Aaron ruling 2026-07-10: MSA R-001 borderline

RULED: ceiling only. The 12-month cap is an upper bound; counters lowering it
may be acceptable when other protections compensate. Current corpus encoding
stands unchanged.
