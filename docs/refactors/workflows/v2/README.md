<!-- file: docs/refactors/workflows/v2/README.md -->
<!-- version: 1.0.0 -->
<!-- guid: a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d -->
<!-- last-edited: 2026-01-19 -->

# Workflow Refactoring V2 - Documentation Hub

This directory contains the comprehensive plan for refactoring ghcommon workflows to be
config-driven, maintainable, and scalable.

## 📋 Quick Navigation

### Strategic Documents

- [Architecture](architecture.md) - High-level design principles and patterns
- [Version Policy](version-policy.md) - Language version support and deprecation policy

### Phase Implementation Guides

Each phase is **independent and idempotent** - can be worked on in parallel by multiple agents.

- [Phase 0: Foundation](phases/phase-0-foundation.md) - Config validation and shared utilities
- [Phase 1: CI Modernization](phases/phase-1-ci-modernization.md) - Config-driven CI workflows
- [Phase 2: Release Consolidation](phases/phase-2-release-consolidation.md) - Unified release
  workflow
- [Phase 3: Maintenance Automation](phases/phase-3-maintenance-automation.md) - Maintenance &
  security helpers
- [Phase 4: Automation Cleanup](phases/phase-4-automation-cleanup.md) - Issue/PR automation
  consolidation

### Implementation Details

- [Helper Scripts Guide](implementation/helper-scripts.md) - How to write and structure helpers
- [Testing Guide](implementation/testing-guide.md) - Unit and integration test patterns
- [Troubleshooting](implementation/troubleshooting.md) - Common issues and solutions

### Operations

- [Rollback Procedures](operations/rollback-procedures.md) - Emergency recovery steps
- [Monitoring Guide](operations/monitoring.md) - Observability and performance tracking
- [Deprecation Policy](operations/deprecation-policy.md) - Timeline and migration support

### Reference

- [Config Schema](reference/config-schema.md) - repository-config.yml specification
- [Helper API Reference](reference/helper-api.md) - Python helper function documentation
- [Workflow Catalog](reference/workflow-catalog.md) - All available workflows and their purposes

## 🎯 Design Principles

1. **Configuration-Driven**: All behavior controlled by `.github/repository-config.yml`
2. **Python Over Bash**: Maintainable, testable, cross-platform helpers
3. **Independent Tasks**: Each task can be executed independently by parallel agents
4. **Idempotent Operations**: Re-running tasks produces same result (safe for concurrent work)
5. **Version Support**: Latest 2 stable versions of each language (Go 1.23/1.24, Python 3.13/3.14)
6. **Code Style Compliance**: All implementations follow `.github/instructions/*.instructions.md`

## 🚀 Getting Started

### For Implementers

1. Read [Architecture](architecture.md) to understand the system
2. Choose a phase based on priority and your expertise
3. Review the phase-specific guide in `phases/`
4. Follow [Helper Scripts Guide](implementation/helper-scripts.md) for coding standards
5. Write tests following [Testing Guide](implementation/testing-guide.md)
6. Ensure compliance with `.github/instructions/` code style rules

### For Code Agents

Each phase document contains:

- **Independent tasks** - Can be executed in any order
- **Idempotent operations** - Safe to re-run without side effects
- **Complete specifications** - No ambiguity, ready for implementation
- **Verification steps** - How to confirm task completion
- **Code style references** - Links to relevant instruction files

Example task structure:

```markdown
## Task 1.2: Create Config Loader Function

**Dependencies**: None (independent task) **Estimated Time**: 30 minutes **Idempotent**: Yes -
creates file only if missing

**Code Style Requirements**:

- Follow `.github/instructions/python.instructions.md`
- Include file headers per `.github/instructions/general-coding.instructions.md`
- Use type hints per Python style guide

**Implementation**: [detailed steps] **Verification**: [test commands]
```

## 📊 Progress Tracking

Track progress in GitHub Projects or Issues:

- Label each task with its phase (e.g., `phase-0`, `phase-1`)
- Mark tasks as `idempotent` and `independent`
- Link to the specific section in phase documents
- Assign to agents (human or AI) as needed

## 🔗 Key References

### Coding Standards

All code must comply with these instruction files:

- `.github/instructions/general-coding.instructions.md` - Universal standards
- `.github/instructions/python.instructions.md` - Python-specific rules
- `.github/instructions/github-actions.instructions.md` - Workflow standards
- `.github/instructions/test-generation.instructions.md` - Testing requirements

### Language Versions

**Supported Versions** (Latest 2 stable/LTS only):

- **Go**: 1.23, 1.24
- **Python**: 3.13, 3.14
- **Node.js**: 20 LTS, 22 LTS
- **Rust**: Latest stable, Previous stable

See [Version Policy](version-policy.md) for complete details.

## 📅 Timeline

| Phase   | Status      | Target Date | Dependencies                             |
| ------- | ----------- | ----------- | ---------------------------------------- |
| Phase 0 | 🟡 Planning | 2025-10-20  | None                                     |
| Phase 1 | 🟡 Planning | 2025-11-01  | Phase 0 complete                         |
| Phase 2 | ⚪ Pending  | 2025-11-15  | Phase 1 complete                         |
| Phase 3 | ⚪ Pending  | 2025-12-01  | Phase 0 complete (parallel with Phase 2) |
| Phase 4 | ⚪ Pending  | 2025-12-15  | Phase 1, 2, 3 complete                   |

## 🆘 Support

- **Questions**: Open an issue with label `workflow-refactor-v2`
- **Bugs**: File issue with label `workflow-bug` and phase number
- **Suggestions**: Use discussion board or issue with label `workflow-enhancement`

## 📄 Document Conventions

All documents in this directory follow:

- File headers with path, version, GUID
- Semantic versioning for document updates
- Links to code style instruction files where relevant
- Task independence and idempotency clearly marked
- Verification steps for each task

---

**Last Updated**: 2025-10-12 **Document Owner**: Workflow Refactoring Team **Related**: Original
audit in `../workflow-optimization.md`
