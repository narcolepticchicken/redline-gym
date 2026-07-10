#!/usr/bin/env python3
"""Build the deterministic draft T2-N tranche and write its only report artifacts."""
from __future__ import annotations
import json, shutil
from collections import defaultdict
from pathlib import Path
from tempfile import TemporaryDirectory
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from baselines.t2n_mech import STRATEGIES, TRANCHE_GATED, drive_strategy
from env import Episode
from generator.t2n_all_concessions import generate_all_concessions
from generator.t2n_response import ResponseGenerationError, generate_response
from scoring.t2n_contract import all_concessions_share_compliant, gated_tranche_composite, tranche_counter_metrics
from validators.t2n_checks import (FORBIDDEN_LEAKAGE_FIELDS, run_all_t2n, v10_t2n_forbidden_fields,
    v10_t2n_lookup_classifiers, v10_t2n_permutation_mi, v10_t2n_quota_batch_attacker, v9_ext_t2n_canary_turn_events)

AREAS={
 "ai":("ai.json","PB-AI-001",["T2-AI-1302","T2-AI-1303"]), "crypto":("crypto.json","PB-CRYPTO-001",["T2-CRYPTO-1502","T2-CRYPTO-1503"]),
 "privacy":("privacy.json","PB-DPA-001",["T2-DPA-302","T2-DPA-303","T2-DPA-312"]), "employment":("employment.json","PB-EMP-001",["T2-EMP-702","T2-EMP-703","T2-EMP-712"]),
 "governance":("governance.json","PB-GOV-001",["T2-GOV-902","T2-GOV-903","T2-GOV-912"]), "ma":("ma.json","PB-MA-001",["T2-MA-1102","T2-MA-1103"]),
 "contracts":("contracts.json",None,["T2-MSA-104","T2-MSA-106","T2-MSA-122","T2-NDA-102","T2-NDA-112"]),}
PILOTS={"T2-DPA-302":("T2N-DPA-302-S7302",7302),"T2-MSA-104":("T2N-MSA-104-S4104",4104)}
ALL={"ai":("T2-AI-1302",9001),"employment":("T2-EMP-702",9002),"governance":("T2-GOV-902",9003)}
PRED={"accept_all":0,"reject_all_nearest_rule":0,"prior_location_replayer":.2,"always_reject_counter":0,"turn2_only":0,"duplicate_action_washer":0,"before_text_quoter":0,"phase1_only":0,"blanket_position_then_clause_match":0,"slot_extractor_counter":0,"unit_normalizing_slot_extractor":0,"common_threshold_lookup":0,"cheapest_harm_oracle":.2,"accept_all_but_1_harm":.2,"accept_all_but_2_harms":.2}

def load(p): return json.loads(Path(p).read_text())
def combine(base, overlay, target):
 if target.exists(): shutil.rmtree(target)
 shutil.copytree(ROOT/'tasks/generated'/base,target); shutil.copytree(ROOT/'tasks/t2n_draft'/overlay,target,dirs_exist_ok=True)
def phase1(ep, task):
 planted=load(task/'planted_deviations.json'); issues=[]
 for d in planted['deviations']:
  a={'action':'flag_issue','rule_id':d['rule_id'],'doc_id':d['doc_id'],'clause_ref':'matched clause','exact_quote':d['mutated_text'],'proposed_redline':d['expected_redline_text']}; ep.step(a); issues.append({k:v for k,v in a.items() if k!='action'})
 missing=planted['missing_info'][0]; esc={'topic':missing['topic'],'reason':missing['topic']}; ep.step({'action':'escalate',**esc})
 return ep.step({'action':'finalize','card':{'issues':issues,'escalations':[esc],'summary':'complete'}})
def honest(task, run):
 ep=Episode(task,seed=0,run_dir=run); ep.reset(); reveal=phase1(ep,task); acts=[]
 for p in load(task/'patch_ledger.json')['patches']:
  a={'action':'review_change','change_id':p['change_id'],'origin':p['origin'],'decision':p['expected_disposition']}
  if p['origin']=='prior_position': a['prior_position_id']='POS-'+p['prior_source_deviation_id'].replace('-',''); a['rule_id']=p['expected_rule_id']
  if p['expected_disposition']=='reject': a.update(rule_id=p['expected_rule_id'],exact_quote=p['ground_span'])
  if p.get('expected_redline_text') and p['expected_disposition']=='reject': a['proposed_redline']=p['expected_redline_text']
  ep.step(a); acts.append(a)
 ep.step({'action':'finalize','card':{'changes':acts,'escalations':[],'summary':'complete'}})
 return load(ep.score_path), reveal
def public_records(label, area, task, ordinal):
 events={e['event_id']:e for e in load(task/'turn_events.json')['events']}; out=[]
 for event_ord,p in enumerate(load(task/'patch_ledger.json')['patches']):
  if p['event_type']!='counter_proposal': continue
  inp=events[p['event_id']]['counter_inputs']; out.append({'label':p['counter_class'],'counter_text_slots':inp['counter_text_slots'],'phase1_context_slots':inp['phase1_context_slots'],'decoy_values':inp['decoy_values'],'task_ordinal':ordinal,'event_ordinal':event_ord,'section_bucket':p['section_ref'],'playbook_rule':p['expected_rule_id'],'family_split':p['counter_family_id'],'observation':{'counter_text_slots':inp['counter_text_slots'],'phase1_context_slots':inp['phase1_context_slots'],'decoy_values':inp['decoy_values']},'public_task_id':label})
 return out

def main():
 inventory=[]; generated=[]
 # exact overlap inventory is derived from base planted rules and applicable family rules.
 for area,(family,playbook,bases) in AREAS.items():
  families=load(ROOT/'generator/t2n_families'/family); 
  for base in bases:
   planted=load(ROOT/'tasks/generated'/base/'planted_deviations.json')['deviations']; eligible=all(d.get('expected_action')=='redline_with_fallback' and d.get('expected_redline_text') for d in planted) and len(planted)==5
   if not eligible: reason=('one seeded deviation has expected_action=escalate, not redline_with_fallback' if base=='T2-NDA-102' else 'wrong deviation count/type (T2-N requires five redline_with_fallback deviations)')
   else:
    pb=playbook or load(ROOT/load(ROOT/'tasks/generated'/base/'task.json')['playbook_ref'])['playbook_id']
    rules={f['rule_id'] for f in families[pb]['counter_families']}; n=len({d['rule_id'] for d in planted}&rules)
    reason='usable: two counter-family rule matches' if n>=2 else f'only {n} counter-family rule match(es); needs two'
   inventory.append({'area':area,'base':base,'mixed_eligible':reason.startswith('usable'), 'reason':reason,'mixed_instances':0,'all_concessions':False})
 # pilots plus thirteen new deterministic seeds on each usable base = 28.
 for base,area,family in [('T2-DPA-302','privacy','privacy.json'),('T2-MSA-104','contracts','contracts.json')]:
  label,seed=PILOTS[base]; generated.append({'label':label,'base':base,'area':area,'seed':seed,'kind':'mixed','existing_pilot':True})
  for seed in range(1,14):
   label=f"T2N-{base[3:]}-S{seed}"; out=ROOT/'tasks/t2n_draft'/label
   generate_response(ROOT/'tasks/generated'/base,seed,ROOT/'generator/t2n_families'/family,out)
   generated.append({'label':label,'base':base,'area':area,'seed':seed,'kind':'mixed','existing_pilot':False})
 for area,(base,seed) in ALL.items():
  label=f"T2N-{base[3:]}-AC-S{seed}"; generate_all_concessions(ROOT/'tasks/generated'/base,seed,ROOT/'tasks/t2n_draft'/label)
  generated.append({'label':label,'base':base,'area':area,'seed':seed,'kind':'all_concessions','existing_pilot':False})
 for row in inventory:
  row['mixed_instances']=sum(g['kind']=='mixed' and g['base']==row['base'] for g in generated); row['all_concessions']=any(g['kind']=='all_concessions' and g['base']==row['base'] for g in generated)
 mixed=[g for g in generated if g['kind']=='mixed']; counters=[]; episodes=[]; battery=defaultdict(list); gamed=defaultdict(int)
 with TemporaryDirectory(prefix='t2n-tranche-') as tmp:
  tmp=Path(tmp)
  for ordinal,g in enumerate(mixed):
   task=tmp/g['label']; combine(g['base'],g['label'],task); score,reveal=honest(task,tmp/'honest'/g['label']); episodes.append({'children':score['telemetry']['children'],'E':score['E']})
   counters += public_records(g['label'],g['area'],task,ordinal)
   public={'observation':{'changes':reveal['changes']},'public_task_id':g['label']}
   assert v10_t2n_forbidden_fields([public]).status=='PASS'
   assert all(not (FORBIDDEN_LEAKAGE_FIELDS & set(c)) for c in reveal['changes'])
   assert all(r.status=='PASS' for r in run_all_t2n(ROOT/'tasks/t2n_draft'/g['label']))
   for strategy in STRATEGIES:
    e=Episode(task,seed=0,run_dir=tmp/'battery'/strategy/g['label']); e.reset(); drive_strategy(e,strategy); s=load(e.score_path); battery[strategy].append(s['composite']); gamed[strategy]+=s['status']=='GAMED'
  # all-concession episode checks use the same real environment fixture.
  all_checks=[]
  for g in (x for x in generated if x['kind']=='all_concessions'):
   task=tmp/g['label']; combine(g['base'],g['label'],task); score,_=honest(task,tmp/'all'/g['label']); all_checks.append({'label':g['label'],'composite':score['composite'],'gate_pass':score['gate_pass']})
 folds=[[] for _ in range(4)]
 for i,r in enumerate(counters): folds[i%4].append(r)
 features=['task_ordinal','event_ordinal','section_bucket','playbook_rule','family_split']
 lookup=v10_t2n_lookup_classifiers(folds,features); mi=v10_t2n_permutation_mi(counters,['task_ordinal','event_ordinal','section_bucket']); quota=v10_t2n_quota_batch_attacker(counters,quota={'acceptable':28,'unacceptable':28})
 metrics=tranche_counter_metrics(episodes); gate=gated_tranche_composite([{'E':s['E']} for s in episodes],metrics)
 # tranche-gated strategies recompute real counters from their episode telemetry
 tranche_strategy={}
 for strategy in TRANCHE_GATED:
  # Drive results above are not retained; derive each batch's counter decisions via a second deterministic run.
  child_episodes=[]
  for g in mixed:
   task=tmp/g['label']; combine(g['base'],g['label'],task); e=Episode(task,seed=0,run_dir=tmp/'tranche'/strategy/g['label']);e.reset();drive_strategy(e,strategy); child_episodes.append(load(e.score_path))
  child_episodes=[{'children':x['telemetry']['children'],'E':x['E']} for x in child_episodes]
  m=tranche_counter_metrics(child_episodes); tranche_strategy[strategy]={'metrics':m,'gated':gated_tranche_composite([{'E':x['E']} for x in child_episodes],m)}
 rows=[{'strategy':s,'predicted':PRED[s],'min':min(battery[s]),'mean':sum(battery[s])/len(battery[s]),'max':max(battery[s]),'gamed_count':gamed[s],'tranche_gated':s in TRANCHE_GATED,'tranche_result':tranche_strategy.get(s)} for s in sorted(STRATEGIES)]
 manifest={'mixed_count':len(mixed),'acceptable_count':sum(r['label']=='acceptable' for r in counters),'unacceptable_count':sum(r['label']=='unacceptable' for r in counters),'all_concessions_count':3,'instances':generated,'inventory':inventory,'all_concession_episode_checks':all_checks,'all_concessions_compliant':all_concessions_share_compliant(len(mixed),3),'all_concessions_four_compliant':all_concessions_share_compliant(len(mixed),4),'counter_records':counters}
 (ROOT/'reports/t2n_tranche_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 report={'banner':'DRAFT-INSTANCES / UNSIGNED-FAMILIES — machine-drafted, model-reviewed families; not a release gate.','manifest':'reports/t2n_tranche_manifest.json','strategy_rows':rows,'v10_lookup':lookup._asdict() if hasattr(lookup,'_asdict') else lookup.__dict__,'v10_permutation_mi':mi.__dict__,'v10_quota_batch_attacker':quota.__dict__,'counter_macro_gate':{'metrics':metrics,'gated':gate},'all_concessions':all_checks,'inventory':inventory}
 (ROOT/'reports/t2n_draft_gates.json').write_text(json.dumps(report,indent=2)+'\n')
 lines=[f"# {report['banner']}",'','## Base inventory (structural authoring-coverage finding)','', '| Area | Base | Mixed eligible | Reason | Mixed generated | All-concessions |','|---|---|---|---|---:|---|']
 lines += [f"| {r['area']} | {r['base']} | {r['mixed_eligible']} | {r['reason']} | {r['mixed_instances']} | {r['all_concessions']} |" for r in inventory]
 lines += ['','## Mechanical battery','', '| Strategy | Predicted | Min | Mean | Max (worst) | GAMED | Cause |','|---|---:|---:|---:|---:|---:|---|']
 for r in rows: lines.append(f"| {r['strategy']} | {r['predicted']:.6f} | {r['min']:.6f} | {r['mean']:.6f} | {r['max']:.6f} | {r['gamed_count']} | {'TRANCHE-GATED: '+json.dumps(r['tranche_result']) if r['tranche_gated'] else 'Measured across 28 mixed draft instances.'} |")
 lines += ['', '## Tranche statistical gates','', '```json',json.dumps({'lookup':report['v10_lookup'],'permutation_mi':report['v10_permutation_mi'],'quota_batch_attacker':report['v10_quota_batch_attacker'],'counter_macro_gate':report['counter_macro_gate']},indent=2),'```','',f"All concessions: {all_checks}; 9*3 <= {len(mixed)} is {manifest['all_concessions_compliant']}; 9*4 <= {len(mixed)} is {manifest['all_concessions_four_compliant']}."]
 (ROOT/'reports/t2n_draft_gates.md').write_text('\n'.join(lines)+'\n')
if __name__=='__main__': main()
