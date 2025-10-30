#!/usr/bin/env python3
"""Normalize Docker build platforms and emit results for the workflow.

Inputs via environment variables:
  INPUT_PLATFORMS: comma-separated platform list (preferred)
  INPUT_DOCKER_MATRIX: JSON matrix with platform entries (legacy compatibility)

Outputs:
  platforms, qemu-platforms     -> appended to $GITHUB_OUTPUT
  PLATFORMS, QEMU_PLATFORMS     -> appended to $GITHUB_ENV
"""

from __future__ import annotations

from collections.abc import Iterable
import json
import os
from typing import List

DEFAULT_PLATFORMS = ("linux/amd64", "linux/arm64")


def normalize_platforms(raw_platforms: str, raw_matrix: str) -> List[str]:
    platforms: list[str] = []

    if raw_platforms:
        platforms.extend(
            value.strip() for value in raw_platforms.split(",") if value.strip()
        )
    elif raw_matrix:
        try:
            matrix = json.loads(raw_matrix)
        except json.JSONDecodeError:
            matrix = None

        if isinstance(matrix, dict):
            values = matrix.get("platform") or []
            if isinstance(values, list):
                platforms.extend(
                    str(item).strip() for item in values if str(item).strip()
                )
            includes = matrix.get("include") or []
            if isinstance(includes, list):
                for entry in includes:
                    if isinstance(entry, dict):
                        value = entry.get("platform")
                        if value:
                            platforms.append(str(value).strip())
        elif isinstance(matrix, list):
            for entry in matrix:
                if isinstance(entry, dict):
                    value = entry.get("platform")
                    if value:
                        platforms.append(str(value).strip())

    if not platforms:
        platforms.extend(DEFAULT_PLATFORMS)

    ordered: list[str] = []
    for item in platforms:
        if item and item not in ordered:
            ordered.append(item)

    return ordered


def derive_qemu_arches(platforms: Iterable[str]) -> List[str]:
    arches: list[str] = []
    for platform in platforms:
        arch = platform.split("/", 1)[1] if "/" in platform else platform
        if arch not in arches:
            arches.append(arch)
    if not arches:
        arches.extend(["amd64", "arm64"])
    return arches


def append_lines(path: str | None, lines: Iterable[str]) -> None:
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        for line in lines:
            handle.write(f"{line}\n")


def main() -> None:
    raw_platforms = os.environ.get("INPUT_PLATFORMS", "")
    raw_matrix = os.environ.get("INPUT_DOCKER_MATRIX", "")

    platforms = normalize_platforms(raw_platforms, raw_matrix)
    qemu_arches = derive_qemu_arches(platforms)

    platforms_value = ",".join(platforms)
    qemu_value = ",".join(qemu_arches)

    append_lines(
        os.environ.get("GITHUB_OUTPUT"),
        [
            f"platforms={platforms_value}",
            f"qemu-platforms={qemu_value}",
        ],
    )
    append_lines(
        os.environ.get("GITHUB_ENV"),
        [
            f"PLATFORMS={platforms_value}",
            f"QEMU_PLATFORMS={qemu_value}",
        ],
    )

    print(f"Resolved build platforms: {platforms_value}")
    print(f"QEMU emulation targets: {qemu_value}")


if __name__ == "__main__":
    main()
