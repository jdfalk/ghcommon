# TODO

## ✅ Completed

- [x] Phase 0: Shared workflow foundations (`workflow_common.py`, config schema, validation tooling,
      security checklist, core tests)
- [x] Phase 1: CI modernization (change detection helper, reusable CI workflow, feature-flagged
      caller, unit + integration tests)
- [x] Phase 2: Release consolidation (branch-aware release helper, reusable release workflow,
      feature-flagged caller, GitHub Packages docs/tests)
- [x] GitHub Packages publishing job, helper script, rollout docs, automated tests, and summary tooling

## 🚧 In Progress / Upcoming

### Phase 3: Documentation Automation

- [ ] Build doc-change detection pipeline and reusable documentation workflow
- [ ] Implement auto-generated docs publishing and changelog updates
- [ ] Wire feature flag `use_new_docs` into workflows and repository configuration
- [ ] Add unit/integration tests for doc automation helpers and workflows

### Phase 4: Maintenance Automation

- [ ] Implement maintenance helpers for dependency updates, security scans, and housekeeping tasks
- [ ] Create reusable maintenance workflow and feature-flagged caller
- [ ] Add scheduling + configuration hooks for maintenance jobs across repos
- [ ] Document maintenance automation runbooks and verification steps

### Phase 5: Advanced Features

- [ ] Add metrics/observability helpers and analytics integration
- [ ] Implement branch lifecycle automation (stable branch aging, locks, notifications)
- [ ] Introduce advanced feature toggles and rollout controls
- [ ] Extend workflow catalog/reference docs with advanced feature details

### Operations & Reference Tasks

- [ ] Finalize rollback procedures, troubleshooting, and migration playbooks for v2 workflows
- [ ] Update implementation guides (testing, release, CI) with new patterns and linters
- [ ] Ensure helper scripts API reference reflects new modules and features
- [ ] Validate workflow catalog entries for new reusable workflows (CI, release, docs, maintenance,
      advanced)
