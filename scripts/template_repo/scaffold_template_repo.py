#!/usr/bin/env python3
# file: scripts/template_repo/scaffold_template_repo.py
# version: 1.7.0
# guid: 7f2d3a2e-4b5c-8d9e-0f1a-2b3c4d5e6f70

"""Scaffold a minimal, public-safe template repository to a target directory.

Design goals:
- No secrets written to disk. No tokens, passwords, or PATs.
- No git submodules or nested repositories are created.
- No network calls. Pure local file system operations.
- Idempotent: safe to re-run; won’t overwrite existing files unless --force is used.

What it creates:
- Core docs: README.md, LICENSE, CODE_OF_CONDUCT.md, CONTRIBUTING.md, SECURITY.md, AGENTS.md
- .github/ files: workflows (ci), issue templates, PR template, CODEOWNERS, copilot-instructions.md,
  instructions/general-coding.instructions.md
- Root linters/config: .editorconfig, .prettierrc.yaml, .eslintrc.yml, .markdownlint.yaml, .yamllint.yml,
  .golangci.yml, .flake8
- Basic .gitignore

By default, it does NOT run any git commands. See push_with_gh.py for optional publishing.
"""

from __future__ import annotations

import argparse
import dataclasses
import os
import sys
from pathlib import Path

SUPPORTED_LICENSES: dict[str, str] = {
    "MIT": """MIT License

Copyright (c) {year} {owner}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to do so, subject to the
following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
""",
    "Apache-2.0": """Apache License
Version 2.0, January 2004
http://www.apache.org/licenses/

TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

Copyright (c) {year} {owner}

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
""",
}


README_TEMPLATE = """<!-- file: README.md -->
<!-- version: 1.0.0 -->
<!-- guid: 0f0e0d0c-0b0a-0908-0706-050403020100 -->

# {name}

{description}

## Status

This repository was created from an automated template scaffold. It intentionally
contains no secrets, tokens, or passwords. See `.github/` for CI and templates.

## License

This project is licensed under the {license} license. See [LICENSE](LICENSE).
"""

CODE_OF_CONDUCT = """<!-- file: CODE_OF_CONDUCT.md -->
<!-- version: 1.0.0 -->
<!-- guid: 11112222-3333-4444-5555-666677778888 -->

# Code of Conduct

This project follows the Contributor Covenant Code of Conduct. Be respectful and
supportive. For issues, contact the maintainers via GitHub issues.
"""

CONTRIBUTING = """<!-- file: CONTRIBUTING.md -->
<!-- version: 1.0.0 -->
<!-- guid: 9999aaaa-bbbb-4ccc-8ddd-eeeeffff0000 -->

# Contributing

We welcome contributions! Please:

- Open an issue describing the change
- Follow conventional commit messages
- Add tests when applicable
- Avoid committing secrets or credentials
"""

SECURITY = """<!-- file: SECURITY.md -->
<!-- version: 1.0.0 -->
<!-- guid: 12345678-90ab-cdef-1234-567890abcdef -->

# Security Policy

Please report security issues privately via the repository's security advisory
workflow on GitHub. Do not open public issues for vulnerabilities.
"""

GITIGNORE = """# file: .gitignore
# version: 1.0.0
# guid: 0a1b2c3d-4e5f-6071-8293-a4b5c6d7e8f9

# General
.DS_Store
*.log
logs/
dist/
build/
venv/
.venv/
__pycache__/
*.pyc
node_modules/
coverage*
*.out
"""


def render_ci_yaml(include_go: bool, include_python: bool) -> str:
    """Build CI workflow content dynamically based on selected overlays.
    Always includes Super Linter job; conditionally adds Go/Python test jobs.
    """
    header = """# file: .github/workflows/ci.yml
# version: 1.1.1
# guid: bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb
"""

    base = """name: CI

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Super Linter
        uses: super-linter/super-linter@v7.1.0
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          DEFAULT_BRANCH: ${{ github.event.repository.default_branch }}
          VALIDATE_ALL_CODEBASE: true
          JAVASCRIPT_ES_CONFIG_FILE: .eslintrc.yml
          MARKDOWN_CONFIG_FILE: .markdownlint.yaml
          YAML_CONFIG_FILE: .yamllint.yml
          GOLANGCI_LINT_CONFIG_FILE: .golangci.yml
          PYTHON_FLAKE8_CONFIG_FILE: .flake8
"""

    blocks: list[str] = [base]

    if include_go:
        go_block = """  go:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Go
        uses: actions/setup-go@v5
        with:
          go-version: stable
      - name: Build
        run: |
          go version
          go build ./...
      - name: Test
        run: go test ./... -v
"""
        blocks.append(go_block)

    if include_python:
        py_block = """  python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.x'
      - name: Install test deps
        run: |
          if [ -f requirements-dev.txt ]; then pip install -r requirements-dev.txt; else pip install pytest; fi
      - name: Run tests
        run: pytest -q || python -m pytest -q
"""
        blocks.append(py_block)

    return header + "".join(blocks)


ISSUE_TEMPLATE_BUG = """---
name: Bug report
about: Create a report to help us improve
title: "[BUG]"
labels: bug
assignees: ''
---

Describe the bug and steps to reproduce.
"""

ISSUE_TEMPLATE_FEATURE = """---
name: Feature request
about: Suggest an idea for this project
title: "[FEAT]"
labels: enhancement
assignees: ''
---

Describe the feature and rationale.
"""

PULL_REQUEST_TEMPLATE = """## Summary

Briefly describe the change and motivation.

## Testing

How did you test this change?

## Related Issues

Link to issues if applicable.
"""

CODEOWNERS = """* @OWNER_USERNAME
"""

# -------------------------
# Root-level linter configs
# -------------------------

EDITORCONFIG = """# file: .editorconfig
# version: 1.0.0
# guid: 11111111-1111-4111-8111-111111111111

root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
indent_style = space
indent_size = 2
trim_trailing_whitespace = true

[*.go]
indent_size = 4

[Makefile]
indent_style = tab
"""

PRETTIERRC_YAML = """# file: .prettierrc.yaml
# version: 1.0.0
# guid: 22222222-2222-4222-8222-222222222222

printWidth: 100
tabWidth: 2
useTabs: false
semi: true
singleQuote: false
trailingComma: es5
bracketSpacing: true
arrowParens: avoid
proseWrap: always
"""

ESLINTRC_YML = """# file: .eslintrc.yml
# version: 1.0.0
# guid: 33333333-3333-4333-8333-333333333333

env:
    browser: true
    es2021: true
    node: true
extends:
    - eslint:recommended
parserOptions:
    ecmaVersion: latest
    sourceType: module
rules:
    no-console: off
    no-unused-vars:
        - warn
        - argsIgnorePattern: ^_
"""

MARKDOWNLINT_YAML = """# file: .markdownlint.yaml
# version: 1.0.0
# guid: 44444444-4444-4444-8444-444444444444

default: true
MD013: false # line length
MD029: style
MD025: false # multiple H1 allowed in some docs
"""

YAMLLINT_YAML = """# file: .yamllint.yml
# version: 1.0.0
# guid: 55555555-5555-4555-8555-555555555555

extends: default
rules:
    line-length:
        max: 120
        level: warning
    trailing-spaces: enable
    truthy:
        check-keys: false
"""

GOLANGCI_YML = """# file: .golangci.yml
# version: 1.0.0
# guid: 66666666-6666-4666-8666-666666666666

run:
    timeout: 3m

linters:
    enable:
        - govet
        - staticcheck
        - gosimple
        - ineffassign
        - errcheck
        - typecheck
    disable:
        - depguard

issues:
    exclude-use-default: false
"""

FLAKE8 = """# file: .flake8
# version: 1.0.0
# guid: 77777777-7777-4777-8777-777777777777

[flake8]
max-line-length = 100
extend-ignore = E203,W503
"""

# -------------------------
# AI/Copilot instruction files
# -------------------------

COPILOT_INSTRUCTIONS_MD = """<!-- file: .github/copilot-instructions.md -->
<!-- version: 1.0.0 -->
<!-- guid: 4d5e6f7a-8b9c-0d1e-2f3a-4b5c6d7e8f9a -->

# Copilot/AI Agent Coding Instructions System

This repository uses a centralized, modular system for Copilot/AI agent coding,
documentation, and workflow instructions.

## System Overview

- General rules: `.github/instructions/general-coding.instructions.md`
- Language/task-specific: place additional files in `.github/instructions/`
- Prompts: `.github/prompts/` (optional)

## For Contributors

- Edit or add rules in `.github/instructions/`.
- Prefer VS Code tasks when available.
- Keep required headers (file path, version, guid) in all instruction files.
"""

GENERAL_CODING_INSTRUCTIONS_MD = """<!-- file: .github/instructions/general-coding.instructions.md -->
<!-- version: 1.0.0 -->
<!-- guid: 1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d -->

<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
---
applyTo: "**"
description: |
    General coding, documentation, and workflow rules for all Copilot/AI agents and VS Code Copilot customization. These rules apply to all files and languages unless overridden by a more specific instructions file.
---
<!-- markdownlint-enable -->
<!-- prettier-ignore-end -->

# General Coding Instructions

- Follow conventional commit message standards and pull request guidelines.
- Document code, classes, functions, and tests extensively.
- Use Arrange-Act-Assert pattern for tests.
- Do not duplicate rules; reference this file from specific instructions.

## Required File Header (File Identification)

All source, script, and documentation files MUST begin with a standard header
containing file path, version, and GUID as comments.

## Version Update Requirements

- Patch: bug fixes/typos
- Minor: new features/significant content
- Major: breaking changes/overhauls
"""

AGENTS_POINTER = """<!-- file: AGENTS.md -->
<!-- version: 1.0.0 -->
<!-- guid: 2e7c1a4b-5d3f-4b8c-9e1f-7a6b2c3d4e5f -->

# AGENTS.md

> NOTE: This is a pointer. All detailed Copilot, agent, and workflow instructions are in the `.github/` directory.

## Canonical Source for Agent Instructions

- General rules: `.github/instructions/`
- System documentation: `.github/copilot-instructions.md`
"""

# -------------------------
# Repo policy / docs
# -------------------------

COMMIT_MESSAGES_MD = """<!-- file: .github/commit-messages.md -->
<!-- version: 1.0.0 -->
<!-- guid: 88888888-8888-4888-8888-888888888888 -->

# Conventional Commit Message Guidelines

- Use `type(scope): description` format
- Keep header under 72 characters, present tense
- Group file changes in the body with brief descriptions
- Include issue numbers only when working on specific issues

Common types: feat, fix, docs, style, refactor, test, chore, perf, ci, build, revert
"""

PULL_REQUEST_DESCRIPTIONS_MD = """<!-- file: .github/pull-request-descriptions.md -->
<!-- version: 1.0.0 -->
<!-- guid: 99999999-9999-4999-8999-999999999999 -->

# Pull Request Description Guidelines

## Template

## Summary

## Issues Addressed

## Testing

## Breaking Changes

## Additional Notes

See examples and best practices in this file.
"""

TEST_GENERATION_MD = """<!-- file: .github/test-generation.md -->
<!-- version: 1.0.0 -->
<!-- guid: aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa -->

# Test Generation Guidelines

- Use Arrange-Act-Assert
- Clear naming: test[UnitOfWork_StateUnderTest_ExpectedBehavior]
- Focus on behavior, not implementation
- Cover happy path and edge cases
- Keep tests deterministic and independent
"""


@dataclasses.dataclass
class Options:
    name: str
    owner: str
    description: str
    license: str
    year: str
    target_dir: Path
    dry_run: bool
    force: bool
    with_go: bool
    with_python: bool
    with_dependabot: bool
    with_releases: bool
    with_docker: bool
    docker_base_image: str
    docker_apt_packages: tuple[str, ...]
    docker_pip_packages: tuple[str, ...]
    docker_go_version: str
    docker_python_version: str
    with_changelog: bool
    with_todo: bool
    with_claudemd: bool
    with_reusable_workflows: bool
    reusable_workflows_ref: str


def render_license(license_id: str, owner: str, year: str) -> str:
    template = SUPPORTED_LICENSES.get(license_id)
    if not template:
        raise ValueError(
            f"Unsupported license '{license_id}'. Supported: {', '.join(SUPPORTED_LICENSES)}"
        )
    return template.format(owner=owner, year=year)


def plan_files(opts: Options) -> list[tuple[Path, str]]:
    root = opts.target_dir
    files: list[tuple[Path, str]] = []

    files.append(
        (
            root / "README.md",
            README_TEMPLATE.format(
                name=opts.name,
                description=opts.description,
                license=opts.license,
            ),
        )
    )
    # Agent pointer at repo root
    files.append((root / "AGENTS.md", AGENTS_POINTER))
    files.append((root / "LICENSE", render_license(opts.license, opts.owner, opts.year)))
    files.append((root / "CODE_OF_CONDUCT.md", CODE_OF_CONDUCT))
    files.append((root / "CONTRIBUTING.md", CONTRIBUTING))
    files.append((root / "SECURITY.md", SECURITY))
    files.append((root / ".gitignore", GITIGNORE))

    # Project hygiene files modeled on the rest of jdfalk's active repos.
    if opts.with_changelog:
        files.append((root / "CHANGELOG.md", render_changelog(opts)))
    if opts.with_todo:
        files.append((root / "TODO.md", render_todo(opts)))
    if opts.with_claudemd:
        files.append((root / "CLAUDE.md", render_claudemd(opts)))

    # Root linters/configs
    files.append((root / ".editorconfig", EDITORCONFIG))
    files.append((root / ".prettierrc.yaml", PRETTIERRC_YAML))
    files.append((root / ".eslintrc.yml", ESLINTRC_YML))
    files.append((root / ".markdownlint.yaml", MARKDOWNLINT_YAML))
    files.append((root / ".yamllint.yml", YAMLLINT_YAML))
    files.append((root / ".golangci.yml", GOLANGCI_YML))
    files.append((root / ".flake8", FLAKE8))

    # .github structure
    files.append(
        (
            root / ".github" / "CODEOWNERS",
            CODEOWNERS.replace("OWNER_USERNAME", opts.owner),
        )
    )
    files.append((root / ".github" / "pull_request_template.md", PULL_REQUEST_TEMPLATE))
    files.append(
        (
            root / ".github" / "ISSUE_TEMPLATE" / "bug_report.md",
            ISSUE_TEMPLATE_BUG,
        )
    )
    files.append(
        (
            root / ".github" / "ISSUE_TEMPLATE" / "feature_request.md",
            ISSUE_TEMPLATE_FEATURE,
        )
    )
    # Either the standalone CI yaml or a thin caller of ghcommon's reusable-ci.
    # When --with-reusable-workflows is set, the standalone copy is replaced
    # with a thin caller that delegates to ghcommon — the repo's own
    # workflow-config.yaml carries the per-repo knobs.
    if opts.with_reusable_workflows:
        files.append((root / ".github" / "workflows" / "ci.yml", render_reusable_ci(opts)))
        files.append(
            (root / ".github" / "workflows" / "security.yml", render_reusable_security(opts))
        )
        files.append((root / ".github" / "workflow-config.yaml", render_workflow_config(opts)))
    else:
        files.append(
            (
                root / ".github" / "workflows" / "ci.yml",
                render_ci_yaml(include_go=opts.with_go, include_python=opts.with_python),
            )
        )
    files.append((root / ".github" / "commit-messages.md", COMMIT_MESSAGES_MD))
    files.append(
        (
            root / ".github" / "pull-request-descriptions.md",
            PULL_REQUEST_DESCRIPTIONS_MD,
        )
    )
    files.append((root / ".github" / "test-generation.md", TEST_GENERATION_MD))

    # AI instructions scaffolding
    files.append((root / ".github" / "copilot-instructions.md", COPILOT_INSTRUCTIONS_MD))
    files.append(
        (
            root / ".github" / "instructions" / "general-coding.instructions.md",
            GENERAL_CODING_INSTRUCTIONS_MD,
        )
    )

    # Language overlays
    if opts.with_go:
        files.extend(plan_go_overlay(opts))

    if opts.with_python:
        files.extend(plan_python_overlay(opts))

    # Optional Dependabot
    if opts.with_dependabot:
        files.append((root / ".github" / "dependabot.yml", render_dependabot_yaml(opts)))

    # Optional release workflows
    if opts.with_releases:
        files.extend(plan_release_workflows(opts))

    # Optional Docker overlay (Dockerfile + GHCR build/push workflow)
    if opts.with_docker:
        files.extend(plan_docker_overlay(opts))

    return files


def module_path(opts: Options) -> str:
    # Best-effort module path for templates
    return f"github.com/{opts.owner}/{opts.name}"


def plan_go_overlay(opts: Options) -> list[tuple[Path, str]]:
    root = opts.target_dir
    mod = f"// file: go.mod\n// version: 1.0.0\n// guid: c1e1c1e1-1111-4111-8111-c1e1c1e1c1e1\n\nmodule {module_path(opts)}\n\ngo 1.22\n"

    hello_go = """// file: internal/hello/hello.go
// version: 1.0.0
// guid: d2e2d2e2-2222-4222-8222-d2e2d2e2d2e2

package hello

// Greet returns a friendly greeting.
func Greet(name string) string {
    if name == "" {
        return "Hello, world!"
    }
    return "Hello, " + name + "!"
}
"""

    hello_test = """// file: internal/hello/hello_test.go
// version: 1.0.0
// guid: e3e3e3e3-3333-4333-8333-e3e3e3e3e3e3

package hello

import "testing"

func TestGreet(t *testing.T) {
    if got := Greet("Go"); got != "Hello, Go!" {
        t.Fatalf("unexpected greeting: %s", got)
    }
    if got := Greet(""); got != "Hello, world!" {
        t.Fatalf("unexpected default greeting: %s", got)
    }
}
"""

    return [
        (root / "go.mod", mod),
        (root / "internal" / "hello" / "hello.go", hello_go),
        (root / "internal" / "hello" / "hello_test.go", hello_test),
    ]


def plan_python_overlay(opts: Options) -> list[tuple[Path, str]]:
    root = opts.target_dir
    req = """# file: requirements-dev.txt
# version: 1.0.0
# guid: f4f4f4f4-4444-4444-8444-f4f4f4f4f4f4

pytest>=7,<9
"""

    sample_py = """#!/usr/bin/env python3
# file: pkg/sample.py
# version: 1.0.0
# guid: a5a5a5a5-5555-4555-8555-a5a5a5a5a5a5

def add(a: int, b: int) -> int:
    '''Add two integers and return the result.'''
    return a + b
"""

    test_py = """# file: tests/test_sample.py
# version: 1.0.0
# guid: b6b6b6b6-6666-4666-8666-b6b6b6b6b6b6

import os
import sys

# Ensure the repository root is on the path for simple imports
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from pkg.sample import add  # noqa: PGH003


def test_add():
    assert add(2, 3) == 5
"""

    return [
        (root / "requirements-dev.txt", req),
        (root / "pkg" / "sample.py", sample_py),
        (root / "tests" / "test_sample.py", test_py),
    ]


def render_dependabot_yaml(opts: Options) -> str:
    header = """# file: .github/dependabot.yml
# version: 1.0.0
# guid: abcdabcd-abcd-4abc-8abc-abcdabcdabcd
"""
    lines = [
        "version: 2",
        "updates:",
        '  - package-ecosystem: "github-actions"',
        '    directory: "/"',
        "    schedule:",
        '      interval: "weekly"',
    ]
    if opts.with_go:
        lines += [
            '  - package-ecosystem: "gomod"',
            '    directory: "/"',
            "    schedule:",
            '      interval: "weekly"',
        ]
    if opts.with_python:
        lines += [
            '  - package-ecosystem: "pip"',
            '    directory: "/"',
            "    schedule:",
            '      interval: "weekly"',
        ]
    return header + "\n".join(lines) + "\n"


def plan_release_workflows(opts: Options) -> list[tuple[Path, str]]:
    root = opts.target_dir
    out: list[tuple[Path, str]] = []

    if opts.with_go:
        go_rel = """# file: .github/workflows/release-go.yml
# version: 1.0.0
# guid: c7c7c7c7-7777-4777-8777-c7c7c7c7c7c7

name: Release (Go)

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: stable
      - name: Build binaries
        run: |
          mkdir -p dist
          GOOS=linux GOARCH=amd64   go build -o dist/app-linux-amd64 ./...
          GOOS=linux GOARCH=arm64   go build -o dist/app-linux-arm64 ./...
          GOOS=darwin GOARCH=amd64  go build -o dist/app-darwin-amd64 ./...
          GOOS=darwin GOARCH=arm64  go build -o dist/app-darwin-arm64 ./...
          GOOS=windows GOARCH=amd64 go build -o dist/app-windows-amd64.exe ./...
      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          files: |
            dist/*
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
"""
        out.append((root / ".github" / "workflows" / "release-go.yml", go_rel))

    if opts.with_python:
        py_rel = """# file: .github/workflows/release-python.yml
# version: 1.0.0
# guid: d8d8d8d8-8888-4888-8888-d8d8d8d8d8d8

name: Release (Python)

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.x'
      - name: Build wheel
        run: |
          python -m pip install --upgrade pip build twine
          python -m build
      - name: Publish to PyPI (if token present)
        if: ${{ secrets.PYPI_TOKEN != '' }}
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
        run: |
          python -m twine upload dist/*
"""
        out.append((root / ".github" / "workflows" / "release-python.yml", py_rel))

    readme = """# file: .github/workflows/README.md
# version: 1.0.0
# guid: e9e9e9e9-9999-4999-8999-e9e9e9e9e9e9

# Release Workflows

This template includes optional release workflows that build artifacts for Go
and/or Python when you push a tag like `v1.2.3`.

- Go release uses GitHub Releases with built binaries (no secrets required)
- Python release publishes to PyPI only if `PYPI_TOKEN` repository secret exists

Disable or delete workflows you don't need.
"""
    out.append((root / ".github" / "workflows" / "README.md", readme))

    return out


def render_changelog(opts: Options) -> str:
    return f"""<!-- file: CHANGELOG.md -->
<!-- version: 0.1.0 -->
<!-- guid: c4a4ce10-0000-4000-8000-000000000001 -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial scaffold of {opts.name}.
"""


def render_todo(opts: Options) -> str:
    return f"""<!-- file: TODO.md -->
<!-- version: 0.1.0 -->
<!-- guid: 1010d010-0000-4000-8000-000000000001 -->

# {opts.name} — TODO

Canonical index of outstanding work. Each item links to a spec, plan, or issue
where the details live; this file exists so the whole backlog is scannable on
one page.

## Active

- [ ] Initial setup tasks (replace with real work).

## Backlog

_(empty)_

## Recently completed

_(empty)_
"""


def render_claudemd(opts: Options) -> str:
    return f"""<!-- file: CLAUDE.md -->
<!-- version: 0.1.0 -->
<!-- guid: c1a4dec0-0000-4000-8000-000000000001 -->

# CLAUDE.md

Entry point for AI agent instructions in **{opts.name}**.

All detailed agent instructions live in `.github/`. This file is a pointer.

## Quick links

- **Coding standards & architecture:** [.github/copilot-instructions.md](.github/copilot-instructions.md)
- **Per-language conventions:** [.github/instructions/](.github/instructions/)
- **Issue / PR templates:** [.github/](./.github/)
- **Full file index:** [AGENTS.md](AGENTS.md)

## Critical rules

1. **Git:** Conventional commits mandatory. Pin all action references to SHAs.
2. **File headers:** All files need versioned headers (file / version / guid).
   Bump the version on every change.
3. **Workflows:** Edit reusable-workflow callers, not the reusables themselves
   (those live in `jdfalk/ghcommon`).
"""


def render_workflow_config(opts: Options) -> str:
    return """# file: .github/workflow-config.yaml
# version: 1.0.0
# guid: c0fc0f1f-0000-4000-8000-000000000001
#
# Per-repo knobs for the reusable workflows in jdfalk/ghcommon. Toggle features
# off here when a repo doesn't need them rather than forking the reusables.

build:
  go_versions: ['1.25']
  python_versions: ['3.13']
  node_versions: ['22']
  platforms: ['linux/amd64', 'linux/arm64']
  enable_protobuf: false
  enable_docker: false
  enable_cross_compile: false
  enable_coverage: false
  enable_security_scan: true
"""


def render_reusable_ci(opts: Options) -> str:
    # Default to @main with a TODO; ghcommon's update-action-docker-ref-action
    # rewrites this to a pinned SHA on the next CI run.
    ref = opts.reusable_workflows_ref or "main"
    return f"""# file: .github/workflows/ci.yml
# version: 1.0.0
# guid: c0c4ce11-0000-4000-8000-000000000001
#
# Thin caller of jdfalk/ghcommon/.github/workflows/reusable-ci.yml.
# Repo-specific knobs live in .github/workflow-config.yaml. The action ref
# below SHOULD be a pinned SHA in production — `@{ref}` is the scaffold
# default; the next CI run's pin-actions-to-hashes step will rewrite it.

name: Continuous Integration

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch: {{}}

concurrency:
  group: ${{{{ github.workflow }}}}-${{{{ github.ref }}}}
  cancel-in-progress: true

permissions:
  contents: write
  actions: write
  checks: write
  packages: write
  id-token: write
  attestations: write

jobs:
  ci:
    name: Run CI
    uses: jdfalk/ghcommon/.github/workflows/reusable-ci.yml@{ref}
    secrets: inherit
"""


def render_reusable_security(opts: Options) -> str:
    ref = opts.reusable_workflows_ref or "main"
    return f"""# file: .github/workflows/security.yml
# version: 1.0.0
# guid: c0c4ce12-0000-4000-8000-000000000001

name: Security

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'  # Mondays 06:00 UTC
  workflow_dispatch: {{}}

permissions:
  contents: read
  security-events: write
  actions: read

jobs:
  security:
    uses: jdfalk/ghcommon/.github/workflows/reusable-security.yml@{ref}
    secrets: inherit
"""


def plan_docker_overlay(opts: Options) -> list[tuple[Path, str]]:
    """Generate a Dockerfile + GHCR build/push workflow.

    The Dockerfile extends a base that already mirrors a GitHub Actions
    Ubuntu runner (gh CLI, git, curl, build-essentials, locales) and layers
    extra deps on top. Default base is the catthehacker `act` image, which
    is the closest publicly-available "GHA runner" container — switch via
    --docker-base-image when the user has a custom base.

    The build workflow targets ghcr.io/<owner>/<name>, multi-arch
    (linux/amd64, linux/arm64), with attestation + SBOM, on push to main
    (tag :sha + :latest), on git tag v* (tag :version + :latest), and a
    weekly cron rebuild to pick up upstream patches without a code change.
    """
    root = opts.target_dir
    out: list[tuple[Path, str]] = []

    # Optional Go install layer (skip if go_version is empty).
    go_layer = ""
    if opts.docker_go_version:
        go_layer = f"""
# --- Go toolchain (pinned) ---
ENV GO_VERSION={opts.docker_go_version}
RUN set -eux; \\
    arch="$(dpkg --print-architecture)"; \\
    case "$arch" in \\
      amd64) goarch=amd64 ;; \\
      arm64) goarch=arm64 ;; \\
      *) echo "unsupported arch: $arch" >&2; exit 1 ;; \\
    esac; \\
    curl -fsSL "https://go.dev/dl/go${{GO_VERSION}}.linux-${{goarch}}.tar.gz" -o /tmp/go.tgz; \\
    tar -C /usr/local -xzf /tmp/go.tgz; \\
    rm /tmp/go.tgz
ENV PATH=/usr/local/go/bin:/root/go/bin:$PATH \\
    GOPATH=/root/go
"""

    # Optional apt layer.
    apt_layer = ""
    if opts.docker_apt_packages:
        pkgs = " ".join(sorted(set(opts.docker_apt_packages)))
        apt_layer = f"""
# --- Extra apt packages ---
RUN apt-get update \\
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends {pkgs} \\
 && rm -rf /var/lib/apt/lists/*
"""

    # Optional Python layer via uv.
    # uv installs as a single static binary, brings in a modern interpreter
    # under /opt/python, creates a system venv at /opt/venv, and installs
    # packages into it. This sidesteps PEP 668 / --break-system-packages
    # entirely and gives every script in the image consistent access to a
    # known Python version + deps. Only emitted when --docker-pip is set.
    pip_layer = ""
    if opts.docker_pip_packages:
        spec = " \\\n        ".join(f'"{p}"' for p in opts.docker_pip_packages)
        py_ver = opts.docker_python_version or "3.13"
        pip_layer = f"""
# --- Python via uv (single static binary; bundles its own Python builds) ---
ARG PYTHON_VERSION={py_ver}
ENV UV_INSTALL_DIR=/usr/local/bin \\
    UV_PYTHON_INSTALL_DIR=/opt/python \\
    VIRTUAL_ENV=/opt/venv \\
    PATH=/opt/venv/bin:$PATH
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \\
 && uv python install ${{PYTHON_VERSION}} \\
 && uv venv --python ${{PYTHON_VERSION}} ${{VIRTUAL_ENV}} \\
 && uv pip install --python ${{VIRTUAL_ENV}}/bin/python \\
        {spec}
"""

    dockerfile = f"""# file: Dockerfile
# version: 1.0.0
# guid: f0c1ker0-0000-4000-8000-000000000001
#
# Extends a GitHub Actions-style Ubuntu base with the project's runtime
# dependencies. Pinning the base by SHA in production is left to the caller
# (set via the IMAGE_BASE build-arg in your CI). The named tag below is the
# floor; CI should override with a digest for reproducibility.

ARG IMAGE_BASE={opts.docker_base_image}
FROM ${{IMAGE_BASE}}

# Provenance labels — picked up by docker/metadata-action and by `gh
# attestation verify` when consumers want to confirm where the image came
# from. Override at build time with --label or via metadata-action.
LABEL org.opencontainers.image.source="https://github.com/{opts.owner}/{opts.name}" \\
      org.opencontainers.image.title="{opts.name}" \\
      org.opencontainers.image.description="{opts.description}" \\
      org.opencontainers.image.licenses="{opts.license}"

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ENV DEBIAN_FRONTEND=noninteractive \\
    LANG=C.UTF-8 \\
    LC_ALL=C.UTF-8

# Baseline tools — these are present on a stock GHA ubuntu-latest runner;
# pinning them here means the image is a drop-in for `runs-on: ubuntu-latest`
# users who switch to `container:`. If your base already has them this is a
# fast no-op apt cache hit.
RUN apt-get update \\
 && apt-get install -y --no-install-recommends \\
        ca-certificates curl git gnupg jq make tar unzip xz-utils \\
 && rm -rf /var/lib/apt/lists/* \\
 && (command -v gh >/dev/null 2>&1 || ( \\
        curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \\
          | gpg --dearmor -o /usr/share/keyrings/githubcli-archive-keyring.gpg \\
        && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \\
        && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \\
            > /etc/apt/sources.list.d/github-cli.list \\
        && apt-get update \\
        && apt-get install -y --no-install-recommends gh \\
        && rm -rf /var/lib/apt/lists/* \\
    ))
{go_layer}{apt_layer}{pip_layer}
WORKDIR /workspace
"""

    out.append((root / "Dockerfile", dockerfile))
    out.append((root / ".dockerignore", DOCKERIGNORE))

    out.append(
        (
            root / ".github" / "workflows" / "build-image.yml",
            render_docker_build_workflow(opts),
        )
    )
    return out


DOCKERIGNORE = """# file: .dockerignore
# version: 1.0.0
# guid: f0c1ker0-0000-4000-8000-000000000002

.git
.github
.vscode
.idea
node_modules
*.log
.DS_Store
"""


def render_docker_build_workflow(opts: Options) -> str:
    return """# file: .github/workflows/build-image.yml
# version: 1.0.0
# guid: f0c1ker0-0000-4000-8000-000000000003
#
# Build and publish a multi-arch container image to GHCR.
#
# Triggers:
#   * push to main         → tag :sha-<short> + :latest
#   * push of v* tag       → tag :<version> + :latest
#   * weekly cron          → rebuild :latest from the same source so upstream
#                            base-image patches roll in without a code commit
#   * workflow_dispatch    → manual rebuild
#
# The image name follows ghcr.io/<owner>/<repo> by convention. Override via
# the IMAGE_NAME repo variable if a different name is needed.

name: Build image

on:
  push:
    branches: [main]
    tags: ['v*']
  schedule:
    - cron: '0 9 * * 1'  # Mondays 09:00 UTC
  workflow_dispatch: {}

permissions:
  contents: read
  packages: write
  id-token: write
  attestations: write

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ vars.IMAGE_NAME || format('{0}/{1}', github.repository_owner, github.event.repository.name) }}

jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 45
    steps:
      # NOTE: action refs are major-version tags here. The repo's
      # pin-actions-to-hashes step (or dependabot) will rewrite each `@vN`
      # to a digest-pinned `@<sha> # vN.M.K` on first run. Don't hand-pin
      # SHAs at scaffold time — there's no source of truth for "the latest
      # known-good SHA" without a network round-trip.
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3

      - name: Set up Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata (tags, labels)
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=raw,value=latest,enable={{is_default_branch}}
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha,format=short

      - name: Build and push
        id: build
        uses: docker/build-push-action@v6
        with:
          context: .
          platforms: linux/amd64,linux/arm64
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          provenance: true
          sbom: true

      - name: Attest provenance
        uses: actions/attest-build-provenance@v1
        with:
          subject-name: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          subject-digest: ${{ steps.build.outputs.digest }}
          push-to-registry: true
"""


def ensure_parents(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_file(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        return
    ensure_parents(path)
    path.write_text(content, encoding="utf-8")


def print_plan(files: list[tuple[Path, str]]) -> None:
    for p, _ in files:
        print(p)


def normalize_path(p: str) -> Path:
    return Path(os.path.expanduser(os.path.expandvars(p))).resolve()


def parse_args(argv: list[str]) -> Options:
    parser = argparse.ArgumentParser(
        description="Scaffold a public-safe template repository (no secrets, no submodules)."
    )
    parser.add_argument("--name", required=True, help="Repository name (e.g., my-template-repo)")
    parser.add_argument(
        "--owner",
        required=True,
        help="GitHub owner/org (used for CODEOWNERS and copyright)",
    )
    parser.add_argument("--description", default="A minimal public-safe template repository.")
    parser.add_argument("--license", choices=list(SUPPORTED_LICENSES.keys()), default="MIT")
    parser.add_argument("--year", default="2025")
    parser.add_argument(
        "--target",
        required=True,
        help="Target directory to create the repository in",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print files that would be created",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files when present",
    )
    parser.add_argument(
        "--with-go",
        action="store_true",
        help="Include minimal Go overlay and tests",
    )
    parser.add_argument(
        "--with-python",
        action="store_true",
        help="Include minimal Python overlay and tests",
    )
    parser.add_argument(
        "--with-dependabot",
        action="store_true",
        help="Include .github/dependabot.yml",
    )
    parser.add_argument(
        "--with-releases",
        action="store_true",
        help="Include optional release workflows for selected languages",
    )
    parser.add_argument(
        "--with-docker",
        action="store_true",
        help="Include Dockerfile + multi-arch GHCR build/push workflow",
    )
    parser.add_argument(
        "--docker-base-image",
        default="ghcr.io/catthehacker/ubuntu:full-22.04",
        help=(
            "Base image for the Dockerfile when --with-docker is set. "
            "Default mirrors a GitHub Actions Ubuntu runner; catthehacker's "
            "'full-22.04' is the known-good tag — verify before bumping to 24.04."
        ),
    )
    parser.add_argument(
        "--docker-apt",
        action="append",
        default=[],
        help="Additional apt package to install in the image (repeatable)",
    )
    parser.add_argument(
        "--docker-pip",
        action="append",
        default=[],
        help="Additional pip package spec to install in the image (repeatable; supports git+URLs)",
    )
    parser.add_argument(
        "--docker-go-version",
        default="",
        help="Pin a Go toolchain into the image (e.g. 1.25.0). Empty = no Go layer.",
    )
    parser.add_argument(
        "--docker-python-version",
        default="3.13",
        help=(
            "Pin a Python interpreter (installed via uv) for the image's pip "
            "layer. Default 3.13. Only relevant when --docker-pip is also set."
        ),
    )
    parser.add_argument(
        "--with-changelog",
        action="store_true",
        help="Include a CHANGELOG.md skeleton (Keep a Changelog format)",
    )
    parser.add_argument(
        "--with-todo",
        action="store_true",
        help="Include a TODO.md skeleton",
    )
    parser.add_argument(
        "--with-claudemd",
        action="store_true",
        help="Include a CLAUDE.md pointing at .github/ instructions (matches jdfalk repo conventions)",
    )
    parser.add_argument(
        "--with-reusable-workflows",
        action="store_true",
        help=(
            "Replace the standalone ci.yml with a thin caller of "
            "jdfalk/ghcommon/.github/workflows/reusable-ci.yml, plus "
            "security.yml and .github/workflow-config.yaml."
        ),
    )
    parser.add_argument(
        "--reusable-workflows-ref",
        default="main",
        help=(
            "Git ref for the ghcommon reusable workflows. Defaults to 'main'. "
            "Production callers SHOULD pin to a SHA — the next pin-actions "
            "step rewrites '@main' automatically."
        ),
    )

    args = parser.parse_args(argv)
    target_dir = normalize_path(args.target)

    return Options(
        name=args.name,
        owner=args.owner,
        description=args.description,
        license=args.license,
        year=args.year,
        target_dir=target_dir,
        dry_run=args.dry_run,
        force=args.force,
        with_go=args.with_go,
        with_python=args.with_python,
        with_dependabot=args.with_dependabot,
        with_releases=args.with_releases,
        with_docker=args.with_docker,
        docker_base_image=args.docker_base_image,
        docker_apt_packages=tuple(args.docker_apt),
        docker_pip_packages=tuple(args.docker_pip),
        docker_go_version=args.docker_go_version,
        docker_python_version=args.docker_python_version,
        with_changelog=args.with_changelog,
        with_todo=args.with_todo,
        with_claudemd=args.with_claudemd,
        with_reusable_workflows=args.with_reusable_workflows,
        reusable_workflows_ref=args.reusable_workflows_ref,
    )


def assert_no_nested_repo(target_dir: Path) -> None:
    # Ensure we don't accidentally create a git repo inside another repo as a submodule-like structure
    # by checking for .git presence in ancestors (informational) and in target (prevent creation here).
    if (target_dir / ".git").exists():
        # Do not delete or modify; just warn and continue (we won't run git here anyway).
        print(
            "Warning: target directory contains a .git folder. This script does not run git commands.",
            file=sys.stderr,
        )


def main(argv: list[str]) -> int:
    opts = parse_args(argv)
    assert_no_nested_repo(opts.target_dir)
    files = plan_files(opts)

    if opts.dry_run:
        print_plan(files)
        return 0

    for path, content in files:
        write_file(path, content, force=opts.force)

    print(f"Scaffold complete at: {opts.target_dir}")
    print("Note: No git commands were executed. Use push_with_gh.py if you want to publish.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
