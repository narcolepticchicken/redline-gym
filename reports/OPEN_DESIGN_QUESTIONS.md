# Open design questions — require Aaron's ruling (2026-07-07)

These define ground truth. Not decided autonomously on principle: the system
exists to be lawyer-verifiable, so a lawyer sets the bar.

## Q1 — The compliance bar: position or fallback-as-floor?

Every rule has a `position` (the client's stance) and a `fallback` (the edit
the AI should propose). V3 currently treats text weaker than the fallback as a
violation even when it arguably satisfies the position. Concrete cases from
tonight's adjudicated audit (reports/answer_key_defects.md):

- MSA base, R-005: "Vendor will process Customer Data only to provide and
  support the services, to comply with Customer's documented instructions,
  and as otherwise expressly authorized in an Order Form." Weaker than the
  documented-instructions-only fallback. Violation, or acceptable drafting?
- DPA base, R-005: base samples a 72-hour breach-notice bound; fallback says
  48. Is 72 a defect in a *clean* base, or within the position's tolerance?
- MSA base, R-007: initial term not expressly capped at one year, renewal
  controls present. Violation of the no-auto-renewal rule, or compliant?

**Option A (fallback-as-floor):** mechanical, unambiguous, machine-checkable —
but flags realistic-but-looser drafting as defective, and clean bases must
match fallbacks nearly verbatim (less natural variety).
**Option B (position, judged):** legally truer, but reintroduces judge
discretion into ground truth — the thing this project exists to avoid.
**Option C (explicit per-rule bounds):** each rule carries machine-checkable
compliance bounds (e.g. breach notice: compliant range ≤72h, fallback 48h)
authored at red-pen time. Most work; keeps determinism AND legal nuance.

Recommendation: C, applied rule-by-rule during your playbook red-pens.
Until ruled: V3 results carry an asterisk; generation continues, no instance
graduates to "verified" on V3 alone.

## Q2 — Confirmed answer-key omissions policy

The adjudicated audit confirmed shipped docs contain genuine violations not in
any answer key (e.g. one-sided indemnity in the MSA docs, R-002). An honest
agent flagging them is scored a false-flagger today. Options: add them to keys
as planted-equivalent findings; fix the base so they don't exist; or a
"defensible extras" list that precision ignores. Recommendation: fix bases for
tranche instances (defects live in templates), keys stay exhaustive.

## Q3 — V4 detectability threshold

Reported gates currently: T1 = 100% of planted findable by the round-trip
reader, T2 ≥ 60%. 60% is my number, not a principled one. Where should the
bar sit for "a competent reader could find this" on the subtle tier?

## Status dependencies

- Judge reliability fix (multi-sample median/spread) — in flight, code-only.
- Everything else tonight (13 dev instances, 3 areas, gates harness,
  adjudication loop) stands regardless of these rulings; the rulings decide
  what "clean" and "detectable" mean before instances are called verified.
