#!/usr/bin/env python3
# file: scripts/template_repo/validate_template_repo.py
# version: 1.0.0
# guid: 5c1d2e3f-4a5b-6c7d-8e9f-0a1b2c3d4e5f

"""Validate that a directory contains no obvious secrets before publishing.

This is a conservative, pattern-based scanner intended to catch common mistakes.
It avoids scanning large/binary files and respects typical ignore directories.

It never uploads data anywhere. All checks are local-only.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections.abc import Iterable
from pathlib import Path

DEFAULT_IGNORE_DIRS = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "dist",
    "build",
    "logs",
    "__pycache__",
}

TEXT_FILE_EXTENSIONS = {
    ".md",
    ".txt",
    ".yml",
    ".yaml",
    ".json",
    ".toml",
    ".py",
    ".sh",
    ".go",
    ".js",
    ".ts",
    ".proto",
    ".env",
    ".ini",
    ".cfg",
    ".conf",
}

# Common secret-like patterns. Intentionally generic to catch accidents.
PATTERNS: list[tuple[str, re.Pattern]] = [
    (
        "Generic API Key",
        re.compile(
            r"(?i)(api[_-]?key|access[_-]?key|secret[_-]?key)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{12,}['\"]?"
        ),
    ),
    ("AWS Access Key", re.compile(r"AKIA[0-9A-Z]{16}")),
    (
        "AWS Secret Key",
        re.compile(r"(?i)aws(.{0,20})?(secret|sk)[\s:]*[A-Za-z0-9/+=]{30,}"),
    ),
    ("GitHub Token", re.compile(r"gh[pousr]_[A-Za-z0-9_]{30,}")),
    (
        "JWT",
        re.compile(
            r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"
        ),
    ),
    (
        "Private Key Block",
        re.compile(r"-----BEGIN (RSA |EC |OPENSSH |)PRIVATE KEY-----"),
    ),
    (
        "Password Assignment",
        re.compile(r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{6,}['\"]"),
    ),
]


def looks_text_file(path: Path) -> bool:
    if path.suffix.lower() in TEXT_FILE_EXTENSIONS:
        return True
    # Fallback: try to read a small chunk and check if it's mostly printable
    try:
        with path.open("rb") as f:
            chunk = f.read(1024)
        if not chunk:
            return True
        # Heuristic: if 95%+ bytes are printable or whitespace
        printable = sum(c in b"\t\n\r\x0b\x0c" or 32 <= c <= 126 for c in chunk)
        return printable / max(1, len(chunk)) > 0.95
    except Exception:
        return False


def iter_files(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        # prune ignored directories
        dirnames[:] = [d for d in dirnames if d not in DEFAULT_IGNORE_DIRS]
        for name in filenames:
            p = Path(dirpath) / name
            if p.is_symlink():
                continue
            yield p


def scan_file(path: Path) -> list[tuple[str, int, str]]:
    results: list[tuple[str, int, str]] = []
    if not looks_text_file(path):
        return results
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return results
    lines = content.splitlines()
    for idx, line in enumerate(lines, start=1):
        for name, pattern in PATTERNS:
            if pattern.search(line):
                # Include a clipped preview, not the full match
                preview = line.strip()
                if len(preview) > 160:
                    preview = preview[:160] + "…"
                results.append((name, idx, preview))
    return results


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a directory contains no obvious secrets."
    )
    parser.add_argument("target", help="Directory to scan")
    args = parser.parse_args(argv)
    root = Path(args.target).resolve()
    if not root.exists() or not root.is_dir():
        print(
            f"Target does not exist or is not a directory: {root}",
            file=sys.stderr,
        )
        return 2

    findings = 0
    for path in iter_files(root):
        for name, line_no, preview in scan_file(path):
            findings += 1
            rel = path.relative_to(root)
            print(f"[POTENTIAL SECRET] {name}: {rel}:{line_no}: {preview}")

    if findings:
        print(f"Scan complete: {findings} potential issue(s) found.")
        return 1
    print("Scan complete: no potential secrets detected.")
    return 0


if __name__ == "__main__":
    import sys as _sys

    raise SystemExit(main(_sys.argv[1:]))
