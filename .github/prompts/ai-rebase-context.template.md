<!-- file: .github/prompts/ai-rebase-context.template.md -->
<!-- version: 1.1.0 -->
<!-- guid: 9c8d7e6f-5a4b-3c2d-1e0f-9a8b7c6d5e4f -->

# Repository Context for AI Rebase

This file contains repository-specific context that should be included with conflict resolution
prompts. Copy this template to your repository and customize it with project-specific information.

**Important Notes for Repository Setup:**

- AGENTS.md and CLAUDE.md are now in the **repository root**, not .github/
- Use **copilot-agent-util** tool for safe git operations (available at
  <https://github.com/jdfalk/copilot-agent-util-rust/releases/latest>)
- Use **direct-edit workflow** for documentation (no doc-update scripts)
- All files require versioned headers with file path, version, and GUID

## Project Overview

<!-- Brief description of the project and its main components -->
<!--
Example:
This is the **[your-repo-name]** repository, which focuses on:
- Key feature 1
- Key feature 2
- Key feature 3
-->

## Coding Standards

<!--
Key coding standards and patterns used in this repository.
Reference your .github/instructions/ files here.
Example:
- Follow conventional commit message format: type(scope): description
- Use proper file headers with path, version, and GUID (see general-coding.instructions.md)
- Follow language-specific guidelines in .github/instructions/[language].instructions.md
- Use semantic versioning for all files
-->

## Key Files to Reference

<!--
Important files that provide context for conflict resolution.
Always include AGENTS.md and CLAUDE.md in repository root.
-->

### AGENTS.md

<!-- Located in repository root. Points to .github/ for detailed instructions. -->

### CLAUDE.md

<!-- Located in repository root. Contains agent-specific workflow guidance. -->

### README.md

<!-- Include relevant sections from README that help understand the project -->

### .github/instructions/general-coding.instructions.md

<!--
Contains canonical coding standards and file header requirements.
All repositories should reference this file.
-->

### Key Configuration Files

<!--
Include snippets from important config files that affect code style.
Examples: .markdownlint.json, .eslintrc.yml, ruff.toml, rustfmt.toml
-->

## Common Conflict Patterns

<!--
Document common types of conflicts that occur in this repo and how to resolve them.
Examples:
- File Headers: Always preserve GUID, increment version, use correct path
- Workflow Files: Preserve both logic when possible, maintain YAML indentation
- Documentation: Combine additions rather than choosing one side
-->

### File Headers

<!--
When resolving conflicts in file headers, always:
- Keep the correct file path relative to repository root
- Increment the version number appropriately (patch/minor/major)
- Preserve the GUID (never change it)
- Use the correct comment format for the file type
-->

## Dependencies and Imports

<!--
Key information about how modules/packages are organized.
Examples:
- Python: Uses standard library when possible
- Go: Uses go.mod for dependency management
- JavaScript: Uses package.json with specific version ranges
-->

## Development Tools

<!--
Mention key tools used in development workflow:
- copilot-agent-util: Safe git operations with enhanced logging
  Download: https://github.com/jdfalk/copilot-agent-util-rust/releases/latest
- VS Code Tasks: Prefer tasks over manual commands
- Super Linter: Automated code quality checks
-->

## Project Structure

<!--
Document the repository structure.
Example:
- .github/workflows/ - GitHub Actions workflows
- .github/instructions/ - Coding standards and guidelines
- .github/prompts/ - AI prompt templates
- scripts/ - Automation and utility scripts
- src/ or pkg/ - Source code
- tests/ - Test files
- docs/ - Additional documentation
-->
