<!-- file: docs/unified-automation.md -->
<!-- version: 1.0.0 -->
<!-- guid: 3153c13c-f92e-4828-aef7-f1e175f22e32 -->

# Unified Automation Workflow

A reusable GitHub Actions workflow that orchestrates issue management,
documentation updates, duplicate cleanup, labeling, linting, and AI-powered automation. It exposes
numerous inputs so each repository can fine-tune exactly which tasks run and how
they're configured.

## Overview

Use the workflow `reusable-unified-automation.yml` in this repository to combine
multiple automation tasks into a single job. You can run all operations or pick
specific ones.

## Usage

```yaml
jobs:
  automation:
    uses: jdfalk/ghcommon/.github/workflows/reusable-unified-automation.yml@main
    with:
      operation: all # or issues, docs, lint, intelligent-labeling, duplicates
      # Additional inputs can override defaults for each sub-workflow
    secrets: inherit
```

For a minimal example see
[`examples/workflows/unified-automation.yml`](../examples/workflows/unified-automation.yml).
The `unified-automation.yml` workflow exposes the same inputs for manual
invocation. **Tip:** Use the `unified-automation.yml` workflow in your
repository to manually run or schedule the orchestrator.

## Inputs

- **operation** – Which operations to run (`all`, `issues`, `docs`, `lint`,
  `intelligent-labeling`, `duplicates`).
- **duplicates** – Runs duplicate issue cleanup in parallel for immediate
  deduplication.
- **im_operations** – Operations for the issue management workflow.
- **im_dry_run** – Run issue management in dry-run mode.
- **docs_updates_directory** – Directory containing documentation updates.
- **labeler_configuration_path** – Path to the pull request labeler
  configuration.
- **sl_validate_all_codebase** – Lint entire codebase instead of changed files.
- **rebase_base_branch** – Branch to rebase pull requests onto.

See the workflow file for the full list of available inputs.

## Manual Execution

Run the workflow from the Actions tab using workflow_dispatch inputs to control operations
