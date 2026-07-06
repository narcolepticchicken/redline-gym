from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_WEIGHTS = {
    "recall": 0.35,
    "precision": 0.15,
    "grounding": 0.15,
    "fallback": 0.15,
    "conformance": 0.10,
    "abstention": 0.10,
}


def derive(task_dir: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    task = json.loads((task_dir / "task.json").read_text())
    planted = json.loads((task_dir / "planted_deviations.json").read_text())
    playbook = json.loads((root / task["playbook_ref"]).read_text())
    rules = {rule["rule_id"]: rule for rule in playbook["rules"]}

    issues = []
    criteria = []
    for index, dev in enumerate(planted["deviations"], start=1):
        issue_id = f"I-{index:03d}"
        issues.append(
            {
                "issue_id": issue_id,
                "deviation_ids": [dev["deviation_id"]],
                "rule_id": dev["rule_id"],
                "doc_ids": [dev["doc_id"]],
                "severity": dev["severity"],
                "expected_action": dev["expected_action"],
            }
        )
        criteria.append(
            {
                "criterion_id": f"C-{index:03d}",
                "issue_id": issue_id,
                "deviation_ids": [dev["deviation_id"]],
                "doc_ids": [dev["doc_id"]],
                "rule_id": dev["rule_id"],
                "points": _severity_points(rules[dev["rule_id"]]["severity"]),
            }
        )

    issue_matrix = {
        "issues": issues,
        "missing_info": planted["missing_info"],
        "distractors": planted["distractors"],
    }
    rubric = {
        "card_schema_id": task["deliverable"]["card_schema_id"],
        "weights": DEFAULT_WEIGHTS,
        "criteria": criteria,
    }
    (task_dir / "issue_matrix.json").write_text(json.dumps(issue_matrix, indent=2) + "\n")
    (task_dir / "rubric.json").write_text(json.dumps(rubric, indent=2) + "\n")


def _severity_points(severity: str) -> float:
    return {"low": 1.0, "medium": 2.0, "high": 3.0, "critical": 5.0}[severity]


def main() -> int:
    parser = argparse.ArgumentParser(description="Derive issue_matrix.json and rubric.json.")
    parser.add_argument("task_dir", nargs="?", type=Path, default=Path("tasks/contracts/T1-NDA-001"))
    args = parser.parse_args()
    derive(args.task_dir)
    print(f"Derived issue_matrix.json and rubric.json for {args.task_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
