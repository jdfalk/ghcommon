#!/usr/bin/env python3
"""
Basic test suite for ghcommon repository.

This is a shared configuration repository that contains workflow
templates and scripts but doesn't have a main Python package to test.
This file ensures CI passes by providing minimal test coverage.
"""

import unittest
import os
import sys

# Add the parent directory to Python path for importing scripts
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestBasicFunctionality(unittest.TestCase):
    """Basic functionality tests."""

    def test_imports_work(self):
        """Test that we can import standard libraries."""
        import json
        import os

        # Test that json works
        test_data = {"test": "data"}
        json_str = json.dumps(test_data)
        self.assertIn("test", json_str)

        # Test that os works
        self.assertTrue(os.path.exists("."))
        self.assertTrue(True)

    def test_repository_structure(self):
        """Test that key repository files exist."""
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Check for key files
        expected_files = [
            ".github/workflows",
            "requirements.txt",
            "README.md",
            "LICENSE",
        ]

        for file_path in expected_files:
            full_path = os.path.join(repo_root, file_path)
            self.assertTrue(
                os.path.exists(full_path),
                f"Expected file/directory {file_path} not found",
            )

    def test_requirements_readable(self):
        """Test that requirements.txt is readable."""
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        requirements_path = os.path.join(repo_root, "requirements.txt")

        with open(requirements_path, "r") as f:
            content = f.read()
            self.assertIn("PyYAML", content)


class TestWorkflowIntegrity(unittest.TestCase):
    """Test workflow file integrity."""

    def test_workflow_files_exist(self):
        """Test that key workflow files exist."""
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        workflows_dir = os.path.join(repo_root, ".github", "workflows")

        expected_workflows = ["ci.yml", "security.yml", "release.yml"]

        for workflow in expected_workflows:
            workflow_path = os.path.join(workflows_dir, workflow)
            self.assertTrue(
                os.path.exists(workflow_path), f"Expected workflow {workflow} not found"
            )

    def test_dependabot_config(self):
        """Test that dependabot.yml is valid and has groups configured."""
        import yaml
        
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dependabot_path = os.path.join(repo_root, ".github", "dependabot.yml")
        
        # Check file exists
        self.assertTrue(os.path.exists(dependabot_path), "dependabot.yml not found")
        
        # Check it's valid YAML
        with open(dependabot_path, "r") as f:
            config = yaml.safe_load(f)
        
        # Check it has updates
        self.assertIn("updates", config)
        self.assertIsInstance(config["updates"], list)
        
        # Find GitHub Actions config
        github_actions_config = None
        for update in config["updates"]:
            if update.get("package-ecosystem") == "github-actions":
                github_actions_config = update
                break
        
        self.assertIsNotNone(github_actions_config, "GitHub Actions config not found")
        
        # Check it has groups
        self.assertIn("groups", github_actions_config, "Groups not configured for GitHub Actions")
        groups = github_actions_config["groups"]
        
        # Check specific groups exist
        self.assertIn("github-actions-minor-patch", groups, "github-actions-minor-patch group not found")
        self.assertIn("github-actions-major", groups, "github-actions-major group not found")
        
        # Check github-actions-minor-patch group configuration
        minor_patch = groups["github-actions-minor-patch"]
        self.assertIn("patterns", minor_patch)
        self.assertIn("*", minor_patch["patterns"])
        self.assertIn("minor", minor_patch["update-types"])
        self.assertIn("patch", minor_patch["update-types"])
        
        # Check github-actions-major group configuration
        major = groups["github-actions-major"]
        self.assertIn("patterns", major)
        self.assertIn("*", major["patterns"])
        self.assertIn("major", major["update-types"])


if __name__ == "__main__":
    unittest.main()
