<!-- file: AGENTS.md -->
<!-- version: 1.1.0 -->
<!-- guid: 2e7c1a4b-5d3f-4b8c-9e1f-7a6b2c3d4e5f -->

# AGENTS.md

---

## 0. Creating GitHub Issues via Script (v1.1.0)

- **All new GitHub issues, comments, updates, and closes must be created by generating a JSON file using the `scripts/create-issue-update.sh` script.**
- Do **not** create or edit `.github/issue-updates/*.json` files by hand. Always use the script to ensure GUID uniqueness and correct formatting.
- The script generates a random GUID and legacy GUID, and places the JSON file in `.github/issue-updates/`.
- **Usage examples:**

  ```bash
  # Create a new issue
  ./scripts/create-issue-update.sh create "Issue Title" "Issue body" "label1,label2"

  # Update an existing issue
  ./scripts/create-issue-update.sh update 123 "Updated body" "label1,label2"

  # Add a comment to an issue
  ./scripts/create-issue-update.sh comment 123 "Comment text"

  # Close an issue
  ./scripts/create-issue-update.sh close 123 "completed"
  ```

- The script will:
  - Ensure the `.github/issue-updates/` directory exists
  - Generate a unique GUID and legacy GUID for each file
  - Check for GUID collisions
  - Output a JSON file with the correct structure for the unified issue management workflow
- **Best practices:**
  - Use clear, concise titles and bodies
  - Use comma-separated labels (no spaces)
  - Always check the script output for success and file path
  - Do not manually edit or move generated files
  - Let the workflow process and archive files as needed
- For more details, see the script header in [`scripts/create-issue-update.sh`](scripts/create-issue-update.sh)

---

## 1. General Agent Workflow

- The user will provide a task.
- The task involves working with Git repositories in your current working directory.
- Wait for all terminal commands to be completed (or terminate them) before finishing.

### Git Instructions

- Use git to commit your changes.
- If pre-commit fails, fix issues and retry.
- Check git status to confirm your commit. You must leave your worktree in a clean state.

---

## 2. AGENTS.md File Policy

- AGENTS.md files may appear anywhere in the container or repo. Their scope is the entire directory tree rooted at their location.
- For every file you touch, you must obey instructions in any AGENTS.md file whose scope includes that file.
- More deeply nested AGENTS.md files take precedence in case of conflicts.
- Direct user/system instructions always take precedence over AGENTS.md.
- If AGENTS.md includes programmatic checks, you MUST run them and validate that they pass after all code changes.

---

## 3. Citations Policy

- If you browse files or use terminal commands, you must add citations to the final response (not the PR body) where relevant.
- **Citations reference file paths and terminal outputs:**

  1. `【F:<file_path>†L<line_start>(-L<line_end>)?】` for file paths
  2. `【<chunk_id>†L<line_start>(-L<line_end>)?】` for terminal output

- Ensure line numbers are correct and directly relevant.
- Do not cite empty lines or previous PR diffs/comments.
- Prefer file citations unless terminal output is directly relevant.
- For PR creation, use file citations in the summary and terminal citations in the testing section.

---

## 4. Code Style Guidelines

### 4.1 Go

- Use `gofmt` or `go fmt` to format code
- Tabs for indentation, line length <100 chars
- Package names: short, lowercase, no underscores
- Interface names: -er suffix for actions
- Variable/function names: MixedCaps, not underscores
- Exported names: Capitalized; unexported: lowercase
- Acronyms all caps (e.g., HTTPServer)
- Group imports: stdlib, third-party, project
- All exported declarations must have doc comments
- Always check errors, return errors (not panic)
- Early returns to reduce nesting
- Defer file/resource closing
- Use context for cancellation/deadlines
- Keep functions short/focused
- Prefer value receivers unless mutation is needed
- Use channels for concurrency, avoid shared memory

### 4.2 Python

- 4 spaces for indentation, no tabs
- Max line length: 80
- Import order: stdlib, third-party, app-specific
- One import per line, no wildcards
- Naming: `module_name`, `ClassName`, `method_name`, `CONSTANT_NAME`, `_private_attribute`
- Use docstrings for all public modules, functions, classes, methods
- Follow PEP 8
- Use type hints where applicable
- Prefer comprehensions over loops where readable

### 4.3 TypeScript/JavaScript

- 2 spaces for indentation
- Use semicolons
- Prefer `const` over `let`, avoid `var`
- PascalCase for classes, camelCase for functions/variables
- UPPER_SNAKE_CASE for constants
- Always use explicit type annotations in TypeScript
- Prefer interfaces over types for object shapes
- Use async/await over promises

### 4.4 Markdown

- Use consistent heading hierarchy
- Fenced code blocks with language
- Line length: 80-100
- Use meaningful link text
- Use `-` for bullets
- Blank lines around code blocks and headers

---

## 5. Commit Message Standards

- Use [Conventional Commits](https://www.conventionalcommits.org/)
- Format: `<type>[optional scope]: <description>`
- Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert
- **REQUIRED:** Always include a "Files changed:" section in the commit body with summary and links:

  ```markdown
  Files changed:

  - Added feature: [src/feature.js](src/feature.js)
  - Updated tests: [test/feature.test.js](test/feature.test.js)
  ```

- Use imperative present tense ("add" not "added")
- No period at end, keep under 50 chars
- Include motivation and contrast with previous behavior in body
- Reference real issues only: `Fixes #123` or `Closes #456`
- No commit should be submitted without file change documentation

---

## 6. Pull Request Description Guidelines

- Use this template:

  ```markdown
  ## Description

  [Concise overview of the changes]

  ## Motivation

  [Why these changes were necessary]

  ## Changes

  [Detailed list of changes made]

  ## Testing

  [How the changes were tested]

  ## Screenshots

  [If applicable]

  ## Related Issues

  [Links to related tickets/issues]
  ```

- Be concise, focus on what/why
- Use bullet points for changes
- Describe how changes were tested
- Link to all relevant issues/tickets
- For breaking changes, include a "Breaking Changes" section

---

## 7. Code Review Guidelines

- Review focus areas (in order):

  1. Correctness
  2. Security
  3. Performance
  4. Readability
  5. Maintainability
  6. Test Coverage

- Be specific about what needs changing and why
- Provide constructive feedback with examples
- Differentiate between required changes and suggestions
- Focus on critical issues first
- For UI, check accessibility/responsiveness
- For API, verify docs/versioning
- For DB, review migrations/data integrity
- For security, apply extra scrutiny
- For performance, request benchmarks

---

## 8. Test Generation Guidelines

- Use Arrange-Act-Assert structure:

  ```markdown
  [Setup] - Prepare the test environment and inputs
  [Exercise] - Execute the functionality being tested
  [Verify] - Check that the results match expectations
  [Teardown] - Clean up any resources (if needed)
  ```

- Test naming: `test[UnitOfWork_StateUnderTest_ExpectedBehavior]`
- Test types: Unit, Integration, Functional, Performance, Security, Accessibility
- Test one specific behavior per test case
- Mock external dependencies
- Cover happy paths and edge cases
- Use clear assertions with meaningful messages
- Group tests by feature/component
- Avoid flaky tests, excessive mocking, and testing implementation details

---

## 9. Documentation & File Responsibilities

- **README.md**: Repo intro, setup, usage, critical info
- **TODO.md**: Roadmap, planning, architecture, diagrams
- **CHANGELOG.md**: Version info, release notes, breaking changes, features, bug fixes

---

## 10. Security & Best Practices

- Avoid hardcoding sensitive info (API keys, passwords, tokens)
- Use proper error handling with meaningful messages
- Validate inputs (sanitize file paths, validate formats)
- Consider performance implications
- Look for injection vulnerabilities
- Use secure defaults for file permissions and temp files
- Review file handling security (path traversal, file size limits)
- Verify secure handling of sensitive data

---

## 11. Version Control Standards

- Write clear commit messages
- Keep PRs focused on a single feature/fix
- Reference issue numbers in commits/PRs (only real issues)
- Use conventional commit format
- Include comprehensive file change documentation in all commits
- Use semantic versioning for releases
- Tag releases appropriately

---

## 12. Project-Specific Guidelines

- Import from project modules, don't duplicate functionality
- Respect established architecture patterns
- Before suggesting one-off commands, check for a defined task in tasks.json
- Use meaningful variable names
- Keep functions small and focused
- Use the existing CLI/web UI framework patterns for new commands/handlers
- Use appropriate logging levels and structured logging

---

## 13. Codex Agent-Specific Instructions

- All references to "copilot" in prior instructions are replaced with "codex" for this repository.
- All code, documentation, and process instructions in this file are mandatory for codex agents.
- If you find programmatic checks in AGENTS.md, you must run them and validate they pass after your changes.

---

## 14. Includes

This file contains a basic version of the more detailed following files, import them as needed:

- .github/commit-messages.md
- .github/copilot-instructions.md (as codex-instructions)
- .github/pull-request-descriptions.md
- .github/review-selection.md
- .github/test-generation.md
- All code style guides (Go, Python, TypeScript, JavaScript, Markdown)

---
