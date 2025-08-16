#!/usr/bin/env python3
# file: .github/scripts/sync-dispatch-events.py
# version: 1.0.0
# guid: b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e

"""
Dispatch repository events to target repositories for synchronization.
"""

import json
import os
import sys
import subprocess
from pathlib import Path


def get_target_repos():
    """Read target repositories from repositories.txt."""
    repo_file = Path(".github/repositories.txt")

    if not repo_file.exists():
        print("Error: .github/repositories.txt not found", file=sys.stderr)
        return []

    repos = []
    try:
        with open(repo_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    # Keep full owner/repo format for API calls
                    repos.append(line)
    except Exception as e:
        print(f"Error reading repositories.txt: {e}", file=sys.stderr)
        return []

    return repos


def dispatch_event(repo, event_type, client_payload):
    """Dispatch a repository event to a target repository."""
    token = os.getenv("JF_CI_GH_PAT") or os.getenv("GITHUB_TOKEN")

    if not token:
        print(
            "Error: No GitHub token found (JF_CI_GH_PAT or GITHUB_TOKEN)",
            file=sys.stderr,
        )
        return False

    # Construct GitHub API URL
    api_url = f"https://api.github.com/repos/{repo}/dispatches"

    # Prepare payload
    payload = {"event_type": event_type, "client_payload": client_payload}

    # Use curl for the API call (more reliable than requests in CI)
    curl_cmd = [
        "curl",
        "-X",
        "POST",
        "-H",
        "Accept: application/vnd.github+json",
        "-H",
        f"Authorization: Bearer {token}",
        "-H",
        "X-GitHub-Api-Version: 2022-11-28",
        api_url,
        "-d",
        json.dumps(payload),
    ]

    try:
        result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            print(f"✅ Successfully dispatched event to {repo}")
            return True
        else:
            print(
                f"❌ Failed to dispatch event to {repo}: {result.stderr}",
                file=sys.stderr,
            )
            return False
    except subprocess.TimeoutExpired:
        print(f"❌ Timeout dispatching event to {repo}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ Error dispatching event to {repo}: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point."""
    event_type = os.getenv("EVENT_TYPE", "sync-from-ghcommon")

    # Get source repository and SHA
    source_repo = os.getenv("GITHUB_REPOSITORY", "jdfalk/ghcommon")
    source_sha = os.getenv("GITHUB_SHA", "unknown")
    source_ref = os.getenv("GITHUB_REF", "refs/heads/main")

    # Create client payload
    client_payload = {
        "source_repository": source_repo,
        "source_sha": source_sha,
        "source_ref": source_ref,
        "dispatch_time": os.getenv("GITHUB_RUN_ID", "unknown"),
    }

    print(f"Dispatching '{event_type}' events to target repositories...")
    print(f"Source: {source_repo}@{source_sha}")

    target_repos = get_target_repos()

    if not target_repos:
        print("No target repositories found")
        sys.exit(1)

    successful = 0
    failed = 0

    for repo in target_repos:
        if dispatch_event(repo, event_type, client_payload):
            successful += 1
        else:
            failed += 1

    print(f"✅ Successfully dispatched to {successful} repositories")
    if failed > 0:
        print(f"❌ Failed to dispatch to {failed} repositories", file=sys.stderr)
        sys.exit(1)

    print("All repository dispatch events sent successfully")


if __name__ == "__main__":
    main()
