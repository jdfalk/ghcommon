#!/usr/bin/env python3
# file: .github/workflows/scripts/check_protobuf_artifacts.py
# version: 1.0.0
# guid: 5e4d3c2b-1a09-48f7-8e6d-5c4b3a2d1f0e

"""Check generated protobuf artifacts and emit workflow outputs."""

from __future__ import annotations

import os
from pathlib import Path


def write_output(name: str, value: str) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with Path(output_path).open("a", encoding="utf-8") as handle:
        handle.write(f"{name}={value}\n")


def main() -> int:
    output_dir = Path(os.environ.get("PROTOBUF_OUTPUT", "sdks")).resolve()
    go_files = {p.resolve() for p in output_dir.rglob("*.pb.go")}
    go_files.update(p.resolve() for p in output_dir.rglob("*_grpc.pb.go"))

    python_files = {
        p.resolve()
        for pattern in ("*.py", "*.pyi")
        for p in output_dir.rglob(pattern)
        if "__pycache__" not in p.parts
    }

    docs_dir = Path("proto-docs")
    doc_files = {p.resolve() for p in docs_dir.rglob("*.md")} if docs_dir.exists() else set()

    write_output("go-files-generated", str(len(go_files)))
    write_output("python-files-generated", str(len(python_files)))
    write_output("docs-generated", "true" if doc_files else "false")
    write_output("artifacts-available", "true" if go_files or python_files else "false")

    print("=== Checking generated artifacts ===")
    print(f"Generated Go files: {len(go_files)}")
    print(f"Generated Python files: {len(python_files)}")
    print(f"Documentation generated: {'yes' if doc_files else 'no'}")

    if go_files or python_files:
        print("✅ Protobuf artifacts generated successfully")
    else:
        print("❌ No protobuf artifacts were generated")

    print("Sample generated files:")
    for path in sorted(go_files)[:3]:
        print(f"  {path}")
    for path in sorted(python_files)[:3]:
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
