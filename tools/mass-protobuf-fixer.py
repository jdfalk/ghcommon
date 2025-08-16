#!/usr/bin/env python3
# file: tools/mass-protobuf-fixer.py
# version: 1.0.0
# guid: 9f8e7d6c-5b4a-3f9e-8d7c-6b5a4f3e2d1c

"""
Mass protobuf import cycle and unused import fixer.
Designed to work autonomously with the copilot-agent-util for execution.
"""

import os
import re
import sys
import subprocess
from pathlib import Path
from typing import Dict, List


class MassProtobufFixer:
    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)
        self.pkg_dir = self.repo_root / "pkg"
        self.fixes_applied = 0

    def remove_unused_imports_from_file(
        self, proto_file: Path, unused_imports: List[str]
    ):
        """Remove unused imports from a proto file."""
        if not proto_file.exists():
            return False

        with open(proto_file, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content
        lines = content.split("\n")
        new_lines = []

        for line in lines:
            should_remove = False
            for unused_import in unused_imports:
                if f'import "{unused_import}"' in line:
                    should_remove = True
                    self.fixes_applied += 1
                    print(f"Removing unused import: {line.strip()} from {proto_file}")
                    break

            if not should_remove:
                new_lines.append(line)

        new_content = "\n".join(new_lines)
        if new_content != original_content:
            with open(proto_file, "w", encoding="utf-8") as f:
                f.write(new_content)
            return True
        return False

    def fix_enum_prefixes(self, proto_file: Path, enum_fixes: List[Dict]):
        """Fix enum value prefixes."""
        if not proto_file.exists():
            return False

        with open(proto_file, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        for fix in enum_fixes:
            old_name = fix["old"]
            new_name = fix["new"]
            # Replace enum value declarations
            content = re.sub(rf"\b{re.escape(old_name)}\b", new_name, content)
            if old_name in original_content and new_name not in original_content:
                self.fixes_applied += 1
                print(f"Fixed enum prefix: {old_name} -> {new_name} in {proto_file}")

        if content != original_content:
            with open(proto_file, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        return False

    def break_import_cycles_aggressively(self):
        """Break import cycles by removing cross-dependencies."""
        # Known problematic cross-imports that create cycles
        cycle_breaking_removals = {
            # Remove common/metrics dependency from organization
            "pkg/organization/proto": [
                "pkg/common/proto/key_value.proto",
                "pkg/common/proto/request_metadata.proto",
                "pkg/common/proto/response_metadata.proto",
                "pkg/common/proto/time_range.proto",
            ],
            # Remove metrics dependency from queue
            "pkg/queue/proto": [
                "pkg/common/proto/request_metadata.proto",
                "pkg/common/proto/response_metadata.proto",
                "pkg/common/proto/time_range.proto",
                "pkg/metrics/proto/metric.proto",
            ],
            # Remove config dependencies that create cycles
            "pkg/config/proto": [
                "pkg/organization/proto/organization.proto",
                "pkg/queue/proto/queue.proto",
            ],
        }

        for proto_dir, imports_to_remove in cycle_breaking_removals.items():
            dir_path = self.repo_root / proto_dir
            if dir_path.exists():
                for proto_file in dir_path.glob("*.proto"):
                    self.remove_unused_imports_from_file(proto_file, imports_to_remove)

    def fix_all_buf_lint_issues(self):
        """Fix all issues identified by buf lint."""
        print("Running mass protobuf fixes...")

        # First, break import cycles aggressively
        self.break_import_cycles_aggressively()

        # Get current buf lint output
        result = subprocess.run(
            ["copilot-agent-util", "buf", "lint"],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("No buf lint issues found!")
            return True

        buf_output = result.stderr
        print(f"Processing {len(buf_output.split('\\n'))} lint issues...")

        # Parse and fix issues
        for line in buf_output.split("\n"):
            if not line.strip():
                continue

            # Handle unused imports
            if "is unused" in line:
                self.fix_unused_import_line(line)

            # Handle enum prefix issues
            elif "should be prefixed with" in line:
                self.fix_enum_prefix_line(line)

            # Handle enum suffix issues
            elif "should be suffixed with" in line:
                self.fix_enum_suffix_line(line)

        print(f"Applied {self.fixes_applied} fixes")

        # Test if fixes worked
        result = subprocess.run(
            ["copilot-agent-util", "buf", "lint"],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("SUCCESS: All buf lint issues fixed!")
            return True
        else:
            print(f"Still have {len(result.stderr.split('\\n'))} issues remaining")
            return False

    def fix_unused_import_line(self, line: str):
        """Fix a single unused import line."""
        # Example: pkg/queue/proto/ack_request.proto:17:1:Import "pkg/common/proto/request_metadata.proto" is unused.
        match = re.search(
            r'(pkg/[^:]+\.proto):\d+:\d+:Import "([^"]+)" is unused', line
        )
        if match:
            proto_file_path = self.repo_root / match.group(1)
            unused_import = match.group(2)
            self.remove_unused_imports_from_file(proto_file_path, [unused_import])

    def fix_enum_prefix_line(self, line: str):
        """Fix a single enum prefix line."""
        # Example: pkg/queue/proto/alert_severity.proto:19:3:Enum value name "ALERT_SEVERITY_UNSPECIFIED" should be prefixed with "QUEUE_ALERT_SEVERITY_".
        match = re.search(
            r'(pkg/[^:]+\.proto):\d+:\d+:Enum value name "([^"]+)" should be prefixed with "([^"]+)"',
            line,
        )
        if match:
            proto_file_path = self.repo_root / match.group(1)
            old_name = match.group(2)
            prefix = match.group(3)
            new_name = (
                prefix + old_name.split("_", 2)[-1]
                if "_" in old_name
                else prefix + old_name
            )
            self.fix_enum_prefixes(
                proto_file_path, [{"old": old_name, "new": new_name}]
            )

    def fix_enum_suffix_line(self, line: str):
        """Fix a single enum suffix line."""
        # Example: pkg/queue/proto/routing_pattern.proto:20:3:Enum zero value name "ROUTING_PATTERN_EXACT" should be suffixed with "_UNSPECIFIED".
        match = re.search(
            r'(pkg/[^:]+\.proto):\d+:\d+:Enum zero value name "([^"]+)" should be suffixed with "([^"]+)"',
            line,
        )
        if match:
            proto_file_path = self.repo_root / match.group(1)
            old_name = match.group(2)
            suffix = match.group(3)
            new_name = old_name + suffix
            self.fix_enum_prefixes(
                proto_file_path, [{"old": old_name, "new": new_name}]
            )


def main():
    if len(sys.argv) > 1:
        repo_root = sys.argv[1]
    else:
        repo_root = os.getcwd()

    fixer = MassProtobufFixer(repo_root)

    # Run multiple passes until clean
    max_passes = 5
    for pass_num in range(1, max_passes + 1):
        print(f"\\n=== Pass {pass_num} ===")
        if fixer.fix_all_buf_lint_issues():
            print(f"All issues fixed in {pass_num} passes!")
            break
        if pass_num == max_passes:
            print(
                f"Reached maximum passes ({max_passes}). Manual intervention may be needed."
            )


if __name__ == "__main__":
    main()
