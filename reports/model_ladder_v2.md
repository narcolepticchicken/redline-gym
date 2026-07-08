# Model ladder — v0.2 union scoring, deterministic (no judge tiebreak), 2026-07-08

Same driver, same 3 T2 gate tasks, temperature 0. GLM n=15 (5 seeds, bounce
harness); others n=9 (3 seeds).

| Model | Mean composite | Distribution |
|---|---:|---|
| GLM-5.2 | 0.843 | 0.55–1.00, no zeros |
| DeepSeek v4-pro | 0.702 | 0.52–0.87, no zeros |
| MiniMax-M3 | 0.640 | two 0.1 outliers, engaged 0.70–0.85 |
| DeepSeek v4-flash | 0.583 | one 0.0, wide spread |
| Qwen3.5-9B-4bit (local, 1 smoke episode) | 0.39 | pilot baseline pending |

Cleanest capability claim (same family, same everything else):
**v4-pro 0.702 > v4-flash 0.583** — the environment separates a stronger
model from its weaker sibling. Cross-family ordering reported as measured
without a ground-truth strength ranking. Rankings usage measured: 858,352
tokens across the three API arms.
