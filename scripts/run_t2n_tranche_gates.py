#!/usr/bin/env python3
"""Build the deterministic v2 T2-N draft tranche and its report artifacts."""
from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from baselines.t2n_mech import STRATEGIES, TRANCHE_GATED, drive_strategy
from env import Episode
from generator.t2n_all_concessions import generate_all_concessions
from generator.t2n_response import generate_response
from scoring.t2n_contract import (
    all_concessions_share_compliant,
    gated_tranche_composite,
    tranche_counter_metrics,
)
from validators.t2n_checks import (
    FORBIDDEN_LEAKAGE_FIELDS,
    run_all_t2n,
    v10_t2n_forbidden_fields,
    v10_t2n_lookup_classifiers,
    v10_t2n_permutation_mi,
    v10_t2n_quota_batch_attacker,
    v9_ext_t2n_canary_turn_events,
)


AREAS = {
    "ai": ("ai.json", ["T2-AI-1302", "T2-AI-1303"]),
    "crypto": ("crypto.json", ["T2-CRYPTO-1502", "T2-CRYPTO-1503"]),
    "privacy": ("privacy.json", ["T2-DPA-302", "T2-DPA-303", "T2-DPA-312"]),
    "employment": ("employment.json", ["T2-EMP-702", "T2-EMP-703", "T2-EMP-712"]),
    "governance": ("governance.json", ["T2-GOV-902", "T2-GOV-903", "T2-GOV-912"]),
    "ma": ("ma.json", ["T2-MA-1102", "T2-MA-1103"]),
    "contracts": ("contracts.json", ["T2-MSA-104", "T2-MSA-106", "T2-MSA-122", "T2-NDA-102", "T2-NDA-112"]),
}
AREA_ORDER = tuple(AREAS)
# Private, deterministic seed manifest chosen from successful base/seed layouts
# to balance route codes and visible event/section/family cells. Seeds and the
# search attempt are not included in episode observations.
MIXED_SEEDS = {
    "ai": [21238, 21171, 21308, 21139],
    "crypto": [21287, 21305, 21255, 21239],
    "privacy": [21302, 21405, 21474, 21237],
    "employment": [21623, 21403, 21523, 21575],
    "governance": [21689, 21554, 21640, 21471],
    "ma": [21687, 21637, 21502, 21707],
    "contracts": [21634, 21788, 21670, 21756],
}
ALL_CONCESSIONS = {
    "ai": ("T2-AI-1302", 29001),
    "employment": ("T2-EMP-702", 29002),
    "governance": ("T2-GOV-902", 29003),
}
HEURISTICS = (
    "max_slot_value",
    "min_slot_value",
    "sum_slots",
    "mean_slots",
    "single_threshold_per_slot",
    "single_slot_logistic",
)
PREDICTED = {
    "accept_all": 0,
    "reject_all_nearest_rule": 0,
    "prior_location_replayer": .2,
    "always_reject_counter": 0,
    "turn2_only": 0,
    "duplicate_action_washer": 0,
    "before_text_quoter": 0,
    "phase1_only": 0,
    "blanket_position_then_clause_match": 0,
    "slot_extractor_counter": 0,
    "unit_normalizing_slot_extractor": 0,
    "common_threshold_lookup": 0,
    "cheapest_harm_oracle": .2,
    "accept_all_but_1_harm": .2,
    "accept_all_but_2_harms": .2,
}


def load(path: Path | str):
    return json.loads(Path(path).read_text())


def combine(base: str, overlay: str, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(ROOT / "tasks/generated" / base, target)
    shutil.copytree(ROOT / "tasks/t2n_draft" / overlay, target, dirs_exist_ok=True)


def phase1(ep: Episode, task: Path):
    planted = load(task / "planted_deviations.json")
    issues = []
    for deviation in planted["deviations"]:
        action = {
            "action": "flag_issue",
            "rule_id": deviation["rule_id"],
            "doc_id": deviation["doc_id"],
            "clause_ref": "matched clause",
            "exact_quote": deviation["mutated_text"],
            "proposed_redline": deviation["expected_redline_text"],
        }
        ep.step(action)
        issues.append({key: value for key, value in action.items() if key != "action"})
    missing = planted["missing_info"][0]
    escalation = {"topic": missing["topic"], "reason": missing["topic"]}
    ep.step({"action": "escalate", **escalation})
    return ep.step({"action": "finalize", "card": {"issues": issues, "escalations": [escalation], "summary": "complete"}})


def honest(task: Path, run_dir: Path):
    ep = Episode(task, seed=0, run_dir=run_dir)
    ep.reset()
    reveal = phase1(ep, task)
    actions = []
    for patch in load(task / "patch_ledger.json")["patches"]:
        action = {
            "action": "review_change",
            "change_id": patch["change_id"],
            "origin": patch["origin"],
            "decision": patch["expected_disposition"],
        }
        if patch["origin"] == "prior_position":
            action["prior_position_id"] = "POS-" + patch["prior_source_deviation_id"].replace("-", "")
            action["rule_id"] = patch["expected_rule_id"]
        if patch["expected_disposition"] == "reject":
            action.update(rule_id=patch["expected_rule_id"], exact_quote=patch["ground_span"])
        if patch.get("expected_redline_text") and patch["expected_disposition"] == "reject":
            action["proposed_redline"] = patch["expected_redline_text"]
        ep.step(action)
        actions.append(action)
    ep.step({"action": "finalize", "card": {"changes": actions, "escalations": [], "summary": "complete"}})
    return load(ep.score_path), reveal


def public_records(label: str, area: str, task: Path, ordinal: int) -> list[dict]:
    events = {event["event_id"]: event for event in load(task / "turn_events.json")["events"]}
    task_record = load(task / "task.json")
    playbook_id = load(ROOT / task_record["playbook_ref"])["playbook_id"]
    output = []
    for event_ordinal, patch in enumerate(load(task / "patch_ledger.json")["patches"]):
        if patch["event_type"] != "counter_proposal":
            continue
        inputs = events[patch["event_id"]]["counter_inputs"]
        output.append({
            "label": patch["counter_class"],
            "counter_text_slots": inputs["counter_text_slots"],
            "phase1_context_slots": inputs["phase1_context_slots"],
            "decoy_values": inputs["decoy_values"],
            "task_ordinal": ordinal,
            "event_ordinal": event_ordinal,
            "section_bucket": patch["section_ref"],
            "playbook_rule": patch["expected_rule_id"],
            "family_split": patch["counter_family_id"],
            "playbook_id": playbook_id,
            "area": area,
            "observation": {
                "counter_text_slots": inputs["counter_text_slots"],
                "phase1_context_slots": inputs["phase1_context_slots"],
                "decoy_values": inputs["decoy_values"],
            },
            "public_task_id": label,
        })
    return output


def authored_families() -> dict[str, set[str]]:
    output: dict[str, set[str]] = {}
    for family_file, _ in AREAS.values():
        data = load(ROOT / "generator/t2n_families" / family_file)
        for playbook_id, bundle in data.items():
            if playbook_id.startswith("PB-"):
                output[playbook_id] = {family["counter_family_id"] for family in bundle["counter_families"]}
    return output


def family_heldout_check(records: list[dict]) -> dict:
    authored = authored_families()
    rows = []
    passed = True
    for playbook_id in sorted(authored):
        used = sorted({r["family_split"] for r in records if r["playbook_id"] == playbook_id})
        heldout = {used[-1]} if used else set()
        train = authored[playbook_id] - heldout
        evaluation = {r["family_split"] for r in records if r["playbook_id"] == playbook_id and r["family_split"] in heldout}
        disjoint = bool(train and heldout and evaluation) and train.isdisjoint(heldout) and train.isdisjoint(evaluation)
        passed &= disjoint
        rows.append({
            "playbook_id": playbook_id,
            "train_family_ids": sorted(train),
            "heldout_family_ids": sorted(heldout),
            "evaluation_family_ids": sorted(evaluation),
            "train_heldout_disjoint": disjoint,
        })
    return {"status": "PASS" if passed else "FAIL", "playbooks": rows}


def inventory_rows() -> list[dict]:
    rows = []
    for area, (family_file, bases) in AREAS.items():
        family_data = load(ROOT / "generator/t2n_families" / family_file)
        for base in bases:
            instance = ROOT / "tasks/generated" / base
            deviations = load(instance / "planted_deviations.json")["deviations"]
            structural = len(deviations) == 5 and all(
                deviation.get("expected_action") == "redline_with_fallback" and deviation.get("expected_redline_text")
                for deviation in deviations
            )
            playbook_id = load(ROOT / load(instance / "task.json")["playbook_ref"])["playbook_id"]
            family_rules = {family["rule_id"] for family in family_data[playbook_id]["counter_families"]}
            overlap = sorted({deviation["rule_id"] for deviation in deviations} & family_rules)
            eligible = structural and len(overlap) >= 2
            if not structural:
                reason = "one seeded deviation has expected_action=escalate and no expected_redline_text"
            elif len(overlap) < 2:
                reason = f"only {len(overlap)} authored rule overlap(s): {overlap}"
            else:
                reason = f"usable: {len(overlap)} authored rule overlaps {overlap}"
            rows.append({"area": area, "base": base, "playbook_id": playbook_id,
                         "mixed_eligible": eligible, "reason": reason,
                         "mixed_instances": 0, "all_concessions": False})
    return rows


def main() -> None:
    inventory = inventory_rows()
    generated = []

    # Four mixed instances per file area.  Rotation gives 2/2 on two-base
    # corpora, 2/1/1 on three-base corpora, and 1/1/1/1 across eligible
    # MSA/NDA contract bases.
    for area in AREA_ORDER:
        family_file, _ = AREAS[area]
        eligible = [row["base"] for row in inventory if row["area"] == area and row["mixed_eligible"]]
        if not eligible:
            continue
        for index in range(4):
            base = eligible[index % len(eligible)]
            seed = MIXED_SEEDS[area][index]
            label = f"T2N-V2-{area.upper()}-{index + 1:02d}-S{seed}"
            generate_response(ROOT / "tasks/generated" / base, seed,
                              ROOT / "generator/t2n_families" / family_file,
                              ROOT / "tasks/t2n_draft" / label)
            generated.append({"label": label, "base": base, "area": area,
                              "seed": seed, "kind": "mixed", "existing_pilot": False})

    for area, (base, seed) in ALL_CONCESSIONS.items():
        label = f"T2N-V2-{area.upper()}-AC-S{seed}"
        generate_all_concessions(ROOT / "tasks/generated" / base, seed, ROOT / "tasks/t2n_draft" / label)
        generated.append({"label": label, "base": base, "area": area,
                          "seed": seed, "kind": "all_concessions", "existing_pilot": False})

    for row in inventory:
        row["mixed_instances"] = sum(g["kind"] == "mixed" and g["base"] == row["base"] for g in generated)
        row["all_concessions"] = any(g["kind"] == "all_concessions" and g["base"] == row["base"] for g in generated)

    mixed = [item for item in generated if item["kind"] == "mixed"]
    counters: list[dict] = []
    episodes = []
    battery: dict[str, list[float]] = defaultdict(list)
    gamed: dict[str, int] = defaultdict(int)
    validator_results = []

    with TemporaryDirectory(prefix="t2n-v2-tranche-") as tmp_name:
        tmp = Path(tmp_name)
        for ordinal, item in enumerate(mixed):
            task = tmp / item["label"]
            combine(item["base"], item["label"], task)
            score, reveal = honest(task, tmp / "honest" / item["label"])
            episodes.append({"children": score["telemetry"]["children"], "E": score["E"]})
            counters.extend(public_records(item["label"], item["area"], task, ordinal))
            public = {"observation": {"changes": reveal["changes"]}, "public_task_id": item["label"]}
            assert v10_t2n_forbidden_fields([public]).status == "PASS"
            assert all(not (FORBIDDEN_LEAKAGE_FIELDS & set(change)) for change in reveal["changes"])
            results = run_all_t2n(ROOT / "tasks/t2n_draft" / item["label"])
            playbook = load(ROOT / load(task / "task.json")["playbook_ref"])
            canary_ids = {rule["rule_id"] for rule in playbook["rules"] if rule.get("is_canary") is True}
            results.append(v9_ext_t2n_canary_turn_events(load(task / "turn_events.json"), canary_ids))
            validator_results.append({"label": item["label"], "results": [result.__dict__ for result in results]})
            assert all(result.status == "PASS" for result in results)
            for strategy in STRATEGIES:
                ep = Episode(task, seed=0, run_dir=tmp / "battery" / strategy / item["label"])
                ep.reset()
                drive_strategy(ep, strategy)
                result = load(ep.score_path)
                battery[strategy].append(result["composite"])
                gamed[strategy] += result["status"] == "GAMED"

        all_checks = []
        for item in (record for record in generated if record["kind"] == "all_concessions"):
            task = tmp / item["label"]
            combine(item["base"], item["label"], task)
            score, _ = honest(task, tmp / "all" / item["label"])
            all_checks.append({"label": item["label"], "composite": score["composite"], "gate_pass": score["gate_pass"]})

        folds = [[] for _ in range(4)]
        for record in counters:
            # Keep each AU task intact inside one independently seeded fold;
            # splitting its two labels across folds creates an artificial
            # anticorrelation in the held-out task-ordinal baseline.
            folds[record["task_ordinal"] % 4].append(record)
        lookup = v10_t2n_lookup_classifiers(folds, ["task_ordinal", "event_ordinal", "section_bucket", "operation", "surface_template_hash", "playbook_rule", "family_split"])
        mi = v10_t2n_permutation_mi(counters, ["task_ordinal", "event_ordinal", "section_bucket"])
        quota = {"acceptable": sum(r["label"] == "acceptable" for r in counters),
                 "unacceptable": sum(r["label"] == "unacceptable" for r in counters)}
        attackers = {heuristic: v10_t2n_quota_batch_attacker(counters, quota=quota, heuristic=heuristic).__dict__
                     for heuristic in HEURISTICS}
        heldout = family_heldout_check(counters)
        metrics = tranche_counter_metrics(episodes)
        gate = gated_tranche_composite([{"E": episode["E"]} for episode in episodes], metrics)

        tranche_strategy = {}
        for strategy in TRANCHE_GATED:
            child_episodes = []
            for item in mixed:
                task = tmp / item["label"]
                combine(item["base"], item["label"], task)
                ep = Episode(task, seed=0, run_dir=tmp / "tranche" / strategy / item["label"])
                ep.reset()
                drive_strategy(ep, strategy)
                result = load(ep.score_path)
                child_episodes.append({"children": result["telemetry"]["children"], "E": result["E"]})
            strategy_metrics = tranche_counter_metrics(child_episodes)
            tranche_strategy[strategy] = {
                "metrics": strategy_metrics,
                "gated": gated_tranche_composite([{"E": result["E"]} for result in child_episodes], strategy_metrics),
            }

    rows = [{
        "strategy": strategy,
        "predicted": PREDICTED[strategy],
        "min": min(battery[strategy]),
        "mean": sum(battery[strategy]) / len(battery[strategy]),
        "max": max(battery[strategy]),
        "worst_instances": [mixed[i]["label"] for i, score in enumerate(battery[strategy]) if score == max(battery[strategy])],
        "gamed_count": gamed[strategy],
        "tranche_gated": strategy in TRANCHE_GATED,
        "tranche_result": tranche_strategy.get(strategy),
    } for strategy in sorted(STRATEGIES)]

    manifest = {
        "mixed_count": len(mixed),
        "acceptable_count": sum(record["label"] == "acceptable" for record in counters),
        "unacceptable_count": sum(record["label"] == "unacceptable" for record in counters),
        "all_concessions_count": 3,
        "instances": generated,
        "inventory": inventory,
        "all_concession_episode_checks": all_checks,
        "all_concessions_compliant": all_concessions_share_compliant(len(mixed), 3),
        "all_concessions_four_compliant": all_concessions_share_compliant(len(mixed), 4),
        "counter_records": counters,
        "family_heldout_split": heldout,
        "per_instance_validators": validator_results,
    }
    (ROOT / "reports/t2n_tranche_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    report = {
        "banner": "DRAFT-INSTANCES / UNSIGNED-FAMILIES — machine-drafted v2 families; attorney line-item review pending; not a release gate.",
        "manifest": "reports/t2n_tranche_manifest.json",
        "strategy_rows": rows,
        "v10_lookup": lookup.__dict__,
        "v10_permutation_mi": mi.__dict__,
        "v10_quota_batch_attackers": attackers,
        "counter_macro_gate": {"metrics": metrics, "gated": gate},
        "family_heldout_split": heldout,
        "all_concessions": all_checks,
        "inventory": inventory,
    }
    (ROOT / "reports/t2n_draft_gates.json").write_text(json.dumps(report, indent=2) + "\n")

    lines = [f"# {report['banner']}", "", "## Base inventory and generated distribution", "",
             "| Area | Base | Playbook | Mixed eligible | Reason | Mixed generated | All-concessions |",
             "|---|---|---|---|---|---:|---|"]
    lines += [f"| {row['area']} | {row['base']} | {row['playbook_id']} | {row['mixed_eligible']} | {row['reason']} | {row['mixed_instances']} | {row['all_concessions']} |" for row in inventory]
    lines += ["", "## Mechanical battery", "",
              "| Strategy | Predicted | Min | Mean | Max (worst) | GAMED | Worst instances |",
              "|---|---:|---:|---:|---:|---:|---|"]
    lines += [f"| {row['strategy']} | {row['predicted']:.6f} | {row['min']:.6f} | {row['mean']:.6f} | {row['max']:.6f} | {row['gamed_count']} | {', '.join(row['worst_instances'])} |" for row in rows]
    statistical = {
        "lookup": report["v10_lookup"],
        "permutation_mi": report["v10_permutation_mi"],
        "quota_batch_attackers": attackers,
        "counter_macro_gate": report["counter_macro_gate"],
        "family_heldout_split": heldout,
    }
    lines += ["", "## Tranche statistical gates", "", "```json", json.dumps(statistical, indent=2), "```", "",
              f"All concessions: {all_checks}; 9*3 <= {len(mixed)} is {manifest['all_concessions_compliant']}; 9*4 <= {len(mixed)} is {manifest['all_concessions_four_compliant']}."]
    (ROOT / "reports/t2n_draft_gates.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
