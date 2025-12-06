#!/usr/bin/env python3
"""Organize release artifacts and generate a manifest."""

from __future__ import annotations

import datetime as _dt
import os
import shutil
import sys
from pathlib import Path


def _categorize(name: str) -> str | None:
    """Categorize a file based on its name."""
    lower = name.lower()

    # SDK packages
    if "-sdk." in lower:
        return "sdks"

    # Documentation
    if "docs" in lower:
        return "documentation"

    # Binary executables and platform-specific builds
    if lower.endswith(".exe") or any(
        token in lower for token in ("-linux-", "-darwin-", "-windows-")
    ):
        return "binaries"

    # Checksum files go with binaries
    if lower.endswith(".sha256") or lower.endswith(".sha512") or lower.endswith(".md5"):
        return "binaries"

    # Package archives
    if lower.endswith((".whl", ".tar.gz", ".zip")):
        return "packages"

    # Build manifests
    if "manifest" in lower and lower.endswith(".json"):
        return "binaries"

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

    moved_files: list[tuple[Path, int, str]] = []
    if artifacts_root.exists():
        for file_path in artifacts_root.rglob("*"):
            if not file_path.is_file():
                continue
            category = _categorize(file_path.name)
            if not category:
                print(f"⚠️  Skipping uncategorized file: {file_path.name}")
                continue
            destination = categories[category] / file_path.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(file_path), destination)
            moved_files.append(
                (
                    destination.relative_to(target_root),
                    destination.stat().st_size,
                    category,
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
                    size_mb = item.stat().st_size / (1024 * 1024)
                    if size_mb < 0.01:
                        size_str = f"{item.stat().st_size} bytes"
                    else:
                        size_str = f"{size_mb:.2f} MB"
                    manifest_sections.append(f"- {item.name} ({size_str})")
        else:
            manifest_sections.append("- None")
        manifest_sections.append("")

    (target_root / "MANIFEST.md").write_text("\n".join(manifest_sections), encoding="utf-8")

    total_files = sum(1 for _ in target_root.rglob("*") if _.is_file())
    total_size = sum(f.stat().st_size for f in target_root.rglob("*") if f.is_file())

    print("📦 Organizing and packaging release artifacts...")
    print(f"Total files: {total_files}")
    print(f"Total size: {total_size / (1024 * 1024):.2f} MB")

    # Print organized by category
    for category, files_in_category in {
        cat: [(rel, sz) for rel, sz, c in moved_files if c == cat] for cat in categories
    }.items():
        if files_in_category:
            print(f"\n{category.title()}:")
            for rel_path, size in files_in_category[:10]:
                size_mb = size / (1024 * 1024)
                size_str = f"{size} bytes" if size_mb < 0.01 else f"{size_mb:.2f} MB"
                print(f"  ✅ {rel_path} ({size_str})")
            if len(files_in_category) > 10:
                print(f"  ... and {len(files_in_category) - 10} more")

    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        with Path(output_path).open("a", encoding="utf-8") as handle:
            handle.write("packaging-complete=true\n")


if __name__ == "__main__":
    main()
