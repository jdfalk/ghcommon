# file: AI_REBASE_WORKFLOW_FIXES.md

# version: 1.0.0

# guid: 9c8d7e6f-5a4b-3c2d-1e0f-9a8b7c6d5e4f

# AI Rebase Workflow Fixes

## Issues Fixed

### 1. **Reusable AI Rebase Workflow (`ghcommon/.github/workflows/reusable-ai-rebase.yml`)**

**Problems:**

- AI prompt was too basic and didn't include conflict information
- Max tokens was only 200 (insufficient for resolving conflicts)
- System prompt was generic "You are a helpful assistant"
- Environment variable substitution wasn't working in the prompt
- Used `response-file` output that doesn't exist
- No proper error handling for failed AI resolution
- Auto-merge was too aggressive

**Solutions:**

- ✅ Added conflict information collection step
- ✅ Increased max-tokens to 4000
- ✅ Added comprehensive system prompt with coding standards
- ✅ Fixed environment variable usage in prompt
- ✅ Used `response` output instead of `response-file`
- ✅ Added fallback conflict resolution strategy
- ✅ Added proper error handling and user feedback
- ✅ Made auto-merge conditional on successful resolution
- ✅ Added detailed comments for manual resolution when AI fails

### 2. **Missing Workflows**

**Problem:** Only subtitle-manager had the fix-merge-conflicts workflow

**Solution:** Created fix-merge-conflicts.yml for all four repos:

- ✅ `/subtitle-manager/.github/workflows/fix-merge-conflicts.yml` (updated)
- ✅ `/gcommon/.github/workflows/fix-merge-conflicts.yml` (created)
- ✅ `/ghcommon/.github/workflows/fix-merge-conflicts.yml` (created)
- ✅ `/codex-cli/.github/workflows/fix-merge-conflicts.yml` (created)

## Key Improvements

### Enhanced AI Prompt

- Provides full conflict context including file contents
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
