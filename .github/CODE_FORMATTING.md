# Code Formatting Configuration

## Overview

This repository uses a **unified formatting strategy** to prevent conflicts between different
formatters:

### Python

- **Formatter**: Ruff (both linting and formatting)
- **Import sorting**: Ruff (replaces isort)
- **Config**: `.github/linters/ruff.toml`
- **VS Code**: Configured to use `charliermarsh.ruff` extension

### JavaScript/TypeScript

- **Formatter**: Prettier
- **Linter**: ESLint
- **Config**: `.github/linters/.prettierrc.json` and `eslint.config.mjs`
- **VS Code**: Configured to use `esbenp.prettier-vscode` extension

### Shell Scripts

- **Formatter**: shfmt
- **Linter**: shellcheck
- **Style**: 2-space indentation, simplified syntax

### YAML

- **Formatter**: Prettier
- **Linter**: yamllint
- **Config**: `.yaml-lint.yml`
- **Max line length**: 200 characters

### Markdown

- **Formatter**: Prettier
- **Linter**: markdownlint
- **Config**: `.markdownlint.json`

## VS Code Setup

The `.vscode/settings.json` file configures:

- Python formatting to use Ruff exclusively
- Disables Black and isort to prevent conflicts
- Sets Prettier for JS/TS/JSON/YAML/Markdown
- Enables format-on-save

## Pre-commit Hooks

All formatters run automatically via pre-commit hooks:

```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Formatter Conflicts Resolution

**Problem**: Multiple formatters (Ruff, Black, isort, Prettier) competing for Python files.

**Solution**:

1. ✅ Use **Ruff only** for Python (linting + formatting + import sorting)
2. ✅ Prettier **excludes Python files** (`exclude_types: [python]`)
3. ✅ Black and isort **disabled** in pre-commit
4. ✅ VS Code configured to use Ruff for Python only

## CI Integration

The CI workflow uses the same configuration:

- `.github/linters/super-linter-ci.env` - Uses Ruff for Python
- `.github/workflows/reusable-ci.yml` - Runs Ruff checks

## Troubleshooting

### If VS Code still uses wrong formatter

1. Reload window: `Cmd+Shift+P` → "Reload Window"
2. Check installed extensions: Ruff extension should be active for Python
3. Verify settings: `.vscode/settings.json` should show Ruff as default formatter

### If pre-commit still conflicts

```bash
# Clear pre-commit cache
pre-commit clean

# Reinstall hooks
pre-commit install --install-hooks

# Run again
pre-commit run --all-files
```

### If imports format differently

- Ruff handles import sorting automatically
- Don't run isort or Black separately
- VS Code will use Ruff's import organization on save
