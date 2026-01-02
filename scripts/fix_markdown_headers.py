#!/usr/bin/env python3
# file: scripts/fix_markdown_headers.py
# version: 1.0.3
# guid: 2f6a7b8c-1d2e-4f3a-9b5c-6d7e8f9a0b1c

"""Find and fix markdown header metadata that uses heading syntax instead of comments.

This script scans all git repositories under ~/repos/github.com/jdfalk for markdown
files whose metadata headers are written with leading '#' (e.g., '# file: ...').
It converts those headers to HTML comments, bumps the version patch, removes
markdownlint MD025 disable markers, and can optionally create a branch, commit,
push, and open a PR for each affected repository.

Usage:
    python scripts/fix_markdown_headers.py --apply   # apply fixes and open PRs
    python scripts/fix_markdown_headers.py           # dry run (report only)
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path.home() / "repos" / "github.com" / "jdfalk"
HEADER_KEYS = ("file", "version", "guid")
MDLINT_DISABLE_PATTERN = re.compile(r"markdownlint-(disable|enable).*MD025", re.IGNORECASE)
VERSION_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")


@dataclass
class FileIssue:
    path: Path
    original_header: list[str]
    new_header: list[str]


@dataclass
class RepoResult:
    repo_path: Path
    issues: list[FileIssue]
    branch: str | None = None
    base_branch: str | None = None
    pr_url: str | None = None


def bump_patch(version: str) -> str:
    match = VERSION_RE.fullmatch(version.strip())
    if not match:
        return version
    major, minor, patch = map(int, match.groups())
    return f"{major}.{minor}.{patch + 1}"


def normalize_header(lines: list[str]) -> tuple[list[str], bool]:
    """Convert leading '#' metadata to HTML comments and remove MD025 disables."""
    changed = False
    output: list[str] = []
    idx = 0

    # Remove markdownlint MD025 disable/enable lines
    filtered = [ln for ln in lines if not MDLINT_DISABLE_PATTERN.search(ln)]
    if len(filtered) != len(lines):
        changed = True
    lines = filtered

    # Normalize top header block
    header: dict[str, str] = {}
    while idx < len(lines):
        stripped = lines[idx].strip()
        if stripped.startswith("# "):
            content = stripped.lstrip("#").strip()
            if ":" in content:
                key, val = content.split(":", 1)
                header[key.strip().lower()] = val.strip()
                changed = True
                idx += 1
                continue
        break

    if header and all(k in header for k in HEADER_KEYS):
        header["version"] = bump_patch(header["version"])
        output.extend([f"<!-- {k}: {header[k]} -->\n" for k in HEADER_KEYS])
        # skip over consumed lines
        lines = lines[idx:]
    else:
        # no conversion; keep original
        output.extend(lines[:idx])
        lines = lines[idx:]

    output.extend(lines)
    return output, changed


def iter_repos(base_dir: Path) -> Iterable[Path]:
    for child in sorted(base_dir.iterdir()):
        if child.is_dir() and (child / ".git").exists():
            yield child


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)


def run_precommit_if_present(repo: Path) -> None:
    """Run pre-commit if config exists in the repo."""
    if not (repo / ".pre-commit-config.yaml").exists():
        return
    try:
        run(["pre-commit", "run", "-av"], repo)
    except subprocess.CalledProcessError as err:
        stdout = err.stdout.strip() if err.stdout else ""
        stderr = err.stderr.strip() if err.stderr else ""
        message = stdout or stderr or "pre-commit failed"
        print(f"[WARN] pre-commit failed in {repo.name}: {message}")


def process_repo(repo: Path, apply: bool) -> RepoResult:
    issues: list[FileIssue] = []
    for md_file in repo.rglob("*.md"):
        if ".git" in md_file.parts or "node_modules" in md_file.parts or "target" in md_file.parts:
            continue
        content = md_file.read_text(encoding="utf-8").splitlines(keepends=True)
        new_content, changed = normalize_header(content)
        if changed:
            issues.append(
                FileIssue(
                    path=md_file,
                    original_header=content[:6],
                    new_header=new_content[:6],
                )
            )
            if apply:
                md_file.write_text("".join(new_content), encoding="utf-8")

    result = RepoResult(repo_path=repo, issues=issues)
    if apply and issues:
        base_branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo).stdout.strip()
        branch_name = (
            f"fix/markdown-headers-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d%H%M%S')}"
        )
        run(["git", "checkout", "-b", branch_name], repo)
        run(["git", "add"] + [str(i.path.relative_to(repo)) for i in issues], repo)
        run_precommit_if_present(repo)
        run(["git", "commit", "-m", "docs(markdown): normalize metadata headers"], repo)
        run(["git", "push", "-u", "origin", branch_name], repo)

        pr_body = "Normalize markdown metadata headers to HTML comments and remove MD025 disables."
        pr_title = "docs: normalize markdown headers"
        pr = run(
            [
                "gh",
                "pr",
                "create",
                "--title",
                pr_title,
                "--body",
                pr_body,
                "--base",
                base_branch,
            ],
            repo,
        )
        result.branch = branch_name
        result.base_branch = base_branch
        result.pr_url = pr.stdout.strip()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Fix markdown metadata headers across repos.")
    parser.add_argument("--base-dir", type=Path, default=BASE_DIR, help="Root containing repos")
    parser.add_argument(
        "--apply", action="store_true", help="Apply fixes, commit, push, and open PRs"
    )
    args = parser.parse_args()

    summary: list[dict] = []
    for repo in iter_repos(args.base_dir):
        result = process_repo(repo, apply=args.apply)
        if result.issues:
            summary.append(
                {
                    "repo": repo.name,
                    "files": [str(i.path.relative_to(repo)) for i in result.issues],
                    "branch": result.branch,
                    "pr_url": result.pr_url,
                }
            )
    report_path = Path("logs/markdown-header-report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Report written to {report_path}")
    if not summary:
        print("No markdown header issues found.")


if __name__ == "__main__":
    main()
