# Held-Out Split Policy

Files under `tasks/heldout/` are reserved for formal evaluation only. They must
not be read by development tooling or humans during generator, validator,
baseline, prompt, or report iteration.

The split exists to preserve an untouched distribution slice. Development gates
must exclude it unless a formal eval protocol explicitly opts in and records
that access.

## Regeneration Log

- 2026-07-07: Crypto recipe QA removed the debatable Digital Assets
  entitlement deviation and retargeted the third distractor to an exact emitted
  span. Replaced stale crypto held-out seed
  `tasks/heldout/T2-CRYPTO-1601` with fresh seed
  `tasks/heldout/T2-CRYPTO-1602`.
- 2026-07-07: AI recipe QA removed the artificial
  `AI-R012-OMISSION-FINE-TUNE-EXPORT` deviation and added exact-once
  distractor span validation. Replaced stale AI held-out seed
  `tasks/heldout/T2-AI-1401` with fresh seed `tasks/heldout/T2-AI-1402`.
- 2026-07-07: Added customer-side digital-asset custody agreement held-out seed
  `tasks/heldout/T2-CRYPTO-1601` for `PB-CRYPTO-001` while adding the crypto
  law practice area.
- 2026-07-07: Added AI vendor/model services agreement held-out seed
  `tasks/heldout/T2-AI-1401` for `PB-AI-001` while adding the seventh
  practice area.
- 2026-07-07: Ruling A (fallback-as-floor) changed the clean MSA, DPA, and
  NDA generator bases and affected recipe originals. Replaced stale held-out
  seeds `tasks/heldout/T2-DPA-605`, `tasks/heldout/T2-MSA-602`, and
  `tasks/heldout/T2-NDA-601` with fresh incremented seeds
  `tasks/heldout/T2-DPA-606`, `tasks/heldout/T2-MSA-603`, and
  `tasks/heldout/T2-NDA-602`.
- 2026-07-07: Added buyer-side M&A asset purchase agreement held-out seed
  `tasks/heldout/T2-MA-1201` for `PB-MA-001` while adding the sixth practice
  area.
- 2026-07-07: GOV recipe mechanism labels were revised after QA tiebreak
  (`R-002` to `off_playbook_addition`, `R-007` to `direct_term_swap`).
  Replaced stale `tasks/heldout/T2-GOV-1001` with fresh seed
  `tasks/heldout/T2-GOV-1002`.
- 2026-07-07: Added corporate governance stockholders' agreement held-out seed
  `tasks/heldout/T2-GOV-1001` for `PB-GOV-001` while adding the fifth practice
  area.
- 2026-07-07: EMP missing-info M-001 was retargeted from equity approval
  process details inside the existing equity topic to the absent company-side
  treatment of golden-parachute and Section 280G change-in-control tax
  exposure. Replaced stale EMP held-out seed `tasks/heldout/T2-EMP-801` with
  fresh seed `tasks/heldout/T2-EMP-802`.
- 2026-07-07: Added employment executive agreement held-out seed
  `tasks/heldout/T2-EMP-801` for `PB-EMP-001` while extending the generator
  to the employment practice area.
- 2026-07-07: DPA missing-info M-002 was retargeted from an existing
  subprocessor-detail clause to the absent obligation for Vendor to maintain
  records of processing activities. Removed the stale DPA held-out seed
  `tasks/heldout/T2-DPA-604` and replaced it with fresh seed
  `tasks/heldout/T2-DPA-605`.
- 2026-07-07: DPA base and recipe templates were revised for the R2 register
  gate: defined terms now remain used after mutations, and vague time/quantity
  phrasing was replaced with bounded values. Replaced stale
  `tasks/heldout/T2-DPA-603` with fresh seed `tasks/heldout/T2-DPA-604`.
- 2026-07-07: Missing-info anchoring changed all three base/recipe families by
  requiring `context_anchor` and `match_keywords`, and appending each anchor to
  `client_context`. Deleted the prior held-out instances and reseeded the split
  with fresh T2 instances: `tasks/heldout/T2-NDA-601`,
  `tasks/heldout/T2-MSA-602`, and `tasks/heldout/T2-DPA-603`.
- 2026-07-07: Generator coherence, parameter sanity, and drafting-register
  fixes changed all three playbook recipe/base families. Deleted the prior
  held-out instances and reseeded the split with fresh T2 instances:
  `tasks/heldout/T2-NDA-501`, `tasks/heldout/T2-MSA-502`, and
  `tasks/heldout/T2-DPA-503`.
- 2026-07-07: NDA T2 recipes were rewritten to remove grep-bot token leaks.
  Replaced stale `tasks/heldout/T2-NDA-201` with fresh seed
  `tasks/heldout/T2-NDA-203`. MSA held-out seed 202 was unchanged because MSA
  recipes did not change.
- 2026-07-07: Added privacy DPA held-out seed `tasks/heldout/T2-DPA-401`
  for `PB-DPA-001` while adding the cybersecurity/privacy practice-area
  generator tranche.
- 2026-07-07: DPA recipes were revised after adjudication to remap the
  narrowed `Processing` definition deviation and remove an unanchored
  data-subject-categories missing-info item. Replaced stale
  `tasks/heldout/T2-DPA-401` with fresh seed `tasks/heldout/T2-DPA-402`.
