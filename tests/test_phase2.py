from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from baselines.grep_bot import main as grep_bot_main
from baselines.random_flagger import main as random_flagger_main
from env import Episode
from report.renderer import render_path
from scoring.core import score_episode
from scoring.judge_claude_sub import ClaudeSubscriptionJudge


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "tasks/contracts/T1-NDA-001"


def sample_flag() -> dict:
    return {
        "rule_id": "R-001",
        "doc_id": "DOC-01",
        "clause_ref": "Section 1",
        "exact_quote": "\"Confidential Information\" means information disclosed by or on behalf of a Discloser that is marked confidential at the time of disclosure or confirmed as confidential in writing within ten days after disclosure.",
        "severity": "high",
        "proposed_redline": "Confidential Information means all non-public information disclosed by or on behalf of a party, whether before or after the effective date, in any form or medium and whether or not marked confidential.",
        "rationale": "Marked-only coverage is narrower than the playbook requires.",
    }


def test_episode_loop_scores_via_core(tmp_path: Path) -> None:
    episode = Episode(SAMPLE, seed=7, run_dir=tmp_path / "run")
    episode.reset()
    flag = sample_flag()
    episode.step({"action": "flag_issue", **flag})
    card = {"summary": "One issue.", "issues": [flag], "escalations": []}
    episode.step({"action": "finalize", "card": card})

    score = json.loads(episode.score_path.read_text())
    direct = score_episode(SAMPLE, [flag], [], card)
    for key in ["composite", "channels", "weights", "status", "false_flags", "matched_deviation_ids"]:
        assert score[key] == direct[key]
    assert score["ended_by"] == "finalize"


def test_timeout_scores_no_card_but_keeps_flags(tmp_path: Path) -> None:
    task_dir = tmp_path / "T1-NDA-001"
    shutil.copytree(SAMPLE, task_dir)
    task = json.loads((task_dir / "task.json").read_text())
    task["turn_cap"] = 2
    (task_dir / "task.json").write_text(json.dumps(task, indent=2) + "\n")

    episode = Episode(task_dir, seed=0, run_dir=tmp_path / "run")
    episode.reset()
    episode.step({"action": "flag_issue", **sample_flag()})
    obs = episode.step({"action": "list_docs"})
    score = json.loads(episode.score_path.read_text())
    assert obs["done"] is True
    assert score["ended_by"] == "timeout"
    assert score["channels"]["conformance"] == 0.0
    assert score["channels"]["recall"] > 0.0
    assert score["channels"]["precision"] > 0.0
    assert score["channels"]["grounding"] > 0.0


def test_playbook_and_tool_observations_redact_answer_keys(tmp_path: Path) -> None:
    episode = Episode(SAMPLE, seed=0, run_dir=tmp_path / "run")
    observations = [
        episode.reset(),
        episode.step({"action": "list_docs"}),
        episode.step({"action": "read_doc", "doc_id": "DOC-01", "start": 1, "end": 8}),
    ]
    action_spec = observations[0]["action_spec"]
    assert action_spec["flag_issue"]["required"] == ["rule_id", "doc_id", "clause_ref", "exact_quote"]
    assert action_spec["flag_issue"]["optional"] == ["severity", "proposed_redline", "rationale"]
    assert action_spec["read_doc"] == {"required": ["doc_id"], "optional": ["start", "end"]}
    assert action_spec["escalate"] == {"required": ["topic", "reason"], "optional": []}
    assert action_spec["finalize"]["required"] == ["card"]
    assert action_spec["finalize"]["optional"] == []
    assert action_spec["finalize"]["card_shape"] == {
        "issues": "[{rule_id, doc_id, clause_ref, exact_quote, proposed_redline?}]",
        "escalations": "[{topic, reason}]",
        "summary": "string",
    }
    payload = json.dumps(observations, sort_keys=True)
    banned = [
        "is_canary",
        "deviation_id",
        "mutated_text",
        "planted_deviations",
        "issue_matrix",
        "rubric.json",
        "D-001",
        "D-006",
        "X-001",
        "M-001",
    ]
    for item in banned:
        assert item not in payload


def test_random_flagger_determinism_same_seed_same_score_json(tmp_path: Path) -> None:
    run_dir = tmp_path / "random-run"
    args = ["--task", str(SAMPLE), "--seed", "11", "--run-dir", str(run_dir)]
    assert random_flagger_main(args) == 0
    first = (run_dir / "T1-NDA-001" / "score.json").read_text()
    assert random_flagger_main(args) == 0
    second = (run_dir / "T1-NDA-001" / "score.json").read_text()
    assert first == second


def test_grep_bot_never_escalates_or_embeds_missing_info_or_distractors(tmp_path: Path) -> None:
    run_dir = tmp_path / "grep-run"
    args = ["--task", str(SAMPLE), "--seed", "0", "--run-dir", str(run_dir)]
    assert grep_bot_main(args) == 0

    transcript = run_dir / "T1-NDA-001" / "episode.jsonl"
    actions = [json.loads(line)["action"] for line in transcript.read_text().splitlines()]
    assert [action["action"] for action in actions].count("escalate") == 0

    score = json.loads((run_dir / "T1-NDA-001" / "score.json").read_text())
    assert score["channels"]["abstention"] == 0.0

    answer_key_strings = _missing_info_and_distractor_strings()
    baseline_sources = "\n".join(
        path.read_text()
        for path in (ROOT / "baselines").glob("*.py")
    ).lower()
    grep_bot_source = (ROOT / "baselines/grep_bot.py").read_text().lower()

    for item in answer_key_strings:
        assert item.lower() not in grep_bot_source
        assert item.lower() not in baseline_sources


def test_report_renderer_smoke(tmp_path: Path) -> None:
    episode = Episode(SAMPLE, seed=0, run_dir=tmp_path / "gamed-run")
    episode.reset()
    episode.step(
        {
            "action": "flag_issue",
            "rule_id": "R-014",
            "doc_id": "DOC-01",
            "clause_ref": "Section 13",
            "exact_quote": "This Agreement is governed by the laws of the State of New York, without regard to conflict-of-law rules.",
            "severity": "low",
            "proposed_redline": "Change governing law.",
            "rationale": "Canary stress test.",
        }
    )
    episode.step({"action": "finalize", "card": {"summary": "Canary.", "issues": [], "escalations": []}})
    outputs = render_path(tmp_path / "gamed-run")
    report = tmp_path / "gamed-run" / "T1-NDA-001" / "report.html"
    index = tmp_path / "gamed-run" / "index.html"
    assert report in outputs
    assert index in outputs
    assert report.exists()
    assert index.exists()
    assert "GAMED" in report.read_text()
    assert "recall" in index.read_text()
    assert "T1-NDA-001" in index.read_text()


def test_signed_verification_report_survives_validator_regeneration(tmp_path: Path) -> None:
    task_dir = tmp_path / "T1-NDA-001"
    shutil.copytree(SAMPLE, task_dir)
    report_path = task_dir / "verification_report.md"
    before = report_path.read_text()
    before_status = next(line for line in before.splitlines() if line.startswith("Status:"))
    before_signoff = before[before.index("Human sign-off:") :]

    completed = subprocess.run(
        ["python3", "-m", "validators", str(task_dir)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    assert "Wrote" in completed.stdout
    after = report_path.read_text()
    after_status = next(line for line in after.splitlines() if line.startswith("Status:"))
    after_signoff = after[after.index("Human sign-off:") :]
    assert after_status == before_status
    assert after_signoff == before_signoff


def test_claude_judge_dry_run_prints_prompt(capsys) -> None:
    judge = ClaudeSubscriptionJudge(dry_run=True)
    judge.fallback_tiebreak_judge("proposed text", "expected text")
    output = capsys.readouterr().out
    assert "Redline Gym channel-4 fallback tiebreak" in output
    assert "proposed text" in output
    assert "expected text" in output


def _missing_info_and_distractor_strings() -> list[str]:
    strings: set[str] = set()
    content_keys = {"topic", "absent_terms", "span", "why_benign"}
    for task_dir in (ROOT / "tasks").glob("*/*"):
        for filename in ["issue_matrix.json", "planted_deviations.json"]:
            path = task_dir / filename
            if not path.exists():
                continue
            payload = json.loads(path.read_text())
            for section in ["missing_info", "distractors"]:
                for entry in payload.get(section, []):
                    for key in content_keys:
                        _collect_strings(entry.get(key), strings)
    return sorted(item for item in strings if len(item) >= 8)


def _collect_strings(value: object, strings: set[str]) -> None:
    if isinstance(value, str):
        strings.add(value)
    elif isinstance(value, list):
        for item in value:
            _collect_strings(item, strings)
