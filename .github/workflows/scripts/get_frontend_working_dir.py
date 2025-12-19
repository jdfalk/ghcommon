#!/usr/bin/env python3
# file: .github/workflows/scripts/get_frontend_working_dir.py
# version: 1.0.0
# guid: 1234abcd-56ef-78ab-90cd-ef1234567890

"""Determine frontend working directory from repository config."""

from __future__ import annotations

import json
import os
from pathlib import Path

DEFAULT_DIR = "."


def load_config() -> dict:
    """Load repository configuration from REPOSITORY_CONFIG env var."""
    raw = os.environ.get("REPOSITORY_CONFIG", "{}")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def determine_frontend_dir(config: dict) -> str:
    """Return frontend working directory path."""
    return config.get("working_directories", {}).get("frontend", DEFAULT_DIR) or DEFAULT_DIR


def write_outputs(directory: str) -> None:
    """Write dir and cache-path outputs."""
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return

    cache_path = f"{directory}/package-lock.json" if directory != "." else "package-lock.json"
    with Path(output_path).open("a", encoding="utf-8") as handle:
        handle.write(f"dir={directory}\n")
        handle.write(f"cache-path={cache_path}\n")


def main() -> int:
    config = load_config()
    directory = determine_frontend_dir(config)
    write_outputs(directory)
    print(directory)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
