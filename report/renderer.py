from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def render_path(path: str | Path) -> list[Path]:
    run_path = Path(path)
    if not run_path.is_absolute():
        run_path = (Path.cwd() / run_path).resolve()
    if (run_path / "score.json").exists():
        report = render_episode(run_path)
        return [report]
    episode_dirs = sorted(p.parent for p in run_path.glob("*/score.json"))
    outputs = [render_episode(episode_dir) for episode_dir in episode_dirs]
    outputs.append(render_index(run_path, episode_dirs))
    return outputs


def render_episode(episode_dir: Path) -> Path:
    score = _read_json(episode_dir / "score.json")
    task_dir = ROOT / "tasks" / "contracts" / score["task_id"]
    if not task_dir.exists():
        candidates = sorted((ROOT / "tasks").glob(f"*/*{score['task_id']}*"))
        task_dir = candidates[0] if candidates else task_dir
    task = _read_json(task_dir / "task.json")
    manifest = _read_json(task_dir / "documents_manifest.json")
    playbook = _read_json(ROOT / task["playbook_ref"])
    planted = _read_json(task_dir / "planted_deviations.json")
    flags, escalations, card = _transcript_payloads(episode_dir / "episode.jsonl")
    canaries = {rule["rule_id"] for rule in playbook["rules"] if rule.get("is_canary")}

    body = [
        "<!doctype html>",
        "<html><head><meta charset='utf-8'>",
        f"<title>{html.escape(score['task_id'])} Redline Gym Report</title>",
        _style(),
        "</head><body>",
        f"<h1>{html.escape(score['task_id'])}</h1>",
    ]
    if score["status"] == "GAMED":
        body.append("<div class='gamed'>GAMED: canary rule was claimed</div>")
    body.append(_score_section(score))
    body.append("<h2>Contract</h2>")
    for doc in manifest["documents"]:
        text = (task_dir / doc["path"]).read_text()
        body.append(f"<h3>{html.escape(doc['title'])}</h3>")
        body.append(_render_doc(text, doc["doc_id"], planted["deviations"], flags, score, canaries))
    body.append("<h2>Submitted Card</h2>")
    body.append("<pre class='json'>" + html.escape(json.dumps(card, indent=2, sort_keys=True)) + "</pre>")
    body.append("<h2>Flags</h2>")
    body.append("<pre class='json'>" + html.escape(json.dumps(flags, indent=2, sort_keys=True)) + "</pre>")
    body.append("<h2>Escalations</h2>")
    body.append("<pre class='json'>" + html.escape(json.dumps(escalations, indent=2, sort_keys=True)) + "</pre>")
    body.append("</body></html>")
    out = episode_dir / "report.html"
    out.write_text("\n".join(body))
    return out


def render_index(run_dir: Path, episode_dirs: list[Path]) -> Path:
    rows = []
    for episode_dir in episode_dirs:
        score = _read_json(episode_dir / "score.json")
        cells = [
            f"<td><a href='{html.escape(episode_dir.name)}/report.html'>{html.escape(score['task_id'])}</a></td>",
            f"<td>{score['composite']:.6f}</td>",
        ]
        for channel in score["weights"]:
            cells.append(f"<td>{score['channels'][channel]:.3f}</td>")
        cells.append(f"<td>{html.escape(score['status'])}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    headers = "".join(f"<th>{html.escape(name)}</th>" for name in ["task", "composite", *(_channel_order(episode_dirs)), "status"])
    out = run_dir / "index.html"
    out.write_text(
        "\n".join(
            [
                "<!doctype html>",
                "<html><head><meta charset='utf-8'>",
                f"<title>{html.escape(run_dir.name)} Redline Gym Summary</title>",
                _style(),
                "</head><body>",
                f"<h1>{html.escape(run_dir.name)}</h1>",
                "<table><thead><tr>" + headers + "</tr></thead><tbody>",
                *rows,
                "</tbody></table>",
                "</body></html>",
            ]
        )
    )
    return out


def _channel_order(episode_dirs: list[Path]) -> list[str]:
    if not episode_dirs:
        return ["recall", "precision", "grounding", "fallback", "conformance", "abstention"]
    return list(_read_json(episode_dirs[0] / "score.json")["weights"].keys())


def _score_section(score: dict[str, Any]) -> str:
    rows = [
        f"<p><strong>Status:</strong> {html.escape(score['status'])} "
        f"<strong>Composite:</strong> {score['composite']:.6f}</p>",
        "<div class='bars'>",
    ]
    for channel, value in score["channels"].items():
        pct = max(0.0, min(1.0, float(value))) * 100
        rows.append(
            f"<div class='bar-row'><span>{html.escape(channel)}</span>"
            f"<div class='bar'><div style='width:{pct:.1f}%'></div></div>"
            f"<b>{value:.3f}</b></div>"
        )
    rows.append("</div>")
    return "\n".join(rows)


def _render_doc(
    text: str,
    doc_id: str,
    deviations: list[dict[str, Any]],
    flags: list[dict[str, Any]],
    score: dict[str, Any],
    canaries: set[str],
) -> str:
    intervals: list[tuple[int, int, str, str, int]] = []
    matched = set(score["matched_deviation_ids"])
    for dev in deviations:
        if dev["doc_id"] != doc_id:
            continue
        cls = "caught" if dev["deviation_id"] in matched else "missed"
        _add_interval(intervals, text, dev["clause_anchor"]["span"], cls, dev["deviation_id"], 1)
    for flag in flags:
        if flag.get("doc_id") != doc_id:
            continue
        quote = str(flag.get("exact_quote", ""))
        if not quote:
            continue
        if flag.get("rule_id") in canaries:
            _add_interval(intervals, text, quote, "canary", f"canary {flag.get('rule_id')}", 3)
        elif _match_flag(flag, deviations) is None:
            _add_interval(intervals, text, quote, "falseflag", f"false flag {flag.get('rule_id')}", 2)
    return "<pre class='contract'>" + _highlight(text, intervals) + "</pre>"


def _add_interval(
    intervals: list[tuple[int, int, str, str, int]],
    text: str,
    snippet: str,
    cls: str,
    title: str,
    priority: int,
) -> None:
    if not snippet:
        return
    start = text.find(snippet)
    while start != -1:
        intervals.append((start, start + len(snippet), cls, title, priority))
        start = text.find(snippet, start + len(snippet))


def _highlight(text: str, intervals: list[tuple[int, int, str, str, int]]) -> str:
    intervals = sorted(intervals, key=lambda item: (item[0], -item[4], -(item[1] - item[0])))
    chosen: list[tuple[int, int, str, str, int]] = []
    cursor = 0
    for item in intervals:
        if item[0] < cursor:
            continue
        chosen.append(item)
        cursor = item[1]
    parts: list[str] = []
    cursor = 0
    for start, end, cls, title, _priority in chosen:
        parts.append(html.escape(text[cursor:start]))
        parts.append(f"<span class='hl {cls}' title='{html.escape(title)}'>")
        parts.append(html.escape(text[start:end]))
        parts.append("</span>")
        cursor = end
    parts.append(html.escape(text[cursor:]))
    return "".join(parts)


def _match_flag(flag: dict[str, Any], deviations: list[dict[str, Any]]) -> dict[str, Any] | None:
    for dev in deviations:
        if flag.get("rule_id") != dev["rule_id"] or flag.get("doc_id") != dev["doc_id"]:
            continue
        clause_ref = str(flag.get("clause_ref", ""))
        quote = flag.get("exact_quote", "")
        if dev["clause_anchor"]["section"] in clause_ref or quote in dev["clause_anchor"]["span"]:
            return dev
    return None


def _transcript_payloads(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    flags: list[dict[str, Any]] = []
    escalations: list[dict[str, Any]] = []
    card: dict[str, Any] = {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        action = record.get("action", {})
        kind = action.get("action")
        if kind == "flag_issue":
            flags.append({k: v for k, v in action.items() if k != "action"})
        elif kind == "escalate":
            escalations.append({"topic": action.get("topic", ""), "reason": action.get("reason", "")})
        elif kind == "finalize":
            candidate = action.get("card")
            card = candidate if isinstance(candidate, dict) else {}
    return flags, escalations, card


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _style() -> str:
    return """<style>
body{font-family:Arial,sans-serif;margin:28px;line-height:1.4;color:#202124;background:#fff}
h1,h2,h3{margin:18px 0 8px}
table{border-collapse:collapse;width:100%;margin-top:12px}
th,td{border:1px solid #c9ced6;padding:6px 8px;text-align:left}
th{background:#eef2f7}
.contract,.json{white-space:pre-wrap;border:1px solid #c9ced6;padding:12px;background:#fafafa;overflow:auto}
.hl{padding:1px 2px;border-radius:2px}
.caught{background:#b7f0c2}
.missed{background:#ffb6b6}
.falseflag{background:#fff08a}
.canary{background:#111;color:#fff}
.gamed{background:#111;color:#fff;padding:12px;font-weight:bold;margin:12px 0}
.bars{max-width:760px}
.bar-row{display:grid;grid-template-columns:120px 1fr 64px;gap:8px;align-items:center;margin:6px 0}
.bar{height:16px;border:1px solid #9aa0a6;background:#f1f3f4}
.bar div{height:100%;background:#3b7ddd}
</style>"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render Redline Gym static HTML reports.")
    parser.add_argument("--run", action="append", required=True, help="Run dir or single episode dir.")
    args = parser.parse_args(argv)
    outputs: list[Path] = []
    for run in args.run:
        outputs.extend(render_path(run))
    for output in outputs:
        print(output)
    return 0
