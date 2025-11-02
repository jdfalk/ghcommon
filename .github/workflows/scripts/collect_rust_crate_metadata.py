#!/usr/bin/env python3
"""Extract Rust crate metadata and validate required fields."""

from __future__ import annotations

import os
import sys
from collections.abc import Iterable
from pathlib import Path

REQUIRED_FIELDS: Iterable[str] = (
    "name",
    "version",
    "edition",
    "authors",
    "description",
    "license",
    "repository",
)


def load_toml(path: Path) -> dict:
    try:
        try:
            import tomllib  # Python 3.11+
        except ModuleNotFoundError:  # pragma: no cover
            import tomli as tomllib  # type: ignore
    except ModuleNotFoundError:  # pragma: no cover
        print("::error::Python tomllib/tomli module is required", file=sys.stderr)
        raise SystemExit(1)

    try:
        return tomllib.loads(path.read_text())
    except Exception as exc:  # pragma: no cover
        print(f"::error::Failed to parse {path}: {exc}", file=sys.stderr)
        raise SystemExit(1)


def main() -> None:
    cargo_path = Path("Cargo.toml")
    if not cargo_path.exists():
        print("::error::Cargo.toml not found in repository root", file=sys.stderr)
        raise SystemExit(1)

    data = load_toml(cargo_path)
    package = data.get("package")
    if not isinstance(package, dict):
        print("::error::[package] section missing in Cargo.toml", file=sys.stderr)
        raise SystemExit(1)

    missing: list[str] = []
    for field in REQUIRED_FIELDS:
        value = package.get(field)
        if (
            value is None
            or (isinstance(value, str) and not value.strip())
            or (isinstance(value, (list, tuple)) and not value)
        ):
            missing.append(field)
        else:
            print(f"✅ {field}: {value}")

    if missing:
        print(
            "::error::Missing required Cargo.toml fields: " + ", ".join(missing),
            file=sys.stderr,
        )
        raise SystemExit(1)

    crate_name = str(package["name"])
    crate_version = str(package["version"])

    print()
    print(f"📦 Crate: {crate_name}")
    print(f"🏷️ Version: {crate_version}")

    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        with open(output_path, "a", encoding="utf-8") as handle:
            handle.write(f"crate-name={crate_name}\n")
            handle.write(f"crate-version={crate_version}\n")


if __name__ == "__main__":
    main()
