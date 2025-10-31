<!-- file: docs/refactors/workflows/v2/architecture.md -->
<!-- version: 1.0.0 -->
<!-- guid: 3c4d5e6f-7081-92a3-b4c5-d6e7f8091a2b -->

# Workflow v2 Architecture

The v2 release system introduces a feature-flagged, branch-aware publishing pipeline that supports
multiple programming languages and GitHub Packages distribution. This document captures the workflow
components, execution flow, and configuration touchpoints required for migration.

## Goals

- Provide a reusable release pipeline that adapts to Go, Rust, Python, and Node.js repositories.
- Support stable branches with language-specific tags (for example, `v1.2.3-go124`).
- Keep the new workflow opt-in via feature flags while the legacy workflow remains available.
- Generate changelog summaries automatically from conventional commits.
- Prepare artifacts for GitHub Releases and GitHub Packages distribution.

## High-Level Flow

1. `release.yml` runs on tag pushes or manual dispatches.
2. The **check feature flag** job inspects `.github/repository-config.yml`.
3. If `workflows.experimental.use_new_release` is `true`, the workflow invokes
   `reusable-release.yml`; otherwise the legacy workflow prints migration guidance and exits.
4. `reusable-release.yml`:
   - Detects the primary language with `release_workflow.py`.
   - Computes semantic versions and branch-aware tags.
   - Builds artifacts for the detected language.
   - Creates a GitHub Release and uploads assets.
   - Triggers GitHub Packages publishing when enabled.
5. If the feature flag is disabled, the legacy workflow remains the active release path.

## Component Overview

### Feature Flag Gate (`release.yml`)

- **Job:** `check-feature-flag`
- **Responsibility:** Parse `.github/repository-config.yml` (via `pyyaml`) to decide whether the new
  system should run.
- **Outputs:** `use_new_release` for downstream jobs.
- **Fallback:** When disabled, the legacy job prints migration guidance.

### Reusable Release Orchestrator (`reusable-release.yml`)

The workflow is split into focused jobs:

- `prepare-release` – Check out the repository, run `release_workflow.py`, and publish outputs
  (`tag`, `version`, `language`, `branch`, `is_stable`, `changelog`).
- `build-go` / `build-rust` / `build-python` / `build-node` – Language-specific builds keyed off the
  detected language.
- `create-release` – Aggregate artifacts, generate a manifest, and create the GitHub Release with
  draft/prerelease semantics derived from the branch strategy.
- `publish-github-packages` – Bundle artifacts and upload them via `publish_to_github_packages.py`
  when the GitHub registry is enabled.
- `build-status` – Runs `generate_release_summary.py` to produce the final Markdown summary and exit
  with a failure if any component failed.

All jobs inherit repository permissions for releases (`contents: write`, `packages: write`) and
surface their state in the final summary job.

### Release Metadata (`release_workflow.py`)

The helper script encapsulates:

- Primary language detection from manifest files (`Cargo.toml`, `go.mod`, `pyproject.toml`,
  `package.json`).
- Branch analysis with support for `stable-1-<language>-<version>` naming.
- Semantic version discovery or overrides (workflow dispatch input).
- Tag assembly (`v1.2.3` for main, `v1.2.3-go124` for `stable-1-go-1.24`).
- Conventional commit parsing to build categorized changelog sections.

The script writes outputs for GitHub Actions usage and appends human-readable summaries to the job
log.

### Artifact Production

Each language job builds and uploads artifacts consumed later by `create-release` and
`publish-github-packages`:

- **Go:** Matrix builds across Linux/macOS (amd64, arm64) with `go build`.
- **Rust:** Cross-target builds using `actions-rust-lang/setup-rust-toolchain`.
- **Python:** Wheel/source distribution via `python -m build`.
- **Node.js:** Optional `npm run build`, followed by `npm pack` to produce tarballs.

### Publishing Stage

`publish-github-packages` downloads merged artifacts and invokes `publish_to_github_packages.py`,
which:

1. Reads configuration to confirm the GitHub registry is enabled.
2. Bundles artifacts into a tarball named after language/branch context.
3. Uploads the tarball as a generic GitHub Package via `gh api` and annotates the job summary.

Future enhancements can extend this job to publish to external registries (npm, PyPI, crates.io)
when secrets are configured in `.github/repository-config.yml`.

### Maintenance Automation

The reusable maintenance workflow uses `maintenance_workflow.py` to parse language-specific reports
(pip, npm, cargo, go), build dependency summaries, and append results to the GitHub Actions step
summary. JSON reports are generated earlier in the job and uploaded along with the Markdown summary
for review.

## Branch and Tag Strategy

| Branch Pattern         | Tag Example         | Package Identifier Example           |
| ---------------------- | ------------------- | ------------------------------------ |
| `main`                 | `v1.2.3`            | `github.com/owner/repo@v1.2.3`       |
| `stable-1-go-1.24`     | `v1.2.3-go124`      | `github.com/owner/repo@v1.2.3-go124` |
| `stable-1-python-3.13` | `v1.2.3-python313`  | `package-name==1.2.3+python313`      |
| `stable-1-node-20`     | `v1.2.3-node20`     | `@owner/package@1.2.3-node20`        |
| `stable-1-rust-stable` | `v1.2.3-ruststable` | `package-name 1.2.3+rust-stable`     |

Tag composition is handled inside `release_workflow.py` to ensure consistent formatting per
language.

## Configuration Inputs

- `.github/repository-config.yml` controls feature flags and registry enablement.
- Secrets:
  - `GITHUB_TOKEN` (auto-provided) for releases and GitHub Packages.
  - Optional registry tokens (`NPM_TOKEN`, `PYPI_TOKEN`, `CARGO_REGISTRY_TOKEN`) for external
    publishing.
- Workflow dispatch inputs (`version`, `draft`, `prerelease`) allow manual overrides.

## Migration Considerations

- Keep the feature flag disabled until the new workflow is validated in dry runs.
- Follow the rollout checklist (`docs/refactors/workflows/v2/rollout-checklist.md`) before removing
  the legacy workflow.
- When enabling GitHub Packages, ensure documentation in `github-packages-setup.md` is followed and
  secrets are configured.
