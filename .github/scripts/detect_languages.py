#!/usr/bin/env python3
# file: .github/scripts/detect_languages.py
# version: 1.0.0
# guid: 6f9d2c3b-1a4e-45c2-b7d8-2e9f4a1c7b56
"""Detect project languages and emit key=value lines for GitHub Actions outputs.

Prints lines suitable for appending directly to $GITHUB_OUTPUT.
"""

from __future__ import annotations

import json
import os


def exists_any(*paths: str) -> bool:
    return any(os.path.exists(p) for p in paths)


has_go = exists_any("go.mod", "main.go")
has_python = (
    exists_any("pyproject.toml", "requirements.txt", "setup.py")
    or any(f.startswith("tests/test_") for f in os.listdir("tests"))
    if os.path.isdir("tests")
    else False
)
has_frontend = exists_any("package.json", "yarn.lock", "pnpm-lock.yaml")
has_docker = exists_any("Dockerfile", "docker-compose.yml", "docker-compose.yaml")
has_rust = exists_any("Cargo.toml")
protobuf_needed = exists_any("buf.gen.yaml", "buf.yaml") or os.path.isdir("proto")

if has_rust:
    primary = "rust"
elif has_go:
    primary = "go"
elif has_python:
    primary = "python"
elif has_frontend:
    primary = "frontend"
else:
    primary = "unknown"

go_matrix = (
    {
        "include": [
            {"os": "ubuntu-latest", "go-version": "1.23", "primary": True},
            {"os": "ubuntu-latest", "go-version": "1.22", "primary": False},
            {"os": "macos-latest", "go-version": "1.23", "primary": False},
            {"os": "windows-latest", "go-version": "1.23", "primary": False},
        ]
    }
    if has_go
    else {"include": []}
)

python_matrix = (
    {
        "include": [
            {"os": "ubuntu-latest", "python-version": "3.12", "primary": True},
            {"os": "ubuntu-latest", "python-version": "3.11", "primary": False},
            {"os": "ubuntu-latest", "python-version": "3.13", "primary": False},
            {"os": "macos-latest", "python-version": "3.12", "primary": False},
            {"os": "windows-latest", "python-version": "3.12", "primary": False},
        ]
    }
    if has_python
    else {"include": []}
)

frontend_matrix = (
    {
        "include": [
            {"os": "ubuntu-latest", "node-version": "20", "primary": True},
            {"os": "ubuntu-latest", "node-version": "18", "primary": False},
            {"os": "ubuntu-latest", "node-version": "22", "primary": False},
            {"os": "macos-latest", "node-version": "20", "primary": False},
            {"os": "windows-latest", "node-version": "20", "primary": False},
        ]
    }
    if has_frontend
    else {"include": []}
)

docker_matrix = (
    {
        "include": [
            {"platform": "linux/amd64", "os": "ubuntu-latest", "primary": True},
            {"platform": "linux/arm64", "os": "ubuntu-latest", "primary": False},
        ]
    }
    if has_docker
    else {"include": []}
)


def emit(key: str, value):
    print(f"{key}={value}")


emit("has-go", str(has_go).lower())
emit("has-python", str(has_python).lower())
emit("has-frontend", str(has_frontend).lower())
emit("has-docker", str(has_docker).lower())
emit("has-rust", str(has_rust).lower())
emit("protobuf-needed", str(protobuf_needed).lower())
emit("primary-language", primary)
emit("project-type", primary)
emit("go-matrix", json.dumps(go_matrix))
emit("python-matrix", json.dumps(python_matrix))
emit("frontend-matrix", json.dumps(frontend_matrix))
emit("docker-matrix", json.dumps(docker_matrix))
