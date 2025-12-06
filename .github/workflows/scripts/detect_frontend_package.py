#!/usr/bin/env python3
"""Detect frontend package metadata for release workflow."""

from __future__ import annotations

import json
import os
from pathlib import Path

CANDIDATES = [Path("package.json"), *sorted(Path(".").glob("*/package.json"))]
LOCK_FILES = {
    "pnpm-lock.yaml": "pnpm",
    "yarn.lock": "yarn",
    "package-lock.json": "npm",
}


def emit_output(name: str, value: str) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        with open(output_path, "a", encoding="utf-8") as handle:
            handle.write(f"{name}={value}\n")


def detect_package() -> tuple[bool, str, str, str]:
    for candidate in CANDIDATES:
        if not candidate.exists():
            continue
        try:
            data = json.loads(candidate.read_text("utf-8"))
        except Exception:
            continue
        name = data.get("name")
        version = data.get("version") or ""
        if name:
            return True, candidate.parent.as_posix(), str(name), str(version)
    return False, ".", "", ""


def main() -> None:
    has_package, package_dir, package_name, package_version = detect_package()
    package_manager = "npm"
    if has_package:
        for filename, value in LOCK_FILES.items():
            if Path(package_dir).joinpath(filename).exists():
                package_manager = value
                break

    emit_output("has-package", "true" if has_package else "false")
    emit_output("package-dir", package_dir)
    emit_output("package-name", package_name)
    emit_output("package-version", package_version)
    emit_output("package-manager", package_manager)


if __name__ == "__main__":
    main()
