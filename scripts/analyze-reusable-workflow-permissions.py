#!/usr/bin/env python3
# file: scripts/analyze-reusable-workflow-permissions.py
# version: 1.0.0
# guid: 8b9c0d1e-2f3a-4b5c-6d7e-8f9a0b1c2d3e

"""
Analyze reusable workflows to determine what permissions calling workflows need.

This script:
1. Examines reusable workflows to understand what they do
2. Extracts permissions from backup files (original permissions)
3. Creates a comprehensive guide for calling workflows
4. Suggests minimal required permissions for each reusable workflow
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, List
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Common permission mappings based on common actions
PERMISSION_MAPPINGS = {
    # Content operations
    "checkout": ["contents: read"],
    "push": ["contents: write"],
    "create_file": ["contents: write"],
    "commit": ["contents: write"],
    # Pull request operations
    "pull_request_comment": ["pull-requests: write"],
    "pull_request_create": ["pull-requests: write"],
    "pull_request_label": ["pull-requests: write"],
    "pull_request_review": ["pull-requests: write"],
    # Issue operations
    "issue_comment": ["issues: write"],
    "issue_label": ["issues: write"],
    "issue_create": ["issues: write"],
    "issue_close": ["issues: write"],
    # Release operations
    "release_create": ["contents: write"],
    "release_upload": ["contents: write"],
    # Security events
    "codeql": ["security-events: write"],
    "sarif_upload": ["security-events: write"],
    # Packages
    "package_write": ["packages: write"],
    "package_read": ["packages: read"],
    # Actions
    "actions_read": ["actions: read"],
    "actions_write": ["actions: write"],
    # Checks
    "checks_write": ["checks: write"],
    "statuses_write": ["statuses: write"],
}


def load_yaml_file(file_path: Path) -> Dict[str, Any]:
    """Load and parse a YAML file."""
    try:
        with open(file_path, "r") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return {}


def extract_permissions_from_backup(backup_path: Path) -> List[Dict[str, Any]]:
    """Extract permissions from a backup file."""
    if not backup_path.exists():
        return []

    try:
        with open(backup_path, "r") as f:
            content = f.read()

        permissions_blocks = []
        lines = content.split("\n")

        for i, line in enumerate(lines):
            if "permissions:" in line and not line.strip().startswith("#"):
                # Found a permissions block
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

                permissions_text = "\n".join(block_lines)

                # Try to parse as YAML
                try:
                    # Create a minimal YAML document
                    yaml_text = permissions_text
                    parsed = yaml.safe_load(yaml_text)
                    if isinstance(parsed, dict) and "permissions" in parsed:
                        permissions_blocks.append(parsed["permissions"])
                    else:
                        # Sometimes the permissions block is standalone
                        permissions_blocks.append(parsed)
                except Exception:
                    # If YAML parsing fails, extract manually
                    perms = {}
                    for block_line in block_lines[1:]:  # Skip the 'permissions:' line
                        if ":" in block_line and not block_line.strip().startswith("#"):
                            key, value = block_line.split(":", 1)
                            key = key.strip()
                            value = value.strip()
                            if value:
                                perms[key] = value
                    if perms:
                        permissions_blocks.append(perms)

        return permissions_blocks
    except Exception as e:
        logger.error(f"Error extracting permissions from {backup_path}: {e}")
        return []


def analyze_workflow_purpose(
    workflow_data: Dict[str, Any], file_path: Path
) -> Dict[str, Any]:
    """Analyze what a workflow does to determine required permissions."""
    analysis = {
        "purpose": "unknown",
        "actions_used": [],
        "github_api_calls": [],
        "inferred_permissions": set(),
        "description": workflow_data.get("description", ""),
    }

    # Extract actions used
    jobs = workflow_data.get("jobs", {})
    for job_name, job_data in jobs.items():
        if isinstance(job_data, dict):
            steps = job_data.get("steps", [])
            for step in steps:
                if isinstance(step, dict) and "uses" in step:
                    action = step["uses"]
                    analysis["actions_used"].append(action)

                    # Infer permissions from common actions
                    if "checkout" in action:
                        analysis["inferred_permissions"].add("contents: read")
                    elif "upload-sarif" in action or "codeql" in action:
                        analysis["inferred_permissions"].add("security-events: write")
                    elif "labeler" in action or "issue" in action.lower():
                        analysis["inferred_permissions"].update(
                            ["issues: write", "pull-requests: write"]
                        )
                    elif "goreleaser" in action or "release" in action.lower():
                        analysis["inferred_permissions"].add("contents: write")
                    elif "comment" in action.lower():
                        analysis["inferred_permissions"].update(
                            ["issues: write", "pull-requests: write"]
                        )

    # Analyze based on file name
    file_name = file_path.stem.lower()
    if "codeql" in file_name:
        analysis["purpose"] = "security_scanning"
        analysis["inferred_permissions"].add("security-events: write")
    elif "issue" in file_name:
        analysis["purpose"] = "issue_management"
        analysis["inferred_permissions"].add("issues: write")
    elif "label" in file_name:
        analysis["purpose"] = "labeling"
        analysis["inferred_permissions"].update(
            ["issues: write", "pull-requests: write"]
        )
    elif "release" in file_name or "goreleaser" in file_name:
        analysis["purpose"] = "release_management"
        analysis["inferred_permissions"].add("contents: write")
    elif "docker" in file_name:
        analysis["purpose"] = "container_build"
        analysis["inferred_permissions"].add("packages: write")
    elif "ci" in file_name:
        analysis["purpose"] = "continuous_integration"
        analysis["inferred_permissions"].add("contents: read")
    elif "docs" in file_name:
        analysis["purpose"] = "documentation"
        analysis["inferred_permissions"].add("contents: write")
    elif "stale" in file_name:
        analysis["purpose"] = "maintenance"
        analysis["inferred_permissions"].update(
            ["issues: write", "pull-requests: write"]
        )

    # Convert set to list for JSON serialization
    analysis["inferred_permissions"] = list(analysis["inferred_permissions"])

    return analysis


def generate_calling_workflow_template(
    workflow_name: str, permissions: List[str]
) -> str:
    """Generate a template for calling workflows."""
    permissions_yaml = {}
    for perm in permissions:
        if ":" in perm:
            key, value = perm.split(":", 1)
            permissions_yaml[key.strip()] = value.strip()

    template = f"""name: Example Calling Workflow

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

# Required permissions for {workflow_name}
permissions:
"""

    for key, value in permissions_yaml.items():
        template += f"  {key}: {value}\n"

    template += f"""
jobs:
  call-{workflow_name.replace("reusable-", "").replace(".yml", "")}:
    uses: ./.github/workflows/{workflow_name}
    with:
      # Add required inputs here
    secrets:
      # Add required secrets here
"""

    return template


def main():
    parser = argparse.ArgumentParser(
        description="Analyze reusable workflow permissions"
    )
    parser.add_argument(
        "--workflows-dir",
        type=Path,
        default=Path(".github/workflows"),
        help="Directory containing workflow files",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("workflow-permissions-analysis.json"),
        help="Output file for analysis results",
    )
    parser.add_argument(
        "--generate-templates",
        action="store_true",
        help="Generate calling workflow templates",
    )
    parser.add_argument(
        "--templates-dir",
        type=Path,
        default=Path("workflow-templates"),
        help="Directory to store generated templates",
    )

    args = parser.parse_args()

    workflows_dir = args.workflows_dir
    if not workflows_dir.exists():
        logger.error(f"Workflows directory not found: {workflows_dir}")
        return 1

    # Find all reusable workflows
    reusable_workflows = []
    for workflow_file in workflows_dir.glob("reusable-*.yml"):
        reusable_workflows.append(workflow_file)

    if not reusable_workflows:
        logger.info("No reusable workflows found")
        return 0

    logger.info(f"Analyzing {len(reusable_workflows)} reusable workflows")

    analysis_results = {}

    for workflow_file in reusable_workflows:
        logger.info(f"Analyzing: {workflow_file.name}")

        # Load current workflow (without permissions)
        workflow_data = load_yaml_file(workflow_file)

        # Load original permissions from backup
        backup_file = workflow_file.with_suffix(f"{workflow_file.suffix}.backup")
        original_permissions = extract_permissions_from_backup(backup_file)

        # Analyze workflow purpose
        purpose_analysis = analyze_workflow_purpose(workflow_data, workflow_file)

        # Combine analysis
        workflow_analysis = {
            "file_name": workflow_file.name,
            "original_permissions": original_permissions,
            "purpose_analysis": purpose_analysis,
            "recommended_permissions": [],
            "minimal_permissions": [],
        }

        # Determine recommended permissions
        all_permissions = set()

        # Add original permissions
        for perm_block in original_permissions:
            if isinstance(perm_block, dict):
                for key, value in perm_block.items():
                    all_permissions.add(f"{key}: {value}")

        # Add inferred permissions
        all_permissions.update(purpose_analysis["inferred_permissions"])

        workflow_analysis["recommended_permissions"] = list(all_permissions)

        # Determine minimal permissions (most restrictive that still work)
        minimal_perms = set()
        if purpose_analysis["purpose"] == "security_scanning":
            minimal_perms.update(["contents: read", "security-events: write"])
        elif purpose_analysis["purpose"] == "issue_management":
            minimal_perms.update(["contents: read", "issues: write"])
        elif purpose_analysis["purpose"] == "labeling":
            minimal_perms.update(
                ["contents: read", "issues: write", "pull-requests: write"]
            )
        elif purpose_analysis["purpose"] == "release_management":
            minimal_perms.update(["contents: write"])
        elif purpose_analysis["purpose"] == "container_build":
            minimal_perms.update(["contents: read", "packages: write"])
        elif purpose_analysis["purpose"] == "documentation":
            minimal_perms.update(["contents: write"])
        elif purpose_analysis["purpose"] == "maintenance":
            minimal_perms.update(
                ["contents: read", "issues: write", "pull-requests: write"]
            )
        else:
            # Default safe permissions
            minimal_perms.update(["contents: read"])

        workflow_analysis["minimal_permissions"] = list(minimal_perms)

        analysis_results[workflow_file.name] = workflow_analysis

    # Save analysis results
    with open(args.output, "w") as f:
        json.dump(analysis_results, f, indent=2)

    logger.info(f"Analysis saved to: {args.output}")

    # Generate templates if requested
    if args.generate_templates:
        templates_dir = args.templates_dir
        templates_dir.mkdir(exist_ok=True)

        for workflow_name, analysis in analysis_results.items():
            template = generate_calling_workflow_template(
                workflow_name, analysis["recommended_permissions"]
            )

            template_file = templates_dir / f"example-{workflow_name}"
            with open(template_file, "w") as f:
                f.write(template)

            logger.info(f"Generated template: {template_file}")

    # Print summary
    print("\n" + "=" * 80)
    print("WORKFLOW PERMISSIONS ANALYSIS SUMMARY")
    print("=" * 80)

    for workflow_name, analysis in analysis_results.items():
        print(f"\n📁 {workflow_name}")
        print(f"   Purpose: {analysis['purpose_analysis']['purpose']}")
        print("   Minimal permissions needed:")
        for perm in analysis["minimal_permissions"]:
            print(f"     - {perm}")

        if analysis["recommended_permissions"]:
            print("   All recommended permissions:")
            for perm in analysis["recommended_permissions"]:
                print(f"     - {perm}")

    print(f"\n💾 Full analysis saved to: {args.output}")
    if args.generate_templates:
        print(f"📝 Templates generated in: {args.templates_dir}")

    return 0


if __name__ == "__main__":
    exit(main())
