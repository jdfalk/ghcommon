#!/usr/bin/env python3
# file: .github/workflows/scripts/maintenance_workflow.py
# version: 1.0.0
# guid: a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d

"""Maintenance workflow helper for automated repository maintenance."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from workflow_common import (
    append_summary_line,
    format_summary_table,
    log_notice,
)


@dataclass
class DependencyUpdate:
    """Information about a dependency update."""

    name: str
    current_version: str
    latest_version: str
    update_type: str
    breaking: bool
    security: bool
    language: str


@dataclass
class StaleItem:
    """Information about a stale issue or pull request."""

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
    """Information about a security advisory."""

    severity: str
    package: str
    vulnerability: str
    description: str
    fixed_version: str
    advisory_url: str


# --------------------------------------------------------------------------- #
# Version helpers                                                             #
# --------------------------------------------------------------------------- #


def _semver_tuple(version: str) -> tuple[int, int, int]:
    parts = [int(part) for part in re.findall(r"\d+", version)[:3]]
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)


def _classify_update(current: str, latest: str) -> str:
    current_tuple = _semver_tuple(current)
    latest_tuple = _semver_tuple(latest)
    if latest_tuple <= current_tuple:
        return "none"
    if latest_tuple[0] > current_tuple[0]:
        return "major"
    if latest_tuple[1] > current_tuple[1]:
        return "minor"
    return "patch"


# --------------------------------------------------------------------------- #
# Dependency parsers                                                          #
# --------------------------------------------------------------------------- #


def parse_pip_outdated(path: Path) -> list[DependencyUpdate]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8") or "[]")
    updates: list[DependencyUpdate] = []
    for item in data:
        latest = item.get("latest_version") or item.get("latest") or ""
        current = item.get("version") or item.get("installed_version") or ""
        if not latest or not current:
            continue
        update_type = _classify_update(current, latest)
        if update_type == "none":
            continue
        updates.append(
            DependencyUpdate(
                name=item.get("name", "unknown"),
                current_version=current,
                latest_version=latest,
                update_type=update_type,
                breaking=update_type == "major",
                security=bool(item.get("is_security", False)),
                language="python",
            )
        )
    return updates


def parse_npm_outdated(path: Path) -> list[DependencyUpdate]:
    if not path.exists():
        return []
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return []
    data = json.loads(raw)
    updates: list[DependencyUpdate] = []
    for name, info in data.items():
        current = info.get("current") or ""
        latest = info.get("latest") or info.get("wanted") or ""
        if not current or not latest or current == latest:
            continue
        update_type = _classify_update(current, latest)
        updates.append(
            DependencyUpdate(
                name=name,
                current_version=current,
                latest_version=latest,
                update_type=update_type,
                breaking=update_type == "major",
                security=info.get("type") == "security",
                language="node",
            )
        )
    return updates


def parse_cargo_outdated(path: Path) -> list[DependencyUpdate]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8") or "{}")
    packages = data.get("packages") or data.get("Packages") or []
    updates: list[DependencyUpdate] = []
    for item in packages:
        current = item.get("version") or ""
        latest = item.get("latest_version") or item.get("latest") or ""
        if not current or not latest or current == latest:
            continue
        update_type = _classify_update(current, latest)
        updates.append(
            DependencyUpdate(
                name=item.get("name", "unknown"),
                current_version=current,
                latest_version=latest,
                update_type=update_type,
                breaking=update_type == "major",
                security=bool(item.get("is_direct") and item.get("rustsec_vulnerabilities")),
                language="rust",
            )
        )
    return updates


def parse_go_outdated(path: Path) -> list[DependencyUpdate]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    decoder = json.JSONDecoder()
    idx = 0
    updates: list[DependencyUpdate] = []
    while idx < len(text):
        text = text.lstrip()
        if not text:
            break
        try:
            obj, offset = decoder.raw_decode(text[idx:])
            idx += offset
        except json.JSONDecodeError:
            break
        current = obj.get("Version") or ""
        update = obj.get("Update") or {}
        latest = update.get("Version") or ""
        if not current or not latest or current == latest:
            continue
        update_type = _classify_update(current, latest)
        updates.append(
            DependencyUpdate(
                name=obj.get("Path", "unknown"),
                current_version=current,
                latest_version=latest,
                update_type=update_type,
                breaking=update_type == "major",
                security=False,
                language="go",
            )
        )
    return updates


def collect_dependency_updates(
    pip_path: Path,
    npm_path: Path,
    cargo_path: Path,
    go_path: Path,
) -> list[DependencyUpdate]:
    updates: list[DependencyUpdate] = []
    updates.extend(parse_pip_outdated(pip_path))
    updates.extend(parse_npm_outdated(npm_path))
    updates.extend(parse_cargo_outdated(cargo_path))
    updates.extend(parse_go_outdated(go_path))
    return updates


def summarize_dependency_updates(updates: Iterable[DependencyUpdate]) -> str:
    updates = list(updates)
    if not updates:
        return "No dependency updates found."

    updates.sort(key=lambda item: (item.language, item.update_type, item.name))
    rows: list[tuple[str, str]] = []
    for update in updates:
        rows.extend(
            [
                ("Package", update.name),
                (
                    "Current → Latest",
                    f"{update.current_version} → {update.latest_version}",
                ),
                ("Update Type", update.update_type),
                ("Security Fix", "yes" if update.security else "no"),
                ("Language", update.language),
                ("", ""),
            ]
        )
    table = format_summary_table(rows)
    append_summary_line(table)
    return table


def write_dependency_summary(
    updates: Iterable[DependencyUpdate],
    output_path: Path,
) -> None:
    updates = list(updates)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not updates:
        output_path.write_text("No dependency updates found.\n", encoding="utf-8")
        return

    lines = ["# Dependency Updates", ""]
    for update in updates:
        lines.append(
            f"- `{update.language}` **{update.name}**: "
            f"{update.current_version} → {update.latest_version} "
            f"({update.update_type})"
        )
    output_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- #
# Security issue helpers                                                      #
# --------------------------------------------------------------------------- #


def parse_security_issues(path: Path) -> list[SecurityIssue]:
    """Parse security advisories from JSON file."""
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8") or "[]")
    issues: list[SecurityIssue] = []
    for item in data:
        issues.append(
            SecurityIssue(
                severity=item.get("severity", "unknown"),
                package=item.get("package", "unknown"),
                vulnerability=item.get("vulnerability", ""),
                description=item.get("description", ""),
                fixed_version=item.get("fixed_version", ""),
                advisory_url=item.get("advisory_url", ""),
            )
        )
    return issues


def summarize_security_issues(issues: Iterable[SecurityIssue]) -> None:
    """Append security issue summary to GitHub summary."""
    issues = list(issues)
    if not issues:
        append_summary_line("No security advisories detected.")
        return

    rows: list[tuple[str, str]] = []
    severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    issues.sort(
        key=lambda issue: severity_order.get(issue.severity.lower(), 0),
        reverse=True,
    )
    for issue in issues:
        rows.extend(
            [
                ("Package", issue.package),
                ("Severity", issue.severity),
                ("Vulnerability", issue.vulnerability or "n/a"),
                ("Fixed Version", issue.fixed_version or "n/a"),
                ("Advisory", issue.advisory_url or "n/a"),
                ("", ""),
            ]
        )
    append_summary_line(format_summary_table(rows))


# --------------------------------------------------------------------------- #
# Stale item helpers                                                          #
# --------------------------------------------------------------------------- #


def parse_stale_items(data: Iterable[dict[str, Any]], days: int) -> list[StaleItem]:
    threshold = timedelta(days=days)
    items: list[StaleItem] = []
    now = datetime.utcnow()
    for item in data:
        updated_at = datetime.fromisoformat(item["updated_at"])
        created_at = datetime.fromisoformat(item["created_at"])
        delta = now - updated_at
        if delta < threshold:
            continue
        items.append(
            StaleItem(
                number=item["number"],
                title=item.get("title", "no title"),
                type=item.get("type", "issue"),
                created_at=created_at,
                updated_at=updated_at,
                days_stale=delta.days,
                labels=item.get("labels", []),
                assignees=item.get("assignees", []),
            )
        )
    return items


# --------------------------------------------------------------------------- #
# CLI                                                                         #
# --------------------------------------------------------------------------- #


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Maintenance workflow utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    dep_parser = subparsers.add_parser(
        "summarize-dependencies", help="Summarize dependency updates"
    )
    dep_parser.add_argument("--pip", type=Path, default=Path("maintenance/pip-outdated.json"))
    dep_parser.add_argument("--npm", type=Path, default=Path("maintenance/npm-outdated.json"))
    dep_parser.add_argument("--cargo", type=Path, default=Path("maintenance/cargo-outdated.json"))
    dep_parser.add_argument("--go", type=Path, default=Path("maintenance/go-outdated.json"))
    dep_parser.add_argument(
        "--output",
        type=Path,
        default=Path("maintenance/dependency-summary.md"),
    )

    stale_parser = subparsers.add_parser("summarize-stale", help="Summarize stale issues/PRs")
    stale_parser.add_argument("--input", type=Path, required=True)
    stale_parser.add_argument("--days", type=int, default=60)

    security_parser = subparsers.add_parser(
        "summarize-security",
        help="Summarize security advisories from JSON report",
    )
    security_parser.add_argument("--input", type=Path, required=True)

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv or sys.argv[1:])

    if args.command == "summarize-dependencies":
        updates = collect_dependency_updates(args.pip, args.npm, args.cargo, args.go)
        write_dependency_summary(updates, args.output)
        summarize_dependency_updates(updates)
        log_notice(f"Dependency summary written to {args.output}")
        return

    if args.command == "summarize-stale":
        data = json.loads(args.input.read_text(encoding="utf-8") or "[]")
        items = parse_stale_items(data, args.days)
        if not items:
            append_summary_line("No stale issues found.")
            return
        rows = [(f"#{item.number} {item.title}", f"{item.days_stale} days stale") for item in items]
        append_summary_line(format_summary_table(rows))
        return

    if args.command == "summarize-security":
        issues = parse_security_issues(args.input)
        summarize_security_issues(issues)
        return

    raise SystemExit(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
