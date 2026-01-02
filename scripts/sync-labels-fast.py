#!/usr/bin/env python3
# file: scripts/sync-labels-fast.py
# version: 1.0.0
# guid: f1a2b3c4-d5e6-f7g8-h901-i234567890jk

"""Fast label sync using gh CLI"""

import json
import subprocess
import sys
from pathlib import Path


def sync_labels(owner: str, repo: str, labels_file: str) -> bool:
    """Sync labels for a repo using gh CLI"""
    print(f"Syncing {owner}/{repo}...", end=" ", flush=True)

    try:
        with open(labels_file) as f:
            labels = json.load(f)
    except Exception as e:
        print(f"❌ Failed to read labels: {e}")
        return False

    success = 0
    failed = 0

    for label in labels:
        try:
            # Check if label exists
            result = subprocess.run(
                [
                    "gh",
                    "label",
                    "list",
                    "-R",
                    f"{owner}/{repo}",
                    "--search",
                    label["name"],
                    "-q",
                    ".[0].name",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if label["name"] in result.stdout:
                # Label exists, update it
                subprocess.run(
                    [
                        "gh",
                        "label",
                        "edit",
                        label["name"],
                        "-R",
                        f"{owner}/{repo}",
                        "-c",
                        label["color"],
                        "-d",
                        label.get("description", ""),
                    ],
                    capture_output=True,
                    timeout=5,
                )
            else:
                # Label doesn't exist, create it
                subprocess.run(
                    [
                        "gh",
                        "label",
                        "create",
                        label["name"],
                        "-R",
                        f"{owner}/{repo}",
                        "-c",
                        label["color"],
                        "-d",
                        label.get("description", ""),
                    ],
                    capture_output=True,
                    timeout=5,
                )
            success += 1
        except Exception:
            failed += 1

    if failed == 0:
        print(f"✅ ({success} labels)")
        return True
    else:
        print(f"⚠️  ({success}/{len(labels)} labels, {failed} failed)")
        return True


def main():
    """Main"""
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
        "release-strategy-action",
        "security-summary-action",
    ]

    owner = "jdfalk"
    labels_file = "labels.json"

    if not Path(labels_file).exists():
        print(f"❌ Labels file not found: {labels_file}")
        sys.exit(1)

    print(f"Syncing {len(action_repos)} action repos...\n")

    failed_repos = []
    for repo in action_repos:
        if not sync_labels(owner, repo, labels_file):
            failed_repos.append(repo)

    print("\nDone!")
    if failed_repos:
        print(f"Failed: {', '.join(failed_repos)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
