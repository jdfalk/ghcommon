<!-- file: docs/refactors/workflows/v2/operations/troubleshooting.md -->
<!-- version: 1.0.0 -->
<!-- guid: c4d5e6f7-a8b9-0c1d-2e3f-4a5b6c7d8e9f -->

# Troubleshooting Guide: v2 Workflow System

## Overview

This guide provides solutions to common issues encountered with the v2 branch-aware workflow system.

**Quick Debug Commands**:

```bash
# Check workflow status
gh run list --limit 10

# View specific workflow run
gh run view <run-id> --log

# Re-run failed workflow
gh run rerun <run-id>

# View workflow logs
gh run view <run-id> --log-failed
```

## Diagnostic Checklist

When encountering issues, run through this checklist:

- [ ] **Check workflow status**: `gh run list --workflow=ci.yml`
- [ ] **Verify branch name**: `git branch --show-current`
- [ ] **Check feature flags**: `cat .github/workflow-feature-flags.yml`
- [ ] **Verify version policy**: `cat .github/workflow-versions.yml`
- [ ] **Check helper scripts**: `ls -la .github/workflows/scripts/`
- [ ] **Test locally**: Run helper scripts with `--debug` flag
- [ ] **Check GitHub Actions logs**: Look for error patterns
- [ ] **Verify secrets**: Ensure required secrets are set

## Common Issues by Category

### Feature Flag Issues

#### Feature flag not being detected

**Symptoms**:

- Workflow runs but uses v1 behavior
- Feature flag check step shows "disabled"
- Expected v2 features not activating

**Diagnosis**:

```bash
# Verify file exists and is valid YAML
ls -la .github/workflow-feature-flags.yml
python -c "import yaml; print(yaml.safe_load(open('.github/workflow-feature-flags.yml')))"

# Check branch name matches enabled_branches
git branch --show-current
grep -A 5 "enabled_branches:" .github/workflow-feature-flags.yml
```

**Solutions**:

1. **File doesn't exist**:

```bash
# Create feature flags file
cat > .github/workflow-feature-flags.yml << 'EOF'
feature_flags:
  use_v2_workflows:
    enabled: true
    enabled_branches:
      - main
      - 'stable-*'
EOF

git add .github/workflow-feature-flags.yml
git commit -m "feat(ci): add workflow feature flags"
git push
```

1. **Branch not in enabled list**:

```bash
# Add branch to enabled_branches
vim .github/workflow-feature-flags.yml
# Add your branch to the list
git commit -am "feat(ci): enable v2 for <branch>"
git push
```

1. **YAML syntax error**:

```bash
# Validate YAML
python -c "import yaml; yaml.safe_load(open('.github/workflow-feature-flags.yml'))"

# Fix syntax errors and commit
git commit -am "fix(ci): correct YAML syntax in feature flags"
git push
```

#### Feature flag check fails with Python error

**Symptoms**:

- Error: "ModuleNotFoundError: No module named 'yaml'"
- Feature flag check step fails immediately

**Solutions**:

```yaml
# Add Python setup to workflow
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.14'

- name: Install dependencies
  run: |
    pip install PyYAML>=6.0

- name: Check feature flag
  run: |
    python .github/workflows/scripts/workflow_common.py check-feature \
      --flag use_v2_workflows
```

### Matrix Generation Issues

#### Matrix generation produces empty matrix

**Symptoms**:

- Job skipped due to empty matrix
- No test configurations generated
- Error: "matrix must define at least one vector"

**Diagnosis**:

```bash
# Test matrix generation locally
python .github/workflows/scripts/ci_workflow.py generate-matrix \
  --branch $(git branch --show-current) \
  --languages go python \
  --debug

# Check version policy exists for branch
grep -A 20 "$(git branch --show-current):" .github/workflow-versions.yml
```

**Solutions**:

1. **Branch not in version policy**:

```yaml
# Add branch to workflow-versions.yml
version_policies:
  your-branch-name:
    created: '2025-10-14'
    description: 'Your branch description'
    go:
      versions: ['1.25']
      default: '1.25'
```

1. **Language not configured**:

```bash
# Check available languages in version policy
python .github/workflows/scripts/ci_workflow.py generate-matrix \
  --branch main \
  --languages go python rust node \
  --debug

# Add missing language to version policy
```

1. **Script error**:

```bash
# Enable debug logging
export DEBUG=1
python .github/workflows/scripts/ci_workflow.py generate-matrix \
  --branch main \
  --languages go \
  --debug 2>&1 | tee matrix-debug.log

# Check for Python tracebacks
grep -A 10 "Traceback" matrix-debug.log
```

#### Matrix includes wrong versions

**Symptoms**:

- Old language versions in matrix
- Versions don't match branch policy
- Wrong default version selected

**Diagnosis**:

```bash
# Verify version policy for current branch
BRANCH=$(git branch --show-current)
grep -A 20 "^  $BRANCH:" .github/workflow-versions.yml

# Check what matrix is generated
python .github/workflows/scripts/ci_workflow.py generate-matrix \
  --branch "$BRANCH" \
  --languages go
```

**Solutions**:

1. **Update version policy**:

```yaml
# Edit .github/workflow-versions.yml
version_policies:
  main:
    go:
      versions: ['1.25'] # Update to correct version
      default: '1.25'
```

1. **Clear cache and regenerate**:

```bash
# In workflow, add cache-busting
- name: Generate matrix
  run: |
    rm -f /tmp/matrix-cache-*
    python .github/workflows/scripts/ci_workflow.py generate-matrix \
      --branch ${{ github.ref_name }} \
      --languages go
```

### Change Detection Issues

#### Change detection not finding changed files

**Symptoms**:

- Jobs skip even when files changed
- `has_code_changes: false` when it should be true
- All change outputs are empty arrays

**Diagnosis**:

```bash
# Check git fetch depth
git log --oneline | wc -l  # Should be > 1

# Test change detection locally
python .github/workflows/scripts/ci_workflow.py detect-changes \
  --base origin/main \
  --head HEAD \
  --verbose

# Check git diff directly
git diff --name-only origin/main...HEAD
```

**Solutions**:

1. **Shallow clone issue**:

```yaml
# Ensure proper fetch depth
- name: Checkout with history
  uses: actions/checkout@v4
  with:
    fetch-depth: 0 # Must be 0 for full history
```

1. **Wrong base/head references**:

```yaml
# For pull requests
- name: Detect changes
  run: |
    python .github/workflows/scripts/ci_workflow.py detect-changes \
      --base origin/${{ github.base_ref }} \
      --head HEAD

# For pushes
- name: Detect changes
  run: |
    python .github/workflows/scripts/ci_workflow.py detect-changes \
      --base ${{ github.event.before }} \
      --head ${{ github.sha }}
```

1. **File patterns not matching**:

```python
# Check change patterns in ci_workflow.py
# Update patterns to match your repository structure
CHANGE_PATTERNS = {
    'go_files': ['**/*.go', '**/go.mod', '**/go.sum'],
    'python_files': ['**/*.py', '**/requirements*.txt', '**/pyproject.toml'],
    # Add custom patterns as needed
}
```

#### Change detection is too broad

**Symptoms**:

- All jobs run on every commit
- Documentation changes trigger code tests
- Takes too long to run CI

**Solutions**:

1. **Add path filters**:

```yaml
# In workflow file
on:
  pull_request:
    paths-ignore:
      - '**.md'
      - 'docs/**'
      - 'LICENSE'
      - '.gitignore'
```

1. **Refine change patterns**:

```python
# In ci_workflow.py, make patterns more specific
CHANGE_PATTERNS = {
    'go_files': [
        'pkg/**/*.go',      # Only pkg directory
        'cmd/**/*.go',      # Only cmd directory
        'internal/**/*.go', # Only internal directory
        'go.mod',
        'go.sum'
    ]
}
```

1. **Add conditional job execution**:

```yaml
jobs:
  test-go:
    if: needs.detect-changes.outputs.go_files == 'true'
    # Only runs if Go files changed
```

### Release Issues

#### Release workflow not triggered

**Symptoms**:

- Tag pushed but no release created
- Workflow doesn't run on tag push
- Release job skipped

**Diagnosis**:

```bash
# Check if tag exists
git tag -l

# Check workflow triggers
grep -A 5 "on:" .github/workflows/release.yml

# Verify tag format
git tag -l "v*"
```

**Solutions**:

1. **Tag format doesn't match**:

```yaml
# Workflow expects specific tag format
on:
  push:
    tags:
      - 'v[0-9]+.[0-9]+.[0-9]+' # Matches v1.2.3
      - 'v[0-9]+.[0-9]+.[0-9]+-*' # Matches v1.2.3-go-1.24
```

1. **Recreate tag**:

```bash
# Delete and recreate tag
git tag -d v1.0.0
git push origin :refs/tags/v1.0.0

# Create with correct format
git tag v1.0.0
git push origin v1.0.0
```

1. **Workflow not enabled**:

```bash
# Check workflow is active
gh api repos/{owner}/{repo}/actions/workflows/release.yml \
  --jq '.state'

# Enable if disabled
gh workflow enable release.yml
```

#### Version mismatch in release

**Symptoms**:

- Tag version doesn't match artifact version
- Release notes show wrong version
- Multiple versions in same release

**Diagnosis**:

```bash
# Check tag version
git describe --tags

# Check version in code
grep -r "version" go.mod Cargo.toml package.json pyproject.toml

# Test release workflow locally
python .github/workflows/scripts/release_workflow.py get-target-version \
  --branch $(git branch --show-current) \
  --language go
```

**Solutions**:

1. **Update version in code**:

```bash
# For Go modules
go mod edit -module=github.com/owner/repo/v2

# For Rust
sed -i 's/version = ".*"/version = "1.0.0"/' Cargo.toml

# For Python
sed -i 's/version = ".*"/version = "1.0.0"/' pyproject.toml
```

1. **Use automated version bumping**:

```yaml
# Add version update step before release
- name: Update version
  run: |
    python .github/workflows/scripts/release_workflow.py update-version \
      --version ${{ github.ref_name }}
```

#### Cross-compilation fails

**Symptoms**:

- Build fails for specific platforms
- Linker errors on aarch64 or musl targets
- CGO errors on cross-compilation

**Diagnosis**:

```bash
# Test cross-compilation locally (Go)
GOOS=linux GOARCH=arm64 go build

# Test cross-compilation locally (Rust)
cargo build --target aarch64-unknown-linux-gnu

# Check for CGO usage
grep -r "import \"C\"" .
```

**Solutions**:

1. **Go cross-compilation with CGO**:

```yaml
# Disable CGO for static binaries
- name: Build
  env:
    CGO_ENABLED: 0
  run: |
    GOOS=linux GOARCH=amd64 go build -o dist/app-linux-amd64
```

1. **Rust cross-compilation setup**:

```toml
# Add to .cargo/config.toml
[target.aarch64-unknown-linux-gnu]
linker = "aarch64-linux-gnu-gcc"

[target.x86_64-unknown-linux-musl]
linker = "x86_64-linux-musl-gcc"
```

```yaml
# Install cross-compilation tools
- name: Install cross-compilation tools
  run: |
    sudo apt-get update
    sudo apt-get install -y \
      gcc-aarch64-linux-gnu \
      gcc-x86-64-linux-musl
```

1. **Use cross-compilation containers**:

```yaml
# Use cross-compilation action
- name: Build with cross
  run: |
    cargo install cross
    cross build --release --target aarch64-unknown-linux-gnu
```

### Cache Issues

#### Cache miss on every run

**Symptoms**:

- Cache restore always fails
- "Cache not found" message every time
- Build times don't improve

**Diagnosis**:

```bash
# Check cache key generation
python .github/workflows/scripts/automation_workflow.py generate-cache-key \
  --language go \
  --branch main \
  --debug

# List recent caches
gh api repos/{owner}/{repo}/actions/caches --jq '.actions_caches[].key'
```

**Solutions**:

1. **Fix cache key**:

```yaml
# Use correct cache key with file hashes
- name: Cache dependencies
  uses: actions/cache@v4
  with:
    path: |
      ~/.cache/go-build
      ~/go/pkg/mod
    key: ${{ runner.os }}-go-${{ hashFiles('**/go.sum') }}
    restore-keys: |
      ${{ runner.os }}-go-
```

1. **Add restore keys**:

```yaml
# Add fallback restore keys
restore-keys: |
  ${{ runner.os }}-go-${{ hashFiles('**/go.sum') }}
  ${{ runner.os }}-go-
```

1. **Check file exists for hash**:

```bash
# Verify hash files exist
test -f go.sum || echo "go.sum not found!"
test -f Cargo.lock || echo "Cargo.lock not found!"
```

#### Cache size too large

**Symptoms**:

- Warning: "Cache size exceeds limit"
- Cache save fails
- Error: "Cache size of XXX MB exceeds the 10GB limit"

**Solutions**:

1. **Exclude large directories**:

```yaml
- name: Cache dependencies
  uses: actions/cache@v4
  with:
    path: |
      ~/go/pkg/mod
      # Don't cache build artifacts
      # ~/.cache/go-build is too large
```

1. **Clean before caching**:

```bash
# Add cleanup step
- name: Clean cache
  run: |
    # Remove unnecessary files
    rm -rf ~/.cache/go-build/trim.txt
    go clean -cache -modcache -testcache
```

1. **Use multiple smaller caches**:

```yaml
# Split into multiple caches
- name: Cache Go modules
  uses: actions/cache@v4
  with:
    path: ~/go/pkg/mod
    key: go-mod-${{ hashFiles('**/go.sum') }}

- name: Cache Go build
  uses: actions/cache@v4
  with:
    path: ~/.cache/go-build
    key: go-build-${{ hashFiles('**/*.go') }}
```

### Helper Script Issues

#### Import error for helper modules

**Symptoms**:

- Error: "ModuleNotFoundError: No module named 'workflow_common'"
- Helper script import fails
- Python can't find modules

**Solutions**:

1. **Fix Python path**:

```yaml
- name: Run helper script
  run: |
    export PYTHONPATH="${PYTHONPATH}:${{ github.workspace }}/.github/workflows/scripts"
    python .github/workflows/scripts/ci_workflow.py generate-matrix
```

1. **Use absolute imports**:

```python
# In helper scripts, add path manipulation
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import workflow_common
```

1. **Install as package**:

```bash
# Create setup.py for helper scripts
pip install -e .github/workflows/scripts/
```

#### Helper script fails with cryptic error

**Symptoms**:

- Script exits with error code 1
- No clear error message
- Traceback is unhelpful

**Solutions**:

1. **Enable debug mode**:

```bash
# Run with debug flag
python .github/workflows/scripts/ci_workflow.py \
  generate-matrix \
  --debug \
  --verbose
```

1. **Add error handling**:

```python
# In helper scripts, wrap in try-except
try:
    result = generate_matrix(branch, languages)
except Exception as e:
    logger.error(f"Matrix generation failed: {e}", exc_info=True)
    sys.exit(1)
```

1. **Check dependencies**:

```bash
# Verify all dependencies installed
pip install -r .github/workflows/scripts/requirements.txt

# Check Python version
python --version  # Should be 3.13 or 3.14
```

### GitHub Actions Issues

#### Workflow fails with permissions error

**Symptoms**:

- Error: "Resource not accessible by integration"
- Permission denied errors
- Can't create release, push tag, etc.

**Solutions**:

1. **Add workflow permissions**:

```yaml
# At workflow or job level
permissions:
  contents: write # For releases, tags
  pull-requests: write # For PR comments
  issues: write # For issue comments
  packages: write # For GitHub Packages
```

1. **Use PAT instead of GITHUB_TOKEN**:

```yaml
# For operations requiring elevated permissions
- name: Create release
  env:
    GITHUB_TOKEN: ${{ secrets.PAT }}
  run: |
    gh release create v1.0.0
```

1. **Check repository settings**:

```bash
# Verify workflow permissions in repo settings
# Settings → Actions → General → Workflow permissions
# Should be "Read and write permissions"
```

#### Workflow timeout

**Symptoms**:

- Job canceled after 6 hours
- "The job was canceled because it exceeded the maximum execution time"
- Long-running builds

**Solutions**:

1. **Increase timeout**:

```yaml
jobs:
  build:
    timeout-minutes: 120 # Default is 360 (6 hours)
```

1. **Optimize build**:

```yaml
# Use caching
- name: Cache dependencies
  uses: actions/cache@v4

# Parallelize builds
strategy:
  matrix:
    target: [linux, macos]
```

1. **Split into multiple jobs**:

```yaml
jobs:
  build-linux:
    # Fast build

  build-macos:
    # Slow build, separate job
```

#### Rate limit exceeded

**Symptoms**:

- Error: "API rate limit exceeded"
- GitHub API calls fail
- 403 Forbidden responses

**Solutions**:

1. **Use GitHub App token** (higher rate limit):

```yaml
- name: Generate token
  uses: actions/create-github-app-token@v1
  with:
    app-id: ${{ secrets.APP_ID }}
    private-key: ${{ secrets.APP_PRIVATE_KEY }}
```

1. **Add delays between API calls**:

```python
import time

for repo in repositories:
    process_repo(repo)
    time.sleep(1)  # Avoid rate limiting
```

1. **Use pagination**:

```python
# Instead of fetching all at once
response = requests.get(
    f"{api_url}?per_page=100&page=1",
    headers={"Authorization": f"token {token}"}
)
```

## Debugging Techniques

### Enable debug logging

```yaml
# In workflow file
- name: Enable debug
  run: |
    echo "ACTIONS_STEP_DEBUG=true" >> $GITHUB_ENV
    echo "ACTIONS_RUNNER_DEBUG=true" >> $GITHUB_ENV
```

### Test workflows locally with act

```bash
# Install act
brew install act

# Test workflow
act -W .github/workflows/ci.yml \
  -s GITHUB_TOKEN="$(gh auth token)" \
  --container-architecture linux/amd64

# Test specific job
act -j test-go

# Dry run
act --dry-run
```

### Inspect workflow artifacts

```bash
# Download artifacts
gh run download <run-id>

# List artifacts
gh api repos/{owner}/{repo}/actions/runs/<run-id>/artifacts

# Extract and inspect
unzip artifact.zip
cat logs/debug.log
```

### Check workflow syntax

```bash
# Validate workflow files
actionlint .github/workflows/*.yml

# Check specific workflow
actionlint .github/workflows/ci.yml
```

## Getting Help

### Community Resources

- **GitHub Discussions**: Ask questions in repository discussions
- **Issues**: Report bugs via GitHub issues
- **Documentation**: Read all documentation in `docs/refactors/workflows/v2/`
- **Examples**: Check example workflows in `.github/workflows/examples/`

### Creating a Bug Report

When reporting issues, include:

1. **Workflow file** (sanitized)
1. **Error message** (full traceback)
1. **Environment**:
   - Runner OS
   - Language versions
   - Branch name
1. **Steps to reproduce**
1. **Expected vs actual behavior**
1. **Workflow run URL**

Example bug report:

```markdown
### Description

Matrix generation fails on stable-1-go-1.24 branch

### Workflow File

[Attach workflow file]

### Error Message
```

Error: matrix must define at least one vector

```

### Environment
- Runner: ubuntu-latest
- Branch: stable-1-go-1.24
- Language: Go 1.24

### Steps to Reproduce
1. Push to stable-1-go-1.24
2. Workflow runs
3. Matrix generation step fails

### Expected Behavior
Matrix should include Go 1.24

### Actual Behavior
Empty matrix generated

### Workflow Run
https://github.com/owner/repo/actions/runs/12345
```

## Emergency Procedures

### Disable v2 system immediately

```bash
# Disable feature flag
sed -i.bak 's/enabled: true/enabled: false/' .github/workflow-feature-flags.yml
git commit -am "fix(ci): disable v2 workflows due to critical issue"
git push origin main
```

### Revert to v1 workflows

```bash
# Restore v1 workflow files
git checkout HEAD~1 -- .github/workflows/ci.yml
git commit -m "revert(ci): restore v1 workflows"
git push origin main
```

### Contact support

For critical production issues:

1. **Disable affected workflows**
1. **Document the issue**
1. **Create incident report**
1. **Follow rollback procedures** (see [Rollback Guide](rollback-procedures.md))

## Prevention

### Best Practices

1. **Test in pilot repository first**
1. **Enable debug logging during migration**
1. **Monitor metrics closely**
1. **Have rollback plan ready**
1. **Keep backups of working configurations**
1. **Document custom changes**
1. **Review logs regularly**
1. **Update helper scripts incrementally**

### Pre-deployment Checklist

- [ ] Test locally with act
- [ ] Validate YAML syntax
- [ ] Check feature flags
- [ ] Verify version policies
- [ ] Test helper scripts
- [ ] Review permissions
- [ ] Monitor first run
- [ ] Have rollback ready

## Next Steps

1. **Review** common issues relevant to your setup
1. **Test** solutions in development environment
1. **Document** any new issues discovered
1. **Share** solutions with team
1. **Update** this guide with new findings

## References

- [Migration Guide](migration-guide.md)
- [Rollback Procedures](rollback-procedures.md)
- [CI Workflows Guide](../implementation/ci-workflows.md)
- [Release Workflows Guide](../implementation/release-workflows.md)
- [Testing Strategy](../implementation/testing-strategy.md)
- [Helper Scripts API](../reference/helper-scripts-api.md)
