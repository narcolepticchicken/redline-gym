# Held-Out Split Policy

Files under `tasks/heldout/` are reserved for formal evaluation only. They must
not be read by development tooling or humans during generator, validator,
baseline, prompt, or report iteration.

The split exists to preserve an untouched distribution slice. Development gates
must exclude it unless a formal eval protocol explicitly opts in and records
that access.

## Regeneration Log

- 2026-07-07: NDA T2 recipes were rewritten to remove grep-bot token leaks.
  Replaced stale `tasks/heldout/T2-NDA-201` with fresh seed
  `tasks/heldout/T2-NDA-203`. MSA held-out seed 202 was unchanged because MSA
  recipes did not change.
