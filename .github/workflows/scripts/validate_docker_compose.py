#!/usr/bin/env python3
"""Validate docker-compose style files if present."""

from __future__ import annotations

import subprocess
from pathlib import Path

COMPOSE_FILES = (
    "docker-compose.yml",
    "docker-compose.yaml",
    "docker-stack.yml",
    "docker-stack-jf.yml",
)


def validate(path: Path) -> int:
    result = subprocess.run(
        ["docker-compose", "-f", str(path), "config"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print(f"{path} is valid")
    else:
        print(f"{path} validation failed:\n{result.stderr}")
    return result.returncode


def main() -> None:
    found = False
    exit_code = 0
    for name in COMPOSE_FILES:
        candidate = Path(name)
        if candidate.exists():
            found = True
            if validate(candidate) != 0:
                exit_code = 1
    if not found:
        print("No Docker Compose files found")
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
