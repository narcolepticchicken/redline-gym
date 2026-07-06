"""Model-backed checks are intentionally unavailable in Phase 1."""

from __future__ import annotations

from dataclasses import dataclass
import os
import argparse


PHASE_BOUNDARY_MESSAGE = "requires lab serving lane -- do not run from build tooling"


@dataclass(frozen=True)
class ModelCheckConfig:
    provider: str | None
    model: str | None
    endpoint: str | None

    @classmethod
    def from_env(cls) -> "ModelCheckConfig":
        return cls(
            provider=os.getenv("REDLINE_GYM_MODEL_PROVIDER"),
            model=os.getenv("REDLINE_GYM_MODEL"),
            endpoint=os.getenv("REDLINE_GYM_MODEL_ENDPOINT"),
        )


class ModelCheck:
    """Interface for checks that require the lab serving lane."""

    def __init__(self, config: ModelCheckConfig | None = None) -> None:
        self.config = config or ModelCheckConfig.from_env()

    def clean_base_judge_pass(self, *_: object, **__: object) -> None:
        raise NotImplementedError(PHASE_BOUNDARY_MESSAGE)

    def round_trip_extractor(self, *_: object, **__: object) -> None:
        raise NotImplementedError(PHASE_BOUNDARY_MESSAGE)

    def missing_info_semantic_search(self, *_: object, **__: object) -> None:
        raise NotImplementedError(PHASE_BOUNDARY_MESSAGE)

    def realism_judge(self, *_: object, **__: object) -> None:
        raise NotImplementedError(PHASE_BOUNDARY_MESSAGE)

    def fallback_tiebreak_judge(self, *_: object, **__: object) -> None:
        raise NotImplementedError(PHASE_BOUNDARY_MESSAGE)


def main() -> int:
    parser = argparse.ArgumentParser(description="Invoke a model-backed Redline Gym check.")
    parser.add_argument(
        "check",
        choices=[
            "v3-clean-base",
            "v4-round-trip",
            "v7-semantic",
            "v11-realism",
            "channel4-fallback-tiebreak",
        ],
    )
    args = parser.parse_args()
    checks = ModelCheck()
    dispatch = {
        "v3-clean-base": checks.clean_base_judge_pass,
        "v4-round-trip": checks.round_trip_extractor,
        "v7-semantic": checks.missing_info_semantic_search,
        "v11-realism": checks.realism_judge,
        "channel4-fallback-tiebreak": checks.fallback_tiebreak_judge,
    }
    dispatch[args.check]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
