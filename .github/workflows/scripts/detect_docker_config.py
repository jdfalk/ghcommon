#!/usr/bin/env python3
"""Determine the Dockerfile path and whether a build should run.

Outputs (written to $GITHUB_OUTPUT):
  dockerfile-path=<path>
  should-build=<true|false>
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path

DOCKERFILE_CANDIDATES: Iterable[str] = (
    "Dockerfile",
    "docker/Dockerfile",
    "build/Dockerfile",
)


def main() -> None:
    override = (os.environ.get("OVERRIDE_DOCKERFILE") or "").strip()
    candidates = list(DOCKERFILE_CANDIDATES)
    if override:
        candidates.insert(0, override)

    dockerfile_path: str | None = None
    for candidate in candidates:
        if Path(candidate).exists():
            dockerfile_path = candidate
            break

    should_build = "true"
    if dockerfile_path is None:
        dockerfile_path = "Dockerfile"
        should_build = "false"

    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        with open(output_path, "a", encoding="utf-8") as handle:
            handle.write(f"dockerfile-path={dockerfile_path}\n")
            handle.write(f"should-build={should_build}\n")

    print(f"Detected Dockerfile: {dockerfile_path} (should_build={should_build})")


if __name__ == "__main__":
    main()
