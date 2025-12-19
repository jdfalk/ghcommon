#!/usr/bin/env python3
# file: .github/workflows/scripts/detect_languages.py
# version: 1.0.0
# guid: 7d6f5c4b-3a2f-4b1c-8d9e-0f1a2b3c4d5e

"""Detect repository languages for security workflows."""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Iterable
from pathlib import Path


def has_files(root: Path, patterns: Iterable[str]) -> bool:
    """Return True if any file matching patterns exists under root."""
    return any(any(root.rglob(pattern)) for pattern in patterns)


def detect_languages(root: Path) -> list[str]:
    """Detect languages based on common project files."""
    languages: list[str] = []

    if any((root / name).exists() for name in ("go.mod", "go.work")):
        languages.append("go")

    if (root / "package.json").exists() or has_files(root, ("*.js", "*.ts", "*.jsx", "*.tsx")):
        languages.append("javascript")

    if any(
        (root / name).exists() for name in ("requirements.txt", "setup.py", "pyproject.toml")
    ) or has_files(root, ("*.py",)):
        languages.append("python")

    if any((root / name).exists() for name in ("pom.xml", "build.gradle")) or has_files(
        root, ("*.java",)
    ):
        languages.append("java")

    if has_files(root, ("*.c", "*.cpp", "*.cc", "*.cxx", "*.h", "*.hpp")):
        languages.append("cpp")

    if has_files(root, ("*.csproj", "*.sln", "*.cs")):
        languages.append("csharp")

    return languages


def write_output(languages: list[str]) -> None:
    """Write detection results to GITHUB_OUTPUT."""
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with Path(output_path).open("a", encoding="utf-8") as handle:
        handle.write(f"languages={json.dumps(languages)}\n")


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    languages = detect_languages(root)
    write_output(languages)
    print(f"Detected languages: {json.dumps(languages)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
