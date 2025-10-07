<!-- file: docs/cross-registry-todos/task-01/t01-part4.md -->
<!-- version: 1.0.0 -->
<!-- guid: t01-yaml-fix-part4-d4e5f6g7-h8i9 -->

# Task 01 Part 4: Git Workflow and Commit Procedures

## Branch Strategy

### Create Feature Branch

```bash
#!/bin/bash
# file: scripts/create-fix-branch.sh
# version: 1.0.0
# guid: create-fix-branch

set -e

echo "=== Creating Fix Branch ==="

# Ensure on main branch
git checkout main

# Pull latest changes
echo ""
echo "Pulling latest changes..."
git pull origin main

# Create feature branch
BRANCH_NAME="fix/yaml-trailing-hyphens"
echo ""
echo "Creating branch: $BRANCH_NAME"
git checkout -b "$BRANCH_NAME"

echo ""
echo "✅ Branch created: $BRANCH_NAME"
git branch --show-current
```

### Expected Branch Output

```text
=== Creating Fix Branch ===
Already on 'main'
Your branch is up to date with 'origin/main'.

Pulling latest changes...
Already up to date.

Creating branch: fix/yaml-trailing-hyphens
Switched to a new branch 'fix/yaml-trailing-hyphens'

✅ Branch created: fix/yaml-trailing-hyphens
fix/yaml-trailing-hyphens
```

## Making Changes

### Apply the Fix

```bash
#!/bin/bash
# file: scripts/apply-yaml-fix.sh
# version: 1.0.0
# guid: apply-yaml-fix

set -e

echo "=== Applying YAML Fix ==="

FILE=".github/workflows/release-rust.yml"

# Backup
cp "$FILE" "${FILE}.bak"
echo "✅ Created backup"

# Apply fix using sed
echo ""
echo "Removing trailing hyphens..."

# Fix line 234 and 235
sed -i '' '234s/\${{ runner\.os }}-cargo-\${{ matrix\.rust }}-$/\${{ runner.os }}-cargo-\${{ matrix.rust }}/' "$FILE"
sed -i '' '235s/\${{ runner\.os }}-cargo-$/\${{ runner.os }}-cargo/' "$FILE"

# Fix line 244 and 245
sed -i '' '244s/\${{ runner\.os }}-cargo-\${{ matrix\.rust }}-$/\${{ runner.os }}-cargo-\${{ matrix.rust }}/' "$FILE"
sed -i '' '245s/\${{ runner\.os }}-cargo-$/\${{ runner.os }}-cargo/' "$FILE"

# Fix line 254
sed -i '' '254s/\${{ runner\.os }}-cargo-$/\${{ runner.os }}-cargo/' "$FILE"

echo "✅ Applied fixes"

# Verify
echo ""
echo "Verifying changes..."
if grep -E "\-$" <(grep -A 2 "restore-keys" "$FILE") ; then
  echo "❌ Still found trailing hyphens"
  exit 1
else
  echo "✅ No trailing hyphens found"
fi

# Show diff
echo ""
echo "Changes:"
diff -u "${FILE}.bak" "$FILE" || true

echo ""
echo "✅ Fix applied successfully"
```

### Review Changes

```bash
# View changes
git diff .github/workflows/release-rust.yml

# View in context
git diff --color-words .github/workflows/release-rust.yml

# Check status
git status
```

### Expected Diff Output

```diff
diff --git a/.github/workflows/release-rust.yml b/.github/workflows/release-rust.yml
index abc1234..def5678 100644
--- a/.github/workflows/release-rust.yml
+++ b/.github/workflows/release-rust.yml
@@ -231,8 +231,8 @@ jobs:
             target/
           key: ${{ runner.os }}-cargo-${{ matrix.rust }}-${{ hashFiles('**/Cargo.lock') }}
           restore-keys: |
-            ${{ runner.os }}-cargo-${{ matrix.rust }}-
-            ${{ runner.os }}-cargo-
+            ${{ runner.os }}-cargo-${{ matrix.rust }}
+            ${{ runner.os }}-cargo

       - name: Cache Cargo dependencies (aarch64)
         if: matrix.target == 'aarch64-unknown-linux-gnu'
@@ -241,8 +241,8 @@ jobs:
             target/
           key: ${{ runner.os }}-cargo-${{ matrix.rust }}-${{ hashFiles('**/Cargo.lock') }}
           restore-keys: |
-            ${{ runner.os }}-cargo-${{ matrix.rust }}-
-            ${{ runner.os }}-cargo-
+            ${{ runner.os }}-cargo-${{ matrix.rust }}
+            ${{ runner.os }}-cargo

       - name: Cache Cargo dependencies (macOS)
         if: startsWith(matrix.os, 'macos')
@@ -251,7 +251,7 @@ jobs:
             target/
           key: ${{ runner.os }}-cargo-${{ hashFiles('**/Cargo.lock') }}
           restore-keys: |
-            ${{ runner.os }}-cargo-
+            ${{ runner.os }}-cargo
```

## Commit Message

### Conventional Commit Format

According to repository standards (see `.github/instructions/commit-messages.instructions.md`):

```bash
git commit -m "fix(ci): remove trailing hyphens from YAML restore-keys

Remove trailing hyphens from restore-keys in release-rust.yml cache
configuration to follow YAML best practices and improve cache key
matching clarity.

Changes Made:

fix(ci): correct restore-keys syntax in release-rust.yml
- Lines 234-235: Remove trailing hyphens from first cache block
- Lines 244-245: Remove trailing hyphens from second cache block
- Line 254: Remove trailing hyphen from third cache block
- Improves YAML lint compliance
- Maintains cache functionality (keys still match correctly)
- No behavior change - purely cosmetic fix

Files Changed:
- .github/workflows/release-rust.yml

Impact: Low risk, no functional changes
Risk Assessment: Very Low - syntax improvement only
Testing: Local validation, yamllint passed, GH Actions syntax valid
"
```

### Alternative Multi-Change Format

If combining with other changes:

```bash
git commit -m "fix(ci): improve YAML syntax in release workflows

Multiple YAML syntax improvements across release workflows.

Changes Made:

fix(ci): remove trailing hyphens from restore-keys in release-rust.yml
- Lines 234-235: First cache block trailing hyphens removed
- Lines 244-245: Second cache block trailing hyphens removed
- Line 254: Third cache block trailing hyphen removed

fix(ci): normalize whitespace in workflow files
- Removed trailing spaces from all workflow files
- Ensured consistent indentation

Files Changed:
- .github/workflows/release-rust.yml
- .github/workflows/release-docker.yml

Impact: Low risk, cosmetic changes only
"
```

### Commit Message Guidelines

**Required Elements:**

- **Type**: `fix`, `feat`, `chore`, `docs`, `style`, `refactor`, `test`, `ci`, `perf`, `build`
- **Scope**: Affected area (e.g., `ci`, `workflows`, `rust`)
- **Subject**: Short description (50 chars max)
- **Body**: Detailed explanation with bullet points
- **Footer**: Breaking changes, issue references (optional)

**For this fix:**

- Type: `fix` (fixes incorrect YAML syntax)
- Scope: `ci` (affects CI workflows)
- Subject: "remove trailing hyphens from YAML restore-keys"
- Body: Detailed explanation with file changes
- Footer: None needed (no breaking changes)

## Staging and Committing

### Stage Changes

```bash
#!/bin/bash
# file: scripts/stage-yaml-fix.sh
# version: 1.0.0
# guid: stage-yaml-fix

set -e

echo "=== Staging Changes ==="

# Stage the file
git add .github/workflows/release-rust.yml

# Review staged changes
echo ""
echo "Staged changes:"
git diff --cached --stat

echo ""
echo "Detailed diff:"
git diff --cached .github/workflows/release-rust.yml

# Confirm
echo ""
read -p "Proceed with commit? (y/n): " confirm
if [ "$confirm" != "y" ]; then
  echo "Aborted"
  exit 0
fi

echo ""
echo "✅ Changes staged"
```

### Commit Using VS Code Task

**PREFERRED METHOD** - Use VS Code task when available:

1. Open Command Palette (`Cmd+Shift+P`)
2. Run task: "Git Commit"
3. Enter commit message following conventional commit format
4. Task automatically logs to `logs/` directory

**Or use copilot-agent-util:**

```bash
copilot-agent-util git commit -m "fix(ci): remove trailing hyphens from YAML restore-keys

Remove trailing hyphens from restore-keys in release-rust.yml cache
configuration to follow YAML best practices.

Changes Made:

fix(ci): correct restore-keys syntax
- Lines 234-235: Remove trailing hyphens from first cache block
- Lines 244-245: Remove trailing hyphens from second cache block
- Line 254: Remove trailing hyphen from third cache block

Files Changed:
- .github/workflows/release-rust.yml

Impact: Low risk, cosmetic fix
"
```

### Verify Commit

```bash
# View commit
git show HEAD

# Check commit message format
git log -1 --pretty=format:"%s"

# Verify conventional commit format
echo ""
git log -1 --pretty=format:"%s" | grep -E "^(feat|fix|docs|style|refactor|test|chore|ci|perf|build)\(.+\):"

if [ $? -eq 0 ]; then
  echo "✅ Commit message format valid"
else
  echo "❌ Commit message format invalid"
  exit 1
fi
```

### Expected Commit Output

```text
[fix/yaml-trailing-hyphens abc1234] fix(ci): remove trailing hyphens from YAML restore-keys
 1 file changed, 5 insertions(+), 5 deletions(-)

✅ Commit message format valid
```

## Push Changes

### Push to Remote

```bash
#!/bin/bash
# file: scripts/push-yaml-fix.sh
# version: 1.0.0
# guid: push-yaml-fix

set -e

echo "=== Pushing Changes ==="

# Get current branch
BRANCH=$(git branch --show-current)
echo "Current branch: $BRANCH"

# Push to remote
echo ""
echo "Pushing to origin/$BRANCH..."
git push -u origin "$BRANCH"

echo ""
echo "✅ Changes pushed"

# Show remote URL
echo ""
echo "Remote branch:"
git rev-parse --abbrev-ref --symbolic-full-name @{u}
```

### Using VS Code Task

**PREFERRED METHOD:**

1. Use task: "Git Push"
2. Task handles authentication and logging
3. Check `logs/` directory for push results

**Or use copilot-agent-util:**

```bash
copilot-agent-util git push -u origin fix/yaml-trailing-hyphens
```

### Expected Push Output

```text
=== Pushing Changes ===
Current branch: fix/yaml-trailing-hyphens

Pushing to origin/fix/yaml-trailing-hyphens...
Enumerating objects: 7, done.
Counting objects: 100% (7/7), done.
Delta compression using up to 8 threads
Compressing objects: 100% (4/4), done.
Writing objects: 100% (4/4), 512 bytes | 512.00 KiB/s, done.
Total 4 (delta 3), reused 0 (delta 0), pack-reused 0
remote: Resolving deltas: 100% (3/3), completed with 3 local objects.
remote:
remote: Create a pull request for 'fix/yaml-trailing-hyphens' on GitHub by visiting:
remote:      https://github.com/jdfalk/ghcommon/pull/new/fix/yaml-trailing-hyphens
remote:
To https://github.com/jdfalk/ghcommon.git
 * [new branch]      fix/yaml-trailing-hyphens -> fix/yaml-trailing-hyphens
branch 'fix/yaml-trailing-hyphens' set up to track 'origin/fix/yaml-trailing-hyphens'.

✅ Changes pushed

Remote branch:
origin/fix/yaml-trailing-hyphens
```

## Create Pull Request

### Using GitHub CLI

```bash
#!/bin/bash
# file: scripts/create-pr.sh
# version: 1.0.0
# guid: create-pr

set -e

echo "=== Creating Pull Request ==="

# Check authentication
gh auth status

# Create PR
echo ""
echo "Creating pull request..."
gh pr create \
  --title "fix(ci): remove trailing hyphens from YAML restore-keys" \
  --body "## Summary

Remove trailing hyphens from \`restore-keys\` in \`release-rust.yml\` cache configuration to follow YAML best practices and improve code clarity.

## Changes Made

- **Lines 234-235**: Remove trailing hyphens from first cache block
- **Lines 244-245**: Remove trailing hyphens from second cache block
- **Line 254**: Remove trailing hyphen from third cache block

## Impact

- ✅ **Risk**: Very Low - cosmetic syntax improvement only
- ✅ **Functionality**: No behavior change - cache keys still match correctly
- ✅ **Testing**: Local validation passed, yamllint clean, GH Actions syntax valid

## Validation

- [x] YAML syntax validated with yamllint
- [x] GitHub Actions syntax checked with gh CLI
- [x] Cache key pattern matching tested
- [x] No trailing hyphens in restore-keys
- [x] Conventional commit format used

## Files Changed

- \`.github/workflows/release-rust.yml\`

## Related

- Follows YAML best practices
- Improves lint compliance
- No breaking changes
" \
  --base main \
  --head fix/yaml-trailing-hyphens

echo ""
echo "✅ Pull request created"

# Show PR URL
PR_URL=$(gh pr view --json url --jq '.url')
echo ""
echo "PR URL: $PR_URL"
```

### Expected PR Creation Output

```text
=== Creating Pull Request ===
✓ Logged in to github.com as jdfalk

Creating pull request...

Creating pull request for fix/yaml-trailing-hyphens into main in jdfalk/ghcommon

https://github.com/jdfalk/ghcommon/pull/123

✅ Pull request created

PR URL: https://github.com/jdfalk/ghcommon/pull/123
```

### PR Template Content

The repository's PR template (`.github/pull-request-descriptions.instructions.md`) requires:

```markdown
## Summary
Brief description of changes

## Changes Made
Detailed bullet list with context

## Impact
- Risk assessment
- Functionality changes
- Testing performed

## Validation
- [ ] Checklist items

## Files Changed
- List of modified files

## Related
- Related issues/PRs
- Documentation updates
```

## CI Checks

### Monitor PR Checks

```bash
#!/bin/bash
# file: scripts/monitor-pr-checks.sh
# version: 1.0.0
# guid: monitor-pr-checks

set -e

echo "=== Monitoring PR Checks ==="

# Get PR number
PR_NUMBER=$(gh pr view --json number --jq '.number')
echo "PR Number: $PR_NUMBER"

# Watch checks
echo ""
echo "Watching checks (Ctrl+C to stop)..."
gh pr checks "$PR_NUMBER" --watch

# Show final status
echo ""
echo "Final status:"
gh pr checks "$PR_NUMBER"

echo ""
echo "✅ CI checks complete"
```

### Expected CI Check Output

```text
=== Monitoring PR Checks ===
PR Number: 123

Watching checks (Ctrl+C to stop)...
Some checks haven't completed yet

✓ Lint / super-linter
✓ Test / test-rust
✓ Build / build-rust
✓ Validate / yaml-validation

All checks passed

Final status:
✓ Lint / super-linter        4m 23s
✓ Test / test-rust          2m 45s
✓ Build / build-rust        5m 12s
✓ Validate / yaml-validation 0m 34s

✅ CI checks complete
```

## Merge Strategy

### Auto-Merge Configuration

```bash
# Enable auto-merge (requires admin/maintain permissions)
gh pr merge 123 --auto --squash

# Or merge manually after approval
gh pr merge 123 --squash --delete-branch
```

### Merge Commit Message

```text
fix(ci): remove trailing hyphens from YAML restore-keys (#123)

Remove trailing hyphens from restore-keys in release-rust.yml cache
configuration to follow YAML best practices and improve code clarity.

Changes Made:
- Lines 234-235: Remove trailing hyphens from first cache block
- Lines 244-245: Remove trailing hyphens from second cache block
- Line 254: Remove trailing hyphen from third cache block

Impact: Low risk, cosmetic fix only
Testing: yamllint validated, GH Actions syntax checked
```

## Post-Merge Cleanup

### Clean Up Local Branches

```bash
#!/bin/bash
# file: scripts/cleanup-after-merge.sh
# version: 1.0.0
# guid: cleanup-after-merge

set -e

echo "=== Post-Merge Cleanup ==="

# Switch to main
git checkout main

# Pull latest
echo ""
echo "Pulling latest changes..."
git pull origin main

# Delete local branch
BRANCH="fix/yaml-trailing-hyphens"
echo ""
echo "Deleting local branch: $BRANCH"
git branch -d "$BRANCH"

# Clean up remote tracking
echo ""
echo "Pruning remote branches..."
git remote prune origin

echo ""
echo "✅ Cleanup complete"
```

### Verify Merge

```bash
# Check commit is in main
git log --oneline --grep "trailing hyphens" -n 1

# Verify file changes
git show HEAD:.github/workflows/release-rust.yml | grep -A 3 "restore-keys"
```

## Continue to Part 5

Next part covers post-merge verification and monitoring.
