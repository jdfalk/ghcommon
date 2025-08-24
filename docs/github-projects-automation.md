<!-- file: docs/github-projects-automation.md -->
<!-- version: 1.0.0 -->
<!-- guid: f6a7b8c9-d0e1-2345-f012-678901234567 -->

# GitHub Projects Automation

This document describes the automated GitHub Projects integration setup across all repositories.

## Overview

⚠️ Note: Custom add-to-project workflows have been removed. GitHub's built-in project automation now
handles issue and PR assignment. ⚠️ Note: Custom add-to-project workflows have been removed.
GitHub's built-in project automation now handles issue and PR assignment. ⚠️ Note: Custom
add-to-project workflows have been removed. GitHub's built-in project automation now handles issue
and PR assignment. ⚠️ Note: Custom add-to-project workflows have been removed. GitHub's built-in
project automation now handles issue and PR assignment.

⚠️ Note: Custom add-to-project workflows have been removed. GitHub's built-in project automation now
handles issue and PR assignment. ⚠️ Note: Custom add-to-project workflows have been removed.
GitHub's built-in project automation now handles issue and PR assignment. ⚠️ Note: Custom
add-to-project workflows have been removed. GitHub's built-in project automation now handles issue
and PR assignment.

We use a reusable workflow to automatically add issues and pull requests to GitHub Projects based on
labels and repository context.

## Reusable Workflow

The main reusable workflow is located at:

- **Repository**: `jdfalk/ghcommon`
- **Path**: `.github/workflows/reusable-add-to-project.yml`
- **Action Used**: `actions/add-to-project@v1.0.2`

### Features

- ✅ Automatic issue and PR assignment to projects
- ✅ Label-based filtering with AND/OR operators
- ✅ URL validation for project paths
- ✅ Comprehensive error handling and logging
- ✅ Support for both user and organization projects

## Repository Configurations

### ghcommon Repository

**Projects Used:**

- **Cleanup Project** (#9): `https://github.com/users/jdfalk/projects/9`
  - Triggers: `bug`, `documentation`, `infrastructure`, `cleanup` labels
- **Core Improvements** (#10): `https://github.com/users/jdfalk/projects/10`
  - Triggers: `enhancement`, `feature`, `improvement`, `automation` labels
- **Testing & Quality** (#11): `https://github.com/users/jdfalk/projects/11`
  - Triggers: `testing`, `quality`, `ci`, `workflow` labels
- **Fallback**: Unlabeled items go to Cleanup Project

### subtitle-manager Repository

**Projects Used:**

- **Subtitle Manager Development** (#5): `https://github.com/users/jdfalk/projects/5`
  - Triggers: All issues and PRs

### gcommon Repository

**Projects Used:**

- **gCommon Development** (#2): `https://github.com/users/jdfalk/projects/2`
  - Triggers: All issues and PRs

### codex-cli Repository

**Projects Used:**

- **Core Improvements** (#10): `https://github.com/users/jdfalk/projects/10`
  - Triggers: All issues and PRs (automation tooling)

## Required Secrets

Each repository needs the following secret configured:

```yaml
JF_CI_GH_PAT: <GitHub Personal Access Token>
```

### PAT Requirements

The Personal Access Token must have the following scopes:

- `repo` - For accessing repository issues and PRs
- `project` - For adding items to projects
- `read:project` - For reading project information

### Setting Up Secrets

1. Go to repository Settings → Secrets and variables → Actions
2. Add new repository secret: `JF_CI_GH_PAT`
3. Use the same PAT value across all repositories

## Workflow Triggers

The automation triggers on:

- `issues.opened`
- `issues.reopened`
- `issues.labeled`
- `pull_request.opened`
- `pull_request.reopened`
- `pull_request.labeled`

## Usage Examples

### Adding Custom Labels

To modify which labels trigger project assignment, edit the calling workflow:

```yaml
with:
  project-url: 'https://github.com/users/jdfalk/projects/9'
  labeled: 'bug,documentation,urgent'
  label-operator: 'OR' # OR means any of these labels
```

### Adding New Projects

1. Create the project using `scripts/create-projects.sh` or GitHub UI
2. Get the project URL
3. Add a new job to the calling workflow:

```yaml
add-to-new-project:
  name: Add to New Project
  uses: jdfalk/ghcommon/.github/workflows/reusable-add-to-project.yml@main
  secrets:
    gh-token: ${{ secrets.JF_CI_GH_PAT }}
  with:
    project-url: 'https://github.com/users/jdfalk/projects/NEW_NUMBER'
    labeled: 'specific,labels'
```

## Troubleshooting

### Common Issues

1. **"Unable to find reusable workflow"**
   - Ensure the reusable workflow is committed to the main branch
   - Check the repository reference format

2. **"Context access might be invalid: JF_CI_GH_PAT"**
   - Set up the secret in repository settings
   - Verify the secret name matches exactly

3. **"Invalid project URL format"**
   - Use format: `https://github.com/users/USERNAME/projects/NUMBER`
   - For organizations: `https://github.com/orgs/ORGNAME/projects/NUMBER`

4. **"Insufficient permissions"**
   - Verify PAT has `project` and `read:project` scopes
   - Ensure the PAT user has access to the target project

### Debugging

Check workflow runs in Actions tab:

- Repository → Actions → Select the workflow run
- Review logs for validation and error messages
- Verify project URLs and label configurations

## Maintenance

### Updating the Reusable Workflow

1. Modify `.github/workflows/reusable-add-to-project.yml` in `ghcommon`
2. Commit changes to main branch
3. Changes automatically apply to all calling repositories

### Adding New Repositories

1. Copy an existing calling workflow
2. Modify project URLs and label filters
3. Ensure `JF_CI_GH_PAT` secret is configured
4. Test with a new issue or PR

## Project URLs Reference

| Project                      | Number | URL                                         |
| ---------------------------- | ------ | ------------------------------------------- |
| ghcommon Cleanup             | #9     | https://github.com/users/jdfalk/projects/9  |
| ghcommon Core Improvements   | #10    | https://github.com/users/jdfalk/projects/10 |
| ghcommon Testing & Quality   | #11    | https://github.com/users/jdfalk/projects/11 |
| Subtitle Manager Development | #5     | https://github.com/users/jdfalk/projects/5  |
| gCommon Development          | #2     | https://github.com/users/jdfalk/projects/2  |
