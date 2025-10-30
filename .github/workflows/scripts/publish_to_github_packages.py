#!/usr/bin/env python3
# file: .github/workflows/scripts/publish_to_github_packages.py
# version: 1.0.0
# guid: 56c78875-9e49-4f08-bfab-3a6d6a327f65

"""Publish build artifacts to GitHub Packages as generic packages."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

from workflow_common import (
    append_summary_line,
    format_summary_table,
    get_repository_config,
    log_notice,
    log_warning,
    registry_enabled,
)


def _collect_artifact_files(directory: Path) -> list[Path]:
    """Collect all artifact files stored inside a directory tree."""
    return [path for path in directory.rglob("*") if path.is_file()]


def _ensure_has_artifacts(directory: Path) -> None:
    """Ensure the artifact directory is not empty."""
    files = _collect_artifact_files(directory)
    if not files:
        log_warning(
            f"No artifact files found in {directory}; skipping publish",
        )
        raise SystemExit(0)


def _sanitize_version(tag: str) -> str:
    """Convert git tag into a package-safe version string."""
    return tag.lstrip("v").replace("/", "-")


def _build_package_name(language: str, branch: str, is_stable: bool) -> str:
    """Construct package name using language and branch context."""
    base = f"{language}-artifacts".replace(" ", "-")
    if is_stable and branch.startswith("stable-"):
        suffix = branch.replace("stable-", "").replace("/", "-")
        return f"{base}-{suffix}"
    return base


def _create_tarball(source_dir: Path, package_name: str, version: str) -> Path:
    """Create a tarball containing the artifacts directory."""
    temp_dir = Path(tempfile.mkdtemp(prefix="ghpkg-"))
    tarball_path = temp_dir / f"{package_name}-{version}.tar.gz"
    with tarfile.open(tarball_path, "w:gz") as archive:
        archive.add(source_dir, arcname=package_name)
    return tarball_path


def _run_gh_api(
    repository: str,
    package_name: str,
    version: str,
    tarball: Path,
) -> None:
    """Upload tarball to GitHub Packages using gh api."""
    if shutil.which("gh") is None:
        print("::error::GitHub CLI (gh) not found on PATH")
        raise SystemExit(1)

    url = (
        f"/repos/{repository}/packages/generic/"
        f"{package_name}/{version}/{tarball.name}"
    )
    command = [
        "gh",
        "api",
        "--method",
        "PUT",
        url,
        "--header",
        "Content-Type: application/octet-stream",
        "--input",
        str(tarball),
    ]
    result = subprocess.run(  # pylint: disable=subprocess-run-check
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        print(f"::error::Failed to upload package: {stderr}")
        raise SystemExit(result.returncode)


def publish_github_package(
    *,
    repository: str,
    language: str,
    tag: str,
    branch: str,
    is_stable: bool,
    artifacts_dir: Path,
) -> None:
    """Publish artifacts directory as a GitHub Packages generic package."""
    _ensure_has_artifacts(artifacts_dir)
    version = _sanitize_version(tag)
    package_name = _build_package_name(language, branch, is_stable)
    tarball = _create_tarball(artifacts_dir, package_name, version)

    try:
        _run_gh_api(repository, package_name, version, tarball)
    finally:
        shutil.rmtree(tarball.parent, ignore_errors=True)

    append_summary_line(
        format_summary_table(
            (
                ("Package", f"`{package_name}`"),
                ("Version", f"`{version}`"),
                ("Source", f"`{artifacts_dir}`"),
            )
        )
    )
    log_notice(
        f"Published {package_name} version {version} "
        f"with artifacts from {artifacts_dir}",
    )


def main() -> None:
    """Entry point for GitHub Actions usage."""
    parser = argparse.ArgumentParser(
        description="Publish build artifacts to GitHub Packages",
    )
    parser.add_argument("--language", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--is-stable", action="store_true")
    parser.add_argument("--artifacts-dir", required=True)
    parser.add_argument(
        "--repository",
        default=os.environ.get("GITHUB_REPOSITORY", ""),
    )
    parser.add_argument("--require-github", action="store_true")
    args = parser.parse_args()

    # Prime configuration cache for helper consumers.
    get_repository_config()

    if args.require_github and not registry_enabled("github"):
        log_notice("GitHub Packages registry disabled; skipping publish")
        raise SystemExit(0)

    repository = args.repository.strip()
    if not repository:
        print("::error::Repository name not provided")
        raise SystemExit(1)

    artifacts_dir = Path(args.artifacts_dir)
    if not artifacts_dir.exists():
        print(f"::error::Artifacts directory not found: {artifacts_dir}")
        raise SystemExit(1)

    publish_github_package(
        repository=repository,
        language=args.language,
        tag=args.tag,
        branch=args.branch,
        is_stable=args.is_stable,
        artifacts_dir=artifacts_dir,
    )


if __name__ == "__main__":  # pragma: no cover
    try:
        main()
    except SystemExit:
        raise
    except Exception as error:  # pylint: disable=broad-except
        print(f"::error::Unexpected error during package publish: {error}")
        sys.exit(1)
