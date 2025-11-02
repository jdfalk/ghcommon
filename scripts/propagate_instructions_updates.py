#!/usr/bin/env python3
# file: scripts/propagate_instructions_updates.py
# version: 1.0.0
# guid: 9b8a7c6d-5e4f-3a2b-1c9d-8e7f6a5b4c3d

"""Propagate updated general coding instructions from ghcommon to all repositories.

This script ensures all repositories have the latest version of the general coding
instructions with the critical version increment requirement.
"""

import shutil
from pathlib import Path

# Source repository (ghcommon)
GHCOMMON_PATH = Path("/Users/jdfalk/repos/github.com/jdfalk/ghcommon")

# Target repositories
REPOS = [
    "/Users/jdfalk/repos/github.com/jdfalk/subtitle-manager",
    "/Users/jdfalk/repos/github.com/jdfalk/gcommon",
    "/Users/jdfalk/repos/github.com/jdfalk/apt-cacher-go",
    "/Users/jdfalk/repos/github.com/jdfalk/audiobook-organizer",
    "/Users/jdfalk/repos/github.com/jdfalk/copilot-agent-util-rust",
    "/Users/jdfalk/repos/github.com/jdfalk/public-scratch",
    "/Users/jdfalk/repos/github.com/jdfalk/ubuntu-autoinstall-webhook",
]


def copy_instructions(target_repo: Path):
    """Copy the general coding instructions from ghcommon to target repository."""
    source_file = (
        GHCOMMON_PATH / ".github/instructions/general-coding.instructions.md"
    )
    target_file = (
        target_repo / ".github/instructions/general-coding.instructions.md"
    )

    if source_file.exists():
        # Ensure target directory exists
        target_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, target_file)
        print(f"✅ Copied general coding instructions to {target_repo.name}")
        return True
    print("❌ Source general coding instructions not found in ghcommon")
    return False


def main():
    """Main function to propagate instructions to all repositories."""
    print(
        "🚀 Propagating updated general coding instructions from ghcommon to all repositories..."
    )
    print()

    if not GHCOMMON_PATH.exists():
        print(f"❌ ghcommon repository not found at {GHCOMMON_PATH}")
        return 1

    success_count = 0
    total_repos = len(REPOS)

    for repo_path_str in REPOS:
        repo_path = Path(repo_path_str)
        print(f"📁 Processing {repo_path.name}...")

        if not repo_path.exists():
            print(f"⚠️ Repository not found: {repo_path}")
            continue

        # Copy instructions
        if copy_instructions(repo_path):
            success_count += 1
            print(f"✅ Successfully updated {repo_path.name}")
        else:
            print(f"⚠️ Failed to update {repo_path.name}")

        print()

    print(
        f"📊 Summary: {success_count}/{total_repos} repositories updated successfully"
    )

    if success_count == total_repos:
        print("🎉 All repositories updated with latest instructions!")
        return 0
    print("⚠️ Some repositories had issues. Review the output above.")
    return 1


if __name__ == "__main__":
    exit(main())
