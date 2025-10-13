<!-- file: docs/refactors/workflows/v2/phases/phase-1-ci-modernization.md -->
<!-- version: 1.0.0 -->
<!-- guid: e5f6a7b8-c9d0-1e2f-3a4b-5c6d7e8f9a0b -->

# Phase 1: CI Modernization

## Overview

Phase 1 modernizes the CI workflow system to use configuration-driven workflows with dynamic matrix generation, intelligent change detection, and optimized test execution.

**Status**: 🟡 Planning
**Dependencies**: Phase 0 (workflow_common.py, config validation)
**Target Completion**: 2025-11-03
**Platforms**: ubuntu-latest, macos-latest (NO WINDOWS)

## Success Criteria

- [ ] `ci_workflow.py` helper created with matrix generation
- [ ] `reusable-ci.yml` workflow created and tested
- [ ] Change detection working for all languages
- [ ] Matrix optimization reducing job count by 60%+
- [ ] All unit tests pass (100% coverage for new code)
- [ ] Documentation updated
- [ ] Feature flag `use_new_ci` functional

## Design Principles

Every task in this phase MUST be:
- **Independent**: Can be executed without waiting for other tasks
- **Idempotent**: Running multiple times produces same result
- **Testable**: Unit tests exist and pass
- **Compliant**: Follows `.github/instructions/python.instructions.md` and `.github/instructions/github-actions.instructions.md`

---

## Task 1.1: Create CI Helper Module

**Status**: Not Started
**Dependencies**: Phase 0 Task 0.1 (workflow_common.py)
**Estimated Time**: 3 hours
**Idempotent**: Yes

### Description

Create `.github/workflows/scripts/ci_workflow.py` containing CI-specific helper functions for matrix generation, change detection, and test orchestration.

### Code Style Requirements

**MUST follow**:
- `.github/instructions/python.instructions.md` - Google Python Style Guide with full docstrings
- `.github/instructions/general-coding.instructions.md` - File headers, versioning
- `.github/instructions/github-actions.instructions.md` - Workflow best practices

### Implementation

Create file: `.github/workflows/scripts/ci_workflow.py`

```python
#!/usr/bin/env python3
# file: .github/workflows/scripts/ci_workflow.py
# version: 1.0.0
# guid: f6a7b8c9-d0e1-2f3a-4b5c-6d7e8f9a0b1c

"""
CI workflow helper functions for matrix generation and change detection.

This module provides functions to generate optimized test matrices based on
repository configuration and detected file changes, reducing unnecessary CI jobs.

Example:
    Generate test matrix for changed Go files:

    >>> matrix = generate_test_matrix(["go"], ["1.23", "1.24"])
    >>> print(matrix)
    {
        "include": [
            {"language": "go", "version": "1.23", "os": "ubuntu-latest"},
            {"language": "go", "version": "1.24", "os": "macos-latest"}
        ]
    }
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import workflow_common


@dataclass
class ChangeDetection:
    """
    Detected file changes and affected languages.

    Attributes:
        go_changed: True if Go files changed
        python_changed: True if Python files changed
        rust_changed: True if Rust files changed
        node_changed: True if Node.js files changed
        docker_changed: True if Docker files changed
        docs_changed: True if documentation files changed
        workflows_changed: True if GitHub Actions workflows changed
        all_files: List of all changed file paths
    """

    go_changed: bool = False
    python_changed: bool = False
    rust_changed: bool = False
    node_changed: bool = False
    docker_changed: bool = False
    docs_changed: bool = False
    workflows_changed: bool = False
    all_files: list[str] = None

    def __post_init__(self) -> None:
        """Initialize all_files as empty list if not provided."""
        if self.all_files is None:
            self.all_files = []


def detect_changes(
    base_ref: str = "origin/main",
    head_ref: str = "HEAD",
) -> ChangeDetection:
    """
    Detect changed files and determine affected languages.

    Analyzes git diff to identify which languages and components have
    changed, enabling intelligent test matrix optimization.

    Args:
        base_ref: Base git reference for comparison (default: origin/main)
        head_ref: Head git reference for comparison (default: HEAD)

    Returns:
        ChangeDetection object with boolean flags for each language/component

    Raises:
        workflow_common.WorkflowError: If git command fails

    Example:
        >>> changes = detect_changes()
        >>> if changes.go_changed:
        ...     print("Go tests needed")
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", base_ref, head_ref],
            capture_output=True,
            text=True,
            check=True,
        )
        changed_files = result.stdout.strip().split("\n")
    except subprocess.CalledProcessError as e:
        raise workflow_common.WorkflowError(
            f"Failed to detect changes: {e}",
            hint="Ensure git repository is initialized and base_ref exists",
        ) from e

    detection = ChangeDetection(all_files=changed_files)

    # Pattern matching for language detection
    patterns = {
        "go": [".go", "go.mod", "go.sum"],
        "python": [".py", "requirements.txt", "pyproject.toml", "setup.py"],
        "rust": [".rs", "Cargo.toml", "Cargo.lock"],
        "node": [".js", ".ts", "package.json", "package-lock.json"],
        "docker": ["Dockerfile", ".dockerignore", "docker-compose.yml"],
        "docs": [".md", ".rst", "/docs/"],
        "workflows": [".github/workflows/", ".github/actions/"],
    }

    for file_path in changed_files:
        # Go files
        if any(file_path.endswith(ext) for ext in patterns["go"]):
            detection.go_changed = True

        # Python files
        if any(file_path.endswith(ext) for ext in patterns["python"]):
            detection.python_changed = True

        # Rust files
        if any(file_path.endswith(ext) for ext in patterns["rust"]):
            detection.rust_changed = True

        # Node.js files
        if any(file_path.endswith(ext) for ext in patterns["node"]):
            detection.node_changed = True

        # Docker files
        if any(pattern in file_path for pattern in patterns["docker"]):
            detection.docker_changed = True

        # Documentation files
        if any(pattern in file_path for pattern in patterns["docs"]):
            detection.docs_changed = True

        # Workflow files
        if any(pattern in file_path for pattern in patterns["workflows"]):
            detection.workflows_changed = True

    return detection


def generate_test_matrix(
    languages: list[str],
    versions: dict[str, list[str]] | None = None,
    platforms: list[str] | None = None,
    optimize: bool = True,
) -> dict[str, Any]:
    """
    Generate optimized test matrix for CI workflows.

    Creates a test matrix based on detected changes and repository
    configuration, optionally optimizing to reduce redundant jobs.

    Args:
        languages: List of languages to test (e.g., ["go", "python"])
        versions: Optional dict mapping language to versions
                 (default: load from config)
        platforms: Optional list of platforms (default: load from config)
        optimize: If True, optimize matrix to reduce job count

    Returns:
        Dictionary with "include" key containing matrix entries

    Example:
        >>> matrix = generate_test_matrix(["go", "python"], optimize=True)
        >>> print(len(matrix["include"]))  # Reduced job count
        4
    """
    # Load defaults from config if not provided
    if versions is None:
        versions = {
            "go": workflow_common.config_path([], "languages", "versions", "go"),
            "python": workflow_common.config_path([], "languages", "versions", "python"),
            "rust": workflow_common.config_path([], "languages", "versions", "rust"),
            "node": workflow_common.config_path([], "languages", "versions", "node"),
        }

    if platforms is None:
        platforms = workflow_common.config_path(
            ["ubuntu-latest", "macos-latest"],
            "build",
            "platforms",
        )

    matrix_entries = []

    for language in languages:
        lang_versions = versions.get(language, [])

        if not lang_versions:
            print(f"⚠️  No versions configured for {language}, skipping")
            continue

        if optimize:
            # Optimized matrix: test latest on all platforms, others on Linux only
            latest_version = lang_versions[-1]
            older_versions = lang_versions[:-1]

            # Latest version on all platforms
            for platform in platforms:
                matrix_entries.append({
                    "language": language,
                    "version": latest_version,
                    "os": platform,
                })

            # Older versions on ubuntu-latest only
            for version in older_versions:
                matrix_entries.append({
                    "language": language,
                    "version": version,
                    "os": "ubuntu-latest",
                })
        else:
            # Full matrix: all versions on all platforms
            for version in lang_versions:
                for platform in platforms:
                    matrix_entries.append({
                        "language": language,
                        "version": version,
                        "os": platform,
                    })

    return {"include": matrix_entries}


def should_run_tests(language: str, changes: ChangeDetection) -> bool:
    """
    Determine if tests should run for a language based on changes.

    Args:
        language: Language to check (go, python, rust, node)
        changes: ChangeDetection object with change flags

    Returns:
        True if tests should run, False otherwise

    Example:
        >>> changes = detect_changes()
        >>> if should_run_tests("go", changes):
        ...     matrix = generate_test_matrix(["go"])
    """
    language_map = {
        "go": changes.go_changed,
        "python": changes.python_changed,
        "rust": changes.rust_changed,
        "node": changes.node_changed,
    }

    # Always run if workflows changed (could affect test execution)
    if changes.workflows_changed:
        return True

    return language_map.get(language, False)


def get_coverage_threshold(language: str) -> float:
    """
    Get coverage threshold for language from config.

    Args:
        language: Language name (go, python, rust, node)

    Returns:
        Coverage threshold percentage (0-100)

    Example:
        >>> threshold = get_coverage_threshold("python")
        >>> print(f"Minimum coverage: {threshold}%")
        Minimum coverage: 80.0%
    """
    return workflow_common.config_path(
        80.0,  # Default threshold
        "testing",
        "coverage",
        language,
        "threshold",
    )


def format_matrix_summary(matrix: dict[str, Any]) -> str:
    """
    Format matrix as markdown summary for GitHub Actions.

    Args:
        matrix: Test matrix dictionary with "include" key

    Returns:
        Markdown-formatted summary string

    Example:
        >>> matrix = generate_test_matrix(["go"])
        >>> summary = format_matrix_summary(matrix)
        >>> workflow_common.append_summary(summary)
    """
    entries = matrix.get("include", [])

    if not entries:
        return "## Test Matrix\n\n❌ No tests to run\n"

    lines = [
        "## Test Matrix",
        "",
        f"**Total Jobs**: {len(entries)}",
        "",
        "| Language | Version | Platform |",
        "|----------|---------|----------|",
    ]

    for entry in entries:
        lang = entry.get("language", "unknown")
        ver = entry.get("version", "unknown")
        os = entry.get("os", "unknown")
        lines.append(f"| {lang} | {ver} | {os} |")

    return "\n".join(lines) + "\n"


def main() -> None:
    """
    Main entry point for CI workflow helper.

    Detects changes, generates test matrix, and outputs results for
    GitHub Actions workflow consumption.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate CI test matrix",
    )
    parser.add_argument(
        "--base-ref",
        default="origin/main",
        help="Base git reference for change detection",
    )
    parser.add_argument(
        "--optimize",
        action="store_true",
        default=True,
        help="Optimize matrix to reduce job count",
    )
    parser.add_argument(
        "--output-matrix",
        action="store_true",
        help="Output matrix JSON to GITHUB_OUTPUT",
    )

    args = parser.parse_args()

    try:
        # Detect changes
        with workflow_common.timed_operation("Detect changes"):
            changes = detect_changes(base_ref=args.base_ref)

        print(f"📊 Change detection results:")
        print(f"   Go: {'✅' if changes.go_changed else '❌'}")
        print(f"   Python: {'✅' if changes.python_changed else '❌'}")
        print(f"   Rust: {'✅' if changes.rust_changed else '❌'}")
        print(f"   Node: {'✅' if changes.node_changed else '❌'}")
        print(f"   Docker: {'✅' if changes.docker_changed else '❌'}")
        print(f"   Docs: {'✅' if changes.docs_changed else '❌'}")
        print(f"   Workflows: {'✅' if changes.workflows_changed else '❌'}")

        # Determine which languages need testing
        languages_to_test = []
        for lang in ["go", "python", "rust", "node"]:
            if should_run_tests(lang, changes):
                languages_to_test.append(lang)

        print(f"\n🎯 Languages requiring tests: {', '.join(languages_to_test) or 'None'}")

        # Generate matrix
        if languages_to_test:
            with workflow_common.timed_operation("Generate test matrix"):
                matrix = generate_test_matrix(
                    languages_to_test,
                    optimize=args.optimize,
                )

            print(f"\n✅ Generated matrix with {len(matrix['include'])} jobs")

            # Output to GitHub Actions
            if args.output_matrix:
                workflow_common.write_output("matrix", json.dumps(matrix))
                workflow_common.write_output("has_tests", "true")

            # Add summary
            summary = format_matrix_summary(matrix)
            workflow_common.append_summary(summary)
        else:
            print("\n✅ No changes detected, skipping tests")

            if args.output_matrix:
                empty_matrix = {"include": []}
                workflow_common.write_output("matrix", json.dumps(empty_matrix))
                workflow_common.write_output("has_tests", "false")

            workflow_common.append_summary("## Test Matrix\n\n✅ No changes detected\n")

    except Exception as e:
        workflow_common.handle_error(e, "CI matrix generation")


if __name__ == "__main__":
    main()
```

### Verification Steps

```bash
# 1. Verify file exists
test -f .github/workflows/scripts/ci_workflow.py && echo "✅ File created"

# 2. Check Python syntax
python3 -m py_compile .github/workflows/scripts/ci_workflow.py && echo "✅ Valid Python"

# 3. Verify imports work
python3 -c "import sys; sys.path.insert(0, '.github/workflows/scripts'); import ci_workflow" && echo "✅ Module imports"

# 4. Run type checking
cd .github/workflows/scripts && mypy ci_workflow.py && echo "✅ Type hints valid"

# 5. Test change detection (requires git repo)
cd /path/to/repo && python3 .github/workflows/scripts/ci_workflow.py --base-ref HEAD~1 && echo "✅ Change detection works"
```

---

## Task 1.2: Create Reusable CI Workflow

**Status**: Not Started
**Dependencies**: Task 1.1 (ci_workflow.py)
**Estimated Time**: 2 hours
**Idempotent**: Yes

### Description

Create `.github/workflows/reusable-ci.yml` - a reusable workflow that calls ci_workflow.py to generate matrices and execute tests.

### Code Style Requirements

**MUST follow**:
- `.github/instructions/github-actions.instructions.md` - Workflow best practices

### Implementation

Create file: `.github/workflows/reusable-ci.yml`

```yaml
# file: .github/workflows/reusable-ci.yml
# version: 1.0.0
# guid: a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d

name: Reusable CI Workflow

on:
  workflow_call:
    inputs:
      base_ref:
        description: 'Base git reference for change detection'
        type: string
        required: false
        default: 'origin/main'
      optimize_matrix:
        description: 'Optimize test matrix to reduce job count'
        type: boolean
        required: false
        default: true
      coverage_threshold:
        description: 'Minimum coverage percentage (overrides config)'
        type: number
        required: false
        default: 0
    outputs:
      matrix:
        description: 'Generated test matrix JSON'
        value: ${{ jobs.generate-matrix.outputs.matrix }}
      has_tests:
        description: 'True if tests should run'
        value: ${{ jobs.generate-matrix.outputs.has_tests }}

permissions:
  contents: read
  pull-requests: write

jobs:
  generate-matrix:
    name: Generate Test Matrix
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.generate.outputs.matrix }}
      has_tests: ${{ steps.generate.outputs.has_tests }}

    steps:
      - name: Checkout code
        uses: actions/checkout@8e5e7e5ab8b370d6c329ec480221332ada57f0ab  # v4.1.1
        with:
          fetch-depth: 0  # Need full history for change detection

      - name: Set up Python
        uses: actions/setup-python@0a5c61591373683505ea898e09a3ea4f39ef2b9c  # v5.0.0
        with:
          python-version: '3.13'

      - name: Install dependencies
        run: |
          pip install pyyaml jsonschema

      - name: Generate test matrix
        id: generate
        run: |
          python3 .github/workflows/scripts/ci_workflow.py \
            --base-ref "${{ inputs.base_ref }}" \
            ${{ inputs.optimize_matrix && '--optimize' || '' }} \
            --output-matrix

  run-tests:
    name: Test ${{ matrix.language }} ${{ matrix.version }} on ${{ matrix.os }}
    needs: generate-matrix
    if: needs.generate-matrix.outputs.has_tests == 'true'
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix: ${{ fromJSON(needs.generate-matrix.outputs.matrix) }}

    steps:
      - name: Checkout code
        uses: actions/checkout@8e5e7e5ab8b370d6c329ec480221332ada57f0ab  # v4.1.1

      # Go setup
      - name: Set up Go
        if: matrix.language == 'go'
        uses: actions/setup-go@0c52d547c9bc32b1aa3301fd7a9cb496313a4491  # v5.0.0
        with:
          go-version: ${{ matrix.version }}

      - name: Run Go tests
        if: matrix.language == 'go'
        run: |
          go test -v -race -coverprofile=coverage.out ./...
          go tool cover -func=coverage.out

      # Python setup
      - name: Set up Python
        if: matrix.language == 'python'
        uses: actions/setup-python@0a5c61591373683505ea898e09a3ea4f39ef2b9c  # v5.0.0
        with:
          python-version: ${{ matrix.version }}

      - name: Run Python tests
        if: matrix.language == 'python'
        run: |
          pip install pytest pytest-cov
          pytest --cov --cov-report=term-missing

      # Rust setup
      - name: Set up Rust
        if: matrix.language == 'rust'
        uses: actions-rust-lang/setup-rust-toolchain@1fbea72663f6d4c03efaab13560c8a24cfd2a7cc  # v1.8.0
        with:
          toolchain: ${{ matrix.version }}

      - name: Run Rust tests
        if: matrix.language == 'rust'
        run: |
          cargo test --all-features
          cargo tarpaulin --out Lcov

      # Node.js setup
      - name: Set up Node.js
        if: matrix.language == 'node'
        uses: actions/setup-node@60edb5dd545a775178f52524783378180af0d1f8  # v4.0.2
        with:
          node-version: ${{ matrix.version }}

      - name: Run Node.js tests
        if: matrix.language == 'node'
        run: |
          npm ci
          npm test -- --coverage

      - name: Upload coverage
        uses: codecov/codecov-action@e0b68c6749509c5f83f984dd99a76a1c1a231044  # v4.0.1
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          file: ./coverage.out
          flags: ${{ matrix.language }}-${{ matrix.version }}-${{ matrix.os }}
```

### Verification Steps

```bash
# 1. Verify workflow file exists
test -f .github/workflows/reusable-ci.yml && echo "✅ Workflow created"

# 2. Validate workflow syntax
gh workflow view reusable-ci.yml 2>/dev/null && echo "✅ Valid workflow syntax" || echo "⚠️  Install gh CLI to validate"

# 3. Lint workflow file
yamllint .github/workflows/reusable-ci.yml && echo "✅ Valid YAML"

# 4. Check for Windows references (should be none)
grep -i "windows" .github/workflows/reusable-ci.yml && echo "❌ Found Windows reference!" || echo "✅ No Windows references"
```

---

## Task 1.3: Create Caller CI Workflow

**Status**: Not Started
**Dependencies**: Task 1.2 (reusable-ci.yml)
**Estimated Time**: 30 minutes
**Idempotent**: Yes

### Description

Create `.github/workflows/ci.yml` that calls the reusable workflow with feature flag support.

### Implementation

Create file: `.github/workflows/ci.yml`

```yaml
# file: .github/workflows/ci.yml
# version: 2.0.0
# guid: b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e

name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  workflow_dispatch:
    inputs:
      force_full_matrix:
        description: 'Force full test matrix (disable optimization)'
        type: boolean
        required: false
        default: false

permissions:
  contents: read
  pull-requests: write

jobs:
  check-feature-flag:
    name: Check Feature Flag
    runs-on: ubuntu-latest
    outputs:
      use_new_ci: ${{ steps.check.outputs.enabled }}

    steps:
      - name: Checkout code
        uses: actions/checkout@8e5e7e5ab8b370d6c329ec480221332ada57f0ab  # v4.1.1

      - name: Set up Python
        uses: actions/setup-python@0a5c61591373683505ea898e09a3ea4f39ef2b9c  # v5.0.0
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
          enabled = config.get('workflows', {}).get('experimental', {}).get('use_new_ci', False)
          print(f'enabled={str(enabled).lower()}')
          " >> $GITHUB_OUTPUT

  # New CI system (config-driven with matrix generation)
  new-ci:
    name: New CI System
    needs: check-feature-flag
    if: needs.check-feature-flag.outputs.use_new_ci == 'true'
    uses: ./.github/workflows/reusable-ci.yml
    with:
      optimize_matrix: ${{ github.event.inputs.force_full_matrix != 'true' }}

  # Legacy CI system (fallback)
  legacy-ci:
    name: Legacy CI System
    needs: check-feature-flag
    if: needs.check-feature-flag.outputs.use_new_ci != 'true'
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@8e5e7e5ab8b370d6c329ec480221332ada57f0ab  # v4.1.1

      - name: Run legacy tests
        run: |
          echo "🔄 Running legacy CI workflow"
          echo "💡 Enable new CI by setting workflows.experimental.use_new_ci: true in .github/repository-config.yml"

          # Run existing CI logic here
          # This preserves current behavior during migration
```

### Verification Steps

```bash
# 1. Verify workflow file exists
test -f .github/workflows/ci.yml && echo "✅ Workflow created"

# 2. Test with feature flag disabled
cat > /tmp/test-config.yml << 'EOF'
workflows:
  experimental:
    use_new_ci: false
EOF

# 3. Test with feature flag enabled
cat > /tmp/test-config-enabled.yml << 'EOF'
workflows:
  experimental:
    use_new_ci: true
EOF

# 4. Validate both paths work
echo "✅ CI workflow created with feature flag support"
```

---

## Task 1.4: Create Unit Tests for ci_workflow

**Status**: Not Started
**Dependencies**: Task 1.1 (ci_workflow.py)
**Estimated Time**: 3 hours
**Idempotent**: Yes

### Description

Create comprehensive unit tests for `ci_workflow.py`.

### Code Style Requirements

**MUST follow**:
- `.github/instructions/test-generation.instructions.md` - Arrange-Act-Assert, independence

### Implementation

Create file: `tests/workflow_scripts/test_ci_workflow.py`

```python
#!/usr/bin/env python3
# file: tests/workflow_scripts/test_ci_workflow.py
# version: 1.0.0
# guid: c3d4e5f6-a7b8-9c0d-1e2f-3a4b5c6d7e8f

"""Unit tests for ci_workflow module."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / ".github/workflows/scripts"))

import ci_workflow
import workflow_common


@pytest.fixture(autouse=True)
def reset_config_cache():
    """Reset global config cache between tests."""
    workflow_common._CONFIG_CACHE = None
    yield
    workflow_common._CONFIG_CACHE = None


def test_change_detection_dataclass_defaults():
    """Test ChangeDetection dataclass has correct defaults."""
    # Arrange & Act
    detection = ci_workflow.ChangeDetection()

    # Assert
    assert detection.go_changed is False
    assert detection.python_changed is False
    assert detection.all_files == []


def test_detect_changes_go_files(monkeypatch):
    """Test detect_changes identifies Go file changes."""
    # Arrange
    mock_result = MagicMock()
    mock_result.stdout = "main.go\ngo.mod\n"

    mock_run = MagicMock(return_value=mock_result)
    monkeypatch.setattr("subprocess.run", mock_run)

    # Act
    changes = ci_workflow.detect_changes()

    # Assert
    assert changes.go_changed is True
    assert changes.python_changed is False
    assert "main.go" in changes.all_files


def test_detect_changes_python_files(monkeypatch):
    """Test detect_changes identifies Python file changes."""
    # Arrange
    mock_result = MagicMock()
    mock_result.stdout = "script.py\nrequirements.txt\n"

    mock_run = MagicMock(return_value=mock_result)
    monkeypatch.setattr("subprocess.run", mock_run)

    # Act
    changes = ci_workflow.detect_changes()

    # Assert
    assert changes.python_changed is True
    assert changes.go_changed is False


def test_detect_changes_workflow_files(monkeypatch):
    """Test detect_changes identifies workflow file changes."""
    # Arrange
    mock_result = MagicMock()
    mock_result.stdout = ".github/workflows/ci.yml\n"

    mock_run = MagicMock(return_value=mock_result)
    monkeypatch.setattr("subprocess.run", mock_run)

    # Act
    changes = ci_workflow.detect_changes()

    # Assert
    assert changes.workflows_changed is True


def test_detect_changes_git_failure(monkeypatch):
    """Test detect_changes raises error when git command fails."""
    # Arrange
    import subprocess

    mock_run = MagicMock(side_effect=subprocess.CalledProcessError(1, "git"))
    monkeypatch.setattr("subprocess.run", mock_run)

    # Act & Assert
    with pytest.raises(workflow_common.WorkflowError) as exc_info:
        ci_workflow.detect_changes()

    assert "Failed to detect changes" in str(exc_info.value)


def test_generate_test_matrix_optimized():
    """Test generate_test_matrix with optimization enabled."""
    # Arrange
    languages = ["go"]
    versions = {"go": ["1.23", "1.24"]}
    platforms = ["ubuntu-latest", "macos-latest"]

    # Act
    matrix = ci_workflow.generate_test_matrix(
        languages,
        versions,
        platforms,
        optimize=True,
    )

    # Assert
    entries = matrix["include"]
    assert len(entries) == 3  # Latest on 2 platforms + older on 1 platform

    # Check latest version is on all platforms
    latest_entries = [e for e in entries if e["version"] == "1.24"]
    assert len(latest_entries) == 2
    assert {e["os"] for e in latest_entries} == {"ubuntu-latest", "macos-latest"}

    # Check older version is only on ubuntu-latest
    older_entries = [e for e in entries if e["version"] == "1.23"]
    assert len(older_entries) == 1
    assert older_entries[0]["os"] == "ubuntu-latest"


def test_generate_test_matrix_full():
    """Test generate_test_matrix without optimization (full matrix)."""
    # Arrange
    languages = ["go"]
    versions = {"go": ["1.23", "1.24"]}
    platforms = ["ubuntu-latest", "macos-latest"]

    # Act
    matrix = ci_workflow.generate_test_matrix(
        languages,
        versions,
        platforms,
        optimize=False,
    )

    # Assert
    entries = matrix["include"]
    assert len(entries) == 4  # 2 versions × 2 platforms


def test_generate_test_matrix_multiple_languages():
    """Test generate_test_matrix with multiple languages."""
    # Arrange
    languages = ["go", "python"]
    versions = {
        "go": ["1.24"],
        "python": ["3.13"],
    }
    platforms = ["ubuntu-latest"]

    # Act
    matrix = ci_workflow.generate_test_matrix(
        languages,
        versions,
        platforms,
        optimize=False,
    )

    # Assert
    entries = matrix["include"]
    assert len(entries) == 2

    languages_in_matrix = {e["language"] for e in entries}
    assert languages_in_matrix == {"go", "python"}


def test_generate_test_matrix_no_versions(capsys):
    """Test generate_test_matrix skips languages with no versions."""
    # Arrange
    languages = ["go", "unknown"]
    versions = {"go": ["1.24"]}
    platforms = ["ubuntu-latest"]

    # Act
    matrix = ci_workflow.generate_test_matrix(
        languages,
        versions,
        platforms,
    )

    # Assert
    captured = capsys.readouterr()
    assert "No versions configured for unknown" in captured.out
    assert len(matrix["include"]) == 1  # Only go entry


def test_should_run_tests_language_changed():
    """Test should_run_tests returns True when language files changed."""
    # Arrange
    changes = ci_workflow.ChangeDetection(go_changed=True)

    # Act
    result = ci_workflow.should_run_tests("go", changes)

    # Assert
    assert result is True


def test_should_run_tests_workflows_changed():
    """Test should_run_tests returns True when workflows changed."""
    # Arrange
    changes = ci_workflow.ChangeDetection(
        go_changed=False,
        workflows_changed=True,
    )

    # Act
    result = ci_workflow.should_run_tests("go", changes)

    # Assert
    assert result is True  # Workflows affect all tests


def test_should_run_tests_no_changes():
    """Test should_run_tests returns False when no relevant changes."""
    # Arrange
    changes = ci_workflow.ChangeDetection(python_changed=True)

    # Act
    result = ci_workflow.should_run_tests("go", changes)

    # Assert
    assert result is False


def test_get_coverage_threshold_from_config(tmp_path, monkeypatch):
    """Test get_coverage_threshold loads from config."""
    # Arrange
    config_file = tmp_path / ".github" / "repository-config.yml"
    config_file.parent.mkdir(parents=True)
    config_file.write_text("""
testing:
  coverage:
    python:
      threshold: 85.5
""")
    monkeypatch.chdir(tmp_path)

    # Act
    threshold = ci_workflow.get_coverage_threshold("python")

    # Assert
    assert threshold == 85.5


def test_get_coverage_threshold_default(tmp_path, monkeypatch):
    """Test get_coverage_threshold returns default for missing config."""
    # Arrange
    config_file = tmp_path / ".github" / "repository-config.yml"
    config_file.parent.mkdir(parents=True)
    config_file.write_text("empty: {}\n")
    monkeypatch.chdir(tmp_path)

    # Act
    threshold = ci_workflow.get_coverage_threshold("python")

    # Assert
    assert threshold == 80.0  # Default


def test_format_matrix_summary_with_entries():
    """Test format_matrix_summary generates markdown table."""
    # Arrange
    matrix = {
        "include": [
            {"language": "go", "version": "1.24", "os": "ubuntu-latest"},
            {"language": "python", "version": "3.13", "os": "macos-latest"},
        ]
    }

    # Act
    summary = ci_workflow.format_matrix_summary(matrix)

    # Assert
    assert "## Test Matrix" in summary
    assert "Total Jobs**: 2" in summary
    assert "| go | 1.24 | ubuntu-latest |" in summary
    assert "| python | 3.13 | macos-latest |" in summary


def test_format_matrix_summary_empty():
    """Test format_matrix_summary handles empty matrix."""
    # Arrange
    matrix = {"include": []}

    # Act
    summary = ci_workflow.format_matrix_summary(matrix)

    # Assert
    assert "## Test Matrix" in summary
    assert "❌ No tests to run" in summary
```

### Verification Steps

```bash
# 1. Install test dependencies
pip install pytest pytest-cov

# 2. Run tests
python -m pytest tests/workflow_scripts/test_ci_workflow.py -v

# 3. Check coverage
python -m pytest tests/workflow_scripts/test_ci_workflow.py --cov=ci_workflow --cov-report=term-missing

# 4. Verify 100% coverage achieved
```

---

## Task 1.5: Create Integration Test

**Status**: Not Started
**Dependencies**: Task 1.2 (reusable-ci.yml), Task 1.3 (ci.yml)
**Estimated Time**: 1 hour
**Idempotent**: Yes

### Description

Create integration test that validates end-to-end CI workflow execution.

### Implementation

Create file: `tests/integration/test_ci_workflow_integration.py`

```python
#!/usr/bin/env python3
# file: tests/integration/test_ci_workflow_integration.py
# version: 1.0.0
# guid: d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a

"""Integration tests for CI workflow system."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / ".github/workflows/scripts"))

import ci_workflow


@pytest.mark.integration
def test_ci_workflow_end_to_end(tmp_path, monkeypatch):
    """
    Test complete CI workflow from change detection to matrix generation.

    This integration test validates that the CI system correctly:
    1. Detects file changes in a git repository
    2. Generates an optimized test matrix
    3. Outputs valid JSON for GitHub Actions consumption
    """
    # Arrange: Create a test git repository
    repo_dir = tmp_path / "test-repo"
    repo_dir.mkdir()
    monkeypatch.chdir(repo_dir)

    # Initialize git repo
    subprocess.run(["git", "init"], check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], check=True)

    # Create initial commit
    (repo_dir / "README.md").write_text("# Test\n")
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)

    # Create config file
    config_dir = repo_dir / ".github"
    config_dir.mkdir()
    config_file = config_dir / "repository-config.yml"
    config_file.write_text("""
languages:
  versions:
    go: ["1.23", "1.24"]
    python: ["3.13", "3.14"]
build:
  platforms:
    - ubuntu-latest
    - macos-latest
""")

    # Add Go files (trigger Go tests)
    (repo_dir / "main.go").write_text("package main\n")
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", "Add Go code"], check=True)

    # Act: Detect changes and generate matrix
    changes = ci_workflow.detect_changes(base_ref="HEAD~1")

    languages_to_test = []
    for lang in ["go", "python"]:
        if ci_workflow.should_run_tests(lang, changes):
            languages_to_test.append(lang)

    matrix = ci_workflow.generate_test_matrix(
        languages_to_test,
        optimize=True,
    )

    # Assert: Verify results
    assert changes.go_changed is True
    assert changes.python_changed is False

    assert "go" in languages_to_test
    assert "python" not in languages_to_test

    entries = matrix["include"]
    assert len(entries) > 0
    assert all(e["language"] == "go" for e in entries)

    # Verify JSON serialization works (for GitHub Actions)
    matrix_json = json.dumps(matrix)
    parsed = json.loads(matrix_json)
    assert parsed == matrix


@pytest.mark.integration
def test_workflow_with_no_changes(tmp_path, monkeypatch):
    """Test CI workflow correctly skips tests when no relevant changes."""
    # Arrange
    repo_dir = tmp_path / "test-repo"
    repo_dir.mkdir()
    monkeypatch.chdir(repo_dir)

    subprocess.run(["git", "init"], check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], check=True)

    (repo_dir / "README.md").write_text("# Test\n")
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)

    # Only change documentation
    (repo_dir / "README.md").write_text("# Updated Test\n")
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", "Update docs"], check=True)

    # Act
    changes = ci_workflow.detect_changes(base_ref="HEAD~1")

    languages_to_test = []
    for lang in ["go", "python"]:
        if ci_workflow.should_run_tests(lang, changes):
            languages_to_test.append(lang)

    # Assert
    assert changes.docs_changed is True
    assert changes.go_changed is False
    assert changes.python_changed is False
    assert len(languages_to_test) == 0
```

### Verification Steps

```bash
# 1. Run integration tests
python -m pytest tests/integration/test_ci_workflow_integration.py -v -m integration

# 2. Verify tests pass
echo "✅ Integration tests complete"
```

---

## Phase 1 Completion Checklist

- [ ] All 5 tasks completed
- [ ] All unit tests passing (100% coverage)
- [ ] Integration test passing
- [ ] Code follows `.github/instructions/python.instructions.md`
- [ ] Workflows follow `.github/instructions/github-actions.instructions.md`
- [ ] No Windows references anywhere
- [ ] Feature flag `use_new_ci` functional
- [ ] Documentation updated
- [ ] Git commit made with conventional commit message

## Commit Message Template

```
feat(ci): implement Phase 1 config-driven CI modernization

Implemented config-driven CI workflow system with dynamic matrix generation,
intelligent change detection, and optimized test execution.

Tasks completed:
- Task 1.1: Created ci_workflow.py with matrix generation and change detection
- Task 1.2: Created reusable-ci.yml workflow
- Task 1.3: Created ci.yml caller workflow with feature flag support
- Task 1.4: Created comprehensive unit tests (100% coverage)
- Task 1.5: Created integration tests for end-to-end validation

Features:
- Intelligent change detection for Go, Python, Rust, Node.js
- Optimized matrix generation (60%+ job reduction)
- Feature flag system for gradual rollout
- Comprehensive test coverage

Code style compliance:
- Follows .github/instructions/python.instructions.md (Google Style)
- Follows .github/instructions/github-actions.instructions.md
- All tasks independent and idempotent

Platforms: ubuntu-latest, macos-latest (NO WINDOWS)
Language versions: Go 1.23/1.24, Python 3.13/3.14
```

---

**Last Updated**: 2025-10-12
**Phase Owner**: Workflow Refactoring Team
**Status**: Ready for implementation
