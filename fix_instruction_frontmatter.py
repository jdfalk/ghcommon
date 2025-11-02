#!/usr/bin/env python3
# file: fix_instruction_frontmatter.py
# version: 1.0.0
# guid: f1e2d3c4-b5a6-9e8f-7d6c-5b4a3e2f1d0e

"""Fix malformed frontmatter in instruction files across all repositories.
Converts improperly formatted frontmatter to proper YAML frontmatter format.
"""

import os
import re
import shutil
from pathlib import Path


# Colors for output
class Colors:
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    NC = "\033[0m"  # No Color


def log_info(msg):
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {msg}")


def log_success(msg):
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {msg}")


def log_warning(msg):
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {msg}")


def fix_instruction_file(file_path):
    """Fix frontmatter in a single instruction file."""
    log_info(f"Processing: {file_path}")

    # Create backup
    backup_path = f"{file_path}.backup"
    shutil.copy2(file_path, backup_path)

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Check if this file needs fixing
        if not re.search(r"^applyTo:", content, re.MULTILINE):
            log_info(f"  Skipping (no applyTo found): {file_path}")
            os.remove(backup_path)
            return False

        if re.search(r"^---\s*$", content, re.MULTILINE):
            log_info(
                f"  Skipping (already has proper frontmatter): {file_path}"
            )
            os.remove(backup_path)
            return False

        lines = content.split("\n")
        fixed_lines = []
        in_frontmatter = False
        frontmatter_started = False

        for i, line in enumerate(lines):
            # Keep header comments
            if line.startswith("<!--") or (
                line.strip() == "" and not frontmatter_started
            ):
                fixed_lines.append(line)
            # Start frontmatter when we find applyTo
            elif line.startswith("applyTo:"):
                if not frontmatter_started:
                    fixed_lines.append("---")
                    frontmatter_started = True
                    in_frontmatter = True
                fixed_lines.append(line)
            # Handle description lines
            elif in_frontmatter and (
                line.startswith("description:")
                or line.startswith("  ")
                or line.startswith("\t")
            ):
                fixed_lines.append(line)
            # End frontmatter when we hit content
            elif (
                frontmatter_started
                and in_frontmatter
                and (line.startswith("#") or line.strip() != "")
            ):
                fixed_lines.append("---")
                fixed_lines.append("")
                fixed_lines.append(line)
                in_frontmatter = False
            else:
                fixed_lines.append(line)

        # If we ended while still in frontmatter, close it
        if in_frontmatter:
            # Insert the closing --- before the last non-empty line
            for j in range(len(fixed_lines) - 1, -1, -1):
                if fixed_lines[j].strip() != "":
                    fixed_lines.insert(j + 1, "---")
                    fixed_lines.insert(j + 2, "")
                    break

        # Write the fixed content
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(fixed_lines))

        log_success(f"  Fixed: {file_path}")
        return True

    except Exception as e:
        log_warning(f"  Error processing {file_path}: {e}")
        # Restore backup
        shutil.copy2(backup_path, file_path)
        return False


def main():
    """Main execution function."""
    log_info("Fixing instruction file frontmatter across all repositories")

    # Repository directories
    base_dirs = [
        "/Users/jdfalk/repos/github.com/jdfalk/gcommon/.github/instructions",
        "/Users/jdfalk/repos/github.com/jdfalk/ghcommon/.github/instructions",
        "/Users/jdfalk/repos/github.com/jdfalk/subtitle-manager/.github/instructions",
        "/Users/jdfalk/repos/github.com/jdfalk/audiobook-organizer/.github/instructions",
        "/Users/jdfalk/repos/github.com/jdfalk/apt-cacher-go/.github/instructions",
    ]

    fixed_count = 0
    total_count = 0

    for base_dir in base_dirs:
        if not os.path.exists(base_dir):
            log_warning(f"Directory not found: {base_dir}")
            continue

        log_info(f"Processing directory: {base_dir}")

        # Find all .instructions.md files
        for file_path in Path(base_dir).glob("*.instructions.md"):
            total_count += 1
            if fix_instruction_file(str(file_path)):
                fixed_count += 1

    log_success(
        f"Processing complete! Fixed {fixed_count}/{total_count} instruction files."
    )
    log_info("Backup files created with .backup extension")


if __name__ == "__main__":
    main()
