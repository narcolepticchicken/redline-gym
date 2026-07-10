# T2-N counter-family design v2

Status: implementation design for the machine-drafted v2 family tranche. The family records remain unsigned until the status string says otherwise; this document does not substitute for line-item attorney review.

## 1. Defect and threat model

The first v2 authoring pass defeated slot attackers by making the legal content hollow. All 32 families reused `counter_route_code == reservation_route_code`; every render carried the same synthetic binary surface and near-identical “adjacent route” filler. The validator itself caused the Goodharting: it required identical per-slot class marginals and one identical numeric multiset across every render, then hard-coded the route-match formula. Real negotiated variables—days, percentages, share counts, written consent, carveout scope, and similar conditions—could not satisfy that contract.

The re-authored corpus removes route codes entirely. Every family now states a unique human-readable predicate over at least two rule-grounded inputs. The variables are terms a lawyer could actually trade: for example, NDA return timing interacts with destruction certification and the scope of retained-copy protection; AI training scope interacts with written opt-in; and governance approval percentage interacts with the Major Investor share threshold. Every class still has four fully realized clause renders, but their values are deliberately not forced into an artificial symmetric multiset.

Decoys are also clause-specific. They describe adjacent, non-decisive contract quantities such as destruction-log timing, distribution claim windows, audit-report intervals, or joinder delivery timing. They appear naturally in the clause text and never determine the label. Generation continues to select one static authored render with the episode's seeded `random.Random(seed)` instance; runtime generation does not compose legal prose.

## 2. Pool-level invariants and validator obligations

Every family record declares `predicate.expression`, `render_pools.acceptable`, and `render_pools.unacceptable`. Each class pool has at least four renders. Every render contains nonempty reviewable clause text, a stable decisive-slot set, and exactly two named decoys. The validator preserves the original minimums, render-shape checks, twin coverage, flip-direction declarations, and shared repair requirement, and adds these authoring checks:

1. both class pools exist and meet the minimum size;
2. the decisive and decoy slot sets are stable across renders;
3. each numeric decisive or decoy slot has overlapping acceptable/unacceptable ranges, and each categorical slot has at least one value appearing under both labels, so no single slot perfectly separates the classes;
4. at least one decisive slot-name token is found in the copied rule position, fallback, escalation trigger, or deterministic checks;
5. across the complete 32-family corpus, normalized `predicate.expression` values are unique;
6. the class-level `expected_redline_text` is nonempty and remains a valid repair for every unacceptable draw.

The family-level exemplar fields retained for v4 compatibility describe slot domains, forms, twins, and decoy IDs; generation consumes only a selected realized pool member. Text is never assembled from clause fragments at generation time.

## 3. Empirical self-attack

There is no closed-form 0.5 guarantee in the new design. Such a guarantee was an artifact of manufacturing the same `{0,0,1,1}` surface everywhere and said nothing about construct validity. Resistance is now empirical: the regenerated tranche runs max, min, sum, mean, best single threshold, and one-slot logistic attackers, plus one-level lookup classifiers, permutation MI, and the existing mechanical strategy battery.

The overlap validator is intentionally only a local authoring floor. It rejects a perfectly thresholdable slot but permits realistic near-boundary ranges such as acceptable `[15, 40]` and unacceptable `[35, 90]`. Corpus gates remain necessary because individually overlapping slots can still combine into a tranche-level shortcut. The family-held-out split is additive: each playbook has nonempty, disjoint train and held-out family-ID sets, and evaluation contains the held-out family.

The obsolete corpus fails both new direct regressions: its synthetic decisive names have no token grounded in the selected rule prose, and all 32 records duplicate the same predicate expression. The re-authored corpus passes both checks.

## 4. Verified base inventory and selected rule targets

The inventory below was recomputed directly from `tasks/generated/*/planted_deviations.json` and `tasks/contracts/*/planted_deviations.json`; `tasks/heldout` was not read. Structural eligibility means exactly five deviations, all `redline_with_fallback`, all with nonempty `expected_redline_text`. The selected rule union contains four targets per playbook.

| area / playbook | selected targets | eligible bases | total T2 bases | gap |
|---|---|---|---:|---|
| ai / PB-AI-001 | R-001, R-002, R-009, R-012 | T2-AI-1302, T2-AI-1303 | 2 | corpus caps the area at 2 |
| crypto / PB-CRYPTO-001 | R-002, R-003, R-006, R-008 | T2-CRYPTO-1502, T2-CRYPTO-1503 | 2 | corpus caps the area at 2 |
| privacy / PB-DPA-001 | R-001, R-002, R-003, R-006 | T2-DPA-302, T2-DPA-303, T2-DPA-312 | 3 | none |
| employment / PB-EMP-001 | R-002, R-004, R-006, R-007 | T2-EMP-702, T2-EMP-703, T2-EMP-712 | 3 | none |
| governance / PB-GOV-001 | R-002, R-006, R-007, R-013 | T2-GOV-902, T2-GOV-903, T2-GOV-912 | 3 | none |
| ma / PB-MA-001 | R-001, R-006, R-008, R-011 | T2-MA-1102, T2-MA-1103 | 2 | corpus caps the area at 2; both bases have the identical planted rule set `{R-001,R-006,R-008,R-011,R-012}` |
| contracts / PB-MSA-001 | R-001, R-003, R-006, R-008 | T2-MSA-104, T2-MSA-106, T2-MSA-122 | 3 | none |
| contracts / PB-NDA-001 | R-002, R-007, R-008, R-009 | T2-NDA-112 | 2 NDA bases | T2-NDA-102 is permanently ineligible because R-008 is `escalate` and lacks redline text |

The four MSA targets also cover all three MSA bases with at least two overlaps: 104 has R-001/R-003/R-006, 106 has R-003/R-006/R-008, and 122 has R-003/R-008. NDA-112 has R-002/R-007.

## 5. Playbook grounding decisions

Each family record copies its rule's `position`, `fallback`, `escalation_trigger`, and `deterministic_checks` (when present) into `playbook_grounding`; the copied fields are review evidence, while the playbook remains authoritative and read-only.

- AI: R-001 accepts no training use or identified-file use with written opt-in; R-002 accepts assignment or exclusive use with export in at most 30 days; R-009 requires a legal/objective-safety basis plus at least 15 days' notice; R-012 requires complete portable coverage plus at least 20 transition hours.
- Crypto: R-002 accepts no asset use or a specifically consented written use; R-003 requires both acknowledged Customer ownership and categorical/qualified estate exclusion; R-006 requires controls reporting at least annually and material-failure notice within 72 hours; R-008 grants 100% Customer entitlement absent an exception and permits unsupported treatment only for express decline or legal prohibition with zero Custodian retention. The unacceptable pool never relabels the signed fallback as harmful.
- Privacy: R-001 permits documented instructions or legally required processing with notice within five days; R-002 permits Customer-directed service use or independent use only after irreversible anonymization removes the information from the personal-data perimeter; R-003 permits prior approval or a 30-day notice/objection process with pass-through duties; R-006 uses request-type-specific support boundaries of 10 days for data-subject matters and 15 for regulator matters.
- Employment: R-002 permits immediate treatment of incurable serious events or at least 10 cure days for curable material breaches; R-004 assigns employment-created work and excludes prior inventions only when scheduled; R-006 remains discretionary unless a written objective plan supports a target no greater than 30%; R-007 creates no extra acceleration unless a plan/award document authorizes it.
- Governance: R-002 requires enumeration or a separate signed approval covenant; R-006 permits investor purchase only after Company decline or expiry of the Company-first period; R-007 requires both a customary transferee and a written joinder; R-013 preserves at least majority Series A approval and the 1,000,000-share Major Investor threshold. No family targets R-008, avoiding the earlier reporting-cadence polarity error.
- M&A: R-001 permits a bounded enumerated assumption or an express signed amendment, never an unsigned catch-all; R-006 requires fraud claims to survive outside the liability cap; R-008 requires zero mandatory-offer percentage and no successor-liability admission; R-011 permits closing after no MAE or preserves Buyer's right not to close when one occurs. All copied deterministic checks retain the `unreviewed ... marker` prohibitions.
- MSA: R-001 limits ordinary exposure to no more than 12 months of fees while preserving all high-risk carveouts; R-003 requires full assignment plus a perpetual embedded-material license; R-006 requires no more than 30 days' notice and zero unused-service charge; R-008 preserves both express warranties and core remedies.
- NDA: R-002 requires coverage and party responsibility when an affiliate participates; R-007 requires cooperation plus notice within 24 hours unless law prohibits notice; R-008 makes 30 days unconditionally acceptable and allows 31–45 days only with certified destruction and a narrow protected-copy carveout; R-009 requires at least three years plus an indefinite trade-secret tail. R-008 never uses the banned literal in an acceptable render, and its backup-cycle decoy never collides with the decisive return-day figure in the same render.

All 32 targets are plausible negotiated middle-ground subjects. The v2 status remains explicitly unreviewed because this grounding pass is mechanical/model-authored, not attorney signature.

## 6. Tranche construction and counts

The implementation target is exactly four families for each of the eight playbooks, 32 total. The mixed tranche has four instances in each of the seven file areas (28 mixed total), rotating deterministically across every eligible base; areas capped at two bases receive two seeds per base, three-base areas receive a 2/1/1 rotation, and contracts rotates across its four eligible MSA/NDA bases. Each mixed instance contributes one acceptable and one unacceptable counter, so the macro denominators are 28/28. Three all-concessions instances comply because `9 * 3 = 27 <= 28`; four do not because `36 > 28`.

Families are grouped by rule and selected with the same seeded RNG before choosing two distinct deviations. This avoids the old sorted-first-family bias and permits all authored families to appear across seeds while preserving byte determinism.
