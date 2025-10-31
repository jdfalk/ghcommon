#!/usr/bin/env python3
# file: scripts/template_repo/push_with_gh.py
# version: 1.0.0
# guid: a1b2c3d4-e5f6-7890-abcd-ef0123456789

"""Optionally initialize a local git repository and publish it to GitHub using the
GitHub CLI (gh). This script does not embed tokens, secrets, or credentials.

Requirements:
- Git and GitHub CLI installed and authenticated (gh auth login)
- A scaffolded directory created by scaffold_template_repo.py

Safety:
- Does not create submodules or nested repos. Operates only in the target dir.
- No modification of parent repos; uses 'git init' in the target directory only.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys


def run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=str(cwd), check=True)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Initialize git and push to GitHub using gh CLI (no secrets)."
    )
    parser.add_argument(
        "--target",
        required=True,
        help="Target directory containing the scaffolded repo",
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="Repository name on GitHub (e.g., my-template-repo)",
    )
    parser.add_argument(
        "--owner", required=True, help="GitHub username or org (e.g., jdfalk)"
    )
    parser.add_argument(
        "--private",
        action="store_true",
        help="Create the repository as private",
    )
    args = parser.parse_args(argv)

    target = Path(os.path.expanduser(args.target)).resolve()
    if not target.exists() or not target.is_dir():
        print(
            f"Target does not exist or is not a directory: {target}",
            file=sys.stderr,
        )
        return 2

    if not shutil.which("git"):
        print("git is not installed or not in PATH", file=sys.stderr)
        return 2
    if not shutil.which("gh"):
        print(
            "GitHub CLI (gh) is not installed or not in PATH", file=sys.stderr
        )
        return 2

    # Ensure we're not inside another repo when initializing (avoid nested repos/submodules)
    try:
        # Returns exit code 0 when inside any git work tree
        res = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            check=False,
            cwd=str(target),
            capture_output=True,
        )
        inside = res.returncode == 0 and res.stdout.decode().strip() == "true"
    except Exception:
        inside = False
    if inside:
        print(
            "Refusing to initialize a repository inside an existing git work tree. "
            "Choose a target path OUTSIDE your current repository.",
            file=sys.stderr,
        )
        return 2

    if (target / ".git").exists():
        print("Target already contains a git repository. Skipping git init.")
    else:
        run(["git", "init"], cwd=target)

    # Configure minimal user info if not present
    try:
        subprocess.run(
            ["git", "config", "user.name"],
            cwd=str(target),
            check=True,
            stdout=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        run(["git", "config", "user.name", args.owner], cwd=target)
    try:
        subprocess.run(
            ["git", "config", "user.email"],
            cwd=str(target),
            check=True,
            stdout=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        run(
            [
                "git",
                "config",
                "user.email",
                f"{args.owner}@users.noreply.github.com",
            ],
            cwd=target,
        )

    run(["git", "add", "-A"], cwd=target)
    run(["git", "commit", "-m", "chore: initial template scaffold"], cwd=target)

    visibility = "private" if args.private else "public"
    # Create repo on GitHub (gh will use the currently authenticated account)
    run(
        [
            "gh",
            "repo",
            "create",
            f"{args.owner}/{args.repo}",
            "--source",
            str(target),
            "--push",
            f"--{visibility}",
        ],
        cwd=target,
    )

    print(
        f"Repository created and pushed: https://github.com/{args.owner}/{args.repo}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
