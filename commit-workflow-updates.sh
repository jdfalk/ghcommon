#!/bin/bash
# file: commit-workflow-updates.sh
# version: 2.0.1
# guid: 123e4567-e89b-12d3-a456-426614174001

set -e

BASE_DIR="/Users/jdfalk/repos/github.com/jdfalk"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_DIR="$SCRIPT_DIR"

echo "🚀 Starting comprehensive GitHub setup across all repositories..."
echo "Base directory: $BASE_DIR"
echo "Script directory: $SCRIPT_DIR"
echo "Template directory: $TEMPLATE_DIR"
echo ""

# Counter variables
REPOS_PROCESSED=0
REPOS_WITH_CHANGES=0
REPOS_COMMITTED=0
REPOS_SKIPPED=0
REPOS_GITHUB_CREATED=0

# Function to create .github structure and files
create_github_structure() {
  local repo_name="$1"
  local created_structure=false

  echo "   🏗️  Setting up .github structure..."

  # Create .github directory structure
  mkdir -p .github/{workflows,instructions,prompts,copilot,ISSUE_TEMPLATE,PULL_REQUEST_TEMPLATE}

  # Create copilot-instructions.md if it doesn't exist
  if [ ! -f ".github/copilot-instructions.md" ]; then
    echo "   📝 Creating copilot-instructions.md..."
    cat >.github/copilot-instructions.md <<'EOF'
<!-- file: .github/copilot-instructions.md -->
<!-- version: 2.0.0 -->
<!-- guid: 4d5e6f7a-8b9c-0d1e-2f3a-4b5c6d7e8f9a -->

# Copilot/AI Agent Coding Instructions System

This repository uses a centralized, modular system for Copilot/AI agent coding,
documentation, and workflow instructions, following the latest VS Code Copilot
customization best practices.

## 🚨 CRITICAL: Documentation Update Protocol

This repository no longer uses doc-update scripts. Follow these rules instead:

- Edit documentation directly in the files within this repository.
- Keep the required file header (file path, version, guid) and bump the version on any change.
- Do not use create-doc-update.sh or related scripts; they are retired.
- Follow \`.github/instructions/general-coding.instructions.md\` and language-specific instruction files for rules.
- Prefer VS Code tasks for git operations (Git Add All, Git Commit, Git Push).
  - These tasks use copilot-agent-util for enhanced logging and safety.
  - Download: https://github.com/jdfalk/copilot-agent-util-rust/releases/latest

## System Overview

- **General rules**: `.github/instructions/general-coding.instructions.md`
  (applies to all files)
- **Language/task-specific rules**: `.github/instructions/*.instructions.md`
  (with `applyTo` frontmatter)
- **Prompt files**: `.github/prompts/` (for Copilot/AI prompt customization)
- **Agent-specific docs**: `.github/AGENTS.md`, `.github/CLAUDE.md`, etc.
  (pointers to this system)
- **VS Code integration**: `.vscode/copilot/` contains symlinks to canonical
  `.github/instructions/` files for VS Code Copilot features

## How It Works

- **General instructions** are always included for all files and languages.
- **Language/task-specific instructions** extend the general rules and use the
  `applyTo` field to target file globs (e.g., `**/*.go`).
- **All code style, documentation, and workflow rules are now found exclusively
  in `.github/instructions/*.instructions.md` files.**
- **Prompt files** are stored in `.github/prompts/` and can reference
  instructions as needed.
- **Agent docs** (e.g., AGENTS.md) point to `.github/` as the canonical source
  for all rules.
- **VS Code** uses symlinks in `.vscode/copilot/` to include these instructions
  for Copilot customization.

## For Contributors

- **Edit or add rules** in `.github/instructions/` only. Do not use or reference
  any `code-style-*.md` files; these are obsolete.
- **Add new prompts** in `.github/prompts/`.
- **Update agent docs** to reference this system.
- **Do not duplicate rules**; always reference the general instructions from
  specific ones.
- **See `.github/README.md`** for a human-friendly summary and contributor
  guide.

For full details, see the
[general coding instructions](instructions/general-coding.instructions.md) and
language-specific files in `.github/instructions/`.
EOF
    created_structure=true
  fi

  # Create general-coding.instructions.md if it doesn't exist
  if [ ! -f ".github/instructions/general-coding.instructions.md" ]; then
    echo "   📝 Creating general-coding.instructions.md..."
    cat >.github/instructions/general-coding.instructions.md <<'EOF'
<!-- file: .github/instructions/general-coding.instructions.md -->
<!-- version: 1.2.0 -->
<!-- guid: 1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d -->
<!-- DO NOT EDIT: This file is managed centrally in ghcommon repository -->
<!-- To update: Create an issue/PR in jdfalk/ghcommon -->

applyTo: "**"
description: |
General coding, documentation, and workflow rules for all Copilot/AI agents and VS Code Copilot customization. These rules apply to all files and languages unless overridden by a more specific instructions file. For details, see the main documentation in `.github/copilot-instructions.md`.

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
EOF
    created_structure=true
  fi

  # Create AGENTS.md if it doesn't exist
  if [ ! -f ".github/AGENTS.md" ]; then
    echo "   📝 Creating AGENTS.md..."
    cat >.github/AGENTS.md <<'EOF'
<!-- file: .github/AGENTS.md -->
<!-- version: 1.0.0 -->
<!-- guid: 3c4d5e6f-7a8b-9c0d-1e2f-3a4b5c6d7e8f -->

# AGENTS.md

> **NOTE:** This file is a pointer. All Copilot/AI agent and workflow
> instructions are now centralized in the `.github/instructions/` and
> `.github/prompts/` directories.

## Canonical Source for Agent Instructions

- General and language-specific rules: `.github/instructions/` (all code style,
  documentation, and workflow rules are here)
- Prompts: `.github/prompts/`
- System documentation: `.github/copilot-instructions.md`

For all agent, Copilot, or workflow tasks, **refer to the above files**. Do not
duplicate or override these rules elsewhere.
EOF
    created_structure=true
  fi

  # Copy workflow files from template repo if they don't exist
  if [ ! -f ".github/workflows/pr-automation.yml" ] && [ -f "$TEMPLATE_DIR/.github/workflows/pr-automation.yml" ]; then
    echo "   📝 Creating pr-automation.yml..."
    cp "$TEMPLATE_DIR/.github/workflows/pr-automation.yml" ".github/workflows/pr-automation.yml"
    created_structure=true
  fi

  if [ ! -f ".github/workflows/unified-automation.yml" ] && [ -f "$TEMPLATE_DIR/.github/workflows/unified-automation.yml" ]; then
    echo "   📝 Creating unified-automation.yml..."
    cp "$TEMPLATE_DIR/.github/workflows/unified-automation.yml" ".github/workflows/unified-automation.yml"
    created_structure=true
  fi

  # Create basic labeler.yml if it doesn't exist
  if [ ! -f ".github/labeler.yml" ]; then
    echo "   📝 Creating labeler.yml..."
    cat >.github/labeler.yml <<'EOF'
# file: .github/labeler.yml
# version: 1.0.0
# guid: 5a6b7c8d-9e0f-1234-5678-90abcdef1234

# Documentation
documentation:
  - changed-files:
    - any-glob-to-any-file:
      - '**/*.md'
      - 'docs/**/*'

# Configuration
configuration:
  - changed-files:
    - any-glob-to-any-file:
      - '**/*.yml'
      - '**/*.yaml'
      - '**/*.json'
      - '**/*.toml'
      - '**/*.ini'
      - '**/*.conf'
      - '**/Dockerfile*'
      - '**/.env*'

# Scripts
scripts:
  - changed-files:
    - any-glob-to-any-file:
      - '**/*.sh'
      - '**/*.py'
      - 'scripts/**/*'

# GitHub Actions
github-actions:
  - changed-files:
    - any-glob-to-any-file:
      - '.github/workflows/**/*'
      - '.github/actions/**/*'

# Dependencies
dependencies:
  - changed-files:
    - any-glob-to-any-file:
      - '**/go.mod'
      - '**/go.sum'
      - '**/package.json'
      - '**/package-lock.json'
      - '**/yarn.lock'
      - '**/requirements.txt'
      - '**/Pipfile*'
      - '**/poetry.lock'
      - '**/pyproject.toml'

# Security
security:
  - changed-files:
    - any-glob-to-any-file:
      - '**/.github/workflows/**'
      - '**/Dockerfile*'
      - '**/*security*'
      - '**/*auth*'
      - '**/*secret*'
EOF
    created_structure=true
  fi

  # Create issue templates
  if [ ! -f ".github/ISSUE_TEMPLATE/bug_report.yml" ]; then
    echo "   📝 Creating bug report template..."
    mkdir -p .github/ISSUE_TEMPLATE
    cat >.github/ISSUE_TEMPLATE/bug_report.yml <<'EOF'
name: Bug Report
description: File a bug report to help us improve
title: "bug: [Brief description]"
labels: ["bug", "needs-triage"]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for taking the time to fill out this bug report!

  - type: textarea
    id: what-happened
    attributes:
      label: What happened?
      description: Also tell us, what did you expect to happen?
      placeholder: Tell us what you see!
    validations:
      required: true

  - type: textarea
    id: steps
    attributes:
      label: Steps to reproduce
      description: How can we reproduce this issue?
      placeholder: |
        1. Go to '...'
        2. Click on '....'
        3. Scroll down to '....'
        4. See error
    validations:
      required: true

  - type: textarea
    id: environment
    attributes:
      label: Environment
      description: What environment are you running?
      placeholder: |
        - OS: [e.g. macOS 12.0]
        - Browser: [e.g. chrome, safari]
        - Version: [e.g. 22]
    validations:
      required: false

  - type: textarea
    id: logs
    attributes:
      label: Relevant log output
      description: Please copy and paste any relevant log output. This will be automatically formatted into code, so no need for backticks.
      render: shell
EOF
    created_structure=true
  fi

  if [ ! -f ".github/ISSUE_TEMPLATE/feature_request.yml" ]; then
    echo "   📝 Creating feature request template..."
    cat >.github/ISSUE_TEMPLATE/feature_request.yml <<'EOF'
name: Feature Request
description: Suggest an idea for this project
title: "feat: [Brief description]"
labels: ["enhancement", "needs-triage"]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for suggesting a new feature!

  - type: textarea
    id: problem
    attributes:
      label: Problem Description
      description: Is your feature request related to a problem? Please describe.
      placeholder: A clear and concise description of what the problem is. Ex. I'm always frustrated when [...]
    validations:
      required: true

  - type: textarea
    id: solution
    attributes:
      label: Proposed Solution
      description: Describe the solution you'd like
      placeholder: A clear and concise description of what you want to happen.
    validations:
      required: true

  - type: textarea
    id: alternatives
    attributes:
      label: Alternatives Considered
      description: Describe alternatives you've considered
      placeholder: A clear and concise description of any alternative solutions or features you've considered.
    validations:
      required: false

  - type: textarea
    id: additional-context
    attributes:
      label: Additional Context
      description: Add any other context or screenshots about the feature request here.
    validations:
      required: false
EOF
    created_structure=true
  fi

  # Create pull request template
  if [ ! -f ".github/PULL_REQUEST_TEMPLATE.md" ]; then
    echo "   📝 Creating pull request template..."
    cat >.github/PULL_REQUEST_TEMPLATE.md <<'EOF'
<!-- file: .github/PULL_REQUEST_TEMPLATE.md -->
<!-- version: 1.0.0 -->
<!-- guid: 6b7c8d9e-0f12-3456-789a-bcdef0123456 -->

## Summary

Brief overview of the entire PR and its purpose

## Issues Addressed

### type(scope): description (#issue-number)

**Description:** Detailed explanation of what was done for this specific issue

**Files Modified:**

- [`path/to/file1.ext`](./path/to/file1.ext) - Description of changes
- [`path/to/file2.ext`](./path/to/file2.ext) - Description of changes

_Note: Omit issue numbers from section headers if not working on specific issues. Use `type(scope): description` format instead._

## Testing

How the changes were tested (unit tests, integration tests, manual testing)

## Breaking Changes

(If applicable) List any breaking changes and migration steps

## Additional Notes

Any additional context, screenshots, or important information

## Checklist

- [ ] Code follows the style guidelines of this project
- [ ] Self-review of the code has been performed
- [ ] Code has been commented, particularly in hard-to-understand areas
- [ ] Corresponding changes to documentation have been made
- [ ] Changes generate no new warnings
- [ ] Tests have been added that prove the fix is effective or that the feature works
- [ ] New and existing unit tests pass locally with the changes

## Related Issues

Closes #123, #456, #789
EOF
    created_structure=true
  fi

  if [ "$created_structure" = true ]; then
    echo "   ✅ Created .github structure and files"
    ((REPOS_GITHUB_CREATED++))
    return 0
  else
    echo "   ℹ️  .github structure already exists"
    return 1
  fi
}

# Change to the base directory
cd "$BASE_DIR"

# Find all directories that contain .git folders (repositories)
for repo_dir in */; do
  repo_name=$(basename "$repo_dir")

  # Skip if not a git repository
  if [ ! -d "$repo_dir/.git" ]; then
    echo "⏭️  Skipping $repo_name (not a git repository)"
    ((REPOS_SKIPPED++))
    continue
  fi

  echo "📁 Processing repository: $repo_name"
  cd "$repo_dir"

  ((REPOS_PROCESSED++))

  # Create .github structure if needed
  github_created=$(create_github_structure "$repo_name")
  structure_created=$?

  # Check for any changes in .github directory (not just workflows)
  GITHUB_CHANGES=$(git status --porcelain .github/ 2>/dev/null || echo "")

  if [ -z "$GITHUB_CHANGES" ]; then
    echo "   ✅ No .github changes detected"
    cd "$BASE_DIR"
    continue
  fi

  echo "   🔍 Found .github changes:"
  echo "$GITHUB_CHANGES" | sed 's/^/      /'
  ((REPOS_WITH_CHANGES++))

  # Check if unified-automation workflow exists and get its version
  UNIFIED_WORKFLOW=".github/workflows/unified-automation.yml"
  PR_AUTOMATION_WORKFLOW=".github/workflows/pr-automation.yml"

  UNIFIED_VERSION=""
  PR_VERSION=""

  if [ -f "$UNIFIED_WORKFLOW" ]; then
    UNIFIED_VERSION=$(grep "# version:" "$UNIFIED_WORKFLOW" | head -1 | sed 's/.*version: //' | tr -d ' ')
    echo "   📝 unified-automation.yml version: $UNIFIED_VERSION"
  else
    echo "   ⚠️  unified-automation.yml not found"
  fi

  if [ -f "$PR_AUTOMATION_WORKFLOW" ]; then
    PR_VERSION=$(grep "# version:" "$PR_AUTOMATION_WORKFLOW" | head -1 | sed 's/.*version: //' | tr -d ' ')
    echo "   📝 pr-automation.yml version: $PR_VERSION"
  else
    echo "   ⚠️  pr-automation.yml not found"
  fi

  # Stage .github changes
  echo "   📦 Staging .github changes..."
  git add .github/

  # Check if there are actually staged changes
  STAGED_CHANGES=$(git diff --cached --name-only .github/ 2>/dev/null || echo "")

  if [ -z "$STAGED_CHANGES" ]; then
    echo "   ℹ️  No changes to commit after staging"
    cd "$BASE_DIR"
    continue
  fi

  # Create detailed commit message
  echo "   ✍️  Creating commit message..."

  # Count different types of changes
  WORKFLOW_FILES=$(echo "$STAGED_CHANGES" | grep "workflows/" | grep -v "\.backup$" | wc -l | tr -d ' ')
  INSTRUCTION_FILES=$(echo "$STAGED_CHANGES" | grep "instructions/" | wc -l | tr -d ' ')
  TEMPLATE_FILES=$(echo "$STAGED_CHANGES" | grep -E "(ISSUE_TEMPLATE|PULL_REQUEST_TEMPLATE)" | wc -l | tr -d ' ')
  BACKUP_FILES=$(echo "$STAGED_CHANGES" | grep "\.backup$" | wc -l | tr -d ' ')
  OTHER_FILES=$(echo "$STAGED_CHANGES" | grep -v -E "(workflows/|instructions/|TEMPLATE|\.backup$)" | wc -l | tr -d ' ')

  # Determine commit type based on changes
  if [ "$WORKFLOW_FILES" -gt 0 ] || [ "$structure_created" -eq 0 ]; then
    COMMIT_TYPE="feat"
    COMMIT_SCOPE="github"
    COMMIT_DESC="setup complete GitHub automation and structure"
  else
    COMMIT_TYPE="chore"
    COMMIT_SCOPE="github"
    COMMIT_DESC="update GitHub configuration files"
  fi

  # Create commit message
  COMMIT_MSG="$COMMIT_TYPE($COMMIT_SCOPE): $COMMIT_DESC

Set up comprehensive GitHub automation system with unified workflows,
coding instructions, issue templates, and standardized configuration.

Files changed:"

  # Add file details with proper categorization
  while IFS= read -r file; do
    if [[ $file == *".backup"* ]]; then
      COMMIT_MSG="$COMMIT_MSG
- $file - Backup of previous version"
    elif [[ $file == *"workflows/pr-automation.yml" ]]; then
      COMMIT_MSG="$COMMIT_MSG
- $file - Unified PR automation workflow v2.0.0"
    elif [[ $file == *"workflows/unified-automation.yml" ]]; then
      COMMIT_MSG="$COMMIT_MSG
- $file - Central automation orchestrator"
    elif [[ $file == *"workflows/"* ]]; then
      COMMIT_MSG="$COMMIT_MSG
- $file - Workflow configuration updates"
    elif [[ $file == *"instructions/"* ]]; then
      COMMIT_MSG="$COMMIT_MSG
- $file - Copilot/AI coding instructions"
    elif [[ $file == *"copilot-instructions.md" ]]; then
      COMMIT_MSG="$COMMIT_MSG
- $file - Copilot system documentation"
    elif [[ $file == *"AGENTS.md" ]]; then
      COMMIT_MSG="$COMMIT_MSG
- $file - AI agent configuration pointer"
    elif [[ $file == *"labeler.yml" ]]; then
      COMMIT_MSG="$COMMIT_MSG
- $file - Automatic issue/PR labeling rules"
    elif [[ $file == *"ISSUE_TEMPLATE"* ]]; then
      COMMIT_MSG="$COMMIT_MSG
- $file - GitHub issue template"
    elif [[ $file == *"PULL_REQUEST_TEMPLATE"* ]]; then
      COMMIT_MSG="$COMMIT_MSG
- $file - GitHub pull request template"
    else
      COMMIT_MSG="$COMMIT_MSG
- $file - GitHub configuration"
    fi
  done <<<"$STAGED_CHANGES"

  # Add summary information
  COMMIT_MSG="$COMMIT_MSG

Summary:
- Workflow files: $WORKFLOW_FILES
- Instruction files: $INSTRUCTION_FILES
- Template files: $TEMPLATE_FILES
- Backup files: $BACKUP_FILES
- Other GitHub files: $OTHER_FILES
- Repository: $repo_name"

  if [ "$structure_created" -eq 0 ]; then
    COMMIT_MSG="$COMMIT_MSG
- Created complete .github structure"
  fi

  if [ -n "$UNIFIED_VERSION" ]; then
    COMMIT_MSG="$COMMIT_MSG
- Unified automation version: $UNIFIED_VERSION"
  fi

  if [ -n "$PR_VERSION" ]; then
    COMMIT_MSG="$COMMIT_MSG
- PR automation version: $PR_VERSION"
  fi

  # Commit the changes
  echo "   💾 Committing GitHub setup..."
  echo "$COMMIT_MSG" | git commit -F -

  if [ $? -eq 0 ]; then
    echo "   ✅ Successfully committed GitHub setup"
    ((REPOS_COMMITTED++))
  else
    echo "   ❌ Failed to commit changes"
  fi

  echo ""
  cd "$BASE_DIR"
done

# Final summary
echo "🎉 GitHub setup process completed!"
echo ""
echo "📊 Summary:"
echo "   • Repositories processed: $REPOS_PROCESSED"
echo "   • Repositories with changes: $REPOS_WITH_CHANGES"
echo "   • Repositories committed: $REPOS_COMMITTED"
echo "   • Repositories skipped: $REPOS_SKIPPED"
echo "   • New .github structures created: $REPOS_GITHUB_CREATED"
echo ""

if [ $REPOS_COMMITTED -gt 0 ]; then
  echo "✅ Successfully set up GitHub automation in $REPOS_COMMITTED repositories"
  echo ""
  echo "🚀 Next steps:"
  echo "   1. Review the commits in each repository"
  echo "   2. Push the changes: git push"
  echo "   3. Monitor the new workflows and automation in action"
  echo "   4. Update any repo-specific configurations as needed"
else
  echo "ℹ️  No repositories required GitHub setup updates"
fi

echo ""
echo "📁 Created complete .github structure with:"
echo "   • Unified automation workflows (pr-automation.yml, unified-automation.yml)"
echo "   • Copilot/AI coding instructions system"
echo "   • Issue and pull request templates"
echo "   • Automatic labeling configuration"
echo "   • Agent configuration pointers"
echo ""
echo "🏁 Done!"
