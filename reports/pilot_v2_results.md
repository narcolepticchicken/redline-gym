# Training pilot round 2 — pod-trained QLoRA, same-lane eval (2026-07-11)

Setup: Qwen/Qwen3.5-9B + QLoRA (r=16, 4-bit NF4), 8 teacher-distilled
conversations (GLM/DeepSeek winners, ≥0.75 composite), trained 42s on a
rented A100 80GB. Merged and served via a transformers-direct server;
BOTH arms (tuned and untuned base) evaluated on the identical lane —
8 tasks, ONE deterministic episode per task per arm (greedy, temperature 0),
v2 union scoring.
SEEN = the 3 SFT-source tasks (contamination labeled, never pooled silently).

| task | base | tuned | delta | split |
|---|---:|---:|---:|---|
| T1-DPA-301 | 0.487 | 0.487 | +0.000 | unseen |
| T1-DPA-311 | 0.394 | 0.394 | +0.000 | unseen |
| T1-MSA-121 | 0.000 | 0.596 | +0.596 | unseen |
| T1-NDA-101 | 0.512 | 0.512 | +0.000 | unseen |
| T2-DPA-302 | 0.540 | 0.395 | −0.145 | SEEN |
| T2-EMP-702 | 0.320 | 0.343 | +0.023 | SEEN |
| T2-EMP-703 | 0.450 | 0.505 | +0.055 | unseen |
| T2-MSA-001 | 0.000 | 0.450 | +0.450 | SEEN |

**Unseen mean: 0.369 → 0.499 (+0.130). Seen mean: 0.287 → 0.396 (+0.109).
Overall: 0.338 → 0.460.**

Findings, stated plainly:
- The lift is real and transfers: the UNSEEN delta (+0.130) matches or beats
  the SEEN delta (+0.109) — this is not memorization of the training tasks.
- The mechanism is protocol conformance, again: the base model scores 0.000
  on two tasks by finalizing an empty card within 2 turns; the tuned model
  never zeros. Where the base already operates the protocol competently
  (three tasks with different transcripts but equal composites), the tiny
  adapter changes nothing.
- One regression, on a SEEN task: T2-DPA-302 drops 0.540 → 0.395 — a single
  unreplicated trajectory, same as every other cell in this table.
- Caveats: 8 training conversations; ONE greedy trajectory per cell (no
  sampling variance measured); single
  serving lane (transformers-direct, NOT comparable to GLM-lane or historical
  MLX numbers — the 0.374 figure from round 1 is a different lane and is not
  used here).

Cost, measured: ~10.5 A100-hours (single pod, created and terminated
2026-07-10/11). Most of that was idle overnight — the pipeline itself needs
~2 pod-hours (train 42s; each eval arm ~25-45 min; the rest was serving
debug: vLLM rejected the Qwen3.5 merged config on both backends, resolved
with a minimal transformers-direct server, runs_pod_eval/artifacts/serve_hf.py).
Adapter: adapters_pod/pilot_v2/ (local, untracked pending publication call).

## Correction (2026-07-11, same day — before anyone used these numbers)

The first version of this report claimed "3 seeds" per cell. That was false
replication: temperature-0 decoding with an episode seed that never reaches
the model API produced three byte-identical runs per cell (verified by
checksum). Every number above is a single deterministic trajectory. The
arithmetic is unchanged; the claimed statistical basis was wrong and is
withdrawn. Sampling-based replication (nonzero temperature, real seeds)
is future work before any of these deltas is called robust.

## Sampled rerun (2026-07-11 — real replication, temperature 0.7, n=3 per cell)

Rerun on a fresh pod with the defect fixed: per-request deterministic sampling
seeds (server --sampling-seed + request counter), temperature 0.7, three
GENUINELY distinct episodes per cell (verified: 0 duplicate transcripts across
all 48 cells by checksum).

| task | base (n=3, range) | tuned (n=3, range) | delta | split |
|---|---:|---:|---:|---|
| T1-DPA-301 | 0.258 ±0.44 | 0.604 ±0.56 | +0.346 | unseen |
| T1-DPA-311 | 0.490 ±0.29 | 0.416 ±0.37 | −0.073 | unseen |
| T1-MSA-121 | 0.000 ±0.00 | 0.318 ±0.57 | +0.318 | unseen |
| T1-NDA-101 | 0.348 ±0.57 | 0.454 ±0.35 | +0.106 | unseen |
| T2-DPA-302 | 0.462 ±0.15 | 0.398 ±0.33 | −0.064 | SEEN |
| T2-EMP-702 | 0.320 ±0.00 | 0.318 ±0.16 | −0.002 | SEEN |
| T2-EMP-703 | 0.368 ±0.58 | 0.425 ±0.15 | +0.057 | unseen |
| T2-MSA-001 | 0.000 ±0.00 | 0.098 ±0.29 | +0.098 | SEEN |

**Unseen: 0.293 → 0.444 (+0.151). Seen: 0.261 → 0.271 (+0.010). All: 0.281 → 0.379.**

Read plainly:
- Per-cell ranges are enormous (up to ±0.58 at n=3): no single-task delta in
  this table is individually robust. The defensible finding is the aggregate:
  the unseen-task lift appears under BOTH decoding regimes (+0.130 greedy,
  +0.151 sampled) and in 4 of 5 unseen tasks.
- The SEEN-task lift from the greedy table (+0.109) DISAPPEARS under sampling
  (+0.010). The tuned model's advantage on its own training-source tasks is
  not robust; the transfer signal is stronger than the memorization signal.
- The protocol-collapse mechanism persists under sampling: base scores 0.000
  on the same two tasks in every sample (empty finalize without reading).
- Both tables stand: greedy = deterministic point estimates; sampled = the
  variance picture. Neither alone would have been honest.

Cost, measured: second pod ~1.5 A100-hours (created and terminated same
morning). Cumulative pilot round 2: ~12 A100-hours.
