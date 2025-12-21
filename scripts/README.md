<!-- file: scripts/README.md -->
<!-- version: 2.0.1 -->
<!-- guid: a6ce4820-bcf8-482e-b2ca-234024d5d77f -->

# Scripts Directory

This directory contains reusable scripts for GitHub automation, workflow debugging, and
multi-repository management.

## Available Scripts

### [`workflow-debugger.py`](workflow-debugger.py)

**Version**: 1.0.0 **Last Updated**: 2025-10-03

Advanced workflow failure analysis and automated fix task generation:

- Analyzes workflow failures across repositories
- Categorizes failures: permissions, dependencies, syntax, infrastructure
- Generates JSON fix tasks for Copilot agents
- Outputs actionable remediation steps with code examples
- Supports scanning multiple repositories and organizations

**Usage**:

```bash
# Analyze failures across all repositories
python scripts/workflow-debugger.py --org jdfalk --scan-all --fix-tasks

# Analyze specific repository
python scripts/workflow-debugger.py --org jdfalk --repo ubuntu-autoinstall-agent --fix-tasks
```

### [`intelligent_sync_to_repos.py`](intelligent_sync_to_repos.py)

**Version**: 1.0.0 **Last Updated**: 2025-10-03

Intelligent synchronization of configurations and instructions across repositories:

- Syncs `.github/instructions/`, `.github/prompts/`, and workflows to target repos
- Creates VS Code Copilot symlinks: `.vscode/copilot/` → `.github/instructions/`
- Handles repository-specific file exclusions and maintains file headers
- Supports dry-run mode for testing changes

**Usage**:

```bash
# Sync to specific repositories (dry run)
python scripts/intelligent_sync_to_repos.py --target-repos "repo1,repo2" --dry-run

# Sync to all configured repositories
python scripts/intelligent_sync_to_repos.py
```

### [`label_manager.py`](label_manager.py)

**Version**: 1.2.0 **Last Updated**: 2025-06-21

GitHub label synchronization and management across repositories:

- Synchronizes labels from central configuration
- Supports label creation, updating, and deletion
- Handles repository-specific label configurations
- Provides detailed reporting and error handling

## Installation

### For Repositories Using ghcommon

These scripts are primarily used by the central ghcommon repository for managing other repositories.
Individual repositories typically don't need to copy these scripts locally.

### Version Checking

Each script includes version information in the header comments. Check the version to see if updates
are available:

```bash
head -n 10 scripts/script-name.py | grep "version:"
```

## Dependencies

- **Python 3.x** (for all Python scripts)
- **requests** library (for GitHub API calls)
- **PyYAML** library (for configuration parsing)
- **GitHub CLI** (`gh`) installed and authenticated
- Proper repository permissions for cross-repo operations

## Contributing

When updating scripts:

1. Increment the version number in the script header
2. Update the last-updated date
3. Document changes in the script header comments
4. Update this README if script functionality changes
5. Test with target repositories before deployment

## Support

For issues or questions:

- Check the [workflow debugging output](workflow-debug-output/) for analysis results
- Review the [main repository documentation](../README.md)
- Open an issue in the ghcommon repository

---

## 🆕 Action Management Scripts (NEW)

### [`quick-start-guide.sh`](quick-start-guide.sh)

**Version**: 1.0.0 **Purpose**: Interactive guide for action pinning workflow

Step-by-step interactive script that guides you through:

- Committing release-go-action changes
- Tagging release-go-action as v2.0.0
- Pinning all actions to commit hashes
- Next steps for workflow conversion

**Usage**:

```bash
# Run the interactive guide
./scripts/quick-start-guide.sh

# The script will prompt you at each step for confirmation
```

**What It Does**:

1. Checks release-go-action git status
2. Optionally commits and pushes changes
3. Tags release-go-action as v2.0.0, v2.0, v2
4. Runs action pinning script
5. Commits and pushes pinned versions
6. Shows next steps

---

### [`pin-actions-to-hashes.py`](pin-actions-to-hashes.py)

**Version**: 1.0.0 **Purpose**: Pin all jdfalk/\* actions to commit hashes

Comprehensive action version management:

- Discovers all jdfalk/\* action repositories automatically
- Gets latest release tags for each action
- Retrieves commit hashes for those tags
- Updates all workflow files to use `hash@commit # vX.Y.Z` format
- Generates `ACTION_VERSIONS.md` reference table

**Usage**:

```bash
# Run the pinning script
python3 scripts/pin-actions-to-hashes.py

# This will:
# - Update .github/workflows/*.yml files
# - Create ACTION_VERSIONS.md
# - Show summary of changes
```

**Output Example**:

```
🔍 Discovering action versions and hashes...

  release-go-action: v2.0.0 @ abc1234
  release-docker-action: v1.0.0 @ def5678
  ...

📝 Updating workflow files...

  ✅ Updated release-go.yml
  ✅ Updated release-docker.yml
  ...

✅ Updated 7 workflow files
📄 Updated ACTION_VERSIONS.md
```

---

### [`tag-release-go-v2.sh`](tag-release-go-v2.sh)

**Version**: 1.0.0 **Purpose**: Tag release-go-action as v2.0.0

Creates Git tags for the release-go-action major version update:

- Creates annotated `v2.0.0` tag with full changelog
- Creates rolling `v2.0` and `v2` tags
- Pushes all tags to GitHub
- Displays commit hash for workflow pinning

**Usage**:

```bash
# Tag release-go-action (from ghcommon directory)
./scripts/tag-release-go-v2.sh

# This will:
# - Create v2.0.0, v2.0, v2 tags
# - Push to origin
# - Show commit hash
```

**Important**: Only run this after committing all release-go-action changes.

---

## Action Pinning Workflow

The complete workflow for pinning actions:

```bash
# 1. Ensure release-go-action changes are committed
cd /Users/jdfalk/repos/github.com/jdfalk/release-go-action
git status
# If changes exist, commit them

# 2. Use the quick-start guide (RECOMMENDED)
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon
./scripts/quick-start-guide.sh

# OR do it manually:

# 2a. Tag release-go-action
./scripts/tag-release-go-v2.sh

# 2b. Pin actions to hashes
python3 scripts/pin-actions-to-hashes.py

# 2c. Review and commit
git diff .github/workflows/
git add .github/workflows/ ACTION_VERSIONS.md
git commit -m "chore(workflows): pin actions to commit hashes"
git push
```

---

## Generated Files

These files are generated by the action management scripts:

### `ACTION_VERSIONS.md` (Root Directory)

Generated by: `pin-actions-to-hashes.py`

Reference table showing:

- Action repository names
- Current version tags
- Commit hashes
- Usage format

**Example**:

| Action Repository | Version | Commit Hash | Usage                                       |
| ----------------- | ------- | ----------- | ------------------------------------------- |
| release-go-action | v2.0.1  | `abc1234`   | `jdfalk/release-go-action@abc1234 # v2.0.1` |

---

## Related Documentation

- [`ACTION_PINNING_PLAN.md`](../ACTION_PINNING_PLAN.md) - Complete pinning strategy
- [`OVERNIGHT_PROGRESS_SUMMARY.md`](../OVERNIGHT_PROGRESS_SUMMARY.md) - Progress summary
- [`TODO.md`](../TODO.md) - Task tracking

---

## Version History

- **v2.0.0** (2025-12-19): Added action management scripts
  - Added `quick-start-guide.sh`
  - Added `pin-actions-to-hashes.py`
  - Added `tag-release-go-v2.sh`
  - Updated documentation
