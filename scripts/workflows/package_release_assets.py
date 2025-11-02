#!/usr/bin/env python3
"""Organize release artifacts and generate a manifest."""

from __future__ import annotations

import datetime as _dt
import os
import shutil
import sys
from pathlib import Path


def _categorize(name: str) -> str | None:
    lower = name.lower()
    if "-sdk." in lower:
        return "sdks"
    if "docs" in lower:
        return "documentation"
    if lower.endswith(".exe") or any(
        token in lower for token in ("-linux-", "-darwin-", "-windows-")
    ):
        return "binaries"
    if lower.endswith((".whl", ".tar.gz", ".zip")):
        return "packages"
    return None


def main() -> None:
    release_version = (
        sys.argv[1] if len(sys.argv) > 1 else os.environ.get("RELEASE_VERSION", "unknown")
    )
    artifacts_root = Path("artifacts")
    target_root = Path("release-assets")

    categories = {
        "sdks": target_root / "sdks",
        "documentation": target_root / "documentation",
        "binaries": target_root / "binaries",
        "packages": target_root / "packages",
    }

    target_root.mkdir(parents=True, exist_ok=True)
    for destination in categories.values():
        destination.mkdir(parents=True, exist_ok=True)

    moved_files: list[tuple[Path, int]] = []
    if artifacts_root.exists():
        for file_path in artifacts_root.rglob("*"):
            if not file_path.is_file():
                continue
            category = _categorize(file_path.name)
            if not category:
                continue
            destination = categories[category] / file_path.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(file_path), destination)
            moved_files.append(
                (
                    destination.relative_to(target_root),
                    destination.stat().st_size,
                )
            )

    manifest_sections: list[str] = [
        f"# Release Manifest - {release_version}",
        f"Generated: {_dt.datetime.utcnow():%Y-%m-%d %H:%M:%S} UTC",
        "",
    ]

    for title, directory in categories.items():
        manifest_sections.append(f"## {title.replace('_', ' ').title()}")
        files = sorted(directory.iterdir()) if directory.exists() else []
        if files:
            for item in files:
                if item.is_file():
                    manifest_sections.append(f"- {item.name} ({item.stat().st_size} bytes)")
        else:
            manifest_sections.append("- None")
        manifest_sections.append("")

    (target_root / "MANIFEST.md").write_text("\n".join(manifest_sections), encoding="utf-8")

    total_files = sum(1 for _ in target_root.rglob("*"))
    print("📦 Organizing and packaging release artifacts...")
    print(f"Total files: {total_files}")
    for rel_path, size in moved_files[:10]:
        print(f"  {rel_path} ({size} bytes)")

    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        with Path(output_path).open("a", encoding="utf-8") as handle:
            handle.write("packaging-complete=true\n")


if __name__ == "__main__":
    main()
