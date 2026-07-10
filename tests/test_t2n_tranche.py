from __future__ import annotations
import json, shutil
from pathlib import Path
import pytest
from env import Episode
from generator.t2n_all_concessions import generate_all_concessions
from scoring.t2n_contract import all_concessions_share_compliant
from validators.t2n_checks import run_all_t2n, v10_t2n_quota_batch_attacker, v9_ext_t2n_canary_turn_events

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=json.loads((ROOT/'reports/t2n_tranche_manifest.json').read_text())

def combine(tmp, item):
 target=tmp/item['label']; shutil.copytree(ROOT/'tasks/generated'/item['base'],target); shutil.copytree(ROOT/'tasks/t2n_draft'/item['label'],target,dirs_exist_ok=True); return target
def phase1(ep, task):
 planted=json.loads((task/'planted_deviations.json').read_text()); issues=[]
 for d in planted['deviations']:
  a={'action':'flag_issue','rule_id':d['rule_id'],'doc_id':d['doc_id'],'clause_ref':'matched clause','exact_quote':d['mutated_text'],'proposed_redline':d['expected_redline_text']};ep.step(a);issues.append({k:v for k,v in a.items() if k!='action'})
 m=planted['missing_info'][0]; esc={'topic':m['topic'],'reason':m['topic']};ep.step({'action':'escalate',**esc});return ep.step({'action':'finalize','card':{'issues':issues,'escalations':[esc],'summary':'x'}})
def actions(task):
 out=[]
 for p in json.loads((task/'patch_ledger.json').read_text())['patches']:
  a={'action':'review_change','change_id':p['change_id'],'origin':p['origin'],'decision':'accept','prior_position_id':'POS-'+p['prior_source_deviation_id'].replace('-',''),'rule_id':p['expected_rule_id']};out.append(a)
 return out

def test_tranche_shape_and_inventory():
 assert MANIFEST['mixed_count'] >= 28 and MANIFEST['acceptable_count'] == MANIFEST['unacceptable_count'] >= 28
 assert MANIFEST['all_concessions_count'] == 3
 assert all_concessions_share_compliant(MANIFEST['mixed_count'],3) and not all_concessions_share_compliant(MANIFEST['mixed_count'],4)
 by_area={a:sum(r['mixed_instances'] for r in MANIFEST['inventory'] if r['area']==a) for a in ('privacy','contracts','ai','crypto','employment','governance','ma')}
 assert all(by_area[a] == 4 for a in by_area)
 assert {x['area'] for x in MANIFEST['instances'] if x['kind']=='all_concessions'} == {'ai','employment','governance'}

def test_sampled_validators_and_all_concessions_episode(tmp_path):
 mixed=next(x for x in MANIFEST['instances'] if x['kind']=='mixed'); fixture=ROOT/'tasks/t2n_draft'/mixed['label']
 events=json.loads((fixture/'turn_events.json').read_text()); canary={c['rule_id'] for e in events['events'] if e['event_type']=='benign_canary_change' for c in e['children']}
 assert all(x.status=='PASS' for x in run_all_t2n(fixture)); assert v9_ext_t2n_canary_turn_events(events,canary).status == 'PASS'
 all_item=next(x for x in MANIFEST['instances'] if x['kind']=='all_concessions'); task=combine(tmp_path,all_item)
 ep=Episode(task,run_dir=tmp_path/'ok');ep.reset();phase1(ep,task); a=actions(task)
 for x in a: ep.step(x)
 ep.step({'action':'finalize','card':{'changes':a,'escalations':[],'summary':'x'}}); assert json.loads(ep.score_path.read_text())['composite']==1.0
 ep=Episode(task,run_dir=tmp_path/'bad');ep.reset();phase1(ep,task); ep.step({'action':'finalize','card':{'changes':[],'escalations':[],'summary':'x'}});ep.step({'action':'finalize','card':{'changes':[],'escalations':[],'summary':'x'}}); assert json.loads(ep.score_path.read_text())['composite']==0.0

def test_quota_attacker_is_deterministic_and_backward_compatible():
 records=MANIFEST['counter_records']; quota={'acceptable':MANIFEST['acceptable_count'],'unacceptable':MANIFEST['unacceptable_count']}
 assert v10_t2n_quota_batch_attacker(records,quota=quota) == v10_t2n_quota_batch_attacker(records,quota=quota)
 for heuristic in ('max_slot_value','min_slot_value','sum_slots','mean_slots','single_threshold_per_slot','single_slot_logistic'):
  result=v10_t2n_quota_batch_attacker(records,quota=quota,heuristic=heuristic)
  assert result.status == 'PASS'
  score=float(result.detail.split('balanced accuracy=',1)[1].split(';',1)[0])
  assert score < .60
 with pytest.raises(NotImplementedError,match='item 4'): v10_t2n_quota_batch_attacker()

def test_all_concession_generator_is_byte_deterministic(tmp_path):
 a,b=tmp_path/'a',tmp_path/'b'; base=ROOT/'tasks/generated/T2-AI-1302';generate_all_concessions(base,1,a);generate_all_concessions(base,1,b)
 assert {p.name:p.read_bytes() for p in a.iterdir()} == {p.name:p.read_bytes() for p in b.iterdir()}
