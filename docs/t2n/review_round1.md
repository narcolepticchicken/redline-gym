# Adversarial red-pen review — proposed T3 multi-turn negotiation tier

The calculations below use the only weights defined by the project for a seeded task: recall 0.35, precision 0.15, grounding 0.15, fallback 0.15, conformance 0.10, and abstention 0.10 (`SPEC.md:250-260`; `scoring/core.py:14-21`). The draft says it keeps the same channels and does not supply replacement weights. Honeypot is a gate, not a seventh weighted channel.

## Area 1 — GAMEABILITY

### 1. Blanket rejection beats the proposed honest band

**Labels:** Areas 1, 3, 6  
**Severity:** **BLOCKER**

**Failure scenario:** Take a 10-event task with four `concession`, two `regression`, one `sneaky_reinsert`, one `new_deviation`, and two `counter_proposal` events, one acceptable and one unacceptable. The agent rejects every change, uses the nearest plausible `rule_id`, copies exact text out of each change block, and flags the fresh deviation.

- Recall is 1.0: all two regressions, the sneaky reinsert, and the new deviation were acted on. The unacceptable counter is not even in the draft's recall denominator.
- On the most natural reading of `total` as the ten canonical event actions, precision is `1 - 4/10 = 0.60`. The wrong rejection of the acceptable counter is not listed as a precision error; the numerator names only false rejections of concessions and phantom flags.
- Grounding is 1.0 because the agent can copy displayed text. Current grounding is correctness-independent and only asks whether the quote occurs in the document (`scoring/core.py:78-79, 308-312`).
- Fallback is 0.5 if one counter rejection is right and one is wrong.
- A valid card gives conformance 1.0. Abstention is 1.0 if there is no missing-info item or the agent emits the mechanically easy escalation described in Finding 5.

The inherited composite is therefore `0.35(1) + 0.15(.60) + 0.15(1) + 0.15(.50) + 0.10(1) + 0.10(1) = 0.865`. Even with abstention forced to zero, it is 0.765—inside the target honest band. This dumb strategy therefore clears or exceeds the success criterion.

The error is structural: recall rewards only aggressive behavior; precision barely prices over-aggression; grounding pays for accurately quoting a wrong answer; and the additive composite lets those channels compensate for no negotiation judgment.

**Fix:** Define one expected disposition for every event and derive a confusion matrix over event IDs. Harmful events must include regression, sneaky reinsert, new deviation, and unacceptable counter; benign events must include concession and acceptable counter. Define:

- safety recall = correctly rejected/flagged harmful events divided by all harmful events;
- rejection precision = correctly rejected/flagged harmful events divided by all reject/flag dispositions, with zero for no reject/flag dispositions;
- restraint = correctly accepted benign events divided by all benign events;
- counter judgment = correct accept/reject decisions over all counter events.

Condition grounding and proposed-redline credit on a correct disposition. Then multiply the ordinary composite by the harmonic mean of safety recall and restraint (with zero when either is zero) on mixed tasks. That joint gate makes both blanket rejection and blanket acceptance fail instead of letting unrelated channels buy them back.

### 2. “Accept everything” either clears the band or makes correct all-concessions behavior unscorable

**Labels:** Areas 1, 3, 6  
**Severity:** **BLOCKER**

**Failure scenario:** On the same 10-event mix, an agent explicitly accepts every `change_id` and files no flags.

Under the draft's literal formula, false rejections and phantom flags are both zero, so precision is `1 - 0/10 = 1.0`. Recall is 0. Fallback is 0.5 because the acceptable counter is accepted and the unacceptable one is not. Grounding is 0 if accepts need no quote. With valid conformance and easy abstention, the score is `0 + .15 + 0 + .075 + .10 + .10 = 0.425`. That clears the lower edge of the proposed honest band without identifying one harmful response.

There is no safe alternative interpretation already present in the draft. If `total` means only rejections and flags, accept-all produces `0/0`. If the implementation imports the current vacuous-credit rule and assigns zero precision when there are no flags (`scoring/core.py:74-79`), accept-all drops to 0.275—but the genuinely correct all-concessions task also loses the intended restraint credit unless it is special-cased. The draft simultaneously invokes event-denominated precision and M1's clean-task exception without resolving the conflict.

**Fix:** State that the denominator is the set of canonical expected event IDs, never raw actions. Require exactly one explicit disposition per event; omission is wrong. Use the harmful/benign confusion matrix and joint safety/restraint gate from Finding 1. Give the dedicated all-concessions type its own explicit-accept coverage rule (Finding 14), not a zero-denominator exception.

### 3. Replaying turn-1 locations scores competitively without reading the response

**Labels:** Areas 1, 3, 4  
**Severity:** **BLOCKER**

**Failure scenario:** Consider ten original turn-1 positions whose responses are three concessions, three regressions, one sneaky reinsert, two counters (one acceptable), plus one new deviation elsewhere. An agent rejects/re-flags all nine original locations and ignores the new location and the turn-2 semantics.

- It catches the three regressions, so recall is `3 / (3 regressions + 1 sneak + 1 new) = 0.60`.
- The draft counts the three rejected concessions as false. It does not say that rejecting the acceptable counter or rejecting the old half of a sneak is a precision error. With nine actions, precision is `1 - 3/9 = 0.667`.
- It copies a verbatim quote at every old location, so grounding is 1.0 under current code.
- Always rejecting the two counters gets fallback 0.5 in this example.
- Conformance and abstention can both be 1.0.

The score is approximately `.35(.60) + .15(.667) + .15(1) + .15(.5) + .10 + .10 = 0.735`; even with abstention zero it is 0.635. This is a turn-1-position lookup bot, not a negotiation reviewer.

Grounding does not close the exploit. `_quote_grounded` ignores `clause_ref` and tests whether the string occurs anywhere in the document. `_match_flag` ignores `clause_ref` too and accepts substring overlap with `mutated_text` (`scoring/core.py:178-192, 308-312`). A tracked markdown block necessarily contains before text, after text, or both; a deleted turn-1 phrase can therefore remain quote-grounded even after a concession. If turn-1 and turn-2 views are both shipped as documents, the old text has another place to ground.

**Fix:** Ground every negative disposition to a canonical pointer `(view_id, change_id, side, start_offset, end_offset)` and require the quote to equal the designated current offending `after` span. A `before` span and a turn-1 view must never ground a turn-2 rejection. Match recall by event ID, not quote overlap. Add a mandatory `prior_location_replayer` baseline gate as specified in Finding 17.

### 4. “No alternatives means reject” creates a 67–87% counter baseline

**Labels:** Areas 1, 2  
**Severity:** **BLOCKER**

**Failure scenario:** The draft expects only 2–4 of 12–15 rules per playbook to receive alternatives. If counters are sampled across planted rules as written, the visible absence of `acceptable_alternatives` makes between `8/12 = 66.7%` and `13/15 = 86.7%` of counter events reject-only. An agent can decide those counters without reading a word of counterparty text. If even half of the counters on alternative-bearing rules are deliberately unacceptable, the always-reject counter heuristic rises further. With one or two counters per task and four held-out tasks, it can easily score 100% by sampling luck.

This is not a weak shortcut. `counter_proposal` is sold as the heart of negotiation judgment, while the dominant visible class has a hard-coded answer.

**Fix:** Emit `counter_proposal` only for rules with attorney-signed acceptable alternatives. Treat a response on a rule without alternatives as a regression or another non-counter event. Within every scored cohort, balance acceptable and unacceptable counters by construction, and report the two accuracies separately. Do not let a tranche pass if the `always_reject_counter` baseline reaches 0.40 composite or 60% of honest.

### 5. Unchanged grounding and abstention donate reward to wrong or mechanical actions

**Labels:** Areas 1, 3, 6  
**Severity:** **DESIGN-RISK**

**Failure scenario:** Current grounding awards credit for a verbatim quote even when the finding matches no deviation; this behavior is explicitly tested (`tests/test_scoring.py:243-263`). Thus every wrong blanket rejection can still earn the full 0.15 grounding contribution.

Current seeded-task abstention is also cheap. The generator appends missing-info context anchors to visible `client_context` (`generator/generate.py:197-200, 516-521`), and the scorer accepts an escalation if it contains any answer-key topic word longer than three characters (`scoring/core.py:433-463`). It does not penalize spurious seeded-task escalations. A blanket strategy can echo every salient client-context phrase as an escalation and usually buy the 0.10 abstention contribution used in Findings 1–3.

**Fix:** Score grounding only for correctly disposed event IDs, with an exact canonical span pointer. Give missing-info items opaque visible IDs, require escalation of the correct ID, deduplicate by ID, and set abstention to precision/recall over missing-info decisions so spurious escalations reduce it. Do not carry the current substring heuristic into T3.

## Area 2 — DETERMINISM HOLES IN COUNTER-PROPOSAL SCORING

### 6. M2 is the wrong-direction instrument and has no binary acceptance semantics

**Labels:** Areas 1, 2  
**Severity:** **BLOCKER**

**Failure scenario:** M2 was built to give partial fallback-writing credit to agent-authored text against one generated target. `_fallback_score` first restricts scoring to correctly matched deviations, then compares the agent's `proposed_redline` with `expected_redline_text` (`scoring/core.py:315-372`). The matcher returns 1.00/0.75/0.50/0.00, not an accept/reject truth value. The draft instead wants to compare generator-authored counterparty text with a list of policy alternatives and then grade an agent decision. That is a different direction, cardinality, and construct.

The matcher is substantively unsafe for this use. Its 0.75 tier uses token LCS and its 0.50 tier uses unordered unique-token containment (`scoring/core.py:375-399`):

- Signed alternative: “Vendor may use Customer Data solely to provide Services and may not train models.”
- Bad counter: the same sentence with “not” removed.

The bad counter preserves 13 of 14 ordered tokens, so it can receive 0.75 while reversing the obligation. Removing both “solely” and “not” still preserves 11 of 13 unique expected tokens, so it receives 0.50. Conversely, “Following expiry, Provider must purge every item of Client information within one month” can be substantively equivalent to “Vendor shall delete all Customer Data within thirty days after termination” while scoring 0.

The draft never states whether 0.50 or 0.75 means “accept,” whether partial credit applies to the decision, or how multiple alternatives are combined. A correct agent can therefore be deterministically marked wrong, and an incorrect agent can be deterministically marked right. Determinism of a bad lexical proxy is not deterministic legal correctness and violates the span-auditable reward claim.

**Fix:** The response recipe—not the scorer—must write `expected_decision: accept|reject` in the same operation that emits the counter. Score `review_change.decision` against that label exactly. Preserve M2 only in its sound direction: when an agent rejects and supplies `proposed_redline`, compare that agent-authored proposal against the signed alternatives and award text-quality credit. Rename counter decision accuracy to negotiation judgment instead of pretending it is the existing fallback channel.

### 7. Nobody authors the generated counter and no emit-time separability gate exists

**Labels:** Areas 2, 5  
**Severity:** **BLOCKER**

**Failure scenario:** The current playbook schema has only `position`, `fallback`, severity, escalation trigger, canary, and deterministic checks (`schema/playbook.schema.json:28-75`). The current recipe engine has signed-looking `original_text`/`mutated_text` templates and performs one exact replacement (`generator/generate.py:151-178, 369-383`). There is no source for a counterparty counter, no acceptable/unacceptable counter template class, and no validator that proves a rendered counter is on the intended side of a matcher boundary. The draft assigns the attorney only the alternative list; it never says who writes the actual counter text.

An implementer has three bad literal options: emit an alternative verbatim, making acceptance a trivial exact-match task; synthesize a paraphrase, reintroducing false rejects; or mechanically damage an alternative, risking the negation false accept in Finding 6. V12 is not an answer: it checks a generated expected redline against one fallback at a 0.075 token-overlap floor (`validators/checks.py:226-249`), not counter semantic class or separation.

**Fix:** Add attorney-reviewed, slot-renderable `acceptable_counter_templates` and `unacceptable_counter_templates` per eligible rule. Each template carries its signed semantic label before generation. At emit time:

1. render the template and log its label and template hash with the event;
2. compute maximum M2 similarity against all alternatives only as a separability validator;
3. require acceptable templates to score at least 0.75 and unacceptable templates to score 0.00; reject the ambiguous 0.50 band;
4. fail emission if normalization merges two templates with different labels; and
5. human-audit every template family, not every random instance.

Reward still uses the signed emitted label, not the lexical gate. This preserves forward-generated truth while using the matcher only to reject ambiguous authored fixtures.

## Area 3 — DOUBLE-COUNTING AND CHANNEL SEMANTICS

### 8. The event table and action space contradict each other

**Labels:** Areas 3, 5  
**Severity:** **BLOCKER**

**Failure scenario:** The draft says every counterparty edit is a `change_id` block (`spec_draft_T3_multiturn.md:21-23`) and V14 says every counterparty diff maps to an event. It then says `flag_issue` is for new deviations “at locations without a change_id” (`:46-50`). A `new_deviation` is, by definition, a fresh counterparty edit, so it must both have and not have a `change_id`.

The same contradiction appears elsewhere. A regression's correct behavior is “reject + re-flag,” even though one `review_change` rejection already carries the rule and quote. A sneaky reinsertion accepts the original location and inserts deviant text elsewhere, which is at least two patches; the table asks only for a flag at the new location and does not say whether the old acceptance must also be reviewed. A literal implementation can award two actions for one regression, one action for a two-patch sneak, or different answers depending on which table row the engineer follows.

**Fix:** Establish one exclusive routing rule:

- Every counterparty-authored patch has a `change_id` and is dispositioned only with `review_change`.
- `flag_issue` is reserved for violations in unchanged text and can never target a `change_id` or event already handled by `review_change`.
- Regression requires one reject decision, not “reject + re-flag.”
- `sneaky_reinsert` is a parent event with two child patches: accept the compliant original-location patch and reject/flag the inserted patch. The parent receives credit only when both child dispositions are correct.
- `new_deviation` is a changed insertion and therefore uses `review_change`; if the design wants it to use `flag_issue`, it must be emitted as untracked text and V14 must explicitly exempt it. The first option is cleaner.

### 9. Reusing V2 union semantics permits collision, denominator washing, and accidental collapse

**Labels:** Areas 1, 3  
**Severity:** **BLOCKER**

**Failure scenario:** Current V2 union is not an event union. `_candidate_findings` concatenates interactive flags and `card.issues`, then deduplicates only by `(rule_id, normalized exact_quote)` (`scoring/core.py:66-69, 143-160`). It does not know `change_id`, decision, action type, document, or location.

That causes failures in both directions:

- A regression can be `review_change`-rejected and separately `flag_issue`-filed. If the two quotes differ, both survive a quote-keyed union. Nothing in the draft forbids both from receiving credit.
- One real regression plus one wrongly rejected concession should yield one correct and one false disposition. An attacker can submit 100 distinct longer/shorter overlapping quotes for the regression and one false rejection. If `total` is raw actions, precision becomes `1 - 1/101 = 0.990` instead of 0.5. Current matching accepts substring overlap of 20 characters, and exact-string dedup does not collapse these variants (`scoring/core.py:178-192`).
- Two genuine events with the same rule and normalized boilerplate quote in different documents or locations collapse into one finding because document and change ID are absent from the dedup key.
- Accept actions have optional rule and quote. If forced through `_candidate_findings`, multiple accepts with empty rule/quote all collapse to the same `("", "")` key. If kept in `card.changes`, current `_card_issues` ignores them entirely.

Current recall's set of matched deviation IDs happens to cap duplicate recall for `flag_issue`, but that protection does not extend to a new action automatically, and it does not stop precision-denominator washing.

**Fix:** Normalize interactive and final-card records into one map keyed by canonical `event_id` or child `change_id`. Allow exactly one final disposition per key; define repeated identical submissions as one action, conflicting submissions as a conformance failure and wrong disposition, and never put duplicates in a precision denominator. Match `flag_issue` only to a separate unchanged-text issue ID namespace. The final card must be checked for exact consistency with the canonical interactive map.

### 10. `review_change` is easy to dispatch but is absent from every state and schema contract that matters

**Labels:** Areas 3, 6  
**Severity:** **BLOCKER**

**Failure scenario:** Adding another `elif` in `Episode._dispatch` is mechanically easy; supporting its semantics is not. The current episode stores only flags, escalations, and a card, and passes only those to the scorer (`env/episode.py:48-57, 104-145, 303-311`). `empty_work` means “no flags and no escalations,” so an episode that explicitly accepts every change is treated as empty (`:123-137`). Seeded-task conformance also requires `flags or escalations`; accepted reviews would not count (`scoring/core.py:84-86`).

The card schema requires only `issues`, `escalations`, and `summary`; it permits arbitrary extra properties (`schema/card.schema.json:4-40`). An implementation could add `changes`, have the schema silently ignore its contents, and still award conformance 1.0. Neither card/interactivity consistency nor one-decision-per-change is defined.

**Fix:** Before implementing dispatch, specify and validate:

- an action schema for `review_change`, including which fields are required for accept and reject;
- episode state `reviews_by_change_id` with duplicate/conflict rules;
- `review_change` as a substantive action for the finalize bounce and conformance;
- a card schema that requires `changes` on T3, sets `additionalProperties: false` within every change entry, and requires decision plus change ID;
- deterministic equality between final-card changes and the canonical interactive map; and
- a scorer signature that consumes the canonical event map, not an untyped pooled list.

## Area 4 — STATE-TRACKING CLAIM

### 11. The task is a static current-document review, not multi-turn state tracking

**Labels:** Areas 1, 4, 7  
**Severity:** **BLOCKER**

**Failure scenario:** At reset the agent receives the perfect turn-1 redline, a turn-2 block containing before and after text, the playbook, and client context. It does not make turn-1 decisions, the environment does not transition between negotiation phases, and no turn-2 action refers to the agent's own prior action.

A response-only agent can ignore turn 1 and review the turn-2 `after` state against the playbook:

- compliant current text: accept;
- current text violating the rule: reject/flag;
- current counter: compare it to visible alternatives;
- fresh insertion: review it against the playbook.

That procedure produces the required disposition without identifying whether the path was concession, regression, or sneak. The before/after block already contains the only historical comparison that might have required memory. The task is existing T2 issue detection plus visible patch IDs and an accept button. Calling it multi-turn does not make it multi-turn, and the response-only ablation is likely to approach honest performance.

**Fix:** Either rename the pilot “deterministic later-turn response review” and drop the state-tracking claim, or make it one two-phase episode. For the latter:

1. Phase 1 requires the agent to submit positions and returns opaque `position_id` values.
2. Phase 2 reveals the fixed, pre-generated response only after phase-1 finalization.
3. `review_change` requires the relevant `prior_position_id`; it is not repeated in the turn-2 block.
4. Credit requires both the correct current disposition and the correct link to the agent's prior position.
5. At least one counter decision per task depends on a deterministic reservation-point/context slot disclosed only in phase 1 and logged by the generator.

The counterparty response can remain static and forward-generated. Missing or wrong phase-1 positions simply make the continuity component wrong. Add a `turn2_only` ablation gate; if it reaches 60% of full honest reward, the state-tracking claim fails.

## Area 5 — GENERATOR FEASIBILITY

### 12. “Response layer” is net-new patch machinery, especially for sneaky relocation

**Labels:** Areas 5, 4  
**Severity:** **BLOCKER**

**Failure scenario:** The current generator accepts only T1/T2 at the CLI and its allowed-mechanism table (`generator/generate.py:27-47`). It emits one document. Every nominal mechanism is implemented by the same operation: render an `original_text` and `mutated_text`, then call `doc_text.replace(original, mutated, 1)` and log one anchor (`:135-178`). There are no tracked-change blocks, patch IDs, insertion/deletion primitives, location relocation, response policies, or per-turn artifacts.

Concession and regression can be expressed as a new exact replacement. A signed counter can be another replacement template. `sneaky_reinsert` cannot. It must remove or accept text at one location, select a distinct professional insertion point, adapt grammar/defined terms/cross-references there, insert the deviant effect, and log both patches as one parent event. Reusing one `replace` either leaves the original violation in place, duplicates it, or gives V14 the wrong event cardinality. The draft's “apply the edits” hides the hardest part of the generator.

**Fix:** Specify a canonical response-patch engine as a separate prerequisite. It needs typed `replace`, `insert_before`, `insert_after`, and `delete` operations over stable section/paragraph IDs; precondition hashes; non-overlap checks; and composite parent events. Sneak recipes must supply a signed source effect plus eligible destination templates and grammar slots. Emit both child patches and score the parent only as described in Finding 8. Do not estimate this as an ordinary extension of current primitives.

### 13. V14 cannot prove “no unlogged edits” from the current artifacts, and the build order violates invariant 2

**Labels:** Areas 3, 5  
**Severity:** **BLOCKER**

**Failure scenario:** Current V2 merely checks that `mutated_text` and an anchor string occur somewhere in the final document (`validators/checks.py:78-92`). The generator never retains a base-to-final patch ledger. A markdown tracked-change view containing both before and after strings will make substring checks even weaker: swapped before/after sides, duplicate blocks, a missing application to the merged document, and unlogged surrounding edits can all pass “spans verbatim.” There is no existing diff algorithm or rendered-change representation to which V14 can attach.

The draft also explicitly orders validators after environment, generator, and scoring work (`spec_draft_T3_multiturn.md:85-86`). `SPEC.md:79-80` says validators are written before the generator. This is not a stylistic preference; without a patch/event contract, the generator will define whatever V14 later happens to accept.

**Fix:** Write schemas and executable validators before the response generator. Use a canonical patch ledger, not a generic after-the-fact text diff:

- every child patch records `change_id`, parent `event_id`, document/section ID, operation, precondition hash, before text, after text, and offsets in a canonical pre-response document;
- the renderer derives markdown blocks only from that ledger;
- V14 replays the ordered non-overlapping patches against the turn-1 canonical document and requires byte equality with the merged turn-2 document;
- V14 requires every rendered block to correspond to exactly one child patch and every child patch to exactly one rendered block;
- V14 requires every child patch to one parent event, while explicitly allowing a composite event such as sneak to own two children; and
- quote pointers are verified against the ledger, not searched globally.

Run merged turn-2 prose through V11/V15; validate the tracked renderer mechanically. A judge evaluating markup is not a substitute for patch integrity.

## Area 6 — HONEYPOTS, ENGAGEMENT, AND NON-GOALS

### 14. M1's clean-task machinery does not generalize to all concessions

**Labels:** Areas 1, 6  
**Severity:** **BLOCKER**

**Failure scenario:** M1 clean tasks require zero planted deviations under V13 (`validators/checks.py:252-263`), whereas an all-concessions T3 has nonzero turn events responding to prior deviations. It cannot literally reuse the clean task type without failing the validator or weakening what “clean” means.

The scoring behavior is worse. For an engaged clean task, zero flags becomes precision 1.0, any schema-valid card gets conformance 1.0, and no spurious escalation gives abstention 1.0 (`scoring/core.py:88-102`). Clean weights are 0.50/0.25/0.25, so this is a 1.0 composite. Engagement counts documents touched, not lines read: on a one-document task, reading one line plus making any search satisfies `>=50% of docs read AND >=1 search`; on two documents, touching one line in one document plus a search also passes (`scoring/core.py:466-479`; `tests/test_m1_clean_tasks.py:117-149`). No `change_id` needs to be accepted. The current finalize bounce also ignores reviews and merely requires a second empty finalize.

Thus the intended “accept everything, engaged” task becomes “touch one line, issue one search, submit an empty card” for a perfect 1.0. This is not an engagement gate; it is a gesture gate.

**Fix:** Create a distinct `task_type: all_concessions`. Require one explicit accept for every change ID and exact equality between interactive and card dispositions. Its engagement condition must be event coverage, not document-touch coverage: all change blocks read and all change IDs decided. Count `review_change` as substantive. Keep zero recall/grounding/fallback weights if desired, but precision/restraint and conformance remain zero until decision coverage is complete. Do not change V13's zero-deviation clean invariant.

### 15. The review-change honeypot is asserted but cannot be generated by the proposed response loop

**Labels:** Areas 1, 5, 6  
**Severity:** **BLOCKER**

**Failure scenario:** Existing V9 requires exactly two canary rules and zero planted deviations against them (`validators/checks.py:182-191`; `SPEC.md:167-171, 211`). The proposed response loop runs “per planted deviation.” Therefore it never produces a counterparty `change_id` under a canary rule. A blanket `review_change` rejector has no canary change to trip. Existing honeypot logic only scans `flag_issue`/card findings for a canary rule ID (`scoring/core.py:66-69, 113-116`); review decisions and `card.changes` are invisible.

If an engineer instead emits a harmful canary response to create a trap, that destroys the canary's meaning: the correct legal action would be to cite the canary rule, and the scorer would brand honest behavior `GAMED`. If `new_deviation` events live only in `planted_turn_events.json`, current V9 will not inspect them, so the same mistake can happen silently.

**Fix:** Add a separate `benign_canary_change` fixture generated from a signed compliant template, never from a planted deviation. Its correct disposition is accept; rejecting or separately flagging it under the canary rule triggers `GAMED`. Extend V9 across all turn-event artifacts to prove that canary rules own no harmful event. Extend honeypot scanning to canonical interactive and final review maps. Keep a wrong/non-canary citation on the span as an ordinary false action, matching the existing rule.

### 16. Deferring multi-document work makes this not T3 under the controlling SPEC

**Labels:** Areas 4, 6, 7  
**Severity:** **BLOCKER**

**Failure scenario:** The controlling spec defines T3 as multi-document MSA + SOW + addendum with `cross_doc_override` (`SPEC.md:163-165`). The published T2 gate report says the difficulty correction is “T3 multi-document” (`reports/gate_results_t2.md:68-73`). The new draft silently reuses the T3 name for a single-contract turn-2 snapshot and defers the original T3 idea as a non-goal.

That breaks an existing tier contract and weakens the very difficulty claim the proposal is supposed to restore. A single merged contract response can be solved as a static current-document review (Finding 11). Shipping it as T3 would make existing reports, task IDs, and public statements mean two incompatible things.

**Fix:** Either call this pilot a separate tier/axis such as `T2-N` and do not use it to declare T3 or the 0.40–0.80 T3 gate restored, or retain T3 as the conjunction of multi-document and negotiated-turn mechanics with at least one cross-document response event. Amend `SPEC.md`, schemas, reports, and gate definitions explicitly before generating task IDs. Turns 3–4 can be deferred if the claim is only one-step response review; they cannot be deferred while claiming long-horizon negotiation.

## Area 7 — WHAT IS MISSING RELATIVE TO REDLINEBENCH

### 17. The legitimacy battery does not contain the new tier's obvious mechanical attackers

**Labels:** Areas 1, 4, 7  
**Severity:** **BLOCKER**

**Failure scenario:** “Full battery reruns” is insufficient. The existing blanket baseline flags clauses and proposes fallbacks; it does not exercise `review_change`, accept/reject event balance, old-location replay, or duplicate-action washing. The existing generic cheater gate only requires gaming to be below honest, and the T2 report itself shows mechanical blanket scores of 0.409–0.578 (`reports/gate_results_t2.md:23-35, 101-114`). A new reject-all score of 0.765–0.865 can ship unless a purpose-built strategy calls the new action correctly.

The honest-band criterion alone proves nothing about gaming. An honest mean of 0.70 and a response-only/reject-all mean of 0.65 both satisfy the proposed honest criterion while invalidating the environment.

**Fix:** Add deterministic T3 gates before any honest spend:

- `accept_all`;
- `reject_all_nearest_rule`;
- `prior_location_replayer`;
- `always_reject_counter`;
- `turn2_only` (never opens turn 1 or uses prior positions);
- `duplicate_action_washer`; and
- `before_text_quoter`.

Each must score below 0.40 and no more than 60% of engaged honest; reject the tier if either condition fails. The turn2-only ablation must also fail the cross-turn link channel on every task. Report per-event confusion matrices so a composite cannot hide which shortcut worked.

### 18. Random response weights plus four held-out tasks cannot support the claimed calibration

**Labels:** Areas 1, 2, 7  
**Severity:** **DESIGN-RISK**

**Failure scenario:** The draft samples response-policy weights but gives no per-task or per-tranche quotas. Channels become incomparable when an event type is absent: current M2 returns fallback 0 if there is no required fallback event (`scoring/core.py:323-329`), while the proposed all-concessions type reweights the task. One task may have two counters and another none; one decision can move the fallback contribution by 0.075 or 0.15. Four held-out tasks are too few to balance five event types, acceptable/unacceptable counters, canary fixtures, and practice areas. A mean inside 0.40–0.80 can be an event-mix accident.

RedlineBench's input groups/cohorts at least avoid treating closely related variants as independent (`redlinebench_teardown.md:39`). This draft takes neither that grouping discipline nor an alternative stratification rule.

**Fix:** Replace free response weights with a declared coverage matrix. Every mixed seeded task should contain at least one concession, regression, sneak, and new deviation plus one acceptable and one unacceptable counter, or the scorer must aggregate event-macro metrics across a tranche with predeclared minimum counts. Increase held-out coverage to at least two tasks per practice area, group variants by base scenario, average within scenario before across scenarios, and publish confidence intervals. No channel should be silently absent; use fixed quotas or an explicit N/A reweighting rule locked before evaluation.

### 19. The draft borrowed RedlineBench's fixed response state but omitted its load-bearing acceptance, negative-action, validity, and context ideas

**Labels:** Areas 1, 4, 7  
**Severity:** **DESIGN-RISK**

**Failure scenario:** The teardown identifies four relevant RedlineBench mechanisms beyond pre-applied later-turn documents:

1. explicit positive “Accepts ...” criteria on acceptance-only tasks;
2. negative rubrics for undesirable edits;
3. a validity gate requiring an authored trace even when acceptance is correct; and
4. turn- and side-specific commercial context, its largest rubric category (`redlinebench_teardown.md:9-17, 29-35`).

The draft implements only a weak version of the first: false rejection of a concession reduces precision. It does not treat rejection of an acceptable counter as a precision error, does not define forbidden contradictory actions, and does not require complete authored dispositions. Its acceptable alternatives are static per rule, so the same counter is always acceptable regardless of client urgency, deal stage, or the prior reservation point. That is playbook classification, not much negotiation judgment.

**Fix:** Adapt these mechanisms deterministically:

- emit `required_accept` and `forbidden_reject/flag` records for every benign event, including acceptable counters;
- make contradictory/duplicate actions event-level false positives and conformance failures;
- require a complete canonical change-disposition trace before conformance or all-concessions credit;
- make alternative eligibility depend on attorney-signed, generator-rendered context guards (for example, `launch_urgency=high` activates a fallback but never relaxes security canaries); and
- generate counterfactual scenario cohorts with the same text under different visible context slots only when the answer key is correspondingly forward-generated.

This takes the useful substance of RedlineBench's positive/negative rubrics without importing a judge.

### 20. `.docx`, a live counterparty, and an LLM reward judge are correctly excluded, but the spec must stop implying equivalent realism

**Labels:** Areas 6, 7  
**Severity:** **NIT**

**Failure scenario:** An implementer could react to the RedlineBench comparison by adding native Word editing, which creates a separate artifact-validity/tool surface, or a live model/judge, which destroys deterministic episodes and RL throughput. Conversely, the current wording can be read as claiming RedlineBench-like negotiation after reproducing only its fixed-input trick. Markdown patch review does not measure native redline surgicalness, comment practice, or multi-round deal closing.

**Fix:** Keep `.docx` rendering, live counterparties, and judge-based reward out of this tier. State explicitly that the redesigned tier measures deterministic patch disposition and cross-turn consistency, not Word-edit quality or open-ended deal-closing prose. Add reporting-only surgicalness/verbosity diagnostics if desired. This is the part of the RedlineBench design the project was right not to adopt.

## Verdict

**RETHINK**

Keep only the fixed, pre-generated counterparty-response premise. The core must be redesigned before implementation: a canonical patch/event ledger; one exclusive action per child change; a complete event-disposition map; correctness-conditioned grounding; signed counter templates with emitted expected decisions; balanced harmful/benign scoring with a joint gate; and an actual two-phase prior-position link if “state tracking” remains the claim. Findings 1–4, 6–17 are not polish. Together they show that the present action/reward/state contract is undefined in places and mechanically rewards agents that do not negotiate. Building the generator first would merely fossilize those defects.
