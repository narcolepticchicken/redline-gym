#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
RUN_DIR="runs/t2n_gates"
if [[ "${1:-}" == "--run-dir" ]]; then RUN_DIR="$2"; fi
python3 -m pytest -q
RUN_DIR="$RUN_DIR" python3 - <<'PY'
from __future__ import annotations
import json, os, shutil
from pathlib import Path
from baselines.t2n_mech import STRATEGIES, TRANCHE_GATED, QUOTA_BATCH_ATTACKER_DISPOSITION, drive_strategy
from env import Episode
root=Path.cwd(); run=root/os.environ["RUN_DIR"]; run.mkdir(parents=True,exist_ok=True)
pilots={"T2N-DPA-302-S7302":("T2-DPA-302","T2N-DPA-302-S7302"),"T2N-MSA-104-S4104":("T2-MSA-104","T2N-MSA-104-S4104")}
tasks={}
for label,(base,overlay) in pilots.items():
 target=run/"combined_tasks"/label
 if target.exists(): shutil.rmtree(target)
 shutil.copytree(root/"tasks/generated"/base,target); shutil.copytree(root/"tasks/t2n_draft"/overlay,target,dirs_exist_ok=True); tasks[label]=target
pred={"accept_all":0,"reject_all_nearest_rule":0,"prior_location_replayer":.2,"always_reject_counter":0,"turn2_only":0,"duplicate_action_washer":0,"before_text_quoter":0,"phase1_only":0,"blanket_position_then_clause_match":0,"slot_extractor_counter":0,"unit_normalizing_slot_extractor":0,"common_threshold_lookup":0,"cheapest_harm_oracle":.2,"accept_all_but_1_harm":.2,"accept_all_but_2_harms":.2}
rows=[]
for s in sorted(STRATEGIES):
 row={"strategy":s,"predicted":pred[s],"tranche_gated":s in TRANCHE_GATED,"pilots":{}}
 for label,task in tasks.items():
  e=Episode(task,seed=0,run_dir=run/s/label);e.reset();drive_strategy(e,s);score=json.loads(e.score_path.read_text())
  phase1=e.phase1_result or {};recall=phase1.get("channels",{}).get("recall")
  positions=e.phase1_positions;matched=sum(bool(p.get("matched")) for p in positions);deviations=round(matched/recall) if recall else 0
  row["pilots"][label]={"composite":score["composite"],"status":score["status"],"family_ok":score.get("harm_integrity"),"transcript_path":str(e.transcript_path),"blanket_recall":recall,"matched_positions":matched,"deviation_count":deviations}
 rows.append(row)
reports=root/"reports";reports.mkdir(exist_ok=True)
(reports/"t2n_draft_gates.json").write_text(json.dumps({"rows":rows,"quota_constrained_batch_attacker":QUOTA_BATCH_ATTACKER_DISPOSITION},indent=2)+"\n")
lines=["# DRAFT-INSTANCES / UNSIGNED-FAMILIES — pilots derive from machine-drafted families, not attorney-signed playbooks; not a release gate.","","| Strategy | DPA composite | MSA composite | GAMED | family_ok / harm_integrity | v4 predicted C8 | Delta (measured − predicted) | Cause |","|---|---:|---:|---|---|---:|---|---|"]
f=lambda x:f"{x:.6f}"
for r in rows:
 d,m=r["pilots"]["T2N-DPA-302-S7302"],r["pilots"]["T2N-MSA-104-S4104"]
 def recall(p):
  return f"{p['blanket_recall']:.1f} ({p['matched_positions']}/{p['deviation_count']} deviations matched)"
 cause="TRANCHE-GATED — not assessable on two pilots." if r["tranche_gated"] else ("Matches contract prediction." if all(abs(p["composite"]-r["predicted"])<1e-9 for p in r["pilots"].values()) else (f"blanket phase-1 recall: DPA={recall(d)}; MSA={recall(m)}; L floor fails (continuity requires exact-tuple matches on matched positions only), zeroing P2 regardless of phase-2 disposition correctness — not a driver defect." if r["predicted"]==.2 else "Pilot-specific mechanical baseline result."))
 lines.append(f"| {r['strategy']}{' (TRANCHE-GATED)' if r['tranche_gated'] else ''} | {f(d['composite'])} | {f(m['composite'])} | DPA={d['status']=='GAMED'}; MSA={m['status']=='GAMED'} | DPA={d['family_ok']}; MSA={m['family_ok']} | {f(r['predicted'])} | DPA={f(d['composite']-r['predicted'])}; MSA={f(m['composite']-r['predicted'])} | {cause} |")
lines += ["",f"| quota_constrained_batch_attacker (SKIPPED) | — | — | — | — | 0.000000 | — | {QUOTA_BATCH_ATTACKER_DISPOSITION} |", "", "## Quota-constrained batch attacker", "", QUOTA_BATCH_ATTACKER_DISPOSITION, ""]
(reports/"t2n_draft_gates.md").write_text("\n".join(lines))
defects=[(r,l,p) for r in rows if not r["tranche_gated"] for l,p in r["pilots"].items() if p["composite"]>=.4]
raise SystemExit(1 if defects else 0)
PY
