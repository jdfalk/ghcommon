# Unified Automation Migration Guide

## Quick Start

### For New Repositories

1. **Copy the complete workflow template**:

   ```bash
   curl -fsSL https://raw.githubusercontent.com/jdfalk/ghcommon/main/examples/workflows/unified-automation-complete.yml \
     -o .github/workflows/unified-automation.yml
   ```

2. **Optional: Add custom configuration**:

   ```bash
   curl -fsSL https://raw.githubusercontent.com/jdfalk/ghcommon/main/.github/unified-automation-config.json \
     -o .github/unified-automation-config.json
   # Edit as needed
   ```

3. **Set repository permissions**:
   - Go to Settings → Actions → General
   - Enable "Read and write permissions"
   - Enable "Allow GitHub Actions to create and approve pull requests"

### For Existing Repositories

Use the automated migration script:

```bash
# Single repository
python scripts/update-repository-automation.py --repo owner/repo-name

# Multiple repositories
echo "owner/repo1" > repos.txt
echo "owner/repo2" >> repos.txt
python scripts/update-repository-automation.py --config repos.txt

# Dry run to see what would change
python scripts/update-repository-automation.py --repo owner/repo-name --dry-run
```

## Enhanced Features

### ✅ Duplicate Prevention & Closure Restored

- **Configurable duplicate prevention** during issue creation
- **Automatic duplicate closure** by title matching
- **Multiple detection methods**: GUID-only, title-only, or both
- **Performance limits** to prevent API exhaustion

### ✅ Standardized Configuration

- **Default JSON configuration** with all automation options
- **Automatic configuration loading** from ghcommon if not present
- **Repository-specific customization** supported
- **Comprehensive documentation** of all available options

### ✅ Workflow Consolidation

- **Single primary workflow**: `reusable-unified-automation.yml`
- **Enhanced workflow available**: For repositories needing timestamp tracking
- **Backward compatibility** maintained
- **Clear migration path** provided

## Configuration Options

### Duplicate Prevention

```json
{
  "issue_management": {
    "enable_duplicate_prevention": true,
    "enable_duplicate_closure": true,
    "duplicate_prevention_method": "guid_and_title",
    "max_duplicate_check_issues": 1000
  }
}
```

- **`enable_duplicate_prevention`**: Prevent creating duplicate issues
- **`enable_duplicate_closure`**: Automatically close duplicate issues
- **`duplicate_prevention_method`**:
  - `"guid_and_title"`: Check both GUID and title (recommended)
  - `"guid_only"`: Only check GUID markers
  - `"title_only"`: Only check issue titles
- **`max_duplicate_check_issues`**: Limit issues checked for performance

### Complete Configuration

See
[`.github/unified-automation-config.json`](.github/unified-automation-config.json)
for all available options covering:

- Issue Management
- Documentation Updates
- Labeling
- Super Linter
- Intelligent Labeling
- Workflow Settings
- Notifications

## Environment Variables

The system respects these environment variables (set automatically from
configuration):

```bash
ENABLE_DUPLICATE_PREVENTION=true
ENABLE_DUPLICATE_CLOSURE=true
DUPLICATE_PREVENTION_METHOD=guid_and_title
MAX_DUPLICATE_CHECK_ISSUES=1000
```

## Migration Benefits

1. **🔄 Restored Functionality**: Duplicate prevention and closure now work
2. **⚙️ Standardized Config**: All repos use the same automation features
3. **🚀 Better Performance**: Rate limiting prevents API exhaustion
4. **📊 Clear Visibility**: Configuration makes automation behavior transparent
5. **🛠 Easy Maintenance**: Centralized configuration reduces overhead

## Troubleshooting

### Common Issues

**❌ Workflow fails with "Invalid input" errors**

- Ensure you're using the latest workflow templates
- Check that all input parameters are defined in your calling workflow

**❌ Duplicate prevention not working**

- Verify `enable_duplicate_prevention: true` in configuration
- Check that environment variables are being set correctly
- Review workflow logs for duplicate detection messages

**❌ API rate limiting**

- Reduce `max_duplicate_check_issues` in configuration
- Consider running automation less frequently
- Use GitHub Apps tokens for higher rate limits

### Getting Help

1. Check the [Enhancement Summary](UNIFIED_AUTOMATION_ENHANCEMENT_SUMMARY.md)
2. Review workflow logs in GitHub Actions
3. Test with dry-run mode: `dry_run: true`
4. Open an issue in the ghcommon repository

## Next Steps

1. **Test the migration** on a few repositories first
2. **Customize configuration** based on your needs
3. **Monitor performance** and adjust limits as needed
4. **Update documentation** in your repositories
5. **Train team members** on the new configuration system

---

_For detailed technical information, see
[UNIFIED_AUTOMATION_ENHANCEMENT_SUMMARY.md](UNIFIED_AUTOMATION_ENHANCEMENT_SUMMARY.md)_
