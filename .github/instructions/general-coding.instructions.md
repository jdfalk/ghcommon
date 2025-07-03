<!-- file: .github/instructions/general-coding.instructions.md -->
---
applyTo: "**"
description: |
  General coding, documentation, and workflow rules for all Copilot/AI agents and VS Code Copilot customization. These rules apply to all files and languages unless overridden by a more specific instructions file. For details, see the main documentation in `.github/copilot-instructions.md`.
---

# General Coding Instructions

These instructions are the canonical source for all Copilot/AI agent coding, documentation, and workflow rules in this repository. They are referenced by language- and task-specific instructions, and are always included by default in Copilot customization.

- Follow the [commit message standards](../commit-messages.md) and [pull request description guidelines](../pull-request-descriptions.md).
- All language/framework-specific style and workflow rules are now found in `.github/instructions/*.instructions.md` files. These are the only canonical source for code style, documentation, and workflow rules for each language or framework.
- Document all code, classes, functions, and tests extensively, using the appropriate style for the language.
- Use the Arrange-Act-Assert pattern for tests, and follow the [test generation guidelines](../test-generation.md).
- For agent/AI-specific instructions, see [AGENTS.md](../AGENTS.md) and related files.
- Do not duplicate rules; reference this file from more specific instructions.
- For VS Code Copilot customization, this file is included via symlink in `.vscode/copilot/`.

For more details and the full system, see [copilot-instructions.md](../copilot-instructions.md).

## Required File Header (File Identification)

All source, script, and documentation files MUST begin with a standard header containing:
- The exact relative file path from the repository root (e.g., `# file: path/to/file.py`)
- The file's semantic version (e.g., `# version: 1.0.0`)
- The file's GUID (e.g., `# guid: 123e4567-e89b-12d3-a456-426614174000`)

**Header format varies by language/file type:**

- **Markdown:**
  ```markdown
  <!-- file: path/to/file.md -->
  <!-- version: 1.0.0 -->
  <!-- guid: 123e4567-e89b-12d3-a456-426614174000 -->
  ```
- **Python:**
  ```python
  #!/usr/bin/env python3
  # file: path/to/file.py
  # version: 1.0.0
  # guid: 123e4567-e89b-12d3-a456-426614174000
  ```
- **Go:**
  ```go
  // file: path/to/file.go
  // version: 1.0.0
  // guid: 123e4567-e89b-12d3-a456-426614174000
  ```
- **JavaScript/TypeScript:**
  ```js
  // file: path/to/file.js
  // version: 1.0.0
  // guid: 123e4567-e89b-12d3-a456-426614174000
  ```
- **Shell (bash/sh):**
  ```bash
  #!/bin/bash
  # file: path/to/script.sh
  # version: 1.0.0
  # guid: 123e4567-e89b-12d3-a456-426614174000
  ```
  (Header must come after the shebang line)
- **Protobuf:**
  ```protobuf
  // file: path/to/file.proto
  // version: 1.0.0
  // guid: 123e4567-e89b-12d3-a456-426614174000
  ```
- **CSS:**
  ```css
  /* file: path/to/file.css */
  /* version: 1.0.0 */
  /* guid: 123e4567-e89b-12d3-a456-426614174000 */
  ```
- **R:**
  ```r
  # file: path/to/file.R
  # version: 1.0.0
  # guid: 123e4567-e89b-12d3-a456-426614174000
  ```
- **JSON:**
  ```jsonc
  // file: path/to/file.json
  // version: 1.0.0
  // guid: 123e4567-e89b-12d3-a456-426614174000
  ```

**All files must include this header in the correct format for their type.**
