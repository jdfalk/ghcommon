#!/usr/bin/env python3
# file: add_sync_warning.py
# version: 1.0.0
# guid: f1a2b3c4-d5e6-f7a8-b9c0-d1e2f3a4b5c6

"""
Add sync warning to all workflow files to indicate they should be edited in ghcommon
"""

import os
import glob


def add_sync_warning_to_workflow(file_path):
    """Add sync warning comment to a workflow file"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Skip if warning already exists
    if "DO NOT EDIT DIRECTLY" in content:
        print(f"Warning already exists in {file_path}")
        return

    # Find the first line that isn't a comment or empty
    lines = content.split("\n")
    insert_index = 0

    # Skip existing file headers and comments
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            insert_index = i
            break

    # Create the sync warning
    warning_lines = [
        "# ⚠️  DO NOT EDIT DIRECTLY - This file is managed in ghcommon repository",
        "# All changes should be made in jdfalk/ghcommon and will be synced to other repositories",
        "# Edit this file at: https://github.com/jdfalk/ghcommon/edit/main/.github/workflows/"
        + os.path.basename(file_path),
        "",
    ]

    # Insert warning after file header but before main content
    new_lines = lines[:insert_index] + warning_lines + lines[insert_index:]

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines))

    print(f"Added sync warning to {file_path}")


def main():
    """Process all workflow files"""
    workflow_dir = "/Users/jdfalk/repos/github.com/jdfalk/ghcommon/.github/workflows"

    # Find all YAML workflow files
    workflow_files = glob.glob(os.path.join(workflow_dir, "*.yml"))
    workflow_files.extend(glob.glob(os.path.join(workflow_dir, "*.yaml")))

    print(f"Found {len(workflow_files)} workflow files")

    for file_path in workflow_files:
        add_sync_warning_to_workflow(file_path)

    print("Sync warnings added to all workflow files")


if __name__ == "__main__":
    main()
