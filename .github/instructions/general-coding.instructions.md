<!-- file: .github/instructions/general-coding.instructions.md -->
<!-- version: 1.3.0 -->
<!-- guid: 1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d -->
<!-- DO NOT EDIT: This file is managed centrally in ghcommon repository -->
<!-- To update: Create an issue/PR in jdfalk/ghcommon -->

---
applyTo: "**"
description: |
  General coding, documentation, and workflow rules for all Copilot/AI agents and VS Code Copilot customization. These rules apply to all files and languages unless overridden by a more specific instructions file. For details, see the main documentation in `.github/copilot-instructions.md`.
---

---

# General Coding Instructions

These instructions are the canonical source for all Copilot/AI agent coding,
documentation, and workflow rules in this repository. They are referenced by
language- and task-specific instructions, and are always included by default in
Copilot customization.

- Follow the [commit message standards](../commit-messages.md) and
  [pull request description guidelines](../pull-request-descriptions.md).
- All language/framework-specific style and workflow rules are now found in
  `.github/instructions/*.instructions.md` files. These are the only canonical
  source for code style, documentation, and workflow rules for each language or
  framework.
- Document all code, classes, functions, and tests extensively, using the
  appropriate style for the language.
- Use the Arrange-Act-Assert pattern for tests, and follow the
  [test generation guidelines](../test-generation.md).
- For agent/AI-specific instructions, see [AGENTS.md](../AGENTS.md) and related
  files.
- Do not duplicate rules; reference this file from more specific instructions.
- For VS Code Copilot customization, this file is included via symlink in
  `.vscode/copilot/`.
- **ALWAYS check before doing:** Before creating files, running operations, or executing scripts, always check current state first. Make all scripts and operations idempotent by checking if the desired state already exists before making changes.
- **Use VS Code Tasks when available:** When performing git operations (add, commit, push, status) or project-specific builds/tests, prefer using the standardized VS Code tasks over manual terminal commands. All task output is logged to the `logs/` folder for review and debugging. Always check the corresponding log file after running a task to verify success or diagnose issues.

For more details and the full system, see
[copilot-instructions.md](../copilot-instructions.md).

## Required File Header (File Identification)

All source, script, and documentation files MUST begin with a standard header
containing:

- The exact relative file path from the repository root (e.g.,
  `# file: path/to/file.py`)
- The file's semantic version (e.g., `# version: 1.1.0`)
- The file's GUID (e.g., `# guid: 123e4567-e89b-12d3-a456-426614174000`)

**Header format varies by language/file type:**

- **Markdown:**
  ```markdown
  <!-- file: path/to/file.md -->
  <!-- version: 1.1.0 -->
  <!-- guid: 123e4567-e89b-12d3-a456-426614174000 -->
  ```
- **Python:**
  ```python
  #!/usr/bin/env python3
  # file: path/to/file.py
  # version: 1.1.0
  # guid: 123e4567-e89b-12d3-a456-426614174000
  ```
- **Go:**
  ```go
  // file: path/to/file.go
  // version: 1.1.0
  // guid: 123e4567-e89b-12d3-a456-426614174000
  ```
- **JavaScript/TypeScript:**
  ```js
  // file: path/to/file.js
  // version: 1.1.0
  // guid: 123e4567-e89b-12d3-a456-426614174000
  ```
- **Shell (bash/sh):**
  ```bash
  #!/bin/bash
  # file: path/to/script.sh
  # version: 1.1.0
  # guid: 123e4567-e89b-12d3-a456-426614174000
  ```
  (Header must come after the shebang line)
- **CSS:**
  ```css
  /* file: path/to/file.css */
  /* version: 1.1.0 */
  /* guid: 123e4567-e89b-12d3-a456-426614174000 */
  ```
- **R:**
  ```r
  # file: path/to/file.R
  # version: 1.1.0
  # guid: 123e4567-e89b-12d3-a456-426614174000
  ```
- **JSON:**
  ```jsonc
  // file: path/to/file.json
  // version: 1.1.0
  // guid: 123e4567-e89b-12d3-a456-426614174000
  ```
- **TOML:**
  ```toml
  [section]
  # file: path/to/file.toml
  # version: 1.1.0
  # guid: 123e4567-e89b-12d3-a456-426614174000
  ```
  (Header must be inside a section as TOML doesn't support top-level comments)

**All files must include this header in the correct format for their type.**

## Version Update Requirements

**When modifying any file with a version header, ALWAYS update the version
number:**

- **Patch version** (x.y.Z): Bug fixes, typos, minor formatting changes
- **Minor version** (x.Y.z): New features, significant content additions,
  template changes
- **Major version** (X.y.z): Breaking changes, structural overhauls, format
  changes

**Examples:**

- Fix typo: `1.2.3` → `1.2.4`
- Add new section: `1.2.3` → `1.3.0`
- Change template structure: `1.2.3` → `2.0.0`

**This applies to all files with version headers including documentation,
templates, and configuration files.**

## Documentation Update System

When making documentation updates to `README.md`, `CHANGELOG.md`, `TODO.md`, or
other documentation files, use the automated documentation update system instead
of direct edits:

### Creating Documentation Updates

1. **Use the script**: Always use `scripts/create-doc-update.sh` to create
   documentation updates
2. **Available modes**:
   - `append` - Add content to end of file
   - `prepend` - Add content to beginning of file
   - `replace-section` - Replace specific section
   - `changelog-entry` - Add properly formatted changelog entry
   - `task-add` - Add task to TODO list
   - `task-complete` - Mark task as complete

### Examples

```bash
# Add a new changelog entry
./scripts/create-doc-update.sh --template changelog-feature "Added user authentication system"

# Add a TODO task with high priority
./scripts/create-doc-update.sh TODO.md "Implement OAuth2 integration" task-add --priority HIGH

# Update a specific section
./scripts/create-doc-update.sh README.md "Updated installation instructions" replace-section --section "Installation"

# Interactive mode for complex updates
./scripts/create-doc-update.sh --interactive
```

### Processing Updates

- Updates are stored as JSON files in `.github/doc-updates/`
- The workflow `docs-update.yml` automatically processes these files
- Processed files are moved to `.github/doc-updates/processed/`
- Changes can be made via direct commit or pull request

### Benefits

- **Consistency**: Standardized formatting across all documentation
- **Traceability**: Each update has a GUID and timestamp
- **Automation**: Reduces manual errors and ensures proper formatting
- **Conflict Resolution**: Multiple agents can create updates simultaneously

**Always use this system for documentation updates instead of direct file
edits.**

## VS Code Tasks and Automation

All repositories are configured with standardized VS Code tasks for common
operations. **Always prefer using these tasks over manual terminal commands.**

### Task Categories

- **Git Operations**: `Git Add All`, `Git Add Selective`, `Git Commit`, `Git Push`, `Git Status`
- **Build Operations**: Repository-specific tasks (e.g., `Go Build`, `Buf Generate`, `Python Test`)
- **Project Operations**: Language/framework-specific tasks

### Task Output and Logging

- **All task output is logged to the `logs/` folder** (gitignored)
- **Always check log files after running tasks** to verify success or diagnose issues
- Log files are named descriptively: `git_commit.log`, `go_build.log`, etc.
- Tasks include success/failure messages at the end of each log

### Usage

1. **Run tasks via VS Code**: Command Palette (`Ctrl/Cmd+Shift+P`) → "Tasks: Run Task"
2. **Check results**: Read the corresponding log file in `logs/` folder
3. **Automate workflows**: Chain tasks together for complex operations

### Examples

```bash
# Instead of: git add . && git commit -m "message" && git push
# Use tasks: "Git Add All" → "Git Commit" → "Git Push"

# Instead of: go build -o bin/app
# Use task: "Go Build"

# Instead of: buf generate
# Use task: "Buf Generate with Output"
```

This approach provides consistent logging, error handling, and automation across
all repositories.
