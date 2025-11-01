#!/usr/bin/env python3
"""Detect override directives in recent commit messages and surface CI toggles."""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys

PATTERNS = {
    "skip-tests": re.compile(
        r"\[(?:skip|no)[^\]]*tests?\]|skip.?tests?|no.?tests?", re.IGNORECASE
    ),
    "skip-validation": re.compile(
        r"\[(?:skip|no)[^\]]*(?:validation|lint)\]|skip.?validation|no.?validation|skip.?lint|no.?lint",
        re.IGNORECASE,
    ),
    "skip-ci": re.compile(
        r"\[(?:skip.?ci|ci.?skip|skip.?actions)\]|skip.?ci|ci.?skip",
        re.IGNORECASE,
    ),
    "skip-build": re.compile(
        r"\[(?:skip|no)[^\]]*build\]|skip.?build|no.?build", re.IGNORECASE
    ),
}


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


def gather_commits(event_name: str, base_branch: str) -> list[str]:
    if event_name == "pull_request":
        commit_range = f"origin/{base_branch}..HEAD"
        try:
            output = run_git(["log", "--pretty=format:%s", commit_range])
            if output:
                return output.splitlines()
        except subprocess.CalledProcessError:
            pass

        print(
            f"⚠️  Unable to compute commit range {commit_range}. Falling back to last 20 commits on HEAD.",
            file=sys.stdout,
        )
        output = run_git(["log", "--pretty=format:%s", "-n", "20"])
        return output.splitlines()

    output = run_git(["log", "--pretty=format:%s", "-n", "1"])
    return output.splitlines()


def detect_overrides(messages: list[str]) -> dict[str, bool]:
    joined = "\n".join(messages)
    return {
        key: bool(pattern.search(joined)) for key, pattern in PATTERNS.items()
    }


def write_outputs(overrides: dict[str, bool], messages: list[str]) -> None:
    gh_output = Path(os.environ["GITHUB_OUTPUT"])
    with gh_output.open("a", encoding="utf-8") as handle:
        for key, value in overrides.items():
            handle.write(f"{key}={'true' if value else 'false'}\n")
        handle.write("commit-message<<EOF\n")
        handle.write("\n".join(messages))
        handle.write("\nEOF\n")


def format_summary(overrides: dict[str, bool], messages: list[str]) -> str:
    lines = [
        "## 🔍 Commit Override Analysis",
        "",
        "| Override Type | Status |",
        "|---------------|--------|",
        f"| Skip Tests | {'true' if overrides['skip-tests'] else 'false'} |",
        f"| Skip Validation | {'true' if overrides['skip-validation'] else 'false'} |",
        f"| Skip CI | {'true' if overrides['skip-ci'] else 'false'} |",
        f"| Skip Build | {'true' if overrides['skip-build'] else 'false'} |",
        "",
    ]

    if any(overrides.values()):
        lines.extend(
            [
                "⚠️ **Warning**: Some CI checks have been disabled via commit message overrides.",
                "",
                "**Commit Messages Analyzed:**",
                "```",
                *messages,
                "```",
                "",
            ]
        )
    else:
        lines.append(
            "✅ **All CI checks enabled** - No override keywords detected.\n"
        )

    return "\n".join(lines)


def append_summary(content: str) -> None:
    summary_path = Path(os.environ["GITHUB_STEP_SUMMARY"])
    with summary_path.open("a", encoding="utf-8") as handle:
        handle.write(content)


def main() -> None:
    event_name = os.environ.get("EVENT_NAME", "").strip() or "push"
    default_branch = os.environ.get("DEFAULT_BRANCH", "main")
    base_ref = os.environ.get("PULL_BASE_REF", "").strip()
    base_branch = (
        base_ref if base_ref and base_ref != "null" else default_branch
    )

    print("Checking commit messages for override keywords...")
    messages = gather_commits(event_name, base_branch)
    print("Commit messages to check:")
    for message in messages:
        print(message)
    print()

    overrides = detect_overrides(messages)
    write_outputs(overrides, messages)
    append_summary(format_summary(overrides, messages))


if __name__ == "__main__":
    main()
