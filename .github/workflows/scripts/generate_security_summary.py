#!/usr/bin/env python3
# file: .github/workflows/scripts/generate_security_summary.py
# version: 1.0.0
# guid: e1f2a3b4-c5d6-47e8-9f10-1a2b3c4d5e6f

"""Generate security scan summary for GitHub Actions."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def build_results(env: dict[str, str | None]) -> dict[str, str]:
    """Build results mapping from environment values."""
    return {
        "CodeQL Analysis": env.get("RESULT_CODEQL", "skipped") or "skipped",
        "Dependency Review": env.get("RESULT_DEP_REVIEW", "skipped") or "skipped",
        "Security Audit": env.get("RESULT_SECURITY_AUDIT", "skipped") or "skipped",
        "Trivy Scan": env.get("RESULT_TRIVY", "skipped") or "skipped",
    }


def generate_summary(results: dict[str, str]) -> tuple[list[str], bool]:
    """Generate summary lines and return whether a warning is required."""
    summary_lines = [
        "## Security Scan Summary",
        "",
        "| Scan Type | Status |",
        "|-----------|--------|",
    ]

    for label, status in results.items():
        summary_lines.append(f"| {label} | {status} |")

    warning_required = any(status == "failure" for status in results.values())
    summary_lines.append("")
    if warning_required:
        summary_lines.append("⚠️ **Security issues detected. Please review the scan results.**")
    else:
        summary_lines.append("✅ **All security scans passed.**")

    return summary_lines, warning_required


def main() -> int:
    results = build_results(os.environ)
    summary_lines, warning_required = generate_summary(results)

    summary_path = Path(os.environ["GITHUB_STEP_SUMMARY"])
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    return 1 if warning_required else 0


if __name__ == "__main__":
    sys.exit(main())
