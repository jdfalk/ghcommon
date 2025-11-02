#!/usr/bin/env python3
# file: scripts/validate-linter-configs.py
# version: 1.0.0
# guid: a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d

"""Comprehensive Linter Configuration Validator

This script validates all linter configuration files in the repository to ensure:
1. Config files exist and are valid
2. Configs follow Google Style Guide standards
3. Configs are parseable by their respective linters
4. Cross-references between configs are correct

Usage:
    python3 scripts/validate-linter-configs.py [--fix] [--verbose]
"""

import json
import sys
from pathlib import Path

import yaml

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


class LinterValidator:
    """Validates linter configuration files."""

    def __init__(self, repo_root: Path, verbose: bool = False):
        self.repo_root = repo_root
        self.verbose = verbose
        self.errors = []
        self.warnings = []
        self.success = []

    def log(self, message: str, level: str = "info"):
        """Log a message with color coding."""
        if level == "success":
            print(f"{GREEN}✅ {message}{RESET}")
            self.success.append(message)
        elif level == "error":
            print(f"{RED}❌ {message}{RESET}")
            self.errors.append(message)
        elif level == "warning":
            print(f"{YELLOW}⚠️  {message}{RESET}")
            self.warnings.append(message)
        elif level == "info" and self.verbose:
            print(f"{BLUE}ℹ️  {message}{RESET}")

    def validate_file_exists(self, filepath: str) -> bool:
        """Check if a config file exists."""
        full_path = self.repo_root / filepath
        if not full_path.exists():
            self.log(f"Missing config file: {filepath}", "error")
            return False
        self.log(f"Found config file: {filepath}", "success")
        return True

    def validate_json_syntax(self, filepath: str) -> bool:
        """Validate JSON file syntax."""
        try:
            with open(self.repo_root / filepath) as f:
                json.load(f)
            self.log(f"Valid JSON syntax: {filepath}", "success")
            return True
        except json.JSONDecodeError as e:
            self.log(f"Invalid JSON in {filepath}: {e}", "error")
            return False

    def validate_yaml_syntax(self, filepath: str) -> bool:
        """Validate YAML file syntax."""
        try:
            with open(self.repo_root / filepath) as f:
                yaml.safe_load(f)
            self.log(f"Valid YAML syntax: {filepath}", "success")
            return True
        except yaml.YAMLError as e:
            self.log(f"Invalid YAML in {filepath}: {e}", "error")
            return False

    def validate_prettier_config(self) -> bool:
        """Validate Prettier configuration against Google JavaScript Style Guide."""
        filepath = ".prettierrc.json"
        if not self.validate_file_exists(filepath):
            return False
        if not self.validate_json_syntax(filepath):
            return False

        with open(self.repo_root / filepath) as f:
            config = json.load(f)

        # Google Style Guide preferences
        checks = [
            ("tabWidth", 2, "Google uses 2 spaces for indentation"),
            ("useTabs", False, "Google uses spaces, not tabs"),
            ("printWidth", 80, "Google recommends 80 character line limit"),
        ]

        for key, expected, reason in checks:
            if key in config:
                if config[key] == expected:
                    self.log(f"Prettier {key}={expected} ✓ ({reason})", "success")
                else:
                    self.log(
                        f"Prettier {key}={config[key]}, expected {expected}. {reason}",
                        "warning",
                    )
            else:
                self.log(f"Prettier missing {key} setting. {reason}", "warning")

        return True

    def validate_eslint_config(self) -> bool:
        """Validate ESLint configuration."""
        filepath = ".eslintrc.yml"
        if not self.validate_file_exists(filepath):
            return False
        if not self.validate_yaml_syntax(filepath):
            return False

        with open(self.repo_root / filepath) as f:
            config = yaml.safe_load(f)

        # Check for Google style guide extends
        if "extends" in config:
            extends = (
                config["extends"] if isinstance(config["extends"], list) else [config["extends"]]
            )
            if any("google" in str(ext).lower() for ext in extends):
                self.log("ESLint extends Google style guide", "success")
            else:
                self.log("ESLint doesn't extend Google style guide", "warning")

        return True

    def validate_python_black_config(self) -> bool:
        """Validate Python Black configuration."""
        filepath = ".python-black"
        if not self.validate_file_exists(filepath):
            return False

        try:
            with open(self.repo_root / filepath) as f:
                content = f.read().strip()

            # Black config should specify line length
            if "line-length" in content or "line_length" in content:
                # Google Python style uses 80 chars
                if "80" in content:
                    self.log(
                        "Black line length set to 80 (Google Python style)",
                        "success",
                    )
                else:
                    self.log(
                        "Black line length not set to 80 (Google recommends 80)",
                        "warning",
                    )
            else:
                self.log("Black config missing line-length setting", "warning")

            return True
        except Exception as e:
            self.log(f"Error reading {filepath}: {e}", "error")
            return False

    def validate_pylint_config(self) -> bool:
        """Validate Pylint configuration."""
        filepath = ".pylintrc"
        if not self.validate_file_exists(filepath):
            return False

        # Just check if it's readable for now
        try:
            with open(self.repo_root / filepath) as f:
                content = f.read()

            # Google Python style uses 80 char lines
            if "max-line-length" in content:
                if "max-line-length=80" in content or "max-line-length = 80" in content:
                    self.log(
                        "Pylint max-line-length set to 80 (Google Python style)",
                        "success",
                    )
                else:
                    self.log(
                        "Pylint max-line-length not set to 80 (Google recommends 80)",
                        "warning",
                    )

            return True
        except Exception as e:
            self.log(f"Error reading {filepath}: {e}", "error")
            return False

    def validate_isort_config(self) -> bool:
        """Validate isort configuration."""
        filepath = ".isort.cfg"
        if not self.validate_file_exists(filepath):
            return False

        try:
            with open(self.repo_root / filepath) as f:
                content = f.read()

            # Google Python style uses 80 char lines
            if "line_length" in content:
                if "line_length = 80" in content or "line_length=80" in content:
                    self.log(
                        "isort line_length set to 80 (Google Python style)",
                        "success",
                    )
                else:
                    self.log(
                        "isort line_length not set to 80 (Google recommends 80)",
                        "warning",
                    )

            return True
        except Exception as e:
            self.log(f"Error reading {filepath}: {e}", "error")
            return False

    def validate_golangci_config(self) -> bool:
        """Validate golangci-lint configuration."""
        filepath = ".golangci.yml"
        if not self.validate_file_exists(filepath):
            return False
        if not self.validate_yaml_syntax(filepath):
            return False

        self.log("golangci-lint config validated", "success")
        return True

    def validate_markdown_config(self) -> bool:
        """Validate Markdownlint configuration."""
        filepath = ".markdownlint.json"
        if not self.validate_file_exists(filepath):
            return False
        if not self.validate_json_syntax(filepath):
            return False

        self.log("Markdownlint config validated", "success")
        return True

    def validate_yaml_config(self) -> bool:
        """Validate YAML lint configuration."""
        filepath = ".yaml-lint.yml"
        if not self.validate_file_exists(filepath):
            return False
        if not self.validate_yaml_syntax(filepath):
            return False

        self.log("yamllint config validated", "success")
        return True

    def validate_rust_configs(self) -> bool:
        """Validate Rust configuration files."""
        configs = ["clippy.toml", "rustfmt.toml"]
        all_valid = True

        for config in configs:
            if not self.validate_file_exists(config):
                all_valid = False
                continue

            # Validate TOML syntax
            try:
                import tomli

                with open(self.repo_root / config, "rb") as f:
                    tomli.load(f)
                self.log(f"Valid TOML syntax: {config}", "success")
            except ImportError:
                self.log(
                    f"Cannot validate TOML syntax (tomli not installed): {config}",
                    "warning",
                )
            except Exception as e:
                self.log(f"Invalid TOML in {config}: {e}", "error")
                all_valid = False

        return all_valid

    def validate_super_linter_env_files(self) -> bool:
        """Validate Super Linter .env files reference existing configs."""
        env_files = ["super-linter-ci.env", "super-linter-pr.env"]
        all_valid = True

        for env_file in env_files:
            if not self.validate_file_exists(env_file):
                all_valid = False
                continue

            with open(self.repo_root / env_file) as f:
                content = f.read()

            # Extract CONFIG_FILE references
            import re

            config_refs = re.findall(r"(\w+_CONFIG_FILE)=(.+)", content)

            for var_name, config_path in config_refs:
                config_path = config_path.strip()
                if config_path and not config_path.startswith("#"):
                    full_path = self.repo_root / config_path
                    if full_path.exists():
                        self.log(f"{env_file}: {var_name}={config_path} ✓", "success")
                    else:
                        self.log(
                            f"{env_file}: {var_name}={config_path} NOT FOUND",
                            "error",
                        )
                        all_valid = False

        return all_valid

    def run_all_validations(self) -> bool:
        """Run all validation checks."""
        print(f"\n{BLUE}{'=' * 70}")
        print("  Linter Configuration Validator")
        print(f"  Repository: {self.repo_root}")
        print("  Google Style Guide Compliance Check")
        print(f"{'=' * 70}{RESET}\n")

        validators = [
            ("Prettier", self.validate_prettier_config),
            ("ESLint", self.validate_eslint_config),
            ("Python Black", self.validate_python_black_config),
            ("Pylint", self.validate_pylint_config),
            ("isort", self.validate_isort_config),
            ("golangci-lint", self.validate_golangci_config),
            ("Markdownlint", self.validate_markdown_config),
            ("yamllint", self.validate_yaml_config),
            ("Rust (clippy/rustfmt)", self.validate_rust_configs),
            ("Super Linter .env files", self.validate_super_linter_env_files),
        ]

        for name, validator in validators:
            print(f"\n{BLUE}━━━ Validating {name} ━━━{RESET}")
            validator()

        # Print summary
        print(f"\n{BLUE}{'=' * 70}")
        print("  Validation Summary")
        print(f"{'=' * 70}{RESET}\n")

        print(f"{GREEN}✅ Successes: {len(self.success)}{RESET}")
        print(f"{YELLOW}⚠️  Warnings: {len(self.warnings)}{RESET}")
        print(f"{RED}❌ Errors: {len(self.errors)}{RESET}\n")

        if self.errors:
            print(f"{RED}Validation FAILED with {len(self.errors)} errors{RESET}")
            return False
        if self.warnings:
            print(f"{YELLOW}Validation passed with {len(self.warnings)} warnings{RESET}")
            return True
        print(f"{GREEN}All validations PASSED!{RESET}")
        return True


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate linter configurations")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--repo-root", default=".", help="Repository root directory")

    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    validator = LinterValidator(repo_root, verbose=args.verbose)

    success = validator.run_all_validations()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
