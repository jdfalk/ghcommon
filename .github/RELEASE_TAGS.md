# Version Tags Plan

This document outlines the version tags to be created for ghcommon repository.

## Tag Structure

Based on commit analysis from v0.1.0 (Oct 12, 2025) to present (Nov 24, 2025):

### v0.2.0 - Foundation & Phase 0 (Oct 13, 2025)

**Commit:** `70fcd6594172b3137f280ee18fbabb0570dfd1d8`

- Foundational infrastructure for Phase 0
- Security frameworks, feature flags, config validation
- Workflow common utilities and JSON Schema

### v0.3.0 - Dependency Updates & Actions Migration (Oct 29, 2025)

**Commit:** `23faf143cf3e8545d91fc18d9a1f9e35c81c8787`

- Major GitHub Actions version bumps (actions/setup-go v5→v6)
- CodeQL v3→v4, checkout v4→v5
- setup-python v5→v6, github-script v7→v8

### v0.4.0 - Style & Linting Standardization (Oct 30, 2025)

**Commit:** `b7277541432eada6b5a9bb7d0bd5b13bf581fc1e`

- Massive ruff/prettier formatting across all Python/MD files
- Actionlint compliance improvements
- Code style consistency

### v0.5.0 - Workflow V2 Architecture (Nov 1, 2025)

**Commit:** `1050ebe6193610f15aa20acff63aff7441659bc9`

- Phase 1-5 documentation complete
- Reusable CI/release/security/protobuf workflows
- Test fixtures and comprehensive testing
- Archived legacy workflows

### v0.6.0 - Maintenance & Documentation Automation (Nov 1, 2025)

**Commit:** `f9a0ac7743d786385f621bb0d8578ecf6a983809`

- Docs workflow automation
- Maintenance workflow scripts
- Performance monitoring enhancements
- Release artifact packaging

### v0.7.0 - Linting & Code Quality (Nov 2, 2025)

**Commit:** `aa5fc97cb6a19bf60a60d435e2c84e488ea3ed5b`

- Lots of linter fixes across codebase
- Ruff configuration updates
- Pre-commit configuration improvements

### v0.8.0 - GitHub Actions v6 Completion (Nov 9, 2025)

**Commit:** `9c72ecaf4a657f9766722c6308c9aa237119dbd0`

- Final actions updates: upload-artifact v4→v5
- actions/download-artifact v5→v6
- Complete v6 migration for all actions

### v0.9.0 - ESLint & Node Updates (Nov 18, 2025)

**Commit:** `09c96e4f462846d2bbda77a18f3dfcbbc2dfeeb2`

- ESLint 9.39.0→9.39.1
- typescript-eslint 8.46.2→8.46.3
- js-yaml security update 4.1.0→4.1.1

### v1.0.0-alpha - Current Stable State (Nov 24, 2025)

**Commit:** `dc21cf5d2739baee5931a0ec9eba659fb339d8c2` (current HEAD)

- Ready for production testing
- All workflows converted to reusable pattern
- Full test coverage and documentation complete
- ESLint config updates and CI environment improvements

## Usage

Repositories can pin to specific versions for stability:

```yaml
uses: jdfalk/ghcommon/.github/workflows/reusable-ci.yml@v0.9.0
```

Or use latest alpha for cutting-edge features:

```yaml
uses: jdfalk/ghcommon/.github/workflows/reusable-ci.yml@v1.0.0-alpha
```
