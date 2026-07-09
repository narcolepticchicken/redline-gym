from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path
from statistics import mean
import sys
import tempfile
from typing import Any
import warnings

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from baselines.honest_llm import SYSTEM_PROMPT as HONEST_LLM_SYSTEM_PROMPT
from baselines.llm_common import DRIVER_CONVERSATION, observation_prompt
from env import Episode


ROOT = Path(__file__).resolve().parents[1]
COLLECT_V1 = (ROOT / "runs_pilot" / "collect_v1").resolve()


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.from_runs:
        max_per_task = args.max_per_task if args.max_per_task is not None else args.top_k_per_task
        if max_per_task is None:
            raise SystemExit("--from-runs requires --max-per-task")
        build_sft_data_from_runs(
            run_globs=args.from_runs,
            min_composite=args.min_composite,
            max_per_task=max_per_task,
            out=args.out,
            sidecar_manifest=args.sidecar_manifest,
        )
    else:
        if args.manifest is None or args.top_k_per_task is None:
            raise SystemExit("--manifest and --top-k-per-task are required unless --from-runs is used")
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


def build_sft_data_from_runs(
    *,
    run_globs: list[str],
    min_composite: float,
    max_per_task: int,
    out: Path,
    sidecar_manifest: Path = Path("data/pilot_sft_manifest.jsonl"),
) -> list[dict[str, Any]]:
    if max_per_task < 1:
        raise ValueError("--max-per-task must be >= 1")
    rows = rows_from_run_globs(run_globs)
    selected = select_episodes(rows, min_composite=min_composite, top_k_per_task=max_per_task)

    training_rows: list[dict[str, Any]] = []
    manifest_rows: list[dict[str, Any]] = []
    for row in selected:
        try:
            training_rows.append(episode_to_training_row(row))
        except ReplayMismatchError as exc:
            warnings.warn(str(exc))
            continue
        manifest_rows.append({"source": _source_manifest(row)})

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as fh:
        for row in training_rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    sidecar_manifest.parent.mkdir(parents=True, exist_ok=True)
    with sidecar_manifest.open("w") as fh:
        for row in manifest_rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    print(json.dumps(selection_stats(rows, selected), indent=2, sort_keys=True))
    return training_rows


class ReplayMismatchError(RuntimeError):
    pass


def rows_from_run_globs(run_globs: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    sample_idx = 0
    for episode_dir in _episode_dirs_from_globs(run_globs):
        task_id = episode_dir.name
        try:
            task_dir = _resolve_task_dir(task_id)
            _reject_heldout(task_dir)
            seed_score = _read_json(episode_dir / "score.json")
            selected_score_path = episode_dir / "score_v2.json"
            if selected_score_path.exists():
                score = _read_json(selected_score_path)
            else:
                selected_score_path = episode_dir / "score.json"
                score = seed_score
        except (FileNotFoundError, KeyError, ValueError, json.JSONDecodeError) as exc:
            warnings.warn(f"skipping {episode_dir}: {exc}")
            continue

        run_dir = episode_dir.parent
        rows.append(
            {
                "task": str(task_dir),
                "task_id": task_id,
                "sample_idx": sample_idx,
                "episode_dir": str(episode_dir),
                "run_dir": str(episode_dir),
                "source_run_dir": str(run_dir),
                "composite": float(score.get("composite", 0)),
                "scorer_version": _scorer_version(score, selected_score_path),
                "teacher_model": _teacher_model_label(run_dir),
                "score_path": str(selected_score_path),
                "seed": int(seed_score["seed"]),
            }
        )
        sample_idx += 1
    return rows


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
    conversation_path = run_dir / DRIVER_CONVERSATION
    if not transcript_path.exists():
        raise FileNotFoundError(f"missing episode transcript: {transcript_path}")
    if not conversation_path.exists():
        return {"messages": reconstruct_conversation(row)}
    # Load the episode transcript as the audited source for the rollout, while
    # using the driver conversation for exact user prompts and raw replies.
    transcript = _read_jsonl(transcript_path)
    messages = _conversation_messages(conversation_path)
    if not any(message["role"] == "assistant" for message in messages) and transcript:
        raise ValueError(f"conversation log has no assistant turns: {conversation_path}")
    return {"messages": messages}


def reconstruct_conversation(row: dict[str, Any]) -> list[dict[str, str]]:
    task_dir = Path(row["task"])
    run_dir = Path(row["run_dir"])
    transcript_path = run_dir / "episode.jsonl"
    transcript = _read_jsonl(transcript_path)
    messages: list[dict[str, str]] = [{"role": "system", "content": HONEST_LLM_SYSTEM_PROMPT}]
    with tempfile.TemporaryDirectory(prefix="redline-sft-replay-") as tmp:
        episode = Episode(task_dir, seed=int(row["seed"]), run_dir=Path(tmp))
        observation = episode.reset()
        for record in transcript:
            action = record.get("action")
            if not isinstance(action, dict):
                raise ReplayMismatchError(f"skipping {run_dir}: transcript action is not an object")
            messages.append({"role": "user", "content": observation_prompt(observation)})
            # Old runs did not persist raw model replies. Compact JSON is a
            # faithful surrogate for the recorded action object used by Episode.
            messages.append({"role": "assistant", "content": json.dumps(action, separators=(",", ":"), sort_keys=True)})
            observation = episode.step(action)
            recorded_observation = record.get("observation")
            recorded_event = recorded_observation.get("event") if isinstance(recorded_observation, dict) else None
            replayed_event = observation.get("event")
            if replayed_event != recorded_event:
                turn = record.get("turn", episode.num_turns)
                raise ReplayMismatchError(
                    f"skipping {run_dir}: replay event mismatch at turn {turn}: "
                    f"recorded={recorded_event!r} replayed={replayed_event!r}"
                )
    return messages


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


def _read_json(path: Path) -> dict[str, Any]:
    item = json.loads(path.read_text())
    if not isinstance(item, dict):
        raise ValueError(f"JSON file must contain an object: {path}")
    return item


def _episode_dirs_from_globs(run_globs: list[str]) -> list[Path]:
    episode_dirs: list[Path] = []
    seen: set[Path] = set()
    for pattern in run_globs:
        matches = sorted(glob.glob(pattern))
        for match in matches:
            run_dir = Path(match).resolve()
            if _is_under(run_dir, COLLECT_V1):
                warnings.warn(f"skipping active collection path: {run_dir}")
                continue
            if run_dir.name == "episode.jsonl":
                candidates = [run_dir]
            elif (run_dir / "episode.jsonl").exists():
                candidates = [run_dir]
            else:
                candidates = sorted(run_dir.glob("*/episode.jsonl"))
            for candidate in candidates:
                episode_dir = candidate if candidate.name != "episode.jsonl" else candidate.parent
                if episode_dir not in seen:
                    seen.add(episode_dir)
                    episode_dirs.append(episode_dir)
    return episode_dirs


def _resolve_task_dir(task_id: str) -> Path:
    for root in [ROOT / "tasks" / "contracts", ROOT / "tasks" / "generated"]:
        candidate = root / task_id
        if (candidate / "task.json").exists():
            return candidate
    raise FileNotFoundError(f"missing task directory for {task_id}")


def _scorer_version(score: dict[str, Any], score_path: Path) -> str:
    if "scorer_version" in score:
        return str(score["scorer_version"])
    if score_path.name == "score_v2.json":
        return "v2"
    return "v1"


def _teacher_model_label(run_dir: Path) -> str:
    name = run_dir.name
    marker = "-seed"
    if marker in name:
        return name.rsplit(marker, 1)[0]
    return name


def _source_manifest(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_dir": row.get("source_run_dir", row["run_dir"]),
        "episode_dir": row["run_dir"],
        "task": row["task"],
        "task_id": row["task_id"],
        "composite": row["composite"],
        "scorer_version": row["scorer_version"],
        "teacher_model": row["teacher_model"],
    }


def _is_under(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _reject_heldout(task: Path) -> None:
    parts = task.parts
    if "tasks" in parts and "heldout" in parts:
        raise ValueError(f"heldout task is not allowed in pilot SFT data: {task}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build mlx_lm chat-format SFT rows from pilot rollout manifest.")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--from-runs", nargs="+", help="Run-directory globs containing <run>/<task_id>/episode.jsonl files.")
    parser.add_argument("--min-composite", type=float, required=True)
    parser.add_argument("--top-k-per-task", type=int)
    parser.add_argument("--max-per-task", type=int)
    parser.add_argument("--out", type=Path, default=Path("data/pilot_sft.jsonl"))
    parser.add_argument("--sidecar-manifest", type=Path, default=Path("data/pilot_sft_manifest.jsonl"))
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
