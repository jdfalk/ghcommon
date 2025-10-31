#!/usr/bin/env python3
# file: tests/workflow_scripts/test_maintenance_workflow.py
# version: 1.0.0
# guid: 7c8d9e0f-a1b2-4c3d-8e9f-0a1b2c3d4e5f

"""Tests for maintenance_workflow helper module."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import maintenance_workflow
from datetime import datetime, timedelta


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def test_collect_dependency_updates(tmp_path: Path) -> None:
    """collect_dependency_updates parses pip/npm/cargo/go outputs."""
    pip_data = [
        {"name": "requests", "version": "2.30.0", "latest_version": "2.31.0"},
    ]
    npm_data = {"lodash": {"current": "4.17.20", "latest": "4.17.21"}}
    cargo_data = {
        "packages": [
            {"name": "serde", "version": "1.0.190", "latest_version": "1.0.201"},
        ]
    }
    go_data = """{"Path":"example.com/mod","Version":"1.2.0","Update":{"Path":"example.com/mod","Version":"1.3.0"}}"""

    pip_path = tmp_path / "pip.json"
    npm_path = tmp_path / "npm.json"
    cargo_path = tmp_path / "cargo.json"
    go_path = tmp_path / "go.json"
    write_json(pip_path, pip_data)
    write_json(npm_path, npm_data)
    write_json(cargo_path, cargo_data)
    go_path.write_text(go_data, encoding="utf-8")

    updates = maintenance_workflow.collect_dependency_updates(
        pip_path, npm_path, cargo_path, go_path
    )

    assert len(updates) == 4
    languages = {update.language for update in updates}
    assert {"python", "node", "rust", "go"}.issubset(languages)


def test_summarize_dependencies(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """summarize_dependency_updates writes markdown summary."""
    updates = [
        maintenance_workflow.DependencyUpdate(
            name="pkg",
            current_version="1.0.0",
            latest_version="1.1.0",
            update_type="minor",
            breaking=False,
            security=False,
            language="python",
        )
    ]
    summary_file = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_file))
    maintenance_workflow.write_dependency_summary(updates, tmp_path / "summary_output.md")
    maintenance_workflow.summarize_dependency_updates(updates)

    assert (tmp_path / "summary_output.md").read_text(encoding="utf-8")
    assert "pkg" in summary_file.read_text(encoding="utf-8")


def test_cli_summarize_dependencies(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """CLI summarize-dependencies command writes summary file."""
    pip_path = tmp_path / "pip.json"
    write_json(
        pip_path,
        [{"name": "flask", "version": "2.1.0", "latest_version": "3.0.0"}],
    )
    summary_file = tmp_path / "GITHUB_STEP_SUMMARY.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_file))

    maintenance_workflow.main(
        [
            "summarize-dependencies",
            "--pip",
            str(pip_path),
            "--npm",
            str(tmp_path / "missing.json"),
            "--cargo",
            str(tmp_path / "missing.json"),
            "--go",
            str(tmp_path / "missing.json"),
            "--output",
            str(tmp_path / "summary.md"),
        ]
    )

    assert (tmp_path / "summary.md").read_text(encoding="utf-8")
    assert "flask" in summary_file.read_text(encoding="utf-8")


def test_parse_stale_items() -> None:
    """parse_stale_items returns items older than threshold."""
    now = datetime.utcnow()
    data = [
        {
            "number": 1,
            "title": "Old issue",
            "type": "issue",
            "created_at": (now - timedelta(days=200)).isoformat(),
            "updated_at": (now - timedelta(days=100)).isoformat(),
            "labels": ["bug"],
            "assignees": ["alice"],
        },
        {
            "number": 2,
            "title": "Recent issue",
            "type": "issue",
            "created_at": (now - timedelta(days=10)).isoformat(),
            "updated_at": (now - timedelta(days=5)).isoformat(),
            "labels": [],
            "assignees": [],
        },
    ]
    stale = maintenance_workflow.parse_stale_items(data, days=30)
    assert len(stale) == 1
    assert stale[0].number == 1


def test_summarize_security_issues(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """summarize_security_issues appends advisory information."""
    issues = [
        maintenance_workflow.SecurityIssue(
            severity="high",
            package="openssl",
            vulnerability="CVE-2024-1234",
            description="Test issue",
            fixed_version="1.2.3",
            advisory_url="https://example.com/advisory",
        )
    ]
    summary_file = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_file))
    maintenance_workflow.summarize_security_issues(issues)
    content = summary_file.read_text(encoding="utf-8")
    assert "openssl" in content
    assert "CVE-2024-1234" in content


def test_cli_summarize_security(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """CLI summarize-security handles missing file gracefully."""
    summary_file = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_file))
    security_path = tmp_path / "security.json"
    security_path.write_text(
        json.dumps(
            [
                {
                    "severity": "medium",
                    "package": "libssl",
                    "vulnerability": "GHSA-123",
                    "fixed_version": "1.1.1",
                    "advisory_url": "https://example.com/ghsa",
                }
            ]
        ),
        encoding="utf-8",
    )
    maintenance_workflow.main(["summarize-security", "--input", str(security_path)])
    assert "libssl" in summary_file.read_text(encoding="utf-8")
