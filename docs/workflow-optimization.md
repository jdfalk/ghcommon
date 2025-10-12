# Workflow Optimization Audit

This document captures the current state of the `ghcommon` workflows and reusable workflows, identifies the main inefficiencies, and proposes improvements aligned with the single source of truth in `.github/repository-config.yml`.

## Guiding Principles

- **Repository-config first:** Workflows should read defaults and toggles from `.github/repository-config.yml` instead of hardcoding matrices and feature flags. Dispatch inputs override, but automatic behaviour should come from config.
- **Reusable > bespoke:** Shared logic belongs in reusable workflows or helper scripts. Inline shell should be avoided when the logic is complex or needed in multiple jobs.
- **Single checkout of ghcommon:** Consumers should not need to re-checkout ghcommon when the workflow already ships the required scripts.
- **Test the helpers:** Every helper script should have direct unit-level coverage and a workflow that exercises the suite (`workflow-scripts-tests.yml`).

## Summary by Workflow

| Workflow | Current Role | Status | Inefficiencies | Recommendation |
| --- | --- | --- | --- | --- |
| `ci.yml` | Delegates to `reusable-ci.yml` | ✅ updated | – | Keep delegating; requires downstream adoption of new helper script flow |
| `ci-tests.yml` | Legacy full-matrix test runner | ⚠️ | Duplicates new reusable CI behaviour, manual path filters, hard-coded matrices | Deprecate in favour of `reusable-ci.yml` or refactor to call targeted reusable components driven by repository-config flags |
| `release.yml` | Calls `reusable-release.yml` | ⚠️ | Dispatch inputs mirror config, duplication for per-language jobs | Extend `reusable-release.yml` to inspect config for enabled languages and build matrices. Remove redundant per-language release workflows once consolidated |
| `release-go.yml`, `release-python.yml`, `release-rust.yml`, `release-frontend.yml`, `release-docker.yml`, `release-protobuf.yml` | Language-specific release orchestrators | ⚠️ | Near-identical scaffolding, manual environment configuration, inconsistent artefact handling | Fold into `reusable-release.yml` with modular jobs toggled by repository-config values. Expose hooks for language-specific steps via scripts |
| `reusable-ci.yml` | Shared CI pipeline | ✅ updated | – | Already converted to python helpers; next iteration should source matrices (versions, OS) from repository-config and expose skip flags via config |
| `reusable-release.yml` | Shared release/cut pipeline | ⚠️ | Heavy reliance on bash scripts, second checkout of ghcommon, duplicated detection logic | Replace shell helpers with python equivalents (mirroring `ci_workflow.py`), load repository-config once, and emit outputs consumed by language jobs |
| `reusable-maintenance.yml`, `reusable-security.yml`, `maintenance.yml`, `security.yml`, `performance-monitoring.yml` | Scheduled maintenance/security tasks | ⚠️ | Hard-coded schedules and behaviours, minimal config integration | Add parsing of repository-config maintenance/security sections for schedule, tooling, thresholds |
| `documentation.yml` | Docs verification | ⚠️ | Inline placeholder shell steps, not driven by config | Convert to python helper (e.g., docs_workflow.py) that reads doc tooling from config |
| `unified-automation.yml`, `issue-automation.yml`, `pr-automation.yml` | Labeling & automation | ⚠️ | Combination of inline scripts and Node entries that duplicate logic already present in scripts | Migrate to python helpers (existing `intelligent_labeling.py`, etc.) and ensure config-driven toggles |
| `auto-module-tagging.yml`, `manager-sync-dispatcher.yml` | Repo synchronisation | ❔ | Behaviour predates repository-config | Evaluate once initial CI/Release consolidation completes |
| `sync-receiver.yml` | Sync entry point | ✅ updated | – | Keep; new python helper already installed |

## High-impact Changes

1. **Repository-config driven matrices:**
   - Extend `ci_workflow.py` to consume `languages.versions` and `build.platforms` from config, eliminating hard-coded version lists.
   - Update `reusable-ci.yml` to request the parsed config and feed it into helper commands.

2. **Release consolidation:**
   - Introduce a `release_workflow.py` helper mirroring the CI helper style (language detection, versioning, artefact mapping based on config).
   - Rewire `reusable-release.yml` to call helper subcommands instead of bash scripts and to emit a structured build plan per language.
   - Replace per-language release workflows with thin wrappers around the new release helper (or integrate the jobs directly in the reusable workflow using dynamic matrices).

3. **Maintenance/Security integration:**
   - Create a `maintenance_workflow.py` helper that reads the `maintenance` and `security` sections of repository-config to determine schedule, tooling, and thresholds.
   - Update `reusable-maintenance.yml` and `reusable-security.yml` to run scripted steps using this helper instead of inline bash.

4. **Documentation validation:**
   - Replace placeholder echo steps in `documentation.yml` with calls to a new helper that can optionally run vale, markdownlint, or other tooling defined in config.

5. **Automation workflows:**
   - Consolidate issue/PR automation under a single reusable workflow that reads `automation.issues` and `automation.pull_requests` sections from config.
   - The existing Python scripts (`intelligent_labeling.py`, etc.) should be invoked from that reusable workflow with inputs derived from config (auto-merge toggles, label rules, etc.).

## Roadmap

1. **Phase 1 (current work)**
   - ✅ CI workflow scripted helpers and tests (`ci_workflow.py`).
   - ✅ Sync receiver helper conversion.
   - ☐ Repository-config parsing for CI matrices.

2. **Phase 2**
   - Implement `release_workflow.py` helper and migrate `reusable-release.yml`.
   - Merge per-language release workflows into reusable release (deprecate single-language ones after confirmation).
   - Add unit tests mirroring the CI helper suite.

3. **Phase 3**
   - Build maintenance/security helper and retrofit reusable workflows.
   - Expand documentation workflow to honour config toggles.
   - Rationalise `ci-tests.yml` (either remove or wire into reusable CI).

4. **Phase 4**
   - Reassess automation workflows, consolidating scripts and enabling config-driven behaviour.
   - Document the new workflow architecture in `docs/` with examples for consumer repositories.

## Implementation Notes

- Helpers should live under `.github/workflows/scripts/` with pytest coverage in `tests/workflow_scripts/`.
- Each reusable workflow should have a matching entry in `.github/workflows/workflow-scripts-tests.yml` once new helpers land.
- When deprecating legacy workflows (e.g., per-language release ones), keep them temporarily but emit warnings pointing maintainers to the consolidated workflow.
- Promote the helper scripts as versioned assets if we want external repos to pin specific revisions instead of fetching `main`.

## Next Actions

1. Add repository-config parsing to `ci_workflow.py` for matrices and pass config JSON through reusable CI.
2. Draft `release_workflow.py` and start migrating bash helpers.
3. Schedule follow-up issues for maintenance/security/doc automation updates using this audit as the spec.
