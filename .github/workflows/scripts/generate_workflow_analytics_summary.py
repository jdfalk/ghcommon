#!/usr/bin/env python3
# file: .github/workflows/scripts/generate_workflow_analytics_summary.py
# version: 1.0.0
# guid: a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d

"""Generate workflow analytics summary from collected metrics."""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def pct(value: float) -> str:
    return f"{value * 100:.1f}%" if isinstance(value, (float, int)) else "N/A"


def format_top_workflows(workflows: dict[str, Any], limit: int = 5) -> list[str]:
    lines: list[str] = []
    top = sorted(workflows.items(), key=lambda item: item[1].get("runs", 0), reverse=True)[:limit]
    if top:
        lines.append("| Workflow | Runs | Success Rate | Avg Duration | Cache Hit Rate |")
        lines.append("| --- | --- | --- | --- | --- |")
        for name, data in top:
            cache_hit = data.get("cache_hit_rate")
            cache_text = pct(cache_hit) if isinstance(cache_hit, (float, int)) else "N/A"
            success = pct(data.get("success_rate", 0.0))
            duration = f"{data.get('average_duration', 0.0):.1f} s"
            lines.append(
                f"| {name} | {data.get('runs', 0)} | {success} | {duration} | {cache_text} |"
            )
    else:
        lines.append("No workflow runs found in the selected window.")
    return lines


def build_summary(report: dict[str, Any]) -> list[str]:
    metrics = report.get("metrics", {})
    workflows = metrics.get("workflows", {})
    self_healing = report.get("self_healing_actions", [])

    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "# Workflow Analytics Report",
        "",
        f"**Generated**: {generated}",
        "",
        "## Summary",
        "",
        f"- **Total Runs**: {metrics.get('total_runs', 0)}",
        f"- **Success Rate**: {pct(metrics.get('success_rate', 0.0))}",
        f"- **Average Duration**: {metrics.get('average_duration', 0.0):.1f} s",
        "",
        "## Top Workflows",
        "",
    ]

    lines.extend(format_top_workflows(workflows))
    lines.extend(["", "## Self-Healing Actions", ""])
    if self_healing:
        for action in self_healing:
            severity = action.get("severity", "info").upper()
            slug = action.get("slug", "unknown")
            description = action.get("description", "")
            lines.append(f"- **{severity}** `{slug}` – {description}")
    else:
        lines.append("- None")
    return lines


def write_summary(lines: Iterable[str], output_path: Path) -> None:
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    report_path = Path("analytics-report.json")
    output_path = Path("workflow-analytics.md")

    report = json.loads(report_path.read_text(encoding="utf-8"))
    summary_lines = build_summary(report)
    write_summary(summary_lines, output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
