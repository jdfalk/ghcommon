# Scripts Directory

This directory contains reusable scripts for GitHub automation and issue management.

## Available Scripts

### [`issue_manager.py`](issue_manager.py)
**Version**: 2.0.0
**Last Updated**: 2025-06-21

Unified GitHub issue management script with comprehensive functionality:
- Process issue updates from JSON files (legacy and distributed formats)
- Manage Copilot review comment tickets
- Close duplicate issues by title
- Generate tickets for CodeQL security alerts
- GUID-based duplicate prevention
- Support for both legacy `issue_updates.json` and new distributed `.github/issue-updates/` formats

Used by the [`unified-issue-management.yml`](../.github/workflows/unified-issue-management.yml) reusable workflow.

### [`create-issue-update.sh`](create-issue-update.sh)
**Version**: 1.0.0
**Last Updated**: 2025-06-21

Helper script to create new issue update files with proper UUIDs in the distributed format.

**Usage**:
```bash
# Create a new issue
./scripts/create-issue-update.sh create "Issue Title" "Description" "label1,label2"

# Update an existing issue
./scripts/create-issue-update.sh update 123 "Updated description" "label1,label2"

# Add comment to issue
./scripts/create-issue-update.sh comment 123 "Comment text"

# Close an issue
./scripts/create-issue-update.sh close 123 "completed"
```

**Features**:
- Automatic UUID generation for file names
- GUID generation for duplicate prevention
- Creates files in `.github/issue-updates/` directory
- Supports all issue actions: create, update, comment, close

## Installation

### For Repositories Using ghcommon

To copy these scripts to your repository:

```bash
# Copy the issue update helper script
curl -fsSL https://raw.githubusercontent.com/jdfalk/ghcommon/main/scripts/create-issue-update.sh -o scripts/create-issue-update.sh
chmod +x scripts/create-issue-update.sh

# The issue_manager.py is automatically downloaded by the reusable workflow
```

### Version Checking

Each script includes version information in the header comments. Check the version to see if updates are available:

```bash
head -n 10 scripts/create-issue-update.sh | grep "version:"
```

## Workflow Integration

These scripts are designed to work with the unified issue management reusable workflow. See the [workflow examples](../examples/workflows/) for integration patterns.

## Dependencies

- **Python 3.x** (for issue_manager.py)
- **requests** library (for GitHub API calls)
- **bash** (for create-issue-update.sh)
- **uuidgen** or **python3** (for UUID generation)

## Contributing

When updating scripts:
1. Increment the version number
2. Update the last-updated date
3. Document changes in the script header
4. Update this README if needed
5. Test with the reusable workflow

## Support

For issues or questions:
- Check the [examples directory](../examples/) for usage patterns
- Review the [migration guide](../examples/migration-guides/subtitle-manager-migration.md)
- Open an issue in the ghcommon repository
