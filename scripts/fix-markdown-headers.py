#!/usr/bin/env python3
# file: scripts/fix-markdown-headers-clean.py
# version: 1.4.0
# guid: 4b8e9f2a-3c5d-4e7f-8a9b-1c2d3e4f5a6b

import argparse
import os
import re
import sys
import uuid


def find_markdown_files(directory):
    """Find all markdown files in the given directory recursively, excluding node_modules and workflow-debug-output."""
    markdown_files = []
    for root, dirs, files in os.walk(directory):
        # Skip excluded directories
        dirs_to_remove = []
        for dir_name in dirs:
            if dir_name in ["node_modules", "workflow-debug-output"]:
                dirs_to_remove.append(dir_name)

        for dir_name in dirs_to_remove:
            dirs.remove(dir_name)

        for file in files:
            if file.endswith(".md"):
                markdown_files.append(os.path.join(root, file))
    return markdown_files


def has_bad_header(content):
    """Check if the file has shell-style header instead of HTML comment header."""
    lines = content.split("\n")
    if len(lines) < 3:
        return False

    # Find the first few non-empty lines that could be headers
    header_lines = []
    for line in lines[:10]:  # Check first 10 lines
        stripped = line.strip()
        if stripped:
            header_lines.append(line)
        if len(header_lines) >= 3:
            break

    if len(header_lines) < 3:
        return False

    # Check for shell-style header pattern
    shell_file_pattern = r"^# file: "
    shell_version_pattern = r"^# version: "
    shell_guid_pattern = r"^# guid: "

    return (
        re.match(shell_file_pattern, header_lines[0])
        and re.match(shell_version_pattern, header_lines[1])
        and re.match(shell_guid_pattern, header_lines[2])
    )


def fix_header(content, file_path):
    """Convert shell-style header to HTML comment header."""
    lines = content.split("\n")

    if not has_bad_header(content):
        return content, False

    # Find the header lines (they might have blank lines between them)
    header_info = {}
    header_line_indices = []

    for i, line in enumerate(lines[:10]):
        stripped = line.strip()
        if re.match(r"^# file: ", line):
            header_info["file"] = line
            header_line_indices.append(i)
        elif re.match(r"^# version: ", line):
            header_info["version"] = line
            header_line_indices.append(i)
        elif re.match(r"^# guid: ", line):
            header_info["guid"] = line
            header_line_indices.append(i)

        if len(header_info) == 3:
            break

    if len(header_info) != 3:
        return content, False

    # Extract the header information
    file_match = re.match(r"^# file: (.+)$", header_info["file"])
    version_match = re.match(r"^# version: (.+)$", header_info["version"])
    guid_match = re.match(r"^# guid: (.+)$", header_info["guid"])

    if not all([file_match, version_match, guid_match]):
        return content, False

    # Create new HTML comment header
    new_header = [
        f"<!-- file: {file_match.group(1)} -->",
        f"<!-- version: {version_match.group(1)} -->",
        f"<!-- guid: {guid_match.group(1)} -->",
    ]

    # Remove all the old header lines and any blank lines at the top
    # Find the last header line index
    last_header_index = max(header_line_indices)

    # Skip any blank lines after the last header
    content_start = last_header_index + 1
    while content_start < len(lines) and lines[content_start].strip() == "":
        content_start += 1

    # Combine new header with remaining content
    remaining_content = lines[content_start:]

    # Add a blank line after header if the next line isn't blank
    if remaining_content and remaining_content[0].strip() != "":
        new_content = "\n".join(new_header + [""] + remaining_content)
    else:
        new_content = "\n".join(new_header + remaining_content)

    return new_content, True


def has_html_comment_header(content):
    """Check if file already has proper HTML comment header."""
    lines = content.split("\n")
    if len(lines) < 3:
        return False

    # Skip over doctoc or other special comment blocks
    start_index = 0
    for i, line in enumerate(lines[:10]):
        if (
            line.startswith("<!-- START doctoc")
            or line.startswith("<!-- DON'T EDIT THIS SECTION")
            or line.strip() == ""
            or line.startswith("<!-- END doctoc")
        ):
            continue
        start_index = i
        break

    # Check if we have enough lines left for a header
    if start_index + 3 > len(lines):
        return False

    return (
        lines[start_index].startswith("<!-- file:")
        and lines[start_index + 1].startswith("<!-- version:")
        and lines[start_index + 2].startswith("<!-- guid:")
    )


def is_special_comment_block(content):
    """Check if file starts with special comment blocks that should be preserved."""
    lines = content.split("\n")
    if not lines:
        return False

    first_line = lines[0].strip()

    # Check for various special comment types that should be preserved
    special_patterns = [
        "<!-- START doctoc",
        "<!-- DON'T EDIT THIS SECTION",
        "<!-- This file is auto-generated",
        "<!-- Copyright",
        "<!-- License",
        "<!-- SPDX-License",
        "<!-- markdownlint-disable",
        "<!-- prettier-ignore",
    ]

    return any(first_line.startswith(pattern) for pattern in special_patterns)


def needs_header(content):
    """Check if file needs a header (missing or incomplete)."""
    if has_bad_header(content) or has_html_comment_header(content):
        return False

    # Don't add headers to files that start with special comment blocks
    if is_special_comment_block(content):
        return False

    # Check if it has any header at all
    lines = content.split("\n")

    # Skip over any initial doctoc or special comment blocks
    content_start = 0
    in_doctoc = False

    for i, line in enumerate(lines[:15]):  # Check more lines for complex blocks
        stripped = line.strip()

        if stripped.startswith("<!-- START doctoc"):
            in_doctoc = True
            continue
        if stripped.startswith("<!-- END doctoc"):
            in_doctoc = False
            content_start = i + 1
            continue
        if in_doctoc or stripped == "":
            continue
        content_start = i
        break

    # Look for partial headers after skipping special blocks
    for line in lines[content_start : content_start + 5]:
        if (
            line.startswith("<!-- file:")
            or line.startswith("# file:")
            or line.startswith("<!-- version:")
            or line.startswith("# version:")
        ):
            return True  # Has partial header, needs completion

    # No header found and no special comments to preserve
    return True


def generate_header(file_path):
    """Generate a complete HTML comment header for a file."""
    # Generate relative path from current working directory
    rel_path = os.path.relpath(file_path)

    # Generate a new UUID4
    new_guid = str(uuid.uuid4())

    header = [
        f"<!-- file: {rel_path} -->",
        "<!-- version: 1.0.0 -->",
        f"<!-- guid: {new_guid} -->",
    ]

    return header


def insert_header_after_special_comments(content, header_lines):
    """Insert header after any special comment blocks like doctoc."""
    lines = content.split("\n")
    insert_position = 0
    in_doctoc = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        if stripped.startswith("<!-- START doctoc"):
            in_doctoc = True
            continue
        if stripped.startswith("<!-- END doctoc"):
            in_doctoc = False
            insert_position = i + 1
            break
        if in_doctoc:
            continue
        if not stripped:  # Skip empty lines at the start
            if not in_doctoc:
                insert_position = i + 1
            continue
        # Found content, stop here if not in doctoc
        if not in_doctoc:
            insert_position = i
            break

    # Insert header at the determined position
    before_lines = lines[:insert_position]
    after_lines = lines[insert_position:]

    # Add a blank line after header if needed
    if after_lines and after_lines[0].strip() != "":
        result_lines = before_lines + header_lines + [""] + after_lines
    else:
        result_lines = before_lines + header_lines + after_lines

    return "\n".join(result_lines)


def process_file(file_path, dry_run=False, verbose=False):
    """Process a single markdown file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # First try to fix existing bad header
        new_content, was_fixed = fix_header(content, file_path)

        # If no fix was made, check if it needs a header
        if not was_fixed and needs_header(content):
            # Add new header
            header_lines = generate_header(file_path)

            # Use smart insertion to handle special comment blocks
            new_content = insert_header_after_special_comments(
                content, header_lines
            )

            was_fixed = True

            if verbose:
                print(f"➕ Added header to: {file_path}")

        if was_fixed:
            if not dry_run:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                return True
            if needs_header(content):
                print(f"   [DRY RUN] Would add header to: {file_path}")
            else:
                print(f"   [DRY RUN] Would fix header in: {file_path}")
            return True
        if verbose:
            if has_html_comment_header(content):
                print(f"✅ Already correct: {file_path}")
            else:
                print(f"ℹ️  No action needed: {file_path}")

        return False

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Fix markdown file headers from shell comments to HTML comments and add missing headers"
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to scan for markdown files (default: current directory)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output for all files",
    )

    args = parser.parse_args()

    if not os.path.exists(args.directory):
        print(f"❌ Directory '{args.directory}' does not exist")
        sys.exit(1)

    print(
        f"🔍 Scanning for markdown files in: {os.path.abspath(args.directory)}"
    )
    if args.dry_run:
        print("🔬 DRY RUN MODE - No files will be modified")

    markdown_files = find_markdown_files(args.directory)

    if not markdown_files:
        print("📄 No markdown files found")
        return

    print(f"📄 Found {len(markdown_files)} markdown files")

    fixed_count = 0
    total_processed = 0

    for file_path in sorted(markdown_files):
        total_processed += 1
        if process_file(file_path, args.dry_run, args.verbose):
            fixed_count += 1

    print("\n📊 Summary:")
    print(f"   Files processed: {total_processed}")
    print(f"   Files modified: {fixed_count}")

    if args.dry_run and fixed_count > 0:
        print("\n💡 Run without --dry-run to apply changes")
    elif fixed_count > 0:
        print(
            f"\n✅ Successfully processed {fixed_count} markdown files (fixes and additions)"
        )
    else:
        print("\n✅ All markdown files already have correct headers")


if __name__ == "__main__":
    main()
