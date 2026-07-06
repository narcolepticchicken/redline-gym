from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .checks import run_all, write_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Redline Gym instance validators.")
    parser.add_argument("task_dir", type=Path)
    args = parser.parse_args(argv)
    results = run_all(args.task_dir)
    print(f"{'Validator':<14} {'Status':<8} Detail")
    print(f"{'-' * 14} {'-' * 8} {'-' * 40}")
    for result in results:
        print(f"{result.code:<14} {result.status:<8} {result.detail}")
    report = write_report(args.task_dir, results)
    print(f"\nWrote {report}")
    return 1 if any(r.status == "FAIL" for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
