# AI Rebase Workflow Fixes - Complete Overhaul

## Summary

Completely overhauled the `reusable-ai-rebase.yml` workflow to fix the "An
unexpected error occurred" issue and add comprehensive error handling and
fallback mechanisms.

## Root Issues Fixed

### 1. "An unexpected error occurred"

**Root cause**: GitHub AI inference service reliability issues **Solutions**:

- Added `continue-on-error: true` to prevent workflow failure
- Implemented Claude API fallback
- Enhanced error messaging with troubleshooting steps

### 2. Token Permission Issues

**Root cause**: Missing 'models' scope on GitHub token **Solution**: Clear error
messages explaining required permissions

### 3. Prompt Size Exceeding Limits

**Root cause**: Including full file contents (200+ lines per file) for multiple
conflicted files **Solutions**:

- Limited to maximum 5 files in prompt
- Show only conflict markers instead of full files
- Reduced max-tokens from 4000 to 2000

### 4. Model Reliability

**Root cause**: Using `openai/gpt-4o` which has availability issues
**Solution**: Changed default to `gpt-4o-mini` for better reliability

## Major Changes Made

### 1. Enhanced Error Handling

```yaml
# Before: Would fail on AI error
uses: actions/ai-inference@v1.1.0

# After: Continues on error with fallbacks
uses: actions/ai-inference@v1.1.0
continue-on-error: true
```

### 2. Claude API Fallback

Added automatic fallback to Claude when GitHub AI fails:

```yaml
- name: Fallback to Claude API (if available)
  if: steps.ai.outcome == 'failure' && env.CLAUDE_API_KEY != ''
  # Uses Claude API for conflict resolution
```

### 3. Intelligent Conflict Resolution Strategy

- **Documentation files** (`.md`, `README`, `CHANGELOG`): Merge both sides
- **Code files**: Prefer incoming changes
- **Protobuf files**: Use smart merging based on file type

### 4. Reduced Prompt Engineering

```bash
# Before: Full file contents (200+ lines each)
head -200 "$file" >> prompt.txt

# After: Only conflict markers
grep -n -A 2 -B 2 "^<<<<<<< |^======= |^>>>>>>> " "$file" | head -20
```

### 5. Better User Communication

Enhanced PR comments with:

- Specific error causes
- Step-by-step resolution instructions
- Which AI service was used
- Troubleshooting guidance

## New Secrets Support

### Required

- `github-token`: Needs `contents: write`, `pull-requests: write`,
  `models: read`

### Optional

- `claude-api-key`: For Claude API fallback when GitHub AI fails

## Usage Examples

### Basic (GitHub AI only)

```yaml
uses: jdfalk/ghcommon/.github/workflows/reusable-ai-rebase.yml@main
with:
  base-branch: main
  model: gpt-4o-mini
secrets:
  github-token: ${{ secrets.GITHUB_TOKEN }}
```

### With Claude Fallback

```yaml
uses: jdfalk/ghcommon/.github/workflows/reusable-ai-rebase.yml@main
with:
  base-branch: main
  model: gpt-4o-mini
secrets:
  github-token: ${{ secrets.GITHUB_TOKEN }}
  claude-api-key: ${{ secrets.CLAUDE_API_KEY }}
```

## Error Flow Improvements

1. **GitHub AI fails** → Clear error message + try Claude
2. **Claude fails** → Intelligent manual resolution by file type
3. **All AI fails** → Detailed manual instructions in PR comment
4. **Success** → Automatic force-push and optional auto-merge

## Testing the Fix

The next time the workflow runs, you should see:

1. More detailed logging about prompt sizes and models
2. Better error messages if AI services fail
3. Automatic fallback attempts
4. Clear manual resolution instructions when needed

This should resolve the "An unexpected error occurred" issue that was plaguing
the AI inference step.

- Uses proper system prompt with coding standards
- Requests specific patch format for reliable application
- Includes repository and branch context

### Better Error Handling

- Validates patches before applying
- Provides fallback conflict resolution
- Leaves helpful comments for manual resolution
- Prevents auto-merge when conflicts aren't properly resolved

### Improved User Experience

- Clear status comments on PRs
- Detailed instructions for manual resolution
- Proper success/failure feedback
- Scheduled daily runs at 6 AM UTC

## Usage

Each repository now has a workflow that:

1. Runs daily at 6 AM UTC to check for conflicted PRs
2. Can be triggered manually via workflow_dispatch
3. Uses AI to resolve conflicts intelligently
4. Falls back to manual resolution instructions when needed
5. Provides clear feedback on PR status

## Testing

The workflow can be tested by:

1. Creating a PR with merge conflicts
2. Running the workflow manually: `Actions > Fix Merge Conflicts > Run workflow`
3. Checking the PR for status comments and resolution attempts
