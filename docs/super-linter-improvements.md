<!--
file: docs/super-linter-improvements.md
version: 1.0.0
guid: 456e7890-f1a2-3b4c-5d6e-789012345678
-->

# Super Linter Improvements Summary

## 🎯 Issues Addressed

Based on feedback about the GitHub Action run at
<https://github.com/jdfalk/subtitle-manager/actions/runs/16693240374>, the following improvements
have been made to the reusable Super Linter workflow:

### 1. **Verbose Output Problem**

- **Issue**: Summary showed all processed files instead of just issues/changes
- **Solution**: Added `show-detailed-summary` parameter (default: false) to control verbosity
- **Result**: By default, only issues and changes are shown

### 2. **Poor Formatting**

- **Issue**: Unreadable, cluttered output in summaries and comments
- **Solution**:
  - Restructured PR comments to be concise and actionable
  - Added GitHub Job Summary with clean formatting
  - Improved error extraction and presentation
- **Result**: Clean, scannable output focused on what needs action

### 3. **Unhelpful Final Summary**

- **Issue**: Long configuration dump that wasn't useful for decision making
- **Solution**:
  - Minimized configuration details (hidden in collapsible section)
  - Focused on actionable next steps
  - Added specific issue details with file context
- **Result**: Summary tells you exactly what to fix

## 🔧 New Features

### Concise Mode (Default)

```yaml
uses: jdfalk/ghcommon/.github/workflows/reusable-super-linter.yml@main
with:
  show-detailed-summary: false # Clean, issue-focused output
```

**Output includes:**

- ✅/❌ Status at a glance
- 🔧 Auto-fixes applied (if any)
- 📋 Specific issues with file references
- 🔧 Clear next steps

### Detailed Mode (Debugging)

```yaml
uses: jdfalk/ghcommon/.github/workflows/reusable-super-linter.yml@main
with:
  show-detailed-summary: true # Verbose processing information
```

**Output includes:**

- All file processing details
- Verbose logging (LOG_LEVEL: VERBOSE)
- Complete configuration information
- Full error traces

## 📊 Improved Outputs

### 1. GitHub Job Summary

- Focused summary in workflow run page
- Issue categorization by linter type
- Auto-fix status clearly indicated
- Minimal configuration details

### 2. PR Comments

- Concise status header
- Actionable issue list with file context
- Collapsible configuration details
- Eliminated redundant information

### 3. Artifacts

- Cleaned up summary files
- Focus on errors and changes, not processing logs
- Structured issue reporting

## 🔄 Migration Guide

### For Existing Workflows

No changes required! The new default behavior provides cleaner output.

### To Enable Detailed Mode (for debugging)

Add `show-detailed-summary: true` to your workflow call:

```yaml
lint:
  uses: jdfalk/ghcommon/.github/workflows/reusable-super-linter.yml@main
  with:
    show-detailed-summary: true # Only for debugging
    validate-all-codebase: false
    enable-auto-fix: true
```

## 🎯 Results

### Before

- 📄 Long lists of all processed files
- 🔍 Configuration dump in every summary
- ❓ Unclear what action is needed
- 📊 200+ line PR comments

### After

- ✅ Shows only issues and changes
- 🎯 Focused on actionable items
- 📝 Clear next steps
- 📄 ~20 line PR comments with relevant details

## 📁 Example Workflows

See `examples/workflows/super-linter-improved-example.yml` for complete examples of both modes.

## 🚀 Version History

- **v2.4.0**: Added concise output mode, improved summaries, better error presentation
- **v2.3.0**: Previous version with verbose output
