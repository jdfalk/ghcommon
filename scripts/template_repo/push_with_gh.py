#!/usr/bin/env python3
# file: scripts/template_repo/push_with_gh.py
# version: 1.1.0
# guid: a1b2c3d4-e5f6-7890-abcd-ef0123456789

"""Optionally initialize a local git repository and publish it to GitHub using the
GitHub CLI (gh). This script does not embed tokens, secrets, or credentials.

Requirements:
- Git and GitHub CLI installed and authenticated (gh auth login)
- A scaffolded directory created by scaffold_template_repo.py

Safety:
- Does not create submodules or nested repos. Operates only in the target dir.
- No modification of parent repos; uses 'git init' in the target directory only.

Repo settings applied after creation (toggleable with --no-settings):
- Disable merge commits + squash merges (rebase-only)
- Disable Projects + Wiki
- Enable auto-merge, allow_update_branch, delete-branch-on-merge
- Workflow permissions: write + can-approve PRs (lets GH Actions merge)
- Actions permissions: sha_pinning_required = true
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=str(cwd), check=True)


def apply_repo_settings(owner: str, repo: str) -> None:
    """Apply the standard repo-settings preset via the gh CLI.

    Each call is independent — if one fails (e.g. an org-level policy
    overrides the request), the rest still run. We log failures but don't
    abort: settings can always be re-applied with `--settings-only`.
    """
    full = f"{owner}/{repo}"

    # Repo-level toggles (gh repo edit covers most of these directly).
    edit_cmd = [
        "gh",
        "repo",
        "edit",
        full,
        "--enable-merge-commit=false",
        "--enable-squash-merge=false",
        "--enable-rebase-merge=true",
        "--enable-auto-merge=true",
        "--delete-branch-on-merge=true",
        "--enable-projects=false",
        "--enable-wiki=false",
    ]
    if subprocess.run(edit_cmd, check=False).returncode != 0:
        print(f"warning: gh repo edit failed for {full}", file=sys.stderr)

    # allow_update_branch is not exposed on `gh repo edit`; PATCH the repo.
    patch_cmd = [
        "gh",
        "api",
        "-X",
        "PATCH",
        f"/repos/{full}",
        "-F",
        "allow_update_branch=true",
        "--silent",
    ]
    if subprocess.run(patch_cmd, check=False).returncode != 0:
        print(f"warning: PATCH allow_update_branch failed for {full}", file=sys.stderr)

    # Workflow permissions: read+write, can approve PRs (so Actions can merge).
    wf_cmd = [
        "gh",
        "api",
        "-X",
        "PUT",
        f"/repos/{full}/actions/permissions/workflow",
        "-F",
        "default_workflow_permissions=write",
        "-F",
        "can_approve_pull_request_reviews=true",
        "--silent",
    ]
    if subprocess.run(wf_cmd, check=False).returncode != 0:
        print(f"warning: PUT actions/permissions/workflow failed for {full}", file=sys.stderr)

    # Require pinned-SHA action refs. This rejects @vN tag refs at run time;
    # the scaffold's generated workflows already use SHAs to satisfy it.
    perms_cmd = [
        "gh",
        "api",
        "-X",
        "PUT",
        f"/repos/{full}/actions/permissions",
        "-F",
        "enabled=true",
        "-f",
        "allowed_actions=all",
        "-F",
        "sha_pinning_required=true",
        "--silent",
    ]
    if subprocess.run(perms_cmd, check=False).returncode != 0:
        print(f"warning: PUT actions/permissions failed for {full}", file=sys.stderr)

    print(f"Settings applied to https://github.com/{full}")


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
    parser.add_argument("--owner", required=True, help="GitHub username or org (e.g., jdfalk)")
    parser.add_argument(
        "--private",
        action="store_true",
        help="Create the repository as private",
    )
    parser.add_argument(
        "--no-settings",
        action="store_true",
        help="Skip applying the standard repo-settings preset after create",
    )
    parser.add_argument(
        "--settings-only",
        action="store_true",
        help=(
            "Skip git init / repo create / push; only apply the settings preset "
            "to an existing repo. Useful for back-filling settings on repos "
            "that were created before this tool was extended."
        ),
    )
    args = parser.parse_args(argv)

    if args.settings_only:
        apply_repo_settings(args.owner, args.repo)
        return 0

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
        print("GitHub CLI (gh) is not installed or not in PATH", file=sys.stderr)
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

    print(f"Repository created and pushed: https://github.com/{args.owner}/{args.repo}")

    if not args.no_settings:
        apply_repo_settings(args.owner, args.repo)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
