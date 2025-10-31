#!/usr/bin/env python3
# file: tests/workflow_scripts/test_publish_to_github_packages.py
# version: 1.0.0
# guid: 6e77a1f8-5c76-41a8-9e3c-9f89cb237a9f

"""Tests for publish_to_github_packages workflow helper."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import publish_to_github_packages as pkg
import pytest
import workflow_common


@pytest.fixture(autouse=True)
def reset_config_cache() -> None:
    """Reset shared config cache between tests."""
    workflow_common.reset_repository_config()
    yield
    workflow_common.reset_repository_config()


@pytest.mark.parametrize(
    ("tag", "expected"),
    [
        ("v1.2.3", "1.2.3"),
        ("release/v0.1.0", "release-v0.1.0"),
    ],
)
def test_sanitize_version_formats_tag(tag: str, expected: str) -> None:
    """_sanitize_version removes leading v and slashes."""
    # pylint: disable=protected-access
    assert pkg._sanitize_version(tag) == expected
    # pylint: enable=protected-access


@pytest.mark.parametrize(
    ("language", "branch", "is_stable", "expected"),
    [
        ("go", "main", False, "go-artifacts"),
        (
            "python",
            "stable-1-python-3.13",
            True,
            "python-artifacts-1-python-3.13",
        ),
    ],
)
def test_build_package_name_handles_stable_branch(
    language: str,
    branch: str,
    is_stable: bool,
    expected: str,
) -> None:
    """_build_package_name decorates stable branches."""
    # pylint: disable=protected-access
    actual = pkg._build_package_name(language, branch, is_stable)
    # pylint: enable=protected-access
    assert actual == expected


def test_publish_github_package_creates_tarball(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """publish_github_package bundles artifacts and uploads via gh api."""
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()
    (artifacts_dir / "file.txt").write_text("example", encoding="utf-8")
    summary_path = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_path))

    captured: dict[str, Any] = {}

    def fake_run(
        repository: str,
        package_name: str,
        version: str,
        tarball: Path,
    ) -> None:
        captured["repository"] = repository
        captured["package_name"] = package_name
        captured["version"] = version
        captured["tarball"] = tarball
        assert tarball.exists()
        assert tarball.name.endswith(".tar.gz")

    monkeypatch.setattr(
        pkg,
        "_run_gh_api",
        fake_run,
    )  # pylint: disable=protected-access

    pkg.publish_github_package(
        repository="owner/repo",
        language="rust",
        tag="v1.2.3",
        branch="stable-1-rust-stable",
        is_stable=True,
        artifacts_dir=artifacts_dir,
    )

    assert captured["repository"] == "owner/repo"
    assert captured["package_name"] == "rust-artifacts-1-rust-stable"
    assert captured["version"] == "1.2.3"
    assert summary_path.exists()
    summary_content = summary_path.read_text(encoding="utf-8")
    assert "rust-artifacts-1-rust-stable" in summary_content


def test_main_skips_when_registry_disabled(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """main exits early when GitHub registry disabled."""
    monkeypatch.setenv(
        "REPOSITORY_CONFIG",
        json.dumps({"packages": {"registries": {"github": False}}}),
    )

    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()
    (artifacts_dir / "file.txt").write_text("example", encoding="utf-8")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")

    def fail_publish(**_: Any) -> None:
        raise AssertionError("Should not run")

    monkeypatch.setattr(
        pkg,
        "publish_github_package",
        fail_publish,
    )

    argv = [
        "publish_to_github_packages.py",
        "--language",
        "go",
        "--tag",
        "v0.1.0",
        "--branch",
        "main",
        "--artifacts-dir",
        str(artifacts_dir),
        "--require-github",
    ]
    monkeypatch.setattr(pkg.sys, "argv", argv)

    with pytest.raises(SystemExit) as excinfo:
        pkg.main()

    assert excinfo.value.code == 0
