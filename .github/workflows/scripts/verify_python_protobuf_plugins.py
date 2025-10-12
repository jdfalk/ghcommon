#!/usr/bin/env python3
"""Verify that required Python protobuf plugins are available."""

from __future__ import annotations

import importlib
import sys

MODULES = ["grpc_tools.protoc", "mypy_protobuf"]


def main() -> None:
    missing = []
    for module in MODULES:
        try:
            importlib.import_module(module)
            print(f"✅ {module} available")
        except Exception as exc:  # pragma: no cover
            print(f"::error::Failed to import {module}: {exc}")
            missing.append(module)

    if missing:
        print("::error::Missing required Python protobuf plugins: " + ", ".join(missing))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
