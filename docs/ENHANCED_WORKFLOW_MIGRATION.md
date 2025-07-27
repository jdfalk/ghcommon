# Migration Guide: Enhanced Workflows with Timestamp Lifecycle Tracking

This guide explains how to migrate from the original workflow automation to the
enhanced version with comprehensive timestamp lifecycle tracking v2.0.

## Overview

The enhanced workflows provide:

- **Enhanced timestamp format v2.0** with comprehensive lifecycle tracking
- **Chronological processing** based on `created_at` timestamps
- **Git-integrated timestamp recovery** for historical accuracy
- **Dependency resolution** via parent GUIDs
- **Comprehensive failure tracking** and rollback capabilities
- **Backwards compatibility** with existing formats

## Enhanced Scripts

### Enhanced Issue Manager

- **File**: `scripts/enhanced_issue_manager.py`
- **Version**: 2.0.0
- **Features**: Chronological processing, timestamp lifecycle tracking,
  dependency resolution

### Enhanced Doc Update Manager

- **File**: `scripts/enhanced_doc_update_manager.py`
- **Version**: 4.0.0
- **Features**: Multiple processing modes, enhanced error isolation, timestamp
  tracking

## Enhanced Workflows

### Enhanced Issue Management

- **File**: `.github/workflows/reusable-enhanced-issue-management.yml`
- **Use case**: Issue updates with timestamp lifecycle tracking
- **Key features**: Chronological processing, automatic migration, fallback
  support

### Enhanced Documentation Updates

- **File**: `.github/workflows/reusable-enhanced-docs-update.yml`
- **Use case**: Documentation updates with timestamp lifecycle tracking
- **Key features**: Multiple processing modes, error isolation, comprehensive
  logging

## Migration Steps

### 1. For New Projects

For new projects, use the enhanced workflows directly:

```yaml
# .github/workflows/issue-management.yml
name: Issue Management

on:
  push:
    paths: ['.github/issue-updates/**']
  schedule:
    - cron: '0 2 * * *'

permissions:
  contents: write
  issues: write
  pull-requests: write
  security-events: read
  repository-projects: write

jobs:
  process-issues:
    uses: jdfalk/ghcommon/.github/workflows/reusable-enhanced-issue-management.yml@main
    with:
      enable_chronological_processing: true
      enable_timestamp_migration: false # Not needed for new projects
```

### 2. For Existing Projects - Gradual Migration

#### Step 1: Add Enhanced Workflows Alongside Existing Ones

```yaml
# .github/workflows/enhanced-issue-management.yml
name: Enhanced Issue Management

on:
  workflow_dispatch:
    inputs:
      enable_timestamp_migration:
        description: 'Migrate legacy files to v2.0'
        default: true
        type: boolean

jobs:
  enhanced-processing:
    uses: jdfalk/ghcommon/.github/workflows/reusable-enhanced-issue-management.yml@main
    with:
      enable_chronological_processing: true
      enable_timestamp_migration:
        ${{ github.event.inputs.enable_timestamp_migration }}
      dry_run: true # Start with dry run
```

#### Step 2: Test Migration

Run the enhanced workflow with migration enabled:

1. Go to **Actions** → **Enhanced Issue Management** → **Run workflow**
2. Enable **"Migrate legacy files to v2.0"**
3. Keep **dry_run: true** for initial testing
4. Review the output to ensure migration works correctly

#### Step 3: Perform Actual Migration

After testing, run with actual migration:

1. Set **dry_run: false**
2. Run the workflow to migrate existing files
3. Verify that files in `.github/issue-updates/` now have enhanced timestamps

#### Step 4: Replace Original Workflows

Once migration is complete, replace the original workflows:

```yaml
# .github/workflows/issue-management.yml (updated)
name: Issue Management

on:
  push:
    paths: ['.github/issue-updates/**']
  schedule:
    - cron: '0 2 * * *'

jobs:
  process-issues:
    # Changed from original to enhanced
    uses: jdfalk/ghcommon/.github/workflows/reusable-enhanced-issue-management.yml@main
    with:
      enable_chronological_processing: true
      enable_timestamp_migration: false # Already migrated
```

### 3. For Projects with Custom Scripts

If your project has custom scripts that use the original format:

#### Update Scripts to Handle Enhanced Format

```python
# Example: Update your custom script
import json
from datetime import datetime, timezone

def load_update_file(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)

    # Handle both formats
    if isinstance(data, dict):
        # Check for enhanced format
        if 'created_at' in data:
            # Enhanced format v2.0
            return data
        else:
            # Legacy format - add timestamps
            data['created_at'] = datetime.now(timezone.utc).isoformat()
            data['enhanced_at'] = datetime.now(timezone.utc).isoformat()
            return data

    return data
```

#### Use Enhanced Scripts Directly

```bash
# Download enhanced scripts
curl -sSL https://raw.githubusercontent.com/jdfalk/ghcommon/main/scripts/enhanced_issue_manager.py \
  -o scripts/enhanced_issue_manager.py

# Use chronological processing
python scripts/enhanced_issue_manager.py process-chronological \
  --directory .github/issue-updates
```

## Enhanced Format Examples

### Enhanced Issue Update Format v2.0

```json
{
  "action": "create",
  "title": "Implement new feature",
  "body": "Feature description...",
  "labels": ["enhancement"],
  "assignees": ["developer"],
  "guid": "1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "created_at": "2025-01-18T22:49:02.123456Z",
  "timestamp_extracted_at": "2025-01-18T22:49:02.789012Z",
  "processing_metadata": {
    "enhanced_at": "2025-01-18T22:49:02.789012Z",
    "source_file": ".github/issue-updates/feature_request.json",
    "version": "2.0.0",
    "migrated_from": "legacy"
  }
}
```

### Enhanced Doc Update Format v2.0

```json
{
  "mode": "append",
  "filename": "README.md",
  "content": "## New Section\n\nContent here...",
  "guid": "2b3c4d5e-6f7a-8b9c-0d1e-2f3a4b5c6d7e",
  "created_at": "2025-01-18T22:49:02.123456Z",
  "timestamp_extracted_at": "2025-01-18T22:49:02.789012Z",
  "processing_metadata": {
    "enhanced_at": "2025-01-18T22:49:02.789012Z",
    "source_file": ".github/doc-updates/readme_update.json",
    "version": "2.0.0"
  }
}
```

## Compatibility Matrix

| Feature                  | Original | Enhanced    | Backwards Compatible |
| ------------------------ | -------- | ----------- | -------------------- |
| Basic processing         | ✅       | ✅          | ✅                   |
| File archival            | ✅       | ✅          | ✅                   |
| Error handling           | ✅       | ✅ Enhanced | ✅                   |
| Timestamp tracking       | ❌       | ✅          | ✅                   |
| Chronological processing | ❌       | ✅          | N/A                  |
| Git integration          | ❌       | ✅          | N/A                  |
| Dependency resolution    | ❌       | ✅          | N/A                  |
| Lifecycle tracking       | ❌       | ✅          | N/A                  |

## Benefits of Migration

### 1. Improved Reliability

- Chronological processing prevents conflicts
- Dependency resolution ensures proper order
- Enhanced error isolation and recovery

### 2. Better Tracking

- Comprehensive timestamp lifecycle tracking
- Git-integrated historical accuracy
- Detailed processing metadata

### 3. Enhanced Features

- Multiple doc update modes (append, prepend, replace-section, etc.)
- Automatic timestamp migration
- Fallback to original processors

### 4. Future-Proofing

- Designed for extensibility
- Backwards compatibility maintained
- Support for new processing patterns

## Troubleshooting

### Migration Issues

**Problem**: Migration fails with timestamp errors **Solution**: Use the
`recover-timestamps` command:

```bash
python scripts/enhanced_issue_manager.py recover-timestamps \
  --directory .github/issue-updates
```

**Problem**: Files stuck in failed directory **Solution**: Use the enhanced doc
manager to reprocess:

```bash
python scripts/enhanced_doc_update_manager.py process-failed \
  --directory .github/doc-updates
```

### Workflow Issues

**Problem**: Enhanced workflow fails, but original works **Solution**: Check the
workflow configuration and enable fallback:

- Ensure all required permissions are granted
- Verify the directory paths are correct
- Check that the GitHub token has appropriate scope

**Problem**: Chronological processing produces unexpected order **Solution**:
Validate timestamp format:

```bash
python scripts/enhanced_issue_manager.py validate-timestamps \
  --directory .github/issue-updates
```

## Support

For issues with the enhanced workflows:

1. **Check the logs**: Enhanced workflows provide detailed logging
2. **Try dry-run mode**: Use `dry_run: true` to test without changes
3. **Use fallback**: Enhanced workflows automatically fall back to original
   processors
4. **File issues**: Report problems in the
   [ghcommon repository](https://github.com/jdfalk/ghcommon/issues)

## Conclusion

The enhanced workflows provide significant improvements while maintaining full
backwards compatibility. Migration is safe and can be done gradually, with
automatic fallback ensuring reliability throughout the process.
