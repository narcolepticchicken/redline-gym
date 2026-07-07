from __future__ import annotations

import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def main() -> int:
    REPORTS.mkdir(exist_ok=True)
    tasks = _task_dirs()
    gate = _load_gate_table()
    lines = [
        "# Validity Report",
        "",
        "This report is assembled from repository artifacts only. It excludes the held-out split unless a formal evaluation protocol opts in.",
        "",
        "## Instance Inventory",
        "",
        "| Task | Practice area | Tier | Source | QA artifacts | Human sign-off |",
        "|---|---|---|---|---|---|",
    ]
    signed_names: set[str] = set()
    signed_count = 0
    stubbed_by_task: dict[str, list[str]] = {}
    for task_dir in tasks:
        task = _load_json(task_dir / "task.json")
        signoff = _signoff_status(task_dir / "verification_report.md")
        if signoff["signed"]:
            signed_count += 1
            if signoff["name"]:
                signed_names.add(signoff["name"])
        stubs = _stubbed_validators(task_dir / "verification_report.md")
        if stubs:
            stubbed_by_task[str(task_dir.relative_to(ROOT))] = stubs
        lines.append(
            "| {task} | {area} | {tier} | {source} | {qa} | {signoff} |".format(
                task=str(task_dir.relative_to(ROOT)),
                area=task["practice_area"],
                tier=task["difficulty_tier"],
                source=_source(task_dir),
                qa=_qa_status(task_dir),
                signoff=signoff["label"],
            )
        )

    lines.extend(["", "## Gate Table", ""])
    if gate:
        lines.extend(_gate_summary(gate))
    else:
        lines.append("No `reports/gate_table.json` artifact found.")

    lines.extend(["", "## Known Limits", ""])
    lines.extend(_known_limits(gate, signed_count, len(tasks), len(signed_names), stubbed_by_task))

    path = REPORTS / "validity_report.md"
    path.write_text("\n".join(lines) + "\n")
    print(f"Wrote {path.relative_to(ROOT)}")
    return 0


def _task_dirs() -> list[Path]:
    paths = []
    for task_json in (ROOT / "tasks").rglob("task.json"):
        if "heldout" in task_json.relative_to(ROOT).parts:
            continue
        paths.append(task_json.parent)
    return sorted(paths, key=lambda path: str(path.relative_to(ROOT)))


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _load_gate_table() -> dict | None:
    path = REPORTS / "gate_table.json"
    if not path.exists():
        return None
    return _load_json(path)


def _source(task_dir: Path) -> str:
    if "generated" in task_dir.relative_to(ROOT).parts:
        return "generated"
    return "handbuilt"


def _qa_status(task_dir: Path) -> str:
    present = []
    for name in ["verification_report.md", "model_checks", "qa"]:
        if (task_dir / name).exists():
            present.append(name)
    return ", ".join(present) if present else "none"


def _signoff_status(path: Path) -> dict:
    if not path.exists():
        return {"signed": False, "name": "", "label": "missing verification report"}
    text = path.read_text()
    status = next((line for line in text.splitlines() if line.startswith("Status:")), "Status: missing")
    signed = "HUMAN SIGNED-OFF" in status
    name = ""
    match = re.search(r"Human sign-off:\s*name\s+(.+?)\s+date\s+", text)
    if match and "____" not in match.group(1):
        name = match.group(1).strip()
    label = status.replace("Status: ", "")
    if signed and name:
        label = f"{label}; {name}"
    return {"signed": signed, "name": name, "label": label}


def _stubbed_validators(path: Path) -> list[str]:
    if not path.exists():
        return ["verification report missing"]
    stubs = []
    for line in path.read_text().splitlines():
        if "| V" in line and "| STUBBED |" in line:
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if cells:
                stubs.append(cells[0])
    return stubs


def _gate_summary(gate: dict) -> list[str]:
    lines = [
        "| Task | Validators | Null gate | Random gate | Grep gate | Mechanical ceiling |",
        "|---|---|---|---|---|---:|",
    ]
    for row in gate.get("rows", []):
        ceiling = row.get("mechanical_ceiling")
        ceiling_text = ""
        if ceiling:
            max_score = ceiling["max"]
            ceiling_text = f"{max_score['composite']:.6f} ({max_score['strategy']})"
        else:
            ceiling_text = "UNMEASURED"
        lines.append(
            f"| {row['task']} | {row['validators']} | {row['null_gate']} | {row['random_gate']} | {row['grep_gate']} | {ceiling_text} |"
        )
    return lines


def _known_limits(
    gate: dict | None,
    signed_count: int,
    total_tasks: int,
    attorney_count: int,
    stubbed_by_task: dict[str, list[str]],
) -> list[str]:
    limits = []
    unmeasured = _unmeasured_gates(gate)
    if unmeasured:
        limits.append("- UNMEASURED gates: " + "; ".join(unmeasured) + ".")
    else:
        limits.append("- UNMEASURED gates: none recorded in the gate table artifact.")
    limits.append(
        f"- Attorney-agreement status: {attorney_count} attorney(s), {signed_count} of {total_tasks} non-held-out instance(s) signed."
    )
    if stubbed_by_task:
        for task, stubs in stubbed_by_task.items():
            limits.append(f"- Validator stubs not yet run for {task}: {', '.join(stubs)}.")
    else:
        limits.append("- Validator stubs not yet run: none shown in verification reports.")
    return limits


def _unmeasured_gates(gate: dict | None) -> list[str]:
    if not gate:
        return ["gate table missing"]
    found: set[str] = set()
    for row in gate.get("rows", []):
        for key in ["random_gate", "grep_gate"]:
            if row.get(key) == "UNMEASURED":
                found.add(f"{row['task']} {key.removesuffix('_gate')}")
        for key in ["honest_llm", "cheater_llm", "deepseek_judge"]:
            value = str(row.get(key, ""))
            if value.startswith("SKIPPED") or value == "UNMEASURED":
                found.add(f"{row['task']} {key}")
        if row.get("mechanical_ceiling") is None:
            found.add(f"{row['task']} mechanical_ceiling")
    return sorted(found)


if __name__ == "__main__":
    raise SystemExit(main())

