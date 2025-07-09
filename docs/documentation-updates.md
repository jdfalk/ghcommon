<!-- file: docs/documentation-updates.md -->
<!-- version: 1.0.0 -->
<!-- guid: b1d1f0f3-9c8a-4c9b-8cc6-b0fc9c573c10 -->

# Documentation Updates Workflow

A centralized workflow for updating `README.md`, `CHANGELOG.md` and `TODO.md`.
Jobs create JSON files in `.github/doc-updates/` with the helper script and the
workflow applies them to reduce merge conflicts.

## Usage

1. Generate an update file:

```bash
./scripts/create-doc-update.sh README.md "Add new section" 
```

2. Commit the generated JSON file.
3. Trigger the `reusable-docs-update.yml` workflow.

Processed files are moved to `.github/doc-updates/processed/`.
