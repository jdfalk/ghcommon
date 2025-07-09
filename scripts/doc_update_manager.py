#!/usr/bin/env python3
# file: scripts/doc_update_manager.py
# version: 1.0.0
# guid: 9e1fdb20-7abd-4b66-b5b5-95180715d24c
"""Apply documentation updates from JSON files."""

from __future__ import annotations

import json
from pathlib import Path
import sys


def apply_update(update: dict[str, str]) -> None:
    path = Path(update["file"])
    mode = update.get("mode", "append")
    content = update.get("content", "")

    if mode == "append":
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        with path.open("w", encoding="utf-8") as fh:
            fh.write(text.rstrip() + "\n" + content + "\n")
    elif mode == "replace":
        with path.open("w", encoding="utf-8") as fh:
            fh.write(content + "\n")


def process(directory: str) -> list[Path]:
    updates_dir = Path(directory)
    processed: list[Path] = []

    for file in sorted(updates_dir.glob("*.json")):
        with file.open(encoding="utf-8") as fh:
            update = json.load(fh)
        apply_update(update)
        processed.append(file)
    if processed:
        processed_dir = updates_dir / "processed"
        processed_dir.mkdir(exist_ok=True)
        for file in processed:
            file.rename(processed_dir / file.name)
    return processed


def main(argv: list[str]) -> None:
    directory = argv[1] if len(argv) > 1 else ".github/doc-updates"
    files = process(directory)
    if files:
        print(f"Processed {len(files)} documentation updates")
        for file in files:
            print(f"- {file.name}")
    else:
        print("No documentation updates found")


if __name__ == "__main__":
    main(sys.argv)
