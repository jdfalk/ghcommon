#!/usr/bin/env python3
# file: tests/workflow_scripts/test_workflow_common.py
# version: 1.0.0
# guid: 4dcbebd7-74dd-4c5f-9442-7ad2c49ea5a6

"""Unit tests for workflow_common helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import workflow_common


@pytest.fixture(autouse=True)
def reset_config_cache() -> None:
    """Reset cached configuration around every test."""
    workflow_common.reset_repository_config()
    yield
    workflow_common.reset_repository_config()


def test_append_summary_line_writes_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """append_summary_line appends newline terminated text."""
    summary_file = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_file))

    workflow_common.append_summary_line("hello")
    workflow_common.append_summary_line("world")

    assert summary_file.read_text(encoding="utf-8") == "hello\nworld\n"


def test_format_summary_table() -> None:
    """format_summary_table returns a Markdown table."""
    table = workflow_common.format_summary_table(
        (("Name", "`value`"), ("Status", "ok")),
    )
    assert "| Item | Value |" in table
    assert "| Name | `value` |" in table
    assert "| Status | ok |" in table


def test_registry_enabled_uses_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """registry_enabled reflects configuration flags."""
    config = {
        "packages": {
            "registries": {
                "github": True,
                "npm": False,
            }
        }
    }
    monkeypatch.setenv("REPOSITORY_CONFIG", json.dumps(config))

    assert workflow_common.registry_enabled("github") is True
    assert workflow_common.registry_enabled("npm") is False
    assert workflow_common.registry_enabled("pypi") is False


def test_config_path_returns_default_for_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """config_path returns provided default when key missing."""
    monkeypatch.delenv("REPOSITORY_CONFIG", raising=False)
    assert workflow_common.config_path("fallback", "missing") == "fallback"


def test_build_release_summary_includes_components() -> None:
    """build_release_summary generates Markdown summary."""
    context = {
        "primary_language": "go",
        "build_target": "all",
        "release_tag": "v1.2.3",
        "release_strategy": "stable",
        "branch": "main",
        "components": {"Go": "success", "Release": "success"},
        "release_created": True,
        "auto_prerelease": False,
        "auto_draft": False,
    }
    summary = workflow_common.build_release_summary(context)
    assert "# 🚀 Release Build Results" in summary
    assert "| Go | success |" in summary
    assert "🎉 **Release created: v1.2.3**" in summary
