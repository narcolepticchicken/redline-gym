# 1. THE FROZEN CONTRACT

This document supersedes only the arithmetic and executable-rule portions of T2-N v3. The v2/v3 architecture named in the prompt remains frozen. `change_id` is the only reward unit; `event_id` is reporting-only. Every truth field below is written by the response generator while it writes the patch ledger. Nothing is inferred from prose by the scorer. This contract is `t2n-reward-v4`; changing any constant, denominator, gate, or table row changes the contract hash and voids prior gate runs.

## 1.1 Artifact and action prerequisites

For each child the answer key MUST contain

`{change_id,event_id,event_type,child_role,origin,expected_disposition,expected_rule_id,expected_clause_id,ground_span,edit_required,expected_redline_text?,prior_source_deviation_id?,counter_family_id?,counter_class?,transition_row_id}`.

For every `prior_position` child it also contains the plant-time expected phase-1 tuple

`P*=(source_deviation_id, phase1_decision, rule_id, clause_id, fallback_text, comparator_record_id?)`.

The agent submits exactly one final phase-2 record per advertised `change_id`. Omission, an unknown ID, a conflicting duplicate, or disagreement between the interactive map and card makes conformance zero. Identical duplicates collapse and never enlarge a denominator. A changed child can be handled only by `review_change`; `flag_issue` remains confined to a separately keyed unchanged-text issue and cannot score a child.

An issued `position_id` is continuity-eligible only when its stored phase-1 record equals `P*` in every applicable field: source deviation, decision, rule, clause, normalized fallback, and comparator/context record. A right rule/span paired with a wrong decision or fallback is ineligible. This requires new T2-N schemas, V14 rules, response engine, and scorer code; current `core.py` cannot compute it. The existing T2 phase-1 scalar is reused, including its known weaknesses, but not its quote-keyed map for continuity.

## 1.2 Phase 2 channels

Let `C` be all expected child IDs, `H={c: expected_disposition(c)=reject}`, `B={c: expected_disposition(c)=accept}`, `R={c: agent_disposition(c)=reject}`, `K` be counter children, and `P` be `prior_position` children. A missing or structurally invalid record is an incorrect disposition. Indicator brackets are 1 when their contents are true and 0 otherwise.

| channel | weight | exact equation | zero rule |
|---|---:|---|---|
| safety `S` | 0.30 | `sum[c in H][agent(c)=reject]/|H|` | mixed coverage requires `|H|>0`; otherwise invalid fixture |
| restraint `T` | 0.20 | `sum[c in B][agent(c)=accept]/|B|` | mixed coverage requires `|B|>0`; otherwise invalid fixture |
| per-task counter accuracy `J` | 0.15 | `sum[c in K][agent(c)=expected(c)]/|K|` | mixed coverage requires `|K|>=1`; otherwise invalid fixture |
| rejection precision `Q` | 0.10 | `sum[c in R][c in H]/|R|` | `R=empty => 0` |
| continuity `L` | 0.10 | `sum[c in P][eligible(agent_prior_id(c)) AND transition_row(c) passes]/|P|` | mixed coverage requires `|P|>=6`; otherwise invalid fixture |
| grounding `G` | 0.05 | `sum[c in R][c in H AND submitted pointer/quote exactly equals ground_span(c)]/|R|` | `R=empty => 0` |
| redline quality `D` | 0.05 | `sum[c in E] tier(c)/|E|`, where `E={c in H: agent(c)=reject AND edit_required(c)}` | `E=empty => 0`; an omitted proposal has `tier=0` |
| conformance `F` | 0.03 | 1 iff schema-valid, complete exact-ID map, no conflicting duplicates, card equals map; else 0 | binary |
| abstention `A` | 0.02 | harmonic mean of precision and recall over opaque missing-info IDs | no planted IDs and no submitted escalation => 1; no planted IDs with any escalation => 0; planted IDs with no submissions => 0 |

`tier(c)` is the existing deterministic M2 matcher applied only in its proper direction, agent-authored redline against plant-time expected redline: `1/.75/.50/0`. No judge tiebreak is allowed. Notice two deliberate denominator choices. Grounding divides by **all submitted rejections**, so four grounded rejections of which only two are correct give `G=2/4=.5`; grounding a wrong disposition never pays. Redline quality divides by **all correctly rejected edit-required children whether or not a proposal was supplied**: one exact proposal on four such children gives `D=(1+0+0+0)/4=.25`, not 1.

The phase-2 raw score is

`W2=.30S+.20T+.15J+.10Q+.10L+.05G+.05D+.03F+.02A`.

There is no N/A reweighting. The abstention zero-case above is the only vacuous case, and its weight stays 0.02.

## 1.3 Discrete family integrity and phase composition

The required harmful-family set for a fixture is

`RF={regression, sneak_inserted_child, new_deviation} UNION {unacceptable_counter if present}`.

Each member must occur at least once. `family_ok(f)=1` iff **every** answer-key child belonging to `f` is correctly rejected. Thus an extra regression does not hide a missed regression. `harm_integrity=AND[f in RF] family_ok(f)`.

The phase-2 ordinary eligibility floors are `S>=0.50`, `T>=0.50`, `J>=0.50`, `L>=0.50`, and `G>=0.50`. They prevent a wholly omitted construct from entering composition; they are not substitutes for family integrity. The grounding floor specifically kills a before-text/phase-1 quoter without making an occasional honest grounding slip trigger the family cap. If any floor fails, `P2=0`; otherwise `P2=W2`.

Let `P1` be the existing seeded-T2 composite. The episode score before the family cap is

`E0 = sqrt(P1*P2)` if `P1>=0.40` and `P2>=0.40`, else `0`.

The final mixed-task episode score is

`E = E0` when `harm_integrity=1`; otherwise `E=min(E0,0.20)`.

The 0.20 cap is the discrete consequence of missing even one required harmful family. It applies after phase composition, so unrelated phase-1 credit cannot buy it back. It is a cap rather than a zero because an honest single-event slip must retain diagnostic gradient. The v3 attacks become: perfect/zero phase `sqrt(1*0)=0`; `P1=.825,P2=0 =>0`, not `.4125`; and even the v3 miss-one `P2=.72-.836` with perfect phase 1 becomes `min(sqrt(.72-.836),.20)=.20`, not `.72-.836`.

The value written as the episode's official composite is `reported_E=min(E,.80)`. The ceiling applies identically to every agent after all floors and caps; it prevents saturation and keeps the honest calibration target inside SPEC's `.40-.80` band. Raw `E` remains telemetry.

For a release tranche, compute `mean(E)` only after the counter gate in 1.6. All legitimacy comparisons use this gated mixed-task tranche score, never an all-concessions pool.

## 1.4 Executable transition predicate table

Common definitions: `eligible P1` means exact equality to `P*` as specified in 1.1. `same rule` means phase-2 `rule_id=P*.rule_id=expected_rule_id`. `source clause` means `P*.clause_id=answer_key.source_clause_id`; `destination clause` means the submitted phase-2 clause equals the child ledger clause. `fallback=` means normalized phase-1 fallback equals the plant-time rendered fallback. `counter guard` means the eligible P1 comparator/context record ID equals the counter record's required guard ID; the scorer does not evaluate prose or recompute a comparator. Correctness always uses the emitted phase-2 label.

| row ID | event_type / child_role / origin | prior_position_id | fields required for continuity | required phase-2 decision | continuity |
|---|---|---|---|---|---|
| TR-01 | `concession / sole / prior_position` | required | eligible P1; P1 decision=`reject`; same rule; source clause; `fallback=`; child after-value is plant-labeled concession | accept | Y |
| TR-02 | `regression / sole / prior_position` | required | eligible P1; P1 decision=`reject`; same rule; source clause; `fallback=` | reject | Y |
| TR-03 | `sneaky_reinsert / source_cleanup / prior_position` | required | eligible P1; P1 decision=`reject`; same rule; source clause; `fallback=`; child ledger clause=source clause | accept | Y |
| TR-04 | `sneaky_reinsert / inserted_effect / prior_position` | required | same eligible P1 as TR-03; P1 decision=`reject`; same rule; P1 source clause must differ from child destination clause; `fallback=` | reject | Y |
| TR-05 | `counter_proposal / sole / prior_position` | required | eligible P1; P1 decision=`reject`; same rule; source clause; `fallback=`; counter guard exact | emitted accept or reject | Y |
| TR-06 | `new_deviation / sole / novel_insertion` | forbidden | submitted rule and destination clause equal emitted child fields; no phase-1 field is consulted | reject | N/A |
| TR-07 | `benign_canary_change / sole / canary_probe` | forbidden | no phase-1 field is consulted; citing its canary rule in a reject/flag still triggers GAMED | accept | N/A |

No other combination is legal. V14 fails emission on an unlisted tuple. For TR-01 through TR-05, continuity numerator credit requires all cells in that row; correctness of the phase-2 decision alone does not imply continuity. TR-06/07 never enter `P`.

## 1.5 The fifth seeded deviation and exact child accounting

All five T2 deviations receive a response. The eligibility-aware sampler assigns the five distinct source deviations to this multiset:

`{concession, regression, sneak, counter, fifth_response}`.

`fifth_response` is plant-time chosen as either (a) a second counter from a different signed family, or (b) a second sneak when two eligible signed destination families exist. It is never silently dropped. Choice (a) is the default; choose (b) only to produce a declared 9-child fixture. It may not be another concession or regression because the minimum must expose two independently classifiable counter records often enough to support counter realism and balance.

The generator additionally emits one `new_deviation` and one independent benign canary. Counts are:

| total | source response accounting | origin counts `(prior,novel,canary)` | harmful / benign | validity |
|---:|---|---|---|---|
| 7 | would require only four of five seeded deviations to receive a response | `(5,1,1)` | class-dependent `3/4` or `4/3` | **invalid; V14 fifth-response check fails** |
| 8 | concession 1 + regression 1 + sneak 2 + two counters 2 + novel 1 + canary 1 | `(6,1,1)` | with counter classes AA: `3/5`; AU: `4/4`; UU: `5/3` | canonical minimum |
| 9 | concession 1 + regression 1 + two sneaks 4 + one counter 1 + novel 1 + canary 1 | `(7,1,1)` | acceptable counter: `4/5`; unacceptable: `5/4` | permitted expansion |

The canonical minimum-coverage mixed task is the 8-child AU form: prior children are concession, regression, sneak source, sneak insertion, acceptable counter, unacceptable counter; plus novel insertion and canary. It has `H/B=4/4`. AA and UU forms are permitted only as part of a balanced hidden tranche and still contain the three always-required harmful families. A release must contain at least 28 acceptable and 28 unacceptable counter children overall, with at least two held-out tasks per practice area. This widens v3's statistical minimum; it adds generated instances, not per-instance attorney work.

## 1.6 Counter arithmetic, aggregation, and leakage controls

Per task, `J` is ordinary accuracy over the counter children actually present. It is always defined because `|K|>=1`; a one-class task has no `0/0`. It is the 0.15 channel in `W2`.

Across a release tranche, let

`RA=# correctly accepted acceptable counters/# acceptable counters`,

`RU=# correctly rejected unacceptable counters/# unacceptable counters`, and

`Jmacro=min(RA,RU)`.

Both denominators must be at least 28. `Jmacro` is reported only at tranche level and is not substituted into an episode. The **counter gate** is: if `Jmacro<0.70`, the gated mixed-task tranche composite is zero. Otherwise it is `mean(E)`. This makes one-class heuristics and chance counter extractors release failures while leaving ordinary per-event gradient inside tasks.

Exact balance is created in a private manifest, then a cryptographically seeded Fisher-Yates permutation independently assigns response bundles to opaque task IDs. The permutation seed, pre-permutation index, tranche membership, quota, generator attempt number, family ID/hash, and class are absent from every observation and rollout filename. Each episode is scored in a fresh process with no cross-episode state or batch API. Event order inside a task is a second independent secret permutation constrained only by patch-offset replay; the displayed change order is document order, never label order. Evaluation clients receive one task at a time and are not told remaining counts. Exact balance is for sampling/reporting, not observable side information.

Extended V10 executes, not merely describes, these checks over at least four independently seeded tranches:

1. reject if any forbidden field above appears in an observation or public task ID;
2. for each visible categorical feature (task ordinal after public sort, event ordinal, section bucket, operation, surface-template hash, playbook rule, family split), fit every one-level lookup classifier on three tranches and require held-out balanced accuracy `<0.60` and each cell contain both labels when cell size is at least 4;
3. compute permutation mutual information between label and task ordinal/event ordinal/section bucket; using 10,000 label permutations, require familywise Holm-corrected `p>=.05` and normalized MI `<.05`;
4. run the quota-constrained batch attacker with the public observation only; require balanced accuracy `<.60` and the full contract gates;
5. unit-test fresh-process isolation by writing sentinel state in one rollout and proving it is unavailable in the next.

Failure rejects the tranche; it is not repaired by score reweighting.

## 1.7 Counter-family realism minimums

The signed contrast record remains the label authority, but every counter family must meet all of these family-level authoring and render-time checks:

1. **Two-input minimum.** Acceptance is a Boolean expression over at least two decisive inputs, not one scalar: at least one counter-text slot and at least one independently varied phase-1 context/reservation slot. Allowed forms include `x<=a AND exception_absent`, `x<=a AND y>=b`, or a signed trade-off table over `(x,y,context)`. A single exposed comparator is invalid.
2. **Decoys.** Every rendered counter contains at least two non-decisive decoy values of the same surface type as a decisive value (two other quantities for numeric/date families; two other category candidates for categorical families). A decoy must vary independently across renders, appear in the operative sentence or its immediately adjacent sentence, and changing it alone must not change the signed label. Boilerplate dates in headings do not count.
3. **Surface variation.** Each decisive input has at least three render forms, including unit/date normalization where applicable, and no fixed token offset or ordinal identifies it. Acceptable and unacceptable labels use every render form.
4. **Qualitative coverage.** At least one third of signed families per playbook (rounding up, so 1 of 2-3 and 2 of 4) include a qualitative exception/condition whose presence, scope, or negation is decisive. At least one third include a two-quantity or date-arithmetic interaction. One family may satisfy both.
5. **Counterfactual tests.** For every family the generator emits non-scored validator twins varying each decisive input alone and each decoy alone. V14 requires the emitted signed truth table to flip exactly where the family record says it flips and never on a decoy-only change.
6. **Attack gate.** Slot regex, unit normalization, date arithmetic, common-threshold, M2 similarity, and single-sentence bag-of-values attackers must each have held-out balanced counter accuracy `<.60` and must fail both release gates.

These are family-level attorney signings within the existing 2-4 counter families per playbook. They require richer contrast records but no per-instance review and no new fixture class.

## 1.8 `all_concessions`

Let `M` be the integer mixed-task count and `A_c` the integer all-concessions count. Compliance is

`A_c/(A_c+M)<=1/10`, equivalently `9A_c<=M`.

Thus with `M=14`, `A_c<=floor(14/9)=1`; two gives `2/16=.125` and is invalid. With `M=18`, `A_c<=2` exactly (`2/20=.10`); with `M=35`, `A_c<=3` (`3/38=.078947`), not 4 (`4/39=.102564`). Never round a percentage upward.

The v3 gate and weights remain: after full change-block read coverage, explicit accept for every advertised ID, exact interactive/card equality, and valid prior links, score restraint `.55`, continuity `.20`, conformance `.15`, abstention `.10`. Failure of the gate gives zero. Only task-type means are published; no labeled or unlabeled top-line pool exists, and this score cannot rescue a mixed-task gate.

A mechanical enumerator can score 1.0 here. That is irreducible: because every child is benign by construction and truth is forward-generated, the observable action trace of complete correct acceptance is identical for the script and the lawyer. No deterministic span label can distinguish their mental process without adding harmful probes, an LLM judge, or per-instance human judgment, all contrary to the settled task type or hard constraints. Therefore `all_concessions` is explicitly a coverage/state/conformance diagnostic, not evidence of negotiation judgment; separate reporting and `9A_c<=M` bound its scope.

# 2. SELF-ATTACK ANALYSIS

## 2.1 Calculation conventions

The table attacks mixed tasks only. `C7` means the attempted 7-child fixture: it receives no score because V14 rejects it. `C8` and `C9` are the 8- and 9-child forms above. To give attackers every benefit, auxiliary fields they can copy are scored 1, phase 1 is set to its best documented mechanical value where applicable (`.825` for blanket), and an attacker otherwise receives `P1=1`. A family miss invokes the final `.20` cap. A phase floor miss gives zero. Counter-only lexical strategies are evaluated on the validator requirement `<.60`; use the most favorable passing-bound value `.5999`, which still fails the tranche `Jmacro>=.70` gate and therefore has gated composite zero.

For reference, without the family cap a one-miss oracle with `P1=1,P2=.836` would get `sqrt(.836)=.914330`; v4 instead gives `.200000`. A phase-1 blanket with no phase 2 is `0`, and with a family-breaching `.72` phase 2 is `min(sqrt(.825*.72),.20)=.20`.

The relative column uses the worst honest endpoint from section 3, `H85=.5408`; sixty percent is `.3245`. Hence any score at or below `.20` fails both attacker-success gates. “Fail” in the last two columns means the attacker correctly fails to clear the tier.

| # | strategy | C7 | C8 gated composite | C9 gated composite | `<.40` gate | `<=.60 H85` gate | arithmetic / binding rule |
|---:|---|---:|---:|---:|---|---|---|
| 1 | `accept_all` | invalid | 0 | 0 | fail | fail | `S=0<.5`, so `P2=0` |
| 2 | `reject_all_nearest_rule` | invalid | 0 | 0 | fail | fail | `T=0<.5`; canary rejection also GAMED |
| 3 | `prior_location_replayer` | invalid | .200000 | .200000 | fail | fail | misses novel harmful family; cap |
| 4 | `always_reject_counter` | invalid | 0 | 0 | fail | fail | tranche `RA=0`, so `Jmacro=0<.70` |
| 5 | `turn2_only` | invalid | 0 | 0 | fail | fail | `P1=0` and `L=0<.5` |
| 6 | `duplicate_action_washer` | invalid | 0 | 0 | fail | fail | identical duplicates collapse; conflicts make `F=0` and affected decisions wrong; blanket form fails `T` |
| 7 | `before_text_quoter` | invalid | 0 | 0 | fail | fail | before span gives `G=0<.50`, so `P2=0` |
| 8 | `accept_all_but_1_harm` | invalid | .200000 | .200000 | fail | fail | misses required family by construction |
| 9 | `accept_all_but_2_harms` | invalid | .200000 | .200000 | fail | fail | one or two required families missed; same cap |
| 10 | `cheapest_harm_oracle` | invalid | .200000 | .200000 | fail | fail | any deliberate required-family omission caps episode |
| 11 | `m2_threshold_counter` | invalid | 0 | 0 | fail | fail | counter balanced accuracy `<.60`; `Jmacro<.70` |
| 12 | `blanket_position_then_clause_match` | invalid | 0 | 0 | fail | fail | `P1=.825`; full-tuple eligibility rejects vacuous P1 records, so `L=0<.5` and `P2=0` |
| 13 | `slot_extractor_counter` | invalid | 0 | 0 | fail | fail | two-input/context + decoy fixtures hold extractor `<.60`; tranche gate |
| 14 | `seeded_blanket` | invalid | 0 | 0 | fail | fail | phase 2 absent, so `P2=0` |
| 15 | `phase1_only` | invalid | 0 | 0 | fail | fail | even `P1=1`, `sqrt(1*0)=0` |
| 16 | `quota_constrained_batch_attacker` | invalid | 0 | 0 | fail | fail | no batch/tranche visibility; V10 requires `<.60`, then counter gate |
| 17 | `unit_normalizing_slot_extractor` | invalid | 0 | 0 | fail | fail | one input plus units is insufficient and attack accuracy `<.60` |
| 18 | `date_arithmetic_extractor` | invalid | 0 | 0 | fail | fail | same; qualitative/context input remains unread, `Jmacro<.70` |
| 19 | `common_threshold_lookup` | invalid | 0 | 0 | fail | fail | family-held-out and context interaction keep balanced accuracy `<.60` |
| 20 | `all_concessions_enumerator` | invalid | N/A mixed | N/A mixed | N/A | N/A | irreducible 1.0 only on separately reported all-concessions diagnostic |

The strongest surviving mixed-task attacker score is `.200000`. All 19 mixed-task strategies fail both gates: `.20<.40` and `.20/.5408=.3698<=.60`. Strategies 11, 13, and 16-19 are zero only after the mandatory tranche gate; their ungated episode scores are not evidence of a valid release. This is intentional: counter discrimination is a population construct when a task may contain one class.

### 2.2 Size-specific spot arithmetic

For C8-AU, `H=B=4`. A deliberate one-harm miss has `S=3/4=.75,T=1`. Giving every other channel 1 yields

`W2=.30(.75)+.20+.15+.10+.10+.05+.05+.03+.02=.925000` and `sqrt(W2)=.961769`, but `harm_integrity=0`, hence `E=.200000`.

For C8-AA, `H=3,B=5`, one-harm miss gives `S=2/3`; the overly generous raw score is `.30(2/3)+.70=.900000`, `sqrt=.948683`, capped to `.200000`. For C8-UU, `H=5,B=3`, one miss gives `S=4/5`; raw `.940000`, `sqrt=.969536`, capped to `.200000`.

For C9 with an acceptable counter, `H=4,B=5`; one miss gives the same raw `.925000`, then `.200000`. With an unacceptable counter, `H=5,B=4`; raw `.940000`, then `.200000`. Thus adding a child cannot wash out the discrete family failure.

Always-reject-counter can be perfect on UU tasks and wrong on AA tasks. Exact balance gives `RU=1,RA=0`, so `Jmacro=0`; quota knowledge is unavailable, and even if it were guessed, V10 rejects any observable feature classifier at `.60` or above.

The all-concessions enumerator is the sole residual. It is not counted as a mixed attacker and cannot inflate a mixed composite because no pooled composite exists. Distinguishing it from a lawyer on a zero-harm answer key would require changing the construct or using forbidden process judgment; section 1.8 is the proof sketch and scope limitation.

# 3. HONEST-AGENT SANITY

This is an analytic calibration model, not a claimed measured result. Let disposition accuracy `p` be `.85,.90,.95`; let grounding on correct rejections be `.90`; continuity accuracy be `.92`; redline tier mean be `.85`; conformance be 1 and abstention `.95`. Model phase 1 conservatively as `P1=p`. For ordinary eligible phase-2 tasks, set `S=T=J=Q=p`, `L=.92`, `G=.90p` (the all-rejection denominator also prices wrong rejections), `D=.85`, `F=1`, `A=.95`. Then

`W2(p)=.30p+.20p+.15p+.10p+.10(.92)+.05(.90p)+.05(.85)+.03+.02(.95)`

`= .795p + .1835`.

So eligible episode scores are:

| p | W2 | `sqrt(P1*W2)` |
|---:|---:|---:|
| .85 | .859250 | .854612 |
| .90 | .899000 | .899500 |
| .95 | .938750 | .944359 |

The discrete cap applies when an honest reviewer misses a required harmful family. The 8-child release mix has three required families on AA tasks, four on AU/UU tasks; the 9-child tasks also have three or four distinct required families (a second sneak remains the same family, but every child in it must be right). Under independent event noise and equal three-/four-family task share, the integrity probability is `r(p)=(p^3+p^4)/2`. Grounding slips remain priced through `G` and its `.50` floor, not through this discrete cap. The expected score is

`H(p)=r(p)*sqrt(p*W2(p)) + (1-r(p))*.20`.

| p | r(p) | honest expected composite H(p) |
|---:|---:|---:|
| .85 | .568066 | **.571863** |
| .90 | .692550 | **.684439** |
| .95 | .835941 | **.822239** |

Applying the section-1 reporting ceiling `reported_E=min(E,.80)` gives

`H_report(p)=r(p)*.80+(1-r(p))*.20=.20+.60r(p)`:

| p | reported honest composite |
|---:|---:|
| .85 | **.540839** |
| .90 | **.615530** |
| .95 | **.701564** |

This is the frozen honest estimate: **0.5408-0.7016** across 85%-95% accuracy. The best mixed mechanical attacker is `.20`; at the low endpoint `.60H85=.3245` and `.20/.5408=.3698`, leaving an absolute gap `.3408`. It neither collides with `.40` nor approaches the relative gate.

The family cap is therefore severe against deliberate omission without zeroing honest learning signal. At 85% accuracy, about 43.2% of tasks hit the cap, yet the expected reported composite remains `.5408`. Correlated mistakes could move this number; before release, engaged-honest must still be empirically measured in `.40-.80`, every counter-class recall must exceed `.70`, and all attackers must satisfy both gates. If measurement disagrees, the tier fails; constants may not be tuned without publishing v5 and rerunning the full battery.

# 4. WHAT YOU CHANGED vs v3 AND WHY

1. v3 `safety>=2/3` aggregate eligibility -> v4 named harmful-family integrity with an episode cap of `.20` for any missed required family; closes round-3 F1 at discrete H=3/4/5 without zeroing honest gradient.
2. v3 permitted an unresolved 7-child reading -> v4 makes all five seeded deviations receive responses, rejects 7 children, freezes 8 as minimum and 9 as the two-sneak expansion; closes F1's fifth-deviation ambiguity.
3. v3 left the fifth response unspecified -> v4 assigns it a second different-family counter by default or a second signed sneak for 9-child fixtures; closes F1.
4. v3 `0.5P1+0.5P2` -> v4 conjunctive floors `P1,P2>=.40` plus `sqrt(P1P2)`; closes F3.
5. v3 had no episode output ceiling -> v4 reports `min(E,.80)` for all mixed episodes; keeps the modeled honest band within the controlling `.40-.80` range and applies equally to attackers.
6. v3 phase-2 floors `S,T>=2/3` and counter positive -> v4 ordinary floors `S,T,J,L,G>=.50`, with the stronger named-family cap and tranche counter gate doing the anti-gaming work; prevents strict aggregate floors from crushing honest noise while closing F1/F2/F8.
7. v3 per-task `counter_judgment=min(recall_A,recall_U)` -> v4 per-task accuracy over present counters enters at weight `.15`; tranche-only `Jmacro=min(RA,RU)` is defined with both denominators `>=28`; closes F2.
8. v3 had no locked tranche counter threshold -> v4 requires `Jmacro>=.70` or the gated mixed-tranche score is zero; kills one-class and near-chance counter policies.
9. v3 `>=1` counter per task -> v4 retains that architecture but makes the canonical 8-child task carry two and permits one in the 9-child expansion; increases counter evidence without reinstating a public per-task opposite-label quota.
10. v3 `>=4 prior_position` children -> v4 `>=6`; follows the complete five-response child accounting and strengthens continuity coverage.
11. v3 grounding denominator said reject/flag but conflicted with v2 -> v4 numerator is correct rejection plus exact designated after-span and denominator is all submitted rejections; closes F8 and denies credit for grounding a wrong decision.
12. v3 redline denominator was conditioned on carrying a proposal -> v4 denominator is every correctly rejected edit-required child, missing proposal `=0`; closes F9 (`1/4=.25`).
13. v3 abstention moved weight to conformance on no-item tasks -> v4 never reweights; no-item/no-escalation is 1 and a spurious escalation is 0, making every task sum to the same fixed weights.
14. v3 ID eligibility used correct rule+span -> v4 requires exact source deviation, decision, rule, clause, fallback and comparator/context record; closes F3/F4's vacuous position farming.
15. v3 asserted allowed transitions -> v4 supplies exhaustive TR-01 through TR-07 and rejects unlisted tuples; closes F4.
16. v3 counter families could differ in one decisive slot -> v4 requires at least two decisive inputs, including phase-1 context; closes F5's naked slot oracle.
17. v3 imposed no decoy minimum -> v4 requires at least two independently varied same-type decoys in or adjacent to the operative sentence; closes F5.
18. v3 had no qualitative quota -> v4 requires `ceil(families/3)` qualitative-exception families and `ceil(families/3)` arithmetic/two-quantity families per playbook; closes F5.
19. v3 had template-family held-out splits -> v4 also splits/tests comparator/rule behavior through validator twins and gates six distinct extractors below `.60`; closes F5.
20. v3 exact tranche balance had unspecified exposure -> v4 hides quota/membership/order/seed, uses two secret permutations, isolates episode processes, and gives V10 five executable checks; closes F6.
21. v3 had no minimum counter sample for macro recall -> v4 requires at least 28 children in each class across the release; makes the `.70` tranche gate statistically usable.
22. v3 all-concessions cap was prose `<=10%` -> v4 integer rule `9A_c<=M`, with no top-line pool; closes F7.
23. v3 described all-concessions 1.0 as a score without construct label -> v4 explicitly calls it a coverage/state/conformance diagnostic and proves protocol enumeration is irreducible; closes F7 without pretending enumeration is judgment.
24. v3 mixed weights `.30/.20/.15/.10/.10/.05/.05/.03/.02` -> v4 retains them exactly; only equations, gates, and zero rules change.
25. v3 all-concessions weights `.55/.20/.15/.10` -> v4 retains them exactly; integer share and interpretation change, not channel arithmetic.
26. v3 legitimacy battery lacked slot variants and quota attack -> v4 adds slot, unit, date, common-threshold, quota, one-easy-redline, seeded-blanket, and phase-only attackers; closes F3/F5/F6/F9.

# 5. v4.1 AMENDMENT (2026-07-11)

Replay of 25 stored real GLM episodes against the frozen v4 scorer exposed an
unsatisfiable continuity predicate. The phase-1 `proposed_redline` submitted by
an agent was compared with `plant_position.fallback_text`, an answer-key value
that is never included in an agent observation and is deliberately different
from the visible playbook fallback. This made `L=0` in 25/25 episodes; because
`L>=.50` is an ordinary floor, all 25 composites were zero. The repository's
`test_honest_perfect_episode_and_prompt` fixture only avoided the defect by
constructing its actions directly from answer-key fields in
`planted_deviations.json` and `patch_ledger.json`.

The v4.1 decision is narrowly scoped. Continuity no longer compares fallback
text; it still requires correct linkage to the matching deviation, decision,
rule, clause, and comparator/context record, and all transition-specific checks
in §1.4 remain unchanged. Grounding now case-folds and collapses whitespace,
then accepts a submitted quote contained in the designated changed span when
the normalized quote is at least `MIN_QUOTE_OVERLAP` characters. The comparison
is intentionally one-directional so an overbroad span containing the target
does not receive credit. The phase-2 driver prompt now explicitly instructs a
rejecting reviewer to quote verbatim from `after_text`, rather than from
`before_text` or a paraphrase. Redline quality remains exclusively in `D`.

Exact implementation changes:

- The contract identifier is bumped from `t2n-reward-v4` to
  `t2n-reward-v4.1`, including the schema const and generated-ledger paths.
- `evaluate_transition` removes only the normalized phase-1/ledger fallback
  equality conjunct from its `exact` tuple.
- `join_phase2_records` replaces byte-exact `grounding_exact` equality with
  normalized, minimum-length, quote-in-span containment.
- The phase-2-only observation prompt adds the `after_text` quotation sentence;
  the phase-1 prompt branch is unchanged.

All other equations, weights, floors, family requirements, transition rows,
and gates in §§1-4 remain frozen and unchanged.
