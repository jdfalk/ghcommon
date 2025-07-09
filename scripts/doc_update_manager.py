#!/usr/bin/env python3
# file: scripts/doc_update_manager.py
# version: 2.0.0
# guid: 9e8d7c6b-5a49-3827-1605-4f3e2d1c0b9a

"""
Enhanced Documentation Update Manager

This script processes JSON-based documentation update files and applies them
to target documentation files. It supports various update modes and provides
comprehensive logging and error handling.

Usage:
    python doc_update_manager.py [options]
    python doc_update_manager.py --updates-dir .github/doc-updates
    python doc_update_manager.py --dry-run --verbose
"""

import json
import sys
import argparse
import re
import shutil
from pathlib import Path
from typing import Dict, Optional, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DocumentationUpdateManager:
    """Manages processing of documentation update files."""

    def __init__(
        self,
        updates_dir: str = ".github/doc-updates",
        cleanup: bool = True,
        dry_run: bool = False,
        verbose: bool = False,
    ):
        self.updates_dir = Path(updates_dir)
        self.cleanup = cleanup
        self.dry_run = dry_run
        self.verbose = verbose
        self.stats = {
            "files_processed": 0,
            "changes_made": False,
            "files_updated": [],
            "errors": [],
        }

        if verbose:
            logger.setLevel(logging.DEBUG)

    def process_all_updates(self) -> Dict[str, Any]:
        """Process all update files in the updates directory."""
        logger.info(f"🔄 Processing documentation updates from {self.updates_dir}")

        if not self.updates_dir.exists():
            logger.info(f"📝 Updates directory does not exist: {self.updates_dir}")
            return self.stats

        update_files = list(self.updates_dir.glob("*.json"))
        if not update_files:
            logger.info("📝 No update files found")
            return self.stats

        logger.info(f"📊 Found {len(update_files)} update files")

        # Process files in order (oldest first based on filename/timestamp)
        update_files.sort()

        for update_file in update_files:
            try:
                self.process_update_file(update_file)
            except Exception as e:
                error_msg = f"Failed to process {update_file}: {str(e)}"
                logger.error(error_msg)
                self.stats["errors"].append(error_msg)

        # Save statistics
        self._save_stats()

        return self.stats

    def process_update_file(self, update_file: Path) -> None:
        """Process a single update file."""
        logger.debug(f"🔍 Processing: {update_file}")

        try:
            with open(update_file, "r", encoding="utf-8") as f:
                update_data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            raise Exception(f"Failed to read update file: {e}")

        # Validate required fields
        required_fields = ["file", "mode", "content"]
        for field in required_fields:
            if field not in update_data:
                raise Exception(f"Missing required field: {field}")

        target_file = Path(update_data["file"])
        mode = update_data["mode"]
        content = update_data["content"]
        options = update_data.get("options", {})

        logger.info(f"📝 Updating {target_file} (mode: {mode})")

        if self.dry_run:
            logger.info(f"🧪 [DRY RUN] Would update {target_file}")
            self.stats["files_processed"] += 1
            return

        # Apply the update
        success = self._apply_update(target_file, mode, content, options)

        if success:
            self.stats["files_processed"] += 1
            self.stats["changes_made"] = True
            if str(target_file) not in self.stats["files_updated"]:
                self.stats["files_updated"].append(str(target_file))

            # Move processed file if cleanup is enabled
            if self.cleanup:
                self._archive_processed_file(update_file)

    def _apply_update(
        self, target_file: Path, mode: str, content: str, options: Dict
    ) -> bool:
        """Apply an update to a target file."""
        try:
            # Create target file if it doesn't exist
            if not target_file.exists():
                target_file.parent.mkdir(parents=True, exist_ok=True)
                target_file.touch()
                logger.info(f"📄 Created new file: {target_file}")

            # Read current content
            try:
                with open(target_file, "r", encoding="utf-8") as f:
                    current_content = f.read()
            except UnicodeDecodeError:
                # Try with different encoding
                with open(target_file, "r", encoding="latin-1") as f:
                    current_content = f.read()

            # Apply update based on mode
            new_content = self._apply_mode(current_content, mode, content, options)

            if new_content != current_content:
                # Write updated content
                with open(target_file, "w", encoding="utf-8") as f:
                    f.write(new_content)
                logger.info(f"✅ Updated {target_file}")
                return True
            else:
                logger.info(f"📄 No changes needed for {target_file}")
                return False

        except Exception as e:
            error_msg = f"Failed to apply update to {target_file}: {str(e)}"
            logger.error(error_msg)
            self.stats["errors"].append(error_msg)
            return False

    def _apply_mode(
        self, current_content: str, mode: str, content: str, options: Dict
    ) -> str:
        """Apply content update based on the specified mode."""

        if mode == "append":
            return current_content + "\n" + content if current_content else content

        elif mode == "prepend":
            return content + "\n" + current_content if current_content else content

        elif mode == "replace":
            return content

        elif mode == "replace-section":
            section = options.get("section")
            if not section:
                raise ValueError("replace-section mode requires 'section' option")
            return self._replace_section(current_content, section, content)

        elif mode == "insert-after":
            after_text = options.get("after")
            if not after_text:
                raise ValueError("insert-after mode requires 'after' option")
            return self._insert_after(current_content, after_text, content)

        elif mode == "insert-before":
            before_text = options.get("before")
            if not before_text:
                raise ValueError("insert-before mode requires 'before' option")
            return self._insert_before(current_content, before_text, content)

        elif mode == "changelog-entry":
            return self._add_changelog_entry(current_content, content)

        elif mode == "task-add":
            return self._add_todo_task(current_content, content)

        elif mode == "task-complete":
            task_id = options.get("task_id")
            return self._complete_todo_task(current_content, content, task_id)

        elif mode == "update-badge":
            badge_name = options.get("badge_name")
            if not badge_name:
                raise ValueError("update-badge mode requires 'badge_name' option")
            return self._update_badge(current_content, badge_name, content)

        else:
            raise ValueError(f"Unknown update mode: {mode}")

    def _replace_section(self, content: str, section: str, new_content: str) -> str:
        """Replace a specific section in the content."""
        # Pattern to match markdown sections
        pattern = rf"(^#{1, 6}\s+{re.escape(section)}\s*$.*?)(?=^#{1, 6}\s+|\Z)"

        if re.search(pattern, content, re.MULTILINE | re.DOTALL):
            return re.sub(
                pattern,
                f"# {section}\n\n{new_content}\n",
                content,
                flags=re.MULTILINE | re.DOTALL,
            )
        else:
            # Section doesn't exist, append it
            return content + f"\n\n# {section}\n\n{new_content}\n"

    def _insert_after(self, content: str, after_text: str, new_content: str) -> str:
        """Insert content after specified text."""
        if after_text in content:
            return content.replace(after_text, after_text + "\n" + new_content)
        else:
            # If text not found, append to end
            return content + "\n" + new_content

    def _insert_before(self, content: str, before_text: str, new_content: str) -> str:
        """Insert content before specified text."""
        if before_text in content:
            return content.replace(before_text, new_content + "\n" + before_text)
        else:
            # If text not found, prepend to beginning
            return new_content + "\n" + content

    def _add_changelog_entry(self, content: str, entry: str) -> str:
        """Add entry to changelog under [Unreleased] section."""
        unreleased_pattern = r"(## \[Unreleased\].*?\n)(.*?)(?=\n## |\Z)"

        match = re.search(unreleased_pattern, content, re.DOTALL)
        if match:
            # Insert entry in unreleased section
            return content.replace(
                match.group(0), match.group(1) + "\n" + entry + "\n" + match.group(2)
            )
        else:
            # No unreleased section, add it
            unreleased_section = f"""## [Unreleased]

{entry}

"""
            # Find the first version section and insert before it
            version_pattern = r"(## \[[\d\.]+\])"
            if re.search(version_pattern, content):
                return re.sub(
                    version_pattern, unreleased_section + r"\1", content, count=1
                )
            else:
                # No version sections, append to end
                return content + "\n" + unreleased_section

    def _add_todo_task(self, content: str, task: str) -> str:
        """Add a task to TODO list."""
        # Find the first incomplete task section or append to end
        return content + "\n" + task + "\n"

    def _complete_todo_task(
        self, content: str, task_description: str, task_id: Optional[str]
    ) -> str:
        """Mark a TODO task as complete."""

        def mark_complete(match):
            return match.group(0).replace("[ ]", "[x]")

        if task_id:
            # Find task by ID and mark complete
            pattern = rf"- \[ \] .*{re.escape(task_id)}.*"
            return re.sub(pattern, mark_complete, content)
        else:
            # Find task by description and mark complete
            pattern = rf"- \[ \] .*{re.escape(task_description)}.*"
            return re.sub(pattern, mark_complete, content)

    def _update_badge(self, content: str, badge_name: str, badge_content: str) -> str:
        """Update or add a badge in README."""
        # This is a simplified implementation
        # In practice, you'd want more sophisticated badge updating
        return content + f"\n{badge_content}\n"

    def _archive_processed_file(self, update_file: Path) -> None:
        """Move processed file to archive/processed directory."""
        try:
            archive_dir = self.updates_dir / "processed"
            archive_dir.mkdir(exist_ok=True)

            archive_path = archive_dir / update_file.name
            shutil.move(str(update_file), str(archive_path))
            logger.debug(f"📦 Archived: {update_file} -> {archive_path}")

        except Exception as e:
            logger.warning(f"Failed to archive {update_file}: {e}")

    def _save_stats(self) -> None:
        """Save processing statistics to a file."""
        try:
            with open(".doc-update-stats.json", "w") as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save stats: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Process documentation update files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python doc_update_manager.py
  python doc_update_manager.py --updates-dir .github/doc-updates
  python doc_update_manager.py --dry-run --verbose
  python doc_update_manager.py --no-cleanup
        """,
    )

    parser.add_argument(
        "--updates-dir",
        default=".github/doc-updates",
        help="Directory containing update files (default: .github/doc-updates)",
    )

    parser.add_argument(
        "--cleanup",
        type=lambda x: x.lower() in ("true", "1", "yes"),
        default=True,
        help="Whether to archive processed files (default: true)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be updated without making changes",
    )

    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    # Support positional argument for backwards compatibility
    parser.add_argument(
        "updates_directory",
        nargs="?",
        help="Directory with update files (positional, overrides --updates-dir)",
    )

    args = parser.parse_args()

    # Use positional argument if provided
    updates_dir = args.updates_directory or args.updates_dir

    manager = DocumentationUpdateManager(
        updates_dir=updates_dir,
        cleanup=args.cleanup,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )

    try:
        stats = manager.process_all_updates()

        if args.verbose or args.dry_run:
            print("\n📊 Processing Summary:")
            print(f"   Files processed: {stats['files_processed']}")
            print(f"   Changes made: {stats['changes_made']}")
            print(f"   Files updated: {len(stats['files_updated'])}")
            if stats["errors"]:
                print(f"   Errors: {len(stats['errors'])}")
                for error in stats["errors"]:
                    print(f"     - {error}")

        # Exit with error code if there were errors
        if stats["errors"]:
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("🛑 Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
