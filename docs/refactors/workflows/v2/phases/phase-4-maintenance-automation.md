<!-- file: docs/refactors/workflows/v2/phases/phase-4-maintenance-automation.md -->
<!-- version: 1.0.0 -->
<!-- guid: f1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c -->

# Phase 4: Maintenance Automation

## Overview

This phase implements automated repository maintenance including dependency updates, stale issue management, security scanning, and performance monitoring. It provides tools to keep repositories healthy with minimal manual intervention.

## Goals

- Automate dependency updates with testing and validation
- Manage stale issues and pull requests with configurable policies
- Integrate security scanning for vulnerabilities and secrets
- Monitor workflow performance and resource usage
- Generate maintenance reports and notifications
- Support branch-specific maintenance policies

## Success Criteria

- [ ] `maintenance_workflow.py` helper module created
- [ ] Automated dependency update workflow operational
- [ ] Stale issue/PR management working
- [ ] Security scanning integrated (CodeQL, Dependabot, secret scanning)
- [ ] Performance monitoring dashboard created
- [ ] Maintenance reports generated weekly
- [ ] Branch-specific maintenance policies supported
- [ ] All maintenance follows repository conventions
- [ ] No Windows-specific maintenance tasks

## Dependencies

- Phase 0: `workflow_common.py` for config and validation
- Phase 1: CI workflows for testing dependency updates
- Phase 2: Release workflows for dependency version management

---

## Task 4.1: Create maintenance_workflow.py Helper Module

**Status**: Not Started
**Dependencies**: Phase 0 (workflow_common.py)
**Estimated Time**: 4 hours
**Idempotent**: Yes

### Description

Create a Python helper module for automated repository maintenance tasks.

### Code Style Requirements

**MUST follow**:
- `.github/instructions/python.instructions.md` - Google Python Style Guide
- `.github/instructions/general-coding.instructions.md` - File headers, versioning

### Implementation

Create file: `.github/workflows/scripts/maintenance_workflow.py`

```python
#!/usr/bin/env python3
# file: .github/workflows/scripts/maintenance_workflow.py
# version: 1.0.0
# guid: a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d

"""Maintenance workflow helper for automated repository maintenance.

This module provides utilities for dependency management, stale issue handling,
security scanning, and performance monitoring.

Features:
    - Dependency update detection and management
    - Stale issue and PR identification
    - Security vulnerability scanning
    - Performance metrics collection
    - Maintenance report generation
    - Branch-specific maintenance policies

Usage:
    # Check for dependency updates
    python maintenance_workflow.py check-dependencies --language go

    # Find stale issues
    python maintenance_workflow.py find-stale --days 90

    # Generate maintenance report
    python maintenance_workflow.py report --output report.md

Example:
    from maintenance_workflow import check_dependencies, find_stale_issues

    # Check for Go dependency updates
    updates = check_dependencies("go")

    # Find issues stale for 90+ days
    stale = find_stale_issues(days=90)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import requests

# Ensure workflow_common is importable
sys.path.insert(0, str(Path(__file__).parent))
import workflow_common


@dataclass
class DependencyUpdate:
    """Information about a dependency update.

    Attributes:
        name: Dependency name.
        current_version: Currently installed version.
        latest_version: Latest available version.
        update_type: Type of update (patch/minor/major).
        breaking: Whether update contains breaking changes.
        security: Whether update fixes security issues.
        language: Programming language (go/rust/python/node).
    """

    name: str
    current_version: str
    latest_version: str
    update_type: str  # patch, minor, major
    breaking: bool
    security: bool
    language: str


@dataclass
class StaleItem:
    """Information about a stale issue or pull request.

    Attributes:
        number: Issue/PR number.
        title: Issue/PR title.
        type: Item type ('issue' or 'pull_request').
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
        days_stale: Days since last update.
        labels: List of labels.
        assignees: List of assignees.
    """

    number: int
    title: str
    type: str
    created_at: datetime
    updated_at: datetime
    days_stale: int
    labels: list[str]
    assignees: list[str]


@dataclass
class SecurityIssue:
    """Information about a security issue.

    Attributes:
        severity: Severity level (critical/high/medium/low).
        package: Affected package name.
        vulnerability: Vulnerability identifier (CVE, GHSA, etc.).
        description: Issue description.
        fixed_version: Version that fixes the issue.
        advisory_url: URL to security advisory.
    """

    severity: str
    package: str
    vulnerability: str
    description: str
    fixed_version: str
    advisory_url: str


def check_dependencies(language: str) -> list[DependencyUpdate]:
    """Check for available dependency updates.

    Detects outdated dependencies and categorizes updates by type
    (patch/minor/major) following semantic versioning.

    Args:
        language: Programming language to check (go/rust/python/node).

    Returns:
        List of available dependency updates.

    Raises:
        WorkflowError: If dependency check fails or language unsupported.

    Example:
        >>> updates = check_dependencies("go")
        >>> for update in updates:
        ...     print(f"{update.name}: {update.current_version} -> {update.latest_version}")
        github.com/stretchr/testify: v1.8.0 -> v1.9.0
    """
    workflow_common.log_info(f"Checking {language} dependencies for updates")

    if language == "go":
        return _check_go_dependencies()
    elif language == "rust":
        return _check_rust_dependencies()
    elif language == "python":
        return _check_python_dependencies()
    elif language == "node":
        return _check_node_dependencies()
    else:
        raise workflow_common.WorkflowError(f"Unsupported language: {language}")


def _check_go_dependencies() -> list[DependencyUpdate]:
    """Check Go module dependencies for updates.

    Returns:
        List of available Go dependency updates.
    """
    updates = []

    try:
        # Run go list to get all dependencies
        result = subprocess.run(
            ["go", "list", "-m", "-u", "-json", "all"],
            capture_output=True,
            text=True,
            check=True,
        )

        # Parse JSON output (one object per line)
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue

            try:
                dep = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Skip if no update available
            if "Update" not in dep:
                continue

            current = dep.get("Version", "")
            latest = dep["Update"].get("Version", "")

            if not current or not latest:
                continue

            # Determine update type
            update_type = _get_update_type(current, latest)

            updates.append(
                DependencyUpdate(
                    name=dep["Path"],
                    current_version=current,
                    latest_version=latest,
                    update_type=update_type,
                    breaking=update_type == "major",
                    security=False,  # Will be enriched by security check
                    language="go",
                )
            )

    except subprocess.CalledProcessError as e:
        raise workflow_common.WorkflowError(f"Failed to check Go dependencies: {e}") from e

    return updates


def _check_rust_dependencies() -> list[DependencyUpdate]:
    """Check Rust crate dependencies for updates.

    Returns:
        List of available Rust dependency updates.
    """
    updates = []

    try:
        # Run cargo outdated
        result = subprocess.run(
            ["cargo", "outdated", "--format", "json"],
            capture_output=True,
            text=True,
            check=True,
        )

        data = json.loads(result.stdout)

        for dep in data.get("dependencies", []):
            current = dep.get("project", "")
            latest = dep.get("latest", "")

            if not current or not latest or current == latest:
                continue

            update_type = _get_update_type(current, latest)

            updates.append(
                DependencyUpdate(
                    name=dep["name"],
                    current_version=current,
                    latest_version=latest,
                    update_type=update_type,
                    breaking=update_type == "major",
                    security=False,
                    language="rust",
                )
            )

    except subprocess.CalledProcessError as e:
        workflow_common.log_warning(f"cargo outdated not available: {e}")
    except (json.JSONDecodeError, KeyError) as e:
        workflow_common.log_warning(f"Failed to parse cargo outdated output: {e}")

    return updates


def _check_python_dependencies() -> list[DependencyUpdate]:
    """Check Python package dependencies for updates.

    Returns:
        List of available Python dependency updates.
    """
    updates = []

    try:
        # Run pip list --outdated
        result = subprocess.run(
            ["pip", "list", "--outdated", "--format", "json"],
            capture_output=True,
            text=True,
            check=True,
        )

        data = json.loads(result.stdout)

        for dep in data:
            current = dep.get("version", "")
            latest = dep.get("latest_version", "")

            if not current or not latest:
                continue

            update_type = _get_update_type(current, latest)

            updates.append(
                DependencyUpdate(
                    name=dep["name"],
                    current_version=current,
                    latest_version=latest,
                    update_type=update_type,
                    breaking=update_type == "major",
                    security=False,
                    language="python",
                )
            )

    except subprocess.CalledProcessError as e:
        workflow_common.log_warning(f"pip list failed: {e}")
    except (json.JSONDecodeError, KeyError) as e:
        workflow_common.log_warning(f"Failed to parse pip output: {e}")

    return updates


def _check_node_dependencies() -> list[DependencyUpdate]:
    """Check Node.js package dependencies for updates.

    Returns:
        List of available Node.js dependency updates.
    """
    updates = []

    try:
        # Run npm outdated
        result = subprocess.run(
            ["npm", "outdated", "--json"],
            capture_output=True,
            text=True,
        )

        # npm outdated returns exit code 1 if there are updates
        if result.returncode not in (0, 1):
            raise workflow_common.WorkflowError(
                f"npm outdated failed: {result.stderr}"
            )

        if not result.stdout.strip():
            return updates

        data = json.loads(result.stdout)

        for name, info in data.items():
            current = info.get("current", "")
            latest = info.get("latest", "")

            if not current or not latest:
                continue

            update_type = _get_update_type(current, latest)

            updates.append(
                DependencyUpdate(
                    name=name,
                    current_version=current,
                    latest_version=latest,
                    update_type=update_type,
                    breaking=update_type == "major",
                    security=False,
                    language="node",
                )
            )

    except (json.JSONDecodeError, KeyError) as e:
        workflow_common.log_warning(f"Failed to parse npm outdated output: {e}")

    return updates


def _get_update_type(current: str, latest: str) -> str:
    """Determine update type from version strings.

    Args:
        current: Current version string.
        latest: Latest version string.

    Returns:
        Update type: 'major', 'minor', or 'patch'.
    """
    # Remove common prefixes
    current = current.lstrip("v")
    latest = latest.lstrip("v")

    try:
        current_parts = [int(x) for x in current.split(".")[:3]]
        latest_parts = [int(x) for x in latest.split(".")[:3]]

        # Pad to 3 parts
        while len(current_parts) < 3:
            current_parts.append(0)
        while len(latest_parts) < 3:
            latest_parts.append(0)

        if latest_parts[0] > current_parts[0]:
            return "major"
        elif latest_parts[1] > current_parts[1]:
            return "minor"
        else:
            return "patch"

    except (ValueError, IndexError):
        # If version parsing fails, assume patch
        return "patch"


def find_stale_issues(
    days: int = 90, include_prs: bool = True
) -> list[StaleItem]:
    """Find stale issues and pull requests.

    Args:
        days: Number of days of inactivity to consider stale.
        include_prs: Whether to include pull requests.

    Returns:
        List of stale items.

    Raises:
        WorkflowError: If GitHub API request fails.

    Example:
        >>> stale = find_stale_issues(days=90, include_prs=True)
        >>> print(f"Found {len(stale)} stale items")
        Found 15 stale items
    """
    workflow_common.log_info(f"Finding items stale for {days}+ days")

    # Get GitHub token
    token = workflow_common.get_env_var("GITHUB_TOKEN")
    repo = workflow_common.get_env_var("GITHUB_REPOSITORY")

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    cutoff_date = datetime.now() - timedelta(days=days)
    stale_items = []

    # Search for stale issues
    stale_items.extend(
        _search_stale_items("issue", repo, cutoff_date, headers)
    )

    # Search for stale PRs if requested
    if include_prs:
        stale_items.extend(
            _search_stale_items("pr", repo, cutoff_date, headers)
        )

    return stale_items


def _search_stale_items(
    item_type: str,
    repo: str,
    cutoff_date: datetime,
    headers: dict[str, str],
) -> list[StaleItem]:
    """Search for stale items via GitHub API.

    Args:
        item_type: Type of item to search ('issue' or 'pr').
        repo: Repository in format 'owner/repo'.
        cutoff_date: Cutoff date for staleness.
        headers: HTTP headers with authentication.

    Returns:
        List of stale items.
    """
    stale_items = []

    try:
        # Search for open items updated before cutoff date
        query = f"repo:{repo} is:{item_type} is:open updated:<{cutoff_date.strftime('%Y-%m-%d')}"

        url = f"https://api.github.com/search/issues?q={query}&per_page=100"
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()

        for item in data.get("items", []):
            created_at = datetime.fromisoformat(item["created_at"].rstrip("Z"))
            updated_at = datetime.fromisoformat(item["updated_at"].rstrip("Z"))
            days_stale = (datetime.now() - updated_at).days

            stale_items.append(
                StaleItem(
                    number=item["number"],
                    title=item["title"],
                    type="pull_request" if "pull_request" in item else "issue",
                    created_at=created_at,
                    updated_at=updated_at,
                    days_stale=days_stale,
                    labels=[label["name"] for label in item.get("labels", [])],
                    assignees=[
                        assignee["login"]
                        for assignee in item.get("assignees", [])
                    ],
                )
            )

    except requests.RequestException as e:
        workflow_common.log_warning(f"Failed to search for stale {item_type}s: {e}")

    return stale_items


def check_security_issues() -> list[SecurityIssue]:
    """Check for security vulnerabilities in dependencies.

    Queries GitHub's Dependabot alerts API for known vulnerabilities.

    Returns:
        List of security issues.

    Raises:
        WorkflowError: If security check fails.

    Example:
        >>> issues = check_security_issues()
        >>> critical = [i for i in issues if i.severity == "critical"]
        >>> print(f"Found {len(critical)} critical security issues")
        Found 2 critical security issues
    """
    workflow_common.log_info("Checking for security vulnerabilities")

    token = workflow_common.get_env_var("GITHUB_TOKEN")
    repo = workflow_common.get_env_var("GITHUB_REPOSITORY")

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    security_issues = []

    try:
        url = f"https://api.github.com/repos/{repo}/dependabot/alerts?state=open"
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        alerts = response.json()

        for alert in alerts:
            security = alert.get("security_advisory", {})
            vulnerability = alert.get("security_vulnerability", {})

            security_issues.append(
                SecurityIssue(
                    severity=security.get("severity", "unknown"),
                    package=vulnerability.get("package", {}).get("name", "unknown"),
                    vulnerability=security.get("ghsa_id", "unknown"),
                    description=security.get("summary", ""),
                    fixed_version=vulnerability.get("first_patched_version", {}).get(
                        "identifier", "unknown"
                    ),
                    advisory_url=security.get("html_url", ""),
                )
            )

    except requests.RequestException as e:
        workflow_common.log_warning(f"Failed to check security issues: {e}")

    return security_issues


def generate_maintenance_report(
    output_file: str | Path,
    dependencies: list[DependencyUpdate],
    stale_items: list[StaleItem],
    security_issues: list[SecurityIssue],
) -> None:
    """Generate comprehensive maintenance report.

    Args:
        output_file: Path to output markdown file.
        dependencies: List of dependency updates.
        stale_items: List of stale issues/PRs.
        security_issues: List of security issues.

    Example:
        >>> generate_maintenance_report(
        ...     "report.md",
        ...     dependencies,
        ...     stale_items,
        ...     security_issues
        ... )
    """
    output_path = Path(output_file)

    lines = []

    # Header
    lines.append("# Repository Maintenance Report")
    lines.append("")
    lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Dependency Updates**: {len(dependencies)}")
    lines.append(f"- **Stale Items**: {len(stale_items)}")
    lines.append(f"- **Security Issues**: {len(security_issues)}")
    lines.append("")

    # Dependency Updates
    if dependencies:
        lines.append("## Dependency Updates")
        lines.append("")

        # Group by update type
        by_type: dict[str, list[DependencyUpdate]] = {
            "major": [],
            "minor": [],
            "patch": [],
        }
        for dep in dependencies:
            by_type[dep.update_type].append(dep)

        for update_type in ["major", "minor", "patch"]:
            deps = by_type[update_type]
            if not deps:
                continue

            lines.append(f"### {update_type.title()} Updates ({len(deps)})")
            lines.append("")
            lines.append("| Package | Current | Latest | Language |")
            lines.append("|---------|---------|--------|----------|")

            for dep in deps:
                lines.append(
                    f"| `{dep.name}` | {dep.current_version} | {dep.latest_version} | {dep.language} |"
                )

            lines.append("")

    # Stale Items
    if stale_items:
        lines.append("## Stale Items")
        lines.append("")
        lines.append("| Number | Type | Title | Days Stale | Labels |")
        lines.append("|--------|------|-------|------------|--------|")

        for item in sorted(stale_items, key=lambda x: x.days_stale, reverse=True):
            labels = ", ".join(item.labels) if item.labels else "-"
            lines.append(
                f"| #{item.number} | {item.type} | {item.title} | {item.days_stale} | {labels} |"
            )

        lines.append("")

    # Security Issues
    if security_issues:
        lines.append("## Security Issues")
        lines.append("")
        lines.append("| Severity | Package | Vulnerability | Fixed Version |")
        lines.append("|----------|---------|---------------|---------------|")

        for issue in sorted(
            security_issues,
            key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(
                x.severity, 99
            ),
        ):
            lines.append(
                f"| {issue.severity.upper()} | `{issue.package}` | [{issue.vulnerability}]({issue.advisory_url}) | {issue.fixed_version} |"
            )

        lines.append("")

    # Write report
    output_path.write_text("\n".join(lines), encoding="utf-8")
    workflow_common.log_info(f"Maintenance report written to {output_path}")


def main() -> None:
    """Main entry point for maintenance CLI."""
    parser = argparse.ArgumentParser(
        description="Repository maintenance automation"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Check dependencies command
    deps_parser = subparsers.add_parser(
        "check-dependencies", help="Check for dependency updates"
    )
    deps_parser.add_argument(
        "--language",
        choices=["go", "rust", "python", "node"],
        required=True,
        help="Programming language to check",
    )

    # Find stale command
    stale_parser = subparsers.add_parser(
        "find-stale", help="Find stale issues and PRs"
    )
    stale_parser.add_argument(
        "--days", type=int, default=90, help="Days of inactivity to consider stale"
    )
    stale_parser.add_argument(
        "--no-prs", action="store_true", help="Exclude pull requests"
    )

    # Check security command
    subparsers.add_parser(
        "check-security", help="Check for security vulnerabilities"
    )

    # Generate report command
    report_parser = subparsers.add_parser(
        "report", help="Generate maintenance report"
    )
    report_parser.add_argument(
        "--output", default="maintenance-report.md", help="Output file path"
    )

    args = parser.parse_args()

    try:
        if args.command == "check-dependencies":
            updates = check_dependencies(args.language)
            workflow_common.log_info(f"Found {len(updates)} dependency updates")
            workflow_common.set_output(
                "updates",
                json.dumps([
                    {
                        "name": u.name,
                        "current": u.current_version,
                        "latest": u.latest_version,
                        "type": u.update_type,
                    }
                    for u in updates
                ]),
            )

        elif args.command == "find-stale":
            stale = find_stale_issues(args.days, not args.no_prs)
            workflow_common.log_info(f"Found {len(stale)} stale items")
            workflow_common.set_output(
                "stale_count", str(len(stale))
            )

        elif args.command == "check-security":
            issues = check_security_issues()
            workflow_common.log_info(f"Found {len(issues)} security issues")
            workflow_common.set_output(
                "security_count", str(len(issues))
            )

        elif args.command == "report":
            # Run all checks
            deps = []
            stale = []
            security = []

            try:
                deps = check_dependencies("go")
            except workflow_common.WorkflowError:
                pass

            try:
                stale = find_stale_issues()
            except workflow_common.WorkflowError:
                pass

            try:
                security = check_security_issues()
            except workflow_common.WorkflowError:
                pass

            generate_maintenance_report(args.output, deps, stale, security)

        sys.exit(0)

    except workflow_common.WorkflowError as e:
        workflow_common.log_error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
```

### Verification Steps

```bash
# 1. Verify script file exists
test -f .github/workflows/scripts/maintenance_workflow.py && echo "✅ Script created"

# 2. Check Python syntax
python3 -m py_compile .github/workflows/scripts/maintenance_workflow.py && echo "✅ Valid Python"

# 3. Make executable
chmod +x .github/workflows/scripts/maintenance_workflow.py && echo "✅ Executable"

# 4. Test dependency check
python3 .github/workflows/scripts/maintenance_workflow.py check-dependencies \
  --language go && echo "✅ Dependency check working"

# 5. Test report generation
python3 .github/workflows/scripts/maintenance_workflow.py report \
  --output /tmp/maintenance-report.md && echo "✅ Report generated"
```

---

## Task 4.2: Create test_maintenance_workflow.py Unit Tests

**Status**: Not Started
**Dependencies**: Task 4.1 (maintenance_workflow.py)
**Estimated Time**: 2 hours
**Idempotent**: Yes

### Description

Create comprehensive unit tests for maintenance_workflow.py.

### Implementation

Create file: `.github/workflows/scripts/tests/test_maintenance_workflow.py`

```python
#!/usr/bin/env python3
# file: .github/workflows/scripts/tests/test_maintenance_workflow.py
# version: 1.0.0
# guid: b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e

"""Unit tests for maintenance_workflow module."""

import json
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
import maintenance_workflow


class TestDependencyChecks(unittest.TestCase):
    """Test dependency checking functionality."""

    @patch("subprocess.run")
    def test_check_go_dependencies(self, mock_run):
        """Test Go dependency checking."""
        # Arrange
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"Path":"github.com/stretchr/testify","Version":"v1.8.0","Update":{"Version":"v1.9.0"}}\n',
        )

        # Act
        updates = maintenance_workflow._check_go_dependencies()

        # Assert
        self.assertEqual(len(updates), 1)
        self.assertEqual(updates[0].name, "github.com/stretchr/testify")
        self.assertEqual(updates[0].current_version, "v1.8.0")
        self.assertEqual(updates[0].latest_version, "v1.9.0")
        self.assertEqual(updates[0].language, "go")

    @patch("subprocess.run")
    def test_check_rust_dependencies(self, mock_run):
        """Test Rust dependency checking."""
        # Arrange
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                "dependencies": [
                    {
                        "name": "serde",
                        "project": "1.0.0",
                        "latest": "1.1.0",
                    }
                ]
            }),
        )

        # Act
        updates = maintenance_workflow._check_rust_dependencies()

        # Assert
        self.assertEqual(len(updates), 1)
        self.assertEqual(updates[0].name, "serde")
        self.assertEqual(updates[0].current_version, "1.0.0")
        self.assertEqual(updates[0].latest_version, "1.1.0")
        self.assertEqual(updates[0].update_type, "minor")

    @patch("subprocess.run")
    def test_check_python_dependencies(self, mock_run):
        """Test Python dependency checking."""
        # Arrange
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps([
                {
                    "name": "requests",
                    "version": "2.28.0",
                    "latest_version": "2.28.1",
                }
            ]),
        )

        # Act
        updates = maintenance_workflow._check_python_dependencies()

        # Assert
        self.assertEqual(len(updates), 1)
        self.assertEqual(updates[0].name, "requests")
        self.assertEqual(updates[0].update_type, "patch")

    def test_get_update_type_major(self):
        """Test major version update detection."""
        result = maintenance_workflow._get_update_type("v1.0.0", "v2.0.0")
        self.assertEqual(result, "major")

    def test_get_update_type_minor(self):
        """Test minor version update detection."""
        result = maintenance_workflow._get_update_type("v1.0.0", "v1.1.0")
        self.assertEqual(result, "minor")

    def test_get_update_type_patch(self):
        """Test patch version update detection."""
        result = maintenance_workflow._get_update_type("v1.0.0", "v1.0.1")
        self.assertEqual(result, "patch")


class TestStaleDetection(unittest.TestCase):
    """Test stale issue/PR detection."""

    @patch("requests.get")
    @patch.dict("os.environ", {"GITHUB_TOKEN": "test-token", "GITHUB_REPOSITORY": "owner/repo"})
    def test_find_stale_issues(self, mock_get):
        """Test finding stale issues."""
        # Arrange
        cutoff = datetime.now() - timedelta(days=90)
        created = (datetime.now() - timedelta(days=100)).isoformat() + "Z"
        updated = cutoff.isoformat() + "Z"

        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "items": [
                    {
                        "number": 123,
                        "title": "Old issue",
                        "created_at": created,
                        "updated_at": updated,
                        "labels": [{"name": "bug"}],
                        "assignees": [],
                    }
                ]
            },
        )

        # Act
        stale = maintenance_workflow.find_stale_issues(days=90, include_prs=False)

        # Assert
        self.assertEqual(len(stale), 1)
        self.assertEqual(stale[0].number, 123)
        self.assertEqual(stale[0].type, "issue")
        self.assertGreaterEqual(stale[0].days_stale, 0)

    @patch("requests.get")
    @patch.dict("os.environ", {"GITHUB_TOKEN": "test-token", "GITHUB_REPOSITORY": "owner/repo"})
    def test_find_stale_with_prs(self, mock_get):
        """Test finding stale items including PRs."""
        # Arrange
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"items": []},
        )

        # Act
        stale = maintenance_workflow.find_stale_issues(days=90, include_prs=True)

        # Assert
        # Should call API twice (once for issues, once for PRs)
        self.assertEqual(mock_get.call_count, 2)


class TestSecurityChecks(unittest.TestCase):
    """Test security vulnerability checking."""

    @patch("requests.get")
    @patch.dict("os.environ", {"GITHUB_TOKEN": "test-token", "GITHUB_REPOSITORY": "owner/repo"})
    def test_check_security_issues(self, mock_get):
        """Test checking for security issues."""
        # Arrange
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [
                {
                    "security_advisory": {
                        "severity": "high",
                        "ghsa_id": "GHSA-xxxx-yyyy-zzzz",
                        "summary": "Test vulnerability",
                        "html_url": "https://github.com/advisories/GHSA-xxxx-yyyy-zzzz",
                    },
                    "security_vulnerability": {
                        "package": {"name": "example-package"},
                        "first_patched_version": {"identifier": "1.2.3"},
                    },
                }
            ],
        )

        # Act
        issues = maintenance_workflow.check_security_issues()

        # Assert
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].severity, "high")
        self.assertEqual(issues[0].package, "example-package")
        self.assertEqual(issues[0].fixed_version, "1.2.3")


class TestReportGeneration(unittest.TestCase):
    """Test maintenance report generation."""

    def test_generate_report(self):
        """Test generating complete maintenance report."""
        # Arrange
        output_file = Path("/tmp/test-report.md")

        dependencies = [
            maintenance_workflow.DependencyUpdate(
                name="test-package",
                current_version="1.0.0",
                latest_version="2.0.0",
                update_type="major",
                breaking=True,
                security=False,
                language="go",
            )
        ]

        stale_items = [
            maintenance_workflow.StaleItem(
                number=123,
                title="Old issue",
                type="issue",
                created_at=datetime.now() - timedelta(days=100),
                updated_at=datetime.now() - timedelta(days=90),
                days_stale=90,
                labels=["bug"],
                assignees=[],
            )
        ]

        security_issues = [
            maintenance_workflow.SecurityIssue(
                severity="high",
                package="vuln-package",
                vulnerability="CVE-2023-12345",
                description="Test vulnerability",
                fixed_version="1.2.3",
                advisory_url="https://example.com/advisory",
            )
        ]

        # Act
        maintenance_workflow.generate_maintenance_report(
            output_file, dependencies, stale_items, security_issues
        )

        # Assert
        self.assertTrue(output_file.exists())
        content = output_file.read_text()
        self.assertIn("# Repository Maintenance Report", content)
        self.assertIn("test-package", content)
        self.assertIn("Old issue", content)
        self.assertIn("vuln-package", content)

        # Cleanup
        output_file.unlink()


if __name__ == "__main__":
    unittest.main()
```

### Verification Steps

```bash
# 1. Run all tests
python3 -m pytest .github/workflows/scripts/tests/test_maintenance_workflow.py -v

# 2. Check test coverage
python3 -m pytest .github/workflows/scripts/tests/test_maintenance_workflow.py \
  --cov=maintenance_workflow --cov-report=term-missing

# 3. Verify specific test categories
python3 -m pytest .github/workflows/scripts/tests/test_maintenance_workflow.py::TestDependencyChecks -v
python3 -m pytest .github/workflows/scripts/tests/test_maintenance_workflow.py::TestStaleDetection -v
python3 -m pytest .github/workflows/scripts/tests/test_maintenance_workflow.py::TestSecurityChecks -v
```

---

## Task 4.3: Create reusable-maintenance.yml Workflow

**Status**: Not Started
**Dependencies**: Tasks 4.1-4.2
**Estimated Time**: 3 hours
**Idempotent**: Yes

### Description

Create reusable workflow for automated maintenance tasks.

### Implementation

Create file: `.github/workflows/reusable-maintenance.yml`

```yaml
# file: .github/workflows/reusable-maintenance.yml
# version: 1.0.0
# guid: c3d4e5f6-a7b8-9c0d-1e2f-3a4b5c6d7e8f

name: Reusable Maintenance

on:
  workflow_call:
    inputs:
      maintenance-type:
        description: 'Type of maintenance to run'
        required: true
        type: string
        # Options: dependency-updates, stale-cleanup, security-scan, all
      language:
        description: 'Programming language for dependency checks'
        required: false
        type: string
        default: 'go'
      stale-days:
        description: 'Days of inactivity to consider stale'
        required: false
        type: number
        default: 90
      create-issues:
        description: 'Create GitHub issues for findings'
        required: false
        type: boolean
        default: false
    outputs:
      dependency-count:
        description: 'Number of dependency updates found'
        value: ${{ jobs.dependency-updates.outputs.update-count }}
      stale-count:
        description: 'Number of stale items found'
        value: ${{ jobs.stale-cleanup.outputs.stale-count }}
      security-count:
        description: 'Number of security issues found'
        value: ${{ jobs.security-scan.outputs.security-count }}

permissions:
  contents: read
  issues: write
  pull-requests: write
  security-events: write

jobs:
  dependency-updates:
    name: Check Dependency Updates
    runs-on: ubuntu-latest
    if: inputs.maintenance-type == 'dependency-updates' || inputs.maintenance-type == 'all'
    outputs:
      update-count: ${{ steps.check-deps.outputs.update-count }}
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install requests pyyaml

      - name: Set up language environment
        run: |
          case "${{ inputs.language }}" in
            go)
              # Install Go
              sudo apt-get update
              sudo apt-get install -y golang-1.25
              echo "/usr/lib/go-1.25/bin" >> $GITHUB_PATH
              ;;
            rust)
              # Install Rust
              curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
              echo "$HOME/.cargo/bin" >> $GITHUB_PATH
              cargo install cargo-outdated
              ;;
            python)
              # Python already installed
              ;;
            node)
              # Install Node.js
              curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
              sudo apt-get install -y nodejs
              ;;
          esac

      - name: Check for dependency updates
        id: check-deps
        run: |
          python .github/workflows/scripts/maintenance_workflow.py \
            check-dependencies --language ${{ inputs.language }}

          # Parse output for count
          UPDATE_COUNT=$(echo "$GITHUB_OUTPUT" | grep -oP 'updates=\K[0-9]+' || echo "0")
          echo "update-count=$UPDATE_COUNT" >> $GITHUB_OUTPUT

      - name: Create dependency update issues
        if: inputs.create-issues && steps.check-deps.outputs.update-count > 0
        uses: actions/github-script@v7
        with:
          script: |
            const updates = JSON.parse(process.env.UPDATES);

            for (const update of updates) {
              const title = `Update ${update.name} to ${update.latest}`;
              const body = `
            ## Dependency Update Available

            - **Package**: \`${update.name}\`
            - **Current Version**: ${update.current}
            - **Latest Version**: ${update.latest}
            - **Update Type**: ${update.type}
            - **Language**: ${{ inputs.language }}

            ### Actions Required

            1. Review changelog for breaking changes
            2. Update dependency in configuration file
            3. Run tests to verify compatibility
            4. Update documentation if needed

            ---
            *Auto-generated by maintenance workflow*
              `;

              await github.rest.issues.create({
                owner: context.repo.owner,
                repo: context.repo.repo,
                title: title,
                body: body,
                labels: ['dependencies', 'maintenance', update.type + '-update']
              });
            }
        env:
          UPDATES: ${{ steps.check-deps.outputs.updates }}

  stale-cleanup:
    name: Manage Stale Items
    runs-on: ubuntu-latest
    if: inputs.maintenance-type == 'stale-cleanup' || inputs.maintenance-type == 'all'
    outputs:
      stale-count: ${{ steps.find-stale.outputs.stale-count }}
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install requests pyyaml

      - name: Find stale items
        id: find-stale
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python .github/workflows/scripts/maintenance_workflow.py \
            find-stale --days ${{ inputs.stale-days }}

      - name: Label stale items
        if: steps.find-stale.outputs.stale-count > 0
        uses: actions/github-script@v7
        with:
          script: |
            // Label stale issues/PRs (actual implementation would parse output)
            console.log('Found ' + process.env.STALE_COUNT + ' stale items');
        env:
          STALE_COUNT: ${{ steps.find-stale.outputs.stale-count }}

  security-scan:
    name: Security Vulnerability Scan
    runs-on: ubuntu-latest
    if: inputs.maintenance-type == 'security-scan' || inputs.maintenance-type == 'all'
    outputs:
      security-count: ${{ steps.check-security.outputs.security-count }}
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install requests pyyaml

      - name: Check security issues
        id: check-security
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python .github/workflows/scripts/maintenance_workflow.py check-security

      - name: Create security alerts
        if: inputs.create-issues && steps.check-security.outputs.security-count > 0
        uses: actions/github-script@v7
        with:
          script: |
            console.log('Found ' + process.env.SECURITY_COUNT + ' security issues');
            // Would create issues for critical/high severity findings
        env:
          SECURITY_COUNT: ${{ steps.check-security.outputs.security-count }}

  generate-report:
    name: Generate Maintenance Report
    runs-on: ubuntu-latest
    needs: [dependency-updates, stale-cleanup, security-scan]
    if: always()
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install requests pyyaml

      - name: Generate report
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python .github/workflows/scripts/maintenance_workflow.py report \
            --output maintenance-report.md

      - name: Upload report
        uses: actions/upload-artifact@v4
        with:
          name: maintenance-report
          path: maintenance-report.md
          retention-days: 90

      - name: Post summary
        run: |
          echo "## Maintenance Summary" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          cat maintenance-report.md >> $GITHUB_STEP_SUMMARY
```

### Verification Steps

```bash
# 1. Validate workflow syntax
actionlint .github/workflows/reusable-maintenance.yml

# 2. Test dependency updates job
gh workflow run reusable-maintenance.yml \
  -f maintenance-type=dependency-updates \
  -f language=go

# 3. Test stale cleanup job
gh workflow run reusable-maintenance.yml \
  -f maintenance-type=stale-cleanup \
  -f stale-days=90

# 4. Test security scan job
gh workflow run reusable-maintenance.yml \
  -f maintenance-type=security-scan

# 5. Test full maintenance run
gh workflow run reusable-maintenance.yml \
  -f maintenance-type=all \
  -f create-issues=true
```

---

## Task 4.4: Create maintenance.yml Caller Workflow

**Status**: Not Started
**Dependencies**: Task 4.3
**Estimated Time**: 1 hour
**Idempotent**: Yes

### Description

Create caller workflow with scheduled and manual triggers.

### Implementation

Create file: `.github/workflows/maintenance.yml`

```yaml
# file: .github/workflows/maintenance.yml
# version: 1.0.0
# guid: d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a

name: Repository Maintenance

on:
  schedule:
    # Weekly dependency checks (Monday 00:00 UTC)
    - cron: '0 0 * * 1'
    # Daily stale cleanup (00:00 UTC)
    - cron: '0 0 * * *'
  workflow_dispatch:
    inputs:
      maintenance-type:
        description: 'Type of maintenance to run'
        required: true
        type: choice
        options:
          - all
          - dependency-updates
          - stale-cleanup
          - security-scan
        default: 'all'
      create-issues:
        description: 'Create GitHub issues for findings'
        required: false
        type: boolean
        default: false

permissions:
  contents: read
  issues: write
  pull-requests: write
  security-events: write

jobs:
  check-feature-flag:
    name: Check Feature Flag
    runs-on: ubuntu-latest
    outputs:
      enabled: ${{ steps.check-config.outputs.enabled }}
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Check repository configuration
        id: check-config
        run: |
          if [ -f .github/repository-config.yml ]; then
            ENABLED=$(yq eval '.feature_flags.use_new_maintenance // false' \
              .github/repository-config.yml)
            echo "enabled=$ENABLED" >> $GITHUB_OUTPUT
          else
            echo "enabled=false" >> $GITHUB_OUTPUT
          fi

  new-maintenance:
    name: Run New Maintenance System
    needs: check-feature-flag
    if: needs.check-feature-flag.outputs.enabled == 'true'
    uses: ./.github/workflows/reusable-maintenance.yml
    with:
      maintenance-type: ${{ github.event.inputs.maintenance-type || 'all' }}
      language: 'go'
      stale-days: 90
      create-issues: ${{ github.event.inputs.create-issues == 'true' }}
    secrets: inherit

  legacy-maintenance:
    name: Legacy Maintenance (Placeholder)
    needs: check-feature-flag
    if: needs.check-feature-flag.outputs.enabled != 'true'
    runs-on: ubuntu-latest
    steps:
      - name: Skip - feature flag disabled
        run: |
          echo "⚠️ New maintenance system disabled"
          echo "Set feature_flags.use_new_maintenance=true to enable"
```

### Verification Steps

```bash
# 1. Validate workflow syntax
actionlint .github/workflows/maintenance.yml

# 2. Test manual dispatch
gh workflow run maintenance.yml \
  -f maintenance-type=all \
  -f create-issues=false

# 3. Verify scheduled runs (check workflow history)
gh run list --workflow=maintenance.yml --limit=5

# 4. Test with feature flag enabled
echo 'feature_flags:
  use_new_maintenance: true' > .github/repository-config.yml

gh workflow run maintenance.yml -f maintenance-type=all

# 5. Test with feature flag disabled
echo 'feature_flags:
  use_new_maintenance: false' > .github/repository-config.yml

gh workflow run maintenance.yml -f maintenance-type=all
```

---

## Task 4.5: Create Maintenance Configuration Documentation

**Status**: Not Started
**Dependencies**: Tasks 4.1-4.4
**Estimated Time**: 1 hour
**Idempotent**: Yes

### Description

Document maintenance configuration options and customization.

### Implementation

Create file: `docs/refactors/workflows/v2/maintenance-config.md`

```markdown
<!-- file: docs/refactors/workflows/v2/maintenance-config.md -->
<!-- version: 1.0.0 -->
<!-- guid: e5f6a7b8-c9d0-1e2f-3a4b-5c6d7e8f9a0b -->

# Maintenance Configuration Guide

## Overview

The v2 maintenance system provides automated repository maintenance including dependency updates, stale issue management, and security scanning.

## Feature Flag

Enable the new maintenance system in `.github/repository-config.yml`:

\`\`\`yaml
feature_flags:
  use_new_maintenance: true
\`\`\`

## Maintenance Types

### Dependency Updates

Automatically checks for outdated dependencies and creates update issues.

**Supported Languages**:
- Go (1.23, 1.24, 1.25)
- Rust (stable, stable-1)
- Python (3.13, 3.14)
- Node.js (20 LTS, 22 LTS)

**Configuration**:

\`\`\`yaml
maintenance:
  dependencies:
    schedule: '0 0 * * 1'  # Weekly, Monday 00:00 UTC
    auto_merge_patch: false
    auto_merge_minor: false
    exemptions:
      - package: 'critical-package'
        reason: 'Requires manual review'
\`\`\`

**Manual Trigger**:

\`\`\`bash
gh workflow run maintenance.yml \\
  -f maintenance-type=dependency-updates \\
  -f create-issues=true
\`\`\`

### Stale Issue Management

Identifies and labels inactive issues and pull requests.

**Configuration**:

\`\`\`yaml
maintenance:
  stale:
    schedule: '0 0 * * *'  # Daily, 00:00 UTC
    days_until_stale: 90
    days_until_close: 30
    exempt_labels:
      - 'security'
      - 'critical'
      - 'help-wanted'
    exempt_assignees: true
\`\`\`

**Manual Trigger**:

\`\`\`bash
gh workflow run maintenance.yml \\
  -f maintenance-type=stale-cleanup
\`\`\`

### Security Scanning

Checks for security vulnerabilities via Dependabot alerts.

**Configuration**:

\`\`\`yaml
maintenance:
  security:
    schedule: '0 */6 * * *'  # Every 6 hours
    auto_fix_patch: false
    severity_threshold: 'medium'
    alert_slack: true
    slack_webhook_secret: 'SLACK_WEBHOOK_URL'
\`\`\`

**Manual Trigger**:

\`\`\`bash
gh workflow run maintenance.yml \\
  -f maintenance-type=security-scan \\
  -f create-issues=true
\`\`\`

## Branch-Specific Policies

Different branches can have different maintenance policies:

\`\`\`yaml
branch_maintenance:
  main:
    dependencies:
      auto_merge_patch: true
      auto_merge_minor: false
    stale:
      days_until_stale: 60

  stable-1-go-1-24:
    dependencies:
      auto_merge_patch: false  # Conservative on stable branches
      auto_merge_minor: false
    stale:
      days_until_stale: 120  # Longer window for stable branches
\`\`\`

## Maintenance Reports

Weekly maintenance reports are generated and uploaded as artifacts.

**Report Contents**:
- Dependency update summary
- Stale issue statistics
- Security vulnerability status
- Recommended actions

**Accessing Reports**:

\`\`\`bash
# List recent maintenance runs
gh run list --workflow=maintenance.yml --limit=5

# Download latest report
gh run download <run-id> --name maintenance-report
\`\`\`

## Exemptions

### Dependency Exemptions

Prevent automatic updates for specific packages:

\`\`\`yaml
maintenance:
  dependencies:
    exemptions:
      - package: 'legacy-library'
        reason: 'Version pinned for compatibility'
        until: '2025-12-31'
\`\`\`

### Stale Exemptions

Prevent issues/PRs from being marked stale:

**Via Labels**:
Add exempt labels in configuration:

\`\`\`yaml
maintenance:
  stale:
    exempt_labels:
      - 'long-term'
      - 'blocked'
\`\`\`

**Via Comments**:
Add comment to issue/PR:

\`\`\`
/no-stale
\`\`\`

## Notifications

### Slack Notifications

Configure Slack webhook for maintenance alerts:

\`\`\`yaml
maintenance:
  notifications:
    slack:
      enabled: true
      webhook_secret: 'SLACK_WEBHOOK_URL'
      channels:
        security: '#security-alerts'
        dependencies: '#dependency-updates'
\`\`\`

### Email Notifications

Configure email for critical issues:

\`\`\`yaml
maintenance:
  notifications:
    email:
      enabled: true
      recipients:
        - 'team@example.com'
      severity_threshold: 'high'
\`\`\`

## Troubleshooting

### Dependency Checks Failing

**Problem**: Dependency checks return no results or fail.

**Solutions**:
1. Verify language-specific tools are installed (go, cargo, pip, npm)
2. Check that dependency files exist (go.mod, Cargo.toml, etc.)
3. Review workflow logs for specific errors
4. Test locally: `python .github/workflows/scripts/maintenance_workflow.py check-dependencies --language go`

### Stale Detection Not Working

**Problem**: Stale items not being identified.

**Solutions**:
1. Verify GITHUB_TOKEN has necessary permissions
2. Check stale days threshold configuration
3. Verify exempt labels are correctly configured
4. Test locally: `python .github/workflows/scripts/maintenance_workflow.py find-stale --days 90`

### Security Scan Incomplete

**Problem**: Security scan misses known vulnerabilities.

**Solutions**:
1. Ensure Dependabot is enabled in repository settings
2. Verify GITHUB_TOKEN has security-events:write permission
3. Check that alerts are not suppressed
4. Review GitHub Security tab for manual alerts

## Best Practices

1. **Start Conservative**: Begin with manual issue creation, then gradually enable auto-merge
2. **Monitor Reports**: Review weekly maintenance reports before enabling automation
3. **Test Locally**: Use CLI commands to test maintenance scripts before deploying
4. **Branch Policies**: Use stricter policies on stable branches
5. **Exemption Documentation**: Always document reasons for exemptions
6. **Regular Reviews**: Review maintenance configuration quarterly

## Examples

### Basic Setup

Minimal configuration for Go project:

\`\`\`yaml
# .github/repository-config.yml
feature_flags:
  use_new_maintenance: true

maintenance:
  dependencies:
    schedule: '0 0 * * 1'
  stale:
    schedule: '0 0 * * *'
    days_until_stale: 90
  security:
    schedule: '0 */6 * * *'
\`\`\`

### Advanced Setup

Full configuration with branch policies and notifications:

\`\`\`yaml
# .github/repository-config.yml
feature_flags:
  use_new_maintenance: true

maintenance:
  dependencies:
    schedule: '0 0 * * 1'
    auto_merge_patch: true
    exemptions:
      - package: 'critical-lib'
        reason: 'Requires manual review'

  stale:
    schedule: '0 0 * * *'
    days_until_stale: 90
    days_until_close: 30
    exempt_labels:
      - 'security'
      - 'blocked'

  security:
    schedule: '0 */6 * * *'
    auto_fix_patch: false
    severity_threshold: 'medium'
    alert_slack: true

  notifications:
    slack:
      enabled: true
      webhook_secret: 'SLACK_WEBHOOK_URL'

branch_maintenance:
  main:
    dependencies:
      auto_merge_patch: true
  stable-1-go-1-24:
    dependencies:
      auto_merge_patch: false
    stale:
      days_until_stale: 120
\`\`\`

## Migration from Legacy

### Step 1: Enable Feature Flag

\`\`\`bash
echo 'feature_flags:
  use_new_maintenance: true' >> .github/repository-config.yml
\`\`\`

### Step 2: Configure Maintenance

Copy and customize configuration from examples above.

### Step 3: Test Manually

\`\`\`bash
gh workflow run maintenance.yml -f maintenance-type=all -f create-issues=false
\`\`\`

### Step 4: Review Results

Check workflow logs and maintenance report artifact.

### Step 5: Enable Automation

Once satisfied, enable auto-merge and issue creation as needed.

## Reference

- **Helper Script**: `.github/workflows/scripts/maintenance_workflow.py`
- **Reusable Workflow**: `.github/workflows/reusable-maintenance.yml`
- **Caller Workflow**: `.github/workflows/maintenance.yml`
- **Tests**: `.github/workflows/scripts/tests/test_maintenance_workflow.py`
\`\`\`

### Verification Steps

\`\`\`bash
# 1. Verify documentation file
test -f docs/refactors/workflows/v2/maintenance-config.md && echo "✅ Config doc created"

# 2. Check markdown syntax
markdownlint docs/refactors/workflows/v2/maintenance-config.md

# 3. Validate YAML examples
yq eval docs/refactors/workflows/v2/maintenance-config.md

# 4. Test configuration examples
cp docs/refactors/workflows/v2/maintenance-config.md .github/repository-config.yml.example
\`\`\`

---

## Phase 4 Completion Checklist

- [ ] maintenance_workflow.py helper module created with dependency checking
- [ ] Unit tests implemented for all helper functions
- [ ] reusable-maintenance.yml workflow operational
- [ ] maintenance.yml caller workflow with scheduling
- [ ] Configuration documentation complete with examples
- [ ] Feature flag pattern implemented
- [ ] All maintenance tasks tested locally
- [ ] Dependency checks working for all languages (Go, Rust, Python, Node.js)
- [ ] Stale detection integrated with GitHub API
- [ ] Security scanning via Dependabot alerts
- [ ] Maintenance reports generated and uploaded
- [ ] Branch-specific policies supported
- [ ] No Windows-specific code or configurations
- [ ] All code follows Google Python Style Guide
- [ ] All workflows follow repository conventions
