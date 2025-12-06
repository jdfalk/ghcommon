#!/usr/bin/env python3
# file: commit-workflow-github-token-fix.py
# version: 1.0.0
# guid: f7e8d9c0-b1a2-3c4d-5e6f-7a8b9c0d1e2f

"""Script to commit the GITHUB_TOKEN workflow fix across repositories.
This fixes the issue where GITHUB_TOKEN was declared as a secret in workflow_call,
which conflicts with GitHub's reserved token name.
"""

import os
import subprocess
import sys


def run_command(cmd, cwd=None):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            cmd,
            check=False,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"Error running command: {cmd}")
            print(f"Error: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Exception running command: {cmd}")
        print(f"Exception: {e}")
        return False


def commit_repo_changes(repo_path, repo_name):
    """Commit changes in a specific repository."""
    print(f"\n=== Processing {repo_name} ===")

    if not os.path.exists(repo_path):
        print(f"Repository path does not exist: {repo_path}")
        return False

    # Check if there are any changes to commit
    if not run_command("git status --porcelain", cwd=repo_path):
        return False

    status_result = subprocess.run(
        "git status --porcelain",
        check=False,
        shell=True,
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if not status_result.stdout.strip():
        print(f"No changes to commit in {repo_name}")
        return True

    # Create commit message
    commit_message = """fix(workflows): remove GITHUB_TOKEN from workflow_call secrets

Fixed critical workflow validation error where GITHUB_TOKEN was declared as a secret
in workflow_call, which conflicts with GitHub Actions reserved token names.

Issues Addressed:

fix(protobuf-generation): remove GITHUB_TOKEN secret declaration
- Removed GITHUB_TOKEN from secrets section in workflow_call
- GITHUB_TOKEN is automatically available in all workflows
- Fixed "secret name `GITHUB_TOKEN` within `workflow_call` can not be used since it would collide with system reserved name" error
- Updated workflow version to reflect the fix

Result: Workflow files now validate successfully without GITHUB_TOKEN collision errors.
The token remains automatically available via ${{ secrets.GITHUB_TOKEN }} in all workflow steps."""

    # Commit the changes
    print(f"Committing changes in {repo_name}...")
    if not run_command(f'git commit -m "{commit_message}"', cwd=repo_path):
        return False

    print(f"Successfully committed changes in {repo_name}")
    return True


def main():
    """Main function to process all repositories."""
    repos = [
        ("/Users/jdfalk/repos/github.com/jdfalk/ghcommon", "ghcommon"),
        ("/Users/jdfalk/repos/github.com/jdfalk/gcommon", "gcommon"),
    ]

    success_count = 0

    for repo_path, repo_name in repos:
        if commit_repo_changes(repo_path, repo_name):
            success_count += 1

    print("\n=== Summary ===")
    print(f"Successfully processed {success_count} out of {len(repos)} repositories")

    if success_count == len(repos):
        print("All repositories processed successfully!")
        return 0
    print("Some repositories had issues.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
