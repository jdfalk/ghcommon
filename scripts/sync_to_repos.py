# file: scripts/sync_to_repos.py
# version: 1.0.0
# guid: 8f2c1b4d-6e3a-4b8c-9e1f-7a6b2c3d4e5f
"""
sync_to_repos.py

Syncs selected files or directories from the current repository to one or more target GitHub repositories.

Usage:
    python scripts/sync_to_repos.py --repos "jdfalk/subtitle-manager,jdfalk/auto-formatter" --files ".github/workflows,docs" --branch "sync-from-ghcommon"

Args:
    --repos: Comma-separated list of target repositories (owner/repo)
    --files: Comma-separated list of files or directories to sync
    --branch: Branch name to push changes to in target repos

Environment:
    GH_TOKEN: GitHub token with repo access

Outputs:
    sync-summary.log: Summary of sync operations
"""

import os
import sys
import subprocess
import shutil
import tempfile
import argparse
from typing import List

import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")


def parse_args():
    parser = argparse.ArgumentParser(description="Sync files to target repos.")
    parser.add_argument(
        "--repos", required=True, help="Comma-separated list of target repos"
    )
    parser.add_argument(
        "--files", required=True, help="Comma-separated list of files/dirs to sync"
    )
    parser.add_argument("--branch", required=True, help="Branch name to push to")
    return parser.parse_args()


def run(cmd: List[str], cwd=None, check=True):
    logging.info(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)
    if result.stdout:
        logging.info(result.stdout)
    if result.stderr:
        logging.info(result.stderr)
    return result


def sync_to_repo(
    repo: str, files: List[str], branch: str, gh_token: str, summary: List[str]
):
    repo_url = f"https://{gh_token}:x-oauth-basic@github.com/{repo}.git"
    with tempfile.TemporaryDirectory() as tmpdir:
        run(["git", "clone", "--depth=1", repo_url, tmpdir])
        run(["git", "checkout", "-b", branch], cwd=tmpdir)
        for f in files:
            src = os.path.abspath(f)
            dst = os.path.join(tmpdir, f)
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            elif os.path.isfile(src):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
            else:
                summary.append(f"[WARN] {f} not found, skipping.")
        run(["git", "add", "."], cwd=tmpdir)
        run(["git", "config", "user.name", "ghcommon-sync-bot"], cwd=tmpdir)
        run(
            [
                "git",
                "config",
                "user.email",
                "ghcommon-sync-bot@users.noreply.github.com",
            ],
            cwd=tmpdir,
        )
        commit_msg = (
            "chore(sync): sync from ghcommon\n\nFiles changed: auto-sync from ghcommon"
        )
        try:
            run(["git", "commit", "-m", commit_msg], cwd=tmpdir)
        except subprocess.CalledProcessError:
            summary.append(f"[SKIP] {repo}: No changes to commit.")
            return
        try:
            run(["git", "push", "-u", "origin", branch, "--force"], cwd=tmpdir)
            summary.append(f"[OK] {repo}: Synced to branch {branch}.")
        except subprocess.CalledProcessError as e:
            summary.append(f"[FAIL] {repo}: Push failed. {e}")


def main():
    args = parse_args()
    gh_token = os.environ.get("GH_TOKEN")
    if not gh_token:
        print("GH_TOKEN environment variable is required.", file=sys.stderr)
        sys.exit(1)
    repos = [r.strip() for r in args.repos.split(",") if r.strip()]
    files = [f.strip() for f in args.files.split(",") if f.strip()]
    branch = args.branch
    summary = []
    for repo in repos:
        sync_to_repo(repo, files, branch, gh_token, summary)
    with open("sync-summary.log", "w") as f:
        for line in summary:
            f.write(line + "\n")
    print("\n".join(summary))


if __name__ == "__main__":
    main()
