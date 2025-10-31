<!-- file: docs/refactors/workflows/v2/rollout-checklist.md -->
<!-- version: 1.0.0 -->
<!-- guid: 5e6f7081-92a3-b4c5-d6e7-f8091a2b3c4d -->

# Workflow v2 Rollout Checklist

Use this checklist to migrate repositories from the legacy release automation to the v2 feature-flagged system with minimal risk.

## 1. Preparation

- [ ] Confirm repository has a clean default branch (no uncommitted or unpushed changes).
- [ ] Review `CHANGELOG.md` for accuracy and ensure semantic versioning is followed.
- [ ] Verify manifest files declare the correct package version (Go `go.mod`, Rust `Cargo.toml`, Python `pyproject.toml`, Node `package.json`).
- [ ] Ensure required secrets exist:
  - `GITHUB_TOKEN` (auto-provided) has `contents`/`packages` write permissions.
  - Language-specific registry tokens (`NPM_TOKEN`, `PYPI_TOKEN`, `CARGO_REGISTRY_TOKEN`) are configured if publishing outside GitHub Packages.
- [ ] Audit `.github/repository-config.yml` for consistency and determine desired registry enablement flags.
- [ ] Communicate rollout plan to stakeholders; schedule a maintenance window if necessary.

## 2. Dry Run Validation

- [ ] Trigger `release.yml` via `workflow_dispatch` with `draft=true` and a prerelease version (e.g., `0.0.0-test1`) while the feature flag remains `false`.
- [ ] Inspect `legacy-release` job logs to confirm it warns about the feature flag (baseline behavior).
- [ ] Create a temporary branch, set `workflows.experimental.use_new_release: true`, and push to trigger the new workflow.
- [ ] Verify `prepare-release` outputs correct language, version, branch, tag, and changelog summary.
- [ ] Confirm relevant language build job executes successfully and produces artifacts.
- [ ] Validate `create-release` job attaches artifacts to a draft release (then delete the draft).
- [ ] Evaluate `publish-packages` logs to ensure the placeholder or real publishing commands behave as expected.
- [ ] Collect feedback from dry run reviewers; update documentation or scripts as needed.

## 3. Enablement

- [ ] Set `workflows.experimental.use_new_release: true` in `.github/repository-config.yml` on the default branch.
- [ ] Merge the change via pull request to ensure code review visibility.
- [ ] Monitor the next scheduled or manual run of `release.yml` on the default branch.
- [ ] Validate that `legacy-release` no longer runs and `new-release` fires automatically.
- [ ] Check the generated GitHub Release and attached artifacts for correctness.
- [ ] If GitHub Packages publishing is enabled, confirm package versions and tags appear with expected naming.

## 4. Stable Branch Adoption

- [ ] For each stable branch (e.g., `stable-1-go-1.24`), merge the feature flag change or cherry-pick once validated on `main`.
- [ ] Trigger a draft release from the stable branch to confirm branch-aware tagging (e.g., `v1.2.3-go124`).
- [ ] Verify consumers can pull stable branch packages (`go get`, `pip install`, `npm install`, `cargo install`) using the decorated versions.
- [ ] Update downstream documentation for stable branch consumers if tag formats changed.

## 5. Post-Migration Cleanup

- [ ] Retire or archive documentation referring to the legacy release workflow.
- [ ] Remove legacy workflow files when all supported branches run v2 successfully.
- [ ] Update onboarding guides to reference the new release process and feature flag settings.
- [ ] Schedule recurring reviews of release artifacts and packages to ensure ongoing compliance.
- [ ] Document any repository-specific caveats discovered during rollout for future maintainers.

## 6. Exit Criteria

- [ ] All release runs on default and stable branches execute the v2 workflow without manual intervention.
- [ ] GitHub Releases and packages follow the branch-aware naming scheme.
- [ ] Stakeholders sign off on the new process and documentation updates.
- [ ] Monitoring and alerting (if any) are updated to track the new workflow jobs.
- [ ] Legacy tooling is removed or disabled, preventing future regressions.
