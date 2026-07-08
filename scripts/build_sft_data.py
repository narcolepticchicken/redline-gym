from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    build_sft_data(
        manifest=args.manifest,
        min_composite=args.min_composite,
        top_k_per_task=args.top_k_per_task,
        out=args.out,
    )
    return 0


def build_sft_data(*, manifest: Path, min_composite: float, top_k_per_task: int, out: Path) -> list[dict[str, Any]]:
    if top_k_per_task < 1:
        raise ValueError("--top-k-per-task must be >= 1")
    rows = _read_jsonl(manifest)
    for row in rows:
        _reject_heldout(Path(row["task"]))
    selected = select_episodes(rows, min_composite=min_composite, top_k_per_task=top_k_per_task)
    out.parent.mkdir(parents=True, exist_ok=True)
    training_rows = [episode_to_training_row(row) for row in selected]
    with out.open("w") as fh:
        for row in training_rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    print(json.dumps(selection_stats(rows, selected), indent=2, sort_keys=True))
    return training_rows


def select_episodes(
    rows: list[dict[str, Any]], *, min_composite: float, top_k_per_task: int
) -> list[dict[str, Any]]:
    by_task: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        composite = float(row.get("composite", 0))
        if composite >= min_composite:
            by_task.setdefault(str(row["task"]), []).append(row)
    selected: list[dict[str, Any]] = []
    for task_rows in by_task.values():
        task_rows.sort(key=lambda row: (-float(row["composite"]), int(row.get("sample_idx", 0))))
        selected.extend(task_rows[:top_k_per_task])
    selected.sort(key=lambda row: (str(row["task"]), int(row.get("sample_idx", 0))))
    return selected


def episode_to_training_row(row: dict[str, Any]) -> dict[str, Any]:
    run_dir = Path(row["run_dir"])
    transcript_path = run_dir / "episode.jsonl"
    conversation_path = run_dir / "driver_conversation.jsonl"
    if not transcript_path.exists():
        raise FileNotFoundError(f"missing episode transcript: {transcript_path}")
    if not conversation_path.exists():
        raise FileNotFoundError(f"missing driver conversation log: {conversation_path}")
    # Load the episode transcript as the audited source for the rollout, while
    # using the driver conversation for exact user prompts and raw replies.
    transcript = _read_jsonl(transcript_path)
    messages = _conversation_messages(conversation_path)
    if not any(message["role"] == "assistant" for message in messages) and transcript:
        raise ValueError(f"conversation log has no assistant turns: {conversation_path}")
    return {"messages": messages}


def _conversation_messages(path: Path) -> list[dict[str, str]]:
    raw = _read_jsonl(path)
    messages: list[dict[str, str]] = []
    pending_user: dict[str, Any] | None = None
    for record in raw:
        role = record.get("role")
        if role == "system":
            messages.append({"role": "system", "content": str(record.get("content", ""))})
        elif role == "user":
            pending_user = record
        elif role == "assistant":
            if record.get("salvage_finalize"):
                pending_user = None
                continue
            if pending_user is None:
                raise ValueError(f"assistant turn without preceding user turn in {path}")
            messages.append({"role": "user", "content": str(pending_user.get("content", ""))})
            messages.append({"role": "assistant", "content": str(record.get("content", ""))})
            pending_user = None
    if not messages or messages[0]["role"] != "system":
        raise ValueError(f"conversation log must begin with a system message: {path}")
    return messages


def selection_stats(rows: list[dict[str, Any]], selected: list[dict[str, Any]]) -> dict[str, Any]:
    rewards = [float(row.get("composite", 0)) for row in rows]
    selected_ids = {(str(row["task"]), int(row.get("sample_idx", 0))) for row in selected}
    dropped = [
        row for row in rows
        if (str(row["task"]), int(row.get("sample_idx", 0))) not in selected_ids
    ]
    return {
        "episodes_kept": len(selected),
        "episodes_dropped": len(dropped),
        "reward_distribution": {
            "count": len(rewards),
            "min": min(rewards) if rewards else None,
            "max": max(rewards) if rewards else None,
            "mean": mean(rewards) if rewards else None,
        },
    }


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text().splitlines():
        if line.strip():
            item = json.loads(line)
            if not isinstance(item, dict):
                raise ValueError(f"JSONL row must be an object in {path}")
            rows.append(item)
    return rows


def _reject_heldout(task: Path) -> None:
    parts = task.parts
    if "tasks" in parts and "heldout" in parts:
        raise ValueError(f"heldout task is not allowed in pilot SFT data: {task}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build mlx_lm chat-format SFT rows from pilot rollout manifest.")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--min-composite", type=float, required=True)
    parser.add_argument("--top-k-per-task", type=int, required=True)
    parser.add_argument("--out", type=Path, default=Path("data/pilot_sft.jsonl"))
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
