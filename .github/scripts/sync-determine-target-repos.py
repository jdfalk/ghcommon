#!/usr/bin/env python3
# file: .github/scripts/sync-determine-target-repos.py
# version: 1.0.0
# guid: a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d

"""
Determine target repositories for sync operations.
Reads from repositories.txt and outputs repository names.
"""

import os
import sys
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
                    # Extract repo name from owner/repo format
                    if "/" in line:
                        repo_name = line.split("/")[-1]
                    else:
                        repo_name = line
                    repos.append(repo_name)
    except Exception as e:
        print(f"Error reading repositories.txt: {e}", file=sys.stderr)
        return []

    return repos


def main():
    """Main entry point."""
    repos = get_target_repos()

    if not repos:
        print("No target repositories found")
        sys.exit(1)

    # Set GitHub Actions output
    repos_str = " ".join(repos)
    print(f"target_repos={repos_str}")

    # Also set as environment variable for downstream steps
    github_output = os.getenv("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"target_repos={repos_str}\n")

    print(f"Found {len(repos)} target repositories: {repos_str}")


if __name__ == "__main__":
    main()
