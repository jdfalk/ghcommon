<!-- file: docs/refactors/workflows/v2/reference/workflow-reference.md -->
<!-- version: 1.1.0 -->
<!-- guid: 4d5e6f70-8192-a3b4-c5d6-e7f8091a2b3c -->

# Workflow v2 Reference

## `release.yml`

- **`check-feature-flag`** – Loads `.github/repository-config.yml` with `pyyaml` to detect whether the new release system should run.
- **`new-release`** – Invokes `reusable-release.yml` when enabled.
- **`legacy-release`** – Provides migration guidance when the feature flag is disabled.

## `reusable-release.yml`

- `prepare-release` – Generates release metadata via `release_workflow.py`.
- `build-*` – Language-specific build jobs (Go, Rust, Python, Node).
- `create-release` – Packages artifacts and creates GitHub releases.
- `publish-github-packages` – Uploads artifacts via `publish_to_github_packages.py`.
- `build-status` – Calls `generate_release_summary.py` to append a Markdown summary and exit on failure.

## `docs_workflow.py`

- `generate_api_docs(source_dirs, output_dir)` – Produce helper module documentation.
- `generate_workflow_docs(workflows_dir, output)` – Summarize GitHub workflow YAML files.
- `build_documentation(source_dirs, workflows_dir, output, version)` – Build versioned doc tree with search index.
- CLI commands: `generate-api`, `generate-workflows`, `build`.

## `maintenance_workflow.py`

- `collect_dependency_updates(pip_path, npm_path, cargo_path, go_path)` – Parse dependency reports.
- `summarize_dependency_updates(updates)` – Append dependency summary to GitHub step summary.
- `parse_stale_items(data, days)` – Filter stale issues/PRs.
- CLI commands:
  - `summarize-dependencies` – Aggregate JSON reports into Markdown and artifacts.
  - `summarize-stale` – Generate table for stale issues/PRs.

## Inputs, Outputs, and Secrets Summary

| Component          | Inputs / Env                               | Outputs / Artifacts                     | Secrets          |
|-------------------|--------------------------------------------|-----------------------------------------|------------------|
| `release.yml`     | `.github/repository-config.yml`             | `use_new_release`                       | _None_           |
| `prepare-release` | Git history, optional version override      | `tag`, `version`, `language`, `changelog` | _None_         |
| Build jobs        | Detected language configuration            | Built artifacts                          | _None_           |
| `create-release`  | Artifacts, changelog                        | GitHub Release                          | `GITHUB_TOKEN`   |
| `publish-packages`| Artifacts, configuration                    | GitHub Packages uploads                 | `GITHUB_TOKEN`   |
| `build-status`    | Component results                           | Markdown summary                        | _None_           |
| Docs build        | Helper scripts, workflows                   | Versioned documentation tree            | _None_           |
| Maintenance       | Dependency reports, stale data              | Markdown summaries + artifacts          | _None_           |

### Maintenance Workflow

- `dependency-updates` — Collect language-specific JSON reports and summarise via `maintenance_workflow.py summarize-dependencies`.
- `cleanup-tasks` — Repository cleanup and artifact upload.
- `license-check` — License audit and reporting.
- `security summary` — Optional step calling `maintenance_workflow.py summarize-security` to append advisories to the workflow summary.

