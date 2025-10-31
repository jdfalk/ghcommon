<!-- file: docs/workflows/consolidation-map.md -->
<!-- version: 1.0.0 -->
<!-- guid: 7f5db8a1-4c9c-4f2a-9b36-5f46dfdb73e2 -->

# Workflow Consolidation Map

## Legacy → V2 Consolidation

| Legacy Workflow                                        | Current Status           | Replacement / Successor                                                        | Coverage Notes                                                                           |
| ------------------------------------------------------ | ------------------------ | ------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------- |
| `.github/workflows/release-frontend-v1-deprecated.yml` | Archived (v1)            | `.github/workflows/reusable-release.yml` via `frontend` branch in build matrix | Frontend packaging, testing, and release artifacts now emitted from reusable pipeline.   |
| `.github/workflows/release-go-v1-deprecated.yml`       | Archived (v1)            | `.github/workflows/reusable-release.yml` + Go module helpers                   | Go module/tag validation and GitHub Packages publishing driven by Python helpers.        |
| `.github/workflows/release-python-v1-deprecated.yml`   | Archived (v1)            | `.github/workflows/reusable-release.yml` + Python packaging job                | Build/Test/PyPI+Packages publishing orchestrated centrally.                              |
| `.github/workflows/release-rust-v1-deprecated.yml`     | Archived (v1)            | `.github/workflows/reusable-release.yml` + Rust target matrix                  | Cross-compilation, signing, and crate publishing handled through reusable plan.          |
| `.github/workflows/release-docker-v1-deprecated.yml`   | Archived (v1)            | `.github/workflows/reusable-release.yml` + Docker build path                   | Image build/push now triggered from unified release workflow.                            |
| `.github/workflows/release-protobuf-v1-deprecated.yml` | Archived (v1)            | `.github/workflows/reusable-release.yml` + protobuf tasks                      | Buf generation, linting, and artifact upload centralized.                                |
| `.github/workflows/ci-tests.yml`                       | Legacy (kept for parity) | `.github/workflows/reusable-ci.yml` (new CI entry point)                       | Kept temporarily for back-compat; config-driven reusable CI is the intended replacement. |

## Active Workflow Inventory

| Workflow                                                                                | Focus Area             | Notes / Next Actions                                                                                      |
| --------------------------------------------------------------------------------------- | ---------------------- | --------------------------------------------------------------------------------------------------------- |
| `.github/workflows/ci.yml`                                                              | CI entrypoint          | Calls `reusable-ci.yml` with repository-config inputs; ensure consumers adopt config pathway.             |
| `.github/workflows/reusable-ci.yml`                                                     | Reusable CI            | Lint/test/coverage pipelines built on Python helpers; roadmap includes config-driven skip flags.          |
| `.github/workflows/release.yml`                                                         | Release dispatcher     | Wraps `reusable-release.yml`; only public interface needed downstream.                                    |
| `.github/workflows/reusable-release.yml`                                                | Reusable release       | Unified orchestration for Go/Python/Rust/Frontend/Docker/Protobuf (replaces all v1 release workflows).    |
| `.github/workflows/reusable-advanced-cache.yml`                                         | Dependency caching     | Provides cache-plan integration for language runtimes; replace raw `actions/cache` usage.                 |
| `.github/workflows/workflow-analytics.yml`                                              | Observability          | Scheduled run that summarizes workflow health, runtimes, failure hot spots.                               |
| `.github/workflows/documentation.yml`                                                   | Docs build             | Generates helper docs, runs optional static site tooling, validates links.                                |
| `.github/workflows/maintenance.yml` / `reusable-maintenance.yml`                        | Maintenance            | Scheduled dependency updates/cleanup; slated for deeper config integration.                               |
| `.github/workflows/security.yml` / `reusable-security.yml`                              | Security scans         | Runs security tooling (e.g., grype, OSV scans) aligned with config toggles.                               |
| `.github/workflows/performance-monitoring.yml`                                          | Benchmarks             | Aggregates Rust/Node/Python benchmark artifacts and publishes summaries.                                  |
| `.github/workflows/pr-automation.yml`                                                   | PR automation          | Super Linter with auto-fix, job summaries, rebase assistance.                                             |
| `.github/workflows/issue-automation.yml` / `reusable-issue-automation.yml`              | Issue triage           | Applies labels, notifies teams, routes issues by config.                                                  |
| `.github/workflows/unified-automation.yml`                                              | Orchestration          | Wrapper workflow that coordinates automation helpers (labels, sync, etc.).                                |
| `.github/workflows/auto-module-tagging.yml`                                             | Repo sync              | Maintains module tags across repositories; modernized shell quoting.                                      |
| `.github/workflows/manager-sync-dispatcher.yml` & `.github/workflows/sync-receiver.yml` | Multi-repo sync        | Dispatcher/receptor pair that pushes ghcommon updates to downstream projects.                             |
| `.github/workflows/commit-override-handler.yml`                                         | Override handling      | Processes approved commit overrides for guarded branches.                                                 |
| `reusable-protobuf.yml`                                                                 | Protobuf tooling       | Reusable helper; migrate consumers to reusable version.                                                   |
| `.github/workflows/test-super-linter.yml`                                               | Lint smoke test        | Standalone Super Linter invocation for troubleshooting.                                                   |
| `.github/workflows/workflow-scripts-tests.yml`                                          | Helper unit tests      | Runs pytest suite for `.github/workflows/scripts/` modules.                                               |
| `.github/workflows/ci-tests.yml`                                                        | Legacy CI (deprecated) | Maintained only for parity while downstream migration completes; target replacement is `reusable-ci.yml`. |

> **Tip:** Reference archived `*-v1-deprecated.yml` files only for historical context. All new
> automation should call `reusable-release.yml` and `reusable-ci.yml` directly.
