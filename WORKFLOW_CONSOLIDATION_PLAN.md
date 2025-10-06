<!-- file: WORKFLOW_CONSOLIDATION_PLAN.md -->
<!-- version: 1.0.0 -->
<!-- guid: ced2dd01-2645-4c87-a2da-a7eaf5387137 -->

# Workflow Consolidation and Reusable Architecture Plan

<!-- file: WORKFLOW_CONSOLIDATION_PLAN.md -->
<!-- version: 1.0.0 -->
<!-- guid: plan-2024-09-24-workflow-consolidation -->

## Executive Summary

We currently have a convoluted mix of workflows, configuration files, and scripts that overlap in
functionality and create maintenance burden. This document outlines a plan to consolidate everything
into a clean reusable workflow architecture with unified configuration.

## Current State Analysis

### Workflow Redundancy Issues

#### 1. Labeling Confusion

- **`intelligent-labeling.yml`** (8 repositories) - AI-powered labeling system
- **`labeler.yml`** (16 repositories) - Traditional path-based labeling configuration
- **Problem**: These serve different purposes but both handle labeling
- **Solution**: Keep both but clarify roles - intelligent-labeling for AI, labeler for path-based
  rules

#### 2. Configuration Fragmentation

- **`release-config.yml`** (1 file) - Comprehensive release configuration with language detection,
  versioning, build settings
- **`unified-automation-config.json`** (1 file) - Issue management, docs, labeling, linting
  configuration
- **Problem**: Split configuration makes it hard to understand repository settings
- **Solution**: Merge into single `repository-config.yml` with sections for all workflow types

#### 3. Script Duplication

- **`propagate_instructions_updates.py`** (new Python script) - Updates copilot instructions across
  repos
- **`update-copilot-instructions.sh`** (8 repositories) - Shell script for same purpose
- **Multiple similar scripts**: `cleanup-*.py`, `sync-*.py`, `repo-*.py` with overlapping
  functionality

### File Purpose Analysis

| File                             | Purpose                         | Status      | Action                            |
| -------------------------------- | ------------------------------- | ----------- | --------------------------------- |
| `intelligent-labeling.yml`       | AI-powered issue labeling       | Keep        | Document as AI labeler            |
| `labeler.yml`                    | Path-based PR labeling          | Keep        | Document as path labeler          |
| `release-config.yml`             | Release workflow configuration  | Keep/Expand | Merge with automation config      |
| `unified-automation-config.json` | General workflow config         | Consolidate | Merge into repository-config.yml  |
| `update-copilot-instructions.sh` | Shell-based instruction updates | Remove      | Replace with Python equivalent    |
| Multiple cleanup scripts         | Various maintenance tasks       | Consolidate | Create unified maintenance script |

## Reusable Workflow Architecture Plan

### Phase 1: Create Reusable Workflow Components

#### 1.1 Language-Specific Reusable Workflows (Keep As-Is)

These are already well-structured and should remain as reusable components:

- `release-go.yml` → `.github/workflows/reusable-go-build.yml`
- `release-rust.yml` → `.github/workflows/reusable-rust-build.yml`
- `release-python.yml` → `.github/workflows/reusable-python-build.yml`
- `release-frontend.yml` → `.github/workflows/reusable-frontend-build.yml`
- `release-docker.yml` → `.github/workflows/reusable-docker-build.yml`
- `protobuf-generation.yml` → `.github/workflows/reusable-protobuf-generation.yml`

#### 1.2 Core Reusable Workflows (New)

Create these new reusable workflows:

- `.github/workflows/reusable-ci.yml` - Main CI workflow logic
- `.github/workflows/reusable-security.yml` - Security scanning and analysis
- `.github/workflows/reusable-maintenance.yml` - Repository maintenance tasks
- `.github/workflows/reusable-issue-automation.yml` - Issue management and automation

#### 1.3 Coordinator Workflows (Convert to Use Reusables)

Update these to call reusable workflows:

- `ci.yml` → calls `reusable-ci.yml`
- `release.yml` → calls appropriate `reusable-*-build.yml` workflows
- `security.yml` → calls `reusable-security.yml`
- `maintenance.yml` → calls `reusable-maintenance.yml`
- `issue-automation.yml` → calls `reusable-issue-automation.yml`

### Phase 2: Unified Configuration System

#### 2.1 Create Repository Configuration Schema

Merge `release-config.yml` and `unified-automation-config.json` into:

```yaml
# .github/repository-config.yml
repository:
  name: 'Repository Name'
  description: 'Repository Description'
  languages: ['go', 'python', 'rust'] # Auto-detected, can override

release:
  versioning: # From release-config.yml
    strategy: 'semantic'
    release_types:
      major: ['feat!', 'breaking']
      minor: ['feat']
      patch: ['fix', 'chore']

  build_matrix: # From release-config.yml
    go:
      versions: ['1.23', '1.24']
      platforms: ['ubuntu-latest', 'windows-latest', 'macos-latest']

ci:
  coverage_threshold: 80
  run_tests: true
  run_linting: true
  protobuf_generation: true # For repos with protobuf

automation: # From unified-automation-config.json
  issue_management:
    auto_close_stale: true
    stale_days: 30
  labeling:
    intelligent_labeling: true
    path_based_labeling: true
  maintenance:
    dependency_updates: true
    security_scanning: true
```

#### 2.2 Configuration Loading Logic

Create a standardized way for workflows to load configuration:

1. Check for repository-specific `.github/repository-config.yml`
2. Fall back to defaults from ghcommon's config
3. Allow workflow_dispatch inputs to override any setting

### Phase 3: Script Consolidation

#### 3.1 Remove Duplicate Scripts

**Delete these duplicates:**

- `update-copilot-instructions.sh` (8 repos) → Use `propagate_instructions_updates.py`
- Multiple `cleanup-*` scripts → Create single `maintenance_runner.py`
- Multiple `sync-*` scripts → Create single `repository_sync.py`

#### 3.2 Create Unified Script Categories

**Repository Management:**

- `scripts/repository_manager.py` - Handles cross-repo operations
- `scripts/workflow_manager.py` - Manages workflow synchronization
- `scripts/configuration_manager.py` - Handles config file updates

**Development Tools:**

- `scripts/maintenance_runner.py` - All cleanup and maintenance tasks
- `scripts/issue_manager.py` - Issue automation (keep existing, it's good)
- `scripts/template_manager.py` - Template repository operations

**CI/CD Tools:**

- `scripts/build_matrix_generator.py` - Generates build matrices from config
- `scripts/release_coordinator.py` - Coordinates releases across languages

### Phase 4: Implementation Order

#### Week 1: Create Reusable Workflows

1. Convert language-specific workflows to reusable format (no logic changes)
2. Create new reusable CI, security, maintenance workflows
3. Test reusable workflows work correctly

#### Week 2: Update Coordinators

1. Update coordinator workflows to call reusables
2. Remove duplicated logic from coordinators
3. Test all coordinators work with reusables

#### Week 3: Unified Configuration

1. Create repository-config.yml schema
2. Update all workflows to read from unified config
3. Migrate existing configs to new format

#### Week 4: Script Consolidation

1. Create consolidated script architecture
2. Remove duplicate scripts from all repositories
3. Update any references to old scripts

#### Week 5: Testing and Validation

1. Test full workflow execution in all repositories
2. Validate configuration loading works correctly
3. Ensure no functionality is lost in consolidation

## Benefits of This Architecture

### For Developers

- Single configuration file to understand repository behavior
- Clearer separation between reusable components and coordinators
- Easier to customize workflows for specific repositories
- Reduced maintenance burden

### For CI/CD

- Reusable workflows prevent drift between repositories
- Centralized updates propagate automatically
- Configuration-driven behavior is more predictable
- Better testing of workflow components

### For Repository Management

- Consistent behavior across all repositories
- Easier to add new repositories with standard setup
- Clear documentation of what each workflow does
- Simplified troubleshooting

## Migration Strategy for Each Repository

1. **ghcommon** (source of truth)
   - Create all reusable workflows
   - Create repository-config.yml schema
   - Update coordinator workflows first

2. **gcommon, subtitle-manager** (high-complexity repos)
   - Test new architecture with these complex repositories
   - Validate protobuf workflows work correctly
   - Ensure no build functionality is lost

3. **Other repositories** (lower-complexity)
   - Bulk update with consolidated scripts
   - Validate CI passes for all
   - Clean up old configuration files

## Success Criteria

- [ ] All repositories use the same reusable workflow components
- [ ] Single configuration file controls all workflow behavior
- [ ] No duplicate scripts across repositories
- [ ] All CI/CD functionality preserved
- [ ] Documentation clearly explains each component's purpose
- [ ] New repositories can be onboarded with minimal setup

## Risk Mitigation

- **Configuration Breaking**: Maintain backward compatibility during transition
- **Workflow Failures**: Test extensively in non-production repositories first
- **Script Dependencies**: Audit all script usages before removal
- **Permission Issues**: Keep reusable workflows permission-minimal as planned

This plan transforms our current chaotic workflow situation into a maintainable, scalable
architecture that will serve us well long-term.
