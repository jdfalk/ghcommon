<!-- file: docs/add-to-project.md -->
<!-- version: 1.0.0 -->
<!-- guid: de8c16e6-d74c-4914-9a04-666d8b4fb2db -->

# Add To Project Workflow

A reusable GitHub Actions workflow for automatically adding issues and pull requests to GitHub Projects.

## Workflow Architecture

- **Canonical Workflow**: `jdfalk/ghcommon/.github/workflows/reusable-add-to-project.yml@main`
- **Documentation**: This file (`docs/add-to-project.md`)
- **Example**: `/examples/workflows/add-to-project.yml`

## Quick Start

1. Copy the example workflow to your repository:

```bash
curl -o .github/workflows/add-to-project.yml \
  https://raw.githubusercontent.com/jdfalk/ghcommon/main/examples/workflows/add-to-project.yml
```

2. Update `project-url` with the URL of your GitHub Project.

## Example Workflow

```yaml
name: Add Issues to Project

on:
  issues:
    types: [opened, reopened, transferred, labeled]
  pull_request:
    types: [opened, reopened, labeled]

jobs:
  add-to-project:
    uses: jdfalk/ghcommon/.github/workflows/reusable-add-to-project.yml@main
    with:
      project-url: https://github.com/orgs/<org>/projects/<number>
    secrets:
      github-token: ${{ secrets.ADD_TO_PROJECT_PAT }}
```

## Inputs

- `project-url` (**required**) - URL of the GitHub project
- `labeled` (optional) - Comma-separated list of labels to match
- `label-operator` (optional) - Label filter behavior (`AND`, `OR`, `NOT`)

## Secrets

- `github-token` - Personal access token with project write access
