#!/usr/bin/env python3
# file: scripts/propagat    # Source linter configs are now in root directory\n    source_linters = GHCOMMON_PATH_ci_fixes.py
# version: 1.0.0
# guid: 8a7b6c5d-4e3f-2a1b-9c8d-7e6f5a4b3c2d

"""Copy fixed CI workflow and Super Linter configs from ghcommon to all repositories.

This script addresses the systematic CI failures caused by incorrect Super Linter
configuration file references across all repositories.
"""

import shutil
from pathlib import Path

# Source repository (ghcommon)
GHCOMMON_PATH = Path(__file__).parent.parent.resolve()

# Target repositories
REPOS = [
    "subtitle-manager",
    "apt-cacher-go",
    "audiobook-organizer",
    "copilot-agent-util-rust",
    "public-scratch",
    "ubuntu-autoinstall-webhook",
]


def copy_ci_workflow(target_repo: Path):
    """Copy the CI workflow from ghcommon to target repository."""
    source_ci = GHCOMMON_PATH / ".github/workflows/ci.yml"
    target_ci = target_repo / ".github/workflows/ci.yml"

    if source_ci.exists():
        # Ensure target directory exists
        target_ci.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_ci, target_ci)
        print(f"✅ Copied CI workflow to {target_repo.name}")
        return True
    print("❌ Source CI workflow not found in ghcommon")
    return False


def copy_super_linter_configs(target_repo: Path):
    """Copy Super Linter config files from ghcommon to target repository."""
    source_linters = GHCOMMON_PATH
    target_linters = target_repo

    # Ensure target directory exists
    target_linters.mkdir(parents=True, exist_ok=True)

    # Copy the two key Super Linter config files
    configs_copied = 0
    for config_file in ["super-linter-ci.env", "super-linter-pr.env"]:
        source_config = source_linters / config_file
        target_config = target_linters / config_file

        if source_config.exists():
            shutil.copy2(source_config, target_config)
            print(f"✅ Copied {config_file} to {target_repo.name}")
            configs_copied += 1
        else:
            print(f"❌ {config_file} not found in ghcommon")

    # Also copy .eslintrc.yml if it doesn't exist in target
    eslint_config = ".eslintrc.yml"
    source_eslint = source_linters / eslint_config
    target_eslint = target_linters / eslint_config

    if source_eslint.exists() and not target_eslint.exists():
        shutil.copy2(source_eslint, target_eslint)
        print(f"✅ Copied {eslint_config} to {target_repo.name}")
        configs_copied += 1

    return configs_copied


def increment_version_in_ci(target_repo: Path):
    """Increment the version in the CI workflow file header."""
    ci_file = target_repo / ".github/workflows/ci.yml"

    if not ci_file.exists():
        return False

    try:
        with open(ci_file) as f:
            content = f.read()

        # Look for version line and increment patch version
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("# version:"):
                # Extract version and increment patch
                version_str = line.split(": ")[1]
                major, minor, patch = map(int, version_str.split("."))
                new_version = f"{major}.{minor}.{patch + 1}"
                lines[i] = f"# version: {new_version}"

                # Write back to file
                with open(ci_file, "w") as f:
                    f.write("\n".join(lines))

                print(f"✅ Incremented CI workflow version to {new_version} in {target_repo.name}")
                return True

        print(f"⚠️ No version header found in CI workflow for {target_repo.name}")
        return False

    except Exception as e:
        print(f"❌ Error updating version in {target_repo.name}: {e}")
        return False


def main():
    """Main function to propagate CI fixes to all repositories."""
    print("🚀 Propagating CI fixes from ghcommon to all repositories...")
    print()

    if not GHCOMMON_PATH.exists():
        print(f"❌ ghcommon repository not found at {GHCOMMON_PATH}")
        return 1

    # Determine the base repos directory (parent of ghcommon)
    repos_base = GHCOMMON_PATH.parent

    success_count = 0
    total_repos = len(REPOS)

    for repo_name in REPOS:
        repo_path = repos_base / repo_name
        print(f"📁 Processing {repo_name}...")

        if not repo_path.exists():
            print(f"⚠️ Repository not found: {repo_path}")
            continue

        # Copy CI workflow
        ci_copied = copy_ci_workflow(repo_path)

        # Copy Super Linter configs
        configs_copied = copy_super_linter_configs(repo_path)

        # Increment version
        increment_version_in_ci(repo_path)

        if ci_copied and configs_copied >= 2:
            success_count += 1
            print(f"✅ Successfully updated {repo_name}")
        else:
            print(f"⚠️ Partial update for {repo_name}")

        print()

    print(f"📊 Summary: {success_count}/{total_repos} repositories updated successfully")

    if success_count == total_repos:
        print("🎉 All repositories updated! Ready to test CI workflows.")
        return 0
    print("⚠️ Some repositories had issues. Review the output above.")
    return 1


if __name__ == "__main__":
    exit(main())
