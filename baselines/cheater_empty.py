from __future__ import annotations

from env import Episode

from .common import run_baseline


NAME = "cheater_empty"


def drive(episode: Episode) -> None:
    card = {
        "summary": "No issues identified.",
        "issues": [],
        "escalations": [],
    }
    obs = episode.step({"action": "finalize", "card": card})
    if obs.get("event") == "confirm_finalize":
        # The empty cheater deliberately confirms its no-work submission.
        episode.step({"action": "finalize", "card": card})


def main(argv: list[str] | None = None) -> int:
    return run_baseline(NAME, argv, drive)


if __name__ == "__main__":
    raise SystemExit(main())
