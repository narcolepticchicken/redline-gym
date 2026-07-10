# Third-round focused adversarial red-pen review — T2-N v3 delta

## Section 1 — Closure check

Tally: R2 CLOSED 7, PARTIAL 5, OPEN 0; v1 holdovers CLOSED 2, PARTIAL 1, OPEN 0.

- **R2-1 — PARTIAL.** V3 adds the requested eligibility floors and attackers (§2, lines 33-40), but its own amended minimum task can have only three or four harmful children; catching two of three survives at exactly `2/3` and scores `0.72`, so the original “two cheap catches pass” defect remains at the new discrete task size.
- **R2-2 — PARTIAL.** V3 freezes nine weights, the formula, and most zero-denominator rules (§2, lines 17-40), but `min(acceptable recall, unacceptable recall)` is undefined on a task containing only one counter class, grounding conflicts with v2's correctness-conditioned denominator, and redline quality can be read as conditioning the denominator on submission.
- **R2-3 — PARTIAL.** Phase 1 is now scored and IDs are answer-key-filtered (§3, lines 42-54), but the additive `0.5/0.5` rule pays `0.5` for one perfect phase, the existing seeded scorer fails high on blanket positions, and ID eligibility checks only rule + span rather than the full decision/fallback record.
- **R2-4 — CLOSED.** V3 supplies the three origin types, requires/forbids `prior_position_id` by origin, validates the relation, and requires at least four prior-position children (§4, lines 56-62).
- **R2-5 — CLOSED.** The hard `0.00` lexical-distance ceiling is expressly deleted and signed slot/comparator contrast records become label authority (§5, lines 64-71); the new slot-grep defect below is a v3 defect, not the old M2 exclusion defect.
- **R2-6 — CLOSED.** The old asymmetric `0.00/0.75` M2 label oracle is removed, alternatives/family identity are hidden, family-hash splits are required, and the named M2 attacker is gated (§5, lines 66-75); a different non-M2 slot oracle remains.
- **R2-7 — PARTIAL.** V3 says continuity needs an eligible phase-1 answer-key match and an event-specific transition predicate (§3, lines 46-54), but it neither defines those predicates nor requires decision/fallback correctness at ID-eligibility time.
- **R2-8 — PARTIAL.** V3 extends V10 over event order, labels, and template hashes (§5, lines 72-75) and removes per-task two-class balance (§6, lines 77-83), but exact tranche balance creates a new task-index/quota signal and no random-permutation or conditional-leakage test is specified.
- **R2-9 — CLOSED.** Signed benign canary templates, new attorney inputs, a dedicated emission step, exactly one benign canary child per mixed task, V9 expansion, and a coverage check are all explicit (§7, lines 85-92).
- **R2-10 — CLOSED.** V3 defines a gated, separately weighted all-concessions score, separate reporting, a suite-share cap, and a mixed-only `accept_all` attacker (§8, lines 94-102). The residual construct-validity/rounding risk is bounded and discussed below.
- **R2-11 — CLOSED.** V3 chooses the offered tranche-level remedy: at least one counter per task, equal tranche classes, validator-backed eligibility sampling, family-level reporting, and template-family-hash held-out splits (§5, lines 72-75; §6, lines 77-83).
- **R2-12 — CLOSED.** Child `change_id` is the exclusive denominator unit, parents are reporting-only, sneak reporting is conjunctive without parent reward, and expected child counts are fixture-validated (§1, lines 9-15).
- **v1-F2 — CLOSED.** Mixed-task accept-all is killed by the safety floor (§2, lines 33-40), while all-concessions receives a defined no-safety score, a complete-disposition gate, separate reporting, and a capped share (§8, lines 94-102).
- **v1-F11 — PARTIAL.** V3 now has scored sequential phases and semantic-transition language (§3, lines 42-54), but a phase-only policy can still earn `0.5`, blanket phase-1 work remains cheap under the existing scorer, and the transitions are not executable definitions.
- **v1-F14 — CLOSED.** V3 keeps all-concessions distinct from clean/V13 and supplies change-block coverage, explicit per-ID accepts, exact card/interactive equality, and a dedicated score (§8, lines 94-102).

## Section 2 — Focused adversarial pass on v3

### (a) Frozen weight table and eligibility floors

#### Minimum-coverage derivation

The nine mixed-task weights sum to one:

`0.30 + 0.20 + 0.15 + 0.10 + 0.10 + 0.05 + 0.05 + 0.03 + 0.02 = 1.00`.

Applying v3's child-only rule and one-counter minimum to the v2 coverage rows gives this coverage-only lower bound:

| required event | child truth | origin | children |
|---|---|---|---:|
| concession | benign | `prior_position` | 1 |
| regression | harmful | `prior_position` | 1 |
| sneaky reinsert, source child | benign | `prior_position` | 1 |
| sneaky reinsert, inserted child | harmful | `prior_position` | 1 |
| one counter | acceptable/benign **or** unacceptable/harmful | `prior_position` | 1 |
| new deviation | harmful | `novel_insertion` | 1 |
| dedicated benign canary | benign | `canary_probe` | 1 |

That is **7 children: 5 `prior_position`, 1 `novel_insertion`, 1 `canary_probe`**. The `>=4 prior_position` requirement is already slack. With one acceptable counter the truth counts are harmful/benign `3/4`; with one unacceptable counter they are `4/3`. A task has only the one counter class it drew, so the phrase “each counter class present” means one correct counter decision if absent classes are ignored.

There is a second, implementation-grounded count. Current T2 selects exactly five unique-rule deviations (`generator/generate.py:37,348-366`) and processes every selected deviation (`generator/generate.py:151-179`). Under the per-deviation response design, concession + regression + sneak + one counter consume only four phase-1 deviations after v3 drops the second required counter. V3 never says what response the fifth deviation receives. The cheapest non-sneak replacement adds one prior-position child, producing **8 children: 6 prior, 1 novel, 1 canary**. If that extra child is benign, acceptable/unacceptable-counter tasks have `H/B = 3/5` and `4/4`; if harmful, they have `4/4` and `5/3`. Omitting it yields the 7-child coverage reading but abandons one phase-1 deviation. The scoring contract therefore has no single validator-derivable expected count until v3 specifies this replacement.

#### Finding 1 — The new floors still pass a cheap miss-one-harm policy, and the dropped counter leaves the task size underdefined

**Severity: BLOCKER**

**Failure scenario.** Define `slot_and_shape_floor_oracle`: decide the sole counter with the exposed slot comparator, accept every benign child, and reject only the cheapest `ceil(2H/3)` harmful children (including the counter when it is unacceptable). It deliberately misses one harmful child. Give it exact after-spans, copied prescribed edits, valid clause-matched IDs, a valid card, and the easy abstention decision; those are mechanical bookkeeping, so every channel other than safety is 1.

For safety `s`, `Harmonic(s,1) = 2s/(1+s)` and the weighted sum is `0.30s + 0.70`:

| harmful children `H` | catches | safety `s` | harmonic | weighted sum | composite |
|---:|---:|---:|---:|---:|---:|
| 3 | 2 | `2/3` | `0.800000` | `0.900000` | **`0.720000`** |
| 4 | 3 | `3/4` | `0.857143` | `0.925000` | **`0.792857`** |
| 5 | 4 | `4/5` | `0.888889` | `0.940000` | **`0.835556`** |

Thus, on the 7-child reading, `accept_all_but_1_harm` is floored to zero and a non-adaptive `accept_all_but_2_harms` scores `0.72` on acceptable-counter tasks but zero on unacceptable-counter tasks, for an equal-tranche mean `0.5(0.72) = 0.36`. The adaptive cheapest-harm oracle rejects two or three according to the extracted counter class and averages

`(0.720000 + 0.792857) / 2 = 0.756429`.

A three-catch oracle is even stronger: it is perfect on the `H=3` acceptable-counter task and scores `0.792857` on the `H=4` task, for `(1 + 0.792857)/2 = 0.896429`. Under the 8-child harmful-extra reading, the adaptive miss-one policy averages `(0.792857 + 0.835556)/2 = 0.814206`.

Every miss-one result clears `0.40`. Even the smallest, `0.72`, exceeds `0.60`, which is 60% of a mathematically perfect honest baseline of `1.00`; it therefore also exceeds 60% of any realistic honest baseline. This is stronger than estimating honest at the controlling SPEC's `0.40-0.80` band. The floors implement the proposed fraction but do not implement the intended mechanical gate at the amended discrete counts.

**Fix.** First freeze whether all five phase-1 deviations receive a response and the exact event/origin/truth count rules. Then gate required harmful families separately (regression, sneak insertion, new deviation, and any unacceptable counter), or set a discrete per-fixture safety requirement derived from `expected_child_counts`; an aggregate `2/3` floor cannot stop choosing only cheap harms. Add three- and four-harm omission oracles to the battery and require every one to satisfy both `<0.40` and `<=60% honest` before preserving these weights.

#### Finding 2 — `counter_judgment` is undefined on the one-class tasks v3 newly permits

**Severity: BLOCKER**

**Failure scenario.** Section 2 defines `counter_judgment = min(acceptable-class recall, unacceptable-class recall)` and says its denominator cannot be zero, while §6 permits one counter of only one class. On a task with one acceptable counter correctly accepted, acceptable recall is `1/1`; unacceptable recall is `0/0`. Mapping absent recall to zero produces `min(1,0)=0` and floors every single-class task to zero. Mapping it to one or dropping absent classes produces `1`. Deferring the missing class to tranche aggregation means a task's episode composite cannot be finalized independently. The parenthetical “each class present” explains the eligibility intent but does not define the channel arithmetic.

**Fix.** Define per-task counter accuracy over present counter children and enforce `min(recall_A, recall_U)` only after tranche aggregation, with both tranche denominators guaranteed nonzero. Alternatively define `min` over present classes explicitly and add a separate tranche-level two-class gate. State which value enters the per-episode weighted sum.

### (b) The `0.5/0.5` phase composition

#### Finding 3 — Additive phase composition pays a passing score for doing only one phase, and seeded T2 makes phase-1 blanket farming score above 0.40 by itself

**Severity: BLOCKER**

**Failure scenario.** The direct endpoints are already disqualifying:

- perfect phase 1 / zero phase 2: `0.5(1) + 0.5(0) = 0.5`;
- zero phase 1 / perfect phase 2: `0.5(0) + 0.5(1) = 0.5`.

Both clear the controlling `0.40` honest-band floor. A phase-2-only score of `0.5` is also `0.5/0.8 = 62.5%` of an honest baseline at the top of the controlling band, so it violates the relative gate too. It would be only 50% of a perfect honest baseline, but it still violates the absolute `<0.40` attacker gate.

The “EXISTING seeded scorer” makes the phase-1-only attack concrete. Current T2 has five deviations. A `blanket_position_then_clause_match` attacker files one broad, document-grounded clause position for each of 15 playbook rules; five match. Under `scoring/core.py:14-21,66-86,117-118`, use conservative channels `recall=1`, `precision=5/15=1/3`, `grounding=1`, `fallback=0.5`, `conformance=1`, `abstention=1`. Grounding counts any quote found in the document, even for false findings (`core.py:78-79,308-312`); the tiered matcher awards `0.5` at 60% token containment (`core.py:375-399`); and seeded abstention penalizes no spurious escalations, only missed items (`core.py:433-441`). Its phase-1 score is

`0.35(1) + 0.15(1/3) + 0.15(1) + 0.15(0.5) + 0.10(1) + 0.10(1) = 0.825`.

With phase 2 at zero, the episode is `0.5(0.825) = 0.4125`, already above `0.40`. Those five true blanket positions also satisfy v3's stated ID test of correct rule + span. Combining this failed-high phase 1 with the smallest floor-surviving phase 2 gives `0.5(0.825) + 0.5(0.72) = 0.7725`, more than 60% even of a perfect `1.00` honest score. V3's statement that blanket flagging “tanks phase-1 precision” overstates the cost: precision is only 0.15 of phase 1, hence at most `0.5(0.15)=0.075` of the episode.

**Fix.** Make phase eligibility conjunctive: episode composite is zero unless each phase clears a locked minimum and its phase-specific cheater gates. Compose eligible phases with a harmonic/geometric rule or another rule that is zero when either phase is zero. Do not reuse seeded T2 unchanged for ID issuance: require a complete correct phase-1 position record, and add `phase1_only`, `seeded_blanket`, and `blanket_position_then_clause_match` to the mandatory battery.

### (c) Continuity eligibility and transition predicates

#### Finding 4 — The transition predicate is an assertion, not an executable scoring contract

**Severity: BLOCKER**

**Failure scenario.** Section 3 says every event type “carries an allowed-transition predicate” over `(decision, rule, clause, fallback)`, but supplies no predicate table, truth function, or validator examples. It also defines initial ID eligibility only as correct rule + span, so a position with the wrong decision or fallback can receive an eligible ID even though those fields supposedly control the transition.

For a phase-1 record rejecting a 180-day deletion term under a 30-day fallback:

- a **concession** to 30 days could permit accept because after-text equals fallback, because it satisfies the rule comparator, or merely because the emitted label says benign;
- a **regression** could require only reject + same rule, or also an exact repeat of the stored fallback;
- the two **sneaky_reinsert** children need different transitions—accept the source cleanup and reject the destination insertion—but v3 does not say whether both link to the same record or how clause relocation affects the clause field;
- a **counter_proposal** may depend on the decisive comparator and phase-1-only context guard, but no relation from those values to the stored fallback is defined;
- **new_deviation** and **benign_canary_change** forbid `prior_position_id` by origin, yet “each phase-2 event type” is said to carry a phase-1 transition predicate; whether their predicate is N/A or always false is unstated.

Two conforming implementers can therefore award different continuity on the same transcript. At phase-2 safety/restraint `1`, that changes the phase-2 score by the full continuity weight `0.10` and the episode by `0.5(0.10)=0.05`.

**Fix.** Put a versioned transition table in the spec and fixture schema. For every `(event_type, child_role, origin)` row, define eligible phase-1 decisions, rule equality, source/destination clause relation, fallback/comparator condition, required phase-2 decision, and whether continuity is N/A. Require decision, rule, clause, and fallback correctness—not just rule + span—before an ID becomes eligible, then validate every transition truth value in V14.

### (d) Near-neighbor counterfactual pairs

#### Finding 5 — Slot-only pairs replace the M2 oracle with a simpler regex/comparator oracle that the named battery cannot see

**Severity: BLOCKER**

**Failure scenario.** If acceptable and unacceptable renderings differ only in `deletion_days`, and the signed comparator is `<=30` versus `>30`, an attacker extracts the number and applies the threshold. Across 14 one-counter tasks with seven of each class, it scores acceptable recall `7/7=1`, unacceptable recall `7/7=1`, and `counter_judgment=min(1,1)=1` without interpreting the obligation.

The `m2_threshold_counter` requirement does not bind this attacker. For “delete ... within 30 days” versus “delete ... within 180 days,” ten of eleven ordered tokens can remain identical: `10/11 = 0.909 > 0.80`. With no counter key-slot list, `_tiered_redline_match` returns the same `0.75` span tier for both (`core.py:385-399`), so a pure M2 threshold can remain at `7/14=0.50` while the numeric extractor is `14/14=1.00`. Even with a key slot, the wrong number can fall through to `0.50` containment because `10/11 > 0.60`; a regex still directly applies the comparator. Template-family hashing does not hide common numbers, units, or comparator ranges.

**Fix.** Add `slot_extractor_counter`, unit-normalization, date-arithmetic, and common-threshold attackers, and require each to remain near chance. Counter families must vary more than a naked decisive scalar: include decoy quantities, paraphrased units, multi-slot/context interactions, and qualitative exceptions; split held-out data by comparator/rule family as well as template hash. Keep signed slots as ground truth, but do not make the slot's surface location and comparator a public lookup table.

### (e) Tranche-level counter balance

#### Finding 6 — Exact tranche balance permits task-index and quota-constrained leakage unless ordering and batch access are specified

**Severity: DESIGN-RISK**

**Failure scenario.** A 14-task tranche with one counter per task must contain exactly seven acceptable and seven unacceptable counters. A generator that fills seven acceptable records followed by seven unacceptable records passes equal-count balance and has nonconstant labels; an alternating `A,U,A,U,...` sequence does too. If stable task index is visible, a position/parity attacker gets `14/14=1` rather than the `7/14=0.5` marginal baseline. “V10 extended over ... labels” does not state a statistic that rejects either conditional pattern. Even with random order, a batch attacker can rank weak heuristic scores and force exactly seven accepts, exploiting the known without-replacement quota; the named M2 attack is per-counter and does not test that transductive policy.

Dropping per-task balance removes the old “the other one must have the opposite label” leak, but moves the same exact-count side information to a larger unit. It is safe only if episodes are isolated, tranche membership/order are hidden, emission uses an independently randomized permutation, and validation tests conditional—not merely marginal—leakage.

**Fix.** Specify independent label assignment followed by a secret seeded permutation, hide tranche position/membership from observations, and forbid cross-episode state during scoring. Extend V10 to test label mutual information with task index, event order, family hash, and generator seed across multiple tranches. Add a tranche-aware quota-constrained attacker; if exact balance is not needed for reward, use stratified reporting over independently sampled tasks instead.

### (f) `all_concessions` scoring

The weights are normalized exactly: `0.55 + 0.20 + 0.15 + 0.10 = 1.00`.

The suite-mean blocker is substantially closed. If `A/(A+M) <= 0.10`, a universal accept-all policy scoring `1` on all-concessions and `0` on mixed contributes at most `0.10`, not enough to reach `0.40`; if the types are never numerically pooled, there is no subsidy at all.

#### Finding 7 — The cap bounds subsidy, but the gate proves protocol enumeration rather than legal engagement and the share arithmetic is not locked

**Severity: DESIGN-RISK**

**Failure scenario.** A stateful script can read exactly every advertised change-block range, loop over all `change_id`s, submit accept for each, and mirror the map into the card. With clause-matched phase-1 IDs it receives `0.55 + 0.20 + 0.15 + 0.10 = 1.00` without deciding whether any text is compliant. That is indistinguishable from honest behavior on an all-benign answer key. This no longer lets the script pass mixed tasks, but the separately reported `1.00` should not be described as evidence of substantive negotiation judgment.

“Suite share capped at <=10%” also needs an integer formula. With 14 mixed held-out tasks, `ceil(0.10 * 14)=2` all-concessions tasks would actually be `2/(14+2)=12.5%`, yielding a `0.125` subsidy if pooled. The wording “never pooled unlabeled” still permits a labeled top-line pool, so the aggregation path is not quite closed as executable math.

**Fix.** Define the cap as `A/(A+M) <= 0.10` after integer selection, never round upward, and state whether any top-line arithmetic mean exists; preferably publish task-type means only. Describe all-concessions as a state/coverage/conformance diagnostic, not semantic-judgment evidence. Retain its separate label and do not use its score to rescue a failed mixed-task gate.

### (g) Internal contradictions and denominator defects

Several apparent conflicts are clean amendments, not findings. Section 6's word “drops” expressly overrides v2's one-acceptable-and-one-unacceptable per-task quota; §7's exactly-one-per-task canary strengthens v2's per-tranche minimum; and §2's frozen formula replaces v2's placeholder weights. The v2 and v3 channel sets are the same nine channels—none was silently added or removed—and the mixed weights sum to `1.00`.

The unresolved fifth response after dropping the second counter is already part of Finding 1, and the absent counter-class denominator is Finding 2. Two further new denominator wordings conflict with, or fail to close, unamended v2 semantics.

#### Finding 8 — The new grounding denominator conflicts with v2's correctness-conditioned auxiliary credit

**Severity: DESIGN-RISK**

**Failure scenario.** V2 says grounding is “ONLY for correctly-disposed events” (v2 lines 87-89). V3's frozen table says its denominator is all reject/flag dispositions (§2, line 28). For four grounded rejections of which two are correct, v2-style correctness conditioning gives `2/2=1`; an all-rejection denominator with a correct-and-grounded numerator gives `2/4=0.5`; a literal text-grounded numerator gives `4/4=1` and awards grounding to wrong decisions. The first two interpretations differ by `0.05(1-0.5)=0.025` in phase 2 when the harmonic multiplier is one, or `0.0125` at episode level. All are plausible from the combined text.

**Fix.** Freeze an explicit numerator and denominator. For example, `grounding = count(correct rejection AND exact designated after-span) / count(all rejection dispositions)`, explicitly superseding v2; or retain v2 by dividing over correct rejections and state the zero rule. Do not leave correctness conditioning implicit.

#### Finding 9 — Redline quality can be maximized by submitting exactly one easy edit

**Severity: DESIGN-RISK**

**Failure scenario.** V3 describes the denominator as “correct rejections carrying `proposed_redline` where rule prescribes an edit” (§2, line 29). With four correct edit-prescribed rejections, an attacker can attach one exact edit and omit three. Conditioning the denominator on “carrying” an edit gives `redline_quality=1/1=1`; treating missing required edits as zero gives `1/4=0.25`. The selective-submission reading buys `(1-0.25)(0.05)=0.0375` phase-2 composite at harmonic one (`0.01875` at episode level). The special “none => 0” rule makes exactly-one submission the dominant gaming choice.

**Fix.** Define the denominator as every correctly rejected child whose rule prescribes an edit, whether or not the agent supplied one; a missing or empty `proposed_redline` contributes zero. Validate the denominator against answer-key-required edit IDs, not submitted fields.

## Verdict

**RETHINK**

V3 closes most structural round-two items, but its newly frozen reward contract does not pass its own legitimacy standard: the minimum-task floors pay `0.72-0.836` to a policy that intentionally misses a harmful child, one perfect phase pays `0.5`, the existing phase-1 scorer lets a blanket phase alone reach `0.4125`, and the new slot-only counters admit a non-M2 perfect grep oracle. The scoring unit can be built, but the frozen numbers, phase composition, counter channel, and transition predicates should be revised and red-penned again before implementation.
