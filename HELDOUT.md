# Held-Out Split Policy

Files under `tasks/heldout/` are reserved for formal evaluation only. They must
not be read by development tooling or humans during generator, validator,
baseline, prompt, or report iteration.

The split exists to preserve an untouched distribution slice. Development gates
must exclude it unless a formal eval protocol explicitly opts in and records
that access.

