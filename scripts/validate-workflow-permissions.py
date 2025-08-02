#!/usr/bin/env python3
# file: scripts/validate-workflow-permissions.py
# version: 1.0.0
# guid: a0b1c2d3-e4f5-6789-abcd-ef0123456789

"""
Validate that workflow permissions migration was successful.

This script:
1. Verifies that reusable workflows have no permissions blocks
2. Checks that calling workflows have appropriate permissions
3. Validates workflow syntax
4. Reports any issues found
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, Tuple
import argparse
import logging
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_yaml_file(file_path: Path) -> Tuple[Dict[str, Any], bool]:
    """Load and parse a YAML file, return (data, success)."""
    try:
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)
        return data or {}, True
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return {}, False


def has_permissions_block(content: str) -> bool:
    """Check if content has a permissions block (not commented out)."""
    lines = content.split("\n")
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("permissions:") and not stripped.startswith("#"):
            return True
    return False


def extract_permissions(content: str) -> Dict[str, str]:
    """Extract permissions from workflow content."""
    permissions = {}
    lines = content.split("\n")
    in_permissions = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("permissions:") and not stripped.startswith("#"):
            in_permissions = True
            continue

        if in_permissions:
            if stripped == "" or line.startswith("#"):
                continue
            elif ":" in stripped and line.startswith(" "):
                key, value = stripped.split(":", 1)
                permissions[key.strip()] = value.strip()
            elif not line.startswith(" ") and stripped:
                # End of permissions block
                break

    return permissions


def validate_reusable_workflow(file_path: Path) -> Dict[str, Any]:
    """Validate a reusable workflow."""
    result = {
        "file": file_path.name,
        "is_valid": True,
        "issues": [],
        "has_permissions": False,
        "is_reusable": False,
    }

    try:
        with open(file_path, "r") as f:
            content = f.read()

        # Check if it's actually a reusable workflow
        if "workflow_call:" in content:
            result["is_reusable"] = True
        else:
            result["issues"].append(
                "File does not appear to be a reusable workflow (no workflow_call trigger)"
            )
            result["is_valid"] = False

        # Check for permissions blocks
        if has_permissions_block(content):
            result["has_permissions"] = True
            result["issues"].append(
                "Reusable workflow should not have permissions block"
            )
            result["is_valid"] = False

        # Try to parse as YAML
        workflow_data, yaml_valid = load_yaml_file(file_path)
        if not yaml_valid:
            result["issues"].append("Invalid YAML syntax")
            result["is_valid"] = False

        # Check for proper comments where permissions were removed
        if "Permissions removed - should be set in calling workflow" not in content:
            result["issues"].append(
                "Missing explanatory comment about removed permissions"
            )

    except Exception as e:
        result["issues"].append(f"Error reading file: {e}")
        result["is_valid"] = False

    return result


def validate_calling_workflow(
    file_path: Path, analysis_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Validate a calling workflow."""
    result = {
        "file": file_path.name,
        "is_valid": True,
        "issues": [],
        "has_permissions": False,
        "reusable_calls": [],
        "permissions": {},
        "required_permissions": {},
    }

    try:
        with open(file_path, "r") as f:
            content = f.read()

        # Extract reusable workflow calls
        uses_pattern = (
            r'uses:\s*["\']?\./?\.github\/workflows\/(reusable-[^"\'\s]+\.yml)["\']?'
        )
        matches = re.findall(uses_pattern, content)
        result["reusable_calls"] = list(set(matches))

        # Check if it has permissions
        result["has_permissions"] = has_permissions_block(content)

        if result["has_permissions"]:
            result["permissions"] = extract_permissions(content)

        # Determine required permissions based on reusable workflows called
        required_perms = {}
        for reusable_workflow in result["reusable_calls"]:
            if reusable_workflow in analysis_data:
                workflow_analysis = analysis_data[reusable_workflow]
                minimal_perms = workflow_analysis.get("minimal_permissions", [])
                for perm in minimal_perms:
                    if ":" in perm:
                        key, value = perm.split(":", 1)
                        current_value = required_perms.get(key.strip())
                        new_value = value.strip()

                        # Prefer 'write' over 'read'
                        if current_value != "write":
                            required_perms[key.strip()] = new_value

        result["required_permissions"] = required_perms

        # Validate permissions are sufficient
        if result["reusable_calls"] and required_perms:
            if not result["has_permissions"]:
                result["issues"].append(
                    "Workflow calls reusable workflows but has no permissions block"
                )
                result["is_valid"] = False
            else:
                # Check if all required permissions are present
                for req_key, req_value in required_perms.items():
                    if req_key not in result["permissions"]:
                        result["issues"].append(
                            f"Missing required permission: {req_key}: {req_value}"
                        )
                        result["is_valid"] = False
                    elif (
                        req_value == "write"
                        and result["permissions"][req_key] == "read"
                    ):
                        result["issues"].append(
                            f'Permission {req_key} should be "write" but is "read"'
                        )
                        result["is_valid"] = False

        # Try to parse as YAML
        workflow_data, yaml_valid = load_yaml_file(file_path)
        if not yaml_valid:
            result["issues"].append("Invalid YAML syntax")
            result["is_valid"] = False

    except Exception as e:
        result["issues"].append(f"Error reading file: {e}")
        result["is_valid"] = False

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Validate workflow permissions migration"
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
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    workflows_dir = args.workflows_dir
    if not workflows_dir.exists():
        logger.error(f"Workflows directory not found: {workflows_dir}")
        return 1

    # Load analysis data
    analysis_data = {}
    if args.analysis_file.exists():
        try:
            with open(args.analysis_file, "r") as f:
                analysis_data = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load analysis file: {e}")

    # Find workflow files
    reusable_workflows = list(workflows_dir.glob("reusable-*.yml"))
    calling_workflows = [
        f for f in workflows_dir.glob("*.yml") if not f.name.startswith("reusable-")
    ]

    logger.info(f"Found {len(reusable_workflows)} reusable workflows")
    logger.info(f"Found {len(calling_workflows)} calling workflows")

    # Validate reusable workflows
    reusable_results = []
    for workflow_file in reusable_workflows:
        result = validate_reusable_workflow(workflow_file)
        reusable_results.append(result)

    # Validate calling workflows
    calling_results = []
    for workflow_file in calling_workflows:
        result = validate_calling_workflow(workflow_file, analysis_data)
        calling_results.append(result)

    # Print results
    print("\n" + "=" * 80)
    print("WORKFLOW PERMISSIONS VALIDATION RESULTS")
    print("=" * 80)

    print(f"\n🔧 REUSABLE WORKFLOWS ({len(reusable_workflows)} files)")
    print("-" * 50)

    reusable_valid = 0
    for result in reusable_results:
        status = "✅" if result["is_valid"] else "❌"
        print(f"{status} {result['file']}")

        if result["is_valid"]:
            reusable_valid += 1
        else:
            for issue in result["issues"]:
                print(f"   ⚠️  {issue}")

    print(f"\n📞 CALLING WORKFLOWS ({len(calling_workflows)} files)")
    print("-" * 50)

    calling_valid = 0
    for result in calling_results:
        status = "✅" if result["is_valid"] else "❌"
        print(f"{status} {result['file']}")

        if result["is_valid"]:
            calling_valid += 1

        if result["reusable_calls"]:
            print(f"   📋 Calls: {', '.join(result['reusable_calls'])}")

        if result["permissions"]:
            perms_str = ", ".join(f"{k}:{v}" for k, v in result["permissions"].items())
            print(f"   🔐 Permissions: {perms_str}")

        if not result["is_valid"]:
            for issue in result["issues"]:
                print(f"   ⚠️  {issue}")

        if args.verbose and result["required_permissions"]:
            req_perms_str = ", ".join(
                f"{k}:{v}" for k, v in result["required_permissions"].items()
            )
            print(f"   📋 Required: {req_perms_str}")

    print("\n📊 SUMMARY")
    print("-" * 20)
    print(f"Reusable workflows: {reusable_valid}/{len(reusable_workflows)} valid")
    print(f"Calling workflows: {calling_valid}/{len(calling_workflows)} valid")

    total_valid = reusable_valid + calling_valid
    total_files = len(reusable_workflows) + len(calling_workflows)
    print(
        f"Overall: {total_valid}/{total_files} valid ({total_valid / total_files * 100:.1f}%)"
    )

    if total_valid == total_files:
        print("\n🎉 All workflows are valid! Migration successful.")
        return 0
    else:
        print(
            f"\n⚠️  {total_files - total_valid} workflows have issues that need attention."
        )
        return 1


if __name__ == "__main__":
    exit(main())
