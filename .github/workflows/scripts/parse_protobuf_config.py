#!/usr/bin/env python3
"""Parse protobuf configuration and emit workflow outputs."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

DEFAULT_CONFIG: Dict[str, Any] = {
    "languages": {
        "go": {"enabled": False},
        "python": {"enabled": False},
        "rust": {"enabled": False},
    },
    "protobuf": {
        "enabled": False,
        "buf_version": "1.56.0",
        "protoc_version": "28.2",
        "source_path": "proto",
        "output_path": "sdks",
        "generate_docs": False,
    },
}


def bool_str(value: bool) -> str:
    return "true" if value else "false"


def load_config(path: Path) -> Dict[str, Any]:
    if not path.exists() or yaml is None:
        return DEFAULT_CONFIG.copy()

    try:
        data = yaml.safe_load(path.read_text())
    except Exception as exc:  # pragma: no cover
        print(f"::warning::Unable to parse {path}: {exc}")
        return DEFAULT_CONFIG.copy()

    if not isinstance(data, dict):
        return DEFAULT_CONFIG.copy()

    config = DEFAULT_CONFIG.copy()
    config.update(data)
    return config


def emit_output(name: str, value: str) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        with open(output_path, "a", encoding="utf-8") as handle:
            handle.write(f"{name}={value}\n")


def main() -> None:
    config_path = Path(os.environ.get("CONFIG_PATH", ".github/repository-config.yml"))
    config = load_config(config_path)

    languages = config.get("languages", {})
    protobuf = config.get("protobuf", {})

    emit_output("protobuf-enabled", bool_str(bool(protobuf.get("enabled", False))))
    emit_output("go-enabled", bool_str(bool(languages.get("go", {}).get("enabled", False))))
    emit_output("python-enabled", bool_str(bool(languages.get("python", {}).get("enabled", False))))
    emit_output("rust-enabled", bool_str(bool(languages.get("rust", {}).get("enabled", False))))
    emit_output("buf-version", str(protobuf.get("buf_version", "1.56.0")))
    emit_output("protoc-version", str(protobuf.get("protoc_version", "28.2")))
    emit_output("protobuf-config", json.dumps(protobuf, separators=(",", ":")))


if __name__ == "__main__":
    main()
