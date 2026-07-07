# Held-Out Split Policy

Files under `tasks/heldout/` are reserved for formal evaluation only. They must
not be read by development tooling or humans during generator, validator,
baseline, prompt, or report iteration.

The split exists to preserve an untouched distribution slice. Development gates
must exclude it unless a formal eval protocol explicitly opts in and records
that access.

## Regeneration Log

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
