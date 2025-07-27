<!-- file: examples/migration-guides/subtitle-manager-migration.md -->

# Migration Guide: subtitle-manager to Centralized Issue Management

This guide shows how to migrate the subtitle-manager repository from its custom
issue management workflow to the centralized reusable workflow in ghcommon.

## Overview

The subtitle-manager repository currently has a sophisticated issue management
system with:

- Advanced Python script (962 lines) with comprehensive functionality
- Full workflow with matrix strategy and parallel execution
- GUID-based duplicate prevention
- Support for multiple operations (update-issues, copilot-tickets,
  close-duplicates, codeql-alerts)

We'll migrate this to use the centralized reusable workflow from ghcommon while
preserving all functionality.

## Migration Steps

### Step 1: Backup Current Implementation

Before migrating, backup the current files:

```bash
# Create backup directory
mkdir -p migration-backup

# Backup current workflow
cp .github/workflows/reusable-unified-issue-management.yml migration-backup/

# Backup current script
cp .github/scripts/issue_manager.py migration-backup/
```

### Step 2: Replace Workflow File

Replace the current workflow with the new one that calls the reusable workflow:

```yaml
# file: .github/workflows/reusable-unified-issue-management.yml
#
# Migrated Issue Management Workflow (Using Reusable Workflow)
#
# This workflow now uses the centralized reusable workflow from ghcommon
# instead of maintaining its own copy of the issue management logic.

name: Unified Issue Management

on:
  # Issue updates from JSON file
  push:
    branches: [main, master]
    paths: [issue_updates.json]

  # Copilot review ticket management
  pull_request_review_comment:
    types: [created, edited, deleted]
  pull_request_review:
    types: [submitted, edited, dismissed]
  pull_request:
    types: [closed]

  # Scheduled operations
  schedule:
    # Close duplicates daily at 1 AM UTC
    - cron: '0 1 * * *'
    # CodeQL alert tickets twice daily at 8 AM and 8 PM UTC
    - cron: '0 8,20 * * *'

  # Manual triggers
  workflow_dispatch:
    inputs:
      operations:
        description: 'Operations to run (comma-separated or auto)'
        required: false
        type: string
        default: 'auto'
      dry_run:
        description: 'Run in dry-run mode (no changes)'
        required: false
        type: boolean
        default: false
      force_update:
        description: 'Force update existing tickets'
        required: false
        type: boolean
        default: false

jobs:
  # Use the centralized reusable workflow from ghcommon
  issue-management:
    uses: jdfalk/ghcommon/.github/workflows/reusable-unified-issue-management.yml@main
    with:
      operations: ${{ github.event.inputs.operations || 'auto' }}
      dry_run: ${{ github.event.inputs.dry_run == 'true' }}
      force_update: ${{ github.event.inputs.force_update == 'true' }}
      issue_updates_file: 'issue_updates.json'
      cleanup_issue_updates: true
      python_version: '3.11'
    secrets: inherit
```

### Step 3: Remove Local Script (Optional)

Since the centralized workflow downloads its own copy of the script, you can
remove the local copy:

```bash
# Remove the local script (it's now centralized in ghcommon)
rm -f .github/scripts/issue_manager.py
```

**Note**: Keep the script if you want to run operations locally for testing.

### Step 4: Test the Migration

1. **Test with a dry run**:

   ```bash
   # Go to Actions tab in GitHub
   # Click "Unified Issue Management"
   # Click "Run workflow"
   # Set dry_run to true
   # Set operations to "close-duplicates" (safe test)
   ```

2. **Test with issue updates**: Create a test `issue_updates.json`:

   ```json
   {
     "comment": [
       {
         "number": 1,
         "body": "Test comment from migrated workflow",
         "guid": "migration-test-2024-06-20-001"
       }
     ]
   }
   ```

3. **Verify all triggers work**:
   - Push the `issue_updates.json` file
   - Create a PR and add Copilot review comments
   - Check scheduled runs

### Step 5: Update Documentation

Update any repository documentation that references the old workflow:

1. **README.md**: Update any references to the issue management system
2. **CONTRIBUTING.md**: Update contributor guidelines if they mention the
   workflow
3. **docs/**: Update any technical documentation

## Benefits of Migration

### Centralized Maintenance

- **Single source of truth**: All improvements benefit all repositories
- **Consistent behavior**: Same functionality across all repos
- **Easier updates**: No need to sync changes manually

### Reduced Repository Complexity

- **Smaller repo size**: Remove 962-line script
- **Simpler workflow**: Focus on configuration, not implementation
- **Less maintenance**: No local script to maintain

### Enhanced Features

- **Always up-to-date**: Automatically get latest improvements
- **Better documentation**: Centralized docs and examples
- **Community contributions**: Benefits from broader usage

## Compatibility

### Preserved Features

✅ All current functionality is preserved:

- JSON-based issue updates (both flat and grouped formats)
- GUID-based duplicate prevention
- Copilot review ticket management
- Duplicate issue closure
- CodeQL security alert tickets
- Matrix-based parallel execution
- Comprehensive logging and summaries

### Enhanced Features

✅ Additional features available:

- Auto-detection of operations based on event context
- More flexible configuration options
- Better error handling and reporting
- Standardized across repositories

### Breaking Changes

❌ No breaking changes:

- Same trigger events supported
- Same input parameters
- Same environment variables
- Same `issue_updates.json` format

## Rollback Plan

If you need to rollback to the original implementation:

```bash
# Restore original files
cp migration-backup/reusable-unified-issue-management.yml .github/workflows/
cp migration-backup/issue_manager.py .github/scripts/

# Commit the changes
git add .
git commit -m "Rollback to local issue management implementation"
git push
```

## Verification Checklist

After migration, verify:

- [ ] Workflow appears in Actions tab
- [ ] Manual trigger works with dry-run
- [ ] Push with `issue_updates.json` triggers workflow
- [ ] PR review comments trigger Copilot ticket management
- [ ] Scheduled runs appear in workflow history
- [ ] All operations complete successfully
- [ ] Logs show operations are executed properly
- [ ] Issue updates are processed correctly

## Support

If you encounter issues during migration:

1. **Check workflow logs** for detailed error messages
2. **Verify permissions** are correctly set in repository settings
3. **Test with dry-run** to debug without making changes
4. **Review examples** in ghcommon repository
5. **Create issue** in ghcommon repository with migration problems

## Conclusion

This migration centralizes issue management while preserving all existing
functionality. The subtitle-manager repository will now benefit from ongoing
improvements to the centralized system while reducing its own maintenance
burden.
