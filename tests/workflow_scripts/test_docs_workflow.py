#!/usr/bin/env python3
# file: tests/workflow_scripts/test_docs_workflow.py
# version: 1.0.0
# guid: 2f3a4b5c-6d7e-8f90-a1b2-c3d4e5f60718

"""Tests for docs_workflow helper module."""

from __future__ import annotations

import textwrap
from pathlib import Path

import docs_workflow
import pytest


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")


def test_generate_api_docs(tmp_path: Path) -> None:
    """generate_api_docs creates Markdown for Python helpers."""
    module_path = tmp_path / "scripts" / "sample.py"
    _write_file(
        module_path,
        """
        \"\"\"Sample module doc.\"\"\"

        def hello(name: str) -> str:
            \"\"\"Say hello.\"\"\"
            return f"hello {name}"


        class Greeter:
            \"\"\"Greets people.\"\"\"

            def greet(self, name: str) -> str:
                \"\"\"Return greeting.\"\"\"
                return f"hello {name}"
        """,
    )

    output_dir = tmp_path / "docs"
    docs_workflow.generate_api_docs([str(module_path.parent)], output_dir)

    doc_file = output_dir / "sample.md"
    content = doc_file.read_text(encoding="utf-8")
    assert "# Module `sample`" in content
    assert "Sample module doc." in content
    assert "### `hello(name: str)`" in content
    assert "Greets people." in content


def test_generate_workflow_docs(tmp_path: Path) -> None:
    """generate_workflow_docs summarizes GitHub workflows."""
    wf_path = tmp_path / ".github" / "workflows" / "ci.yml"
    _write_file(
        wf_path,
        """
        name: CI
        on:
          push: {}
        jobs:
          test:
            runs-on: ubuntu-latest
        """,
    )

    output = tmp_path / "docs" / "workflows.md"
    docs_workflow.generate_workflow_docs(str(wf_path.parent), output)

    content = output.read_text(encoding="utf-8")
    assert "# Workflow Catalog" in content
    assert "## CI" in content
    assert "runs-on `ubuntu-latest`" in content


def test_build_documentation_creates_versioned_site(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """build_documentation assembles API docs, workflow docs, and search index."""
    monkeypatch.setenv("DOC_VERSION", "v1")
    source_dir = tmp_path / "scripts"
    workflow_dir = tmp_path / ".github" / "workflows"
    _write_file(
        source_dir / "mod.py",
        """
        \"\"\"Doc\"\"\"
        def foo(): pass
        """,
    )
    _write_file(
        workflow_dir / "ci.yml",
        """
        name: CI
        on: { push: {} }
        jobs: { build: { runs-on: ubuntu-latest } }
        """,
    )

    result = docs_workflow.build_documentation(
        [str(source_dir)],
        str(workflow_dir),
        tmp_path / "site",
    )

    assert result["version"] == "v1"
    search_index = Path(result["search_index"]).read_text(encoding="utf-8")
    assert "Workflows" in search_index
    versions = (tmp_path / "site" / "versions.json").read_text(encoding="utf-8")
    assert '"v1"' in versions
