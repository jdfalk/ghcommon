<!-- file: .github/copilot-instructions.md -->
<!-- version: 2.4.0 -->
<!-- guid: 4d5e6f7a-8b9c-0d1e-2f3a-4b5c6d7e8f9a -->
<!-- last-edited: 2026-06-13 -->

# github-common — Additional Context

Org-wide coding standards (file headers, language rules, commit format) are at
**<https://github.com/falkcorp/.github>** and apply automatically to this repo.

For full project context: **CLAUDE.md** at the repo root.

## Project overview

Reusable GitHub Actions workflows, scripts, and multi-repo automation. Language: Python.

## Key directories

| Path | Purpose |
|---|---|
| `.github/workflows/reusable-*.yml` | Reusable workflows called by other repos |
| `scripts/` | Python automation tools for cross-repo operations |
| `.github/instructions/` | Modular AI agent rules with language targeting |

## Critical constraints

- `scripts/intelligent_sync_to_repos.py` — propagates changes to target repos; use `--dry-run` first
- `scripts/workflow-debugger.py` — analyzes workflow failures; outputs to `workflow-debug-output/fix-tasks/`
- All commits must use conventional commit format: `type(scope): description`
