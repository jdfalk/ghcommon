#!/usr/bin/env python3
# file: scripts/remove-reusable-workflow-permissions.py
# version: 1.0.0
# guid: 7a8b9c0d-1e2f-3a4b-5c6d-7e8f9a0b1c2d

"""
Remove permissions from reusable workflows to avoid permission conflicts.

This script:
1. Identifies all reusable workflows (files starting with reusable-)
2. Removes any permissions blocks from them
3. Adds comments explaining that permissions should be set in calling workflows
4. Creates a backup of original files
"""

import shutil
from pathlib import Path
from typing import Dict, Any, List
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def find_reusable_workflows(workflows_dir: Path) -> List[Path]:
    """Find all reusable workflow files."""
    reusable_workflows = []

    for workflow_file in workflows_dir.glob("*.yml"):
        if workflow_file.name.startswith("reusable-"):
            reusable_workflows.append(workflow_file)

    return reusable_workflows


def backup_file(file_path: Path) -> Path:
    """Create a backup of the original file."""
    backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
    shutil.copy2(file_path, backup_path)
    logger.info(f"Created backup: {backup_path}")
    return backup_path


def remove_permissions_from_yaml(content: str) -> tuple[str, bool]:
    """
    Remove permissions blocks from YAML content while preserving structure.
    Returns (modified_content, was_modified).
    """
    lines = content.split("\n")
    modified_lines = []
    in_permissions_block = False
    permissions_indent = 0
    was_modified = False

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()

        # Check if this line starts a permissions block
        if stripped.startswith("permissions:"):
            was_modified = True
            in_permissions_block = True
            permissions_indent = len(line) - len(stripped)

            # Add comment explaining the change
            indent_str = " " * permissions_indent
            modified_lines.append(
                f"{indent_str}# Permissions removed - should be set in calling workflow"
            )
            modified_lines.append(
                f"{indent_str}# See: https://docs.github.com/en/actions/using-workflows/reusing-workflows#supported-keywords-for-jobs-that-call-a-reusable-workflow"
            )

            i += 1
            continue

        # If we're in a permissions block, skip lines that are part of it
        if in_permissions_block:
            current_indent = (
                len(line) - len(line.lstrip())
                if line.strip()
                else permissions_indent + 1
            )

            # If this line is indented more than the permissions line, it's part of the block
            if line.strip() == "" or current_indent > permissions_indent:
                i += 1
                continue
            else:
                # We've reached the end of the permissions block
                in_permissions_block = False

        modified_lines.append(line)
        i += 1

    return "\n".join(modified_lines), was_modified


def analyze_workflow_permissions(file_path: Path) -> Dict[str, Any]:
    """Analyze a workflow file for permissions usage."""
    try:
        with open(file_path, "r") as f:
            content = f.read()

        # Count permissions occurrences
        permissions_count = content.count("permissions:")

        # Check if it's a reusable workflow
        is_reusable = "workflow_call:" in content

        # Extract permissions blocks for analysis
        permissions_blocks = []
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if "permissions:" in line and not line.strip().startswith("#"):
                # Found a permissions block, extract it
                start_indent = len(line) - len(line.lstrip())
                block_lines = [line]

                # Get subsequent indented lines
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    if next_line.strip() == "":
                        block_lines.append(next_line)
                    elif len(next_line) - len(next_line.lstrip()) > start_indent:
                        block_lines.append(next_line)
                    else:
                        break
                    j += 1

                permissions_blocks.append("\n".join(block_lines))

        return {
            "is_reusable": is_reusable,
            "permissions_count": permissions_count,
            "permissions_blocks": permissions_blocks,
            "file_size": len(content),
            "line_count": len(lines),
        }

    except Exception as e:
        logger.error(f"Error analyzing {file_path}: {e}")
        return {}


def process_reusable_workflow(file_path: Path, dry_run: bool = False) -> Dict[str, Any]:
    """Process a single reusable workflow file."""
    logger.info(f"Processing: {file_path}")

    try:
        with open(file_path, "r") as f:
            original_content = f.read()

        # Analyze the file first
        analysis = analyze_workflow_permissions(file_path)

        if not analysis.get("is_reusable", False):
            logger.warning(f"File {file_path} doesn't appear to be a reusable workflow")
            return {
                "status": "not_reusable",
                "reason": "not_reusable",
                "analysis": analysis,
            }

        if analysis.get("permissions_count", 0) == 0:
            logger.info(f"No permissions found in {file_path}")
            return {
                "status": "already_correct",
                "reason": "no_permissions",
                "analysis": analysis,
            }

        # Remove permissions
        modified_content, was_modified = remove_permissions_from_yaml(original_content)

        if not was_modified:
            logger.info(f"No changes needed for {file_path}")
            return {"status": "no_changes", "analysis": analysis}

        if dry_run:
            logger.info(f"DRY RUN: Would modify {file_path}")
            return {
                "status": "would_modify",
                "analysis": analysis,
                "original_size": len(original_content),
                "modified_size": len(modified_content),
            }

        # Create backup and write modified file
        backup_path = backup_file(file_path)

        with open(file_path, "w") as f:
            f.write(modified_content)

        logger.info(f"Successfully modified {file_path}")
        return {
            "status": "modified",
            "backup_path": str(backup_path),
            "analysis": analysis,
            "original_size": len(original_content),
            "modified_size": len(modified_content),
        }

    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return {"status": "error", "error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="Remove permissions from reusable workflows"
    )
    parser.add_argument(
        "--workflows-dir",
        type=Path,
        default=Path(".github/workflows"),
        help="Directory containing workflow files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    workflows_dir = args.workflows_dir
    if not workflows_dir.exists():
        logger.error(f"Workflows directory not found: {workflows_dir}")
        return 1

    # Find all reusable workflows
    reusable_workflows = find_reusable_workflows(workflows_dir)

    if not reusable_workflows:
        logger.info("No reusable workflows found")
        return 0

    logger.info(f"Found {len(reusable_workflows)} reusable workflows")

    results = {}

    # Process each workflow
    for workflow_file in reusable_workflows:
        result = process_reusable_workflow(workflow_file, dry_run=args.dry_run)
        results[str(workflow_file)] = result

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    modified_count = 0
    already_correct_count = 0
    not_reusable_count = 0
    error_count = 0

    for file_path, result in results.items():
        status = result["status"]
        file_name = Path(file_path).name

        if status == "modified" or status == "would_modify":
            modified_count += 1
            print(f"✓ {file_name}: {status}")
            if "analysis" in result:
                perms_count = result["analysis"].get("permissions_count", 0)
                print(f"  - Removed {perms_count} permissions block(s)")
        elif status == "already_correct":
            already_correct_count += 1
            reason = result.get("reason", "unknown")
            print(f"✅ {file_name}: already correct ({reason})")
        elif status == "not_reusable":
            not_reusable_count += 1
            print(f"⚠️  {file_name}: not a reusable workflow")
        elif status == "no_changes":
            already_correct_count += 1
            print(f"✅ {file_name}: already correct (no changes needed)")
        elif status == "error":
            error_count += 1
            print(f"❌ {file_name}: error - {result.get('error', 'unknown')}")
        else:
            print(f"? {file_name}: {status}")

    print(f"\nFiles processed: {len(results)}")
    print(f"Modified: {modified_count}")
    print(f"Already correct: {already_correct_count}")
    print(f"Not reusable workflows: {not_reusable_count}")
    print(f"Errors: {error_count}")

    if args.dry_run:
        print("\nThis was a dry run. Use --dry-run=false to make actual changes.")

    return 0


if __name__ == "__main__":
    exit(main())
