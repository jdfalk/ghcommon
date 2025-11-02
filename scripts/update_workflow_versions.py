#!/usr/bin/env python3
# file: scripts/update_workflow_versions.py
# version: 1.0.0
# guid: 9b8a7c6d-5e4f-3a2b-1c0d-9e8f7a6b5c4d

"""Update all workflow file versions in ghcommon to match the propagated versions.

This ensures consistency between the source repository (ghcommon) and all
target repositories that received the CI fixes.
"""

import re
from pathlib import Path

# Define version mappings
VERSION_UPDATES = {
    "ci.yml": "1.18.1",  # Match propagated version
    "manager-sync-dispatcher.yml": "1.1.0",
    "sync-receiver.yml": "1.1.0",
    "issue-automation.yml": "1.1.0",
    "pr-automation.yml": "1.1.0",
    "security.yml": "1.2.0",
    "maintenance.yml": "1.1.0",
    "unified-automation.yml": "1.1.0",
    "auto-module-tagging.yml": "1.1.0",
    "commit-override-handler.yml": "1.1.0",
    "protobuf-generation.yml": "1.1.0",
    "release.yml": "2.0.0",
    "release-go-v1-deprecated.yml": "2.2.3",
    "release-rust-v1-deprecated.yml": "1.9.4",
    "release-python-v1-deprecated.yml": "1.3.3",
    "release-docker-v1-deprecated.yml": "1.2.3",
    "release-frontend-v1-deprecated.yml": "1.3.3",
    "release-protobuf-v1-deprecated.yml": "1.3.2",
}


def update_workflow_version(file_path: Path, new_version: str):
    """Update the version header in a workflow file."""
    content = file_path.read_text()

    # Pattern to match version header
    version_pattern = r"^# version: \d+\.\d+\.\d+$"
    new_version_line = f"# version: {new_version}"

    # Replace the version line
    updated_content = re.sub(
        version_pattern, new_version_line, content, flags=re.MULTILINE
    )

    if updated_content != content:
        file_path.write_text(updated_content)
        print(f"✅ Updated {file_path.name} to version {new_version}")
        return True
    print(f"⚠️  No version header found in {file_path.name}")
    return False


def main():
    """Update all workflow versions."""
    workflows_dir = Path(
        "/Users/jdfalk/repos/github.com/jdfalk/ghcommon/.github/workflows"
    )

    if not workflows_dir.exists():
        print("❌ Workflows directory not found")
        return False

    updated_count = 0

    for filename, version in VERSION_UPDATES.items():
        file_path = workflows_dir / filename
        if file_path.exists():
            if update_workflow_version(file_path, version):
                updated_count += 1
        else:
            print(f"⚠️  File not found: {filename}")

    print(
        f"\n📊 Summary: {updated_count}/{len(VERSION_UPDATES)} workflow files updated"
    )
    return updated_count > 0


if __name__ == "__main__":
    main()
