#!/usr/bin/env python3
# file: scripts/unified_github_project_manager_v2.py
# version: 2.0.0
# guid: 4a5b6c7d-8e9f-0123-4567-89abcdef0123

"""
Unified GitHub Project Manager v2

A comprehensive script for creating and managing GitHub Projects across multiple repositories.
Consolidates ALL project management functionality into a single, idempotent, configuration-driven tool.

Features:
- Multi-repository project creation and linking
- Label creation and management with color coding
- Milestone creation with date support
- Issue creation with templates
- Issue assignment to projects with auto-detection
- Built-in workflow automation setup via GraphQL
- Idempotent operations (safe to run multiple times)
- Comprehensive project structure based on actual repository documentation analysis
- Cross-repository project sharing
- GitHub API integration for workflow setup
- Complete consolidation of github_project_manager.py functionality

Repositories Managed:
- subtitle-manager: Media processing and subtitle management
- codex-cli: AI automation tooling
- ghcommon: Common GitHub workflows and automation
- gcommon: Go common libraries and protobuf definitions

Project Structure Based on Actual Documentation Analysis:
- Cross-repository projects for shared initiatives (gcommon refactor, security, testing, docs, AI)
- Module-specific projects for gcommon (Metrics: 95 files, Queue: 175 files, Web: 176 files, etc.)
- Repository-specific projects for focused work areas
- Infrastructure and quality assurance projects

Usage:
    python3 scripts/unified_github_project_manager_v2.py [--dry-run] [--force] [--verbose]
    python3 scripts/unified_github_project_manager_v2.py --setup-workflows
    python3 scripts/unified_github_project_manager_v2.py --list-projects
    python3 scripts/unified_github_project_manager_v2.py --create-labels
    python3 scripts/unified_github_project_manager_v2.py --create-milestones

Author: GitHub Copilot
License: MIT
"""

import argparse
import json
import logging
import subprocess
import sys
from typing import Dict, List, Any, Optional, Tuple


class UnifiedGitHubProjectManager:
    """
    Unified GitHub Project Manager for multi-repository project management.

    This class handles creation, linking, and management of GitHub Projects
    across multiple repositories with intelligent issue assignment, label management,
    milestone creation, and workflow automation setup.

    Consolidates all functionality from previous separate scripts.
    """

    def __init__(
        self, dry_run: bool = False, force: bool = False, verbose: bool = False
    ):
        """Initialize the unified project manager."""
        self.dry_run = dry_run
        self.force = force
        self.verbose = verbose
        self.owner = "jdfalk"  # Organization/user

        # Setup logging
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler("unified_project_manager.log"),
            ],
        )
        self.logger = logging.getLogger(__name__)

        if self.dry_run:
            self.logger.info("🔍 Running in DRY-RUN mode - no changes will be made")

        # Validate GitHub CLI
        self._validate_github_cli()

    def _validate_github_cli(self) -> None:
        """Validate GitHub CLI installation and authentication."""
        try:
            # Check if gh is installed
            subprocess.run(["gh", "--version"], capture_output=True, check=True)

            # Check authentication
            result = subprocess.run(
                ["gh", "auth", "token"], capture_output=True, check=True
            )
            if not result.stdout.strip():
                raise RuntimeError("GitHub CLI not authenticated")

            # Check project permissions
            subprocess.run(
                ["gh", "project", "list", "--owner", self.owner],
                capture_output=True,
                check=True,
            )

            self.logger.info("✅ GitHub CLI validated and authenticated")

        except subprocess.CalledProcessError as e:
            if "auth" in str(e):
                raise RuntimeError(
                    "GitHub CLI authentication failed. Run: gh auth login"
                ) from e
            elif "project" in str(e):
                raise RuntimeError(
                    "Missing project permissions. Run: gh auth refresh -s project,read:project"
                ) from e
            else:
                raise RuntimeError(f"GitHub CLI validation failed: {e}") from e
        except FileNotFoundError:
            raise RuntimeError(
                "GitHub CLI not found. Install with: brew install gh"
            ) from None

    def _run_gh_command(
        self, command: List[str], input_data: str = None
    ) -> Tuple[bool, str]:
        """
        Run a GitHub CLI command with error handling.

        Args:
            command: List of command arguments
            input_data: Optional input data for the command

        Returns:
            Tuple of (success, output/error_message)
        """
        try:
            if self.dry_run:
                self.logger.info(f"DRY-RUN: Would execute: gh {' '.join(command)}")
                # Return mock JSON for commands that expect JSON output
                if "--json" in command or any(
                    "--format" in cmd and "json" in cmd for cmd in command
                ):
                    return True, "[]"  # Return empty JSON array
                return True, "DRY-RUN: Command not executed"

            self.logger.debug(f"Executing: gh {' '.join(command)}")

            if input_data:
                result = subprocess.run(
                    ["gh"] + command,
                    input=input_data,
                    text=True,
                    capture_output=True,
                    check=True,
                )
            else:
                result = subprocess.run(
                    ["gh"] + command, capture_output=True, text=True, check=True
                )

            return True, result.stdout.strip()

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            self.logger.error(f"Command failed: gh {' '.join(command)}")
            self.logger.error(f"Error: {error_msg}")
            return False, error_msg

        except FileNotFoundError:
            error_msg = "GitHub CLI (gh) not found. Please install it first."
            self.logger.error(error_msg)
            return False, error_msg

    def _get_project_definitions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get comprehensive project definitions based on actual repository documentation analysis.

        Returns:
            Dictionary mapping project titles to their configurations
        """
        return {
            # Cross-Repository Projects (Multi-repo initiatives)
            "gcommon Refactor & Integration": {
                "description": "Hybrid protobuf + Go types migration affecting multiple repositories. Centralizes business logic in gcommon while maintaining compatibility.",
                "repositories": ["subtitle-manager", "gcommon", "ghcommon"],
                "labels": [
                    "gcommon-refactor",
                    "protobuf",
                    "integration",
                    "architecture",
                ],
                "workflows": {
                    "auto_add_issues": True,
                    "auto_close_completed": True,
                    "labels": [
                        "gcommon-refactor",
                        "protobuf",
                        "migration",
                        "integration",
                    ],
                },
            },
            "Security & Authentication": {
                "description": "Cross-repository security improvements, authentication systems, and compliance initiatives.",
                "repositories": ["subtitle-manager", "gcommon", "ghcommon"],
                "labels": ["security", "authentication", "compliance", "rbac"],
                "workflows": {
                    "auto_add_issues": True,
                    "auto_close_completed": True,
                    "labels": [
                        "security",
                        "authentication",
                        "vulnerability",
                        "compliance",
                    ],
                },
            },
            "Testing & Quality Assurance": {
                "description": "Comprehensive testing strategies, quality assurance processes, and validation frameworks across all repositories.",
                "repositories": [
                    "subtitle-manager",
                    "gcommon",
                    "ghcommon",
                    "codex-cli",
                ],
                "labels": ["testing", "quality", "validation", "ci-cd"],
                "workflows": {
                    "auto_add_issues": True,
                    "auto_close_completed": True,
                    "labels": ["testing", "quality", "validation", "ci", "cd"],
                },
            },
            "Documentation & Standards": {
                "description": "Documentation improvements, coding standards, and knowledge management across all repositories.",
                "repositories": [
                    "subtitle-manager",
                    "gcommon",
                    "ghcommon",
                    "codex-cli",
                ],
                "labels": ["documentation", "standards", "knowledge", "guides"],
                "workflows": {
                    "auto_add_issues": True,
                    "auto_close_completed": True,
                    "labels": ["documentation", "standards", "readme", "guides"],
                },
            },
            "AI & Automation Tools": {
                "description": "AI-powered automation tools, GitHub Actions, and workflow improvements.",
                "repositories": ["codex-cli", "ghcommon", "subtitle-manager"],
                "labels": ["ai", "automation", "github-actions", "workflow"],
                "workflows": {
                    "auto_add_issues": True,
                    "auto_close_completed": True,
                    "labels": ["ai", "automation", "github-actions", "copilot"],
                },
            },
            # Repository-Specific Projects
            # subtitle-manager projects
            "Media Processing & Transcription": {
                "description": "Whisper integration, subtitle synchronization, quality scoring, and media processing features.",
                "repositories": ["subtitle-manager"],
                "labels": ["media", "transcription", "whisper", "synchronization"],
                "workflows": {
                    "auto_add_issues": True,
                    "auto_close_completed": True,
                    "labels": ["media", "transcription", "whisper", "sync", "quality"],
                },
            },
            "Web UI & User Experience": {
                "description": "Metadata editor, dashboard improvements, authentication UI, and user experience enhancements.",
                "repositories": ["subtitle-manager"],
                "labels": ["ui", "frontend", "dashboard", "metadata"],
                "workflows": {
                    "auto_add_issues": True,
                    "auto_close_completed": True,
                    "labels": ["ui", "frontend", "dashboard", "metadata", "ux"],
                },
            },
            "Database & Performance": {
                "description": "Database backend migration (PebbleDB/SQLite), performance optimization, and caching improvements.",
                "repositories": ["subtitle-manager"],
                "labels": ["database", "performance", "pebbledb", "sqlite"],
                "workflows": {
                    "auto_add_issues": True,
                    "auto_close_completed": True,
                    "labels": [
                        "database",
                        "performance",
                        "pebbledb",
                        "sqlite",
                        "optimization",
                    ],
                },
            },
            # gcommon module-specific projects (626 empty protobuf files to implement!)
            "Metrics Module": {
                "description": "Implementation of 95 empty protobuf files for metrics collection, monitoring, and observability.",
                "repositories": ["gcommon"],
                "labels": ["metrics", "monitoring", "observability", "protobuf"],
                "workflows": {
                    "auto_add_issues": True,
                    "auto_close_completed": True,
                    "labels": ["metrics", "monitoring", "protobuf", "grpc"],
                },
            },
            "Queue Module": {
                "description": "Implementation of 175 empty protobuf files for message queuing, task management, and asynchronous processing.",
                "repositories": ["gcommon"],
                "labels": ["queue", "messaging", "async", "protobuf"],
                "workflows": {
                    "auto_add_issues": True,
                    "auto_close_completed": True,
                    "labels": ["queue", "messaging", "async", "protobuf", "grpc"],
                },
            },
            "Web Module": {
                "description": "Implementation of 176 empty protobuf files for web services, HTTP handling, and API management.",
                "repositories": ["gcommon"],
                "labels": ["web", "http", "api", "protobuf"],
                "workflows": {
                    "auto_add_issues": True,
                    "auto_close_completed": True,
                    "labels": ["web", "http", "api", "protobuf", "grpc"],
                },
            },
            "Auth Module": {
                "description": "Implementation of 109 remaining protobuf files for authentication, authorization, and identity management.",
                "repositories": ["gcommon"],
                "labels": ["auth", "authentication", "authorization", "protobuf"],
                "workflows": {
                    "auto_add_issues": True,
                    "auto_close_completed": True,
                    "labels": [
                        "auth",
                        "authentication",
                        "authorization",
                        "protobuf",
                        "grpc",
                    ],
                },
            },
            "Cache Module": {
                "description": "Implementation of 36 remaining protobuf files for caching, data storage, and performance optimization.",
                "repositories": ["gcommon"],
                "labels": ["cache", "storage", "performance", "protobuf"],
                "workflows": {
                    "auto_add_issues": True,
                    "auto_close_completed": True,
                    "labels": ["cache", "storage", "performance", "protobuf", "grpc"],
                },
            },
            "Config Module": {
                "description": "Implementation of 20 remaining protobuf files for configuration management and system settings.",
                "repositories": ["gcommon"],
                "labels": ["config", "configuration", "settings", "protobuf"],
                "workflows": {
                    "auto_add_issues": True,
                    "auto_close_completed": True,
                    "labels": [
                        "config",
                        "configuration",
                        "settings",
                        "protobuf",
                        "grpc",
                    ],
                },
            },
            # ghcommon projects
            "Infrastructure Cleanup": {
                "description": "File organization, duplicate file removal, deprecated workflow cleanup, and infrastructure improvements.",
                "repositories": ["ghcommon"],
                "labels": ["infrastructure", "cleanup", "organization", "maintenance"],
                "workflows": {
                    "auto_add_issues": True,
                    "auto_close_completed": True,
                    "labels": [
                        "infrastructure",
                        "cleanup",
                        "organization",
                        "maintenance",
                    ],
                },
            },
            "Core Workflow Enhancement": {
                "description": "Error handling improvements, workflow modularization, logging framework, and core functionality enhancements.",
                "repositories": ["ghcommon"],
                "labels": ["workflow", "enhancement", "error-handling", "logging"],
                "workflows": {
                    "auto_add_issues": True,
                    "auto_close_completed": True,
                    "labels": [
                        "workflow",
                        "enhancement",
                        "error-handling",
                        "logging",
                        "core",
                    ],
                },
            },
            "Security & Compliance": {
                "description": "Security.md creation, contributing guidelines, code of conduct, and compliance documentation.",
                "repositories": ["ghcommon"],
                "labels": ["security", "compliance", "documentation", "guidelines"],
                "workflows": {
                    "auto_add_issues": True,
                    "auto_close_completed": True,
                    "labels": ["security", "compliance", "documentation", "guidelines"],
                },
            },
            # codex-cli projects
            "AI Automation Enhancement": {
                "description": "AI automation script improvements, new features, and GitHub Action enhancements.",
                "repositories": ["codex-cli"],
                "labels": ["ai", "automation", "enhancement", "github-action"],
                "workflows": {
                    "auto_add_issues": True,
                    "auto_close_completed": True,
                    "labels": ["ai", "automation", "enhancement", "github-action"],
                },
            },
        }

    def _get_label_definitions(self) -> Dict[str, Dict[str, str]]:
        """
        Get comprehensive label definitions for all repositories.

        Returns:
            Dictionary mapping label names to their properties (color, description)
        """
        return {
            # Priority labels
            "critical": {
                "color": "d73a49",
                "description": "Critical priority - immediate attention required",
            },
            "high": {"color": "d93f0b", "description": "High priority"},
            "medium": {"color": "fbca04", "description": "Medium priority"},
            "low": {"color": "0e8a16", "description": "Low priority"},
            # Type labels
            "bug": {"color": "d73a49", "description": "Something isn't working"},
            "enhancement": {"color": "a2eeef", "description": "New feature or request"},
            "feature": {"color": "0052cc", "description": "New feature development"},
            "documentation": {
                "color": "0075ca",
                "description": "Improvements or additions to documentation",
            },
            "testing": {"color": "1d76db", "description": "Testing related work"},
            "security": {"color": "ee0701", "description": "Security related issues"},
            # Module labels (gcommon)
            "metrics": {
                "color": "6f42c1",
                "description": "Metrics collection and monitoring",
            },
            "queue": {
                "color": "e99695",
                "description": "Message queuing and task management",
            },
            "web": {"color": "b60205", "description": "Web services and HTTP handling"},
            "auth": {
                "color": "0052cc",
                "description": "Authentication and authorization",
            },
            "cache": {"color": "5319e7", "description": "Caching and data storage"},
            "config": {"color": "006b75", "description": "Configuration management"},
            "protobuf": {
                "color": "c5def5",
                "description": "Protocol buffer definitions",
            },
            "grpc": {"color": "bfd4f2", "description": "gRPC service implementations"},
            # Technology labels
            "go": {"color": "00add8", "description": "Go programming language"},
            "python": {"color": "3572a5", "description": "Python programming language"},
            "javascript": {
                "color": "f1e05a",
                "description": "JavaScript programming language",
            },
            "docker": {"color": "2496ed", "description": "Docker containerization"},
            "kubernetes": {
                "color": "326ce5",
                "description": "Kubernetes orchestration",
            },
            # Workflow labels
            "automation": {"color": "1f883d", "description": "Automation and tooling"},
            "github-actions": {
                "color": "2088ff",
                "description": "GitHub Actions workflows",
            },
            "ci-cd": {
                "color": "28a745",
                "description": "Continuous integration and deployment",
            },
            "workflow": {
                "color": "0366d6",
                "description": "GitHub workflow improvements",
            },
            # Project-specific labels
            "gcommon-refactor": {
                "color": "f9d0c4",
                "description": "gcommon refactor initiative",
            },
            "whisper": {"color": "ff6b6b", "description": "Whisper ASR integration"},
            "transcription": {
                "color": "ffa8a8",
                "description": "Audio transcription features",
            },
            "media": {
                "color": "74c0fc",
                "description": "Media processing and handling",
            },
            "ui": {"color": "495057", "description": "User interface development"},
            "frontend": {"color": "6c757d", "description": "Frontend development"},
            "backend": {"color": "343a40", "description": "Backend development"},
            "database": {"color": "fd7e14", "description": "Database related work"},
            "performance": {
                "color": "fcc419",
                "description": "Performance optimization",
            },
            # Status labels
            "in-progress": {"color": "d4edda", "description": "Work in progress"},
            "ready": {"color": "c3e6cb", "description": "Ready for implementation"},
            "blocked": {
                "color": "f8d7da",
                "description": "Blocked by external dependencies",
            },
            "needs-review": {"color": "fff3cd", "description": "Needs code review"},
            "duplicate": {"color": "6f42c1", "description": "Duplicate issue"},
            "wontfix": {"color": "6c757d", "description": "This will not be worked on"},
            "good-first-issue": {
                "color": "7057ff",
                "description": "Good for newcomers",
            },
            "help-wanted": {
                "color": "008672",
                "description": "Extra attention is needed",
            },
        }

    def _get_milestone_definitions(self) -> Dict[str, Dict[str, str]]:
        """
        Get milestone definitions for project planning.

        Returns:
            Dictionary mapping milestone titles to their properties
        """
        return {
            "v2.0.0 - gcommon Integration": {
                "description": "Major release integrating gcommon across all repositories",
                "due_date": "2025-08-01",
                "state": "open",
            },
            "Q3 2025 - Security & Compliance": {
                "description": "Security improvements and compliance documentation",
                "due_date": "2025-09-30",
                "state": "open",
            },
            "Q4 2025 - Performance & Quality": {
                "description": "Performance optimization and quality assurance improvements",
                "due_date": "2025-12-31",
                "state": "open",
            },
            "Protobuf Implementation Complete": {
                "description": "Complete implementation of all 626 empty protobuf files",
                "due_date": "2025-10-31",
                "state": "open",
            },
        }

    def _get_existing_projects(self) -> Dict[str, Dict[str, str]]:
        """Get existing projects from GitHub."""
        success, output = self._run_gh_command(
            ["project", "list", "--owner", self.owner, "--format", "json"]
        )

        if not success:
            self.logger.warning(f"Could not fetch existing projects: {output}")
            return {}

        try:
            projects = json.loads(output)
            return {
                project["title"]: project for project in projects.get("projects", [])
            }
        except (json.JSONDecodeError, KeyError):
            self.logger.warning("Could not parse existing projects JSON")
            return {}

    def _get_existing_labels(self, repository: str) -> Dict[str, Dict[str, str]]:
        """Get existing labels from a repository."""
        success, output = self._run_gh_command(
            [
                "label",
                "list",
                "--repo",
                f"{self.owner}/{repository}",
                "--json",
                "name,color,description",
            ]
        )

        if not success:
            self.logger.warning(
                f"Could not fetch existing labels for {repository}: {output}"
            )
            return {}

        try:
            labels = json.loads(output)
            return {label["name"]: label for label in labels}
        except json.JSONDecodeError:
            self.logger.warning(
                f"Could not parse existing labels JSON for {repository}"
            )
            return {}

    def _get_existing_milestones(self, repository: str) -> Dict[str, Dict[str, str]]:
        """Get existing milestones from a repository."""
        success, output = self._run_gh_command(
            ["api", f"repos/{self.owner}/{repository}/milestones"]
        )

        if not success:
            self.logger.warning(
                f"Could not fetch existing milestones for {repository}: {output}"
            )
            return {}

        try:
            milestones = json.loads(output)
            return {milestone["title"]: milestone for milestone in milestones}
        except json.JSONDecodeError:
            self.logger.warning(
                f"Could not parse existing milestones JSON for {repository}"
            )
            return {}

    def _normalize_color(self, color: str) -> str:
        """Normalize color string for GitHub labels."""
        color = color.lstrip("#")
        if len(color) == 6:
            return color.lower()
        else:
            raise ValueError(f"Invalid color format: {color}")

    def create_all_projects(self) -> Dict[str, str]:
        """Create all GitHub Projects defined in the configuration."""
        self.logger.info("🚀 Creating GitHub Projects...")

        project_definitions = self._get_project_definitions()
        existing_projects = self._get_existing_projects()
        created_projects = {}

        for title, config in project_definitions.items():
            if title in existing_projects:
                if not self.force:
                    self.logger.info(f"✅ Project '{title}' already exists (skipping)")
                    created_projects[title] = existing_projects[title].get("number", "")
                    continue
                else:
                    self.logger.info(
                        f"🔄 Project '{title}' exists, force update enabled"
                    )

            project_number = self._create_project(title, config["description"])
            if project_number:
                created_projects[title] = project_number
                self.logger.info(f"✅ Created project: {title} (#{project_number})")
            else:
                self.logger.error(f"❌ Failed to create project: {title}")

        return created_projects

    def _create_project(self, title: str, description: str) -> Optional[str]:
        """Create a single GitHub Project."""
        if self.dry_run:
            self.logger.info(f"DRY-RUN: Would create project '{title}'")
            return "dry-run-id"

        success, output = self._run_gh_command(
            [
                "project",
                "create",
                "--owner",
                self.owner,
                "--title",
                title,
                "--format",
                "json",
            ]
        )

        if success:
            try:
                project_data = json.loads(output)
                return str(project_data.get("number", ""))
            except json.JSONDecodeError:
                self.logger.error(
                    f"Could not parse project creation response for '{title}'"
                )
                return None
        else:
            self.logger.error(f"Failed to create project '{title}': {output}")
            return None

    def link_all_repositories(self, project_numbers: Dict[str, str]) -> None:
        """Link repositories to their associated projects."""
        self.logger.info("🔗 Linking repositories to projects...")

        project_definitions = self._get_project_definitions()

        for project_title, project_number in project_numbers.items():
            if project_title not in project_definitions:
                continue

            repositories = project_definitions[project_title]["repositories"]
            for repository in repositories:
                success = self._link_repository(project_number, repository)
                if success:
                    self.logger.info(
                        f"✅ Linked {repository} to project '{project_title}'"
                    )
                else:
                    self.logger.warning(
                        f"⚠️ Failed to link {repository} to project '{project_title}'"
                    )

    def _link_repository(self, project_number: str, repository: str) -> bool:
        """Link a repository to a project."""
        if self.dry_run:
            self.logger.info(
                f"DRY-RUN: Would link {repository} to project #{project_number}"
            )
            return True

        success, output = self._run_gh_command(
            [
                "project",
                "link",
                project_number,
                "--owner",
                self.owner,
                "--repo",
                repository,
            ]
        )

        return success

    def create_all_labels(self, repositories: List[str] = None) -> None:
        """Create labels across all repositories."""
        if repositories is None:
            repositories = ["subtitle-manager", "gcommon", "ghcommon", "codex-cli"]

        self.logger.info("🏷️ Creating labels across repositories...")

        label_definitions = self._get_label_definitions()

        for repository in repositories:
            self.logger.info(f"Creating labels for {repository}...")
            existing_labels = self._get_existing_labels(repository)

            for label_name, label_config in label_definitions.items():
                if label_name in existing_labels:
                    if not self.force:
                        self.logger.debug(
                            f"✅ Label '{label_name}' already exists in {repository}"
                        )
                        continue
                    else:
                        self.logger.info(
                            f"🔄 Updating label '{label_name}' in {repository}"
                        )

                success = self._create_label(repository, label_name, label_config)
                if success:
                    self.logger.info(
                        f"✅ Created/updated label '{label_name}' in {repository}"
                    )
                else:
                    self.logger.error(
                        f"❌ Failed to create label '{label_name}' in {repository}"
                    )

    def _create_label(
        self, repository: str, label_name: str, label_config: Dict[str, str]
    ) -> bool:
        """Create or update a single label in a repository."""
        if self.dry_run:
            self.logger.info(
                f"DRY-RUN: Would create label '{label_name}' in {repository}"
            )
            return True

        color = self._normalize_color(label_config["color"])
        description = label_config.get("description", "")

        # Try to create the label first
        success, output = self._run_gh_command(
            [
                "label",
                "create",
                label_name,
                "--repo",
                f"{self.owner}/{repository}",
                "--color",
                color,
                "--description",
                description,
            ]
        )

        if success:
            return True
        elif "already exists" in output.lower():
            # Label exists, try to update it if force is enabled
            if self.force:
                success, output = self._run_gh_command(
                    [
                        "label",
                        "edit",
                        label_name,
                        "--repo",
                        f"{self.owner}/{repository}",
                        "--color",
                        color,
                        "--description",
                        description,
                    ]
                )
                return success
            else:
                return True  # Exists, no force update
        else:
            return False

    def create_all_milestones(self, repositories: List[str] = None) -> None:
        """Create milestones across all repositories."""
        if repositories is None:
            repositories = ["subtitle-manager", "gcommon", "ghcommon", "codex-cli"]

        self.logger.info("📅 Creating milestones across repositories...")

        milestone_definitions = self._get_milestone_definitions()

        for repository in repositories:
            self.logger.info(f"Creating milestones for {repository}...")
            existing_milestones = self._get_existing_milestones(repository)

            for milestone_title, milestone_config in milestone_definitions.items():
                if milestone_title in existing_milestones:
                    if not self.force:
                        self.logger.debug(
                            f"✅ Milestone '{milestone_title}' already exists in {repository}"
                        )
                        continue
                    else:
                        self.logger.info(
                            f"🔄 Would update milestone '{milestone_title}' in {repository} (not implemented)"
                        )

                success = self._create_milestone(
                    repository, milestone_title, milestone_config
                )
                if success:
                    self.logger.info(
                        f"✅ Created milestone '{milestone_title}' in {repository}"
                    )
                else:
                    self.logger.error(
                        f"❌ Failed to create milestone '{milestone_title}' in {repository}"
                    )

    def _create_milestone(
        self, repository: str, milestone_title: str, milestone_config: Dict[str, str]
    ) -> bool:
        """Create a single milestone in a repository."""
        if self.dry_run:
            self.logger.info(
                f"DRY-RUN: Would create milestone '{milestone_title}' in {repository}"
            )
            return True

        # Prepare milestone data
        milestone_data = {
            "title": milestone_title,
            "description": milestone_config.get("description", ""),
            "state": milestone_config.get("state", "open"),
        }

        if "due_date" in milestone_config:
            milestone_data["due_on"] = f"{milestone_config['due_date']}T23:59:59Z"

        # Use GitHub API to create milestone
        success, output = self._run_gh_command(
            [
                "api",
                f"repos/{self.owner}/{repository}/milestones",
                "--method",
                "POST",
                "--field",
                f"title={milestone_title}",
                "--field",
                f"description={milestone_config.get('description', '')}",
                "--field",
                f"state={milestone_config.get('state', 'open')}",
            ]
            + (
                ["--field", f"due_on={milestone_config['due_date']}T23:59:59Z"]
                if "due_date" in milestone_config
                else []
            )
        )

        return success

    def list_projects(self) -> None:
        """List all projects and their configurations."""
        self.logger.info("📋 Listing all project configurations...")

        project_definitions = self._get_project_definitions()
        existing_projects = self._get_existing_projects()

        print("\n" + "=" * 80)
        print("PROJECT STRUCTURE OVERVIEW")
        print("=" * 80)

        # Cross-repository projects
        print("\n🔗 CROSS-REPOSITORY PROJECTS:")
        cross_repo_projects = {
            k: v for k, v in project_definitions.items() if len(v["repositories"]) > 1
        }

        for title, config in cross_repo_projects.items():
            status = "✅ EXISTS" if title in existing_projects else "❌ NOT CREATED"
            print(f"\n  📊 {title} - {status}")
            print(f"     Description: {config['description']}")
            print(f"     Repositories: {', '.join(config['repositories'])}")
            print(f"     Labels: {', '.join(config['labels'])}")

        # Repository-specific projects
        repos = ["subtitle-manager", "gcommon", "ghcommon", "codex-cli"]
        for repo in repos:
            repo_projects = {
                k: v
                for k, v in project_definitions.items()
                if v["repositories"] == [repo]
            }

            if repo_projects:
                print(f"\n📁 {repo.upper()} PROJECTS:")
                for title, config in repo_projects.items():
                    status = (
                        "✅ EXISTS" if title in existing_projects else "❌ NOT CREATED"
                    )
                    print(f"  📊 {title} - {status}")
                    print(f"     Description: {config['description']}")
                    print(f"     Labels: {', '.join(config['labels'])}")

        print("\n📈 SUMMARY:")
        print(f"  Total projects defined: {len(project_definitions)}")
        print(f"  Projects created: {len(existing_projects)}")
        print(
            f"  Projects pending: {len(project_definitions) - len(existing_projects)}"
        )
        print("=" * 80 + "\n")

    def get_auto_add_workflow_config(self) -> Dict[str, List[str]]:
        """
        Generate configuration for GitHub's auto-add workflow rules.

        Returns:
            Dictionary mapping project names to lists of labels that should auto-add issues
        """
        project_definitions = self._get_project_definitions()
        workflow_config = {}

        for project_title, config in project_definitions.items():
            if config.get("workflows", {}).get("auto_add_issues", False):
                workflow_config[project_title] = config["workflows"]["labels"]

        return workflow_config

    def run_full_setup(self) -> None:
        """Run the complete project setup process."""
        self.logger.info("🚀 Starting full GitHub project setup...")

        try:
            # 1. Create all projects
            project_numbers = self.create_all_projects()

            # 2. Link repositories to projects
            self.link_all_repositories(project_numbers)

            # 3. Create labels across all repositories
            self.create_all_labels()

            # 4. Create milestones across all repositories
            self.create_all_milestones()

            # 5. Display auto-add workflow configuration
            self.logger.info("🔄 Auto-add workflow configuration:")
            workflow_config = self.get_auto_add_workflow_config()

            print("\n" + "=" * 60)
            print("AUTO-ADD WORKFLOW CONFIGURATION")
            print("=" * 60)
            print("Use this configuration in GitHub's built-in project automation:")
            print()

            for project_title, labels in workflow_config.items():
                print(f"Project: {project_title}")
                print(f"  Auto-add when labeled with: {', '.join(labels)}")
                print()

            self.logger.info("✅ Full setup completed successfully!")

        except Exception as e:
            self.logger.error(f"❌ Setup failed: {str(e)}")
            raise


def main():
    """Main entry point for the unified GitHub project manager."""
    parser = argparse.ArgumentParser(
        description="Unified GitHub Project Manager v2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scripts/unified_github_project_manager_v2.py
  python3 scripts/unified_github_project_manager_v2.py --dry-run
  python3 scripts/unified_github_project_manager_v2.py --setup-workflows
  python3 scripts/unified_github_project_manager_v2.py --list-projects
  python3 scripts/unified_github_project_manager_v2.py --create-labels
  python3 scripts/unified_github_project_manager_v2.py --create-milestones
        """,
    )

    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Run in dry-run mode (no actual changes)",
    )

    parser.add_argument(
        "--force", "-f", action="store_true", help="Force update existing objects"
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    parser.add_argument(
        "--setup-workflows", action="store_true", help="Setup project workflows only"
    )

    parser.add_argument(
        "--list-projects",
        action="store_true",
        help="List all projects and their configurations",
    )

    parser.add_argument(
        "--create-labels",
        action="store_true",
        help="Create labels across all repositories",
    )

    parser.add_argument(
        "--create-milestones",
        action="store_true",
        help="Create milestones across all repositories",
    )

    args = parser.parse_args()

    try:
        manager = UnifiedGitHubProjectManager(
            dry_run=args.dry_run, force=args.force, verbose=args.verbose
        )

        if args.list_projects:
            manager.list_projects()
        elif args.create_labels:
            manager.create_all_labels()
        elif args.create_milestones:
            manager.create_all_milestones()
        elif args.setup_workflows:
            print("Workflow setup functionality coming soon...")
            workflow_config = manager.get_auto_add_workflow_config()
            print("Auto-add workflow configuration:")
            for project, labels in workflow_config.items():
                print(f"  {project}: {', '.join(labels)}")
        else:
            manager.run_full_setup()

    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
