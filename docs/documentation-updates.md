<!-- file: docs/documentation-updates.md -->
<!-- version: 2.0.0 -->
<!-- guid: 4e5f6789-0123-4567-8901-2345678901ab -->

# Documentation Update System

A comprehensive, automated system for managing documentation updates across repositories using JSON-driven update files and workflows.

## Overview

The Documentation Update System provides a structured approach to updating documentation files like `README.md`, `CHANGELOG.md`, and `TODO.md` through automated workflows. Instead of directly editing documentation files, users create JSON update files that are processed by workflows.

## System Architecture

### Components

- **`create-doc-update.sh`**: Enhanced script for creating documentation update files
- **`doc_update_manager.py`**: Python processor that applies updates to target files
- **`reusable-docs-update.yml`**: Reusable GitHub Actions workflow
- **`docs-update.yml`**: Repository-specific workflow that uses the reusable workflow

### File Structure

```text
repository/
├── .github/
│   ├── doc-updates/           # Pending update files
│   │   ├── update-1.json
│   │   ├── update-2.json
│   │   └── processed/         # Archived processed files
│   │       ├── update-1.json
│   │       └── update-2.json
│   └── workflows/
│       └── docs-update.yml    # Repository workflow
└── scripts/
    └── create-doc-update.sh   # Update creation script
```

## Creating Documentation Updates

### Basic Usage

The `create-doc-update.sh` script provides multiple ways to create updates:

```bash
# Basic append operation
./scripts/create-doc-update.sh README.md "## New Section\nContent here" append

# Using templates for common operations
./scripts/create-doc-update.sh --template changelog-feature "Added user authentication"
./scripts/create-doc-update.sh --template todo-task "Implement OAuth2 integration"

# Interactive mode
./scripts/create-doc-update.sh --interactive
```

### Available Update Modes

| Mode              | Description                            | Example Use Case                   |
| ----------------- | -------------------------------------- | ---------------------------------- |
| `append`          | Add content to end of file             | Adding new sections                |
| `prepend`         | Add content to beginning of file       | Adding urgent notices              |
| `replace`         | Replace entire file content            | Complete rewrites                  |
| `replace-section` | Replace specific section               | Updating installation instructions |
| `insert-after`    | Insert after specific text             | Adding content after a heading     |
| `insert-before`   | Insert before specific text            | Adding prerequisites               |
| `changelog-entry` | Add properly formatted changelog entry | Release notes                      |
| `task-add`        | Add task to TODO list                  | Project planning                   |
| `task-complete`   | Mark task as complete                  | Progress tracking                  |
| `update-badge`    | Update README badge                    | Status updates                     |

### Template System

Pre-built templates for common documentation patterns:

```bash
# Changelog templates
./scripts/create-doc-update.sh --template changelog-fix "Fixed authentication bug"
./scripts/create-doc-update.sh --template changelog-feature "Added user profiles"
./scripts/create-doc-update.sh --template changelog-breaking "Changed API response format"

# TODO templates
./scripts/create-doc-update.sh --template todo-task "Implement feature X" --priority HIGH
./scripts/create-doc-update.sh --template todo-epic "User Management System"

# README templates
./scripts/create-doc-update.sh --template readme-section "Installation"
./scripts/create-doc-update.sh --template readme-badge "build-status"
```

### Advanced Options

```bash
# Section replacement
./scripts/create-doc-update.sh README.md "New content" replace-section --section "Installation"

# Task management
./scripts/create-doc-update.sh TODO.md "Feature complete" task-complete --task-id "AUTH-001"

# Priority and categorization
./scripts/create-doc-update.sh TODO.md "Critical bug fix" task-add --priority HIGH --category "Bugs"

# Dry run mode
./scripts/create-doc-update.sh README.md "Test content" append --dry-run
```

## Use Cases

### For AI/Copilot Agents

**AI agents and Copilot should ALWAYS use this system instead of directly editing documentation files.**

```bash
# Creating changelog entries during development
./scripts/create-doc-update.sh --template changelog-feature "Implemented user authentication system"

# Adding TODO items for future work
./scripts/create-doc-update.sh --template todo-task "Add integration tests" --priority MED

# Updating README with new features
./scripts/create-doc-update.sh README.md "## Authentication\n\nUsers can now sign in with..." append
```

### For Development Teams

```bash
# Interactive updates for complex changes
./scripts/create-doc-update.sh --interactive

# Batch operations via templates
for feature in auth profiles admin; do
  ./scripts/create-doc-update.sh --template todo-task "Implement $feature module" --category "Features"
done

# Section updates during refactoring
./scripts/create-doc-update.sh README.md "Updated API documentation" replace-section --section "API Reference"
```

### For Project Management

```bash
# Marking tasks complete
./scripts/create-doc-update.sh TODO.md "Authentication implementation" task-complete

# Adding milestones
./scripts/create-doc-update.sh --template todo-epic "Phase 2: Advanced Features"

# Release notes
./scripts/create-doc-update.sh --template changelog-breaking "API endpoints now require authentication"
```

## Best Practices

### For AI Agents

1. **Always use the script** instead of direct file edits
2. **Choose appropriate modes** for the type of update
3. **Include context** in update content
4. **Use GUID system** to prevent duplicate operations

### For Documentation Authors

1. **Use templates** for consistent formatting
2. **Test with dry-run** before creating updates
3. **Group related changes** in single updates when possible
4. **Use descriptive content** that explains the change context

## Related Documentation

- [Issue Management System](unified-issue-management.md)
- [Workflow Architecture](../WORKFLOW_ARCHITECTURE.md)
- [Copilot Instructions](../copilot-instructions.md)
- [General Coding Guidelines](../instructions/general-coding.instructions.md)
