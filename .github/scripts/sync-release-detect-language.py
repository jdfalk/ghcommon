#!/usr/bin/env python3
# file: .github/scripts/sync-release-detect-language.py
# version: 1.0.0
# guid: a7b8c9d0-e1f2-3a4b-5c6d-7e8f9a0b1c2d

"""
Detect programming language and determine if release should be triggered.
Usage: sync-release-detect-language.py [force_language]
"""

import os
import sys
import subprocess
from pathlib import Path


def check_file_exists(filename):
    """Check if a file exists in the current directory."""
    return Path(filename).exists()


def has_changes_since_last_release():
    """Check if there are changes since the last release tag."""
    try:
        # Get the latest tag
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            # No tags found, so there are changes
            return True

        latest_tag = result.stdout.strip()

        # Check if there are commits since the latest tag
        result = subprocess.run(
            ["git", "rev-list", f"{latest_tag}..HEAD", "--count"],
            capture_output=True,
            text=True,
            check=True,
        )

        commit_count = int(result.stdout.strip())
        return commit_count > 0

    except (subprocess.CalledProcessError, ValueError):
        # If git commands fail, assume there are changes
        return True


def detect_language():
    """Detect the primary programming language of the project."""
    # Language detection priority order
    language_files = [
        ("rust", "Cargo.toml"),
        ("go", "go.mod"),
        ("python", "pyproject.toml"),
        ("python", "setup.py"),
        ("python", "requirements.txt"),
        ("javascript", "package.json"),  # Will be refined below
        ("typescript", "tsconfig.json"),
    ]

    detected_language = None

    # Check for language-specific files
    for language, filename in language_files:
        if check_file_exists(filename):
            detected_language = language
            break

    # Refine JavaScript vs TypeScript detection
    if detected_language == "javascript":
        if (
            check_file_exists("tsconfig.json")
            or check_file_exists("src/main.ts")
            or check_file_exists("index.ts")
        ):
            detected_language = "typescript"

    # Additional checks for edge cases
    if not detected_language:
        # Check for common source directories
        src_path = Path("src")
        if src_path.exists():
            # Look for TypeScript files
            if list(src_path.glob("**/*.ts")):
                detected_language = "typescript"
            # Look for Rust files
            elif list(src_path.glob("**/*.rs")):
                detected_language = "rust"
            # Look for Go files
            elif list(src_path.glob("**/*.go")):
                detected_language = "go"
            # Look for Python files
            elif list(src_path.glob("**/*.py")):
                detected_language = "python"
            # Look for JavaScript files
            elif list(src_path.glob("**/*.js")):
                detected_language = "javascript"

    return detected_language or "unknown"


def should_release():
    """Determine if a release should be triggered."""
    # Check for changes since last release
    has_changes = has_changes_since_last_release()

    # For manual dispatch, always allow release
    if os.getenv("GITHUB_EVENT_NAME") == "workflow_dispatch":
        return True

    # For push events, only release if there are changes
    if os.getenv("GITHUB_EVENT_NAME") == "push":
        return has_changes

    # Default: no release
    return False


def set_github_output(name, value):
    """Set GitHub Actions output variable."""
    github_output = os.getenv("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"{name}={value}\n")
    print(f"::set-output name={name}::{value}")


def main():
    """Main entry point."""
    force_language = sys.argv[1] if len(sys.argv) > 1 else None

    # Detect language
    if force_language and force_language != "auto":
        language = force_language
        print(f"Language forced to: {language}")
    else:
        language = detect_language()
        print(f"Detected language: {language}")

    # Determine if release should happen
    should_rel = should_release()
    print(f"Should release: {should_rel}")

    # Set outputs for GitHub Actions
    set_github_output("language", language)
    set_github_output("should-release", "true" if should_rel else "false")

    # Print summary
    print("\nLanguage Detection Summary:")
    print(f"  Language: {language}")
    print(f"  Should Release: {should_rel}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
