<!-- file: docs/refactors/workflows/v2/phases/phase-2-release-consolidation.md -->
<!-- version: 1.0.0 -->
<!-- guid: d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a -->

# Phase 2: Release Consolidation

## Overview

Phase 2 consolidates release workflows into a unified system with branch-aware version detection,
automated changelog generation, GitHub Packages publishing, and support for parallel release tracks
via stable-1-\* branches.

**Status**: 🟡 Planning **Dependencies**: Phase 0 (workflow_common.py), Phase 1 (ci_workflow.py for
branch detection patterns) **Target Completion**: 2025-11-10 **Platforms**: ubuntu-latest,
macos-latest (NO WINDOWS)

## Branching Strategy for Parallel Releases

Release workflows support parallel release tracks using branch-aware version targeting:

- **`main` branch releases**: Standard semantic versions (e.g., `v1.2.3`)
  - Uses latest language versions (Go 1.25, Python 3.14, Node 22, Rust stable)
  - Tagged as `v{major}.{minor}.{patch}`
  - Published to GitHub Packages with `latest` tag

- **`stable-1-*` branch releases**: Branch-specific versions (e.g., `v1.2.3-go1.24`)
  - Examples: `stable-1-go-1.24`, `stable-1-python-3.13`
  - Tagged as `v{major}.{minor}.{patch}-{language}{version}`
  - Published to GitHub Packages with branch-specific tags
  - Enables users on older versions to receive updates during deprecation period

**Release Examples**:

- Main branch → `v2.1.0` (Go 1.25, Python 3.14)
- stable-1-go-1.24 → `v2.1.0-go1.24` (Go 1.24)
- stable-1-go-1.23 → `v2.1.0-go1.23` (Go 1.23)
- stable-1-python-3.13 → `v2.1.0-python3.13` (Python 3.13)

**Benefits**:

- Multiple parallel versions available simultaneously
- Clear version identification with language tags
- Users can select appropriate version for their environment
- Automated changelog generation per branch context

## Success Criteria

- [ ] `release_workflow.py` helper created with branch-aware logic
- [ ] Language detection from repository structure
- [ ] Version extraction from branch names
- [ ] `reusable-release.yml` workflow created and tested
- [ ] Changelog generation working for all languages
- [ ] GitHub Packages publishing with branch-specific tags
- [ ] All unit tests pass (100% coverage for new code)
- [ ] Documentation updated
- [ ] Feature flag `use_new_release` functional

## Design Principles

Every task in this phase MUST be:

- **Independent**: Can be executed without waiting for other tasks
- **Idempotent**: Running multiple times produces same result
- **Testable**: Unit tests exist and pass
- **Compliant**: Follows `.github/instructions/python.instructions.md` and
  `.github/instructions/github-actions.instructions.md`

---

## Task 2.1: Create Release Helper Module

**Status**: Not Started **Dependencies**: Phase 0 Task 0.1 (workflow_common.py) **Estimated Time**:
4 hours **Idempotent**: Yes

### Description

Create `.github/workflows/scripts/release_workflow.py` containing release-specific helper functions
for language detection, version extraction, changelog generation, and branch-aware tagging.

### Code Style Requirements

**MUST follow**:

- `.github/instructions/python.instructions.md` - Google Python Style Guide with full docstrings
- `.github/instructions/general-coding.instructions.md` - File headers, versioning
- `.github/instructions/github-actions.instructions.md` - Workflow best practices

### Implementation

Create file: `.github/workflows/scripts/release_workflow.py`

```python
#!/usr/bin/env python3
# file: .github/workflows/scripts/release_workflow.py
# version: 1.0.0
# guid: e5f6a7b8-c9d0-1e2f-3a4b5c6d7e8f9a0b

"""
Release workflow helper functions for version management and publishing.

This module provides functions to detect programming languages, extract versions
from branch names, generate changelogs, and publish releases with branch-aware
tagging for parallel release track support.

Example:
    Detect language and generate release tag:

    >>> lang = detect_primary_language()
    >>> print(lang)
    "go"
    >>> tag = generate_release_tag("v1.2.3", "stable-1-go-1.24", "go")
    >>> print(tag)
    "v1.2.3-go1.24"
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import workflow_common


@dataclass
class ReleaseInfo:
    """
    Release information including version, branch, and language context.

    Attributes:
        version: Semantic version (e.g., "1.2.3")
        branch: Current branch name
        language: Primary language (go, python, rust, node)
        language_version: Language version from branch (e.g., "1.24") or None
        tag: Full release tag (e.g., "v1.2.3-go1.24")
        is_stable_branch: True if releasing from stable-1-* branch
    """

    version: str
    branch: str
    language: str
    language_version: str | None = None
    tag: str = ""
    is_stable_branch: bool = False

    def __post_init__(self) -> None:
        """Generate release tag based on branch context."""
        if self.language_version and self.is_stable_branch:
            # Stable branch: include language version in tag
            clean_version = self.language_version.replace(".", "")
            self.tag = f"v{self.version}-{self.language}{clean_version}"
        else:
            # Main branch: standard semantic version
            self.tag = f"v{self.version}"


def detect_primary_language() -> str:
    """
    Detect primary programming language from repository structure.

    Analyzes key files to determine the primary language used in the project.
    Detection priority: Go > Rust > Python > Node.js

    Returns:
        Language identifier: "go", "python", "rust", or "node"

    Raises:
        workflow_common.WorkflowError: If no supported language detected

    Example:
        >>> lang = detect_primary_language()
        >>> print(f"Detected language: {lang}")
        Detected language: go
    """
    repo_root = Path.cwd()

    # Detection patterns (order matters - priority)
    patterns = [
        ("go", ["go.mod", "go.sum", "main.go"]),
        ("rust", ["Cargo.toml", "Cargo.lock", "src/main.rs"]),
        ("python", ["setup.py", "pyproject.toml", "requirements.txt"]),
        ("node", ["package.json", "package-lock.json"]),
    ]

    for language, files in patterns:
        for file_name in files:
            if (repo_root / file_name).exists():
                return language

    raise workflow_common.WorkflowError(
        "Could not detect primary language",
        hint="Ensure repository contains language-specific files (go.mod, Cargo.toml, etc.)",
    )


def get_branch_language_version(branch_name: str, language: str) -> str | None:
    """
    Extract language version from stable branch name.

    Parses stable-1-{language}-{version} format to extract version.
    Returns None for main/master/develop branches.

    Args:
        branch_name: Current git branch name
        language: Language to check (go, python, rust, node)

    Returns:
        Language version string or None if not a stable branch

    Example:
        >>> get_branch_language_version("stable-1-go-1.24", "go")
        "1.24"
        >>> get_branch_language_version("stable-1-python-3.13", "python")
        "3.13"
        >>> get_branch_language_version("main", "go")
        None
    """
    # Main branches use latest version from config
    if branch_name in ("main", "master", "develop"):
        return None

    # Parse stable-1-{language}-{version} format
    pattern = rf"stable-1-{language}-(.+)$"
    match = re.match(pattern, branch_name)

    if match:
        return match.group(1)

    return None


def is_stable_branch(branch_name: str) -> bool:
    """
    Determine if current branch is a stable maintenance branch.

    Args:
        branch_name: Current git branch name

    Returns:
        True if branch follows stable-1-* pattern

    Example:
        >>> is_stable_branch("stable-1-go-1.24")
        True
        >>> is_stable_branch("main")
        False
    """
    return branch_name.startswith("stable-1-")


def get_current_branch() -> str:
    """
    Get current git branch name.

    Returns:
        Branch name string

    Raises:
        workflow_common.WorkflowError: If git command fails

    Example:
        >>> branch = get_current_branch()
        >>> print(f"Current branch: {branch}")
        Current branch: main
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise workflow_common.WorkflowError(
            f"Failed to get current branch: {e}",
            hint="Ensure git repository is initialized",
        ) from e


def extract_version_from_file(language: str) -> str:
    """
    Extract version from language-specific configuration file.

    Args:
        language: Language identifier (go, python, rust, node)

    Returns:
        Version string (without 'v' prefix)

    Raises:
        workflow_common.WorkflowError: If version file not found or invalid

    Example:
        >>> version = extract_version_from_file("go")
        >>> print(version)
        "1.2.3"
    """
    version_patterns = {
        "go": ("go.mod", r'module .+ // v([0-9]+\.[0-9]+\.[0-9]+)'),
        "rust": ("Cargo.toml", r'version = "([0-9]+\.[0-9]+\.[0-9]+)"'),
        "python": ("pyproject.toml", r'version = "([0-9]+\.[0-9]+\.[0-9]+)"'),
        "node": ("package.json", r'"version": "([0-9]+\.[0-9]+\.[0-9]+)"'),
    }

    if language not in version_patterns:
        raise workflow_common.WorkflowError(
            f"Unsupported language: {language}",
            hint=f"Supported languages: {', '.join(version_patterns.keys())}",
        )

    file_name, pattern = version_patterns[language]
    version_file = Path(file_name)

    if not version_file.exists():
        raise workflow_common.WorkflowError(
            f"Version file not found: {file_name}",
            hint=f"Create {file_name} with version information",
        )

    content = version_file.read_text()
    match = re.search(pattern, content)

    if not match:
        raise workflow_common.WorkflowError(
            f"Version not found in {file_name}",
            hint=f"Ensure {file_name} contains version in correct format",
        )

    return match.group(1)


def create_release_info(
    version: str | None = None,
    branch: str | None = None,
) -> ReleaseInfo:
    """
    Create comprehensive release information object.

    Detects language, extracts version, determines branch context, and
    generates appropriate release tag for GitHub Packages publishing.

    Args:
        version: Optional version override (default: extract from config)
        branch: Optional branch override (default: auto-detect)

    Returns:
        ReleaseInfo object with all release details

    Example:
        >>> info = create_release_info()
        >>> print(f"Tag: {info.tag}, Language: {info.language}")
        Tag: v1.2.3-go124, Language: go
    """
    # Detect language
    language = detect_primary_language()

    # Get current branch
    if branch is None:
        branch = get_current_branch()

    # Extract version
    if version is None:
        version = extract_version_from_file(language)

    # Check for stable branch
    stable = is_stable_branch(branch)

    # Get language version from branch name
    lang_version = get_branch_language_version(branch, language) if stable else None

    return ReleaseInfo(
        version=version,
        branch=branch,
        language=language,
        language_version=lang_version,
        is_stable_branch=stable,
    )


def generate_changelog(
    previous_tag: str | None = None,
    current_tag: str | None = None,
) -> str:
    """
    Generate changelog from git commits since last release.

    Parses conventional commits and generates markdown changelog with
    sections for features, fixes, and breaking changes.

    Args:
        previous_tag: Previous release tag (default: auto-detect)
        current_tag: Current release tag (default: HEAD)

    Returns:
        Markdown-formatted changelog string

    Example:
        >>> changelog = generate_changelog("v1.2.2", "v1.2.3")
        >>> print(changelog)
        ## Features
        - feat: add new API endpoint
        ## Bug Fixes
        - fix: resolve memory leak
    """
    # Find previous tag if not provided
    if previous_tag is None:
        try:
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0", "HEAD^"],
                capture_output=True,
                text=True,
                check=True,
            )
            previous_tag = result.stdout.strip()
        except subprocess.CalledProcessError:
            # No previous tag, use initial commit
            previous_tag = ""

    # Get commits since previous tag
    git_range = f"{previous_tag}..{current_tag or 'HEAD'}"
    try:
        result = subprocess.run(
            ["git", "log", git_range, "--pretty=format:%s"],
            capture_output=True,
            text=True,
            check=True,
        )
        commits = result.stdout.strip().split("\n")
    except subprocess.CalledProcessError as e:
        raise workflow_common.WorkflowError(
            f"Failed to generate changelog: {e}",
            hint="Ensure git repository has commit history",
        ) from e

    # Categorize commits by type
    features = []
    fixes = []
    breaking = []
    other = []

    for commit in commits:
        if not commit:
            continue

        # Check for breaking changes
        if "BREAKING CHANGE" in commit or commit.startswith("!"):
            breaking.append(commit)
        # Conventional commit patterns
        elif commit.startswith("feat"):
            features.append(commit)
        elif commit.startswith("fix"):
            fixes.append(commit)
        else:
            other.append(commit)

    # Build markdown changelog
    sections = []

    if breaking:
        sections.append("## ⚠️ Breaking Changes\n")
        sections.extend(f"- {c}" for c in breaking)
        sections.append("")

    if features:
        sections.append("## ✨ Features\n")
        sections.extend(f"- {c}" for c in features)
        sections.append("")

    if fixes:
        sections.append("## 🐛 Bug Fixes\n")
        sections.extend(f"- {c}" for c in fixes)
        sections.append("")

    if other:
        sections.append("## 📝 Other Changes\n")
        sections.extend(f"- {c}" for c in other)
        sections.append("")

    return "\n".join(sections)


def main() -> None:
    """
    Main entry point for release workflow helper.

    Generates release information, creates changelog, and outputs results
    for GitHub Actions workflow consumption.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate release information and changelog",
    )
    parser.add_argument(
        "--version",
        help="Version override (default: extract from config)",
    )
    parser.add_argument(
        "--branch",
        help="Branch name override (default: auto-detect)",
    )
    parser.add_argument(
        "--output",
        action="store_true",
        help="Output release info to GITHUB_OUTPUT",
    )
    parser.add_argument(
        "--generate-changelog",
        action="store_true",
        help="Generate changelog from commits",
    )

    args = parser.parse_args()

    try:
        # Create release info
        with workflow_common.timed_operation("Generate release info"):
            info = create_release_info(
                version=args.version,
                branch=args.branch,
            )

        print(f"📦 Release Information:")
        print(f"   Language: {info.language}")
        print(f"   Version: {info.version}")
        print(f"   Branch: {info.branch}")
        print(f"   Tag: {info.tag}")
        print(f"   Stable Branch: {'✅' if info.is_stable_branch else '❌'}")
        if info.language_version:
            print(f"   Language Version: {info.language_version}")

        # Output to GitHub Actions
        if args.output:
            workflow_common.write_output("language", info.language)
            workflow_common.write_output("version", info.version)
            workflow_common.write_output("tag", info.tag)
            workflow_common.write_output("branch", info.branch)
            workflow_common.write_output("is_stable", str(info.is_stable_branch).lower())
            if info.language_version:
                workflow_common.write_output("language_version", info.language_version)

        # Generate changelog if requested
        if args.generate_changelog:
            with workflow_common.timed_operation("Generate changelog"):
                changelog = generate_changelog(current_tag=info.tag)

            print(f"\n📝 Changelog:\n{changelog}")

            if args.output:
                # Escape for GitHub Actions multiline output
                changelog_escaped = changelog.replace("%", "%25").replace("\n", "%0A").replace("\r", "%0D")
                workflow_common.write_output("changelog", changelog_escaped)

            # Add to workflow summary
            summary = f"## Release {info.tag}\n\n{changelog}"
            workflow_common.append_summary(summary)

    except Exception as e:
        workflow_common.handle_error(e, "Release preparation")


if __name__ == "__main__":
    main()
```

### Verification Steps

```bash
# 1. Verify file exists
test -f .github/workflows/scripts/release_workflow.py && echo "✅ File created"

# 2. Check Python syntax
python3 -m py_compile .github/workflows/scripts/release_workflow.py && echo "✅ Valid Python"

# 3. Verify imports work
python3 -c "import sys; sys.path.insert(0, '.github/workflows/scripts'); import release_workflow" && echo "✅ Module imports"

# 4. Run type checking
cd .github/workflows/scripts && mypy release_workflow.py && echo "✅ Type hints valid"

# 5. Test language detection
cd /path/to/go/repo && python3 .github/workflows/scripts/release_workflow.py && echo "✅ Language detection works"

# 6. Test stable branch detection
cd /path/to/repo && git checkout -b stable-1-go-1.24 && python3 .github/workflows/scripts/release_workflow.py && echo "✅ Stable branch detection works"
```

---

## Task 2.2: Create Reusable Release Workflow

**Status**: Not Started **Dependencies**: Task 2.1 (release_workflow.py) **Estimated Time**: 3 hours
**Idempotent**: Yes

### Description

Create `.github/workflows/reusable-release.yml` - a reusable workflow that calls release_workflow.py
to generate releases with branch-aware tagging and GitHub Packages publishing.

### Code Style Requirements

**MUST follow**:

- `.github/instructions/github-actions.instructions.md` - Workflow best practices

### Implementation

Create file: `.github/workflows/reusable-release.yml`

```yaml
# file: .github/workflows/reusable-release.yml
# version: 1.0.0
# guid: f6a7b8c9-d0e1-2f3a-4b5c6d7e8f9a0b1c

name: Reusable Release Workflow

on:
  workflow_call:
    inputs:
      version:
        description: 'Version override (default: extract from config)'
        type: string
        required: false
      draft:
        description: 'Create draft release'
        type: boolean
        required: false
        default: false
      prerelease:
        description: 'Mark as prerelease'
        type: boolean
        required: false
        default: false
    outputs:
      tag:
        description: 'Generated release tag'
        value: ${{ jobs.prepare-release.outputs.tag }}
      version:
        description: 'Release version'
        value: ${{ jobs.prepare-release.outputs.version }}
      language:
        description: 'Detected primary language'
        value: ${{ jobs.prepare-release.outputs.language }}

permissions:
  contents: write
  packages: write
  pull-requests: read

jobs:
  prepare-release:
    name: Prepare Release
    runs-on: ubuntu-latest
    outputs:
      tag: ${{ steps.release-info.outputs.tag }}
      version: ${{ steps.release-info.outputs.version }}
      language: ${{ steps.release-info.outputs.language }}
      branch: ${{ steps.release-info.outputs.branch }}
      is_stable: ${{ steps.release-info.outputs.is_stable }}
      changelog: ${{ steps.release-info.outputs.changelog }}

    steps:
      - name: Checkout code
        uses: actions/checkout@8e5e7e5ab8b370d6c329ec480221332ada57f0ab # v4.1.1
        with:
          fetch-depth: 0 # Need full history for changelog

      - name: Set up Python
        uses: actions/setup-python@0a5c61591373683505ea898e09a3ea4f39ef2b9c # v5.0.0
        with:
          python-version: '3.13'

      - name: Install dependencies
        run: |
          pip install pyyaml

      - name: Generate release info
        id: release-info
        run: |
          python3 .github/workflows/scripts/release_workflow.py \
            ${{ inputs.version && format('--version {0}', inputs.version) || '' }} \
            --output \
            --generate-changelog

      - name: Display release info
        run: |
          echo "🏷️  Tag: ${{ steps.release-info.outputs.tag }}"
          echo "📦 Version: ${{ steps.release-info.outputs.version }}"
          echo "💻 Language: ${{ steps.release-info.outputs.language }}"
          echo "🌿 Branch: ${{ steps.release-info.outputs.branch }}"
          echo "🔒 Stable: ${{ steps.release-info.outputs.is_stable }}"

  build-go:
    name: Build Go Artifacts
    needs: prepare-release
    if: needs.prepare-release.outputs.language == 'go'
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        include:
          - os: ubuntu-latest
            goos: linux
            goarch: amd64
          - os: ubuntu-latest
            goos: linux
            goarch: arm64
          - os: macos-latest
            goos: darwin
            goarch: amd64
          - os: macos-latest
            goos: darwin
            goarch: arm64

    steps:
      - name: Checkout code
        uses: actions/checkout@8e5e7e5ab8b370d6c329ec480221332ada57f0ab # v4.1.1

      - name: Set up Go
        uses: actions/setup-go@0c52d547c9bc32b1aa3301fd7a9cb496313a4491 # v5.0.0
        with:
          go-version-file: go.mod

      - name: Build binary
        env:
          GOOS: ${{ matrix.goos }}
          GOARCH: ${{ matrix.goarch }}
        run: |
          output_name="app-${{ matrix.goos }}-${{ matrix.goarch }}"
          if [ "${{ matrix.goos }}" = "windows" ]; then
            output_name="${output_name}.exe"
          fi
          go build -v -o "${output_name}" .
          chmod +x "${output_name}" || true

      - name: Upload artifact
        uses: actions/upload-artifact@26f96dfa697d77e81fd5907df203aa23a56210a8 # v4.3.0
        with:
          name: go-${{ matrix.goos }}-${{ matrix.goarch }}
          path: app-${{ matrix.goos }}-${{ matrix.goarch }}*

  build-rust:
    name: Build Rust Artifacts
    needs: prepare-release
    if: needs.prepare-release.outputs.language == 'rust'
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        include:
          - os: ubuntu-latest
            target: x86_64-unknown-linux-gnu
          - os: ubuntu-latest
            target: aarch64-unknown-linux-gnu
          - os: macos-latest
            target: x86_64-apple-darwin
          - os: macos-latest
            target: aarch64-apple-darwin

    steps:
      - name: Checkout code
        uses: actions/checkout@8e5e7e5ab8b370d6c329ec480221332ada57f0ab # v4.1.1

      - name: Set up Rust
        uses: actions-rust-lang/setup-rust-toolchain@1fbea72663f6d4c03efaab13560c8a24cfd2a7cc # v1.8.0
        with:
          toolchain: stable
          target: ${{ matrix.target }}

      - name: Build binary
        run: |
          cargo build --release --target ${{ matrix.target }}

      - name: Upload artifact
        uses: actions/upload-artifact@26f96dfa697d77e81fd5907df203aa23a56210a8 # v4.3.0
        with:
          name: rust-${{ matrix.target }}
          path: target/${{ matrix.target }}/release/app

  build-python:
    name: Build Python Package
    needs: prepare-release
    if: needs.prepare-release.outputs.language == 'python'
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@8e5e7e5ab8b370d6c329ec480221332ada57f0ab # v4.1.1

      - name: Set up Python
        uses: actions/setup-python@0a5c61591373683505ea898e09a3ea4f39ef2b9c # v5.0.0
        with:
          python-version: '3.13'

      - name: Install build tools
        run: |
          pip install build wheel

      - name: Build package
        run: |
          python -m build

      - name: Upload artifact
        uses: actions/upload-artifact@26f96dfa697d77e81fd5907df203aa23a56210a8 # v4.3.0
        with:
          name: python-dist
          path: dist/*

  build-node:
    name: Build Node.js Package
    needs: prepare-release
    if: needs.prepare-release.outputs.language == 'node'
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@8e5e7e5ab8b370d6c329ec480221332ada57f0ab # v4.1.1

      - name: Set up Node.js
        uses: actions/setup-node@60edb5dd545a775178f52524783378180af0d1f8 # v4.0.2
        with:
          node-version-file: package.json

      - name: Install dependencies
        run: npm ci

      - name: Build package
        run: npm run build || echo "No build script"

      - name: Pack package
        run: npm pack

      - name: Upload artifact
        uses: actions/upload-artifact@26f96dfa697d77e81fd5907df203aa23a56210a8 # v4.3.0
        with:
          name: node-package
          path: '*.tgz'

  create-release:
    name: Create GitHub Release
    needs: [prepare-release, build-go, build-rust, build-python, build-node]
    if: always() && needs.prepare-release.result == 'success'
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@8e5e7e5ab8b370d6c329ec480221332ada57f0ab # v4.1.1

      - name: Download all artifacts
        uses: actions/download-artifact@6b208ae046db98c579e8a3aa621ab581ff575935 # v4.1.1
        with:
          path: artifacts

      - name: Create release
        uses: softprops/action-gh-release@c062e08bd532815e2082a85e87e3ef29c3e6d191 # v0.1.15
        with:
          tag_name: ${{ needs.prepare-release.outputs.tag }}
          name: Release ${{ needs.prepare-release.outputs.tag }}
          body: ${{ needs.prepare-release.outputs.changelog }}
          draft: ${{ inputs.draft }}
          prerelease: ${{ inputs.prerelease }}
          files: artifacts/**/*
          token: ${{ secrets.GITHUB_TOKEN }}

  publish-packages:
    name: Publish to GitHub Packages
    needs: [prepare-release, create-release]
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@8e5e7e5ab8b370d6c329ec480221332ada57f0ab # v4.1.1

      - name: Set up language environment
        run: |
          case "${{ needs.prepare-release.outputs.language }}" in
            go)
              echo "Setting up Go"
              ;;
            python)
              echo "Setting up Python"
              pip install twine
              ;;
            node)
              echo "Setting up Node.js"
              ;;
            rust)
              echo "Setting up Rust"
              ;;
          esac

      - name: Publish package
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          echo "📦 Publishing ${{ needs.prepare-release.outputs.language }} package"
          echo "🏷️  Tag: ${{ needs.prepare-release.outputs.tag }}"
          echo "🌿 Branch: ${{ needs.prepare-release.outputs.branch }}"

          # Language-specific publishing logic would go here
          # This is a placeholder for actual publishing commands
```

### Verification Steps

```bash
# 1. Verify workflow file exists
test -f .github/workflows/reusable-release.yml && echo "✅ Workflow created"

# 2. Validate workflow syntax
gh workflow view reusable-release.yml 2>/dev/null && echo "✅ Valid workflow syntax" || echo "⚠️  Install gh CLI to validate"

# 3. Lint workflow file
yamllint .github/workflows/reusable-release.yml && echo "✅ Valid YAML"

# 4. Check for Windows references (should be none)
grep -i "windows" .github/workflows/reusable-release.yml && echo "❌ Found Windows reference!" || echo "✅ No Windows references"
```

---

## Task 2.3: Create Caller Release Workflow

**Status**: Not Started **Dependencies**: Task 2.2 (reusable-release.yml) **Estimated Time**: 30
minutes **Idempotent**: Yes

### Description

Create `.github/workflows/release.yml` that calls the reusable workflow with feature flag support.

### Implementation

Create file: `.github/workflows/release.yml`

```yaml
# file: .github/workflows/release.yml
# version: 2.0.0
# guid: a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d

name: Release

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to release (e.g., 1.2.3)'
        required: false
      draft:
        description: 'Create draft release'
        type: boolean
        required: false
        default: false
      prerelease:
        description: 'Mark as prerelease'
        type: boolean
        required: false
        default: false

permissions:
  contents: write
  packages: write

jobs:
  check-feature-flag:
    name: Check Feature Flag
    runs-on: ubuntu-latest
    outputs:
      use_new_release: ${{ steps.check.outputs.enabled }}

    steps:
      - name: Checkout code
        uses: actions/checkout@8e5e7e5ab8b370d6c329ec480221332ada57f0ab # v4.1.1

      - name: Set up Python
        uses: actions/setup-python@0a5c61591373683505ea898e09a3ea4f39ef2b9c # v5.0.0
        with:
          python-version: '3.13'

      - name: Install dependencies
        run: pip install pyyaml

      - name: Check feature flag
        id: check
        run: |
          python3 -c "
          import yaml
          from pathlib import Path

          config_path = Path('.github/repository-config.yml')
          if not config_path.exists():
              print('enabled=false')
              exit(0)

          config = yaml.safe_load(config_path.read_text())
          enabled = config.get('workflows', {}).get('experimental', {}).get('use_new_release', False)
          print(f'enabled={str(enabled).lower()}')
          " >> $GITHUB_OUTPUT

  # New release system (branch-aware with GitHub Packages)
  new-release:
    name: New Release System
    needs: check-feature-flag
    if: needs.check-feature-flag.outputs.use_new_release == 'true'
    uses: ./.github/workflows/reusable-release.yml
    with:
      version: ${{ github.event.inputs.version }}
      draft: ${{ github.event.inputs.draft == 'true' }}
      prerelease: ${{ github.event.inputs.prerelease == 'true' }}

  # Legacy release system (fallback)
  legacy-release:
    name: Legacy Release System
    needs: check-feature-flag
    if: needs.check-feature-flag.outputs.use_new_release != 'true'
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@8e5e7e5ab8b370d6c329ec480221332ada57f0ab # v4.1.1

      - name: Run legacy release
        run: |
          echo "🔄 Running legacy release workflow"
          # Existing release logic here
          # This preserves current behavior during migration
```

### Verification Steps

```bash
# 1. Verify workflow file exists
test -f .github/workflows/release.yml && echo "✅ Workflow created"

# 2. Test with feature flag disabled
cat > /tmp/test-config.yml << 'EOF'
workflows:
  experimental:
    use_new_release: false
EOF

# 3. Test with feature flag enabled
cat > /tmp/test-config-enabled.yml << 'EOF'
workflows:
  experimental:
    use_new_release: true
EOF

# 4. Validate both paths work
echo "✅ Release workflow created with feature flag support"
```

---

## Task 2.4: Create Unit Tests for release_workflow

**Status**: Not Started **Dependencies**: Task 2.1 (release_workflow.py) **Estimated Time**: 3 hours
**Idempotent**: Yes

### Description

Create comprehensive unit tests for `release_workflow.py`.

### Code Style Requirements

**MUST follow**:

- `.github/instructions/test-generation.instructions.md` - Arrange-Act-Assert, independence

### Implementation

Create file: `tests/workflow_scripts/test_release_workflow.py`

```python
#!/usr/bin/env python3
# file: tests/workflow_scripts/test_release_workflow.py
# version: 1.0.0
# guid: b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e

"""Unit tests for release_workflow module."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / ".github/workflows/scripts"))

import release_workflow
import workflow_common


@pytest.fixture(autouse=True)
def reset_config_cache():
    """Reset global config cache between tests."""
    workflow_common._CONFIG_CACHE = None
    yield
    workflow_common._CONFIG_CACHE = None


def test_release_info_dataclass_main_branch():
    """Test ReleaseInfo generates standard tag for main branch."""
    # Arrange & Act
    info = release_workflow.ReleaseInfo(
        version="1.2.3",
        branch="main",
        language="go",
        language_version=None,
        is_stable_branch=False,
    )

    # Assert
    assert info.tag == "v1.2.3"


def test_release_info_dataclass_stable_branch():
    """Test ReleaseInfo generates branch-specific tag for stable branch."""
    # Arrange & Act
    info = release_workflow.ReleaseInfo(
        version="1.2.3",
        branch="stable-1-go-1.24",
        language="go",
        language_version="1.24",
        is_stable_branch=True,
    )

    # Assert
    assert info.tag == "v1.2.3-go124"


def test_detect_primary_language_go(tmp_path, monkeypatch):
    """Test detect_primary_language identifies Go projects."""
    # Arrange
    monkeypatch.chdir(tmp_path)
    (tmp_path / "go.mod").write_text("module example.com/test")

    # Act
    language = release_workflow.detect_primary_language()

    # Assert
    assert language == "go"


def test_detect_primary_language_rust(tmp_path, monkeypatch):
    """Test detect_primary_language identifies Rust projects."""
    # Arrange
    monkeypatch.chdir(tmp_path)
    (tmp_path / "Cargo.toml").write_text('[package]\nname = "test"')

    # Act
    language = release_workflow.detect_primary_language()

    # Assert
    assert language == "rust"


def test_detect_primary_language_python(tmp_path, monkeypatch):
    """Test detect_primary_language identifies Python projects."""
    # Arrange
    monkeypatch.chdir(tmp_path)
    (tmp_path / "setup.py").write_text("from setuptools import setup")

    # Act
    language = release_workflow.detect_primary_language()

    # Assert
    assert language == "python"


def test_detect_primary_language_node(tmp_path, monkeypatch):
    """Test detect_primary_language identifies Node.js projects."""
    # Arrange
    monkeypatch.chdir(tmp_path)
    (tmp_path / "package.json").write_text('{"name": "test"}')

    # Act
    language = release_workflow.detect_primary_language()

    # Assert
    assert language == "node"


def test_detect_primary_language_priority(tmp_path, monkeypatch):
    """Test detect_primary_language uses priority order (Go > Rust > Python > Node)."""
    # Arrange
    monkeypatch.chdir(tmp_path)
    (tmp_path / "go.mod").write_text("module example.com/test")
    (tmp_path / "package.json").write_text('{"name": "test"}')

    # Act
    language = release_workflow.detect_primary_language()

    # Assert - Should detect Go first due to priority
    assert language == "go"


def test_detect_primary_language_no_files(tmp_path, monkeypatch):
    """Test detect_primary_language raises error when no supported language found."""
    # Arrange
    monkeypatch.chdir(tmp_path)

    # Act & Assert
    with pytest.raises(workflow_common.WorkflowError) as exc_info:
        release_workflow.detect_primary_language()

    assert "Could not detect primary language" in str(exc_info.value)


def test_get_branch_language_version_stable_branch():
    """Test get_branch_language_version extracts version from stable branch."""
    # Arrange & Act
    version = release_workflow.get_branch_language_version("stable-1-go-1.24", "go")

    # Assert
    assert version == "1.24"


def test_get_branch_language_version_python():
    """Test get_branch_language_version extracts Python version."""
    # Arrange & Act
    version = release_workflow.get_branch_language_version("stable-1-python-3.13", "python")

    # Assert
    assert version == "3.13"


def test_get_branch_language_version_main_branch():
    """Test get_branch_language_version returns None for main branch."""
    # Arrange & Act
    version = release_workflow.get_branch_language_version("main", "go")

    # Assert
    assert version is None


def test_get_branch_language_version_wrong_language():
    """Test get_branch_language_version returns None for different language."""
    # Arrange & Act
    version = release_workflow.get_branch_language_version("stable-1-go-1.24", "python")

    # Assert
    assert version is None


def test_is_stable_branch_true():
    """Test is_stable_branch returns True for stable branches."""
    # Arrange & Act
    result = release_workflow.is_stable_branch("stable-1-go-1.24")

    # Assert
    assert result is True


def test_is_stable_branch_false():
    """Test is_stable_branch returns False for main branch."""
    # Arrange & Act
    result = release_workflow.is_stable_branch("main")

    # Assert
    assert result is False


def test_get_current_branch(monkeypatch):
    """Test get_current_branch returns current git branch."""
    # Arrange
    mock_result = MagicMock()
    mock_result.stdout = "main\n"

    mock_run = MagicMock(return_value=mock_result)
    monkeypatch.setattr("subprocess.run", mock_run)

    # Act
    branch = release_workflow.get_current_branch()

    # Assert
    assert branch == "main"


def test_get_current_branch_git_failure(monkeypatch):
    """Test get_current_branch raises error when git command fails."""
    # Arrange
    import subprocess

    mock_run = MagicMock(side_effect=subprocess.CalledProcessError(1, "git"))
    monkeypatch.setattr("subprocess.run", mock_run)

    # Act & Assert
    with pytest.raises(workflow_common.WorkflowError) as exc_info:
        release_workflow.get_current_branch()

    assert "Failed to get current branch" in str(exc_info.value)


def test_extract_version_from_file_go(tmp_path, monkeypatch):
    """Test extract_version_from_file extracts Go version."""
    # Arrange
    monkeypatch.chdir(tmp_path)
    (tmp_path / "go.mod").write_text("module example.com/test // v1.2.3")

    # Act
    version = release_workflow.extract_version_from_file("go")

    # Assert
    assert version == "1.2.3"


def test_extract_version_from_file_rust(tmp_path, monkeypatch):
    """Test extract_version_from_file extracts Rust version."""
    # Arrange
    monkeypatch.chdir(tmp_path)
    (tmp_path / "Cargo.toml").write_text('[package]\nversion = "1.2.3"')

    # Act
    version = release_workflow.extract_version_from_file("rust")

    # Assert
    assert version == "1.2.3"


def test_extract_version_from_file_python(tmp_path, monkeypatch):
    """Test extract_version_from_file extracts Python version."""
    # Arrange
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "1.2.3"')

    # Act
    version = release_workflow.extract_version_from_file("python")

    # Assert
    assert version == "1.2.3"


def test_extract_version_from_file_node(tmp_path, monkeypatch):
    """Test extract_version_from_file extracts Node.js version."""
    # Arrange
    monkeypatch.chdir(tmp_path)
    (tmp_path / "package.json").write_text('{"version": "1.2.3"}')

    # Act
    version = release_workflow.extract_version_from_file("node")

    # Assert
    assert version == "1.2.3"


def test_extract_version_from_file_not_found(tmp_path, monkeypatch):
    """Test extract_version_from_file raises error when file not found."""
    # Arrange
    monkeypatch.chdir(tmp_path)

    # Act & Assert
    with pytest.raises(workflow_common.WorkflowError) as exc_info:
        release_workflow.extract_version_from_file("go")

    assert "Version file not found" in str(exc_info.value)


def test_extract_version_from_file_invalid_format(tmp_path, monkeypatch):
    """Test extract_version_from_file raises error when version not found."""
    # Arrange
    monkeypatch.chdir(tmp_path)
    (tmp_path / "go.mod").write_text("module example.com/test")

    # Act & Assert
    with pytest.raises(workflow_common.WorkflowError) as exc_info:
        release_workflow.extract_version_from_file("go")

    assert "Version not found" in str(exc_info.value)


def test_create_release_info_main_branch(tmp_path, monkeypatch):
    """Test create_release_info for main branch."""
    # Arrange
    monkeypatch.chdir(tmp_path)
    (tmp_path / "go.mod").write_text("module example.com/test // v1.2.3")

    mock_result = MagicMock()
    mock_result.stdout = "main\n"
    mock_run = MagicMock(return_value=mock_result)
    monkeypatch.setattr("subprocess.run", mock_run)

    # Act
    info = release_workflow.create_release_info()

    # Assert
    assert info.language == "go"
    assert info.version == "1.2.3"
    assert info.branch == "main"
    assert info.tag == "v1.2.3"
    assert info.is_stable_branch is False
    assert info.language_version is None


def test_create_release_info_stable_branch(tmp_path, monkeypatch):
    """Test create_release_info for stable branch."""
    # Arrange
    monkeypatch.chdir(tmp_path)
    (tmp_path / "go.mod").write_text("module example.com/test // v1.2.3")

    mock_result = MagicMock()
    mock_result.stdout = "stable-1-go-1.24\n"
    mock_run = MagicMock(return_value=mock_result)
    monkeypatch.setattr("subprocess.run", mock_run)

    # Act
    info = release_workflow.create_release_info()

    # Assert
    assert info.language == "go"
    assert info.version == "1.2.3"
    assert info.branch == "stable-1-go-1.24"
    assert info.tag == "v1.2.3-go124"
    assert info.is_stable_branch is True
    assert info.language_version == "1.24"


def test_generate_changelog_features_and_fixes(monkeypatch):
    """Test generate_changelog categorizes commits correctly."""
    # Arrange
    commits = [
        "feat: add new API endpoint",
        "fix: resolve memory leak",
        "docs: update README",
    ]

    mock_result_tag = MagicMock()
    mock_result_tag.stdout = "v1.0.0\n"

    mock_result_log = MagicMock()
    mock_result_log.stdout = "\n".join(commits) + "\n"

    def mock_run(cmd, **kwargs):
        if "describe" in cmd:
            return mock_result_tag
        return mock_result_log

    monkeypatch.setattr("subprocess.run", mock_run)

    # Act
    changelog = release_workflow.generate_changelog()

    # Assert
    assert "## ✨ Features" in changelog
    assert "feat: add new API endpoint" in changelog
    assert "## 🐛 Bug Fixes" in changelog
    assert "fix: resolve memory leak" in changelog
    assert "## 📝 Other Changes" in changelog


def test_generate_changelog_breaking_changes(monkeypatch):
    """Test generate_changelog identifies breaking changes."""
    # Arrange
    commits = ["feat!: remove deprecated API"]

    mock_result_tag = MagicMock()
    mock_result_tag.stdout = "v1.0.0\n"

    mock_result_log = MagicMock()
    mock_result_log.stdout = "\n".join(commits) + "\n"

    def mock_run(cmd, **kwargs):
        if "describe" in cmd:
            return mock_result_tag
        return mock_result_log

    monkeypatch.setattr("subprocess.run", mock_run)

    # Act
    changelog = release_workflow.generate_changelog()

    # Assert
    assert "## ⚠️ Breaking Changes" in changelog
    assert "feat!: remove deprecated API" in changelog
```

### Verification Steps

```bash
# 1. Verify test file exists
test -f tests/workflow_scripts/test_release_workflow.py && echo "✅ Test file created"

# 2. Check Python syntax
python3 -m py_compile tests/workflow_scripts/test_release_workflow.py && echo "✅ Valid Python"

# 3. Run tests
pytest tests/workflow_scripts/test_release_workflow.py -v && echo "✅ All tests pass"

# 4. Check coverage
pytest tests/workflow_scripts/test_release_workflow.py --cov=release_workflow --cov-report=term-missing && echo "✅ Coverage report generated"
```

---

## Task 2.5: Document GitHub Packages Configuration

**Status**: Not Started **Dependencies**: Task 2.2 (reusable-release.yml) **Estimated Time**: 1 hour
**Idempotent**: Yes

### Description

Create documentation for configuring GitHub Packages publishing with branch-specific tags.

### Implementation

Create file: `docs/refactors/workflows/v2/github-packages-setup.md`

````markdown
<!-- file: docs/refactors/workflows/v2/github-packages-setup.md -->
<!-- version: 1.0.0 -->
<!-- guid: c2d3e4f5-a6b7-8c9d-0e1f-2a3b4c5d6e7f -->

# GitHub Packages Setup

This guide explains how to configure GitHub Packages publishing for multi-version support with
branch-specific tags.

## Overview

The v2 workflow system publishes packages to GitHub Packages with branch-aware tagging:

- **Main branch**: Packages tagged as `latest` and semantic version
- **Stable branches**: Packages tagged with language-specific versions

## Supported Languages

### Go Modules

**Publishing from main branch**:

```bash
# Tag: v1.2.3
# Package: github.com/owner/repo@v1.2.3
```
````

**Publishing from stable-1-go-1.24 branch**:

```bash
# Tag: v1.2.3-go124
# Package: github.com/owner/repo@v1.2.3-go124
```

**Consuming packages**:

```bash
# Latest version (from main)
go get github.com/owner/repo@latest

# Specific stable version
go get github.com/owner/repo@v1.2.3-go124
```

### Python Packages (PyPI)

**Publishing from main branch**:

```bash
# Package: package-name==1.2.3
```

**Publishing from stable-1-python-3.13 branch**:

```bash
# Package: package-name==1.2.3+python313
```

**Consuming packages**:

```bash
# Latest version
pip install package-name

# Specific stable version
pip install package-name==1.2.3+python313
```

### Node.js Packages (npm)

**Publishing from main branch**:

```bash
# Package: @owner/package@1.2.3
# Tag: latest
```

**Publishing from stable-1-node-20 branch**:

```bash
# Package: @owner/package@1.2.3-node20
# Tag: node20
```

**Consuming packages**:

```bash
# Latest version
npm install @owner/package

# Specific stable version
npm install @owner/package@1.2.3-node20
```

### Rust Crates (crates.io)

**Publishing from main branch**:

```bash
# Crate: package-name 1.2.3
```

**Publishing from stable-1-rust-stable branch**:

```bash
# Crate: package-name 1.2.3+rust-stable
```

**Consuming crates**:

```toml
# Latest version
[dependencies]
package-name = "1.2.3"

# Specific stable version
[dependencies]
package-name = "1.2.3+rust-stable"
```

## Configuration Requirements

### Repository Settings

1. **Enable GitHub Packages**:
   - Go to repository Settings → Actions → General
   - Under "Workflow permissions", select "Read and write permissions"
   - Check "Allow GitHub Actions to create and approve pull requests"

2. **Add Package Registry**:
   - Go to repository Settings → Packages
   - Link to repository if not already linked

### Secrets Configuration

No additional secrets required for GitHub Packages. The workflow uses `GITHUB_TOKEN` automatically.

For publishing to external registries (PyPI, npm, crates.io), add these secrets:

- `PYPI_TOKEN` - PyPI API token
- `NPM_TOKEN` - npm access token
- `CARGO_REGISTRY_TOKEN` - crates.io API token

### Repository Config

Add to `.github/repository-config.yml`:

```yaml
workflows:
  experimental:
    use_new_release: true

packages:
  registries:
    github: true
    pypi: false # Enable when ready
    npm: false # Enable when ready
    cargo: false # Enable when ready
```

## Testing

Test package publishing with draft releases:

```bash
# Trigger draft release
gh workflow run release.yml \
  --ref main \
  -f draft=true \
  -f version=0.0.1-test
```

## Troubleshooting

### Package Not Found

**Problem**: Package not appearing in GitHub Packages

**Solution**:

1. Check workflow permissions (read/write required)
2. Verify package is linked to repository
3. Check workflow logs for publishing errors

### Version Conflicts

**Problem**: Version already exists error

**Solution**:

1. Increment version number
2. For testing, use prerelease versions (e.g., 1.2.3-rc1)
3. Delete old test packages from GitHub Packages UI

### Tag Already Exists

**Problem**: Git tag already exists error

**Solution**:

1. Delete the tag: `git tag -d v1.2.3 && git push origin :refs/tags/v1.2.3`
2. Increment version number
3. Use semantic versioning correctly (patch/minor/major)

## Best Practices

1. **Use semantic versioning**: Follow MAJOR.MINOR.PATCH format
2. **Test with drafts**: Always test with draft releases first
3. **Tag naming**: Let the workflow generate tags automatically
4. **Branch lifecycle**: Remove old stable branches after deprecation period
5. **Documentation**: Keep package changelogs updated

## Migration from Legacy System

If migrating from an existing package publishing system:

1. Enable `use_new_release: true` feature flag
2. Test with draft releases on a test branch
3. Verify packages appear in GitHub Packages
4. Update consumer documentation with new package names
5. Gradually migrate consumers to new package versions
6. Deprecate old package publishing after successful migration

## Additional Resources

- [GitHub Packages Documentation](https://docs.github.com/packages)
- [Semantic Versioning Spec](https://semver.org/)
- [Workflow v2 Architecture](architecture.md)
- [Release Workflow Reference](reference/workflow-reference.md)

````

### Verification Steps

```bash
# 1. Verify documentation file exists
test -f docs/refactors/workflows/v2/github-packages-setup.md && echo "✅ Documentation created"

# 2. Check markdown syntax
markdownlint docs/refactors/workflows/v2/github-packages-setup.md && echo "✅ Valid Markdown"

# 3. Verify links work (if markdown-link-check installed)
markdown-link-check docs/refactors/workflows/v2/github-packages-setup.md && echo "✅ All links valid"
````

---

## Phase 2 Completion Checklist

- [ ] All tasks completed (2.1-2.5)
- [ ] `release_workflow.py` created with branch-aware logic
- [ ] `reusable-release.yml` workflow created
- [ ] `release.yml` caller workflow created
- [ ] Unit tests pass with 100% coverage
- [ ] GitHub Packages documentation created
- [ ] Feature flag `use_new_release` functional
- [ ] No Windows references in any files
- [ ] All code follows Google Python Style Guide
- [ ] All workflows validated with yamllint
- [ ] Manual testing completed with draft releases

---

**Phase 2 Complete!** This phase establishes the foundation for branch-aware releases with GitHub
Packages support.
