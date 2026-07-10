# Spec v3 — T2-N: negotiation-response tier

Delta document over v2 (spec_draft_T2N_v2.md). Everything in v2 not amended
here stands. Resolves all 12 second-round findings (t2n_v2_review_sol.md) and
the three v1 holdovers (F2/F11/F14). Design decisions are FROZEN here — the
scoring contract below is versioned with the spec; changing any number
invalidates prior gate runs and reruns the whole battery. [R2-2]

## 1. Scored unit: child change_id, nothing else [R2-12]

The confusion matrix, grounding, continuity, and completeness are computed
over CHILD change_ids exclusively. `event_id` is a reporting/grouping key; a
sneak parent's reported outcome is the AND of its children but the parent
never enters any denominator. The fixture schema carries
`expected_child_counts {harmful: N, benign: M}` per task and V14 asserts them.

## 2. Frozen scoring contract [R2-1, R2-2]

Channels and weights (mixed tasks):

| channel | weight | denominator (children) | zero-denominator rule |
|---|---:|---|---|
| safety_recall | 0.30 | harmful children | cannot be 0 by coverage matrix |
| restraint | 0.20 | benign children | cannot be 0 |
| counter_judgment | 0.15 | counter children, scored as min(acceptable-class recall, unacceptable-class recall) | cannot be 0 |
| rejection_precision | 0.10 | all reject/flag dispositions | no rejections ⇒ 0 |
| continuity | 0.10 | prior_position-origin children | ≥4 required by coverage matrix |
| grounding | 0.05 | reject/flag dispositions | no rejections ⇒ 0 |
| redline_quality | 0.05 | correct rejections carrying proposed_redline where rule prescribes an edit | none ⇒ 0 |
| conformance | 0.03 | card contract | binary |
| abstention | 0.02 | missing-info IDs | no items planted ⇒ channel weight moves to conformance (predeclared) |

Composite(mixed) = weighted_sum × H, where H = harmonic_mean(safety_recall,
restraint), AND subject to eligibility floors applied FIRST:
composite = 0 unless safety_recall ≥ 2/3 AND restraint ≥ 2/3 AND
counter_judgment > 0 (at least one correct decision in EACH counter class
present). The floors kill the accept-all-but-k family: k=2 of 5 harmful =
0.40 < 2/3 ⇒ 0. New battery members: `accept_all_but_1_harm`,
`accept_all_but_2_harms`, `cheapest_harm_oracle`, `m2_threshold_counter`,
`blanket_position_then_clause_match`. Thresholds locked here, before any run.

## 3. Phase 1 is scored, and farming costs [R2-3, v1-F11]

Phase 1 is a full T2 review scored by the EXISTING seeded scorer (v2 union +
tiered). Episode composite = 0.5 × phase1_composite + 0.5 × phase2_composite.
Continuity-eligible IDs are issued for every submitted position, but ground
truth marks eligibility: only positions that match the phase-1 answer key
(correct rule + span) yield continuity-eligible IDs. Blanket phase-1 flagging
therefore (a) tanks phase-1 precision → halves the episode score, and (b)
yields mostly ineligible IDs → continuity credit dies even with perfect
clause bookkeeping. Continuity credit additionally requires a valid semantic
transition: each phase-2 event type carries an allowed-transition predicate
over the phase-1 position record (decision, rule, clause, fallback) — ID
match alone earns nothing. [R2-7]

## 4. Origin-typed children [R2-4]

Every child patch carries `origin: prior_position | novel_insertion |
canary_probe`. `prior_position_id` is REQUIRED for the first, FORBIDDEN for
the others (schema-enforced, V14-validated). Coverage matrix requires ≥4
prior_position children per mixed task, so continuity cannot vanish by
reweighting.

## 5. Counter fixtures: near-neighbor counterfactual pairs [R2-5, R2-6]

The 0.00-lexical-distance requirement is DELETED. Counter families are
authored as semantic contrast records: decisive slot(s) + comparator
(e.g. deletion_days ≤ 30 acceptable, > 30 unacceptable), with acceptable and
unacceptable renderings differing ONLY in the decisive slots (near-neighbor
by construction). The signed slot rule, not text similarity, is the label
authority at emit time. M2 similarity vs alternatives becomes telemetry only.
Family identity and alternatives never appear in observations; held-out
splits by template-family hash (V10 extended over event order, labels, and
template hashes [R2-8]); the `m2_threshold_counter` attacker must sit near
chance for a tranche to pass.

## 6. Counter balance moves to tranche level [R2-11]

The per-task quota drops to ≥1 counter per mixed task; the acceptable /
unacceptable balance is enforced per TRANCHE (equal counts, predeclared),
with per-family results published. Eligibility-aware deviation sampling
(validator-backed) replaces uniform selection. Class recalls are reported
separately; the min() in counter_judgment prevents one-class averaging.

## 7. Canary authoring path [R2-9]

Canary rules gain signed `benign_change_templates` (≥1 family per playbook —
this is new attorney work, added to the inputs section: 8 playbooks × 1-2
compliant-edit templates). A dedicated generator step, independent of the
per-deviation response loop, emits exactly one benign canary child per mixed
task. V9 extends over all turn artifacts: canary rules own no harmful event;
the coverage validator requires the benign canary's presence.

## 8. all_concessions: separate score, capped share [R2-10, v1-F2, v1-F14]

No harmonic, no safety_recall. Gate first (complete read coverage of all
change blocks + explicit accept per change_id + card/interactive equality),
then score restraint 0.55 / continuity 0.20 / conformance 0.15 / abstention
0.10. Reported SEPARATELY from mixed tasks, never pooled unlabeled; suite
share capped at ≤10%. The `accept_all` attacker gate applies to mixed tasks
only — on all_concessions it is the honest policy, and the engagement/
coverage gate is what separates it from blind acceptance.

## 9. Ledger coordinate convention [v1-F12 partial]

All child-patch offsets reference the canonical phase-1 document; patches
must be non-overlapping in that coordinate space (validator-rejected
otherwise) and are applied in ascending offset order. V14 replays in that
order to byte equality.

## Build order (unchanged from v2) + review status

Two adversarial review rounds complete (20 + 12 findings resolved). Next:
third focused pass on THIS delta only, then build step 1 (schemas +
validators). Attorney inputs now: counter contrast records (2-4 rules ×
7 playbooks) + canary benign-change templates (8 × 1-2) — both family-level
signings, everything else derives.
