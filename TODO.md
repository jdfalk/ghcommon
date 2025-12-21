# TODO

## 🤖 Background Agent Queue (manage_todo_list sync)

- [ ] Plan security workflow actionization - Goal: Move security scanning logic out of
      reusable-security.yml into auditable composite actions with external scripts only. - Scope
      (initial action repos): - jdfalk/security-codeql-action: Orchestrate codeql
      init/analyze/upload (wraps actions/codeql) with repo config overrides. -
      jdfalk/security-trivy-action: Trivy filesystem/image/vulnerability scan with SARIF output and
      severity gating. - jdfalk/security-osv-scan-action: OSV-Scanner on repo dependencies (Go,
      Python, Node, Rust) with SARIF output. - jdfalk/security-secrets-action: Gitleaks (or
      repo-level secret scan wrapper) with allowlist support. - jdfalk/security-summary-action:
      Aggregate SARIFs, gate on thresholds, and write step summary + artifacts. - Inputs/Outputs
      (common): - Inputs: `paths`, `exclude`, `severity-threshold`, `fail-on`, `sarif-path`,
      `upload-sarif` (true/false), `tool-args`. - Outputs: `sarif`, `findings-count`,
      `critical-count`, `high-count`, `failed`. - Deliverables: - Each repo: action.yml, README with
      usage, src/ implementation (Python/Bash), .github/workflows/ci.yml tests. - Tags: v1.0.0
      initial, moving tags v1 and v1.0, GitHub Release with changelog. - Docs: ghcommon
      ACTIONS_INTEGRATION_GUIDE.md section for security actions + examples. - Acceptance Criteria: -
      Actions run on sample repos producing SARIF, respect thresholds, and publish summaries. -
      reusable-security.yml refactored to call these actions; dry-run passes in 2 representative
      repos. - Risks/Notes: Keep codeql on GH-hosted runners; avoid inline scripts; support matrix
      by language as needed.

- [ ] Audit remaining workflows for action conversion - Inventory Targets: -
      reusable-advanced-cache.yml → cache-strategy-action - reusable-maintenance.yml →
      maintenance-summary-action - reusable-protobuf.yml → protobuf-config-action,
      protobuf-verify-action (if not done) - documentation.yml → docs-generator-action -
      issue-automation.yml → intelligent-labeling-action - sync-receiver.yml →
      sync-receiver-action - Steps: - Build call graph from WORKFLOW_SCRIPT_USAGE_MAP.md to confirm
      dependencies. - Define action contracts (inputs/outputs) matching current scripts. - Draft
      action repos list, ownership, and rollout order (P1→P4). - Deliverables: Updated
      WORKFLOW_SCRIPT_AUDIT.md with status, risks, and ETA per action. - Acceptance Criteria:
      Signed-off actionization plan with sequencing and test strategy.

- [ ] Validate new composite actions CI/CD pipelines - Scope: Six already-created actions
      (load-config, ci-generate-matrices, detect-languages, release-strategy, generate-version,
      package-assets). - Tests to Run: - Lint/parse action.yml; run action unit tests via local
      workflow in each repo. - Integration: use minimal sample repos to execute typical paths and
      verify outputs + summaries. - Failure modes: missing configs, malformed inputs, matrix edge
      cases. - Observability: Ensure GITHUB_STEP_SUMMARY is populated and outputs match docs
      exactly. - Deliverables: ACTIONS_VERIFICATION_REPORT.md updated with run IDs and pass/fail
      notes. - Acceptance Criteria: All action repos have green CI on main and successful
      integration runs.

- [ ] Verify action tags and releases (v1/v1.0/v1.0.0) - Tag Policy: - Create immutable v1.0.0 tags;
      create/update moving tags v1 and v1.0 to latest compatible. - Ensure GitHub Releases exist for
      v1.0.0 with notes mirroring README features and changes. - Steps: - List tags in each action
      repo; create missing moving tags; verify protection settings. - Confirm release metadata:
      title, body, links to example workflows, and compatibility notes. - Deliverables: Tag and
      Release checklist log per repo in ghcommon (logs/tags/...). - Acceptance Criteria: Consumers
      can pin @v1, @v1.0, or @v1.0.0 consistently; Marketplace visibility OK.

- [ ] Update reusable workflows to use new actions and verify - Targets: reusable-ci.yml (partially
      done), reusable-release.yml (partially done), reusable-security.yml (new), protobuf workflow
      (if applicable). - Steps: - Replace inline/scripted steps with uses: jdfalk/\*-action@v1. -
      Keep dorny/paths-filter where fit; remove sparse-checkout logic entirely. - Add summary
      checkpoints and robust outputs wiring between jobs. - Run on ghcommon (self) and
      audiobook-organizer as canary; capture run logs. - Deliverables: PR/commit diffs for each
      workflow; Integration Guide updated with before/after. - Acceptance Criteria: Green pipeline
      in canary repos; artifacts/releases intact; no inline scripts remain.

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
