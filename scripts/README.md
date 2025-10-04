<!-- file: scripts/README.md -->
<!-- version: 2.0.0 -->
<!-- guid: a6ce4820-bcf8-482e-b2ca-234024d5d77f -->

# Scripts Directory

This directory contains reusable scripts for GitHub automation, workflow debugging, and multi-repository management.

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

These scripts are primarily used by the central ghcommon repository for managing other repositories. Individual repositories typically don't need to copy these scripts locally.

### Version Checking

Each script includes version information in the header comments. Check the version to see if updates are available:

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
