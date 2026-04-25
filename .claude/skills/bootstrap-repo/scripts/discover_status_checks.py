#!/usr/bin/env python3
"""Discover required-status-check contexts from a repo's workflows directory.

Outputs newline-separated job IDs from any workflow that triggers on
`pull_request` (or `pull_request_target`). Used by apply_branch_protection.sh
to populate `required_status_checks.contexts`.

Usage:
    discover_status_checks.py <workflows_dir>

Example:
    discover_status_checks.py .github/workflows/

See references/branch-protection.md for the matrix-job caveat.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

PR_TRIGGERS = {"pull_request", "pull_request_target"}


def has_pr_trigger(on_block) -> bool:
    """Return True if a workflow's `on:` block triggers on a PR event."""
    if isinstance(on_block, str):
        return on_block in PR_TRIGGERS
    if isinstance(on_block, list):
        return any(t in PR_TRIGGERS for t in on_block)
    if isinstance(on_block, dict):
        return any(t in PR_TRIGGERS for t in on_block)
    return False


def collect_job_ids(workflows_dir: Path) -> list[str]:
    """Walk *.yml and *.yaml in workflows_dir, return sorted job IDs."""
    job_ids: set[str] = set()
    for path in sorted(workflows_dir.glob("*.y*ml")):
        try:
            with path.open() as f:
                doc = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"warning: skipping {path.name}: {e}", file=sys.stderr)
            continue
        if not isinstance(doc, dict):
            continue
        # PyYAML parses the bare key `on` as Python True (boolean). Handle both.
        on_block = doc.get("on", doc.get(True))
        if not has_pr_trigger(on_block):
            continue
        jobs = doc.get("jobs") or {}
        if isinstance(jobs, dict):
            job_ids.update(jobs.keys())
    return sorted(job_ids)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {argv[0]} <workflows_dir>", file=sys.stderr)
        return 2
    workflows_dir = Path(argv[1])
    if not workflows_dir.is_dir():
        print(f"error: not a directory: {workflows_dir}", file=sys.stderr)
        return 1
    for jid in collect_job_ids(workflows_dir):
        print(jid)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
