#!/usr/bin/env python3
# file: scripts/pin-actions-to-hashes.py
# version: 1.0.0
# guid: a1b2c3d4-e5f6-7890-abcd-ef1234567890

"""Pin all GitHub Actions to specific commit hashes with version comments.

This script:
1. Discovers all jdfalk/* action repositories
2. Gets the latest release/tag for each
3. Gets the commit hash for that tag
4. Updates all workflow files to use hash@commit # vX.Y.Z format
5. Writes the mappings to ACTION_VERSIONS.md for reference
"""

import re
import subprocess
from pathlib import Path


def run_command(cmd: list[str]) -> str:
    """Run a command and return output."""
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def get_latest_tag(repo: str) -> str:
    """Get the latest tag for a repository."""
    try:
        tags = run_command(["gh", "api", f"/repos/jdfalk/{repo}/tags", "--jq", ".[0].name"])
        return tags if tags else "v1.0.0"
    except subprocess.CalledProcessError:
        return "v1.0.0"


def get_commit_for_tag(repo: str, tag: str) -> str:
    """Get the commit hash for a specific tag."""
    try:
        commit = run_command(
            [
                "gh",
                "api",
                f"/repos/jdfalk/{repo}/git/ref/tags/{tag}",
                "--jq",
                ".object.sha",
            ]
        )
        return commit[:7]  # Use short hash
    except subprocess.CalledProcessError:
        # If tag doesn't exist, get latest commit
        try:
            commit = run_command(
                [
                    "gh",
                    "api",
                    f"/repos/jdfalk/{repo}/commits",
                    "--jq",
                    ".[0].sha",
                ]
            )
            return commit[:7]
        except subprocess.CalledProcessError:
            return "unknown"


def discover_action_repos() -> list[str]:
    """Discover all jdfalk/*-action repositories."""
    action_repos = [
        "release-go-action",
        "release-docker-action",
        "release-frontend-action",
        "release-python-action",
        "release-rust-action",
        "release-protobuf-action",
        "auto-module-tagging-action",
    ]
    return action_repos


def get_action_versions() -> dict[str, tuple[str, str]]:
    """Get version and hash for all action repositories."""
    repos = discover_action_repos()
    versions = {}

    print("🔍 Discovering action versions and hashes...\n")

    for repo in repos:
        tag = get_latest_tag(repo)
        commit = get_commit_for_tag(repo, tag)
        versions[repo] = (tag, commit)
        print(f"  {repo}: {tag} @ {commit}")

    print()
    return versions


def update_workflow_file(file_path: Path, versions: dict[str, tuple[str, str]]) -> bool:
    """Update a single workflow file to pin actions to hashes."""
    content = file_path.read_text()
    updated = False

    for repo, (tag, commit) in versions.items():
        # Pattern 1: jdfalk/repo-name@hash (with or without comment)
        pattern1 = rf"(jdfalk/{repo})@[a-f0-9]{{7,40}}(?:\s+#\s+v[\d.]+)?"
        # Pattern 2: jdfalk/repo-name@vX.Y.Z (tag reference)
        pattern2 = rf"(jdfalk/{repo})@v[\d.]+"
        # Pattern 3: jdfalk/repo-name@v1 or @v2 (major version)
        pattern3 = rf"(jdfalk/{repo})@v\d+"

        replacement = rf"\1@{commit} # {tag}"

        # Try all patterns
        new_content = content
        new_content = re.sub(pattern1, replacement, new_content)
        new_content = re.sub(pattern2, replacement, new_content)
        new_content = re.sub(pattern3, replacement, new_content)

        if new_content != content:
            content = new_content
            updated = True

    if updated:
        file_path.write_text(content)

    return updated


def update_all_workflows(versions: dict[str, tuple[str, str]]) -> int:
    """Update all workflow files in ghcommon."""
    script_dir = Path(__file__).parent.resolve()
    workflows_dir = script_dir.parent / ".github" / "workflows"
    updated_count = 0

    print("📝 Updating workflow files...\n")

    for workflow_file in workflows_dir.glob("*.yml"):
        if update_workflow_file(workflow_file, versions):
            print(f"  ✅ Updated {workflow_file.name}")
            updated_count += 1

    print(f"\n✅ Updated {updated_count} workflow files")
    return updated_count


def write_version_reference(versions: dict[str, tuple[str, str]]):
    """Write action versions to reference file."""
    script_dir = Path(__file__).parent.resolve()
    ref_file = script_dir.parent / "ACTION_VERSIONS.md"

    content = """<!-- file: ACTION_VERSIONS.md -->
<!-- version: 1.0.0 -->
<!-- guid: b2c3d4e5-f6a7-8901-bcde-f12345678901 -->

# GitHub Actions Version Reference

This file tracks the pinned versions and commit hashes for all jdfalk/* actions.

**Last Updated:** {timestamp}

## Action Versions

| Action Repository | Version | Commit Hash | Usage |
|-------------------|---------|-------------|-------|
"""

    from datetime import datetime

    content = content.format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    for repo, (tag, commit) in sorted(versions.items()):
        usage = f"`jdfalk/{repo}@{commit} # {tag}`"
        content += f"| {repo} | {tag} | `{commit}` | {usage} |\n"

    content += """
## Update Instructions

To update action versions:

1. Release a new version of the action (creates tag)
2. Run `scripts/pin-actions-to-hashes.py` to update hashes
3. Commit and push the updated workflows

## Manual Update

If you need to manually update an action:

```yaml
# Get the commit hash for a tag
gh api /repos/jdfalk/ACTION-NAME/git/ref/tags/vX.Y.Z --jq ".object.sha"

# Update in workflow
uses: jdfalk/ACTION-NAME@COMMIT_HASH # vX.Y.Z
```
"""

    ref_file.write_text(content)
    print(f"\n📄 Updated {ref_file.name}")


def main():
    """Main execution."""
    print("🚀 GitHub Actions Version Pinning Tool\n")
    print("=" * 60)
    print()

    # Get versions and hashes
    versions = get_action_versions()

    # Update all workflows
    update_all_workflows(versions)

    # Write reference file
    write_version_reference(versions)

    print("\n" + "=" * 60)
    print("✅ Action pinning complete!")
    print("\nNext steps:")
    print("1. Review changes in .github/workflows/")
    print("2. Review ACTION_VERSIONS.md")
    print("3. Commit and push changes")


if __name__ == "__main__":
    main()
