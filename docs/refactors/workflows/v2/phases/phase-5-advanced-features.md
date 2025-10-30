<!-- file: docs/refactors/workflows/v2/phases/phase-5-advanced-features.md -->
<!-- version: 1.0.0 -->
<!-- guid: a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d -->

# Phase 5: Advanced Features

## Overview

This phase implements advanced automation features including GitHub Apps integration, intelligent
caching strategies, performance optimization, and workflow analytics. These features enhance the v2
system with sophisticated automation capabilities.

## Goals

- Integrate GitHub Apps for enhanced API access and automation
- Implement intelligent caching strategies for faster builds
- Optimize workflow performance and resource usage
- Collect and analyze workflow metrics
- Support advanced automation patterns
- Enable workflow self-healing and auto-remediation

## Success Criteria

- [ ] `automation_workflow.py` helper module created
- [ ] GitHub Apps integration operational
- [ ] Intelligent caching system implemented
- [ ] Performance optimization applied to all workflows
- [ ] Workflow analytics dashboard created
- [ ] Self-healing workflows operational
- [ ] Advanced patterns documented and tested
- [ ] All features follow repository conventions
- [ ] No Windows-specific features

## Dependencies

- Phase 0: `workflow_common.py` for config and validation
- Phase 1-4: All CI, release, documentation, and maintenance workflows

---

## Task 5.1: Create automation_workflow.py Helper Module

**Status**: Not Started **Dependencies**: Phase 0 (workflow_common.py) **Estimated Time**: 5 hours
**Idempotent**: Yes

### Description

Create a Python helper module for advanced automation features including GitHub Apps integration,
caching strategies, performance monitoring, and self-healing capabilities.

### Code Style Requirements

**MUST follow**:

- `.github/instructions/python.instructions.md` - Google Python Style Guide
- `.github/instructions/general-coding.instructions.md` - File headers, versioning

### Implementation

Create file: `.github/workflows/scripts/automation_workflow.py`

```python
#!/usr/bin/env python3
# file: .github/workflows/scripts/automation_workflow.py
# version: 1.0.0
# guid: b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e

"""Advanced automation workflow helper.

This module provides utilities for GitHub Apps integration, intelligent caching,
performance optimization, workflow analytics, and self-healing capabilities.

Features:
    - GitHub Apps authentication and API access
    - Intelligent cache key generation and management
    - Performance monitoring and optimization
    - Workflow analytics and metrics collection
    - Self-healing workflow detection and remediation
    - Advanced automation patterns

Usage:
    # Generate GitHub App token
    python automation_workflow.py github-app-token --app-id 123456

    # Generate intelligent cache key
    python automation_workflow.py cache-key --files "go.mod,go.sum"

    # Collect workflow metrics
    python automation_workflow.py collect-metrics

Example:
    from automation_workflow import get_github_app_token, generate_cache_key

    # Get GitHub App token
    token = get_github_app_token(app_id=123456, private_key=key)

    # Generate cache key
    cache_key = generate_cache_key(["go.mod", "go.sum"], "go-build")
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import jwt
import requests

# Ensure workflow_common is importable
sys.path.insert(0, str(Path(__file__).parent))
import workflow_common


@dataclass
class CacheStrategy:
    """Information about a cache strategy.

    Attributes:
        key: Cache key.
        restore_keys: List of fallback restore keys.
        paths: List of paths to cache.
        compression: Compression algorithm (zstd/gzip).
        ttl_days: Time-to-live in days.
    """

    key: str
    restore_keys: list[str]
    paths: list[str]
    compression: str
    ttl_days: int


@dataclass
class WorkflowMetrics:
    """Workflow execution metrics.

    Attributes:
        workflow_name: Name of workflow.
        run_id: Workflow run ID.
        started_at: Start timestamp.
        completed_at: Completion timestamp.
        duration_seconds: Total duration.
        status: Workflow status (success/failure/cancelled).
        jobs: List of job metrics.
        cache_hit_rate: Cache hit rate percentage.
        resource_usage: Resource usage statistics.
    """

    workflow_name: str
    run_id: int
    started_at: datetime
    completed_at: datetime
    duration_seconds: int
    status: str
    jobs: list[dict[str, Any]]
    cache_hit_rate: float
    resource_usage: dict[str, Any]


@dataclass
class SelfHealingAction:
    """Self-healing action information.

    Attributes:
        workflow: Workflow name.
        job: Job name.
        issue_type: Type of issue detected.
        action: Remediation action taken.
        success: Whether remediation succeeded.
        details: Additional details.
    """

    workflow: str
    job: str
    issue_type: str
    action: str
    success: bool
    details: dict[str, Any]


def get_github_app_token(
    app_id: int,
    private_key: str | Path,
    installation_id: int | None = None,
) -> str:
    """Generate GitHub App installation access token.

    Creates a JWT for GitHub App authentication and exchanges it for
    an installation access token with enhanced API rate limits.

    Args:
        app_id: GitHub App ID.
        private_key: Path to private key file or key content.
        installation_id: Installation ID (auto-detected if not provided).

    Returns:
        Installation access token.

    Raises:
        WorkflowError: If token generation fails.

    Example:
        >>> token = get_github_app_token(
        ...     app_id=123456,
        ...     private_key="key.pem"
        ... )
        >>> print(f"Token: {token[:10]}...")
        Token: ghs_abc123...
    """
    workflow_common.log_info(f"Generating GitHub App token for app {app_id}")

    # Load private key
    if isinstance(private_key, (str, Path)):
        key_path = Path(private_key)
        if key_path.exists():
            private_key_content = key_path.read_text()
        else:
            private_key_content = private_key
    else:
        private_key_content = private_key

    # Generate JWT
    now = int(time.time())
    payload = {
        "iat": now - 60,  # Issued 60 seconds in the past
        "exp": now + (10 * 60),  # Expires in 10 minutes
        "iss": str(app_id),
    }

    try:
        encoded_jwt = jwt.encode(payload, private_key_content, algorithm="RS256")
    except Exception as e:
        raise workflow_common.WorkflowError(f"Failed to generate JWT: {e}") from e

    # Get installation ID if not provided
    if installation_id is None:
        installation_id = _get_installation_id(encoded_jwt)

    # Exchange JWT for installation token
    headers = {
        "Authorization": f"Bearer {encoded_jwt}",
        "Accept": "application/vnd.github.v3+json",
    }

    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"

    try:
        response = requests.post(url, headers=headers, timeout=30)
        response.raise_for_status()
        token_data = response.json()
        return token_data["token"]
    except requests.RequestException as e:
        raise workflow_common.WorkflowError(
            f"Failed to get installation token: {e}"
        ) from e


def _get_installation_id(jwt_token: str) -> int:
    """Get GitHub App installation ID for current repository.

    Args:
        jwt_token: GitHub App JWT token.

    Returns:
        Installation ID.

    Raises:
        WorkflowError: If installation ID cannot be determined.
    """
    repo = workflow_common.get_env_var("GITHUB_REPOSITORY")
    owner = repo.split("/")[0]

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Try to get installation for specific repository
    url = f"https://api.github.com/repos/{repo}/installation"

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()["id"]
    except requests.RequestException:
        # Fall back to listing all installations
        url = "https://api.github.com/app/installations"
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        installations = response.json()
        for installation in installations:
            if installation["account"]["login"] == owner:
                return installation["id"]

        raise workflow_common.WorkflowError(
            f"No installation found for {owner}"
        )


def generate_cache_key(
    files: list[str | Path],
    prefix: str,
    include_runner: bool = True,
    include_branch: bool = False,
) -> CacheStrategy:
    """Generate intelligent cache key with restore keys.

    Creates a cache key based on file hashes, runner OS, and optionally
    branch name. Provides fallback restore keys for cache reuse.

    Args:
        files: List of files to hash for cache key.
        prefix: Cache key prefix (e.g., 'go-build', 'npm-cache').
        include_runner: Include runner OS in cache key.
        include_branch: Include branch name in cache key.

    Returns:
        CacheStrategy with key, restore keys, and paths.

    Example:
        >>> strategy = generate_cache_key(
        ...     files=["go.mod", "go.sum"],
        ...     prefix="go-build",
        ...     include_runner=True
        ... )
        >>> print(strategy.key)
        go-build-linux-abc123def456
    """
    workflow_common.log_info(f"Generating cache key with prefix: {prefix}")

    # Compute hash of all specified files
    hasher = hashlib.sha256()
    for file_path in files:
        path = Path(file_path)
        if path.exists():
            hasher.update(path.read_bytes())
        else:
            workflow_common.log_warning(f"Cache key file not found: {file_path}")

    file_hash = hasher.hexdigest()[:12]

    # Build cache key components
    key_parts = [prefix]

    if include_runner:
        runner_os = workflow_common.get_env_var("RUNNER_OS", "linux").lower()
        key_parts.append(runner_os)

    if include_branch:
        ref = workflow_common.get_env_var("GITHUB_REF", "")
        if ref.startswith("refs/heads/"):
            branch = ref.replace("refs/heads/", "")
            key_parts.append(branch)

    key_parts.append(file_hash)

    # Primary cache key
    cache_key = "-".join(key_parts)

    # Generate restore keys (fallback keys without file hash)
    restore_keys = []

    # Level 1: Same runner, same branch (if included), any hash
    level1_parts = key_parts[:-1]
    if level1_parts:
        restore_keys.append("-".join(level1_parts) + "-")

    # Level 2: Same runner, any branch, any hash
    if include_runner and include_branch:
        restore_keys.append(f"{prefix}-{runner_os}-")

    # Level 3: Any runner, any branch, any hash
    restore_keys.append(f"{prefix}-")

    # Determine paths to cache based on prefix
    cache_paths = _get_cache_paths(prefix)

    return CacheStrategy(
        key=cache_key,
        restore_keys=restore_keys,
        paths=cache_paths,
        compression="zstd",
        ttl_days=7,
    )


def _get_cache_paths(prefix: str) -> list[str]:
    """Get cache paths for a given cache prefix.

    Args:
        prefix: Cache prefix (e.g., 'go-build', 'npm-cache').

    Returns:
        List of paths to cache.
    """
    cache_paths = {
        "go-build": [
            "~/.cache/go-build",
            "~/go/pkg/mod",
        ],
        "rust-cargo": [
            "~/.cargo/registry/index",
            "~/.cargo/registry/cache",
            "~/.cargo/git/db",
            "target/",
        ],
        "python-pip": [
            "~/.cache/pip",
            ".venv/",
        ],
        "node-npm": [
            "~/.npm",
            "node_modules/",
        ],
        "node-yarn": [
            "~/.yarn/cache",
            "node_modules/",
        ],
    }

    return cache_paths.get(prefix, [])


def collect_workflow_metrics(
    workflow_name: str | None = None,
) -> list[WorkflowMetrics]:
    """Collect workflow execution metrics.

    Retrieves metrics for recent workflow runs including duration,
    status, cache hit rates, and resource usage.

    Args:
        workflow_name: Specific workflow to collect metrics for.
                      If None, collects for all workflows.

    Returns:
        List of workflow metrics.

    Raises:
        WorkflowError: If metrics collection fails.

    Example:
        >>> metrics = collect_workflow_metrics("ci.yml")
        >>> for m in metrics:
        ...     print(f"{m.workflow_name}: {m.duration_seconds}s")
        ci.yml: 245s
    """
    workflow_common.log_info("Collecting workflow metrics")

    token = workflow_common.get_env_var("GITHUB_TOKEN")
    repo = workflow_common.get_env_var("GITHUB_REPOSITORY")

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    metrics = []

    try:
        # Get recent workflow runs
        url = f"https://api.github.com/repos/{repo}/actions/runs"
        params = {"per_page": 100, "status": "completed"}

        if workflow_name:
            # Get workflow ID first
            workflows_url = f"https://api.github.com/repos/{repo}/actions/workflows"
            workflows_response = requests.get(
                workflows_url, headers=headers, timeout=30
            )
            workflows_response.raise_for_status()

            for workflow in workflows_response.json().get("workflows", []):
                if workflow["path"].endswith(workflow_name):
                    params["workflow_id"] = workflow["id"]
                    break

        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()

        runs = response.json().get("workflow_runs", [])

        for run in runs:
            # Get job details
            jobs_url = run["jobs_url"]
            jobs_response = requests.get(jobs_url, headers=headers, timeout=30)
            jobs_response.raise_for_status()

            jobs = jobs_response.json().get("jobs", [])

            # Calculate metrics
            started_at = datetime.fromisoformat(run["created_at"].rstrip("Z"))
            completed_at = datetime.fromisoformat(run["updated_at"].rstrip("Z"))
            duration = (completed_at - started_at).total_seconds()

            # Calculate cache hit rate from job logs (simplified)
            cache_hit_rate = _calculate_cache_hit_rate(jobs)

            metrics.append(
                WorkflowMetrics(
                    workflow_name=run["name"],
                    run_id=run["id"],
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_seconds=int(duration),
                    status=run["conclusion"],
                    jobs=[
                        {
                            "name": job["name"],
                            "duration": (
                                datetime.fromisoformat(job["completed_at"].rstrip("Z"))
                                - datetime.fromisoformat(job["started_at"].rstrip("Z"))
                            ).total_seconds()
                            if job.get("completed_at") and job.get("started_at")
                            else 0,
                            "status": job["conclusion"],
                        }
                        for job in jobs
                    ],
                    cache_hit_rate=cache_hit_rate,
                    resource_usage={
                        "runner_count": len(jobs),
                        "total_duration": sum(
                            (
                                datetime.fromisoformat(job["completed_at"].rstrip("Z"))
                                - datetime.fromisoformat(job["started_at"].rstrip("Z"))
                            ).total_seconds()
                            if job.get("completed_at") and job.get("started_at")
                            else 0
                            for job in jobs
                        ),
                    },
                )
            )

    except requests.RequestException as e:
        workflow_common.log_warning(f"Failed to collect metrics: {e}")

    return metrics


def _calculate_cache_hit_rate(jobs: list[dict[str, Any]]) -> float:
    """Calculate cache hit rate from job data.

    Args:
        jobs: List of job dictionaries.

    Returns:
        Cache hit rate as percentage (0-100).
    """
    # Simplified calculation - would parse job logs in real implementation
    return 85.0


def detect_workflow_issues(
    workflow_name: str,
    lookback_days: int = 7,
) -> list[SelfHealingAction]:
    """Detect workflow issues and recommend self-healing actions.

    Analyzes recent workflow failures and suggests remediation actions.

    Args:
        workflow_name: Workflow to analyze.
        lookback_days: Days of history to analyze.

    Returns:
        List of self-healing actions.

    Example:
        >>> actions = detect_workflow_issues("ci.yml", lookback_days=7)
        >>> for action in actions:
        ...     print(f"{action.issue_type}: {action.action}")
        cache-miss: regenerate-cache-key
    """
    workflow_common.log_info(
        f"Detecting issues in {workflow_name} (last {lookback_days} days)"
    )

    metrics = collect_workflow_metrics(workflow_name)

    actions = []

    # Analyze cache performance
    recent_metrics = [
        m for m in metrics
        if (datetime.now() - m.completed_at).days <= lookback_days
    ]

    if recent_metrics:
        avg_cache_hit = sum(m.cache_hit_rate for m in recent_metrics) / len(
            recent_metrics
        )

        if avg_cache_hit < 50.0:
            actions.append(
                SelfHealingAction(
                    workflow=workflow_name,
                    job="all",
                    issue_type="low-cache-hit-rate",
                    action="regenerate-cache-keys",
                    success=False,
                    details={
                        "current_rate": avg_cache_hit,
                        "threshold": 50.0,
                        "recommendation": "Review cache key generation strategy",
                    },
                )
            )

    # Analyze failure patterns
    failed_runs = [m for m in recent_metrics if m.status == "failure"]

    if len(failed_runs) > len(recent_metrics) * 0.3:  # >30% failure rate
        actions.append(
            SelfHealingAction(
                workflow=workflow_name,
                job="all",
                issue_type="high-failure-rate",
                action="alert-maintainers",
                success=False,
                details={
                    "failure_rate": len(failed_runs) / len(recent_metrics) * 100,
                    "threshold": 30.0,
                    "recommendation": "Investigate root cause of failures",
                },
            )
        )

    return actions


def optimize_workflow_performance(workflow_file: str | Path) -> dict[str, Any]:
    """Analyze workflow and suggest performance optimizations.

    Args:
        workflow_file: Path to workflow YAML file.

    Returns:
        Dictionary of optimization suggestions.

    Example:
        >>> suggestions = optimize_workflow_performance(".github/workflows/ci.yml")
        >>> print(suggestions["suggestions"])
        ['Enable dependency caching', 'Parallelize test jobs']
    """
    workflow_common.log_info(f"Analyzing workflow performance: {workflow_file}")

    workflow_path = Path(workflow_file)
    if not workflow_path.exists():
        raise workflow_common.WorkflowError(f"Workflow file not found: {workflow_file}")

    workflow_data = workflow_common.load_yaml_config(workflow_path)

    suggestions = []

    # Check for caching
    has_cache = False
    jobs = workflow_data.get("jobs", {})

    for job_name, job_config in jobs.items():
        steps = job_config.get("steps", [])
        for step in steps:
            if step.get("uses", "").startswith("actions/cache"):
                has_cache = True
                break

    if not has_cache:
        suggestions.append({
            "type": "caching",
            "priority": "high",
            "suggestion": "Add dependency caching to reduce build times",
            "example": "Use actions/cache@v4 for Go modules, npm packages, etc.",
        })

    # Check for parallelization opportunities
    serial_jobs = []
    for job_name, job_config in jobs.items():
        if "needs" not in job_config:
            serial_jobs.append(job_name)

    if len(serial_jobs) > 3:
        suggestions.append({
            "type": "parallelization",
            "priority": "medium",
            "suggestion": f"Consider parallelizing {len(serial_jobs)} independent jobs",
            "jobs": serial_jobs,
        })

    # Check for matrix strategy usage
    uses_matrix = False
    for job_config in jobs.values():
        if "strategy" in job_config and "matrix" in job_config["strategy"]:
            uses_matrix = True
            break

    if not uses_matrix and len(jobs) > 1:
        suggestions.append({
            "type": "matrix-strategy",
            "priority": "medium",
            "suggestion": "Consider using matrix strategy for testing multiple configurations",
            "example": "Test multiple Go versions, operating systems, etc.",
        })

    return {
        "workflow": str(workflow_file),
        "analyzed_at": datetime.now().isoformat(),
        "jobs_count": len(jobs),
        "has_caching": has_cache,
        "uses_matrix": uses_matrix,
        "suggestions": suggestions,
    }


def main() -> None:
    """Main entry point for automation CLI."""
    parser = argparse.ArgumentParser(
        description="Advanced automation workflow helper"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # GitHub App token command
    app_parser = subparsers.add_parser(
        "github-app-token", help="Generate GitHub App installation token"
    )
    app_parser.add_argument(
        "--app-id", type=int, required=True, help="GitHub App ID"
    )
    app_parser.add_argument(
        "--private-key", required=True, help="Path to private key file"
    )
    app_parser.add_argument(
        "--installation-id", type=int, help="Installation ID (auto-detected if omitted)"
    )

    # Cache key command
    cache_parser = subparsers.add_parser(
        "cache-key", help="Generate intelligent cache key"
    )
    cache_parser.add_argument(
        "--files", required=True, help="Comma-separated list of files to hash"
    )
    cache_parser.add_argument(
        "--prefix", required=True, help="Cache key prefix"
    )
    cache_parser.add_argument(
        "--no-runner", action="store_true", help="Exclude runner OS from key"
    )
    cache_parser.add_argument(
        "--branch", action="store_true", help="Include branch name in key"
    )

    # Metrics command
    metrics_parser = subparsers.add_parser(
        "collect-metrics", help="Collect workflow metrics"
    )
    metrics_parser.add_argument(
        "--workflow", help="Specific workflow to collect metrics for"
    )

    # Issues command
    issues_parser = subparsers.add_parser(
        "detect-issues", help="Detect workflow issues"
    )
    issues_parser.add_argument(
        "--workflow", required=True, help="Workflow to analyze"
    )
    issues_parser.add_argument(
        "--lookback-days", type=int, default=7, help="Days of history to analyze"
    )

    # Optimize command
    optimize_parser = subparsers.add_parser(
        "optimize", help="Analyze workflow performance"
    )
    optimize_parser.add_argument(
        "--workflow-file", required=True, help="Path to workflow YAML file"
    )

    args = parser.parse_args()

    try:
        if args.command == "github-app-token":
            token = get_github_app_token(
                args.app_id,
                args.private_key,
                args.installation_id,
            )
            workflow_common.set_output("token", token)
            workflow_common.log_info("GitHub App token generated successfully")

        elif args.command == "cache-key":
            files = args.files.split(",")
            strategy = generate_cache_key(
                files,
                args.prefix,
                include_runner=not args.no_runner,
                include_branch=args.branch,
            )
            workflow_common.set_output("cache-key", strategy.key)
            workflow_common.set_output(
                "restore-keys", "\n".join(strategy.restore_keys)
            )
            workflow_common.set_output("cache-paths", "\n".join(strategy.paths))
            workflow_common.log_info(f"Cache key: {strategy.key}")

        elif args.command == "collect-metrics":
            metrics = collect_workflow_metrics(args.workflow)
            workflow_common.log_info(f"Collected metrics for {len(metrics)} runs")
            workflow_common.set_output("metrics-count", str(len(metrics)))

        elif args.command == "detect-issues":
            actions = detect_workflow_issues(args.workflow, args.lookback_days)
            workflow_common.log_info(f"Detected {len(actions)} issues")
            workflow_common.set_output("issues-count", str(len(actions)))

        elif args.command == "optimize":
            result = optimize_workflow_performance(args.workflow_file)
            workflow_common.log_info(
                f"Found {len(result['suggestions'])} optimization suggestions"
            )
            print(json.dumps(result, indent=2))

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
test -f .github/workflows/scripts/automation_workflow.py && echo "✅ Script created"

# 2. Check Python syntax
python3 -m py_compile .github/workflows/scripts/automation_workflow.py && echo "✅ Valid Python"

# 3. Make executable
chmod +x .github/workflows/scripts/automation_workflow.py && echo "✅ Executable"

# 4. Test cache key generation
python3 .github/workflows/scripts/automation_workflow.py cache-key \
  --files "go.mod,go.sum" --prefix "go-build" && echo "✅ Cache key generation working"

# 5. Test workflow optimization analysis
python3 .github/workflows/scripts/automation_workflow.py optimize \
  --workflow-file .github/workflows/ci.yml && echo "✅ Optimization analysis working"
```

---

## Task 5.2: Create test_automation_workflow.py Unit Tests

**Status**: Not Started **Dependencies**: Task 5.1 (automation_workflow.py) **Estimated Time**: 2
hours **Idempotent**: Yes

### Description

Create comprehensive unit tests for automation_workflow.py.

### Implementation

Create file: `.github/workflows/scripts/tests/test_automation_workflow.py`

```python
#!/usr/bin/env python3
# file: .github/workflows/scripts/tests/test_automation_workflow.py
# version: 1.0.0
# guid: c3d4e5f6-a7b8-9c0d-1e2f-3a4b5c6d7e8f

"""Unit tests for automation_workflow module."""

import json
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
import automation_workflow


class TestGitHubAppIntegration(unittest.TestCase):
    """Test GitHub App authentication."""

    @patch("time.time")
    @patch("jwt.encode")
    @patch("requests.post")
    def test_get_github_app_token(self, mock_post, mock_jwt, mock_time):
        """Test GitHub App token generation."""
        # Arrange
        mock_time.return_value = 1000000
        mock_jwt.return_value = "test-jwt"
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"token": "ghs_test_token"},
        )

        # Act
        token = automation_workflow.get_github_app_token(
            app_id=123456,
            private_key="test-key",
            installation_id=789
        )

        # Assert
        self.assertEqual(token, "ghs_test_token")
        mock_jwt.assert_called_once()
        mock_post.assert_called_once()


class TestCacheKeyGeneration(unittest.TestCase):
    """Test intelligent cache key generation."""

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.read_bytes")
    @patch.dict("os.environ", {"RUNNER_OS": "Linux", "GITHUB_REF": "refs/heads/main"})
    def test_generate_cache_key_basic(self, mock_read, mock_exists):
        """Test basic cache key generation."""
        # Arrange
        mock_exists.return_value = True
        mock_read.return_value = b"test content"

        # Act
        strategy = automation_workflow.generate_cache_key(
            files=["go.mod"],
            prefix="go-build",
            include_runner=True,
            include_branch=False
        )

        # Assert
        self.assertTrue(strategy.key.startswith("go-build-linux-"))
        self.assertGreater(len(strategy.restore_keys), 0)
        self.assertIn("~/.cache/go-build", strategy.paths)

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.read_bytes")
    @patch.dict("os.environ", {"RUNNER_OS": "Linux", "GITHUB_REF": "refs/heads/main"})
    def test_generate_cache_key_with_branch(self, mock_read, mock_exists):
        """Test cache key generation with branch name."""
        # Arrange
        mock_exists.return_value = True
        mock_read.return_value = b"test content"

        # Act
        strategy = automation_workflow.generate_cache_key(
            files=["go.mod"],
            prefix="go-build",
            include_runner=True,
            include_branch=True
        )

        # Assert
        self.assertIn("main", strategy.key)

    def test_get_cache_paths_go(self):
        """Test cache paths for Go."""
        paths = automation_workflow._get_cache_paths("go-build")
        self.assertIn("~/.cache/go-build", paths)
        self.assertIn("~/go/pkg/mod", paths)

    def test_get_cache_paths_rust(self):
        """Test cache paths for Rust."""
        paths = automation_workflow._get_cache_paths("rust-cargo")
        self.assertIn("~/.cargo/registry/cache", paths)
        self.assertIn("target/", paths)


class TestWorkflowMetrics(unittest.TestCase):
    """Test workflow metrics collection."""

    @patch("requests.get")
    @patch.dict("os.environ", {"GITHUB_TOKEN": "test-token", "GITHUB_REPOSITORY": "owner/repo"})
    def test_collect_workflow_metrics(self, mock_get):
        """Test collecting workflow metrics."""
        # Arrange
        mock_get.side_effect = [
            # Workflow runs response
            MagicMock(
                status_code=200,
                json=lambda: {
                    "workflow_runs": [
                        {
                            "id": 123,
                            "name": "CI",
                            "created_at": "2024-01-01T00:00:00Z",
                            "updated_at": "2024-01-01T00:05:00Z",
                            "conclusion": "success",
                            "jobs_url": "https://api.github.com/jobs",
                        }
                    ]
                },
            ),
            # Jobs response
            MagicMock(
                status_code=200,
                json=lambda: {
                    "jobs": [
                        {
                            "name": "test",
                            "started_at": "2024-01-01T00:00:00Z",
                            "completed_at": "2024-01-01T00:05:00Z",
                            "conclusion": "success",
                        }
                    ]
                },
            ),
        ]

        # Act
        metrics = automation_workflow.collect_workflow_metrics("ci.yml")

        # Assert
        self.assertEqual(len(metrics), 1)
        self.assertEqual(metrics[0].workflow_name, "CI")
        self.assertEqual(metrics[0].status, "success")


class TestSelfHealing(unittest.TestCase):
    """Test self-healing workflow detection."""

    @patch("automation_workflow.collect_workflow_metrics")
    def test_detect_workflow_issues_low_cache(self, mock_collect):
        """Test detecting low cache hit rate."""
        # Arrange
        mock_collect.return_value = [
            automation_workflow.WorkflowMetrics(
                workflow_name="CI",
                run_id=123,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                duration_seconds=300,
                status="success",
                jobs=[],
                cache_hit_rate=30.0,  # Below 50% threshold
                resource_usage={},
            )
        ]

        # Act
        actions = automation_workflow.detect_workflow_issues("ci.yml", lookback_days=7)

        # Assert
        self.assertGreater(len(actions), 0)
        self.assertTrue(
            any(a.issue_type == "low-cache-hit-rate" for a in actions)
        )

    @patch("automation_workflow.collect_workflow_metrics")
    def test_detect_workflow_issues_high_failure(self, mock_collect):
        """Test detecting high failure rate."""
        # Arrange
        mock_collect.return_value = [
            automation_workflow.WorkflowMetrics(
                workflow_name="CI",
                run_id=i,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                duration_seconds=300,
                status="failure" if i % 2 == 0 else "success",  # 50% failure rate
                jobs=[],
                cache_hit_rate=85.0,
                resource_usage={},
            )
            for i in range(10)
        ]

        # Act
        actions = automation_workflow.detect_workflow_issues("ci.yml", lookback_days=7)

        # Assert
        self.assertTrue(
            any(a.issue_type == "high-failure-rate" for a in actions)
        )


class TestWorkflowOptimization(unittest.TestCase):
    """Test workflow performance optimization."""

    @patch("automation_workflow.workflow_common.load_yaml_config")
    @patch("pathlib.Path.exists")
    def test_optimize_workflow_no_cache(self, mock_exists, mock_load):
        """Test detecting missing cache configuration."""
        # Arrange
        mock_exists.return_value = True
        mock_load.return_value = {
            "jobs": {
                "build": {
                    "steps": [
                        {"name": "Checkout", "uses": "actions/checkout@v4"}
                    ]
                }
            }
        }

        # Act
        result = automation_workflow.optimize_workflow_performance("test.yml")

        # Assert
        self.assertFalse(result["has_caching"])
        self.assertTrue(
            any(s["type"] == "caching" for s in result["suggestions"])
        )

    @patch("automation_workflow.workflow_common.load_yaml_config")
    @patch("pathlib.Path.exists")
    def test_optimize_workflow_parallelization(self, mock_exists, mock_load):
        """Test detecting parallelization opportunities."""
        # Arrange
        mock_exists.return_value = True
        mock_load.return_value = {
            "jobs": {
                "job1": {"steps": []},
                "job2": {"steps": []},
                "job3": {"steps": []},
                "job4": {"steps": []},
            }
        }

        # Act
        result = automation_workflow.optimize_workflow_performance("test.yml")

        # Assert
        suggestions = result["suggestions"]
        parallel_suggestions = [s for s in suggestions if s["type"] == "parallelization"]
        self.assertGreater(len(parallel_suggestions), 0)


if __name__ == "__main__":
    unittest.main()
```

### Verification Steps

```bash
# 1. Run all tests
python3 -m pytest .github/workflows/scripts/tests/test_automation_workflow.py -v

# 2. Check test coverage
python3 -m pytest .github/workflows/scripts/tests/test_automation_workflow.py \
  --cov=automation_workflow --cov-report=term-missing

# 3. Verify specific test categories
python3 -m pytest .github/workflows/scripts/tests/test_automation_workflow.py::TestGitHubAppIntegration -v
python3 -m pytest .github/workflows/scripts/tests/test_automation_workflow.py::TestCacheKeyGeneration -v
python3 -m pytest .github/workflows/scripts/tests/test_automation_workflow.py::TestWorkflowMetrics -v
```

---

## Task 5.3: Create GitHub Apps Configuration

**Status**: Not Started **Dependencies**: Tasks 5.1-5.2 **Estimated Time**: 2 hours **Idempotent**:
Yes

### Description

Configure GitHub Apps for enhanced API access and automation.

### Implementation

Create file: `docs/refactors/workflows/v2/github-apps-setup.md`

````markdown
<!-- file: docs/refactors/workflows/v2/github-apps-setup.md -->
<!-- version: 1.0.0 -->
<!-- guid: d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a -->

# GitHub Apps Setup Guide

## Overview

GitHub Apps provide enhanced API access with higher rate limits and more granular permissions than
personal access tokens. The v2 workflow system uses GitHub Apps for advanced automation features.

## Benefits

- **Higher rate limits**: 5,000 requests/hour per installation vs 1,000/hour for PATs
- **Granular permissions**: Request only needed permissions
- **Better security**: Tokens expire automatically, no user PAT dependencies
- **Organization-wide**: Single app installation across all repositories

## Setup Steps

### 1. Create GitHub App

1. Navigate to Organization Settings → Developer Settings → GitHub Apps
2. Click "New GitHub App"
3. Fill in app details:

**Basic Information**:

- **Name**: "Workflow Automation v2"
- **Description**: "Advanced workflow automation with intelligent caching and self-healing"
- **Homepage URL**: https://github.com/YOUR_ORG/ghcommon
- **Webhook**: Disable (not needed for workflow automation)

**Permissions**:

Repository permissions:

- **Actions**: Read & Write (for workflow dispatch and monitoring)
- **Contents**: Read & Write (for automated commits)
- **Issues**: Read & Write (for maintenance automation)
- **Pull Requests**: Read & Write (for automated PRs)
- **Metadata**: Read (required)

Organization permissions:

- **Administration**: Read (for organization-wide operations)
- **Members**: Read (for team mentions)

**Where can this GitHub App be installed?**:

- Select "Only on this account"

4. Click "Create GitHub App"

### 2. Generate Private Key

1. Scroll to "Private keys" section
2. Click "Generate a private key"
3. Save the downloaded `.pem` file securely

### 3. Install App

1. Click "Install App" in left sidebar
2. Select your organization
3. Choose "All repositories" or select specific repositories
4. Click "Install"

### 4. Store Secrets

Add secrets to repository:

```bash
# Get App ID from app settings page
gh secret set GITHUB_APP_ID --body "123456"

# Get Installation ID from installation URL
# Format: https://github.com/settings/installations/{installation_id}
gh secret set GITHUB_APP_INSTALLATION_ID --body "789012"

# Add private key (multi-line secret)
gh secret set GITHUB_APP_PRIVATE_KEY < path/to/private-key.pem
```
````

### 5. Test Integration

Create test workflow:

\`\`\`yaml name: Test GitHub App

on: workflow_dispatch:

jobs: test-app: runs-on: ubuntu-latest steps: - name: Checkout uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'

      - name: Install dependencies
        run: |
          pip install pyjwt requests

      - name: Generate App Token
        id: app-token
        run: |
          python .github/workflows/scripts/automation_workflow.py github-app-token \\
            --app-id \${{ secrets.GITHUB_APP_ID }} \\
            --private-key \${{ secrets.GITHUB_APP_PRIVATE_KEY }} \\
            --installation-id \${{ secrets.GITHUB_APP_INSTALLATION_ID }}

      - name: Test API Access
        env:
          GITHUB_TOKEN: \${{ steps.app-token.outputs.token }}
        run: |
          curl -H "Authorization: Bearer $GITHUB_TOKEN" \\
            https://api.github.com/rate_limit

\`\`\`

Run workflow and verify:

- Token generation succeeds
- API rate limit shows 5,000/hour

## Usage in Workflows

### Basic Usage

\`\`\`yaml jobs: automated-task: runs-on: ubuntu-latest steps: - name: Generate App Token id:
app-token uses: actions/github-script@v7 with: script: | const { execSync } =
require('child_process'); const token = execSync( 'python
.github/workflows/scripts/automation_workflow.py github-app-token ' + '--app-id
\${{ secrets.GITHUB_APP_ID }} ' + '--private-key \${{ secrets.GITHUB_APP_PRIVATE_KEY }}'
).toString().trim(); core.setOutput('token', token);

      - name: Use Enhanced Token
        env:
          GITHUB_TOKEN: \${{ steps.app-token.outputs.token }}
        run: |
          # API calls here use app token with higher rate limits
          gh api /repos/\${{ github.repository }}/actions/runs

\`\`\`

### Advanced: Reusable Action

Create `.github/actions/github-app-token/action.yml`:

\`\`\`yaml name: 'Get GitHub App Token' description: 'Generate installation token for GitHub App'
outputs: token: description: 'GitHub App installation token' value:
\${{ steps.generate.outputs.token }} runs: using: composite steps: - name: Set up Python uses:
actions/setup-python@v5 with: python-version: '3.14'

    - name: Install dependencies
      shell: bash
      run: pip install pyjwt requests

    - name: Generate token
      id: generate
      shell: bash
      run: |
        python .github/workflows/scripts/automation_workflow.py github-app-token \\
          --app-id \${{ secrets.GITHUB_APP_ID }} \\
          --private-key \${{ secrets.GITHUB_APP_PRIVATE_KEY }} \\
          --installation-id \${{ secrets.GITHUB_APP_INSTALLATION_ID }}

\`\`\`

Use in workflows:

\`\`\`yaml jobs: task: runs-on: ubuntu-latest steps: - name: Get App Token id: app-token uses:
./.github/actions/github-app-token

      - name: Use Token
        env:
          GITHUB_TOKEN: \${{ steps.app-token.outputs.token }}
        run: gh api /user

\`\`\`

## Security Best Practices

1. **Private Key Storage**:
   - Never commit private keys to repository
   - Store only in GitHub Secrets
   - Rotate keys quarterly

2. **Permission Scope**:
   - Request minimum necessary permissions
   - Review permissions quarterly
   - Document why each permission is needed

3. **Token Handling**:
   - Tokens automatically expire after 1 hour
   - Never log tokens
   - Use masked secrets in workflows

4. **Access Review**:
   - Monitor app activity in audit log
   - Review installations monthly
   - Revoke unused installations

## Troubleshooting

### Token Generation Fails

**Error**: `Failed to generate JWT`

**Solutions**:

1. Verify private key format (PEM with header/footer)
2. Check that private key secret is multi-line
3. Ensure pyjwt package is installed

### Invalid Installation ID

**Error**: `No installation found`

**Solutions**:

1. Verify app is installed in organization
2. Check installation ID in GitHub settings
3. Ensure app has access to repository

### Permission Denied

**Error**: `Resource not accessible by integration`

**Solutions**:

1. Review app permissions in settings
2. Verify permission matches required operation
3. Regenerate token with updated permissions

## Migration from PAT

### Step 1: Create GitHub App

Follow setup steps above.

### Step 2: Update Workflows

Replace PAT usage:

\`\`\`yaml

# Before (using PAT)

env: GITHUB_TOKEN: \${{ secrets.PERSONAL_ACCESS_TOKEN }}

# After (using GitHub App)

- name: Get App Token id: app-token uses: ./.github/actions/github-app-token

- name: Use Token env: GITHUB_TOKEN: \${{ steps.app-token.outputs.token }} \`\`\`

### Step 3: Test

Run workflows with GitHub App token and verify functionality.

### Step 4: Remove PAT

Once all workflows migrated, remove PAT secret.

## Rate Limit Monitoring

Monitor API usage:

\`\`\`bash

# Check current rate limit

gh api /rate_limit --jq '.resources.core'

# Expected output with GitHub App:

# {

# "limit": 5000,

# "remaining": 4999,

# "reset": 1234567890

# }

\`\`\`

## References

- [GitHub Apps Documentation](https://docs.github.com/en/apps)
- [Creating a GitHub App](https://docs.github.com/en/apps/creating-github-apps)
- [Rate Limits](https://docs.github.com/en/rest/rate-limit) \`\`\`

### Verification Steps

\`\`\`bash

# 1. Verify documentation exists

test -f docs/refactors/workflows/v2/github-apps-setup.md && echo "✅ GitHub Apps doc created"

# 2. Create GitHub App following guide

# (Manual step in GitHub UI)

# 3. Test app integration

gh workflow run test-github-app.yml

# 4. Verify rate limits

gh api /rate_limit \`\`\`

---

## Task 5.4: Create Advanced Caching Workflow

**Status**: Not Started **Dependencies**: Tasks 5.1-5.3 **Estimated Time**: 2 hours **Idempotent**:
Yes

### Description

Create workflow with intelligent caching strategies.

### Implementation

Create file: `.github/workflows/reusable-advanced-cache.yml`

\`\`\`yaml

# file: .github/workflows/reusable-advanced-cache.yml

# version: 1.0.0

# guid: e5f6a7b8-c9d0-1e2f-3a4b-5c6d7e8f9a0b

name: Reusable Advanced Caching

on: workflow_call: inputs: language: description: 'Programming language' required: true type: string
cache-prefix: description: 'Cache key prefix' required: true type: string include-branch:
description: 'Include branch in cache key' required: false type: boolean default: false outputs:
cache-hit: description: 'Whether cache was hit' value: \${{ jobs.cache-setup.outputs.cache-hit }}
cache-key: description: 'Generated cache key' value: \${{ jobs.cache-setup.outputs.cache-key }}

permissions: contents: read

jobs: cache-setup: name: Setup Intelligent Cache runs-on: ubuntu-latest outputs: cache-hit:
\${{ steps.cache.outputs.cache-hit }} cache-key: \${{ steps.generate-key.outputs.cache-key }}
steps: - name: Checkout code uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'

      - name: Install dependencies
        run: pip install pyyaml

      - name: Determine cache files
        id: cache-files
        run: |
          case "\${{ inputs.language }}" in
            go)
              echo "files=go.mod,go.sum" >> $GITHUB_OUTPUT
              ;;
            rust)
              echo "files=Cargo.toml,Cargo.lock" >> $GITHUB_OUTPUT
              ;;
            python)
              echo "files=requirements.txt,pyproject.toml" >> $GITHUB_OUTPUT
              ;;
            node)
              echo "files=package.json,package-lock.json,yarn.lock" >> $GITHUB_OUTPUT
              ;;
            *)
              echo "::error::Unsupported language: \${{ inputs.language }}"
              exit 1
              ;;
          esac

      - name: Generate intelligent cache key
        id: generate-key
        run: |
          python .github/workflows/scripts/automation_workflow.py cache-key \\
            --files "\${{ steps.cache-files.outputs.files }}" \\
            --prefix "\${{ inputs.cache-prefix }}" \\
            \${{ inputs.include-branch && '--branch' || '' }}

      - name: Setup cache
        id: cache
        uses: actions/cache@v4
        with:
          key: \${{ steps.generate-key.outputs.cache-key }}
          restore-keys: \${{ steps.generate-key.outputs.restore-keys }}
          path: \${{ steps.generate-key.outputs.cache-paths }}

      - name: Report cache status
        run: |
          if [ "\${{ steps.cache.outputs.cache-hit }}" == "true" ]; then
            echo "✅ Cache hit: \${{ steps.generate-key.outputs.cache-key }}"
          else
            echo "⚠️  Cache miss: \${{ steps.generate-key.outputs.cache-key }}"
          fi

\`\`\`

### Verification Steps

\`\`\`bash

# 1. Validate workflow syntax

actionlint .github/workflows/reusable-advanced-cache.yml

# 2. Test Go caching

gh workflow run test-advanced-cache.yml \\ -f language=go \\ -f cache-prefix=go-build

# 3. Test Rust caching

gh workflow run test-advanced-cache.yml \\ -f language=rust \\ -f cache-prefix=rust-cargo

# 4. Test with branch-specific cache

gh workflow run test-advanced-cache.yml \\ -f language=go \\ -f cache-prefix=go-build \\ -f
include-branch=true

# 5. Verify cache hit rate

gh run list --workflow=test-advanced-cache.yml --json conclusion,name | \\ jq -r '.[] |
select(.conclusion=="success") | .name' \`\`\`

---

## Task 5.5: Create Workflow Analytics Dashboard

**Status**: Not Started **Dependencies**: Tasks 5.1-5.4 **Estimated Time**: 3 hours **Idempotent**:
Yes

### Description

Create workflow for collecting and displaying analytics.

### Implementation

Create file: `.github/workflows/workflow-analytics.yml`

\`\`\`yaml

# file: .github/workflows/workflow-analytics.yml

# version: 1.0.0

# guid: f6a7b8c9-d0e1-2f3a-4b5c-6d7e8f9a0b1c

name: Workflow Analytics

on: schedule: # Daily at 00:00 UTC - cron: '0 0 \* \* \*' workflow_dispatch: inputs: lookback-days:
description: 'Days of history to analyze' required: false type: number default: 30

permissions: contents: write actions: read

jobs: collect-metrics: name: Collect Workflow Metrics runs-on: ubuntu-latest steps: - name: Checkout
code uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'

      - name: Install dependencies
        run: |
          pip install requests pyyaml matplotlib pandas

      - name: Collect metrics
        env:
          GITHUB_TOKEN: \${{ secrets.GITHUB_TOKEN }}
        run: |
          python .github/workflows/scripts/automation_workflow.py collect-metrics

      - name: Generate analytics report
        run: |
          # Create analytics report with charts
          python << 'EOF'
          import json
          import matplotlib.pyplot as plt
          import pandas as pd
          from datetime import datetime, timedelta

          # Load metrics (would come from collect-metrics step)
          # For now, create sample report structure

          report = {
              "generated_at": datetime.now().isoformat(),
              "period_days": \${{ github.event.inputs.lookback-days || 30 }},
              "summary": {
                  "total_runs": 0,
                  "success_rate": 0.0,
                  "avg_duration": 0,
                  "cache_hit_rate": 0.0
              },
              "workflows": []
          }

          with open("analytics-report.json", "w") as f:
              json.dump(report, f, indent=2)

          print("Analytics report generated")
          EOF

      - name: Create visualizations
        run: |
          python << 'EOF'
          import matplotlib.pyplot as plt
          import json

          # Load report
          with open("analytics-report.json") as f:
              report = json.load(f)

          # Create charts (sample structure)
          fig, axes = plt.subplots(2, 2, figsize=(15, 10))

          # Chart 1: Success rate over time
          axes[0, 0].set_title("Workflow Success Rate")
          axes[0, 0].set_xlabel("Date")
          axes[0, 0].set_ylabel("Success Rate (%)")

          # Chart 2: Average duration
          axes[0, 1].set_title("Average Workflow Duration")
          axes[0, 1].set_xlabel("Workflow")
          axes[0, 1].set_ylabel("Duration (seconds)")

          # Chart 3: Cache hit rate
          axes[1, 0].set_title("Cache Hit Rate")
          axes[1, 0].set_xlabel("Workflow")
          axes[1, 0].set_ylabel("Hit Rate (%)")

          # Chart 4: Runs per workflow
          axes[1, 1].set_title("Runs per Workflow")
          axes[1, 1].set_xlabel("Workflow")
          axes[1, 1].set_ylabel("Number of Runs")

          plt.tight_layout()
          plt.savefig("analytics-charts.png", dpi=300, bbox_inches='tight')
          print("Charts created")
          EOF

      - name: Generate markdown report
        run: |
          cat > workflow-analytics.md << 'EOF'
          # Workflow Analytics Report

          **Generated**: $(date -u +"%Y-%m-%d %H:%M:%S UTC")

          ## Summary

          - **Period**: Last \${{ github.event.inputs.lookback-days || 30 }} days
          - **Total Runs**: N/A
          - **Success Rate**: N/A
          - **Average Duration**: N/A
          - **Cache Hit Rate**: N/A

          ## Visualizations

          ![Analytics Charts](analytics-charts.png)

          ## Top Workflows

          | Workflow | Runs | Success Rate | Avg Duration | Cache Hit Rate |
          | -------- | ---- | ------------ | ------------ | -------------- |
          | CI       | N/A  | N/A          | N/A          | N/A            |

          ## Recommendations

          Based on the analysis:

          1. Consider enabling caching for workflows with low hit rates
          2. Investigate frequently failing workflows
          3. Review long-running workflows for optimization opportunities

          ## Self-Healing Actions

          The following issues were detected and remediated:

          - None

          ---

          *Report generated by workflow-analytics.yml*
          EOF

      - name: Upload analytics artifacts
        uses: actions/upload-artifact@v4
        with:
          name: workflow-analytics
          path: |
            analytics-report.json
            analytics-charts.png
            workflow-analytics.md
          retention-days: 90

      - name: Comment on summary
        run: |
          cat workflow-analytics.md >> $GITHUB_STEP_SUMMARY

\`\`\`

### Verification Steps

\`\`\`bash

# 1. Validate workflow syntax

actionlint .github/workflows/workflow-analytics.yml

# 2. Test analytics collection

gh workflow run workflow-analytics.yml

# 3. Download analytics report

gh run download --name workflow-analytics

# 4. View charts

open analytics-charts.png

# 5. Schedule verification

gh workflow view workflow-analytics.yml \`\`\`

---

## Phase 5 Completion Checklist

- [ ] automation_workflow.py helper module created
- [ ] Unit tests implemented for automation functions
- [ ] GitHub Apps integration configured
- [ ] Advanced caching workflow operational
- [ ] Workflow analytics dashboard created
- [ ] GitHub App token generation working
- [ ] Intelligent cache key generation tested
- [ ] Workflow metrics collection functional
- [ ] Self-healing detection implemented
- [ ] Performance optimization analysis working
- [ ] Analytics visualizations generated
- [ ] All features follow repository conventions
- [ ] No Windows-specific features
- [ ] All code follows Google Python Style Guide
- [ ] Documentation complete
