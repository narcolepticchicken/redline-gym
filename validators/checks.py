from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Callable

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schema"
MODEL_STUB_MESSAGE = "requires lab serving lane -- do not run from build tooling"


@dataclass
class ValidationResult:
    code: str
    name: str
    status: str
    detail: str


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _task_artifacts(task_dir: Path) -> dict[str, Any]:
    task = _load_json(task_dir / "task.json")
    return {
        "task": task,
        "manifest": _load_json(task_dir / "documents_manifest.json"),
        "playbook": _load_json(ROOT / task["playbook_ref"]),
        "planted": _load_json(task_dir / "planted_deviations.json"),
        "issue_matrix": _load_json(task_dir / "issue_matrix.json"),
        "rubric": _load_json(task_dir / "rubric.json"),
    }


def _docs_by_id(task_dir: Path, manifest: dict[str, Any]) -> dict[str, str]:
    docs = {}
    for doc in manifest["documents"]:
        docs[doc["doc_id"]] = (task_dir / doc["path"]).read_text()
    return docs


def _schema_validate(instance: dict[str, Any], schema_name: str) -> list[str]:
    schema = _load_json(SCHEMA_DIR / f"{schema_name}.schema.json")
    validator = Draft202012Validator(schema)
    return [f"{'/'.join(map(str, e.path))}: {e.message}" for e in validator.iter_errors(instance)]


def _ids(items: list[dict[str, Any]], key: str) -> set[str]:
    return {item[key] for item in items}


def v1_rubric_citations(task_dir: Path) -> ValidationResult:
    a = _task_artifacts(task_dir)
    doc_ids = _ids(a["manifest"]["documents"], "doc_id")
    dev_ids = _ids(a["planted"]["deviations"], "deviation_id")
    issue_ids = _ids(a["issue_matrix"]["issues"], "issue_id")
    errors = []
    for criterion in a["rubric"]["criteria"]:
        if criterion["issue_id"] not in issue_ids:
            errors.append(f"{criterion['criterion_id']} cites missing issue {criterion['issue_id']}")
        for doc_id in criterion["doc_ids"]:
            if doc_id not in doc_ids:
                errors.append(f"{criterion['criterion_id']} cites missing doc {doc_id}")
        for dev_id in criterion["deviation_ids"]:
            if dev_id not in dev_ids:
                errors.append(f"{criterion['criterion_id']} cites missing deviation {dev_id}")
    return _result("V1", "rubric citations", errors)


def v2_mutation_anti_drift(task_dir: Path) -> ValidationResult:
    a = _task_artifacts(task_dir)
    docs = _docs_by_id(task_dir, a["manifest"])
    errors = []
    for dev in a["planted"]["deviations"]:
        doc_text = docs.get(dev["doc_id"], "")
        anchor = dev["clause_anchor"]["span"]
        mutated = dev["mutated_text"]
        if mutated not in doc_text:
            errors.append(f"{dev['deviation_id']} mutated_text missing from {dev['doc_id']}")
        if anchor not in doc_text:
            errors.append(f"{dev['deviation_id']} anchor span missing from {dev['doc_id']}")
        if mutated not in anchor:
            errors.append(f"{dev['deviation_id']} mutated_text not contained in anchor span")
    return _result("V2", "mutation anti-drift", errors)


def v3_clean_base_stub(_: Path) -> ValidationResult:
    return ValidationResult("V3", "clean-base check", "STUBBED", MODEL_STUB_MESSAGE)


def v4_round_trip_stub(_: Path) -> ValidationResult:
    return ValidationResult("V4", "round-trip detectability", "STUBBED", MODEL_STUB_MESSAGE)


def v5_issue_deviation_mapping(task_dir: Path) -> ValidationResult:
    a = _task_artifacts(task_dir)
    rule_ids = _ids(a["playbook"]["rules"], "rule_id")
    issue_by_dev: dict[str, int] = {}
    errors = []
    for issue in a["issue_matrix"]["issues"]:
        if not issue["deviation_ids"]:
            errors.append(f"{issue['issue_id']} has no deviations")
        if issue["rule_id"] not in rule_ids:
            errors.append(f"{issue['issue_id']} maps to missing rule {issue['rule_id']}")
        for dev_id in issue["deviation_ids"]:
            issue_by_dev[dev_id] = issue_by_dev.get(dev_id, 0) + 1
    for dev in a["planted"]["deviations"]:
        if dev["rule_id"] not in rule_ids:
            errors.append(f"{dev['deviation_id']} maps to missing rule {dev['rule_id']}")
        if issue_by_dev.get(dev["deviation_id"]) != 1:
            errors.append(f"{dev['deviation_id']} appears in {issue_by_dev.get(dev['deviation_id'], 0)} issues")
    return _result("V5", "issue/deviation mapping", errors)


def v6_distractor_integrity_scan(task_dir: Path) -> ValidationResult:
    a = _task_artifacts(task_dir)
    banned: list[tuple[str, str]] = []
    for rule in a["playbook"]["rules"]:
        for phrase in rule.get("deterministic_checks", {}).get("must_not_contain", []):
            banned.append((rule["rule_id"], phrase.lower()))
    errors = []
    for distractor in a["issue_matrix"]["distractors"]:
        span_lower = distractor["span"].lower()
        for rule_id, phrase in banned:
            if phrase and phrase in span_lower:
                errors.append(f"{distractor['distractor_id']} contains banned phrase for {rule_id}: {phrase}")
    return _result("V6", "distractor integrity rule scan", errors)


def v7_missing_info_string_search(task_dir: Path) -> ValidationResult:
    a = _task_artifacts(task_dir)
    docs = "\n".join(_docs_by_id(task_dir, a["manifest"]).values()).lower()
    errors = []
    for item in a["issue_matrix"]["missing_info"]:
        for term in item["absent_terms"]:
            if term.lower() in docs:
                errors.append(f"{item['missing_info_id']} absent term appears in docs: {term}")
    return _result("V7", "missing-info string search", errors)


def v7_missing_info_semantic_stub(_: Path) -> ValidationResult:
    return ValidationResult("V7-semantic", "missing-info semantic search", "STUBBED", MODEL_STUB_MESSAGE)


def v8_schema_and_hashes(task_dir: Path) -> ValidationResult:
    errors = []
    artifacts = {
        "task": _load_json(task_dir / "task.json"),
        "documents_manifest": _load_json(task_dir / "documents_manifest.json"),
        "planted_deviations": _load_json(task_dir / "planted_deviations.json"),
        "issue_matrix": _load_json(task_dir / "issue_matrix.json"),
        "rubric": _load_json(task_dir / "rubric.json"),
    }
    artifacts["playbook"] = _load_json(ROOT / artifacts["task"]["playbook_ref"])
    for name, instance in artifacts.items():
        for error in _schema_validate(instance, name):
            errors.append(f"{name}: {error}")
    if len(artifacts["task"]["instruction"]) > 300:
        errors.append("task instruction exceeds 300 chars")
    for doc in artifacts["documents_manifest"]["documents"]:
        actual = hashlib.sha256((task_dir / doc["path"]).read_bytes()).hexdigest()
        if actual != doc["sha256"]:
            errors.append(f"{doc['doc_id']} sha256 mismatch")
    return _result("V8", "schema and hashes", errors)


def v9_canary_empty(task_dir: Path) -> ValidationResult:
    a = _task_artifacts(task_dir)
    canary_ids = {rule["rule_id"] for rule in a["playbook"]["rules"] if rule["is_canary"]}
    errors = []
    if len(canary_ids) != 2:
        errors.append(f"expected exactly 2 canary rules, found {len(canary_ids)}")
    for dev in a["planted"]["deviations"]:
        if dev["rule_id"] in canary_ids:
            errors.append(f"{dev['deviation_id']} planted against canary {dev['rule_id']}")
    return _result("V9", "canary rules empty", errors)


def v10_leakage_scan(path: Path) -> ValidationResult:
    task_dirs = _collect_task_dirs(path)
    if len(task_dirs) < 2:
        return ValidationResult("V10", "tranche leakage scan", "PASS", "single task; variance gate not applicable")
    sections_by_task = []
    mechanisms_by_task = []
    starts_by_task = []
    for task_dir in task_dirs:
        planted = _load_json(task_dir / "planted_deviations.json")
        sections_by_task.append(tuple(dev["clause_anchor"]["section"] for dev in planted["deviations"]))
        mechanisms_by_task.append(tuple(dev["mechanism"] for dev in planted["deviations"]))
        starts_by_task.append(tuple(_surface_key(dev["mutated_text"]) for dev in planted["deviations"]))
    errors = []
    if len(set(sections_by_task)) == 1:
        errors.append("deviation section pattern is constant across tranche")
    if len(set(mechanisms_by_task)) == 1:
        errors.append("deviation mechanism pattern is constant across tranche")
    if len(set(starts_by_task)) == 1:
        errors.append("deviation surface phrasing pattern is constant across tranche")
    return _result("V10", "tranche leakage scan", errors)


def v11_realism_stub(_: Path) -> ValidationResult:
    return ValidationResult("V11", "realism/coherence judge", "STUBBED", MODEL_STUB_MESSAGE)


def run_all(task_dir: Path) -> list[ValidationResult]:
    task_dir = task_dir.resolve()
    return [
        v1_rubric_citations(task_dir),
        v2_mutation_anti_drift(task_dir),
        v3_clean_base_stub(task_dir),
        v4_round_trip_stub(task_dir),
        v5_issue_deviation_mapping(task_dir),
        v6_distractor_integrity_scan(task_dir),
        v7_missing_info_string_search(task_dir),
        v7_missing_info_semantic_stub(task_dir),
        v8_schema_and_hashes(task_dir),
        v9_canary_empty(task_dir),
        v10_leakage_scan(task_dir.parent),
        v11_realism_stub(task_dir),
    ]


def write_report(task_dir: Path, results: list[ValidationResult]) -> Path:
    path = task_dir / "verification_report.md"
    preserved = _preserved_signoff(path)
    lines = [
        "# Verification Report",
        "",
        preserved["status"] or "Status: AWAITING HUMAN SIGN-OFF",
        "",
        "| Validator | Status | Detail |",
        "|---|---|---|",
    ]
    for r in results:
        lines.append(f"| {r.code} {r.name} | {r.status} | {r.detail} |")
    lines.extend(
        [
            "",
            "Model-stubbed validators: V3, V4, V7-semantic, V11.",
            "",
        ]
    )
    if preserved["signoff"]:
        lines.append(preserved["signoff"].rstrip("\n"))
    else:
        lines.append("Human sign-off: name ____________________ date __________")
    lines.append("")
    path.write_text("\n".join(lines))
    return path


def _preserved_signoff(path: Path) -> dict[str, str]:
    if not path.exists():
        return {"status": "", "signoff": ""}
    text = path.read_text()
    status = ""
    for line in text.splitlines():
        if line.startswith("Status:") and "HUMAN SIGNED-OFF" in line:
            status = line
            break
    marker = "Human sign-off:"
    signoff = ""
    start = text.find(marker)
    if start != -1:
        signoff = text[start:]
    return {"status": status, "signoff": signoff}


def _result(code: str, name: str, errors: list[str]) -> ValidationResult:
    if errors:
        return ValidationResult(code, name, "FAIL", "; ".join(errors))
    return ValidationResult(code, name, "PASS", "ok")


def _collect_task_dirs(path: Path) -> list[Path]:
    if (path / "task.json").exists():
        return [path]
    return sorted(p.parent for p in path.rglob("task.json") if p.name == "task.json")


def _surface_key(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()[:80]
