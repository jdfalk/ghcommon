# TODO

## ✅ Completed

- [x] Phase 0: Shared workflow foundations (`workflow_common.py`, config schema, validation tooling,
      security checklist, core tests)
- [x] Phase 1: CI modernization (change detection helper, reusable CI workflow, feature-flagged
      caller, unit + integration tests)
- [x] Phase 2: Release consolidation (branch-aware release helper, reusable release workflow,
      feature-flagged caller, GitHub Packages docs/tests)
- [x] GitHub Packages publishing job, helper script, rollout docs, automated tests, and summary
      tooling

## 🚧 In Progress / Upcoming

### Phase 3: Documentation Automation

- [x] Build doc-change detection pipeline and reusable documentation workflow
- [x] Implement auto-generated docs publishing and changelog updates
- [x] Wire feature flag `use_new_docs` into workflows and repository configuration
- [x] Add unit/integration tests for doc automation helpers and workflows

### Phase 4: Maintenance Automation

- [x] Implement maintenance helpers for dependency updates (docs + summary tooling).
- [x] Create reusable maintenance workflow and feature-flagged caller (wired to maintenance helper)
- [x] Add scheduling + configuration hooks for maintenance jobs across repos (config-driven via
      repository-config.yml)
- [x] Document maintenance automation runbooks and verification steps

### Phase 5: Advanced Features

- [x] Add metrics/observability helpers and analytics integration
- [x] Implement automation workflows for caching, analytics, and self-healing reporting
- [x] Extend workflow catalog/reference docs with advanced feature details

### Operations & Reference Tasks

- [x] Finalize rollback procedures, troubleshooting, and migration playbooks for v2 workflows
- [x] Update implementation guides (testing, release, CI) with new patterns and linters
- [x] Ensure helper scripts API reference reflects new modules and features
- [x] Validate workflow catalog entries for new reusable workflows (CI, release, docs, maintenance,
      advanced)
