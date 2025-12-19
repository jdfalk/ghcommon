#!/usr/bin/env python3
# file: .github/workflows/scripts/capture_benchmark_metrics.py
# version: 1.0.0
# guid: 0c1d2e3f-4a5b-6789-0abc-def123456789

"""Capture benchmark metrics and emit GitHub Actions outputs."""

from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path
from typing import Any


def fmt(value: float | int | None) -> str:
    """Format numeric values for summary output."""
    if value is None:
        return "n/a"
    if isinstance(value, float) and math.isnan(value):
        return "n/a"
    return f"{value:.6f}"


def load_entry(path: Path) -> dict[str, Any]:
    """Load the first entry from a benchmark JSON file."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list) and data:
        return data[0]
    if isinstance(data, dict):
        return data
    raise ValueError(f"Unexpected data format in {path}")


def write_output(average: str, best: str, worst: str) -> None:
    """Write outputs to GITHUB_OUTPUT."""
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return

    with Path(output_path).open("a", encoding="utf-8") as handle:
        handle.write(f"average={average}\n")
        handle.write(f"best={best}\n")
        handle.write(f"worst={worst}\n")


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: capture_benchmark_metrics.py <benchmark-file>", file=sys.stderr)
        return 1

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"Benchmark file not found: {path}", file=sys.stderr)
        return 1

    entry = load_entry(path)
    average = entry.get("average_seconds", entry.get("value"))
    best = entry.get("best_seconds", entry.get("value"))
    worst = entry.get("worst_seconds", entry.get("value"))

    average_fmt, best_fmt, worst_fmt = fmt(average), fmt(best), fmt(worst)
    write_output(average_fmt, best_fmt, worst_fmt)

    print(
        f"Captured metrics from {path}: average={average_fmt}, best={best_fmt}, worst={worst_fmt}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
