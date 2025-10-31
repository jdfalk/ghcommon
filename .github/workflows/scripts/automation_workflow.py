#!/usr/bin/env python3
# file: .github/workflows/scripts/automation_workflow.py
# version: 1.1.0
# guid: b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e

"""Advanced automation workflow helper.

This module provides utilities for GitHub Apps integration, intelligent caching,
performance optimization, workflow analytics, and self-healing capabilities.

The API is intentionally modular so GitHub Actions steps and reusable workflow
helpers can compose the pieces they need without relying on shell scripts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Final

import jwt
import requests

import workflow_common

DEFAULT_CACHE_RESTORE_SLICES: Final[tuple[int, ...]] = (32, 24, 16)
DEFAULT_GITHUB_API_URL: Final[str] = "https://api.github.com"


@dataclass(slots=True)
class CacheStrategy:
    """Represents the cache key and related metadata."""

    key: str
    restore_keys: tuple[str, ...] = tuple()
    metadata: dict[str, Any] = field(default_factory=dict)
    paths: tuple[str, ...] = tuple()

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable representation."""
        return {
            "key": self.key,
            "restore_keys": list(self.restore_keys),
            "metadata": self.metadata,
            "paths": list(self.paths),
        }


@dataclass(slots=True)
class WorkflowRun:
    """Normalized information about a workflow run."""

    workflow: str
    status: str
    conclusion: str
    started_at: datetime | None
    completed_at: datetime | None
    duration_seconds: float
    cache_hit: bool | None = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "WorkflowRun":
        """Normalise raw workflow run data."""
        workflow = str(
            data.get("name")
            or data.get("workflow_name")
            or data.get("workflow")
            or "unknown"
        )
        status = str(data.get("status", "completed")).lower()
        conclusion = str(data.get("conclusion", status)).lower()
        started_at = _parse_datetime(
            data.get("run_started_at") or data.get("started_at")
        )
        completed_at = _parse_datetime(
            data.get("updated_at") or data.get("completed_at")
        )
        duration_seconds = _resolve_duration_seconds(data, started_at, completed_at)
        cache_hit: bool | None = None
        cache_info = data.get("cache")
        if isinstance(cache_info, Mapping):
            cache_hit = _coerce_bool(cache_info.get("hit"))
        elif "cache_hit" in data:
            cache_hit = _coerce_bool(data.get("cache_hit"))
        return cls(
            workflow=workflow,
            status=status,
            conclusion=conclusion,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration_seconds,
            cache_hit=cache_hit,
        )

    @property
    def succeeded(self) -> bool:
        """Return True if the run finished successfully."""
        return self.conclusion == "success"

    @property
    def failed(self) -> bool:
        """Return True if the run concluded with a failure."""
        return self.conclusion in {"failure", "timed_out", "cancelled"}


@dataclass(slots=True)
class WorkflowSummary:
    """Aggregate metrics for a single workflow."""

    name: str
    runs: int
    successes: int
    failures: int
    average_duration: float
    cache_hit_rate: float | None
    consecutive_failures: int
    last_run: WorkflowRun | None

    @property
    def success_rate(self) -> float:
        """Return success ratio for this workflow."""
        if self.runs == 0:
            return 0.0
        return self.successes / self.runs


@dataclass(slots=True)
class WorkflowMetrics:
    """Aggregate metrics across all workflows."""

    total_runs: int
    success_rate: float
    average_duration: float
    workflows: dict[str, WorkflowSummary]
    start_time: datetime | None
    end_time: datetime | None
    runs: tuple[WorkflowRun, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return metrics in a serialisable structure."""
        return {
            "total_runs": self.total_runs,
            "success_rate": self.success_rate,
            "average_duration": self.average_duration,
            "start_time": _datetime_to_str(self.start_time),
            "end_time": _datetime_to_str(self.end_time),
            "workflows": {
                name: {
                    "runs": summary.runs,
                    "successes": summary.successes,
                    "failures": summary.failures,
                    "average_duration": summary.average_duration,
                    "success_rate": summary.success_rate,
                    "cache_hit_rate": summary.cache_hit_rate,
                    "consecutive_failures": summary.consecutive_failures,
                    "last_run": _serialize_run(summary.last_run),
                }
                for name, summary in self.workflows.items()
            },
        }


@dataclass(slots=True)
class SelfHealingAction:
    """Represents a recommended remediation step."""

    slug: str
    description: str
    severity: str = "info"

    def to_dict(self) -> dict[str, str]:
        """Return a simple dict representation."""
        return {
            "slug": self.slug,
            "description": self.description,
            "severity": self.severity,
        }


def build_app_jwt(
    app_id: int | str,
    private_key: str,
    expires_in: int = 600,
    now: datetime | None = None,
) -> str:
    """Return a signed JWT for GitHub App authentication.

    Args:
        app_id: GitHub App identifier.
        private_key: PEM encoded private key for the GitHub App.
        expires_in: Lifetime in seconds (between 60 and 600).
        now: Optional override for current time (UTC).
    """
    if expires_in < 60 or expires_in > 10 * 60:
        msg = "expires_in must be between 60 and 600 seconds"
        raise ValueError(msg)

    issued_at = now or datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(seconds=expires_in)
    payload = {
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
        "iss": str(app_id),
    }
    token = jwt.encode(payload, private_key, algorithm="RS256")
    return token if isinstance(token, str) else token.decode("utf-8")


def get_installation_access_token(
    app_id: int | str,
    private_key: str,
    installation_id: int | str,
    *,
    api_url: str = DEFAULT_GITHUB_API_URL,
    session: requests.Session | None = None,
    expires_in: int = 600,
) -> dict[str, Any]:
    """Return an installation access token for the GitHub App."""
    token = build_app_jwt(app_id, private_key, expires_in=expires_in)
    url = f"{api_url.rstrip('/')}/app/installations/{installation_id}/access_tokens"
    client = session or requests.Session()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    response = client.post(url, headers=headers)
    if response.status_code != 201:
        workflow_common.log_error(
            f"Failed to obtain installation token (status={response.status_code})",
        )
        response.raise_for_status()
    return response.json()


def fingerprint_paths(paths: Sequence[str | os.PathLike[str]]) -> dict[str, str]:
    """Return SHA256 fingerprints for files/directories."""
    fingerprints: dict[str, str] = {}
    for raw_path in paths:
        path = Path(raw_path).expanduser()
        identifier = str(path)
        if path.is_file():
            fingerprints[identifier] = _hash_file(path)
        elif path.is_dir():
            fingerprints[identifier] = _hash_directory(path)
        else:
            fingerprints[identifier] = "missing"
    return fingerprints


def generate_cache_strategy(
    prefix: str,
    paths: Sequence[str | os.PathLike[str]],
    *,
    namespace: str | None = None,
    extras: Mapping[str, Any] | None = None,
    restore_slices: Sequence[int] = DEFAULT_CACHE_RESTORE_SLICES,
    cache_paths: Sequence[str | os.PathLike[str]] = (),
) -> CacheStrategy:
    """Generate a deterministic cache key based on file fingerprints."""
    fingerprints = fingerprint_paths(paths)
    digest = hashlib.sha256()
    digest.update(prefix.encode("utf-8"))
    if namespace:
        digest.update(namespace.encode("utf-8"))
    if extras:
        for key in sorted(extras):
            digest.update(str(key).encode("utf-8"))
            digest.update(str(extras[key]).encode("utf-8"))
    for path, fingerprint in sorted(fingerprints.items()):
        digest.update(path.encode("utf-8"))
        digest.update(fingerprint.encode("utf-8"))
    full_hash = digest.hexdigest()
    restore_keys = tuple(
        f"{prefix}-{full_hash[:length]}"
        for length in restore_slices
        if 0 < length <= len(full_hash)
    )
    norm_cache_paths = tuple(str(Path(item).expanduser()) for item in cache_paths)
    metadata = {
        "prefix": prefix,
        "namespace": namespace or "",
        "extras": dict(extras or {}),
        "fingerprints": fingerprints,
        "generated_at": _datetime_to_str(datetime.now(timezone.utc)),
    }
    if norm_cache_paths:
        metadata["paths"] = list(norm_cache_paths)
    return CacheStrategy(
        key=f"{prefix}-{full_hash}",
        restore_keys=restore_keys,
        metadata=metadata,
        paths=norm_cache_paths,
    )


def collect_workflow_metrics(
    runs_data: Sequence[Mapping[str, Any]],
) -> WorkflowMetrics:
    """Aggregate workflow run information into metrics."""
    runs = tuple(WorkflowRun.from_dict(data) for data in runs_data)
    if not runs:
        return WorkflowMetrics(
            total_runs=0,
            success_rate=0.0,
            average_duration=0.0,
            workflows={},
            start_time=None,
            end_time=None,
            runs=tuple(),
        )

    runs_by_workflow: dict[str, list[WorkflowRun]] = defaultdict(list)
    for run in runs:
        runs_by_workflow[run.workflow].append(run)

    workflow_summaries: dict[str, WorkflowSummary] = {}
    overall_duration = 0.0
    overall_success = 0
    timestamps: list[datetime] = []

    for name, workflow_runs in runs_by_workflow.items():
        sorted_runs = sorted(
            workflow_runs,
            key=lambda item: item.started_at or item.completed_at or datetime.now(timezone.utc),
        )
        runs_count = len(sorted_runs)
        successes = sum(1 for item in sorted_runs if item.succeeded)
        failures = sum(1 for item in sorted_runs if item.failed)
        duration_sum = sum(item.duration_seconds for item in sorted_runs)
        overall_duration += duration_sum
        overall_success += successes
        cache_hits = [item.cache_hit for item in sorted_runs if item.cache_hit is not None]
        cache_hit_rate = (
            sum(1 for hit in cache_hits if hit) / len(cache_hits) if cache_hits else None
        )
        consecutive_failures = _calculate_consecutive_failures(sorted_runs)
        last_run = sorted_runs[-1] if sorted_runs else None
        for item in sorted_runs:
            if item.started_at:
                timestamps.append(item.started_at)
            if item.completed_at:
                timestamps.append(item.completed_at)
        workflow_summaries[name] = WorkflowSummary(
            name=name,
            runs=runs_count,
            successes=successes,
            failures=failures,
            average_duration=duration_sum / runs_count if runs_count else 0.0,
            cache_hit_rate=cache_hit_rate,
            consecutive_failures=consecutive_failures,
            last_run=last_run,
        )

    total_runs = len(runs)
    success_rate = overall_success / total_runs if total_runs else 0.0
    average_duration = overall_duration / total_runs if total_runs else 0.0
    timestamps.sort()
    start_time = timestamps[0] if timestamps else None
    end_time = timestamps[-1] if timestamps else None
    return WorkflowMetrics(
        total_runs=total_runs,
        success_rate=success_rate,
        average_duration=average_duration,
        workflows=workflow_summaries,
        start_time=start_time,
        end_time=end_time,
        runs=runs,
    )


def detect_self_healing_actions(
    metrics: WorkflowMetrics,
    *,
    overall_threshold: float = 0.9,
    failure_streak_threshold: int = 3,
    min_runs_for_success_rate: int = 5,
    cache_hit_threshold: float = 0.5,
) -> list[SelfHealingAction]:
    """Return recommended remediation steps based on metrics."""
    actions: list[SelfHealingAction] = []

    if (
        metrics.total_runs >= min_runs_for_success_rate
        and metrics.success_rate < overall_threshold
    ):
        severity = "high" if metrics.success_rate < overall_threshold / 2 else "medium"
        actions.append(
            SelfHealingAction(
                slug="global-success-rate",
                description=(
                    f"Success rate dropped to {metrics.success_rate:.0%}. "
                    "Recommend enabling automatic retries and notifying maintainers."
                ),
                severity=severity,
            )
        )

    for name, summary in metrics.workflows.items():
        if summary.consecutive_failures >= failure_streak_threshold:
            actions.append(
                SelfHealingAction(
                    slug=f"{name}-failure-streak",
                    description=(
                        f"{name} has {summary.consecutive_failures} consecutive failures. "
                        "Trigger fallback workflow or open an incident ticket."
                    ),
                    severity="high",
                )
            )
        if (
            summary.cache_hit_rate is not None
            and summary.cache_hit_rate < cache_hit_threshold
        ):
            actions.append(
                SelfHealingAction(
                    slug=f"{name}-cache-optimization",
                    description=(
                        f"{name} cache hit rate is {summary.cache_hit_rate:.0%}. "
                        "Recommend refreshing caches or widening restore keys."
                    ),
                    severity="medium",
                )
            )
    return actions


def fetch_recent_workflow_runs(
    repo: str,
    *,
    token: str,
    per_page: int = 30,
    pages: int = 1,
    base_url: str = DEFAULT_GITHUB_API_URL,
    session: requests.Session | None = None,
) -> list[dict[str, Any]]:
    """Fetch workflow run data from the GitHub REST API."""
    if per_page <= 0 or per_page > 100:
        msg = "per_page must be between 1 and 100"
        raise ValueError(msg)
    if pages <= 0:
        msg = "pages must be a positive integer"
        raise ValueError(msg)

    url = f"{base_url.rstrip('/')}/repos/{repo}/actions/runs"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    client = session or requests.Session()
    runs: list[dict[str, Any]] = []
    for page in range(1, pages + 1):
        response = client.get(
            url,
            headers=headers,
            params={"per_page": per_page, "page": page},
            timeout=30,
        )
        if response.status_code != 200:
            workflow_common.log_warning(
                f"Unable to fetch workflow runs (status={response.status_code}, page={page})",
            )
            break
        payload = response.json()
        runs.extend(payload.get("workflow_runs", []))
        if len(payload.get("workflow_runs", [])) < per_page:
            break
    return runs


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hash_directory(path: Path) -> str:
    digest = hashlib.sha256()
    for child in sorted(path.rglob("*")):
        if child.is_file():
            digest.update(child.name.encode("utf-8"))
            digest.update(_hash_file(child).encode("utf-8"))
    return digest.hexdigest()


def filter_runs_by_lookback(
    runs_data: Sequence[Mapping[str, Any]],
    lookback_days: int,
    *,
    now: datetime | None = None,
) -> list[Mapping[str, Any]]:
    """Limit workflow run payloads to those within lookback window."""
    if lookback_days <= 0:
        return list(runs_data)
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(days=lookback_days)
    filtered: list[Mapping[str, Any]] = []
    for item in runs_data:
        timestamp = _parse_datetime(
            item.get("run_started_at")
            or item.get("started_at")
            or item.get("created_at")
            or item.get("updated_at"),
        )
        if timestamp is None or timestamp >= cutoff:
            filtered.append(item)
    return filtered


def _current_branch() -> str | None:
    ref_name = os.environ.get("GITHUB_REF_NAME")
    if ref_name:
        return ref_name
    ref = os.environ.get("GITHUB_REF")
    if ref and ref.startswith("refs/heads/"):
        return ref.split("/", 2)[-1]
    return None


def _sanitize_branch(value: str) -> str:
    sanitized = "".join(ch if ch.isalnum() else "-" for ch in value.strip())
    sanitized = sanitized.strip("-") or "unknown"
    while "--" in sanitized:
        sanitized = sanitized.replace("--", "-")
    return sanitized.lower()


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    return None


def _resolve_duration_seconds(
    data: Mapping[str, Any],
    started_at: datetime | None,
    completed_at: datetime | None,
) -> float:
    if "duration_seconds" in data:
        return float(data["duration_seconds"])
    if "run_duration_ms" in data:
        return float(data["run_duration_ms"]) / 1000.0
    if started_at and completed_at:
        return max((completed_at - started_at).total_seconds(), 0.0)
    return 0.0


def _calculate_consecutive_failures(runs: Sequence[WorkflowRun]) -> int:
    streak = 0
    for run in reversed(runs):
        if run.failed:
            streak += 1
        else:
            break
    return streak


def _coerce_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    if isinstance(value, (int, float)):
        return bool(value)
    return None


def _datetime_to_str(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _serialize_run(run: WorkflowRun | None) -> dict[str, Any] | None:
    if run is None:
        return None
    return {
        "workflow": run.workflow,
        "status": run.status,
        "conclusion": run.conclusion,
        "started_at": _datetime_to_str(run.started_at),
        "completed_at": _datetime_to_str(run.completed_at),
        "duration_seconds": run.duration_seconds,
        "cache_hit": run.cache_hit,
    }


def _load_runs_from_file(path: str | os.PathLike[str]) -> list[dict[str, Any]]:
    raw = Path(path).read_text(encoding="utf-8")
    payload = json.loads(raw)
    if isinstance(payload, Mapping):
        return list(payload.get("workflow_runs", []))
    if isinstance(payload, list):
        return list(payload)
    msg = "Input JSON must be a list or object containing workflow_runs"
    raise ValueError(msg)


def _write_json(path: str | os.PathLike[str], data: Mapping[str, Any]) -> None:
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _create_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Utilities for advanced workflow automation.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    app_parser = subparsers.add_parser(
        "github-app-token",
        help="Generate a GitHub App JWT.",
    )
    app_parser.add_argument("--app-id", required=True, help="GitHub App id.")
    app_parser.add_argument(
        "--private-key-file",
        required=True,
        help="Path to PEM encoded private key.",
    )
    app_parser.add_argument(
        "--expires-in",
        type=int,
        default=600,
        help="Token lifetime in seconds (default: 600).",
    )

    cache_parser = subparsers.add_parser(
        "cache-key",
        help="Generate a cache key from file fingerprints.",
    )
    cache_parser.add_argument("--prefix", required=True, help="Cache key prefix.")
    cache_parser.add_argument(
        "--files",
        required=True,
        help="Comma separated list of files or directories.",
    )
    cache_parser.add_argument(
        "--namespace",
        help="Optional namespace component for the cache key.",
    )
    cache_parser.add_argument(
        "--paths",
        help="Comma separated cache paths to return for actions/cache.",
    )
    cache_parser.add_argument(
        "--include-branch",
        action="store_true",
        help="Include current branch name in the cache key prefix.",
    )

    metrics_parser = subparsers.add_parser(
        "collect-metrics",
        help="Collect workflow metrics from JSON or GitHub API.",
    )
    metrics_parser.add_argument(
        "--input",
        help="Path to JSON file containing workflow run payloads.",
    )
    metrics_parser.add_argument(
        "--repo",
        help="owner/name of repository when fetching from GitHub API.",
    )
    metrics_parser.add_argument(
        "--token",
        help="GitHub token used when fetching from the API.",
    )
    metrics_parser.add_argument(
        "--output",
        help="Optional path to write metrics JSON.",
    )
    metrics_parser.add_argument(
        "--per-page",
        type=int,
        default=30,
        help="Number of runs to fetch per page (API mode).",
    )
    metrics_parser.add_argument(
        "--pages",
        type=int,
        default=1,
        help="Number of pages to fetch (API mode).",
    )
    metrics_parser.add_argument(
        "--lookback-days",
        type=int,
        help="Only include workflow runs from the last N days.",
    )
    return parser


def _handle_github_app_token(args: argparse.Namespace) -> int:
    private_key = Path(args.private_key_file).read_text(encoding="utf-8")
    token = build_app_jwt(args.app_id, private_key, expires_in=args.expires_in)
    print(token)
    return 0


def _handle_cache_key(args: argparse.Namespace) -> int:
    files = [item.strip() for item in args.files.split(",") if item.strip()]
    cache_paths = []
    if args.paths:
        cache_paths = [item.strip() for item in args.paths.split(",") if item.strip()]
    extras: dict[str, Any] = {}
    prefix = args.prefix
    branch_value: str | None = None
    if args.include_branch:
        branch_value = _current_branch()
        if branch_value:
            sanitized_branch = _sanitize_branch(branch_value)
            prefix = f"{prefix}-{sanitized_branch}"
            extras["branch"] = sanitized_branch
        else:
            workflow_common.log_warning(
                "include-branch flag set but branch could not be detected; proceeding without it",
            )
    strategy = generate_cache_strategy(
        prefix,
        files,
        namespace=args.namespace,
        extras=extras or None,
        cache_paths=cache_paths,
    )
    payload = strategy.to_dict()
    if branch_value:
        payload["branch"] = _sanitize_branch(branch_value)

    workflow_common.write_output("cache-key", strategy.key)
    workflow_common.write_output("restore-keys", "\n".join(strategy.restore_keys))
    workflow_common.write_output("cache-metadata", json.dumps(payload["metadata"]))
    if strategy.paths:
        workflow_common.write_output("cache-paths", "\n".join(strategy.paths))
    if branch_value:
        workflow_common.write_output("cache-branch", _sanitize_branch(branch_value))

    print(json.dumps(payload, indent=2))
    return 0


def _handle_collect_metrics(args: argparse.Namespace) -> int:
    if args.input:
        runs = _load_runs_from_file(args.input)
    else:
        if not args.repo or not args.token:
            msg = "--repo and --token are required when --input is not provided"
            raise ValueError(msg)
        runs = fetch_recent_workflow_runs(
            args.repo,
            token=args.token,
            per_page=args.per_page,
            pages=args.pages,
        )
    if args.lookback_days:
        runs = filter_runs_by_lookback(runs, args.lookback_days)
    metrics = collect_workflow_metrics(runs)
    payload = {
        "metrics": metrics.to_dict(),
        "self_healing_actions": [action.to_dict() for action in detect_self_healing_actions(metrics)],
    }
    if args.output:
        _write_json(args.output, payload)
    print(json.dumps(payload, indent=2))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for CLI usage."""
    parser = _create_arg_parser()
    args = parser.parse_args(argv)
    if args.command == "github-app-token":
        return _handle_github_app_token(args)
    if args.command == "cache-key":
        return _handle_cache_key(args)
    if args.command == "collect-metrics":
        return _handle_collect_metrics(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
