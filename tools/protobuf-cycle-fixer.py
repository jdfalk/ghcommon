#!/usr/bin/env python3
# file: tools/protobuf-cycle-fixer.py
# version: 1.0.1
# guid: 8f7e6d5c-4b3a-2f9e-8d7c-6b5a4f3e2d1c

"""Automated protobuf import cycle detection and resolution tool.
Designed to work with the copilot-agent-util for logging and execution.
"""

import os
import re
import subprocess
import sys
from collections import defaultdict, deque
from pathlib import Path


class ProtobufCycleFixer:
    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)
        self.pkg_dir = self.repo_root / "pkg"
        self.import_graph = defaultdict(set)
        self.reverse_graph = defaultdict(set)
        self.cycles = []
        self.unused_imports = []

    def analyze_proto_file(self, proto_path: Path) -> tuple[str, list[str]]:
        """Extract package name and imports from a proto file."""
        package_name = ""
        imports = []

        with open(proto_path, encoding="utf-8") as f:
            content = f.read()

        # Extract package name
        package_match = re.search(r"package\s+([\w.]+)\s*;", content)
        if package_match:
            package_name = package_match.group(1)

        # Extract imports
        import_matches = re.findall(r'import\s+"([^"]+)"\s*;', content)
        for import_path in import_matches:
            if import_path.startswith("pkg/"):
                # Convert import path to package name
                parts = (
                    import_path.replace("pkg/", "").replace("/proto/", ".").replace(".proto", "")
                )
                imports.append(f"gcommon.v1.{parts}")

        return package_name, imports

    def build_dependency_graph(self):
        """Build the import dependency graph from all proto files."""
        print("Building dependency graph...")

        for proto_file in self.pkg_dir.rglob("*.proto"):
            package_name, imports = self.analyze_proto_file(proto_file)
            if package_name:
                for imported_package in imports:
                    self.import_graph[package_name].add(imported_package)
                    self.reverse_graph[imported_package].add(package_name)

    def detect_cycles(self) -> list[list[str]]:
        """Detect all cycles in the import graph using DFS."""
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node, path):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return

            if node in visited:
                return

            visited.add(node)
            rec_stack.add(node)

            for neighbor in self.import_graph[node]:
                dfs(neighbor, path + [node])

            rec_stack.remove(node)

        for node in self.import_graph:
            if node not in visited:
                dfs(node, [])

        self.cycles = cycles
        return cycles

    def generate_cycle_breaking_plan(self) -> dict[str, list[str]]:
        """Generate a plan to break cycles by identifying redundant imports."""
        breaking_plan = defaultdict(list)

        for cycle in self.cycles:
            print(f"Analyzing cycle: {' -> '.join(cycle)}")

            # For each edge in the cycle, check if it's actually needed
            for i in range(len(cycle) - 1):
                from_pkg = cycle[i]
                to_pkg = cycle[i + 1]

                # Check if this import is used or just transitive
                if self.is_import_redundant(from_pkg, to_pkg):
                    breaking_plan[from_pkg].append(to_pkg)

        return breaking_plan

    def is_import_redundant(self, from_pkg: str, to_pkg: str) -> bool:
        """Check if an import is redundant (can be reached transitively)."""
        # Simple heuristic: if there's another path, this import might be redundant
        temp_graph = self.import_graph.copy()
        temp_graph[from_pkg].discard(to_pkg)

        # BFS to see if to_pkg is still reachable
        queue = deque([from_pkg])
        visited = {from_pkg}

        while queue:
            current = queue.popleft()
            for neighbor in temp_graph[current]:
                if neighbor == to_pkg:
                    return True  # Reachable via another path
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return False

    def fix_proto_file(self, package_name: str, imports_to_remove: list[str]):
        """Remove specified imports from proto files of a package."""
        # Find proto files for this package
        pkg_parts = package_name.replace("gcommon.v1.", "").split(".")
        pkg_dir = self.pkg_dir / "/".join(pkg_parts) / "proto"

        if not pkg_dir.exists():
            print(f"Warning: Package directory not found: {pkg_dir}")
            return

        for proto_file in pkg_dir.glob("*.proto"):
            self.remove_imports_from_file(proto_file, imports_to_remove)

    def remove_imports_from_file(self, proto_file: Path, imports_to_remove: list[str]):
        """Remove specific imports from a proto file."""
        with open(proto_file, encoding="utf-8") as f:
            content = f.read()

        modified = False
        lines = content.split("\n")
        new_lines = []

        for line in lines:
            should_remove = False
            for import_to_remove in imports_to_remove:
                # Convert package name back to import path
                import_path = (
                    import_to_remove.replace("gcommon.v1.", "pkg/").replace(".", "/") + ".proto"
                )
                if f'import "{import_path}"' in line:
                    should_remove = True
                    modified = True
                    print(f"Removing import: {line.strip()} from {proto_file}")
                    break

            if not should_remove:
                new_lines.append(line)

        if modified:
            with open(proto_file, "w", encoding="utf-8") as f:
                f.write("\n".join(new_lines))

    def run_buf_lint(self) -> tuple[int, str]:
        """Run buf lint and return results."""
        try:
            result = subprocess.run(
                ["copilot-agent-util", "buf", "lint"],
                check=False,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )
            return result.returncode, result.stderr
        except Exception as e:
            return 1, str(e)

    def generate_report(self) -> str:
        """Generate a comprehensive report of the analysis."""
        report = []
        report.append("# Protobuf Import Cycle Analysis Report")
        report.append(f"Generated by: {__file__}")
        report.append(f"Repository: {self.repo_root}")
        report.append("")

        report.append("## Summary")
        report.append(f"- Total packages analyzed: {len(self.import_graph)}")
        report.append(f"- Cycles detected: {len(self.cycles)}")
        report.append("")

        if self.cycles:
            report.append("## Detected Cycles")
            for i, cycle in enumerate(self.cycles, 1):
                report.append(f"### Cycle {i}")
                report.append("```")
                report.append(" -> ".join(cycle))
                report.append("```")
                report.append("")

        return "\n".join(report)

    def fix_all_cycles(self):
        """Main method to detect and fix all import cycles."""
        print("Starting protobuf cycle analysis and fixing...")

        # Build dependency graph
        self.build_dependency_graph()

        # Detect cycles
        cycles = self.detect_cycles()
        print(f"Found {len(cycles)} cycles")

        if not cycles:
            print("No cycles detected!")
            return

        # Generate fixing plan
        breaking_plan = self.generate_cycle_breaking_plan()

        # Apply fixes
        for package, imports_to_remove in breaking_plan.items():
            print(f"Fixing package {package}: removing {imports_to_remove}")
            self.fix_proto_file(package, imports_to_remove)

        # Generate report
        report = self.generate_report()
        report_path = self.repo_root / "protobuf_cycle_analysis.md"
        with open(report_path, "w") as f:
            f.write(report)

        print(f"Report saved to: {report_path}")

        # Run buf lint to verify fixes
        returncode, output = self.run_buf_lint()
        if returncode == 0:
            print("SUCCESS: All cycles fixed! Buf lint passes.")
        else:
            print("Buf lint still shows errors. Manual intervention needed.")
            print(output)


def main():
    repo_root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

    fixer = ProtobufCycleFixer(repo_root)
    fixer.fix_all_cycles()


if __name__ == "__main__":
    main()
