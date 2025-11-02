#!/usr/bin/env python3
"""Detect Python package metadata for release workflow."""

from __future__ import annotations

import configparser
import json
import os
import subprocess
import sys
from pathlib import Path

module_name = ""
module_version = ""
build_system = "unknown"

pyproject = Path("pyproject.toml")
setup_cfg = Path("setup.cfg")
setup_py = Path("setup.py")


def read_pyproject() -> None:
    global module_name, module_version, build_system
    if not pyproject.exists():
        return
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover
        import tomli as tomllib  # type: ignore  # noqa: PGH003
    try:
        data = tomllib.loads(pyproject.read_text("utf-8"))
    except Exception as exc:  # pragma: no cover
        print(f"::warning::Unable to parse pyproject.toml: {exc}")
        return

    project = data.get("project")
    poetry = data.get("tool", {}).get("poetry") if isinstance(data.get("tool"), dict) else None

    if isinstance(project, dict):
        module_name = module_name or str(project.get("name") or "")
        module_version = module_version or str(project.get("version") or "")
        build_system = "pyproject"
        dynamic = project.get("dynamic") or []
        if module_version and "version" in dynamic:
            module_version = ""
    if isinstance(poetry, dict):
        build_system = "poetry"
        module_name = module_name or str(poetry.get("name") or "")
        module_version = module_version or str(poetry.get("version") or "")


def read_setup_cfg() -> None:
    global module_name, module_version, build_system
    if not setup_cfg.exists():
        return
    config = configparser.ConfigParser()
    config.read(setup_cfg)
    if config.has_section("metadata"):
        module_name = module_name or config.get("metadata", "name", fallback="")
        module_version = module_version or config.get("metadata", "version", fallback="")
        build_system = "setuptools"


def read_setup_py() -> None:
    global module_name, module_version, build_system
    if not setup_py.exists():
        return
    build_system = "setuptools"
    try:
        if not module_name:
            module_name = subprocess.check_output(
                [sys.executable, "setup.py", "--name"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
    except Exception:
        pass
    try:
        if not module_version:
            module_version = subprocess.check_output(
                [sys.executable, "setup.py", "--version"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
    except Exception:
        pass


def main() -> None:
    read_pyproject()
    read_setup_cfg()
    read_setup_py()

    has_package = "true" if module_name else "false"

    output = {
        "has-package": has_package,
        "package-name": module_name,
        "package-version": module_version,
        "build-system": build_system,
    }

    print(json.dumps(output))

    output_path = Path(os.environ["GITHUB_OUTPUT"]) if "GITHUB_OUTPUT" in os.environ else None
    if output_path:
        with output_path.open("a", encoding="utf-8") as handle:
            for key, value in output.items():
                handle.write(f"{key}={value}\n")


if __name__ == "__main__":
    main()
