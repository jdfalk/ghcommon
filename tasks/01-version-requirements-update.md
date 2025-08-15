# Task 1: Go and Python Version Requirements Update

<!-- file: tasks/01-version-requirements-update.md -->
<!-- version: 1.0.0 -->
<!-- guid: 12345678-1234-1234-1234-123456789abc -->

## Overview

Update all Go and Python version requirements across all repositories to use minimum versions Go 1.23+ and Python 3.13+. This ensures consistency and access to latest language features.

## Critical Instructions

**NEVER edit README.md, CHANGELOG.md, TODO.md or other documentation files directly. ALWAYS use:**
- `scripts/create-doc-update.sh` for documentation updates
- `scripts/create-issue-update.sh` for issue updates
- This prevents merge conflicts between multiple AI agents

**ALWAYS follow the VS Code task priority:**
1. Use VS Code tasks first (via `run_task` tool)
2. Use `copilot-agent-util` / `copilot-agent-utilr`
3. Manual terminal commands only as last resort

## Repository Standards

### General Coding Instructions
Follow the complete [general coding instructions](../.github/instructions/general-coding.instructions.md) which include:
- Required file headers with path, version, and GUID
- Version update requirements when modifying files
- Documentation update system usage
- VS Code tasks priority system

### Go Language Standards
<!-- file: .github/instructions/go.instructions.md -->
<!-- version: 1.3.0 -->
<!-- guid: 4f5a6b7c-8d9e-0f1a-2b3c-4d5e6f7a8b9c -->
<!-- DO NOT EDIT: This file is managed centrally in ghcommon repository -->
<!-- To update: Create an issue/PR in jdfalk/ghcommon -->

---
applyTo: "**/*.go"
description: |
  Go language-specific coding, documentation, and testing rules for Copilot/AI agents and VS Code Copilot customization. These rules extend the general instructions in `general-coding.instructions.md` and merge all unique content from the Google Go Style Guide.
---

# Go Coding Instructions

- Follow the [general coding instructions](general-coding.instructions.md).
- Follow the
  [Google Go Style Guide](https://google.github.io/styleguide/go/index.html) for
  additional best practices.
- All Go files must begin with the required file header (see general
  instructions for details and Go example).

## Version Requirements

- **MANDATORY**: All Go projects must use Go 1.23 or higher
- Update `go.mod` files to specify `go 1.23` minimum
- Update `go.work` files to specify `go 1.23` minimum
- All Go file headers must use version 1.23.0 or higher

## Core Principles

- Clarity over cleverness: Code should be clear and readable
- Simplicity: Prefer simple solutions over complex ones
- Consistency: Follow established patterns within the codebase
- Readability: Code is written for humans to read

## Naming Conventions

- Use short, concise, evocative package names (lowercase, no underscores)
- Use camelCase for unexported names, PascalCase for exported names
- Use short names for short-lived variables, descriptive names for longer-lived
  variables
- Use PascalCase for exported constants, camelCase for unexported constants
- Single-method interfaces should end in "-er" (e.g., Reader, Writer)

## Code Organization

- Use `goimports` to format imports automatically
- Group imports: standard library, third-party, local
- No blank lines within groups, one blank line between groups
- Keep functions short and focused
- Use blank lines to separate logical sections
- Order: receiver, name, parameters, return values

## Formatting

- Use tabs for indentation, spaces for alignment
- Opening brace on same line as declaration, closing brace on its own line
- No strict line length limit, but aim for readability

## Comments

- Every package should have a package comment
- Public functions must have comments starting with the function name
- Comment exported variables, explain purpose and constraints

## Error Handling

- Use lowercase for error messages, no punctuation at end
- Be specific about what failed
- Create custom error types for specific error conditions
- Use `errors.Is` and `errors.As` for error checking

## Best Practices

- Use short variable declarations (`:=`) when possible
- Use `var` for zero values or when type is important
- Use `make()` for slices and maps with known capacity
- Accept interfaces, return concrete types
- Keep interfaces small and focused
- Use channels for communication between goroutines
- Use sync primitives for protecting shared state
- Test file names end with `_test.go`, test function names start with `Test`
- Use table-driven tests for multiple scenarios

## Required File Header

All Go files must begin with a standard header as described in the
[general coding instructions](general-coding.instructions.md). Example for Go:

```go
// file: path/to/file.go
// version: 1.0.0
// guid: 123e4567-e89b-12d3-a456-426614174000
```

### Python Language Standards

Follow the [Python instructions](../.github/instructions/python.instructions.md) which require Python 3.13+ and include comprehensive style guidelines.

### Rust Utility Instructions

<!-- file: .github/instructions/rust-utility.instructions.md -->
<!-- version: 1.2.0 -->
<!-- guid: a1b2c3d4-e5f6-7890-1234-567890abcdef -->

---

applyTo: "**"
description: |
  Instructions for using the copilot-agent-util Rust utility as the primary tool for development operations. This utility provides superior performance, memory safety, and comprehensive command coverage compared to manual terminal commands.

---

# Copilot Agent Utility (Rust) - Command Reference

The `copilot-agent-util` (or `copilot-agent-utilr`) is a comprehensive Rust-based development utility that provides superior performance, memory safety, and extensive command coverage. **Always prefer this utility over manual commands when available.**

## 📥 Installation & Download

**Download the copilot-agent-util tool from:**
- **Source Repository**: https://github.com/jdfalk/copilot-agent-util-rust
- **Installation**: Follow the installation instructions in the repository's README
- **Requirements**: The tool is required for proper VS Code task execution and logging

**If the tool is not available in your environment:**
1. Clone the repository: `git clone https://github.com/jdfalk/copilot-agent-util-rust`
2. Build with Cargo: `cargo build --release`
3. Add to PATH or use the binary directly from `target/release/copilot-agent-util`

## 🚀 NEW: Arguments File Support

The utility now supports loading arguments from a standard configuration file called `copilot-util-args`. This allows for:

- **Consistent configuration** across all repositories
- **Easy updates** by modifying a single file
- **Environment-specific settings** without changing tasks
- **Complex argument sets** without cluttering VS Code tasks

### Arguments File Location

The utility looks for `copilot-util-args` in the current working directory or any parent directory (similar to how git finds .git). The file format supports:

```bash
# copilot-util-args - Standard configuration file
# Comments are supported with #

# Git configuration
git.default-branch=main
git.auto-push=true
git.commit-template="feat: {message}"

# Editor settings
editor.syntax=auto-detect
editor.tab-width=4
editor.show-line-numbers=true

# Buf/protobuf settings
buf.output-dir=gen
buf.lint-config=.buf.yaml
buf.generate-docs=true

# Global settings
verbose=true
log-level=info
```

### Using Arguments Files

When a `copilot-util-args` file is present, the utility automatically loads these settings:

```bash
# The utility automatically finds and uses the args file
copilot-agent-utilr git commit -m "implement feature"
# Uses git.commit-template and other git.* settings from copilot-util-args

copilot-agent-utilr buf generate
# Uses buf.* settings from copilot-util-args

copilot-agent-utilr editor file.rs
# Uses editor.* settings from copilot-util-args
```

## 🚨 PRIORITY ORDER FOR OPERATIONS

**MANDATORY: Follow this exact priority when performing ANY operation:**

1. **FIRST**: Use VS Code tasks (via `run_task` tool) when available
2. **SECOND**: Use `copilot-agent-util` / `copilot-agent-utilr` Rust utility
3. **LAST RESORT**: Manual terminal commands only if neither above option exists

## Available Commands

### 🔧 Git Operations (Comprehensive)

The utility provides **complete git functionality** with 18+ subcommands and automatic configuration from `copilot-util-args`:

```bash
# Git command structure
copilot-agent-utilr git <subcommand> [options] [args]

# Available git subcommands:
copilot-agent-utilr git add [files...]           # Add files to staging
copilot-agent-utilr git commit -m "message"      # Commit changes (uses templates from args file)
copilot-agent-utilr git push                     # Push to remote (respects auto-push setting)
copilot-agent-utilr git pull                     # Pull from remote
copilot-agent-utilr git status                   # Show working tree status
copilot-agent-utilr git branch [name]            # List/create branches
copilot-agent-utilr git checkout <branch>        # Switch branches
copilot-agent-utilr git merge <branch>           # Merge branches
copilot-agent-utilr git rebase <branch>          # Rebase commits
```

For complete command reference and advanced features, see the full documentation at: https://github.com/jdfalk/copilot-agent-util-rust

## Tasks to Complete

### 1. Update Go Module Files
**Repositories to check:** gcommon, ghcommon, subtitle-manager, audiobook-organizer, copilot-agent-util-rust

For each repository:
- Update `go.mod` to specify `go 1.23` minimum version
- Update any `go.work` files to specify `go 1.23` minimum version
- Update Go file headers that reference older versions

### 2. Update Python Requirements Files
**Repositories to check:** All repositories with Python files

For each repository:
- Update `requirements.txt` files to specify `python_requires=">=3.13"`
- Update `pyproject.toml` files to specify `requires-python = ">=3.13"`
- Update `setup.py` files to specify `python_requires=">=3.13"`
- Update Python file headers that reference older versions

### 3. Validation Steps
- Run `go mod tidy` in each Go repository after updates
- Test Python environments with new requirements
- Verify all modules build successfully
- Check for any version-specific compatibility issues

## Expected Deliverables

1. Updated `go.mod` and `go.work` files with Go 1.23+ requirements
2. Updated Python requirements files with Python 3.13+ requirements
3. Updated file headers where version numbers were changed
4. Validation that all modules build and work correctly
5. Documentation updates using the proper update system (NOT direct edits)

## Acceptance Criteria

- [ ] All Go modules specify Go 1.23+ minimum
- [ ] All Python projects specify Python 3.13+ minimum
- [ ] All updated files have proper version headers
- [ ] All modules build without version-related errors
- [ ] No direct documentation file edits (used scripts instead)

## Repository List to Update

1. `/Users/jdfalk/repos/github.com/jdfalk/gcommon`
2. `/Users/jdfalk/repos/github.com/jdfalk/ghcommon`
3. `/Users/jdfalk/repos/github.com/jdfalk/subtitle-manager`
4. `/Users/jdfalk/repos/github.com/jdfalk/audiobook-organizer`
5. `/Users/jdfalk/repos/github.com/jdfalk/copilot-agent-util-rust`

## Notes
- The ghcommon repository already has Go 1.23.0 in go.mod - verify others match
- Focus on consistency across all repositories
- Test thoroughly after version updates
- Use VS Code tasks for git operations where possible
