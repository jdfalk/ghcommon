# TODO

## 🤖 Background Agent Queue (manage_todo_list sync)

- [ ] Plan security workflow actionization
- [ ] Audit remaining workflows for action conversion
- [ ] Validate new composite actions CI/CD pipelines
- [ ] Verify action tags and releases (v1/v1.0/v1.0.0)
- [ ] Update reusable workflows to use new actions and verify

### Next Actions (Security Workflow Actionization)

- Create security-focused composite action repos (no inline scripts), scaffold `action.yml`,
  `README.md`, and test workflows
- Define inputs/outputs (branch/paths, severity thresholds, SARIF handling), and
  `GITHUB_OUTPUT`/summary contracts
- Implement CI for actions, cut `v1.0.0`, and add moving tags `v1` and `v1.0`; create GitHub
  Releases like other actions
- Patch `reusable-security.yml` to use new actions; dry-run in 1-2 repos and verify behavior

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

## 🔥 Critical - Action Repository CI Failures

### Priority 1: Critical Failures (Missing Core Files)

#### #todo release-docker-action - Create Missing Files

**Status:** Blocked **Priority:** Critical **Repository:**
[release-docker-action](https://github.com/jdfalk/release-docker-action)

**Issues:**

- Missing action.yml completely
- Missing README.md
- Missing test Dockerfile
- Tests failing due to missing files

**Action Items:**

1. Create action.yml with complete action definition
2. Create README.md with usage documentation
3. Create test structure with sample Dockerfile
4. Implement Docker build functionality
5. Fix and test CI workflow

**Tracking:** See `/Users/jdfalk/repos/github.com/jdfalk/release-docker-action/TODO.md`

---

#### #todo release-go-action - Create Missing Files

**Status:** Blocked **Priority:** Critical **Repository:**
[release-go-action](https://github.com/jdfalk/release-go-action)

**Issues:**

- Missing action.yml completely
- Missing README.md
- No action implementation

**Action Items:**

1. Create action.yml with Go build configuration
2. Create README.md with usage documentation
3. Implement cross-compilation support
4. Add release artifact handling
5. Fix and test CI workflow

**Tracking:** See `/Users/jdfalk/repos/github.com/jdfalk/release-go-action/TODO.md`

---

### Priority 2: High Priority Failures (Lint/Config Issues)

#### #todo auto-module-tagging-action - Fix YAML Linting

**Status:** Open **Priority:** High **Repository:**
[auto-module-tagging-action](https://github.com/jdfalk/auto-module-tagging-action)

**Issues:**

- 10 YAML line length violations (lines too long)
- Test execution failing (exit code 128)
- Cache restore warnings

**Action Items:**

1. Fix all yamllint line length errors in action.yml
2. Investigate and fix test execution error (exit 128)
3. Fix Go module cache configuration
4. Test and verify CI passes

**Tracking:** See `/Users/jdfalk/repos/github.com/jdfalk/auto-module-tagging-action/TODO.md`

---

#### #todo release-frontend-action - Fix YAML Linting

**Status:** Open **Priority:** High **Repository:**
[release-frontend-action](https://github.com/jdfalk/release-frontend-action)

**Issues:**

- 6 YAML line length violations
- Missing README.md
- Cache dependencies error

**Action Items:**

1. Fix all yamllint line length errors in action.yml
2. Create comprehensive README.md
3. Fix cache dependencies configuration
4. Test and verify CI passes

**Tracking:** See `/Users/jdfalk/repos/github.com/jdfalk/release-frontend-action/TODO.md`

---

#### #todo release-rust-action - Fix Cargo.toml Error

**Status:** Open **Priority:** High **Repository:**
[release-rust-action](https://github.com/jdfalk/release-rust-action)

**Issues:**

- rust-cache action cannot find Cargo.toml
- Incorrectly treating composite action repo as Rust project
- Test workflow needs restructuring

**Action Items:**

1. Remove or conditionally skip rust-cache in CI
2. Restructure test workflow for composite action testing
3. Create sample Rust project for integration testing
4. Test and verify CI passes

**Tracking:** See `/Users/jdfalk/repos/github.com/jdfalk/release-rust-action/TODO.md`

---

### Priority 3: Working (No Immediate Action Required)

#### #todo release-protobuf-action - Monitor

**Status:** Passing **Priority:** Low **Repository:**
[release-protobuf-action](https://github.com/jdfalk/release-protobuf-action)

**Notes:**

- CI currently passing
- No failures detected
- Ready for migration to reusable workflows

**Tracking:** See `/Users/jdfalk/repos/github.com/jdfalk/release-protobuf-action/TODO.md`

---

## 🔄 Migration to Reusable Workflows

### #todo Phase 1: Fix All CI Failures First

**Status:** In Progress **Priority:** Critical **Dependencies:** All above CI fixes must be
completed

**Completion Criteria:**

- [ ] release-docker-action: CI passing
- [ ] release-go-action: CI passing
- [ ] auto-module-tagging-action: CI passing
- [ ] release-frontend-action: CI passing
- [ ] release-rust-action: CI passing
- [ ] release-protobuf-action: CI verified passing

---

### #todo Phase 2: Migrate to Reusable Workflows

**Status:** Blocked **Priority:** High **Dependencies:** Phase 1 must complete first

**Action Items:**

1. Update each action to use `.github/workflows/reusable-action-ci.yml`
2. Update each action to use `.github/workflows/reusable-release.yml`
3. Test workflows in each repository
4. Pull and verify logs for each workflow run
5. Document any issues or customizations needed

**Repositories to Migrate:**

- [ ] release-docker-action
- [ ] release-go-action
- [ ] auto-module-tagging-action
- [ ] release-frontend-action
- [ ] release-rust-action
- [ ] release-protobuf-action

---

### #todo Phase 3: Continuous Testing and Validation

**Status:** Blocked **Priority:** High **Dependencies:** Phase 2 must complete first

**Testing Plan:**

1. Run CI workflows in each repository
2. Pull and analyze logs from each run
3. Verify all jobs pass successfully
4. Test release workflows with version bumps
5. Verify artifact creation and uploads
6. Document any issues found
7. Iterate until all workflows are stable

**Success Metrics:**

- All CI workflows passing
- All release workflows creating proper artifacts
- Logs showing no errors or warnings
- Documentation updated with any learnings

---

## 📊 Summary Status

**Total Repositories:** 6 **Critical Failures:** 2 (release-docker-action, release-go-action) **High
Priority Failures:** 3 (auto-module-tagging-action, release-frontend-action, release-rust-action)
**Passing:** 1 (release-protobuf-action)

**Estimated Timeline:**

- Phase 1 (Fix CI): 2-3 days
- Phase 2 (Migration): 1-2 days
- Phase 3 (Testing): 1-2 days
- **Total:** 4-7 days

---

**Last Updated:** 2025-12-19 **Next Review:** After critical failures are resolved

---

## 🚀 New High Priority Tasks

### #todo Tag release-go-action as v2.0.0

**Status:** Ready **Priority:** Critical **Repository:**
[release-go-action](https://github.com/jdfalk/release-go-action)

**Context:** release-go-action has been completely rewritten to use GoReleaser instead of manual Go
builds. This is a breaking change requiring v2.0.0.

**Action Items:**

1. [ ] Ensure release-go-action changes are committed and pushed
2. [ ] Run `scripts/tag-release-go-v2.sh` to create v2.0.0, v2.0, and v2 tags
3. [ ] Verify tags are pushed to GitHub
4. [ ] Get commit hash for pinning in workflows
5. [ ] Update ghcommon workflows to use v2

**Script:** `/Users/jdfalk/repos/github.com/jdfalk/ghcommon/scripts/tag-release-go-v2.sh`

---

### #todo Pin all actions to commit hashes

**Status:** Ready **Priority:** High **Repository:** ghcommon

**Context:** All jdfalk/\* actions should be pinned to specific commit hashes with version comments
for security and reproducibility.

**Action Items:**

1. [ ] Run `scripts/pin-actions-to-hashes.py` to discover and pin actions
2. [ ] Review generated ACTION_VERSIONS.md reference file
3. [ ] Verify all workflows use `jdfalk/action@hash # vX.Y.Z` format
4. [ ] Commit and push changes
5. [ ] Update documentation with pinning policy

**Script:** `/Users/jdfalk/repos/github.com/jdfalk/ghcommon/scripts/pin-actions-to-hashes.py`

**Output:** `ACTION_VERSIONS.md` - Version/hash reference table

---

### #todo Convert reusable workflows to new actions

**Status:** Pending **Priority:** High **Repository:** ghcommon

**Context:** Now that actions are extracted, convert reusable workflows to use the new jdfalk/\*
actions.

**Action Items:**

1. [ ] Update `release-go.yml` to use `jdfalk/release-go-action@hash # v2.0.0`
2. [ ] Update `release-docker.yml` to use `jdfalk/release-docker-action@hash # v1.0.0`
3. [ ] Update `release-frontend.yml` to use `jdfalk/release-frontend-action@hash # v1.0.0`
4. [ ] Update `release-python.yml` to use `jdfalk/release-python-action@hash # v1.0.0`
5. [ ] Update `release-rust.yml` to use `jdfalk/release-rust-action@hash # v1.0.0`
6. [ ] Update `release-protobuf.yml` to use `jdfalk/release-protobuf-action@hash # v1.0.0`
7. [ ] Test each workflow conversion
8. [ ] Document migration for repositories using these workflows

**Dependencies:** Requires #todo Pin all actions to commit hashes

---

### #todo Monitor and fix remaining action CI failures

**Status:** In Progress **Priority:** High **Repository:** All action repos

**Context:** Some actions still have CI failures that need investigation and fixing.

**Action Items:**

1. [ ] Run `scripts/trigger-and-monitor-ci.sh` to check all action CI status
2. [ ] Review failure logs in `logs/ci-failures/`
3. [ ] Fix any remaining YAML linting errors
4. [ ] Fix any test failures
5. [ ] Ensure all actions pass CI before v1.0.0 release

**Completed:**

- ✅ Fixed action.yml shell parameter errors
- ✅ Fixed input validation mismatches
- ✅ Added GoReleaser support to release-go-action (v2.0.0)

---
