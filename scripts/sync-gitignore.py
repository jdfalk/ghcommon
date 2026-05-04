#!/usr/bin/env python3
# file: scripts/sync-gitignore.py
# version: 1.0.0
# guid: 7b2c0e3d-9f81-4a5e-8c2b-1d4f6e9a3c10

"""Append (or replace) a managed block of standard ignore patterns in every
.gitignore under the configured repo roots.

Idempotent: re-running the script replaces the previous managed block in place.

Usage:
    scripts/sync-gitignore.py                 # default roots, dry-run off
    scripts/sync-gitignore.py --dry-run       # preview changes
    scripts/sync-gitignore.py --root PATH ... # override search roots
    scripts/sync-gitignore.py --commit        # also git add/commit per repo
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

DEFAULT_ROOTS = [
    Path.home() / "repos" / "github.com" / "jdfalk",
]

BEGIN_MARKER = "# >>> jdfalk managed ignore block (sync-gitignore.py) >>>"
END_MARKER = "# <<< jdfalk managed ignore block (sync-gitignore.py) <<<"

# Patterns that are common across all repos. Add new entries here and re-run.
MANAGED_PATTERNS = [
    "# AI agent scratch / state (may contain PII, machine paths, secrets)",
    ".claude/notes/",
    ".claude/state/",
    ".claude/worktrees/",
    ".claude/settings.local.json",
    ".claude/scheduled_tasks.lock",
    ".copilot/",
    ".aider*",
    ".cursor/",
    ".windsurf/",
    ".remember/",
    ".superpowers/",
    "",
    "# Per-session copilot transcripts",
    "copilot-session-*.md",
    "",
    "# OS junk",
    ".DS_Store",
    "Thumbs.db",
]


def find_gitignores(roots: list[Path]) -> list[Path]:
    found: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        for entry in sorted(root.iterdir()):
            if not entry.is_dir():
                continue
            if not (entry / ".git").exists():
                continue
            gi = entry / ".gitignore"
            if gi.exists():
                found.append(gi)
            else:
                found.append(gi)  # we'll create it
    return found


def build_block() -> str:
    body = "\n".join(MANAGED_PATTERNS)
    return f"\n{BEGIN_MARKER}\n{body}\n{END_MARKER}\n"


def update_file(path: Path, block: str, dry_run: bool) -> tuple[bool, str]:
    """Returns (changed, action). action in {created, replaced, appended, unchanged}."""
    new_block = block.strip("\n") + "\n"
    if not path.exists():
        new_content = new_block
        action = "created"
    else:
        original = path.read_text(encoding="utf-8")
        if BEGIN_MARKER in original and END_MARKER in original:
            pre, _, rest = original.partition(BEGIN_MARKER)
            _, _, post = rest.partition(END_MARKER)
            pre = pre.rstrip("\n")
            post = post.lstrip("\n")
            new_content = (pre + "\n\n" if pre else "") + new_block + ("\n" + post if post else "")
            action = "replaced"
        else:
            sep = "" if original.endswith("\n") else "\n"
            new_content = original + sep + "\n" + new_block
            action = "appended"

        if new_content == original:
            return False, "unchanged"

    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(new_content, encoding="utf-8")
    return True, action


def maybe_commit(repo: Path, dry_run: bool) -> None:
    try:
        subprocess.run(
            ["git", "-C", str(repo), "add", ".gitignore"],
            check=True,
            capture_output=True,
        )
        # Skip commit if nothing staged
        result = subprocess.run(
            ["git", "-C", str(repo), "diff", "--cached", "--quiet"],
        )
        if result.returncode == 0:
            return
        if dry_run:
            print(f"  (dry-run) would commit in {repo}")
            return
        subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "commit",
                "-m",
                "chore(gitignore): sync managed ignore block\n\n"
                "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>",
            ],
            check=True,
            capture_output=True,
        )
        print(f"  committed in {repo}")
    except subprocess.CalledProcessError as exc:
        print(f"  ! git error in {repo}: {exc.stderr.decode().strip()}", file=sys.stderr)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--root",
        action="append",
        type=Path,
        default=None,
        help="Repo root to scan (repeatable). Default: ~/repos/github.com/jdfalk",
    )
    p.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    p.add_argument("--commit", action="store_true", help="git add + commit each updated repo")
    args = p.parse_args()

    roots = args.root if args.root else DEFAULT_ROOTS
    block = build_block()
    files = find_gitignores(roots)

    if not files:
        print("No git repos found under:", *roots, file=sys.stderr)
        return 1

    summary: dict[str, int] = {"created": 0, "replaced": 0, "appended": 0, "unchanged": 0}
    for gi in files:
        changed, action = update_file(gi, block, args.dry_run)
        summary[action] += 1
        marker = "*" if changed else " "
        print(f"{marker} {action:9s} {gi}")
        if changed and args.commit:
            maybe_commit(gi.parent, args.dry_run)

    print()
    print("Summary:", ", ".join(f"{k}={v}" for k, v in summary.items()))
    if args.dry_run:
        print("(dry-run; no files written)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
