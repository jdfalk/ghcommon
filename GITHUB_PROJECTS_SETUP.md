<!-- file: GITHUB_PROJECTS_SETUP.md -->
<!-- version: 1.0.0 -->
<!-- guid: b8c9d0e1-f2a3-4567-b123-890123456789 -->

# GitHub Projects Automation Setup Summary

This document summarizes the GitHub Projects automation setup created across all repositories.
⚠️ The reusable add-to-project workflows described here have been removed. Repositories now rely on GitHub's built-in project automation.

## 🎯 What Was Created

### 1. Reusable Workflow (`ghcommon` repository)

**File**: `.github/workflows/reusable-add-to-project.yml`

**Features**:

- Uses `actions/add-to-project@v1.0.2` action
- Supports dynamic project URLs
- Label-based filtering with AND/OR operators
- Comprehensive validation and error handling
- Works with both user and organization projects

### 2. Calling Workflows (All Repositories)

**File**: `.github/workflows/add-to-project.yml` in each repo

**Triggers**:

- Issue opened/reopened/labeled
- PR opened/reopened/labeled

### 3. Project Mappings

| Repository         | Project(s)                        | Strategy               |
| ------------------ | --------------------------------- | ---------------------- |
| `ghcommon`         | Multiple projects based on labels | Smart routing by label |
| `subtitle-manager` | Subtitle Manager Development (#5) | All issues/PRs         |
| `gcommon`          | gCommon Development (#2)          | All issues/PRs         |
| `codex-cli`        | Core Improvements (#10)           | All issues/PRs         |

## 🔧 Technical Details

### Authentication

- Uses `JF_CI_GH_PAT` secret (your Personal Access Token)
- Required scopes: `repo`, `project`, `read:project`
- Configured in each repository's secrets

### Label-Based Routing (ghcommon)

- **Cleanup Project**: `bug`, `documentation`, `infrastructure`, `cleanup`
- **Core Improvements**: `enhancement`, `feature`, `improvement`, `automation`
- **Testing & Quality**: `testing`, `quality`, `ci`, `workflow`
- **Fallback**: Unlabeled items → Cleanup Project

## 📋 Next Steps

### 1. Set Up Secrets

Each repository needs the `JF_CI_GH_PAT` secret:

```bash
# For each repo, go to: Settings → Secrets and variables → Actions
# Add secret: JF_CI_GH_PAT with your PAT value
```

### 2. Commit and Push Workflows

The workflows need to be committed to trigger on future issues/PRs:

```bash
# In ghcommon repository
git add .github/workflows/reusable-add-to-project.yml
git add .github/workflows/add-to-project.yml
git add docs/github-projects-automation.md
git add scripts/test-project-automation.sh
git add GITHUB_PROJECTS_SETUP.md
git commit -m "feat: add GitHub Projects automation workflows"
git push

# Repeat for other repositories (they reference the ghcommon workflow)
```

### 3. Test the Setup

Run the test script to verify everything works:

```bash
./scripts/test-project-automation.sh
```

This will create test issues in each repository to verify the automation.

### 4. Monitor and Adjust

- Check Actions tabs for workflow runs
- Verify issues appear in correct projects
- Adjust label mappings as needed

## 🛠️ Customization

### Adding New Labels

Edit the calling workflow in the target repository:

```yaml
with:
  project-url: "https://github.com/users/jdfalk/projects/9"
  labeled: "bug,documentation,new-label"
  label-operator: "OR"
```

### Adding New Projects

1. Create project using `scripts/create-projects.sh`
2. Add new job to calling workflow
3. Configure appropriate label filters

### Changing Project Assignments

Modify the `project-url` and `labeled` inputs in the calling workflows.

## 📚 Documentation

- **Complete Documentation**: `docs/github-projects-automation.md`
- **Test Script**: `scripts/test-project-automation.sh`
- **Project Creation**: `scripts/create-projects.sh`

## 🔍 Troubleshooting

### Workflow Not Triggering

1. Ensure workflows are committed to main branch
2. Check repository secrets are configured
3. Verify PAT has required scopes

### Items Not Added to Projects

1. Check label filters match issue/PR labels
2. Verify project URLs are correct
3. Ensure PAT user has project access

### Authentication Errors

1. Refresh PAT scopes: `gh auth refresh -s project,read:project`
2. Verify secret name matches `JF_CI_GH_PAT`
3. Check PAT hasn't expired

## 🎉 Benefits

- ✅ **Automatic Organization**: Issues/PRs automatically go to appropriate projects
- ✅ **Consistent Workflow**: Same pattern across all repositories
- ✅ **Centralized Management**: Reusable workflow in one place
- ✅ **Flexible Configuration**: Easy to adjust mappings and add new projects
- ✅ **Comprehensive Logging**: Clear success/failure feedback

This setup provides a robust, automated way to manage GitHub Projects across your entire repository ecosystem!
