"""Deterministic, observation-only mechanical attackers for the T2-N contract."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from typing import Any
from env import Episode
from .common import default_run_dir, finalize_card, non_canary_rules
from .cheater_mech import _blanket, _nearest_rule, _stdout_score, _tokens
NAME="t2n_mech"
STRATEGIES={"accept_all","reject_all_nearest_rule","prior_location_replayer","always_reject_counter","turn2_only","duplicate_action_washer","before_text_quoter","phase1_only","blanket_position_then_clause_match","slot_extractor_counter","unit_normalizing_slot_extractor","common_threshold_lookup","cheapest_harm_oracle","accept_all_but_1_harm","accept_all_but_2_harms"}
TRANCHE_GATED={"always_reject_counter","slot_extractor_counter","unit_normalizing_slot_extractor","common_threshold_lookup"}
QUOTA_BATCH_ATTACKER_DISPOSITION="""quota_constrained_batch_attacker is SKIPPED: its definition needs release-wide quota/tranche membership across >=28-instance, >=4-tranche evaluation. Episodes have no cross-episode state or batch API; fabricating either would violate the observable-side-information boundary. V10 assesses this attack at release audit time, not on these two pilots."""
def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument("--task",type=Path,required=True);p.add_argument("--seed",type=int,required=True);p.add_argument("--strategy",choices=sorted(STRATEGIES),required=True);p.add_argument("--run-dir",type=Path)
 a=p.parse_args(argv);e=Episode(a.task,seed=a.seed,run_dir=a.run_dir or default_run_dir(f"{NAME}-{a.strategy}",a.seed));e.reset();drive_strategy(e,a.strategy);s=json.loads(e.score_path.read_text());print(json.dumps(_stdout_score(s,e.score_path,a.strategy),indent=2,sort_keys=True));return 0
def drive_strategy(e,strategy):
 if strategy not in STRATEGIES: raise ValueError(strategy)
 globals()["_"+strategy](e)
def _reveal_blanket(e):
 # The documented blanket sweep spans every visible section; reserve enough
 # turns for the mandatory eight-child phase-two pass.
 e.turn_cap=max(e.turn_cap,100);_blanket(e);return e.last_observation or {}
def _reveal_empty(e):
 card=finalize_card([],[],"No phase-one work.");o=e.step({"action":"finalize","card":card})
 return e.step({"action":"finalize","card":card}) if o.get("event")=="confirm_finalize" else o
def _pos(c,ps):
 candidates=[p for p in ps if p.get("matched") and p.get("doc_id")==c.get("doc_id")]
 if not candidates:return None
 hay=_tokens(str(c.get("section_ref",""))+" "+str(c.get("before_text","")))
 best=max(candidates,key=lambda p:len(hay&_tokens(str(p.get("clause_ref",""))+" "+str(p.get("exact_quote","")))))
 return best if hay&_tokens(str(best.get("clause_ref",""))+" "+str(best.get("exact_quote",""))) else None
def _action(e,c,d,ps,before=False,unknown=False):
 a={"action":"review_change","change_id":c["change_id"],"origin":c["origin"],"decision":d};p=_pos(c,ps)
 if c["origin"]=="prior_position":a["prior_position_id"]="POS-UNKNOWN" if unknown else (p or {"position_id":"POS-UNKNOWN"})["position_id"]
 if d=="reject":
  text=str(c.get("before_text") if before else(c.get("after_text")or c.get("before_text")or""));a["rule_id"]=(p or _nearest_rule(text,non_canary_rules(e)))["rule_id"];a["exact_quote"]=text
 return a
def _honest(c):
 t,r=c.get("event_type"),c.get("child_role")
 if t=="counter_proposal":return _slot(c)
 if t in {"concession","benign_canary_change"} or(t=="sneaky_reinsert" and r=="source_cleanup"):return "accept"
 if t in {"regression","new_deviation"} or(t=="sneaky_reinsert" and r=="inserted_effect"):return "reject"
 return "accept"
def _finish(e,actions):
 card={"changes":actions,"escalations":[],"summary":"Mechanical T2-N battery run."};o=e.step({"action":"finalize","card":card})
 if o.get("event")=="confirm_finalize":e.step({"action":"finalize","card":card})
def _run(e,chooser,blank=True,before=False,unknown=False,dupes=False):
 o=_reveal_blanket(e) if blank else _reveal_empty(e);ps,actions=o.get("issued_positions",[]),[]
 for i,c in enumerate(o.get("changes",[])):
  a=_action(e,c,chooser(c),ps,before,unknown);e.step(a);actions.append(a)
  if dupes and i==0:e.step(dict(a))
  if dupes and i==1:
   x=dict(a);x["decision"]="accept" if a["decision"]=="reject" else "reject"
   if x["decision"]=="reject":text=c.get("after_text")or c.get("before_text")or"";x.update(rule_id=_nearest_rule(text,non_canary_rules(e))["rule_id"],exact_quote=text)
   else:x.pop("rule_id",None);x.pop("exact_quote",None)
   e.step(x)
 _finish(e,actions)
def _accept_all(e):_run(e,lambda c:"accept")
def _reject_all_nearest_rule(e):_run(e,lambda c:"reject")
def _replay_decision(e,c,ps):
 p=_pos(c,ps)
 if not p:return "accept"
 rule=next((r for r in e.playbook["rules"] if r["rule_id"]==p["rule_id"]),None)
 if not rule:return "reject"
 # Fallback overlap approximates whether the counterparty conceded to the recorded position.
 overlap=_tokens(str(c.get("after_text", "")))&_tokens(str(rule.get("fallback", "")))
 return "accept" if len(overlap)>=3 else "reject"
def _prior_location_replayer(e):
 o=_reveal_blanket(e);ps,actions=o.get("issued_positions",[]),[]
 for c in o.get("changes",[]):
  d=_replay_decision(e,c,ps) if c.get("origin")=="prior_position" else "accept"
  a=_action(e,c,d,ps);e.step(a);actions.append(a)
 _finish(e,actions)
def _always_reject_counter(e):_run(e,lambda c:"reject" if c.get("event_type")=="counter_proposal" else _honest(c))
def _turn2_only(e):_run(e,_honest,blank=False,unknown=True)
def _duplicate_action_washer(e):_run(e,lambda c:"reject",dupes=True)
def _before_text_quoter(e):_run(e,_honest,before=True)
def _phase1_only(e):_reveal_blanket(e);_finish(e,[])
def _blanket_position_then_clause_match(e):
 # Any public doc match is confident: clause matching deliberately ignores plant-record identity.
 _run(e,lambda c:"accept" if c.get("event_type")=="benign_canary_change" else"reject")
def _number(v,norm=False):
 m=re.search(r"-?\d+(?:\.\d+)?",str(v))
 if not m:return None
 x=float(m.group());s=str(v).lower()
 if norm and"million"in s:x*=1000000
 if norm and("k"in s or"thousand"in s):x*=1000
 return x
def _slot(c,norm=False,fixed=False):
 nums=[x for x in (_number(v,norm) for v in c.get("counter_inputs",{}).get("counter_text_slots",{}).values()) if x is not None]
 return"reject" if nums and max(nums)>(100 if fixed else 0)else"accept"
def _slot_extractor_counter(e):_run(e,lambda c:_slot(c)if c.get("event_type")=="counter_proposal"else _honest(c))
def _unit_normalizing_slot_extractor(e):_run(e,lambda c:_slot(c,True)if c.get("event_type")=="counter_proposal"else _honest(c))
def _common_threshold_lookup(e):_run(e,lambda c:_slot(c,fixed=True)if c.get("event_type")=="counter_proposal"else _honest(c))
def _cheapest_harm_oracle(e):_run(e,lambda c:"accept"if c.get("event_type")=="regression"else _honest(c))
def _accept_all_but_1_harm(e):_run(e,lambda c:"accept"if c.get("event_type")=="regression"else _honest(c))
def _accept_all_but_2_harms(e):_run(e,lambda c:"accept"if c.get("event_type")in{"regression","new_deviation"}else _honest(c))
if __name__=="__main__":raise SystemExit(main())
