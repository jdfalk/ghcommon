#!/usr/bin/env python3
"""Utility to benchmark shell commands and export results for github-action-benchmark.

The script runs the provided command multiple times, measures wall-clock duration,
and writes a JSON array where the first entry contains summary statistics that the
`customSmallerIsBetter` tool understands.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import json
import math
from pathlib import Path
import statistics
import subprocess
import time


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Measure command execution time."
    )
    parser.add_argument(
        "--label", required=True, help="Benchmark label to report."
    )
    parser.add_argument(
        "--command",
        required=True,
        help=(
            "Command to execute. Use quotes for complex commands; executed via the shell "
            "for compatibility with existing tooling."
        ),
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=5,
        help="Number of times to execute the command (default: 5).",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=1,
        help="Number of warmup iterations to discard before recording timings (default: 1).",
    )
    parser.add_argument(
        "--workdir",
        default=".",
        help="Working directory in which to execute the command.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to write the benchmark JSON results.",
    )
    parser.add_argument(
        "--metadata",
        default="",
        help="Optional extra text appended to the benchmark metadata.",
    )
    return parser.parse_args()


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def run_command(command: str, cwd: Path) -> None:
    subprocess.run(command, shell=True, check=True, cwd=cwd)


def to_human(value: float) -> str:
    return f"{value:.6f}s"


def write_results(
    output: Path,
    label: str,
    durations: Sequence[float],
    metadata: str,
) -> None:
    ensure_parent(output)
    mean = statistics.fmean(durations) if durations else math.nan
    best = min(durations, default=math.nan)
    worst = max(durations, default=math.nan)

    extra_lines = [
        f"iterations: {len(durations)}",
        f"average: {to_human(mean)}",
    ]
    if durations:
        extra_lines.extend(
            [
                f"best: {to_human(best)}",
                f"worst: {to_human(worst)}",
                f"latest: {to_human(durations[-1])}",
            ]
        )
    if metadata:
        extra_lines.append(metadata)

    average = round(mean, 6) if durations else math.nan
    best_value = round(best, 6) if durations else math.nan
    worst_value = round(worst, 6) if durations else math.nan

    result = [
        {
            "name": label,
            "unit": "seconds",
            "value": average,
            "range": f"{to_human(best)} … {to_human(worst)}"
            if durations
            else "",
            "extra": "\n".join(extra_lines),
            "average_seconds": average,
            "best_seconds": best_value,
            "worst_seconds": worst_value,
        }
    ]

    with output.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")


def main() -> None:
    args = parse_args()
    iterations = max(args.iterations, 1)
    warmup = max(min(args.warmup, iterations - 1), 0)
    cwd = Path(args.workdir).resolve()
    output = Path(args.output).resolve()

    timings: list[float] = []
    for index in range(iterations + warmup):
        start = time.perf_counter()
        run_command(args.command, cwd)
        elapsed = time.perf_counter() - start
        if index >= warmup:
            timings.append(elapsed)

    write_results(output, args.label, timings, args.metadata)


if __name__ == "__main__":
    main()
