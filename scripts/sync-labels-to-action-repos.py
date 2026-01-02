#!/usr/bin/env python3
# file: scripts/sync-labels-to-action-repos.py
# version: 1.0.0
# guid: 8a9b0c1d-2e3f-4a5b-6c7d-8e9f0a1b2c3d

"""Sync labels to all action repositories."""

import os
import subprocess
import sys


def sync_labels_for_repo(owner: str, repo: str, labels_file: str, token: str) -> bool:
    """Sync labels for a single repository."""
    print(f"\n📦 Syncing labels for {owner}/{repo}...")

    env = os.environ.copy()
    env["GITHUB_TOKEN"] = token

    try:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/sync-github-labels.py",
                owner,
                repo,
                "--labels-file",
                labels_file,
            ],
            env=env,
            capture_output=False,
            check=False,
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error syncing labels for {repo}: {e}")
        return False


def main():
    """Main entry point."""
    # Get GitHub token
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("PAT_TOKEN")
    if not token:
        print("❌ GITHUB_TOKEN or PAT_TOKEN environment variable is required")
        sys.exit(1)

    # List of action repositories to sync
    action_repos = [
        "detect-languages-action",
        "generate-version-action",
        "get-frontend-config-action",
        "package-assets-action",
        "auto-module-tagging-action",
        "ci-generate-matrices-action",
        "load-config-action",
        "release-docker-action",
        "release-frontend-action",
        "release-go-action",
        "release-protobuf-action",
        "release-python-action",
        "release-rust-action",
        "ci-workflow-helpers-action",
        "pr-auto-label-action",
        "docs-generator-action",
    ]

    # Repo owner
    owner = "jdfalk"

    # Labels file
    labels_file = "labels.json"

    if not os.path.isfile(labels_file):
        print(f"❌ Labels file not found: {labels_file}")
        sys.exit(1)

    print(f"🏷️  Syncing labels to {len(action_repos)} action repositories")
    print(f"📁 Owner: {owner}")
    print(f"📄 Labels file: {labels_file}")

    success_count = 0
    failed_repos = []

    for repo in action_repos:
        if sync_labels_for_repo(owner, repo, labels_file, token):
            success_count += 1
        else:
            failed_repos.append(repo)

    print(f"\n{'=' * 50}")
    print(f"✅ Successfully synced {success_count}/{len(action_repos)} repositories")

    if failed_repos:
        print(f"❌ Failed to sync {len(failed_repos)} repositories:")
        for repo in failed_repos:
            print(f"   - {repo}")
        sys.exit(1)
    else:
        print("🎉 All repositories synced successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
