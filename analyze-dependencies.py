#!/usr/bin/env python3
# file: analyze-dependencies.py
# version: 1.1.0
# guid: 9b7e2c3d-4f5a-6b7c-8d9e-0f1a2b3c4d5e
"""Comprehensive dependency analyzer for the ghcommon repository.

Generates multiple graph formats: ASCII, DOT, HTML, and Mermaid.js.

Usage examples:
    python3 analyze-dependencies.py --full
    python3 analyze-dependencies.py --exclude .git,node_modules,.venv --mermaid-max-files 500 --mermaid-max-edges 5000
"""

import argparse
from collections import defaultdict
from datetime import datetime
import json
import logging
from pathlib import Path
import re


class DependencyAnalyzer:
    """Analyze project files and build dependency graphs.

    Attributes:
        root: The repository root path.
        exclude_dirs: Directory names to exclude anywhere in a path.
        mermaid_max_files_per_category: Node limit per category in Mermaid output (None for unlimited).
        mermaid_max_edges: Edge limit for Mermaid output (None for unlimited).
    """

    def __init__(
        self,
        root_path: str,
        exclude_dirs: list[str] | None = None,
        mermaid_max_files_per_category: int = 20,
        mermaid_max_edges: int = 50,
    ):
        """Initialize the analyzer with paths and limits."""
        self.root = Path(root_path)
        self.dependencies: dict[str, set[str]] = defaultdict(set)
        self.file_types: dict[str, set[str]] = defaultdict(set)
        self.references: dict[str, set[str]] = defaultdict(set)
        self.orphans: set[str] = set()
        self.progress_log: list[str] = []
        self.exclude_dirs = set(exclude_dirs or [])
        self.mermaid_max_files_per_category = mermaid_max_files_per_category
        self.mermaid_max_edges = mermaid_max_edges

    def log(self, message: str):
        """Log progress."""
        logging.info(message)
        self.progress_log.append(message)

    def analyze_file(self, file_path: Path) -> dict:
        """Analyze a single file for dependencies."""
        rel_path = file_path.relative_to(self.root)
        suffix = file_path.suffix

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            self.log(f"  ⚠️  Could not read {rel_path}: {e}")
            return {}

        refs = set()

        # Shell scripts
        if suffix in [".sh", ".bash"]:
            # source, includes, script calls
            refs.update(
                re.findall(r'source\s+["\']?([^"\'\s]+)["\']?', content)
            )
            refs.update(re.findall(r"\.\s+([^\s]+\.sh)", content))
            refs.update(re.findall(r"bash\s+([^\s]+\.sh)", content))
            refs.update(re.findall(r"sh\s+([^\s]+\.sh)", content))
            refs.update(re.findall(r'\./scripts/([^\s"\']+)', content))
            refs.update(re.findall(r'\./tools/([^\s"\']+)', content))

        # Python files
        elif suffix == ".py":
            # imports, requires
            refs.update(re.findall(r"from\s+([\w.]+)\s+import", content))
            refs.update(re.findall(r"import\s+([\w.]+)", content))
            refs.update(re.findall(r'["\']([^"\']+\.py)["\']', content))
            refs.update(re.findall(r'scripts/([^\s"\']+\.py)', content))
            refs.update(re.findall(r'tools/([^\s"\']+\.py)', content))

        # YAML/Workflow files
        elif suffix in [".yml", ".yaml"]:
            # uses (reusable workflows), run scripts
            refs.update(
                re.findall(
                    r"uses:\s*jdfalk/ghcommon/\.github/workflows/([^\s@]+)",
                    content,
                )
            )
            refs.update(
                re.findall(r"uses:\s*\.github/workflows/([^\s]+)", content)
            )
            refs.update(
                re.findall(r"uses:\s*\./\.github/workflows/([^\s]+)", content)
            )
            refs.update(
                re.findall(r'\.github/workflows/scripts/([^\s"\']+)', content)
            )
            refs.update(re.findall(r'scripts/([^\s"\']+)', content))
            refs.update(re.findall(r'tools/([^\s"\']+)', content))
            refs.update(
                re.findall(r'\$\{\{\s*hashFiles\(["\']([^"\']+)', content)
            )

        # Markdown files
        elif suffix == ".md":
            # Links to other docs, scripts, workflows
            refs.update(re.findall(r"\[([^\]]+)\]\(([^)]+\.md)\)", content))
            refs.update(re.findall(r"\[([^\]]+)\]\(([^)]+\.yml)\)", content))
            refs.update(re.findall(r"\[([^\]]+)\]\(([^)]+\.sh)\)", content))
            refs.update(re.findall(r"\[([^\]]+)\]\(([^)]+\.py)\)", content))
            refs.update(re.findall(r"`([^`]+\.yml)`", content))
            refs.update(re.findall(r"`([^`]+\.sh)`", content))
            refs.update(re.findall(r"`([^`]+\.py)`", content))
            refs.update(re.findall(r'docs/([^\s"\'`\)]+)', content))
            refs.update(re.findall(r'scripts/([^\s"\'`\)]+)', content))
            refs.update(re.findall(r'\.github/([^\s"\'`\)]+)', content))

        # JSON files
        elif suffix == ".json":
            refs.update(re.findall(r'["\']([^"\']+\.yml)["\']', content))
            refs.update(re.findall(r'["\']([^"\']+\.yaml)["\']', content))
            refs.update(re.findall(r'["\']([^"\']+\.py)["\']', content))
            refs.update(re.findall(r'["\']([^"\']+\.sh)["\']', content))

        return {str(rel_path): list(refs)}

    def scan_directory(self, dir_path: Path, category: str):
        """Scan a directory for files."""
        self.log(f"\n📁 Scanning {category}: {dir_path.relative_to(self.root)}")

        if not dir_path.exists():
            self.log("  ⚠️  Directory does not exist")
            return

        patterns = [
            "**/*.md",
            "**/*.py",
            "**/*.sh",
            "**/*.bash",
            "**/*.yml",
            "**/*.yaml",
            "**/*.json",
            "**/*.txt",
        ]

        files_found = set()
        for pattern in patterns:
            files_found.update(dir_path.glob(pattern))

        self.log(f"  📊 Found {len(files_found)} files")

        for file_path in sorted(files_found):
            parts = set(file_path.parts)
            # Skip excluded directories (by name) anywhere in the path
            if any(ex in parts for ex in self.exclude_dirs):
                continue

            rel_path = str(file_path.relative_to(self.root))
            self.file_types[category].add(rel_path)

            deps = self.analyze_file(file_path)
            if deps:
                for source, targets in deps.items():
                    for target in targets:
                        # Normalize path
                        if isinstance(target, tuple):
                            normalized_target = (
                                target[1] if len(target) > 1 else target[0]
                            )
                        else:
                            normalized_target = target
                        self.dependencies[source].add(normalized_target)
                        self.references[normalized_target].add(source)

    def find_orphans(self):
        """Identify files that are not referenced by anything."""
        self.log("\n🔍 Finding orphaned files...")

        all_files = set()
        for files in self.file_types.values():
            all_files.update(files)

        referenced_files = set(self.references.keys())

        # Files that exist but are never referenced
        self.orphans = all_files - referenced_files

        # Exclude always-important files
        important_patterns = [
            "README.md",
            "LICENSE",
            "CHANGELOG.md",
            ".github/workflows/ci.yml",
            ".github/workflows/security.yml",
            "package.json",
            "requirements.txt",
        ]

        self.orphans = {
            f
            for f in self.orphans
            if not any(pattern in f for pattern in important_patterns)
        }

        self.log(f"  📊 Found {len(self.orphans)} potentially orphaned files")

    def generate_ascii_graph(self) -> str:
        """Generate ASCII art dependency graph."""
        lines = ["# ASCII Dependency Graph", ""]

        for category, files in sorted(self.file_types.items()):
            lines.append(f"\n## {category} ({len(files)} files)")
            lines.append("=" * 60)

            for file in sorted(files):
                if file in self.dependencies:
                    deps = self.dependencies[file]
                    if deps:
                        lines.append(f"\n{file}")
                        for dep in sorted(deps):
                            lines.append(f"  ├─→ {dep}")

        return "\n".join(lines)

    def generate_dot_graph(self) -> str:
        """Generate Graphviz DOT format."""
        lines = [
            "digraph ghcommon_dependencies {",
            "  rankdir=LR;",
            "  node [shape=box, style=rounded];",
            "",
        ]

        # Define subgraphs by category
        colors = {
            "root": "#ff6b6b",
            "docs": "#4ecdc4",
            "scripts": "#45b7d1",
            "workflows": "#f9ca24",
            "tools": "#6c5ce7",
            "templates": "#a29bfe",
            "examples": "#fd79a8",
            "tests": "#2ecc71",
        }

        for category, color in colors.items():
            if category in self.file_types:
                lines.append(f"  subgraph cluster_{category} {{")
                lines.append(f'    label="{category.upper()}";')
                lines.append(f'    color="{color}";')

                for file in self.file_types[category]:
                    safe_name = (
                        file.replace("/", "_")
                        .replace(".", "_")
                        .replace("-", "_")
                    )
                    lines.append(
                        f'    {safe_name} [label="{Path(file).name}"];'
                    )

                lines.append("  }")
                lines.append("")

        # Add edges
        for source, targets in self.dependencies.items():
            safe_source = (
                source.replace("/", "_").replace(".", "_").replace("-", "_")
            )
            for target in targets:
                safe_target = (
                    target.replace("/", "_").replace(".", "_").replace("-", "_")
                )
                lines.append(f"  {safe_source} -> {safe_target};")

        lines.append("}")
        return "\n".join(lines)

    def generate_mermaid_graph(self) -> str:
        """Generate Mermaid.js format."""
        lines = ["```mermaid", "graph TD", ""]

        # Group by category
        for category, files in sorted(self.file_types.items()):
            lines.append(f"  subgraph {category}")

            limit = self.mermaid_max_files_per_category
            for file in sorted(files)[
                : (limit if limit and limit > 0 else None)
            ]:
                safe_name = (
                    file.replace("/", "_").replace(".", "_").replace("-", "_")
                )
                display_name = Path(file).name[:30]
                lines.append(f'    {safe_name}["{display_name}"]')

            lines.append("  end")
            lines.append("")

        # Add key relationships (limit to most important)
        edge_count = 0
        max_edges = self.mermaid_max_edges
        for source, targets in sorted(self.dependencies.items()):
            if max_edges and edge_count >= max_edges:
                break
            safe_source = (
                source.replace("/", "_").replace(".", "_").replace("-", "_")
            )
            for target in list(targets)[:3]:  # Max 3 deps per file
                safe_target = (
                    target.replace("/", "_").replace(".", "_").replace("-", "_")
                )
                lines.append(f"  {safe_source} --> {safe_target}")
                edge_count += 1

        lines.append("```")
        return "\n".join(lines)

    def generate_html_report(self) -> str:
        """Generate interactive HTML report."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_files = sum(len(files) for files in self.file_types.values())
        total_deps = sum(len(deps) for deps in self.dependencies.values())
        total_categories = len(self.file_types)
        orphan_count = len(self.orphans)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ghcommon Dependency Analysis</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-card h3 {{ margin: 0 0 10px 0; font-size: 24px; }}
        .stat-card p {{ margin: 0; font-size: 14px; opacity: 0.9; }}
        .file-list {{ background: #f8f9fa; padding: 15px; border-radius: 4px; margin: 10px 0; max-height: 400px; overflow-y: auto; }}
        .file-item {{ padding: 8px; margin: 4px 0; background: white; border-left: 4px solid #3498db; border-radius: 4px; }}
        .dep-item {{ padding: 4px 0 4px 20px; color: #7f8c8d; font-size: 14px; }}
        .orphan {{ border-left-color: #e74c3c; }}
        .category {{ background: #ecf0f1; padding: 10px; margin: 10px 0; border-radius: 4px; cursor: pointer; }}
        .category:hover {{ background: #d5dbdb; }}
        details {{ margin: 10px 0; }}
        summary {{ cursor: pointer; font-weight: bold; padding: 10px; background: #ecf0f1; border-radius: 4px; }}
        summary:hover {{ background: #d5dbdb; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 ghcommon Repository Dependency Analysis</h1>
        <p><strong>Generated:</strong> {timestamp}</p>

        <div class="stats">
            <div class="stat-card">
                <h3>{total_files}</h3>
                <p>Total Files Analyzed</p>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                <h3>{total_deps}</h3>
                <p>Dependencies Found</p>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                <h3>{total_categories}</h3>
                <p>File Categories</p>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);">
                <h3>{orphan_count}</h3>
                <p>Potentially Unused Files</p>
            </div>
        </div>
"""

        # Add category sections
        for category, files in sorted(self.file_types.items()):
            html += f"""
        <details open>
            <summary>{category.upper()} ({len(files)} files)</summary>
            <div class="file-list">
"""
            for file in sorted(files):
                is_orphan = file in self.orphans
                orphan_class = " orphan" if is_orphan else ""
                deps = self.dependencies.get(file, set())
                refs = self.references.get(file, set())

                html += f'<div class="file-item{orphan_class}">'
                html += f"<strong>{file}</strong>"
                if is_orphan:
                    html += ' <span style="color: #e74c3c;">⚠️ Potentially unused</span>'

                if deps:
                    html += "<br><em>Depends on:</em>"
                    for dep in sorted(list(deps)[:10]):
                        html += f'<div class="dep-item">→ {dep}</div>'

                if refs:
                    html += f"<br><em>Referenced by: {len(refs)} file(s)</em>"

                html += "</div>\n"

            html += """
            </div>
        </details>
"""

        html += """
    </div>
</body>
</html>
"""

        return html

    def run_analysis(self):
        """Run complete analysis."""
        self.log("=" * 60)
        self.log("🔍 Starting comprehensive dependency analysis")
        self.log("=" * 60)

        # Scan all major directories
        self.scan_directory(self.root, "root")
        self.scan_directory(self.root / "docs", "docs")
        self.scan_directory(self.root / "scripts", "scripts")
        self.scan_directory(self.root / ".github" / "workflows", "workflows")
        self.scan_directory(self.root / "tools", "tools")
        self.scan_directory(self.root / "templates", "templates")
        self.scan_directory(self.root / "examples", "examples")
        self.scan_directory(self.root / "tests", "tests")

        # Find orphans
        self.find_orphans()

        # Generate outputs
        self.log("\n" + "=" * 60)
        self.log("📊 Generating output files...")
        self.log("=" * 60)

        output_dir = self.root / "dependency-analysis"
        output_dir.mkdir(exist_ok=True)

        # ASCII
        ascii_path = output_dir / "dependencies.txt"
        ascii_path.write_text(self.generate_ascii_graph())
        self.log(f"✅ Generated ASCII graph: {ascii_path}")

        # DOT
        dot_path = output_dir / "dependencies.dot"
        dot_path.write_text(self.generate_dot_graph())
        self.log(f"✅ Generated DOT graph: {dot_path}")
        self.log(f"   Run: dot -Tpng {dot_path} -o dependencies.png")

        # Mermaid
        mermaid_path = output_dir / "dependencies.mermaid.md"
        mermaid_path.write_text(self.generate_mermaid_graph())
        self.log(f"✅ Generated Mermaid graph: {mermaid_path}")

        # HTML
        html_path = output_dir / "dependencies.html"
        html_path.write_text(self.generate_html_report())
        self.log(f"✅ Generated HTML report: {html_path}")

        # JSON data
        json_data = {
            "file_types": {k: list(v) for k, v in self.file_types.items()},
            "dependencies": {k: list(v) for k, v in self.dependencies.items()},
            "references": {k: list(v) for k, v in self.references.items()},
            "orphans": list(self.orphans),
        }
        json_path = output_dir / "dependencies.json"
        json_path.write_text(json.dumps(json_data, indent=2))
        self.log(f"✅ Generated JSON data: {json_path}")

        # Progress log
        log_path = output_dir / "analysis.log"
        log_path.write_text("\n".join(self.progress_log))
        self.log(f"✅ Saved progress log: {log_path}")

        self.log("\n" + "=" * 60)
        self.log("✨ Analysis complete!")
        self.log("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze repository dependencies and generate multiple graph outputs."
    )
    default_root = str(Path(__file__).resolve().parent)
    parser.add_argument(
        "--root",
        default=default_root,
        help="Root path to analyze (default: script directory)",
    )
    parser.add_argument(
        "--exclude",
        default=".git,node_modules,.venv",
        help="Comma-separated directory names to exclude anywhere in paths.",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Generate full-size Mermaid output (no node/edge limits).",
    )
    parser.add_argument(
        "--mermaid-max-files",
        type=int,
        default=20,
        help="Maximum nodes per category for Mermaid output (ignored with --full).",
    )
    parser.add_argument(
        "--mermaid-max-edges",
        type=int,
        default=50,
        help="Maximum edges for Mermaid output (ignored with --full).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level.",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level), format="%(message)s"
    )

    exclude = [s.strip() for s in args.exclude.split(",") if s.strip()]
    max_files = None if args.full else args.mermaid_max_files
    max_edges = None if args.full else args.mermaid_max_edges

    analyzer = DependencyAnalyzer(
        args.root,
        exclude_dirs=exclude,
        mermaid_max_files_per_category=max_files
        if max_files is not None
        else 0
        if args.full
        else args.mermaid_max_files,
        mermaid_max_edges=max_edges
        if max_edges is not None
        else 0
        if args.full
        else args.mermaid_max_edges,
    )
    analyzer.run_analysis()
