<!-- file: docs/PROMPT_CATEGORIZATION.md -->
<!-- version: 1.0.0 -->
<!-- guid: 3f4a5b6c-7d8e-9f0a-1b2c-3d4e5f6a7b8c -->
<!-- last-edited: 2026-01-19 -->

# Prompt Categorization Report

This document provides a comprehensive analysis of all prompt files in `.github/prompts/` and
recommendations for maintaining the prompt system.

## Summary Statistics

- **Total Prompt Files**: 20
- **KEEP (as-is)**: 19 files
- **REVISE (needs updates)**: 1 file
- **REMOVE (obsolete)**: 0 files
- **ADD (recommended new prompts)**: 4 suggestions

## Detailed Categorization

### KEEP - Prompts That Are Good As-Is (19 files)

These prompts are clear, useful, and have valid references to documentation. No changes needed.

#### Core Development Prompts (10 files)

1. **ai-architecture.prompt.md** ✅
   - Purpose: Architecture review guidance
   - Status: Clear and concise
   - References: general-coding.instructions.md

2. **ai-refactor.prompt.md** ✅
   - Purpose: Code refactoring guidance
   - Status: Clear and concise
   - References: general-coding.instructions.md

3. **bug-report.prompt.md** ✅
   - Purpose: Bug report generation
   - Status: Clear structure and guidance
   - References: general-coding.instructions.md

4. **code-review.prompt.md** ✅
   - Purpose: Code review guidance
   - Status: Good focus on correctness, security, performance, readability
   - References: general-coding.instructions.md, review-selection.md

5. **commit-message.prompt.md** ✅
   - Purpose: Conventional commit message generation
   - Status: Essential and well-referenced
   - References: commit-messages.md

6. **documentation.prompt.md** ✅
   - Purpose: Documentation generation
   - Status: Clear language-appropriate guidance
   - References: general-coding.instructions.md

7. **feature-request.prompt.md** ✅
   - Purpose: Feature request generation
   - Status: Good structure with acceptance criteria
   - References: general-coding.instructions.md

8. **pull-request.prompt.md** ✅
   - Purpose: PR description generation
   - Status: Well-structured with template reference
   - References: pull-request-descriptions.md

9. **security-review.prompt.md** ✅
   - Purpose: Security review guidance
   - Status: Comprehensive security focus
   - References: general-coding.instructions.md

10. **test-generation.prompt.md** ✅
    - Purpose: Test generation using AAA pattern
    - Status: Clear and language-agnostic
    - References: general-coding.instructions.md

#### Release Management Prompts (3 files)

11. **ai-changelog.prompt.md** ✅
    - Purpose: Changelog generation
    - Status: Good for release management
    - References: general-coding.instructions.md

12. **ai-release-notes.prompt.md** ✅
    - Purpose: Release notes generation
    - Status: Well-organized by type
    - References: general-coding.instructions.md

13. **ai-roadmap.prompt.md** ✅
    - Purpose: Roadmap generation
    - Status: Good prioritization guidance
    - References: general-coding.instructions.md

#### Project Management Prompts (3 files)

14. **ai-contribution.prompt.md** ✅
    - Purpose: Contribution guidelines generation
    - Status: Good for onboarding
    - References: general-coding.instructions.md

15. **ai-issue-triage.prompt.md** ✅
    - Purpose: Issue categorization and prioritization
    - Status: Clear triage guidance
    - References: general-coding.instructions.md

16. **onboarding.prompt.md** ✅
    - Purpose: Onboarding documentation
    - Status: Good for new contributors
    - References: general-coding.instructions.md

#### Migration & Maintenance Prompts (3 files)

17. **ai-migration.prompt.md** ✅
    - Purpose: Migration planning for instructions/prompts/workflows
    - Status: Very relevant, comprehensive approach
    - References: general-coding.instructions.md

18. **ai-rebase-context.md** ✅
    - Purpose: ghcommon-specific repository context for conflict resolution
    - Status: Well-maintained, repository-specific details
    - Note: This is the actual context file, not a template

19. **ai-rebase-system.prompt.md** ✅
    - Purpose: Expert Git conflict resolution
    - Status: Expert-level guidance, preserves intent
    - References: ai-rebase-context.template.md

### REVISE - Prompts Needing Updates (1 file)

#### 1. ai-rebase-context.template.md 🔧

**Current Status**: Outdated file location references and missing tool information

**Issues Identified**:

- References should mention AGENTS.md and CLAUDE.md are in repository root (not .github/)
- Should mention copilot-agent-util Rust utility for safe git operations
- Should reference direct-edit documentation workflow (no doc-update scripts)
- Template comments should guide users to update for their repository

**Recommended Changes**:

1. Add note about AGENTS.md and CLAUDE.md location in root
2. Add note about copilot-agent-util tool availability and benefits
3. Add note about direct-edit workflow vs deprecated doc-update scripts
4. Update "Key Files to Reference" section template to include AGENTS.md and CLAUDE.md
5. Update version to 1.1.0 after changes

### REMOVE - Obsolete Prompts (0 files)

No prompts are obsolete or redundant. The current set is well-curated and useful.

### ADD - Recommended New Prompts (4 suggestions)

#### 1. workflow-debugging.prompt.md (Recommended)

**Purpose**: Guide for debugging GitHub Actions workflow failures

**Rationale**: ghcommon is a workflow infrastructure repository with extensive GitHub Actions usage.
A dedicated prompt for workflow debugging would be valuable.

**Suggested Content**:

- Analyze workflow logs and identify failure patterns
- Common workflow error categories (permissions, dependencies, syntax, etc.)
- Reference workflow-debugger.py tool in scripts/
- Generate actionable remediation steps

#### 2. super-linter-config.prompt.md (Recommended)

**Purpose**: Guide for configuring and troubleshooting Super Linter

**Rationale**: Super Linter configuration is complex with many gotchas. A dedicated prompt would
help maintain consistency across repositories.

**Suggested Content**:

- Explain _\_CONFIG_FILE vs _\_RULES variables
- Guide for setting up linter configs in repository root or .github/linters/
- Never use symlinks approach (configs should be regular files)
- Reference super-linter configuration documentation
- Note: ghcommon uses root directory for all linter configs

#### 3. multi-repo-sync.prompt.md (Recommended)

**Purpose**: Guide for synchronizing files across multiple repositories

**Rationale**: ghcommon manages configurations for multiple repositories. A prompt for sync
operations would ensure consistency.

**Suggested Content**:

- Reference intelligent_sync_to_repos.py script
- Explain file versioning requirements
- Guide for VS Code Copilot symlink creation
- Handle repository-specific exclusions

#### 4. file-header-maintenance.prompt.md (Optional)

**Purpose**: Guide for maintaining file headers (path, version, GUID)

**Rationale**: File headers are critical to the repository system but can be error-prone. A
dedicated prompt could help maintain consistency.

**Suggested Content**:

- Reference general-coding.instructions.md header requirements
- Explain semantic versioning (patch/minor/major)
- Handle shebang compatibility for scripts
- Different header formats by file type

## Analysis Summary

### Strengths of Current Prompt System

1. **Comprehensive Coverage**: 20 prompts cover development, release management, project management,
   and maintenance
2. **Consistent Structure**: All prompts follow similar format with frontmatter and references
3. **Valid References**: All prompts reference existing documentation correctly
4. **Well-Organized**: Clear naming convention and logical grouping
5. **Maintained**: ai-rebase-context.md is regularly updated with repository-specific details

### Areas for Improvement

1. **File Location Updates**: One template needs updating for new AGENTS.md/CLAUDE.md locations
2. **Tool Awareness**: Prompts should mention copilot-agent-util where relevant
3. **Specialized Needs**: Could add prompts for workflow debugging, super-linter config, and
   multi-repo sync

### Recommendations

#### Immediate Actions (Priority)

1. ✅ Update ai-rebase-context.template.md with correct file locations and tool references
2. ✅ Document this categorization for future reference

#### Future Enhancements (Optional)

1. Consider adding workflow-debugging.prompt.md when workflow-debugger.py is mature
2. Consider adding super-linter-config.prompt.md after super-linter testing is complete (Tasks
   14-23)
3. Consider adding multi-repo-sync.prompt.md after MANUAL_SYNC_PROCESS.md is created (Task 24)
4. Consider adding file-header-maintenance.prompt.md if header issues become common

## Maintenance Guidelines

### When to Add a New Prompt

- Task is performed frequently across multiple repositories
- Task has specific requirements documented elsewhere
- Task benefits from AI agent guidance
- Task is complex enough to warrant dedicated instructions

### When to Revise a Prompt

- Referenced documentation paths change
- New tools or workflows are introduced that affect the task
- User feedback indicates confusion or missing information
- Repository structure changes significantly

### When to Remove a Prompt

- Task is no longer performed
- Prompt is redundant with another prompt
- Documentation has been consolidated elsewhere
- Tool or workflow has been deprecated

## Conclusion

The ghcommon prompt system is **well-maintained and comprehensive**. Only one file requires updates
(ai-rebase-context.template.md), and the system could be enhanced with 3-4 additional prompts as the
repository evolves. The current set of 20 prompts provides excellent coverage for development,
release management, project management, and maintenance tasks.

**Next Steps**:

1. Complete Task 9: Revise ai-rebase-context.template.md
2. Complete Task 10: Document these recommendations (this file)
3. Consider adding new prompts after completing related TODO tasks (workflow debugging after Tasks
   14-23, sync after Task 24)
