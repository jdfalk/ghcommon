#!/usr/bin/env python3
# file: scripts/update-calling-workflows.py
# version: 1.0.0
# guid: 9c0d1e2f-3a4b-5c6d-7e8f-9a0b1c2d3e4f

"""
Update calling workflows to include required permissions for reusable workflows.

This script:
1. Scans calling workflows to identify which reusable workflows they use
2. Determines required permissions based on analysis
3. Updates calling workflows with appropriate permissions
4. Merges permissions if multiple reusable workflows are called
"""

import json
from pathlib import Path
from typing import Dict, Any, List
import argparse
import logging
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_permissions_analysis(analysis_file: Path) -> Dict[str, Any]:
    """Load the permissions analysis from the analysis file."""
    try:
        with open(analysis_file, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading permissions analysis: {e}")
        return {}


def find_calling_workflows(workflows_dir: Path) -> List[Path]:
    """Find all non-reusable workflow files."""
    calling_workflows = []

    for workflow_file in workflows_dir.glob("*.yml"):
        if not workflow_file.name.startswith("reusable-"):
            calling_workflows.append(workflow_file)

    return calling_workflows


def extract_reusable_workflow_calls(content: str) -> List[str]:
    """Extract calls to reusable workflows from workflow content."""
    reusable_calls = []

    # Look for uses: patterns that reference reusable workflows
    uses_pattern = (
        r'uses:\s*["\']?\.\/\.github\/workflows\/(reusable-[^"\'\s]+\.yml)["\']?'
    )
    matches = re.findall(uses_pattern, content)

    for match in matches:
        reusable_calls.append(match)

    # Also look for relative paths without ./
    uses_pattern2 = (
        r'uses:\s*["\']?\.github\/workflows\/(reusable-[^"\'\s]+\.yml)["\']?'
    )
    matches2 = re.findall(uses_pattern2, content)

    for match in matches2:
        reusable_calls.append(match)

    return list(set(reusable_calls))  # Remove duplicates


def parse_permissions(permissions_list: List[str]) -> Dict[str, str]:
    """Parse permissions list into a dictionary."""
    permissions_dict = {}

    for perm in permissions_list:
        if ":" in perm:
            key, value = perm.split(":", 1)
            permissions_dict[key.strip()] = value.strip()

    return permissions_dict


def merge_permissions(perm_dicts: List[Dict[str, str]]) -> Dict[str, str]:
    """Merge multiple permission dictionaries, preferring 'write' over 'read'."""
    merged = {}

    for perm_dict in perm_dicts:
        for key, value in perm_dict.items():
            if key not in merged:
                merged[key] = value
            else:
                # Prefer 'write' over 'read'
                if value == "write" or merged[key] == "read":
                    merged[key] = value

    return merged


def has_permissions_block(content: str) -> bool:
    """Check if the workflow already has a permissions block."""
    return "permissions:" in content and not all(
        line.strip().startswith("#")
        for line in content.split("\n")
        if "permissions:" in line
    )


def add_permissions_to_workflow(content: str, permissions: Dict[str, str]) -> str:
    """Add permissions block to a workflow file."""
    lines = content.split("\n")

    # Find the right place to insert permissions
    # Should be after 'on:' block but before 'jobs:'
    insert_index = 0
    in_on_block = False
    on_block_end = 0

    for i, line in enumerate(lines):
        stripped = line.strip()

        if stripped.startswith("on:"):
            in_on_block = True
            continue

        if in_on_block:
            # Check if we're still in the on block
            if (
                stripped
                and not line.startswith(" ")
                and not line.startswith("\t")
                and ":" in stripped
            ):
                # We've reached the next top-level block
                on_block_end = i
                break
            elif stripped.startswith("jobs:"):
                on_block_end = i
                break

        if stripped.startswith("jobs:"):
            on_block_end = i
            break

    if on_block_end == 0:
        # Fallback: insert at the beginning if we can't find a good spot
        insert_index = 0
        for i, line in enumerate(lines):
            if line.strip().startswith("name:"):
                insert_index = i + 1
                break
    else:
        insert_index = on_block_end

    # Create permissions block
    permissions_lines = [
        "",
        "# Required permissions for reusable workflows",
        "permissions:",
    ]

    for key, value in sorted(permissions.items()):
        permissions_lines.append(f"  {key}: {value}")

    # Insert the permissions block
    lines[insert_index:insert_index] = permissions_lines

    return "\n".join(lines)


def update_existing_permissions(content: str, permissions: Dict[str, str]) -> str:
    """Update existing permissions block with merged permissions."""
    lines = content.split("\n")
    new_lines = []
    permissions_indent = 0

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()

        if stripped.startswith("permissions:"):
            permissions_indent = len(line) - len(stripped)

            # Add the permissions line
            new_lines.append(line)

            # Skip existing permissions and add merged ones
            i += 1
            while i < len(lines):
                next_line = lines[i]
                current_indent = (
                    len(next_line) - len(next_line.lstrip())
                    if next_line.strip()
                    else permissions_indent + 1
                )

                # If this line is part of the permissions block, skip it
                if next_line.strip() == "" or current_indent > permissions_indent:
                    i += 1
                    continue
                else:
                    # We've reached the end of the permissions block
                    break

            # Add merged permissions
            for key, value in sorted(permissions.items()):
                new_lines.append(f"{' ' * (permissions_indent + 2)}{key}: {value}")

            continue

        new_lines.append(line)
        i += 1

    return "\n".join(new_lines)


def analyze_calling_workflow(
    file_path: Path, permissions_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """Analyze a calling workflow and determine required permissions."""
    try:
        with open(file_path, "r") as f:
            content = f.read()

        # Find reusable workflow calls
        reusable_calls = extract_reusable_workflow_calls(content)

        # Determine required permissions
        required_permissions = []

        for reusable_workflow in reusable_calls:
            if reusable_workflow in permissions_analysis:
                analysis = permissions_analysis[reusable_workflow]
                # Use minimal permissions as the baseline
                minimal_perms = analysis.get("minimal_permissions", [])
                required_permissions.extend(minimal_perms)

        # Parse and merge permissions
        perm_dicts = [parse_permissions(required_permissions)]
        merged_permissions = merge_permissions(perm_dicts)

        # Check if workflow already has permissions
        has_existing_permissions = has_permissions_block(content)

        return {
            "reusable_calls": reusable_calls,
            "required_permissions": merged_permissions,
            "has_existing_permissions": has_existing_permissions,
            "file_size": len(content),
            "analysis_successful": True,
        }

    except Exception as e:
        logger.error(f"Error analyzing {file_path}: {e}")
        return {"analysis_successful": False, "error": str(e)}


def update_calling_workflow(
    file_path: Path, analysis: Dict[str, Any], dry_run: bool = False
) -> Dict[str, Any]:
    """Update a calling workflow with required permissions."""
    try:
        with open(file_path, "r") as f:
            original_content = f.read()

        if not analysis["required_permissions"]:
            return {"status": "no_permissions_needed", "analysis": analysis}

        # Update the workflow
        if analysis["has_existing_permissions"]:
            modified_content = update_existing_permissions(
                original_content, analysis["required_permissions"]
            )
        else:
            modified_content = add_permissions_to_workflow(
                original_content, analysis["required_permissions"]
            )

        if original_content == modified_content:
            return {"status": "no_changes_needed", "analysis": analysis}

        if dry_run:
            return {
                "status": "would_modify",
                "analysis": analysis,
                "original_size": len(original_content),
                "modified_size": len(modified_content),
            }

        # Write the updated file
        with open(file_path, "w") as f:
            f.write(modified_content)

        return {
            "status": "modified",
            "analysis": analysis,
            "original_size": len(original_content),
            "modified_size": len(modified_content),
        }

    except Exception as e:
        logger.error(f"Error updating {file_path}: {e}")
        return {"status": "error", "error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="Update calling workflows with required permissions"
    )
    parser.add_argument(
        "--workflows-dir",
        type=Path,
        default=Path(".github/workflows"),
        help="Directory containing workflow files",
    )
    parser.add_argument(
        "--analysis-file",
        type=Path,
        default=Path("workflow-permissions-analysis.json"),
        help="Permissions analysis file",
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

    # Load permissions analysis
    permissions_analysis = load_permissions_analysis(args.analysis_file)
    if not permissions_analysis:
        logger.error("Could not load permissions analysis")
        return 1

    workflows_dir = args.workflows_dir
    if not workflows_dir.exists():
        logger.error(f"Workflows directory not found: {workflows_dir}")
        return 1

    # Find all calling workflows
    calling_workflows = find_calling_workflows(workflows_dir)

    if not calling_workflows:
        logger.info("No calling workflows found")
        return 0

    logger.info(f"Found {len(calling_workflows)} calling workflows")

    results = {}

    # Process each workflow
    for workflow_file in calling_workflows:
        logger.info(f"Analyzing: {workflow_file.name}")

        # Analyze the workflow
        analysis = analyze_calling_workflow(workflow_file, permissions_analysis)

        if not analysis["analysis_successful"]:
            results[str(workflow_file)] = {
                "status": "analysis_error",
                "error": analysis.get("error"),
            }
            continue

        # Update the workflow
        result = update_calling_workflow(workflow_file, analysis, dry_run=args.dry_run)
        results[str(workflow_file)] = result

    # Summary
    print("\n" + "=" * 70)
    print("CALLING WORKFLOW UPDATE SUMMARY")
    print("=" * 70)

    modified_count = 0
    already_correct_count = 0
    error_count = 0

    for file_path, result in results.items():
        status = result["status"]
        file_name = Path(file_path).name

        if status == "modified" or status == "would_modify":
            modified_count += 1
            print(f"✓ {file_name}: {status}")

            # Show what reusable workflows are called
            analysis = result.get("analysis", {})
            reusable_calls = analysis.get("reusable_calls", [])
            if reusable_calls:
                print(f"  - Calls: {', '.join(reusable_calls)}")

            # Show permissions added
            permissions = analysis.get("required_permissions", {})
            if permissions:
                print(
                    f"  - Permissions: {', '.join(f'{k}:{v}' for k, v in permissions.items())}"
                )

        elif status == "no_permissions_needed":
            already_correct_count += 1
            print(f"✅ {file_name}: already correct (no reusable workflows called)")

        elif status == "no_changes_needed":
            already_correct_count += 1
            print(f"✅ {file_name}: already correct (permissions already sufficient)")

        else:
            error_count += 1
            print(f"❌ {file_name}: {status}")
            if "error" in result:
                print(f"  - Error: {result['error']}")

    print(f"\nFiles processed: {len(results)}")
    print(f"Modified: {modified_count}")
    print(f"Already correct: {already_correct_count}")
    print(f"Errors: {error_count}")

    if args.dry_run:
        print("\nThis was a dry run. Remove --dry-run to make actual changes.")

    return 0


if __name__ == "__main__":
    exit(main())
