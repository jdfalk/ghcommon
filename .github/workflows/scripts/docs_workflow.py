#!/usr/bin/env python3
# file: .github/workflows/scripts/docs_workflow.py
# version: 1.0.0
# guid: e4f5a6b7-c8d9-0e1f-2a3b-4c5d6e7f8a9b

"""Documentation generation workflow helper.

This module provides utilities for automated documentation generation from
source code, workflow definitions, and configuration files.

Features:
    - API documentation generation from Python docstrings
    - Workflow reference generation from GitHub Actions YAML definitions
    - Search index generation for static sites
    - Version-aware documentation builds
    - CLI entrypoints for integration with GitHub workflows

Usage:
    python docs_workflow.py generate-api --source .github/workflows/scripts \
        --output docs/generated/api
    python docs_workflow.py generate-workflows --workflows .github/workflows \
        --output docs/generated/workflows
    python docs_workflow.py build --source .github/workflows/scripts \
        --workflows .github/workflows --output docs/site
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml

from workflow_common import (
    append_summary_line,
    config_path,
    format_summary_table,
    get_repository_config,
    log_notice,
    log_warning,
)

# --------------------------------------------------------------------------- #
# Data structures                                                             #
# --------------------------------------------------------------------------- #


@dataclass
class DocFunction:
    """Documentation for a function."""

    name: str
    signature: str
    docstring: str


@dataclass
class DocClass:
    """Documentation for a class."""

    name: str
    docstring: str
    methods: list[DocFunction]


@dataclass
class DocModule:
    """Documentation for a Python module."""

    name: str
    path: Path
    version: str
    docstring: str
    functions: list[DocFunction]
    classes: list[DocClass]


@dataclass
class WorkflowDoc:
    """Documentation for a GitHub Actions workflow."""

    name: str
    file: Path
    on: list[str]
    description: str
    jobs: dict[str, Any]


# --------------------------------------------------------------------------- #
# Python documentation helpers                                                #
# --------------------------------------------------------------------------- #


def _format_args(args: ast.arguments) -> str:
    """Format function arguments into a signature string."""
    parts: list[str] = []
    defaults = list(args.defaults)
    kw_defaults = list(args.kw_defaults)

    def _format(arg: ast.arg, default: ast.AST | None) -> str:
        name = arg.arg
        annotation = ast.unparse(arg.annotation) if arg.annotation else None
        default_str = ast.unparse(default) if default else None
        result = name
        if annotation:
            result += f": {annotation}"
        if default_str:
            result += f" = {default_str}"
        return result

    positional = args.posonlyargs + args.args
    total_defaults = len(defaults)
    default_start = len(positional) - total_defaults
    for index, arg in enumerate(positional):
        default = defaults[index - default_start] if index >= default_start else None
        parts.append(_format(arg, default))

    if args.vararg:
        parts.append(f"*{args.vararg.arg}")

    if args.kwonlyargs:
        if not args.vararg:
            parts.append("*")
        for kw_arg, default in zip(args.kwonlyargs, kw_defaults):
            parts.append(_format(kw_arg, default))

    if args.kwarg:
        parts.append(f"**{args.kwarg.arg}")

    return ", ".join(parts)


def _extract_version(path: Path) -> str:
    """Extract module version from header comment."""
    for line in path.read_text(encoding="utf-8").splitlines()[:5]:
        match = re.search(r"#\s*version:\s*([0-9]+\.[0-9]+\.[0-9]+)", line, re.IGNORECASE)
        if match:
            return match.group(1)
    return "0.0.0"


def parse_python_module(path: Path) -> DocModule:
    """Parse a Python file into documentation structures."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    module_doc = ast.get_docstring(tree) or ""
    module_name = path.stem

    functions: list[DocFunction] = []
    classes: list[DocClass] = []

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            signature = f"{node.name}({_format_args(node.args)})"
            docstring = ast.get_docstring(node) or ""
            functions.append(DocFunction(node.name, signature, docstring))
        elif isinstance(node, ast.ClassDef):
            methods: list[DocFunction] = []
            docstring = ast.get_docstring(node) or ""
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    signature = f"{item.name}({_format_args(item.args)})"
                    method_doc = ast.get_docstring(item) or ""
                    methods.append(DocFunction(item.name, signature, method_doc))
            classes.append(DocClass(node.name, docstring, methods))

    return DocModule(
        name=module_name,
        path=path,
        version=_extract_version(path),
        docstring=module_doc,
        functions=functions,
        classes=classes,
    )


def discover_python_modules(sources: Iterable[Path]) -> list[DocModule]:
    """Discover Python modules under the given source directories."""
    modules: list[DocModule] = []
    for source in sources:
        for path in source.rglob("*.py"):
            if path.name.startswith("__"):
                continue
            modules.append(parse_python_module(path))
    modules.sort(key=lambda module: module.name)
    return modules


def generate_api_docs(source_dirs: list[str], output_dir: Path) -> list[Path]:
    """Generate Markdown documentation for Python helpers."""
    output_dir.mkdir(parents=True, exist_ok=True)
    sources = [Path(source).resolve() for source in source_dirs]
    modules = discover_python_modules(sources)
    written_files: list[Path] = []

    for module in modules:
        rel_path = module.path.relative_to(sources[0].parent)
        doc_path = output_dir / f"{module.name}.md"
        lines = [f"# Module `{module.name}`", "", f"**Version:** {module.version}", ""]
        if module.docstring:
            lines.extend([module.docstring.strip(), ""])

        if module.functions:
            lines.append("## Functions")
            lines.append("")
            for func in module.functions:
                lines.append(f"### `{func.signature}`")
                if func.docstring:
                    lines.append("")
                    lines.append(func.docstring.strip())
                lines.append("")

        if module.classes:
            lines.append("## Classes")
            lines.append("")
            for cls in module.classes:
                lines.append(f"### `{cls.name}`")
                if cls.docstring:
                    lines.append("")
                    lines.append(cls.docstring.strip())
                    lines.append("")
                if cls.methods:
                    lines.append("#### Methods")
                    lines.append("")
                    for method in cls.methods:
                        lines.append(f"- `{method.signature}`")
                        if method.docstring:
                            lines.append(f"  - {method.docstring.strip()}")
                    lines.append("")

        lines.append(f"_Source: `{rel_path}`_")
        doc_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
        written_files.append(doc_path)

    return written_files


# --------------------------------------------------------------------------- #
# Workflow documentation helpers                                             #
# --------------------------------------------------------------------------- #


def parse_workflow(path: Path) -> WorkflowDoc:
    """Parse a workflow YAML file into documentation structure."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    name = data.get("name", path.stem)
    triggers = list(data.get("on", {}))
    description = data.get("description", "")
    jobs = data.get("jobs", {})
    return WorkflowDoc(name=name, file=path, on=triggers, description=description, jobs=jobs)


def discover_workflows(workflows_dir: Path) -> list[WorkflowDoc]:
    """Discover workflow files."""
    docs: list[WorkflowDoc] = []
    for path in workflows_dir.glob("*.yml"):
        docs.append(parse_workflow(path))
    for path in workflows_dir.glob("*.yaml"):
        docs.append(parse_workflow(path))
    docs.sort(key=lambda doc: doc.name)
    return docs


def generate_workflow_docs(workflows_dir: str, output: Path) -> Path:
    """Generate Markdown documentation for workflows."""
    output.parent.mkdir(parents=True, exist_ok=True)
    workflows = discover_workflows(Path(workflows_dir))
    lines = ["# Workflow Catalog", ""]

    for workflow in workflows:
        lines.append(f"## {workflow.name}")
        if workflow.description:
            lines.append("")
            lines.append(workflow.description)
        lines.append("")
        lines.append("**File:** `" + str(workflow.file) + "`  ")
        lines.append("**Triggers:** " + ", ".join(workflow.on or ["manual"]))
        lines.append("")
        lines.append("### Jobs")
        lines.append("")
        for job_name, job in workflow.jobs.items():
            lines.append(f"- **{job_name}**: runs-on `{job.get('runs-on', 'N/A')}`")
        lines.append("")

    output.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    return output


# --------------------------------------------------------------------------- #
# Build orchestration                                                         #
# --------------------------------------------------------------------------- #


def _derive_version(version: str | None) -> str:
    """Derive documentation version from args, env, or config."""
    if version:
        return version
    env_version = os.environ.get("DOC_VERSION")
    if env_version:
        return env_version
    config = get_repository_config()
    doc_version = config_path(None, "documentation", "version")
    if isinstance(doc_version, str) and doc_version:
        return doc_version
    branch = os.environ.get("GITHUB_REF_NAME")
    if branch and branch.startswith("stable-"):
        return branch
    return "latest"


def build_documentation(
    source_dirs: list[str],
    workflows_dir: str,
    output_root: Path,
    version: str | None = None,
) -> dict[str, Any]:
    """Build documentation site structure."""
    version_name = _derive_version(version)
    version_dir = output_root / version_name
    api_dir = version_dir / "api"
    workflows_output = version_dir / "workflows.md"

    output_root.mkdir(parents=True, exist_ok=True)
    version_dir.mkdir(parents=True, exist_ok=True)

    log_notice(f"Building documentation for version '{version_name}'")
    api_files = generate_api_docs(source_dirs, api_dir)
    generate_workflow_docs(workflows_dir, workflows_output)

    search_index = [
        {"title": doc_path.stem, "path": str(doc_path.relative_to(output_root))}
        for doc_path in api_files
    ]
    search_index.append(
        {"title": "Workflows", "path": str(workflows_output.relative_to(output_root))}
    )

    (output_root / "search-index.json").write_text(
        json.dumps(search_index, indent=2),
        encoding="utf-8",
    )

    versions_path = output_root / "versions.json"
    versions: list[str] = []
    if versions_path.exists():
        try:
            versions = json.loads(versions_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            log_warning("versions.json malformed; regenerating")
    if version_name not in versions:
        versions.append(version_name)
    versions_path.write_text(json.dumps(sorted(versions), indent=2), encoding="utf-8")

    summary_table = format_summary_table(
        [
            ("Version", version_name),
            ("API Docs", f"{len(api_files)} files"),
            ("Workflows Doc", str(workflows_output.relative_to(output_root))),
        ]
    )
    append_summary_line(summary_table)

    return {
        "version": version_name,
        "api": [str(path) for path in api_files],
        "workflows": str(workflows_output),
        "search_index": str(output_root / "search-index.json"),
    }


# --------------------------------------------------------------------------- #
# CLI                                                                         #
# --------------------------------------------------------------------------- #


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Documentation workflow utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    api_parser = subparsers.add_parser("generate-api", help="Generate API documentation")
    api_parser.add_argument(
        "--source",
        action="append",
        required=True,
        help="Source directory containing Python helpers (repeatable)",
    )
    api_parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output directory for generated API docs",
    )

    wf_parser = subparsers.add_parser(
        "generate-workflows", help="Generate workflow documentation"
    )
    wf_parser.add_argument(
        "--workflows",
        type=Path,
        required=True,
        help="Directory containing workflow YAML files",
    )
    wf_parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output Markdown file",
    )

    build_parser = subparsers.add_parser("build", help="Build complete documentation")
    build_parser.add_argument(
        "--source",
        action="append",
        default=[".github/workflows/scripts"],
        help="Source directories for API docs (default: scripts)",
    )
    build_parser.add_argument(
        "--workflows",
        default=".github/workflows",
        help="Directory containing workflow files",
    )
    build_parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Documentation output root directory",
    )
    build_parser.add_argument(
        "--version",
        help="Documentation version (overrides config/env)",
    )

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv or sys.argv[1:])

    if args.command == "generate-api":
        generate_api_docs(args.source, args.output)
        return

    if args.command == "generate-workflows":
        generate_workflow_docs(str(args.workflows), args.output)
        return

    if args.command == "build":
        build_documentation(
            source_dirs=args.source,
            workflows_dir=str(args.workflows),
            output_root=args.output,
            version=args.version,
        )
        return

    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
