<!-- file: ACTION_REPO_STANDARDS.md -->
<!-- version: 1.0.0 -->
<!-- guid: a1b2c3d4-e5f6-7890-abcd-ef1234567890 -->

# Action Repository File Standards

This document defines the required and recommended files for all GitHub Action
repositories in the `jdfalk` organization.

## Required Files (100% Compliance)

All action repositories **MUST** have these files:

### Root Files

- **`action.yml`** - GitHub Action definition file
- **`README.md`** - Comprehensive documentation with usage examples
- **`CHANGELOG.md`** - Version history following Keep a Changelog format
- **`TODO.md`** - Track future work and known issues
- **`ruff.toml`** - Python linting configuration (even for non-Python actions)

### Configuration Files

- **`.pre-commit-config.yaml`** - Pre-commit hooks for code quality
- **`.yamllint`** - YAML linting configuration

### GitHub Files

- **`.github/dependabot.yml`** - Dependency update automation
- **`.github/copilot-instructions.md`** - AI agent context and instructions

## Recommended Files (Optional But Standardized)

These files should be present when applicable:

### Docker Actions

- **`Dockerfile`** - Only for dockerized actions
- **`.github/workflows/publish-docker.yml`** - Docker image publishing workflow

### Licensing

- **`LICENSE`** - MIT license for open source actions

### Code Quality

- **`.prettierrc`** - Code formatting configuration
- **`.gitignore`** - Git ignore patterns

### CI/CD

- **`.github/workflows/ci.yml`** - Continuous integration workflow (for complex
  actions)

## Future Standardization (Under Consideration)

These files are not yet standardized but may be added:

- **`.editorconfig`** - Editor configuration for consistent coding styles
- **`.github/CODEOWNERS`** - Define code ownership
- **`.github/PULL_REQUEST_TEMPLATE.md`** - PR template
- **`.markdownlint.yaml`** - Markdown linting rules
- **`.shellcheckrc`** - Shell script linting
- **`.github/workflows/lint.yml`** - Dedicated linting workflow

## File Content Standards

### `.pre-commit-config.yaml`

Should include hooks for:

- `ruff` - Python linting and formatting
- `yamllint` - YAML validation
- `end-of-file-fixer` - Ensure files end with newline
- `trailing-whitespace` - Remove trailing whitespace
- `check-yaml` - YAML syntax validation
- `check-added-large-files` - Prevent large file commits

### `.yamllint`

Standard configuration from ghcommon:

```yaml
extends: default
rules:
  line-length:
    max: 120
  indentation:
    spaces: 2
  document-start: disable
```

### `.github/dependabot.yml`

Should monitor:

- GitHub Actions (`github-actions`)
- Docker (if applicable)
- Python pip (if applicable)

### `.github/copilot-instructions.md`

Minimum content:

- Link to ghcommon standards
- Repository-specific context
- Key architectural decisions
- Critical workflows

## Compliance Status

As of 2026-01-11, the following repository needs updates:

### update-action-docker-ref-action

**Missing Files:**

- `.github/dependabot.yml`
- `.pre-commit-config.yaml`
- `.yamllint`

## Implementation Notes

### Template Files

Standard templates for required files are maintained in:

- `ghcommon/templates/action-repo/` (when created)

### Automated Checks

A validation script is available:

```bash
python3 scripts/validate-action-repo-files.py --repo <repo-name>
```

### Bulk Updates

For mass standardization:

```bash
python3 scripts/standardize-all-action-repos.py
```

## Version History

- **1.0.0** (2026-01-11): Initial standardization analysis and documentation

## References

- [Analysis Report](/Users/jdfalk/repos/temp_crap/action-repo-analysis.md)
- [GitHub Actions Best Practices](https://docs.github.com/en/actions/creating-actions/creating-a-composite-action)
- [Pre-commit Framework](https://pre-commit.com/)
