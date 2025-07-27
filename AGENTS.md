<!-- file: AGENTS.md -->
<!-- version: 2.0.0 -->
<!-- guid: 2e7c1a4b-5d3f-4b8c-9e1f-7a6b2c3d4e5f -->

# AGENTS.md

> **NOTE:** This is a pointer file. All detailed Copilot, agent, and workflow
> instructions are in the [.github/](.github/) directory.

## 🚨 CRITICAL: Documentation Update Protocol

**NEVER edit markdown files directly. ALWAYS use the documentation update
system:**

1. **Create GitHub Issue First** (if none exists):

   ```bash
   ./scripts/create-issue-update.sh "Update [filename] - [description]" "Detailed description of what needs to be updated"
   ```

2. **Create Documentation Update**:

   ```bash
   # Basic modes (append/prepend/replace)
   ./scripts/create-doc-update.sh [filename] "[content]" [mode] --issue [issue-number]

   # For precise insertion, use 'after' mode with specific text to insert after
   ./scripts/create-doc-update.sh README.md "New content here" after --after "## Installation" --issue [issue-number]

   # For section replacement
   ./scripts/create-doc-update.sh README.md "Updated content" replace-section --section "Usage" --issue [issue-number]
   ```

3. **⚠️ CRITICAL - "after" mode requirements**:
   - **ALWAYS specify `--after "exact text"`** when using `after` mode
   - The text in `--after` must exist exactly in the target file
   - Example: `--after "## Installation"` will insert content after that heading
   - **Malformed JSON error = missing `--after` parameter**

4. **Link to Issue**: Every documentation change MUST reference a GitHub issue
   for tracking and context.

**Common Modes:**

- `append` - Add to end of file
- `prepend` - Add to beginning of file
- `after` - Insert after specific text (REQUIRES `--after "text"`)
- `replace-section` - Replace entire section (REQUIRES `--section "name"`)
- `changelog-entry` - Add changelog entry
- `task-add` - Add TODO task

**Failure to follow this protocol will result in workflow conflicts and lost
changes.**

## Key Copilot/Agent Documents

- [Copilot Instructions](.github/copilot-instructions.md)
- [Commit Message Standards](.github/commit-messages.md)
- [Pull Request Description Guidelines](.github/pull-request-descriptions.md)
- [Code Review Guidelines](.github/review-selection.md)
- [Test Generation Guidelines](.github/test-generation.md)
- [Security Guidelines](.github/security-guidelines.md)
- [Repository Setup Guide](.github/repository-setup.md)
- [Workflow Usage](.github/workflow-usage.md)
- [All Code Style Guides](.github/)

> For any agent, Copilot, or workflow task, **always refer to the above files.**
