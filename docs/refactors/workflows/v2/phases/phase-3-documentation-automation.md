<!-- file: docs/refactors/workflows/v2/phases/phase-3-documentation-automation.md -->
<!-- version: 1.0.0 -->
<!-- guid: d3e4f5a6-b7c8-9d0e-1f2a-3b4c5d6e7f8a -->

# Phase 3: Documentation Automation

## Overview

This phase implements automated documentation generation, versioning, and publishing for the v2
workflow system. It provides tools to generate API documentation, workflow references, and user
guides from code and configuration.

## Goals

- Automate generation of documentation from code comments and workflow definitions
- Support versioned documentation for multiple language/version combinations
- Generate API references for Python helper modules
- Create workflow catalogs from YAML definitions
- Publish documentation to GitHub Pages with branch-specific versions
- Maintain documentation for stable branches alongside main branch

## Success Criteria

- [ ] `docs_workflow.py` helper module created with documentation generation functions
- [ ] Automated API documentation from Python docstrings
- [ ] Workflow reference generation from YAML files
- [ ] Versioned documentation site with branch selector
- [ ] Documentation publishing workflow operational
- [ ] All documentation follows Google Style Guides
- [ ] Documentation coverage for all helper modules and workflows
- [ ] Search functionality across all documentation versions
- [ ] No Windows references in any generated documentation

## Dependencies

- Phase 0: `workflow_common.py` for config loading and validation
- Phase 1: CI workflow definitions for reference generation
- Phase 2: Release workflow definitions for reference generation

---

## Task 3.1: Create docs_workflow.py Helper Module

**Status**: Not Started **Dependencies**: Phase 0 (workflow_common.py) **Estimated Time**: 4 hours
**Idempotent**: Yes

### Description

Create a Python helper module for automated documentation generation from code and configuration
files.

### Code Style Requirements

**MUST follow**:

- `.github/instructions/python.instructions.md` - Google Python Style Guide
- `.github/instructions/general-coding.instructions.md` - File headers, versioning

### Implementation

Create file: `.github/workflows/scripts/docs_workflow.py`

````python
#!/usr/bin/env python3
# file: .github/workflows/scripts/docs_workflow.py
# version: 1.0.0
# guid: e4f5a6b7-c8d9-0e1f-2a3b-4c5d6e7f8a9b

"""Documentation generation workflow helper.

This module provides utilities for automated documentation generation from
source code, workflow definitions, and configuration files.

Features:
    - API documentation generation from Python docstrings
    - Workflow reference generation from YAML files
    - Configuration schema documentation
    - Multi-version documentation support
    - Search index generation
    - GitHub Pages publishing support

Usage:
    # Generate API documentation
    python docs_workflow.py generate-api --output docs/api

    # Generate workflow reference
    python docs_workflow.py generate-workflows --output docs/workflows

    # Build complete documentation site
    python docs_workflow.py build --output docs-site

Example:
    from docs_workflow import generate_api_docs, generate_workflow_docs

    # Generate API docs for all Python modules
    api_docs = generate_api_docs("scripts")

    # Generate workflow reference
    workflow_docs = generate_workflow_docs(".github/workflows")
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# Ensure workflow_common is importable
sys.path.insert(0, str(Path(__file__).parent))
import workflow_common


@dataclass
class DocModule:
    """Documentation information for a Python module.

    Attributes:
        name: Module name (e.g., 'workflow_common').
        path: Path to the module file.
        docstring: Module-level docstring.
        functions: List of documented functions.
        classes: List of documented classes.
        version: Module version from header.
    """

    name: str
    path: Path
    docstring: str
    functions: list[DocFunction]
    classes: list[DocClass]
    version: str


@dataclass
class DocFunction:
    """Documentation for a function.

    Attributes:
        name: Function name.
        signature: Full function signature with type hints.
        docstring: Function docstring in Google style.
        args: List of argument names and types.
        returns: Return type and description.
        raises: List of exceptions raised.
        examples: List of usage examples.
    """

    name: str
    signature: str
    docstring: str
    args: list[tuple[str, str, str]]  # (name, type, description)
    returns: tuple[str, str]  # (type, description)
    raises: list[tuple[str, str]]  # (exception, description)
    examples: list[str]


@dataclass
class DocClass:
    """Documentation for a class.

    Attributes:
        name: Class name.
        docstring: Class docstring.
        bases: List of base class names.
        attributes: List of class/instance attributes.
        methods: List of documented methods.
    """

    name: str
    docstring: str
    bases: list[str]
    attributes: list[tuple[str, str, str]]  # (name, type, description)
    methods: list[DocFunction]


@dataclass
class WorkflowDoc:
    """Documentation for a GitHub Actions workflow.

    Attributes:
        name: Workflow name.
        file: Workflow filename.
        description: Workflow description.
        triggers: List of trigger events.
        inputs: Workflow dispatch inputs.
        outputs: Workflow outputs.
        jobs: List of job definitions.
        secrets: Required secrets.
    """

    name: str
    file: str
    description: str
    triggers: list[str]
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    jobs: list[dict[str, Any]]
    secrets: list[str]


def extract_module_info(module_path: Path) -> DocModule:
    """Extract documentation information from a Python module.

    Parses the module file using AST to extract docstrings, function
    signatures, and class definitions following Google Python Style Guide
    conventions.

    Args:
        module_path: Path to the Python module file.

    Returns:
        DocModule containing all extracted documentation information.

    Raises:
        WorkflowError: If module file cannot be parsed or read.

    Example:
        >>> module = extract_module_info(Path("workflow_common.py"))
        >>> print(module.name)
        workflow_common
        >>> print(len(module.functions))
        15
    """
    try:
        content = module_path.read_text(encoding="utf-8")
    except OSError as e:
        raise workflow_common.WorkflowError(
            f"Failed to read module {module_path}: {e}"
        ) from e

    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        raise workflow_common.WorkflowError(
            f"Failed to parse module {module_path}: {e}"
        ) from e

    # Extract version from header
    version_match = re.search(r"# version: ([\d.]+)", content)
    version = version_match.group(1) if version_match else "unknown"

    # Extract module docstring
    module_docstring = ast.get_docstring(tree) or ""

    functions = []
    classes = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_doc = _extract_function_doc(node)
            if func_doc:
                functions.append(func_doc)
        elif isinstance(node, ast.ClassDef):
            class_doc = _extract_class_doc(node)
            if class_doc:
                classes.append(class_doc)

    return DocModule(
        name=module_path.stem,
        path=module_path,
        docstring=module_docstring,
        functions=functions,
        classes=classes,
        version=version,
    )


def _extract_function_doc(node: ast.FunctionDef) -> DocFunction | None:
    """Extract documentation from a function AST node.

    Args:
        node: AST FunctionDef node.

    Returns:
        DocFunction if function has docstring, None otherwise.
    """
    docstring = ast.get_docstring(node)
    if not docstring:
        return None

    # Build function signature
    args_list = []
    for arg in node.args.args:
        arg_name = arg.arg
        arg_type = _get_type_annotation(arg.annotation)
        args_list.append((arg_name, arg_type, ""))

    return_type = _get_type_annotation(node.returns)

    # Parse Google-style docstring sections
    args_docs = _parse_docstring_section(docstring, "Args:")
    returns_docs = _parse_docstring_section(docstring, "Returns:")
    raises_docs = _parse_docstring_section(docstring, "Raises:")
    examples = _parse_docstring_section(docstring, "Example:")

    # Match args with their descriptions
    enriched_args = []
    for arg_name, arg_type, _ in args_list:
        description = args_docs.get(arg_name, "")
        enriched_args.append((arg_name, arg_type, description))

    return DocFunction(
        name=node.name,
        signature=_build_signature(node),
        docstring=docstring,
        args=enriched_args,
        returns=(return_type, returns_docs.get("return", "")),
        raises=[(k, v) for k, v in raises_docs.items()],
        examples=list(examples.values()) if examples else [],
    )


def _extract_class_doc(node: ast.ClassDef) -> DocClass | None:
    """Extract documentation from a class AST node.

    Args:
        node: AST ClassDef node.

    Returns:
        DocClass if class has docstring, None otherwise.
    """
    docstring = ast.get_docstring(node)
    if not docstring:
        return None

    # Extract base classes
    bases = [_get_base_name(base) for base in node.bases]

    # Extract attributes from docstring
    attrs_section = _parse_docstring_section(docstring, "Attributes:")
    attributes = [(k, "", v) for k, v in attrs_section.items()]

    # Extract methods
    methods = []
    for item in node.body:
        if isinstance(item, ast.FunctionDef):
            method_doc = _extract_function_doc(item)
            if method_doc:
                methods.append(method_doc)

    return DocClass(
        name=node.name,
        docstring=docstring,
        bases=bases,
        attributes=attributes,
        methods=methods,
    )


def _get_type_annotation(annotation: ast.expr | None) -> str:
    """Convert AST type annotation to string representation.

    Args:
        annotation: AST expression for type annotation.

    Returns:
        String representation of the type, or 'Any' if None.
    """
    if annotation is None:
        return "Any"
    return ast.unparse(annotation)


def _get_base_name(base: ast.expr) -> str:
    """Extract base class name from AST expression.

    Args:
        base: AST expression for base class.

    Returns:
        Name of the base class.
    """
    if isinstance(base, ast.Name):
        return base.id
    return ast.unparse(base)


def _build_signature(node: ast.FunctionDef) -> str:
    """Build full function signature with type hints.

    Args:
        node: AST FunctionDef node.

    Returns:
        Complete function signature as string.
    """
    args_parts = []
    for arg in node.args.args:
        arg_str = arg.arg
        if arg.annotation:
            arg_str += f": {_get_type_annotation(arg.annotation)}"
        args_parts.append(arg_str)

    signature = f"{node.name}({', '.join(args_parts)})"
    if node.returns:
        signature += f" -> {_get_type_annotation(node.returns)}"

    return signature


def _parse_docstring_section(docstring: str, section_name: str) -> dict[str, str]:
    """Parse a section from Google-style docstring.

    Args:
        docstring: Full docstring text.
        section_name: Section header to find (e.g., 'Args:', 'Returns:').

    Returns:
        Dictionary mapping item names to descriptions.
    """
    result = {}
    lines = docstring.split("\n")

    in_section = False
    current_item = None
    current_desc = []

    for line in lines:
        stripped = line.strip()

        if stripped == section_name:
            in_section = True
            continue

        if in_section:
            # Check if we hit another section
            if stripped.endswith(":") and not stripped.startswith(" "):
                break

            # Check if line starts a new item (name: description)
            if stripped and not stripped.startswith(" "):
                if current_item:
                    result[current_item] = " ".join(current_desc).strip()
                    current_desc = []

                if ":" in stripped:
                    item_name, desc = stripped.split(":", 1)
                    current_item = item_name.strip()
                    current_desc = [desc.strip()]
                else:
                    current_item = stripped
            elif stripped:
                # Continuation of current item description
                current_desc.append(stripped)

    # Add the last item
    if current_item:
        result[current_item] = " ".join(current_desc).strip()

    return result


def generate_api_docs(scripts_dir: str | Path, output_dir: str | Path) -> list[Path]:
    """Generate API documentation for all Python modules in directory.

    Creates markdown files with comprehensive API documentation extracted
    from Python docstrings following Google Python Style Guide.

    Args:
        scripts_dir: Directory containing Python modules.
        output_dir: Directory to write markdown documentation files.

    Returns:
        List of generated documentation file paths.

    Raises:
        WorkflowError: If script directory doesn't exist or is not readable.

    Example:
        >>> docs = generate_api_docs("scripts", "docs/api")
        >>> print(f"Generated {len(docs)} API documentation files")
        Generated 6 API documentation files
    """
    scripts_path = Path(scripts_dir)
    output_path = Path(output_dir)

    if not scripts_path.exists():
        raise workflow_common.WorkflowError(f"Scripts directory not found: {scripts_dir}")

    output_path.mkdir(parents=True, exist_ok=True)

    generated_files = []

    # Find all Python modules
    for py_file in scripts_path.glob("*.py"):
        if py_file.name.startswith("_"):
            continue  # Skip private modules

        workflow_common.log_info(f"Processing module: {py_file.name}")

        module = extract_module_info(py_file)
        doc_file = output_path / f"{module.name}.md"

        _write_module_docs(module, doc_file)
        generated_files.append(doc_file)

    workflow_common.log_info(f"Generated {len(generated_files)} API documentation files")
    return generated_files


def _write_module_docs(module: DocModule, output_file: Path) -> None:
    """Write module documentation to markdown file.

    Args:
        module: Module documentation to write.
        output_file: Path to output markdown file.
    """
    lines = []

    # Header
    lines.append(f"# {module.name}")
    lines.append("")
    lines.append(f"**Version**: {module.version}")
    lines.append("")

    # Module docstring
    if module.docstring:
        lines.append(module.docstring)
        lines.append("")

    # Functions
    if module.functions:
        lines.append("## Functions")
        lines.append("")
        for func in module.functions:
            lines.extend(_format_function_docs(func))

    # Classes
    if module.classes:
        lines.append("## Classes")
        lines.append("")
        for cls in module.classes:
            lines.extend(_format_class_docs(cls))

    output_file.write_text("\n".join(lines), encoding="utf-8")


def _format_function_docs(func: DocFunction) -> list[str]:
    """Format function documentation as markdown.

    Args:
        func: Function documentation to format.

    Returns:
        List of markdown lines.
    """
    lines = []

    lines.append(f"### `{func.name}`")
    lines.append("")
    lines.append(f"```python")
    lines.append(func.signature)
    lines.append(f"```")
    lines.append("")

    # Description (first paragraph of docstring)
    desc_lines = func.docstring.split("\n\n")[0].split("\n")
    for line in desc_lines:
        lines.append(line.strip())
    lines.append("")

    # Arguments
    if func.args:
        lines.append("**Arguments:**")
        lines.append("")
        for name, type_hint, description in func.args:
            lines.append(f"- `{name}` ({type_hint}): {description}")
        lines.append("")

    # Returns
    if func.returns[1]:
        lines.append("**Returns:**")
        lines.append("")
        lines.append(f"- {func.returns[0]}: {func.returns[1]}")
        lines.append("")

    # Raises
    if func.raises:
        lines.append("**Raises:**")
        lines.append("")
        for exception, description in func.raises:
            lines.append(f"- `{exception}`: {description}")
        lines.append("")

    # Examples
    if func.examples:
        lines.append("**Example:**")
        lines.append("")
        for example in func.examples:
            lines.append("```python")
            lines.append(example)
            lines.append("```")
        lines.append("")

    return lines


def _format_class_docs(cls: DocClass) -> list[str]:
    """Format class documentation as markdown.

    Args:
        cls: Class documentation to format.

    Returns:
        List of markdown lines.
    """
    lines = []

    # Class header
    if cls.bases:
        bases_str = ", ".join(cls.bases)
        lines.append(f"### `{cls.name}({bases_str})`")
    else:
        lines.append(f"### `{cls.name}`")
    lines.append("")

    # Description
    desc_lines = cls.docstring.split("\n\n")[0].split("\n")
    for line in desc_lines:
        lines.append(line.strip())
    lines.append("")

    # Attributes
    if cls.attributes:
        lines.append("**Attributes:**")
        lines.append("")
        for name, type_hint, description in cls.attributes:
            type_str = f" ({type_hint})" if type_hint else ""
            lines.append(f"- `{name}`{type_str}: {description}")
        lines.append("")

    # Methods
    if cls.methods:
        lines.append("**Methods:**")
        lines.append("")
        for method in cls.methods:
            lines.extend(_format_function_docs(method))

    return lines


def extract_workflow_info(workflow_path: Path) -> WorkflowDoc:
    """Extract documentation from a GitHub Actions workflow file.

    Args:
        workflow_path: Path to workflow YAML file.

    Returns:
        WorkflowDoc containing extracted workflow information.

    Raises:
        WorkflowError: If workflow file cannot be parsed.
    """
    try:
        with open(workflow_path, encoding="utf-8") as f:
            workflow = yaml.safe_load(f)
    except (OSError, yaml.YAMLError) as e:
        raise workflow_common.WorkflowError(
            f"Failed to parse workflow {workflow_path}: {e}"
        ) from e

    name = workflow.get("name", workflow_path.stem)

    # Extract description from comments at top of file
    description = ""
    try:
        content = workflow_path.read_text(encoding="utf-8")
        for line in content.split("\n")[:10]:
            if line.strip().startswith("#") and "description:" in line.lower():
                description = line.split(":", 1)[1].strip()
                break
    except OSError:
        pass

    # Extract triggers
    triggers = list(workflow.get("on", {}).keys()) if isinstance(workflow.get("on"), dict) else []

    # Extract workflow_dispatch inputs
    inputs = {}
    if "on" in workflow and isinstance(workflow["on"], dict):
        dispatch = workflow["on"].get("workflow_dispatch", {})
        inputs = dispatch.get("inputs", {})

    # Extract outputs
    outputs = workflow.get("outputs", {})

    # Extract jobs
    jobs = []
    if "jobs" in workflow:
        for job_name, job_def in workflow["jobs"].items():
            jobs.append({
                "name": job_name,
                "runs-on": job_def.get("runs-on", ""),
                "steps": len(job_def.get("steps", [])),
            })

    # Extract required secrets
    secrets = []
    content = workflow_path.read_text(encoding="utf-8")
    secret_matches = re.findall(r"\$\{\{\s*secrets\.(\w+)\s*\}\}", content)
    secrets = sorted(set(secret_matches))

    return WorkflowDoc(
        name=name,
        file=workflow_path.name,
        description=description,
        triggers=triggers,
        inputs=inputs,
        outputs=outputs,
        jobs=jobs,
        secrets=secrets,
    )


def generate_workflow_docs(
    workflows_dir: str | Path, output_dir: str | Path
) -> list[Path]:
    """Generate documentation for all workflows in directory.

    Args:
        workflows_dir: Directory containing workflow YAML files.
        output_dir: Directory to write workflow documentation.

    Returns:
        List of generated documentation file paths.

    Raises:
        WorkflowError: If workflows directory doesn't exist.
    """
    workflows_path = Path(workflows_dir)
    output_path = Path(output_dir)

    if not workflows_path.exists():
        raise workflow_common.WorkflowError(
            f"Workflows directory not found: {workflows_dir}"
        )

    output_path.mkdir(parents=True, exist_ok=True)

    generated_files = []

    # Find all workflow files
    for workflow_file in workflows_path.glob("*.yml"):
        if workflow_file.name.startswith("."):
            continue

        workflow_common.log_info(f"Processing workflow: {workflow_file.name}")

        workflow = extract_workflow_info(workflow_file)
        doc_file = output_path / f"{workflow_file.stem}.md"

        _write_workflow_docs(workflow, doc_file)
        generated_files.append(doc_file)

    workflow_common.log_info(
        f"Generated {len(generated_files)} workflow documentation files"
    )
    return generated_files


def _write_workflow_docs(workflow: WorkflowDoc, output_file: Path) -> None:
    """Write workflow documentation to markdown file.

    Args:
        workflow: Workflow documentation to write.
        output_file: Path to output markdown file.
    """
    lines = []

    # Header
    lines.append(f"# {workflow.name}")
    lines.append("")
    lines.append(f"**File**: `{workflow.file}`")
    lines.append("")

    if workflow.description:
        lines.append(workflow.description)
        lines.append("")

    # Triggers
    if workflow.triggers:
        lines.append("## Triggers")
        lines.append("")
        for trigger in workflow.triggers:
            lines.append(f"- `{trigger}`")
        lines.append("")

    # Inputs
    if workflow.inputs:
        lines.append("## Inputs")
        lines.append("")
        lines.append("| Input | Type | Required | Default | Description |")
        lines.append("|-------|------|----------|---------|-------------|")
        for input_name, input_def in workflow.inputs.items():
            input_type = input_def.get("type", "string")
            required = "Yes" if input_def.get("required", False) else "No"
            default = input_def.get("default", "-")
            description = input_def.get("description", "")
            lines.append(
                f"| `{input_name}` | {input_type} | {required} | {default} | {description} |"
            )
        lines.append("")

    # Outputs
    if workflow.outputs:
        lines.append("## Outputs")
        lines.append("")
        for output_name, output_def in workflow.outputs.items():
            description = output_def.get("description", "")
            lines.append(f"- `{output_name}`: {description}")
        lines.append("")

    # Jobs
    if workflow.jobs:
        lines.append("## Jobs")
        lines.append("")
        for job in workflow.jobs:
            lines.append(f"### {job['name']}")
            lines.append("")
            lines.append(f"- **Runs on**: {job['runs-on']}")
            lines.append(f"- **Steps**: {job['steps']}")
            lines.append("")

    # Secrets
    if workflow.secrets:
        lines.append("## Required Secrets")
        lines.append("")
        for secret in workflow.secrets:
            lines.append(f"- `{secret}`")
        lines.append("")

    output_file.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    """Main entry point for documentation generation CLI."""
    parser = argparse.ArgumentParser(
        description="Generate documentation for workflow system"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # API docs command
    api_parser = subparsers.add_parser("generate-api", help="Generate API documentation")
    api_parser.add_argument(
        "--scripts-dir",
        default=".github/workflows/scripts",
        help="Directory containing Python modules",
    )
    api_parser.add_argument(
        "--output",
        default="docs/api",
        help="Output directory for API docs",
    )

    # Workflow docs command
    workflow_parser = subparsers.add_parser(
        "generate-workflows", help="Generate workflow documentation"
    )
    workflow_parser.add_argument(
        "--workflows-dir",
        default=".github/workflows",
        help="Directory containing workflow files",
    )
    workflow_parser.add_argument(
        "--output",
        default="docs/workflows",
        help="Output directory for workflow docs",
    )

    args = parser.parse_args()

    try:
        if args.command == "generate-api":
            files = generate_api_docs(args.scripts_dir, args.output)
            workflow_common.set_output("api_docs", json.dumps([str(f) for f in files]))

        elif args.command == "generate-workflows":
            files = generate_workflow_docs(args.workflows_dir, args.output)
            workflow_common.set_output(
                "workflow_docs", json.dumps([str(f) for f in files])
            )

        sys.exit(0)

    except workflow_common.WorkflowError as e:
        workflow_common.log_error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
````

### Verification Steps

```bash
# 1. Verify script file exists
test -f .github/workflows/scripts/docs_workflow.py && echo "✅ Script created"

# 2. Check Python syntax
python3 -m py_compile .github/workflows/scripts/docs_workflow.py && echo "✅ Valid Python"

# 3. Make executable
chmod +x .github/workflows/scripts/docs_workflow.py && echo "✅ Executable"

# 4. Test API doc generation
python3 .github/workflows/scripts/docs_workflow.py generate-api \
  --scripts-dir .github/workflows/scripts \
  --output /tmp/docs-test/api && echo "✅ API docs generated"

# 5. Test workflow doc generation
python3 .github/workflows/scripts/docs_workflow.py generate-workflows \
  --workflows-dir .github/workflows \
  --output /tmp/docs-test/workflows && echo "✅ Workflow docs generated"
```

---

## Task 3.2: Create Unit Tests for docs_workflow

**Status**: Not Started **Dependencies**: Task 3.1 (docs_workflow.py) **Estimated Time**: 3 hours
**Idempotent**: Yes

### Description

Create comprehensive unit tests for the documentation generation module.

### Code Style Requirements

**MUST follow**:

- `.github/instructions/test-generation.instructions.md` - Arrange-Act-Assert pattern

### Implementation

Create file: `tests/workflow_scripts/test_docs_workflow.py`

```python
#!/usr/bin/env python3
# file: tests/workflow_scripts/test_docs_workflow.py
# version: 1.0.0
# guid: f5a6b7c8-d9e0-1f2a-3b4c-5d6e7f8a9b0c

"""Unit tests for docs_workflow module."""

from __future__ import annotations

import sys
from pathlib import Path
from textwrap import dedent
from unittest.mock import MagicMock, patch

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / ".github/workflows/scripts"))

import docs_workflow
import workflow_common


@pytest.fixture(autouse=True)
def reset_config_cache():
    """Reset global config cache between tests."""
    workflow_common._CONFIG_CACHE = None
    yield
    workflow_common._CONFIG_CACHE = None


def test_extract_module_info_basic(tmp_path):
    """Test extract_module_info extracts basic module information."""
    # Arrange
    module_content = dedent('''
        #!/usr/bin/env python3
        # file: test_module.py
        # version: 1.2.3
        # guid: test-guid

        """Test module docstring.

        This is a test module.
        """

        def test_function():
            """Test function."""
            pass
    ''')

    module_file = tmp_path / "test_module.py"
    module_file.write_text(module_content)

    # Act
    module = docs_workflow.extract_module_info(module_file)

    # Assert
    assert module.name == "test_module"
    assert module.version == "1.2.3"
    assert "Test module docstring" in module.docstring
    assert len(module.functions) == 1
    assert module.functions[0].name == "test_function"


def test_extract_module_info_with_classes(tmp_path):
    """Test extract_module_info extracts class information."""
    # Arrange
    module_content = dedent('''
        """Module with classes."""

        class TestClass:
            """Test class.

            Attributes:
                attr1: First attribute.
                attr2: Second attribute.
            """

            def method1(self):
                """First method."""
                pass
    ''')

    module_file = tmp_path / "test_module.py"
    module_file.write_text(module_content)

    # Act
    module = docs_workflow.extract_module_info(module_file)

    # Assert
    assert len(module.classes) == 1
    assert module.classes[0].name == "TestClass"
    assert len(module.classes[0].attributes) == 2
    assert len(module.classes[0].methods) == 1


def test_extract_function_doc_with_google_style(tmp_path):
    """Test function extraction with Google-style docstring."""
    # Arrange
    module_content = dedent('''
        def example_function(arg1: str, arg2: int) -> bool:
            """Example function with Google-style docstring.

            Args:
                arg1: First argument description.
                arg2: Second argument description.

            Returns:
                Boolean result.

            Raises:
                ValueError: If arg2 is negative.

            Example:
                >>> example_function("test", 42)
                True
            """
            return True
    ''')

    module_file = tmp_path / "test_module.py"
    module_file.write_text(module_content)

    # Act
    module = docs_workflow.extract_module_info(module_file)

    # Assert
    func = module.functions[0]
    assert func.name == "example_function"
    assert len(func.args) == 2
    assert func.args[0][0] == "arg1"
    assert func.args[0][2] == "First argument description."
    assert func.returns[1] == "Boolean result."
    assert len(func.raises) == 1
    assert func.raises[0][0] == "ValueError"


def test_generate_api_docs_creates_files(tmp_path):
    """Test generate_api_docs creates markdown files."""
    # Arrange
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()

    module_content = dedent('''
        """Test module."""

        def test_func():
            """Test function."""
            pass
    ''')

    (scripts_dir / "test_module.py").write_text(module_content)

    output_dir = tmp_path / "docs"

    # Act
    files = docs_workflow.generate_api_docs(scripts_dir, output_dir)

    # Assert
    assert len(files) == 1
    assert files[0].name == "test_module.md"
    assert files[0].exists()
    content = files[0].read_text()
    assert "# test_module" in content
    assert "## Functions" in content


def test_generate_api_docs_skips_private_modules(tmp_path):
    """Test generate_api_docs skips private modules."""
    # Arrange
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()

    (scripts_dir / "_private.py").write_text('"""Private module."""')
    (scripts_dir / "public.py").write_text('"""Public module."""')

    output_dir = tmp_path / "docs"

    # Act
    files = docs_workflow.generate_api_docs(scripts_dir, output_dir)

    # Assert
    assert len(files) == 1
    assert files[0].name == "public.md"


def test_generate_api_docs_missing_directory():
    """Test generate_api_docs raises error for missing directory."""
    # Arrange & Act & Assert
    with pytest.raises(workflow_common.WorkflowError) as exc_info:
        docs_workflow.generate_api_docs("/nonexistent", "/tmp/docs")

    assert "not found" in str(exc_info.value)


def test_extract_workflow_info_basic(tmp_path):
    """Test extract_workflow_info extracts basic workflow information."""
    # Arrange
    workflow_content = dedent('''
        name: Test Workflow

        on:
          push:
          pull_request:
          workflow_dispatch:
            inputs:
              test_input:
                description: Test input
                type: string
                required: true

        jobs:
          test_job:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v4
              - run: echo "test"
    ''')

    workflow_file = tmp_path / "test.yml"
    workflow_file.write_text(workflow_content)

    # Act
    workflow = docs_workflow.extract_workflow_info(workflow_file)

    # Assert
    assert workflow.name == "Test Workflow"
    assert workflow.file == "test.yml"
    assert "push" in workflow.triggers
    assert "workflow_dispatch" in workflow.triggers
    assert "test_input" in workflow.inputs
    assert len(workflow.jobs) == 1
    assert workflow.jobs[0]["name"] == "test_job"


def test_extract_workflow_info_with_secrets(tmp_path):
    """Test extract_workflow_info extracts secret references."""
    # Arrange
    workflow_content = dedent('''
        name: Test Workflow

        on: push

        jobs:
          test:
            runs-on: ubuntu-latest
            steps:
              - env:
                  TOKEN: ${{ secrets.GITHUB_TOKEN }}
                  API_KEY: ${{ secrets.API_KEY }}
                run: echo "test"
    ''')

    workflow_file = tmp_path / "test.yml"
    workflow_file.write_text(workflow_content)

    # Act
    workflow = docs_workflow.extract_workflow_info(workflow_file)

    # Assert
    assert "GITHUB_TOKEN" in workflow.secrets
    assert "API_KEY" in workflow.secrets


def test_generate_workflow_docs_creates_files(tmp_path):
    """Test generate_workflow_docs creates markdown files."""
    # Arrange
    workflows_dir = tmp_path / "workflows"
    workflows_dir.mkdir()

    workflow_content = dedent('''
        name: Test Workflow
        on: push
        jobs:
          test:
            runs-on: ubuntu-latest
            steps:
              - run: echo "test"
    ''')

    (workflows_dir / "test.yml").write_text(workflow_content)

    output_dir = tmp_path / "docs"

    # Act
    files = docs_workflow.generate_workflow_docs(workflows_dir, output_dir)

    # Assert
    assert len(files) == 1
    assert files[0].name == "test.md"
    content = files[0].read_text()
    assert "# Test Workflow" in content
    assert "## Jobs" in content


def test_format_function_docs_markdown():
    """Test function documentation formatting."""
    # Arrange
    func = docs_workflow.DocFunction(
        name="test_func",
        signature="test_func(arg1: str, arg2: int) -> bool",
        docstring="Test function.\n\nDetailed description.",
        args=[("arg1", "str", "First arg"), ("arg2", "int", "Second arg")],
        returns=("bool", "Result"),
        raises=[("ValueError", "If invalid")],
        examples=["test_func('a', 1)"],
    )

    # Act
    lines = docs_workflow._format_function_docs(func)
    markdown = "\n".join(lines)

    # Assert
    assert "### `test_func`" in markdown
    assert "**Arguments:**" in markdown
    assert "`arg1` (str): First arg" in markdown
    assert "**Returns:**" in markdown
    assert "**Raises:**" in markdown
    assert "`ValueError`: If invalid" in markdown
    assert "**Example:**" in markdown


def test_parse_docstring_section():
    """Test docstring section parsing."""
    # Arrange
    docstring = dedent('''
        Function description.

        Args:
            arg1: First argument
                with multiple lines.
            arg2: Second argument.

        Returns:
            Return value description.
    ''')

    # Act
    args = docs_workflow._parse_docstring_section(docstring, "Args:")
    returns = docs_workflow._parse_docstring_section(docstring, "Returns:")

    # Assert
    assert "arg1" in args
    assert "multiple lines" in args["arg1"]
    assert "arg2" in args
    assert "return" in returns
```

### Verification Steps

```bash
# 1. Verify test file exists
test -f tests/workflow_scripts/test_docs_workflow.py && echo "✅ Test file created"

# 2. Check Python syntax
python3 -m py_compile tests/workflow_scripts/test_docs_workflow.py && echo "✅ Valid Python"

# 3. Run tests
pytest tests/workflow_scripts/test_docs_workflow.py -v && echo "✅ All tests pass"

# 4. Check coverage
pytest tests/workflow_scripts/test_docs_workflow.py \
  --cov=docs_workflow \
  --cov-report=term-missing && echo "✅ Coverage report generated"
```

---

## Task 3.3: Create Documentation Publishing Workflow

**Status**: Not Started **Dependencies**: Task 3.1 (docs_workflow.py) **Estimated Time**: 2 hours
**Idempotent**: Yes

### Description

Create workflow to automatically generate and publish documentation to GitHub Pages with versioning
support.

### Implementation

Create file: `.github/workflows/reusable-docs.yml`

```yaml
# file: .github/workflows/reusable-docs.yml
# version: 1.0.0
# guid: a6b7c8d9-e0f1-2a3b-4c5d-6e7f8a9b0c1d

name: Reusable Documentation Generation

on:
  workflow_call:
    inputs:
      deploy:
        description: 'Deploy to GitHub Pages'
        type: boolean
        default: false
        required: false

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  generate-docs:
    name: Generate Documentation
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0 # Need full history for version info

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'
          cache: pip

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pyyaml pytest

      - name: Get current branch
        id: branch
        run: |
          branch=$(git rev-parse --abbrev-ref HEAD)
          echo "branch=${branch}" >> "$GITHUB_OUTPUT"

          # Determine if this is a versioned branch
          if [[ "$branch" =~ ^stable-1- ]]; then
            version=$(echo "$branch" | sed 's/^stable-1-//')
            echo "version=${version}" >> "$GITHUB_OUTPUT"
            echo "versioned=true" >> "$GITHUB_OUTPUT"
          else
            echo "version=latest" >> "$GITHUB_OUTPUT"
            echo "versioned=false" >> "$GITHUB_OUTPUT"
          fi

      - name: Generate API documentation
        run: |
          python .github/workflows/scripts/docs_workflow.py generate-api \
            --scripts-dir .github/workflows/scripts \
            --output docs-site/${{ steps.branch.outputs.version }}/api

      - name: Generate workflow documentation
        run: |
          python .github/workflows/scripts/docs_workflow.py generate-workflows \
            --workflows-dir .github/workflows \
            --output docs-site/${{ steps.branch.outputs.version }}/workflows

      - name: Create documentation index
        run: |
          cat > docs-site/${{ steps.branch.outputs.version }}/index.md << 'EOF'
          # Workflow System Documentation

          Version: ${{ steps.branch.outputs.version }}

          ## Contents

          - [API Reference](api/)
          - [Workflow Reference](workflows/)
          - [Implementation Guides](../implementation/)
          - [Operations Guides](../operations/)
          - [Reference Documentation](../reference/)

          ## Quick Links

          - [Getting Started](../implementation/ci-workflows.md)
          - [Migration Guide](../operations/migration-guide.md)
          - [Troubleshooting](../operations/troubleshooting.md)
          EOF

      - name: Create version selector
        run: |
          # Generate list of all versions
          versions=$(find docs-site -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort -V)

          cat > docs-site/versions.json << EOF
          {
            "current": "${{ steps.branch.outputs.version }}",
            "versions": $(echo "$versions" | jq -R . | jq -s .)
          }
          EOF

      - name: Setup GitHub Pages
        if: inputs.deploy
        uses: actions/configure-pages@v5

      - name: Upload documentation artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: docs-site

      - name: Deploy to GitHub Pages
        if: inputs.deploy
        uses: actions/deploy-pages@v4

  validation:
    name: Validate Documentation
    runs-on: ubuntu-latest
    needs: generate-docs

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Download documentation
        uses: actions/download-artifact@v4
        with:
          name: github-pages
          path: docs-site

      - name: Check for broken links
        uses: gaurav-nelson/github-action-markdown-link-check@v1
        with:
          use-quiet-mode: 'yes'
          folder-path: docs-site

      - name: Validate markdown formatting
        run: |
          npm install -g markdownlint-cli
          markdownlint docs-site/**/*.md
```

### Verification Steps

```bash
# 1. Verify workflow file exists
test -f .github/workflows/reusable-docs.yml && echo "✅ Workflow created"

# 2. Validate YAML syntax
yamllint .github/workflows/reusable-docs.yml && echo "✅ Valid YAML"

# 3. Check workflow with actionlint
actionlint .github/workflows/reusable-docs.yml && echo "✅ Workflow validated"

# 4. Test locally (without deploy)
act workflow_call --input deploy=false && echo "✅ Local test passed"
```

---

## Task 3.4: Create Documentation Workflow Caller

**Status**: Not Started **Dependencies**: Task 3.3 (reusable-docs.yml) **Estimated Time**: 1 hour
**Idempotent**: Yes

### Description

Create caller workflow with feature flag and manual trigger support.

### Implementation

Create file: `.github/workflows/docs.yml`

```yaml
# file: .github/workflows/docs.yml
# version: 1.0.0
# guid: b7c8d9e0-f1a2-3b4c-5d6e-7f8a9b0c1d2e

name: Documentation

on:
  push:
    branches:
      - main
      - 'stable-1-*'
    paths:
      - '.github/workflows/scripts/**/*.py'
      - '.github/workflows/*.yml'
      - 'docs/**'
  pull_request:
    paths:
      - '.github/workflows/scripts/**/*.py'
      - '.github/workflows/*.yml'
      - 'docs/**'
  workflow_dispatch:
    inputs:
      deploy:
        description: 'Deploy to GitHub Pages'
        type: boolean
        default: false
        required: false

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  check-feature-flag:
    name: Check Feature Flag
    runs-on: ubuntu-latest
    outputs:
      enabled: ${{ steps.check.outputs.enabled }}

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Check feature flag
        id: check
        run: |
          if [ -f .github/repository-config.yml ]; then
            enabled=$(python -c "
          import yaml
          with open('.github/repository-config.yml') as f:
              config = yaml.safe_load(f)
          print(str(config.get('workflows', {}).get('experimental', {}).get('use_new_docs', False)).lower())
          ")
            echo "enabled=${enabled}" >> "$GITHUB_OUTPUT"
          else
            echo "enabled=false" >> "$GITHUB_OUTPUT"
          fi

  new-docs:
    name: Generate Documentation (v2)
    needs: check-feature-flag
    if: needs.check-feature-flag.outputs.enabled == 'true'
    uses: ./.github/workflows/reusable-docs.yml
    with:
      deploy:
        ${{ github.event_name == 'push' && github.ref == 'refs/heads/main' ||
        github.event.inputs.deploy == 'true' }}

  legacy-docs:
    name: Documentation (legacy)
    needs: check-feature-flag
    if: needs.check-feature-flag.outputs.enabled != 'true'
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Use legacy documentation workflow
        run: echo "Using legacy documentation system"
```

### Verification Steps

```bash
# 1. Verify workflow file exists
test -f .github/workflows/docs.yml && echo "✅ Workflow created"

# 2. Validate YAML syntax
yamllint .github/workflows/docs.yml && echo "✅ Valid YAML"

# 3. Enable feature flag in repository-config.yml
yq eval '.workflows.experimental.use_new_docs = true' -i .github/repository-config.yml

# 4. Test workflow dispatch
gh workflow run docs.yml --ref main -f deploy=false
```

---

## Task 3.5: Create Documentation Site Configuration

**Status**: Not Started **Dependencies**: Task 3.3 (reusable-docs.yml) **Estimated Time**: 1 hour
**Idempotent**: Yes

### Description

Create configuration for GitHub Pages documentation site with version selector and navigation.

### Implementation

Create file: `docs-site/_config.yml`

```yaml
# file: docs-site/_config.yml
# version: 1.0.0
# guid: c8d9e0f1-a2b3-4c5d-6e7f-8a9b0c1d2e3f

# GitHub Pages Jekyll configuration
title: Workflow System Documentation
description: Comprehensive documentation for the v2 workflow system
theme: jekyll-theme-minimal

# URL configuration
baseurl: ''
url: 'https://jdfalk.github.io/ghcommon'

# Build settings
markdown: kramdown
highlighter: rouge

kramdown:
  input: GFM
  syntax_highlighter: rouge

# Collections
collections:
  api:
    output: true
    permalink: /api/:path/
  workflows:
    output: true
    permalink: /workflows/:path/
  implementation:
    output: true
    permalink: /implementation/:path/
  operations:
    output: true
    permalink: /operations/:path/
  reference:
    output: true
    permalink: /reference/:path/

# Navigation
navigation:
  - title: Home
    url: /
  - title: API Reference
    url: /api/
  - title: Workflow Reference
    url: /workflows/
  - title: Implementation Guides
    url: /implementation/
  - title: Operations Guides
    url: /operations/
  - title: Reference
    url: /reference/

# Version selector
versions:
  - latest
  - go-1.24
  - go-1.23
  - python-3.13
  - rust-stable

# Exclude from processing
exclude:
  - Gemfile
  - Gemfile.lock
  - node_modules
  - vendor
  - '*.py'
  - '*.sh'

# Include hidden files
include:
  - _config.yml
```

Create file: `docs-site/_layouts/default.html`

```html
<!-- file: docs-site/_layouts/default.html -->
<!-- version: 1.0.0 -->
<!-- guid: d9e0f1a2-b3c4-5d6e-7f8a-9b0c1d2e3f4a -->

<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{{ page.title }} - {{ site.title }}</title>
    <link rel="stylesheet" href="{{ '/assets/css/style.css' | relative_url }}" />
  </head>
  <body>
    <header>
      <div class="container">
        <h1>{{ site.title }}</h1>
        <p>{{ site.description }}</p>

        <!-- Version selector -->
        <div class="version-selector">
          <label for="version">Version:</label>
          <select id="version" onchange="switchVersion(this.value)">
            <option value="latest">Latest</option>
            <option value="go-1.24">Go 1.24</option>
            <option value="go-1.23">Go 1.23</option>
            <option value="python-3.13">Python 3.13</option>
            <option value="rust-stable">Rust Stable</option>
          </select>
        </div>
      </div>
    </header>

    <nav>
      <div class="container">
        <ul>
          {% for item in site.navigation %}
          <li><a href="{{ item.url | relative_url }}">{{ item.title }}</a></li>
          {% endfor %}
        </ul>
      </div>
    </nav>

    <main>
      <div class="container">{{ content }}</div>
    </main>

    <footer>
      <div class="container">
        <p>&copy; 2025 ghcommon - Workflow System Documentation</p>
        <p>Generated on {{ site.time | date: "%Y-%m-%d %H:%M" }}</p>
      </div>
    </footer>

    <script>
      // Version switcher
      function switchVersion(version) {
        const currentPath = window.location.pathname;
        const pathParts = currentPath.split('/');

        // Replace version in path (assumes /<version>/... structure)
        if (pathParts.length > 2) {
          pathParts[1] = version;
          window.location.pathname = pathParts.join('/');
        } else {
          window.location.pathname = `/${version}/`;
        }
      }

      // Set current version in selector
      document.addEventListener('DOMContentLoaded', () => {
        const pathParts = window.location.pathname.split('/');
        if (pathParts.length > 1) {
          const currentVersion = pathParts[1];
          const selector = document.getElementById('version');
          if (selector) {
            selector.value = currentVersion || 'latest';
          }
        }
      });

      // Search functionality
      function initSearch() {
        const searchInput = document.getElementById('search-input');
        if (!searchInput) return;

        searchInput.addEventListener('input', e => {
          const query = e.target.value.toLowerCase();
          // Implement search logic here
          console.log('Search query:', query);
        });
      }

      initSearch();
    </script>
  </body>
</html>
```

Create file: `docs-site/assets/css/style.css`

```css
/* file: docs-site/assets/css/style.css */
/* version: 1.0.0 */
/* guid: e0f1a2b3-c4d5-6e7f-8a9b-0c1d2e3f4a5b */

/* Global styles */
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
  line-height: 1.6;
  color: #333;
  background: #f5f5f5;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

/* Header */
header {
  background: #2c3e50;
  color: white;
  padding: 20px 0;
  border-bottom: 3px solid #3498db;
}

header h1 {
  font-size: 2em;
  margin-bottom: 5px;
}

header p {
  opacity: 0.9;
}

/* Version selector */
.version-selector {
  margin-top: 15px;
}

.version-selector label {
  margin-right: 10px;
  font-weight: bold;
}

.version-selector select {
  padding: 5px 10px;
  border-radius: 4px;
  border: 1px solid #ddd;
  background: white;
  font-size: 14px;
}

/* Navigation */
nav {
  background: white;
  border-bottom: 1px solid #ddd;
  padding: 15px 0;
}

nav ul {
  list-style: none;
  display: flex;
  gap: 20px;
}

nav a {
  color: #2c3e50;
  text-decoration: none;
  font-weight: 500;
  padding: 8px 12px;
  border-radius: 4px;
  transition: background 0.2s;
}

nav a:hover {
  background: #ecf0f1;
}

/* Main content */
main {
  background: white;
  margin: 20px 0;
  padding: 40px 0;
  min-height: calc(100vh - 400px);
}

/* Typography */
h1,
h2,
h3,
h4,
h5,
h6 {
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.25;
}

h1 {
  font-size: 2em;
  border-bottom: 2px solid #eee;
  padding-bottom: 10px;
}

h2 {
  font-size: 1.5em;
  border-bottom: 1px solid #eee;
  padding-bottom: 8px;
}

h3 {
  font-size: 1.25em;
}

p {
  margin-bottom: 16px;
}

/* Code blocks */
code {
  background: #f6f8fa;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
}

pre {
  background: #f6f8fa;
  padding: 16px;
  border-radius: 6px;
  overflow-x: auto;
  margin-bottom: 16px;
}

pre code {
  background: none;
  padding: 0;
}

/* Tables */
table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 16px;
}

th,
td {
  padding: 12px;
  text-align: left;
  border: 1px solid #ddd;
}

th {
  background: #f6f8fa;
  font-weight: 600;
}

/* Links */
a {
  color: #3498db;
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}

/* Footer */
footer {
  background: #2c3e50;
  color: white;
  padding: 20px 0;
  text-align: center;
  opacity: 0.9;
}

/* Responsive */
@media (max-width: 768px) {
  nav ul {
    flex-direction: column;
    gap: 10px;
  }

  .container {
    padding: 0 15px;
  }

  h1 {
    font-size: 1.5em;
  }
}
```

### Verification Steps

```bash
# 1. Verify all site files exist
test -f docs-site/_config.yml && \
test -f docs-site/_layouts/default.html && \
test -f docs-site/assets/css/style.css && \
echo "✅ Site files created"

# 2. Test Jekyll build locally
cd docs-site && jekyll build && echo "✅ Jekyll build successful"

# 3. Test site locally
cd docs-site && jekyll serve && echo "✅ Site running at http://localhost:4000"

# 4. Validate HTML
html5validator docs-site/_site && echo "✅ HTML validation passed"
```

---

## Phase 3 Completion Checklist

- [ ] All tasks completed (3.1-3.5)
- [ ] `docs_workflow.py` created with comprehensive doc generation
- [ ] Unit tests pass with 100% coverage
- [ ] Documentation publishing workflow operational
- [ ] GitHub Pages site configured with versioning
- [ ] Feature flag `use_new_docs` functional
- [ ] No Windows references in any files
- [ ] All code follows Google Python Style Guide
- [ ] Markdown files validated
- [ ] Links checked for broken references
- [ ] Version selector working in documentation site

---

**Phase 3 Complete!** This phase establishes automated documentation generation with versioning
support and GitHub Pages publishing.
