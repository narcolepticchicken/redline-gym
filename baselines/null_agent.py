from __future__ import annotations

from env import Episode

from .common import run_baseline


NAME = "null_agent"


def drive(episode: Episode) -> None:
    episode.step(
        {
            "action": "finalize",
            "card": {
                "summary": "No issues identified.",
                "issues": [],
                "escalations": [],
            },
        }
    )


def main(argv: list[str] | None = None) -> int:
    return run_baseline(NAME, argv, drive)


if __name__ == "__main__":
    raise SystemExit(main())
