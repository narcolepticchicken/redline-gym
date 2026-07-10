# Second-round adversarial red-pen review — T2-N negotiation-response tier v2

## Section 1 — Closure check

Closed: 13, Partial: 6, Open: 1

F1 [BLOCKER] — CLOSED — emitted expected dispositions, harmful/benign event matrices, correctness-conditioned auxiliary credit, and the joint gate make literal reject-all score zero through `restraint = 0` (v2:44-55, 76-100).

F2 [BLOCKER] — PARTIAL — accept-all is zeroed on mixed tasks and every all-concessions change requires an explicit accept, but v2 never defines `safety_recall` or the joint gate when an all-concessions task has zero harmful events (v2:96-105).

F3 [BLOCKER] — CLOSED — phase-2 negatives are matched by event/change ID and can ground only to the designated canonical after-span, while the prior-location replayer is an explicit pre-spend attacker (v2:87-92, 117-121).

F4 [BLOCKER] — CLOSED — counters can be emitted only from signed acceptable/unacceptable families, every mixed task has one of each, and `always_reject_counter` is gated (v2:50-55, 109-120).

F5 [DESIGN-RISK] — CLOSED — grounding is conditioned on correct disposition at a canonical pointer and missing-info decisions use opaque IDs with precision/recall rather than topic-word substring hits (v2:87-94).

F6 [BLOCKER] — CLOSED — the signed emitted label, not M2 similarity, grades counter decisions; M2 remains only a fixture filter and an agent-redline quality measure (v2:50-55, 90-92).

F7 [BLOCKER] — CLOSED — attorney-signed, slot-renderable acceptable and unacceptable template families now author the counter text and its truth label before emission (v2:50-55, 123-128).

F8 [BLOCKER] — CLOSED — every changed child has one `review_change` route, regressions need one rejection, sneaks have accept/reject children with conjunctive parent credit, and new deviations are tracked changes (v2:44-74).

F9 [BLOCKER] — CLOSED — canonical `change_id` maps replace quote-keyed union semantics; identical repeats collapse and conflicts become both conformance failures and wrong dispositions (v2:65-74).

F10 [BLOCKER] — CLOSED — v2 requires the action schema, `reviews_by_change_id`, substantive-review bounce behavior, closed card entries, interactive/card equality, and scorer consumption of the canonical event map (v2:63-74).

F11 [BLOCKER] — OPEN — two phases and opaque IDs exist, but unscored/vacuous phase-1 positions can farm IDs and v2 checks only ID linkage, so a static phase-2 reviewer can still avoid making a meaningful prior decision (v2:17-28, 76-100).

F12 [BLOCKER] — PARTIAL — typed patches, stable IDs, preconditions, a ledger, and two-child sneaks are structural progress, but v2 omits the required non-overlap rule and a precise coordinate/update convention for ordered edits whose offsets all reference the phase-1 document (v2:30-40, 132-135).

F13 [BLOCKER] — CLOSED — schemas and executable V14 precede generator work, and V14 must replay the ledger to byte equality plus prove rendered-block/child/parent cardinality (v2:30-40, 130-139).

F14 [BLOCKER] — PARTIAL — the distinct task type, explicit accepts, event-level reading, exact card equality, and substantive reviews close the empty-card exploit, but the zero-harmful denominator and task-type aggregation rule remain undefined (v2:96-105).

F15 [BLOCKER] — PARTIAL — v2 requires a benign canary event and an all-artifact V9, but neither the current per-deviation generator loop nor the stated attorney-input schema supplies the signed compliant canary edit template or its separate emission path (v2:58-61, 123-139).

F16 [BLOCKER] — CLOSED — the proposal is explicitly renamed T2-N, T3 retains its multi-document/cross-document contract, and reports are forbidden from conflating them (v2:3-9, 141-146).

F17 [BLOCKER] — CLOSED — all seven requested mechanical attackers now have both absolute `<0.40` and relative `<=60% of honest` gates before honest spend, with per-event matrices (v2:115-121).

F18 [DESIGN-RISK] — PARTIAL — fixed event quotas, at least two held-out tasks per area, base-scenario grouping, and within-group averaging replace random weights, but turn-event label/order leakage, family reuse, and confidence-interval requirements are not controlled (v2:107-113).

F19 [DESIGN-RISK] — PARTIAL — expected accept/reject dispositions, conflict penalties, an authored trace, and at least one phase-1-only context slot are present, but context guards remain optional and mixed-task conformance does not require completeness against the canonical change set or counterfactual context cohorts (v2:17-28, 44-74, 123-128).

F20 [NIT] — CLOSED — the non-goals now expressly disclaim `.docx`, live counterparties, judge reward, Word surgicalness, and open-ended deal closing (v2:141-146).

## Section 2 — Fresh adversarial pass on v2 mechanisms

### (a) The harmonic-mean joint gate

#### 1. The gate has no minimum harmful-catch floor; two cheap catches can look like a passing review

**Labels:** (a), scoring, gameability  
**Severity:** **BLOCKER**

**Failure scenario:** Use the requested 10-disposition mix with six harmful and four benign events. The attacker accepts all ten except for `k` obvious harmful events, rejects those with exact after-spans and exact prescribed redlines, and uses farmed valid prior IDs. Until it chooses the unacceptable counter, its channels are `safety_recall = k/6`, `restraint = 1`, `rejection_precision = 1`, `counter_judgment = 0.5`, and continuity/grounding/redline-quality/conformance/abstention all equal 1. Because v2 does not supply weights, the table uses equal weights over its nine named channels solely to expose the gate's scale:

| harmful catches `k` | safety | restraint | harmonic gate | base weighted sum | composite |
|---:|---:|---:|---:|---:|---:|
| 1/6 | 0.1667 | 1.0000 | 0.2857 | 0.8519 | 0.2434 |
| 2/6 | 0.3333 | 1.0000 | 0.5000 | 0.8704 | 0.4352 |
| 3/6 | 0.5000 | 1.0000 | 0.6667 | 0.8889 | 0.5926 |
| 4/6 | 0.6667 | 1.0000 | 0.8000 | 0.9074 | 0.7259 |

If the single cheap catch is the unacceptable counter, `counter_judgment` rises to 1 and the one-catch composite is 0.2593. More importantly, two non-counter catches already produce 0.4352, above the controlling SPEC's 0.40 honest-band floor, and three produce a superficially respectable 0.5926 while missing half the harmful events. A genuinely careful reviewer that catches five of six harmful events gets a gate of 0.9091; the gate therefore supplies no structural boundary between “caught one-third” and “nearly complete.”

The exact-zero cliff is not independently exploitable at arbitrary scale: if both inputs are 0.01, `H = 0.01` and the composite is at most 0.01; if safety is 0.01 and restraint is 1, `H = 0.0198`. The actual cliff is discrete and task-sized: on a six-harm task the first catch jumps the multiplier from 0 to 0.2857 and the second to 0.5. Nothing zeroes a reviewer below a minimum harmful-catch rate.

**Fix:** Add a conjunctive eligibility gate before the harmonic multiplier, such as `safety_recall >= 0.67`, `restraint >= 0.67`, and separate acceptable/unacceptable-counter recall floors; below any floor the mixed-task composite is zero. Add `accept_all_but_1_harm`, `accept_all_but_2_harms`, and a cheapest-harm oracle to the mechanical battery, and set thresholds before looking at their scores.

#### 2. The composite is not an implementable number, and weight selection is circular with the mechanical gate

**Labels:** (a), scoring contract, build order  
**Severity:** **BLOCKER**

**Failure scenario:** V2 names nine channels but supplies no weights, no N/A reweighting algorithm, no grounding denominator when accepts need no quote, and no redline-quality denominator when there is no correct rejection. The same two-catch vector above fails or passes the mandatory 0.40 mechanical threshold depending on an equally permissible weight proposal. If `w_safety = 0.35`, `w_counter = 0.15`, and the remaining 0.50 is on its perfect channels, the base is `0.35(1/3) + 0.15(0.5) + 0.50 = 0.6917` and the composite is `0.3458`. If those two weights are 0.05 each and the other perfect channels receive 0.90, the base is `0.05(1/3) + 0.05(0.5) + 0.90 = 0.9417` and the composite is `0.4708`.

Lines 117-121 require attackers to score `<0.40 composite` before honest spend, while lines 96-100 defer weights until after pilot mechanical numbers exist. There is no composite with which to run that pilot, and an implementer can tune the weights after seeing the attackers until the gate passes.

**Fix:** Freeze a complete weight table, every denominator/zero-denominator rule, task-type aggregation, and the pass/fail thresholds before running the legitimacy battery. Version and hash that scoring contract; weight changes require rerunning all attackers and invalidate prior gate numbers.

### (b) The two-phase episode

#### 3. Phase 1 is unscored, so blanket-position farming is free and can tie an honest reviewer

**Labels:** (b), phase-1 incentives, state tracking  
**Severity:** **BLOCKER**

**Failure scenario:** Current T2 generation plants exactly five deviations (`DEVIATION_COUNT["T2"] = 5` in `generator/generate.py`), while a playbook exposes 12-15 rules. In phase 1 an attacker submits a generic “flag/escalate” position for every plausible rule/clause pair—five IDs if it limits itself to the visible deviations, or 12-15 if it blankets the playbook—and records the returned `(clause, position_id)` map. V2's scoring section contains only phase-2 event metrics; it assigns no false-position cost, phase-1 recall/precision, completeness target, position-quality check, or cap on issued IDs.

The attacker then performs a static current-text review in phase 2, attaches its farmed IDs, and copies the one phase-1-only context slot. If its phase-2 dispositions are correct, all nine listed channels are 1, the harmonic gate is 1, and the composite is 1 under every normalized weight table—the same result as an honest phase-1 reviewer even though every phase-1 position was semantically vacuous. If phase 1 was intended to retain today's T2 score, v2 still never states whether that score is averaged, multiplied, gated, or ignored when producing the one episode composite.

**Fix:** Specify a phase-1 position action/card schema and score it against the seeded T2 answer key. Issue continuity-eligible IDs only for complete, non-conflicting phase-1 positions; penalize extra/false positions; and define one locked composition rule, for example a minimum phase-1 eligibility gate followed by a separately weighted phase-2 score. A vacuous “flag everything” phase 1 must score zero or make its IDs ineligible.

#### 4. The universal `prior_position_id` requirement is impossible for genuinely new and canary changes

**Labels:** (b), action contract, generator feasibility  
**Severity:** **BLOCKER**

**Failure scenario:** The minimum coverage task has seven parent events but eight child `change_id`s: one concession, one regression, two sneak children, one new deviation, two counters, and one benign canary change. At most six children naturally descend from the five seeded T2 positions: concession, regression, both sneak children linked to the sneak's source position, and the two counters. A `new_deviation` has no phase-1 position by definition, and today's T2 action space creates no positive position for the compliant clause later changed by the canary.

V2 nevertheless says every `review_change` requires `prior_position_id` (lines 23 and 65-67), then defines continuity over “dispositions requiring one” (line 86) without identifying an exempt subset. Literal enforcement caps an honest review at `6/8 = 0.75` continuity or forces it to cite two unrelated IDs; exemption makes the action schema false and gives two implementers different denominators.

**Fix:** Add a typed origin to every child patch: `prior_position`, `novel_insertion`, or `canary_probe`. Require and score `prior_position_id` only for the first type, make it forbidden for the others, and validate the relation in V14. Predeclare a minimum count of genuinely prior-dependent events so continuity cannot disappear through N/A reweighting.

### (c) The emit-time separability gate for counters

#### 5. A hard 0.00 ceiling filters out the subtle bad counters the tier most needs

**Labels:** (c), fixture validity, realism coverage  
**Severity:** **DESIGN-RISK**

**Failure scenario:** Current `_tiered_redline_match` tokenizes every alphanumeric word, gives 0.75 at ordered LCS `>=80%` when key slots pass, and otherwise gives 0.50 when at least 60% of the expected alternative's unique tokens occur anywhere in the proposal (`scoring/core.py:375-420`). Consider the signed acceptable alternative:

> Provider shall delete all Customer Data within thirty days after termination.

It has 11 tokens. The realistic but unacceptable counter “Provider shall delete all Customer Data within one hundred eighty days after termination” preserves 10 of 11 expected tokens. With no key-slot list—v2 defines none for counter alternatives—its ordered score is `10/11 = 0.909`, so M2 returns 0.75. Even if `thirty` is made a required key slot and defeats the 0.75 tier, containment is still `10/11 = 0.909`, so M2 returns 0.50. The mandatory 0.00 gate rejects the fixture in either case. A 36-month liability cap substituted for a 12-month cap similarly preserves 21 of 22 ordered tokens (`95.5%`) and is rejected despite being exactly the close, plausible negotiation miss the benchmark should test.

Zero is achievable, but it selects obvious rewrites. “After termination, archival copies may be retained indefinitely for business purposes” shares only `after` and `termination` with the 11-token deletion alternative (`2/11 = 18.2%`) and gets 0.00. Thus acceptable counters may stay richly clause-like at >=0.75, while unacceptable counters are pressured toward conspicuously different, easy language. The result is a coverage/realism hole, not a direct reward mislabel: signed labels still protect correctness, but subtle unacceptable counters cannot enter the distribution.

**Fix:** Do not require lexical distance from an acceptable alternative. Validate both labels with attorney-signed semantic contrast records that identify the decisive slots (for example, `deletion_days <= 30` versus `>30`) and render near-neighbor counterfactual pairs differing only in those slots. Keep M2 as diagnostic telemetry; if retained as a gate, use it to require high surface similarity for paired acceptable/unacceptable fixtures rather than to exclude it.

#### 6. The asymmetric gate manufactures a lexical correctness oracle

**Labels:** (c), gameability, distribution leakage  
**Severity:** **BLOCKER**

**Failure scenario:** Every emitted acceptable counter is guaranteed to have maximum M2 similarity at least 0.75, and every unacceptable counter is guaranteed to have similarity exactly 0.00; the entire 0.50 band is absent. An agent that can see the alternatives can run the public matcher and decide `>=0.75 => accept`, `0 => reject`, earning `counter_judgment = 2/2 = 1` on every minimum-coverage task without interpreting the obligation. If alternatives are hidden, the 2-4 reusable families per playbook still let a trained agent learn the same surface partition; the gate has deliberately made label and lexical style perfectly correlated.

By comparison, always rejecting the two counters earns 0.5, while the similarity shortcut earns 1. If the agent handles the other fixed-shape events correctly, the shortcut produces all channels 1 and composite 1. This is not incidental leakage from a weak generator; it is an invariant enforced by fixture validation.

**Fix:** Admit lexically overlapping acceptable and unacceptable near-neighbor pairs, hide template/family identity and signed alternatives from observations, split held-out data by template family, and add an `m2_threshold_counter` attacker. Counter legitimacy should require that this attacker remain near chance while a semantic reviewer exceeds it.

### (d) The continuity channel and `prior_position_id`

#### 7. Random ID guessing is weak, but clause-key matching buys full continuity without prior-decision continuity

**Labels:** (d), continuity construct validity, gameability  
**Severity:** **BLOCKER**

**Failure scenario:** A normal current T2 phase 1 exposes about five true positions. With five opaque IDs, independent random guessing gives expected continuity `1/5 = 0.20`; for six prior-dependent child dispositions, the chance of guessing all six is `(1/5)^6 = 0.000064`, or 0.0064%. With ten IDs those figures are 0.10 and `10^-6`. “Always use the most recent ID” is no better without an ordering correlation. Random brute force is therefore not the serious attack.

The serious attack is deterministic clause matching. The phase-2 patch exposes section, text, and `change_id`; the farmer from Finding 3 retained each returned ID next to the phase-1 clause/rule. It can cite the clause-matched ID on all six dependent changes for `continuity = 6/6 = 1`, even though every stored prior decision said the same vacuous “flag/escalate.” This demonstrates cross-turn referential bookkeeping, but not consistency with the substance of the agent's own prior decision. Opaque IDs prevent phase-2-only fabrication; they do not make the linked position meaningful.

**Fix:** Store a canonical semantic phase-1 position record behind each ID—decision, rule, clause, reservation slot, and any proposed fallback—and define allowed transition predicates for each phase-2 event. Continuity credit requires both a correct phase-1 record and a semantically valid transition, not merely the ID whose clause matches. Add a `blanket_position_then_clause_match` attacker distinct from `turn2_only`.

### (e) Coverage matrix, benign canary, and all-concessions mechanisms

#### 8. Exactly two balanced counters create a coarse, order-leaking task signature

**Labels:** (e), coverage matrix, counter gameability  
**Severity:** **DESIGN-RISK**

**Failure scenario:** Once the agent recognizes the two `counter_proposal` events, it knows exactly one is acceptable and one unacceptable. A fixed “accept the first, reject the second” strategy scores 1 if generator order is stable and 0 if it is reversed; v2 contains no turn-event analogue of V10 that randomizes or tests label/order leakage. If order is independently randomized, the strategy's expected counter accuracy is still 0.5. Across the minimum 14 held-out tasks (two for each of seven practice areas), it has a `3473/16384 = 21.2%` chance to guess both labels correctly on at least 9 tasks and report counter accuracy at least `9/14 = 0.643` purely by task-level coin flips.

Always rejecting is deterministically less variable but still scores 0.5 on counters. On the stipulated six-harm/four-benign mix, if it is correct on all non-counter events, its channels are safety 1, restraint `3/4 = 0.75`, rejection precision `6/7 = 0.857`, counter judgment 0.5, and the other five channels 1. The harmonic gate is `2(1)(0.75)/(1+0.75) = 0.857`; under equal nine-channel weights the base is 0.9008 and the composite is 0.7721. The mandatory `always_reject_counter` battery will detect this, but v2 gives the implementer no score rule capable of making it pass `<0.40` without post-hoc weight tuning.

**Fix:** Randomize and validate event order, extend V10 over phase-2 event types/template hashes/labels, increase counter counts, and score acceptable-counter recall and unacceptable-counter recall separately with `min(class recalls)` as a gate. Lock the counter-class gate before mechanical runs; one correct class and one zero class must not be averaged to 0.5 credit.

#### 9. `benign_canary_change` has no authored source or independent generation path

**Labels:** (e), canary generation, validator feasibility  
**Severity:** **BLOCKER**

**Failure scenario:** The current generator selects five non-canary T2 recipes, applies one `replace` per selected deviation, and logs only those deviations. Current V9 checks that each of the eight playbooks' two canary rules owns zero planted deviations; it creates nothing. The current playbook schema gives a canary only `position`, `fallback`, severity, and escalation text, and the sampled canary fallbacks are “No change” statements—not slot-renderable compliant edits.

V2 requires one benign canary change in every mixed task but says the only new attorney work is 2-4 counter families per playbook. Continuing the per-planted-deviation response loop yields zero canary changes while V9 passes. Enforcing the coverage row without another source makes every task fail emission. Across the present eight playbooks, satisfying the new claim needs at least eight signed canary edit families (one per playbook), or sixteen if each canary must be exercisable; that work and schema do not exist in v2.

**Fix:** Add signed `benign_change_templates` to canary-rule schema and attorney inputs. Add an explicit generator step independent of planted deviations that chooses and emits one as an expected-accept patch, then make the coverage validator require its existence and V9 prove both its benign label and the absence of harmful canary events. Honeypot scanning must cover the canonical interactive and card maps.

#### 10. `all_concessions` is both mathematically undefined and a suite-level blanket-accept subsidy

**Labels:** (e), all-concessions, aggregation  
**Severity:** **BLOCKER**

**Failure scenario:** A perfect all-concessions review has `harmful = 0`, so `safety_recall = 0/0`. If an implementation follows the current scorer's denominator guard style and makes it 0, v2's joint gate makes the perfect explicit-accept review score 0. If it grants N/A/vacuous safety as 1, restraint and every covered channel can be 1, so the exact same accept-all policy scores 1. V2 defines neither branch nor a task-specific weight table.

Aggregation makes the second branch exploitable. If all-concessions tasks are a fraction `p` of a pooled benchmark, literal accept-all scores 1 on that subset and 0 on mixed tasks, for suite mean `p`. At `p = 0.40` it clears the controlling 0.40 honest-band floor without reading any task; at `p = 0.20` it still receives a 0.20 subsidy. The battery's universal “accept_all <0.40” is incompatible with its being the correct all-concessions policy unless the mix is capped, but v2 supplies no mix or separate-report rule. The controlling SPEC already says clean and seeded composites are never averaged without a task-type label; v2 omits the analogous protection.

**Fix:** Define a separate all-concessions score with no safety harmonic: gate first on complete read/decision/card equality, then score restraint, continuity, conformance, and abstention under a locked table. Report it separately from mixed tasks, predeclare and cap its suite share, and apply the `accept_all` cheater gate only to mixed tasks; on all-concessions it is an honest-task baseline, not an attacker.

#### 11. The per-task counter quota forces reuse of a tiny eligible-rule pool

**Labels:** (e), coverage feasibility, memorization  
**Severity:** **DESIGN-RISK**

**Failure scenario:** Each current T2 task selects five unique-rule deviations, but v2 adds counter families to only 2-4 of 12-15 rules and requires two counter events in every mixed task. Under a simple five-of-`R` sample, the probability of selecting both eligible rules is only `C(13,3)/C(15,5) = 286/3003 = 9.52%` when `E=2,R=15`, or `C(10,3)/C(12,5) = 120/792 = 15.15%` when `E=2,R=12`. Even with four eligible rules, the probability of at least two is only 40.66% for `R=15` and 57.58% for `R=12`. The actual selector is mechanism-stratified rather than uniform, but it has no counter-eligibility constraint at all.

A new constrained sampler can make emission feasible, but with exactly two eligible rules it must select the same two on 100% of mixed tasks. With four, there are only six possible rule pairs and each rule appears in roughly half the tasks under balance. The required one-acceptable/one-unacceptable fixtures therefore concentrate on 2-4 reusable families per practice area, making counter judgment memorizable across the pool rather than a general negotiation skill; the 0.00/0.75 lexical partition worsens that signal.

**Fix:** Add a validator-backed eligibility matrix to phase-1 selection and either expand signed counter families enough to split template families—not merely base scenarios—between train and held-out, or move counter balance to tranche-level macro aggregation instead of forcing two into every task. Publish per-family results and fail any split that shares normalized template hashes across train and held-out.

### (f) Additional new defect — scoring-unit ambiguity

#### 12. Parent events and child changes produce incompatible denominators

**Labels:** new (f), event model, scorer determinism  
**Severity:** **BLOCKER**

**Failure scenario:** V2 says the confusion matrix is over event IDs, says expected dispositions are emitted per child patch, and says a sneak parent receives credit only when both children are correct. Those are three different scoring units. The coverage minimum has seven parents but eight child dispositions: four harmful children (regression, sneak insertion, new deviation, unacceptable counter) and four benign children (concession, sneak source acceptance, acceptable counter, canary). If the parent is also scored, there are nine units and the mixed-disposition sneak has no single harmful/benign label.

The requested first-review mix exposes the same defect. Four concessions, two regressions, one sneak, one new deviation, and two counters are ten parent events, but v2's child taxonomy yields 11 dispositions: harmful `2 + 1 + 1 + 1 = 5` and benign `4 + 1 + 1 = 6`, not a derivable six/four split. The calculations in Finding 1 used the prompt's stipulated six/four denominator, but an implementer following v2 can legitimately produce 5/6, 4/4 for the minimum coverage shape, or a parent-level count. Safety, restraint, precision, grounding, continuity, and the harmonic multiplier then all change.

**Fix:** Make child `change_id` the sole scored unit for confusion, grounding, continuity, and completeness. Treat `event_id` as a reporting/grouping key; for a composite sneak, derive one reporting outcome by AND-ing its child correctness but never add the parent to any reward denominator. Put exact expected harmful/benign child counts and denominator assertions in the fixture schema and V14.

## Verdict

**RETHINK**

V2 genuinely closes 13 first-round findings, especially the ledger, exclusive action map, signed truth labels, and tier naming, but F11 remains open and F2/F14 remain unscorable at the zero-harmful boundary. The worst new blockers are the unfrozen composite and weak harmonic threshold, free phase-1 ID farming, impossible prior links for novel patches, lexical label oracle, missing canary authoring path, and parent/child denominator ambiguity. Those are core reward/state/generation contracts, so implementation should not begin until they are redesigned and mechanically specified.
