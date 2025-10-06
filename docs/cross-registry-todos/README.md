<!-- file: docs/cross-registry-todos/README.md -->
<!-- version: 1.0.0 -->
<!-- guid: a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d -->

# Cross-Registry Workflow Improvement Tasks

This directory contains detailed, actionable tasks for improving GitHub Actions workflows across the
`ghcommon` and `ubuntu-autoinstall-agent` repositories.

## Overview

These tasks address critical issues identified in the workflow infrastructure:

1. **YAML Syntax Issues** - Fix trailing slashes in cache restore-keys
2. **GitHub Packages Integration** - Ensure all release workflows publish to GitHub Packages
3. **CI Workflow Consolidation** - Merge duplicate CI implementations into unified reusable workflow
4. **Repository Config Integration** - Make workflows read from repository-config.yml
5. **Script Extraction** - Move inline scripts to separate files for maintainability

## Task Organization

Each task is:

- **Idempotent**: Can be run multiple times without side effects
- **Independent**: Can be completed without dependencies on other tasks
- **Detailed**: Includes complete code examples, file paths, and validation steps
- **Repository-Specific**: Clearly indicates which repository to work in

## Task Files

### Critical Fixes (Priority 1)

- `task-01-fix-yaml-syntax.md` - Fix YAML syntax errors in release-rust.yml
- `task-02-docker-packages.md` - Verify and enhance Docker image publishing (already working)

### GitHub Packages Publishing (Priority 2)

- `task-03-rust-packages.md` - Add Rust crate publishing to GitHub Packages
- `task-04-go-packages.md` - Add Go module/binary publishing to GitHub Packages
- `task-05-python-packages.md` - Add Python package publishing to GitHub Packages
- `task-06-frontend-packages.md` - Add npm package publishing to GitHub Packages
- `task-07-protobuf-packages.md` - Add protobuf artifact publishing to GitHub Packages

### CI Workflow Modernization (Priority 3)

- `task-08-analyze-ci-workflows.md` - Comprehensive analysis of CI implementations
- `task-09-consolidate-ci-workflows.md` - Merge CI workflows into reusable implementation
- `task-10-update-ci-callers.md` - Update both repositories to use consolidated CI

### Repository Config Integration (Priority 4)

- `task-11-config-loader-script.md` - Create repository-config.yml loader utility
- `task-12-integrate-reusable-ci.md` - Add config support to reusable-ci.yml
- `task-13-integrate-release-workflows.md` - Add config support to all release workflows
- `task-14-integrate-protobuf-workflow.md` - Add config support to protobuf workflow

### Script Extraction (Priority 5)

- `task-15-extract-ci-scripts.md` - Extract CI workflow inline scripts
- `task-16-extract-release-scripts.md` - Extract release workflow inline scripts
- `task-17-create-script-library.md` - Organize extracted scripts with documentation

### Testing and Validation (Priority 6)

- `task-18-test-package-publishing.md` - Test all GitHub Packages publishing
- `task-19-test-ci-workflows.md` - Test consolidated CI workflows
- `task-20-validate-config-integration.md` - Validate repository-config.yml integration

## Execution Guidelines

### Before Starting Any Task

1. **Read the entire task file completely**
2. **Check current state** - Many tasks include validation commands to check if work is needed
3. **Backup if needed** - Some tasks modify critical workflow files
4. **Verify repository** - Ensure you're in the correct repository (ghcommon vs
   ubuntu-autoinstall-agent)

### Task Execution Pattern

Each task follows this structure:

```markdown
## Task Overview

- What needs to be done
- Why it matters
- Expected outcome

## Prerequisites

- Required tools/access
- Knowledge requirements
- Repository state checks

## Current State Analysis

- Commands to check current state
- What to look for
- Decision points

## Implementation Steps

1. Detailed step-by-step instructions
2. Complete code examples
3. File paths and line numbers
4. Expected outputs

## Validation

- How to test the changes
- Expected results
- Rollback procedures

## Integration Notes

- How this affects other systems
- What to communicate
- Follow-up tasks
```

### Success Criteria

A task is complete when:

- ✅ All implementation steps executed successfully
- ✅ Validation commands pass
- ✅ Workflow runs successfully in GitHub Actions
- ✅ Documentation updated (if applicable)
- ✅ Changes committed with conventional commit message

### Commit Message Format

All commits must use conventional commit format:

```
type(scope): brief description

Detailed explanation of changes made.

Related to task: task-XX-name
```

Examples:

```
fix(workflows): remove trailing slashes from cache restore-keys

Fixed YAML syntax errors in release-rust.yml where restore-keys
had trailing dashes causing cache mismatches.

Related to task: task-01-fix-yaml-syntax
```

```
feat(release): add Rust crate publishing to GitHub Packages

Implemented cargo publish workflow step in release-rust.yml to
publish crates to GitHub Packages registry. Includes authentication,
version detection, and error handling.

Related to task: task-03-rust-packages
```

## Progress Tracking

Create a checklist in your workspace:

```markdown
- [ ] Task 01: Fix YAML Syntax
- [ ] Task 02: Docker Packages (verify)
- [ ] Task 03: Rust Packages
- [ ] Task 04: Go Packages
- [ ] Task 05: Python Packages
- [ ] Task 06: Frontend Packages
- [ ] Task 07: Protobuf Packages
- [ ] Task 08: Analyze CI Workflows
- [ ] Task 09: Consolidate CI Workflows
- [ ] Task 10: Update CI Callers
- [ ] Task 11: Config Loader Script
- [ ] Task 12: Integrate Reusable CI Config
- [ ] Task 13: Integrate Release Config
- [ ] Task 14: Integrate Protobuf Config
- [ ] Task 15: Extract CI Scripts
- [ ] Task 16: Extract Release Scripts
- [ ] Task 17: Create Script Library
- [ ] Task 18: Test Package Publishing
- [ ] Task 19: Test CI Workflows
- [ ] Task 20: Validate Config Integration
```

## Repository Context

### ghcommon Repository

- **Purpose**: Central infrastructure hub for reusable workflows and scripts
- **Key Files**:
  - `.github/workflows/reusable-*.yml` - Reusable workflow definitions
  - `.github/repository-config.yml` - Unified configuration schema
  - `scripts/` - Python automation tools
- **Workflow**: Changes here propagate to other repositories via sync

### ubuntu-autoinstall-agent Repository

- **Purpose**: Ubuntu autoinstall automation tool (Rust application)
- **Key Files**:
  - `.github/workflows/ci.yml` - Full CI implementation
  - `.github/workflows/release.yml` - Release orchestrator
  - `Cargo.toml` - Rust project configuration
- **Workflow**: Consumes reusable workflows from ghcommon

## Common Patterns

### Checking Current State

```bash
# Always check before modifying
cd /path/to/repository
git status
git diff

# Verify workflow syntax
actionlint .github/workflows/*.yml

# Check for specific patterns
grep -n "pattern" .github/workflows/file.yml
```

### Testing Workflow Changes

```bash
# Local validation
actionlint .github/workflows/changed-file.yml

# Commit and push to trigger
git add .github/workflows/changed-file.yml
git commit -m "type(scope): description"
git push

# Monitor workflow
gh run list --workflow=workflow-name
gh run view --log
```

### Rollback Procedure

```bash
# If something goes wrong
git log --oneline -5
git revert <commit-hash>
git push

# Or reset if not pushed
git reset --hard HEAD~1
```

## Getting Help

### Resources

- GitHub Actions Documentation: https://docs.github.com/en/actions
- GitHub Packages Documentation: https://docs.github.com/en/packages
- Workflow Syntax: https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions

### Debug Commands

```bash
# View workflow logs
gh run list --limit 5
gh run view <run-id> --log

# Check workflow syntax
actionlint .github/workflows/*.yml

# Validate YAML
yamllint .github/workflows/*.yml

# Test workflow locally (if using act)
act -l
act pull_request
```

## Notes for AI Agents

When working on these tasks:

1. **Always verify current state first** - Use the "Current State Analysis" section
2. **Make changes incrementally** - Commit after each logical change
3. **Test after each change** - Don't stack multiple changes without testing
4. **Follow conventions** - Use existing patterns from the repository
5. **Update version headers** - Increment version numbers in modified files
6. **Document decisions** - Add comments explaining complex logic
7. **Use ENV variables** - Don't use GitHub context variables directly in scripts
8. **Respect the 10-input limit** - workflow_dispatch can only have 10 inputs max

## File Version Header Requirements

All modified files MUST have updated headers:

```yaml
# file: .github/workflows/example.yml
# version: 1.2.0  # Increment this!
# guid: unchanged-guid-here
```

Version increment rules:

- **Patch (x.y.Z)**: Bug fixes, typos, minor changes
- **Minor (x.Y.z)**: New features, significant additions
- **Major (X.y.z)**: Breaking changes, structural overhauls

## Contact and Support

For questions or issues with these tasks:

1. Review the specific task file completely
2. Check the "Common Issues" section in the task
3. Verify you're in the correct repository
4. Ensure prerequisites are met
5. Check GitHub Actions logs for detailed error messages

---

**Ready to start?** Begin with `task-01-fix-yaml-syntax.md` - it's the quickest win with immediate
impact.
