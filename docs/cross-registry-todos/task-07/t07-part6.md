<!-- file: docs/cross-registry-todos/task-07/t07-part6.md -->
<!-- version: 1.0.0 -->
<!-- guid: t07-protobuf-packages-part6-v1w2x3y4-z5a6 -->

# Task 07 Part 6: Troubleshooting and Completion

## Troubleshooting Guide

### Issue 1: Buf Authentication Failed

**Symptoms:**
- `buf push` returns 401 Unauthorized
- "authentication required" errors
- Cannot login to BSR

**Causes:**
1. BUF_TOKEN not set or invalid
2. Token expired
3. Wrong username
4. Network connectivity issues

**Solutions:**

```bash
# Verify BUF_TOKEN is set
echo $BUF_TOKEN | wc -c  # Should be non-zero

# Test authentication locally
echo $BUF_TOKEN | buf registry login buf.build --username your-username --token-stdin

# Verify login
buf registry whoami

# Generate new token if needed
# Visit: https://buf.build/settings/tokens
```

**In Workflow:**

```yaml
# Verify secret is configured
- name: Check BUF_TOKEN
  env:
    BUF_TOKEN: ${{ secrets.BUF_TOKEN }}
  run: |
    if [ -z "$BUF_TOKEN" ]; then
        echo "❌ BUF_TOKEN secret not set"
        echo "Add at: Settings > Secrets > Actions > New repository secret"
        exit 1
    fi
    echo "✅ BUF_TOKEN is set"
```

### Issue 2: Code Generation Failed

**Symptoms:**
- `buf generate` produces no output
- Plugin errors
- Missing generated files

**Causes:**
1. buf.gen.yaml misconfigured
2. Plugin not available on BSR
3. Output directory permissions
4. Protobuf syntax errors

**Solutions:**

```bash
# Test generation locally
buf generate

# Check buf.gen.yaml syntax
cat buf.gen.yaml

# Verify plugins exist on BSR
buf registry plugin list

# Check specific plugin
buf registry plugin info buf.build/protocolbuffers/go

# Clear and regenerate
rm -rf gen/
buf generate
```

**Fix common buf.gen.yaml issues:**

```yaml
# ❌ Wrong: Using local plugin (not available in CI)
plugins:
  - name: go
    out: gen/go

# ✅ Correct: Using BSR remote plugin
plugins:
  - remote: buf.build/protocolbuffers/go
    out: gen/go
```

### Issue 3: Go Module Tag Conflicts

**Symptoms:**
- "tag already exists"
- Cannot create go-v* tag
- Version mismatch errors

**Causes:**
1. Tag already pushed
2. Local tag not pushed
3. Version collision

**Solutions:**

```bash
# List existing tags
git tag | grep "^go-v"

# Delete local tag
git tag -d go-v1.0.0

# Delete remote tag (use with caution!)
git push origin :go-v1.0.0

# Recreate tag
git tag -a go-v1.0.1 -m "Release Go SDK v1.0.1"
git push origin go-v1.0.1
```

### Issue 4: Python Package Build Failed

**Symptoms:**
- `python -m build` fails
- Missing dependencies
- setup.py errors

**Causes:**
1. Missing build dependencies
2. Invalid setup.py
3. Missing __init__.py files
4. Import errors

**Solutions:**

```bash
# Install build tools
pip install --upgrade build setuptools wheel

# Verify setup.py
python setup.py check

# Test import
python -c "import sys; sys.path.insert(0, '.'); import your_module"

# Build with verbose output
python -m build --verbose

# Check generated files
ls -lR dist/
```

**Fix Python package structure:**

```python
# Ensure __init__.py exists
sdk/python/
├── __init__.py          # Required!
├── ghcommon/
│   ├── __init__.py      # Required!
│   └── v1/
│       ├── __init__.py  # Required!
│       ├── api_pb2.py
│       └── api_pb2_grpc.py
├── setup.py
└── pyproject.toml
```

### Issue 5: TypeScript Build Errors

**Symptoms:**
- `npm run build` fails
- TypeScript compilation errors
- Missing type declarations

**Causes:**
1. Missing dependencies
2. tsconfig.json misconfigured
3. Import path errors
4. Node version mismatch

**Solutions:**

```bash
# Clean install
rm -rf node_modules package-lock.json
npm install

# Verify TypeScript config
npx tsc --showConfig

# Build with errors visible
npx tsc --noEmit

# Check for type errors
npx tsc --strict
```

**Fix common tsconfig.json issues:**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "declaration": true,
    "declarationMap": true,
    "outDir": "./dist",
    "rootDir": "./",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["**/*.ts"],
  "exclude": ["node_modules", "dist", "**/*.test.ts"]
}
```

### Issue 6: Rust Crate Publishing Failed

**Symptoms:**
- `cargo publish` fails
- "crate name already exists"
- Version conflict

**Causes:**
1. Crate name taken
2. Version already published
3. CARGO_REGISTRY_TOKEN invalid
4. Missing documentation

**Solutions:**

```bash
# Check if crate name available
cargo search your-crate-name

# Verify Cargo.toml
cargo verify-project

# Dry run publish
cargo publish --dry-run

# Check token
cargo login --registry crates-io $CARGO_REGISTRY_TOKEN

# Publish with verbose output
cargo publish --verbose
```

**Fix Cargo.toml issues:**

```toml
[package]
name = "your-crate-name"     # Must be unique on crates.io
version = "0.1.0"             # Must be higher than last published
edition = "2021"              # Use latest edition
license = "MIT"               # Required for publishing
description = "..."           # Required for publishing
repository = "..."            # Recommended
documentation = "..."         # Recommended

[dependencies]
prost = "0.12"
tonic = "0.10"
```

### Issue 7: Breaking Changes Not Detected

**Symptoms:**
- Major breaking changes not flagged
- `buf breaking` passes incorrectly
- Missing previous tag

**Causes:**
1. No previous proto-v* tag
2. Wrong comparison target
3. Buf breaking rules too lenient

**Solutions:**

```bash
# List proto tags
git tag | grep "^proto-v" | sort -V

# Manually compare against previous tag
buf breaking --against ".git#tag=proto-v1.0.0"

# Check breaking rules in buf.yaml
cat buf.yaml | grep -A5 "breaking:"

# Strict breaking detection
cat > buf.yaml << EOF
breaking:
  use:
    - FILE
    - WIRE_JSON
  except: []  # No exceptions
EOF
```

### Issue 8: BSR Module Not Accessible

**Symptoms:**
- Cannot import from BSR
- `buf pull` fails after publish
- 404 errors

**Causes:**
1. Module name mismatch in buf.yaml
2. Propagation delay
3. Module not public
4. Authentication issues

**Solutions:**

```bash
# Verify module name matches BSR
cat buf.yaml | grep "name:"

# Should be: buf.build/your-org/your-repo

# Check module on BSR
open "https://buf.build/your-org/your-repo"

# Wait for propagation (can take 1-2 minutes)
sleep 120

# Try to pull with explicit auth
buf pull buf.build/your-org/your-repo:proto-v1.0.0

# Make repository public on BSR if needed
# Visit: https://buf.build/your-org/your-repo/settings
```

### Issue 9: Multi-Language SDK Version Mismatch

**Symptoms:**
- Different versions across languages
- Tags out of sync
- Import errors between SDKs

**Causes:**
1. Parallel publishing race conditions
2. Manual version updates
3. Failed job but partial completion

**Solutions:**

```bash
# List all version tags
git tag | grep -E "(proto|go|python|typescript|rust)-v"

# Should all have same version number:
# proto-v1.0.0
# go-v1.0.0
# python-v1.0.0
# typescript-v1.0.0
# rust-v1.0.0

# Delete mismatched tags
git tag -d go-v1.0.1
git push origin :go-v1.0.1

# Re-run workflow from proto-v1.0.0 tag
```

### Issue 10: Workflow Permission Denied

**Symptoms:**
- "Resource not accessible"
- Cannot create tags
- Cannot push commits

**Causes:**
1. GITHUB_TOKEN permissions insufficient
2. Branch protection rules
3. Workflow permissions not set

**Solutions:**

```yaml
# In workflow file, ensure permissions set:
permissions:
  contents: write    # For tags and commits
  packages: write    # For GitHub Packages

# Or in repository settings:
# Settings > Actions > General > Workflow permissions
# Select: Read and write permissions
```

## Complete Workflow Summary

### Full Job Dependency Graph

```
trigger: proto-v* tag
    ↓
detect-protobuf (detects .proto files, extracts version)
    ↓
validate-protobuf (buf lint, breaking changes)
    ↓
collect-protobuf-stats (statistics, analysis)
    ↓
publish-buf-bsr (push to Buf Schema Registry)
    ↓
generate-sdks (matrix: go, python, typescript, rust)
    ↓
    ├── publish-go-sdk (git tag)
    ├── publish-python-sdk (PyPI)
    ├── publish-typescript-sdk (npm)
    └── publish-rust-sdk (crates.io)
    ↓
    ├── create-github-release (release with artifacts)
    ├── generate-documentation (API docs)
    └── verify-publication (verify all registries)
```

### Environment Variables Reference

```yaml
env:
  # Buf Configuration
  BUF_VERSION: '1.28.1'
  BUF_MODULE_NAME: 'buf.build/jdfalk/ghcommon'

  # Language Versions
  GO_VERSION: '1.21'
  PYTHON_VERSION: '3.11'
  NODE_VERSION: '20'
  RUST_VERSION: 'stable'

  # Publishing Flags
  PUBLISH_TO_BSR: 'true'
  PUBLISH_GO_SDK: 'true'
  PUBLISH_PYTHON_SDK: 'true'
  PUBLISH_TYPESCRIPT_SDK: 'true'
  PUBLISH_RUST_SDK: 'true'
  DRY_RUN: 'false'
```

### Required Secrets

```
BUF_TOKEN              - Buf Schema Registry (buf.build/settings/tokens)
CARGO_REGISTRY_TOKEN   - crates.io (crates.io/settings/tokens)
NPM_TOKEN              - npm (npmjs.com/settings/tokens)
PYPI_TOKEN             - PyPI (pypi.org/manage/account/token)
GITHUB_TOKEN           - Automatic (no setup needed)
```

### All Artifacts Generated

```
bsr-publication-info/          - BSR URLs and import instructions
sdk-go-{version}/              - Generated Go SDK
sdk-python-{version}/          - Generated Python SDK
sdk-typescript-{version}/      - Generated TypeScript SDK
sdk-rust-{version}/            - Generated Rust SDK
go-installation-instructions/  - Go installation guide
python-installation-instructions/ - Python installation guide
typescript-installation-instructions/ - TypeScript installation guide
rust-installation-instructions/ - Rust installation guide
breaking-changes-report/       - Breaking change details (if any)
protobuf-statistics/           - JSON statistics
api-documentation/             - Complete API docs (MD, HTML, JSON)
verification-report/           - Publication verification status
```

## Pre-Flight Checklist

### Before First Protobuf Release

- [ ] Protobuf files exist in `proto/` directory
- [ ] `buf.yaml` configured with correct module name
- [ ] `buf.gen.yaml` configured for all target languages
- [ ] All protobuf files follow style guide
- [ ] `buf lint` passes with no errors
- [ ] BUF_TOKEN secret configured
- [ ] CARGO_REGISTRY_TOKEN secret configured (for Rust)
- [ ] NPM_TOKEN secret configured (for TypeScript)
- [ ] PYPI_TOKEN secret configured (for Python)
- [ ] Repository is public or BSR module is public
- [ ] Workflow permissions set to "Read and write"

### Before Each Release

- [ ] Version number decided (follows semver)
- [ ] All protobuf changes reviewed
- [ ] Breaking changes documented (if any)
- [ ] `buf lint` passes
- [ ] `buf breaking` checked against previous version
- [ ] All tests pass for generated code
- [ ] Tag name follows pattern: `proto-v{version}`
- [ ] CHANGELOG updated (if maintained)
- [ ] No uncommitted changes

## Success Criteria

### After Successful Publication

You should see:

1. **Buf Schema Registry:**
   - Module visible at `https://buf.build/{owner}/{repo}`
   - Tag `proto-v{version}` listed
   - Can import: `buf pull buf.build/{owner}/{repo}:proto-v{version}`

2. **Go Module:**
   - Tag `go-v{version}` created
   - Indexed on pkg.go.dev (may take 10 minutes)
   - Can install: `go get github.com/{owner}/{repo}/sdk/go@v{version}`

3. **Python Package:**
   - Listed on PyPI: `https://pypi.org/project/{owner}-{repo}-proto`
   - Version {version} visible
   - Can install: `pip install {owner}-{repo}-proto=={version}`

4. **TypeScript Package:**
   - Listed on npm: `https://www.npmjs.com/package/@{owner}/{repo}-proto`
   - Version {version} published
   - Can install: `npm install @{owner}/{repo}-proto@{version}`

5. **Rust Crate:**
   - Listed on crates.io: `https://crates.io/crates/{owner}-{repo}-proto`
   - Version {version} published
   - Can add to Cargo.toml

6. **GitHub Release:**
   - Release created with tag `proto-v{version}`
   - All artifacts attached
   - Installation instructions included

### Verification Commands

```bash
# Buf BSR
buf pull buf.build/jdfalk/ghcommon:proto-v1.0.0

# Go module
go get github.com/jdfalk/ghcommon/sdk/go@v1.0.0

# Python package
pip install jdfalk-ghcommon-proto==1.0.0

# TypeScript package
npm view @jdfalk/ghcommon-proto@1.0.0

# Rust crate
cargo search jdfalk-ghcommon-proto

# GitHub release
curl -s https://api.github.com/repos/jdfalk/ghcommon/releases/latest | jq '.tag_name'
```

## Monitoring and Maintenance

### Monitor Package Health

```bash
# BSR statistics
buf stats buf.build/jdfalk/ghcommon

# Go module downloads (via pkg.go.dev)
open "https://pkg.go.dev/github.com/jdfalk/ghcommon/sdk/go"

# PyPI downloads
pip download --no-deps jdfalk-ghcommon-proto && ls -lh *.whl

# npm downloads
npm view @jdfalk/ghcommon-proto

# crates.io downloads
cargo search jdfalk-ghcommon-proto
```

### Update Protobuf Schemas

```bash
# Make changes to .proto files
vim proto/v1/api.proto

# Lint changes
buf lint

# Check for breaking changes
buf breaking --against ".git#tag=proto-v1.0.0"

# If breaking changes, bump major version
# Otherwise bump minor (new features) or patch (fixes)

# Create and push tag
git tag -a proto-v1.1.0 -m "Release protobuf schemas v1.1.0"
git push origin proto-v1.1.0

# Workflow will automatically:
# - Publish to BSR
# - Generate all SDKs
# - Publish to all registries
# - Create GitHub release
```

## Final Commit

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Stage all Task 07 files
git add \
  .github/workflows/protobuf-release.yml \
  docs/cross-registry-todos/task-07/

# Commit with comprehensive message
git commit -m "docs(task-07): complete protobuf multi-registry publishing documentation

Completed Task 07: Protobuf Package Publishing to Multiple Registries

Documentation Structure:
- Part 1: Overview, BSR basics, prerequisites, sample protobuf structure
- Part 2: Workflow setup, protobuf detection, Buf validation
- Part 3: BSR publishing, multi-language SDK generation
- Part 4: Publishing SDKs to language registries (Go, Python, TypeScript, Rust)
- Part 5: GitHub release, API documentation generation, verification
- Part 6: Troubleshooting guide, complete workflow summary, checklists

Workflow Features:
- Comprehensive protobuf detection and analysis
- Buf linting with DEFAULT + COMMENTS rules
- Breaking change detection against previous tags
- BSR publishing with versioned tags
- Multi-language SDK generation (Go, Python, TypeScript, Rust)
- Language-specific package publishing to native registries
- GitHub release with all artifacts
- API documentation generation (Markdown, HTML, JSON)
- Multi-registry verification

Publishing Targets:
- Buf Schema Registry (BSR) - buf.build
- Go Modules - pkg.go.dev via git tags
- Python - PyPI and GitHub Packages
- TypeScript - npm and GitHub Packages
- Rust - crates.io

SDK Generation:
- Go: protocolbuffers/go + grpc/go plugins
- Python: protocolbuffers/python + grpc/python + pyi plugins
- TypeScript: connectrpc/es + bufbuild/es plugins
- Rust: community/neoeinstein-prost + neoeinstein-tonic plugins

Troubleshooting Guide:
- Buf authentication failures
- Code generation issues
- Go module tag conflicts
- Python package build errors
- TypeScript compilation issues
- Rust crate publishing failures
- Breaking change detection
- BSR accessibility problems
- Multi-language version mismatches
- Workflow permission issues

Quality Assurance:
- Protobuf structure analysis
- Package/service/message/enum counting
- Dependency extraction
- Statistics JSON generation
- Breaking change reports
- Publication verification across all registries

Documentation:
- Complete API documentation generation
- Protoc-gen-doc integration
- Multiple output formats (MD, HTML, JSON)
- Auto-commit documentation to repository
- Installation instructions for all languages
- Comprehensive verification reports

Local Testing:
- test-protobuf-detection.sh
- test-buf-lint.sh
- test-breaking-changes.sh
- test-code-generation.sh
- test-bsr-publish-dry-run.sh
- test-go-module.sh
- test-python-package.sh
- test-complete-protobuf-release.sh

Files changed:
- docs/cross-registry-todos/task-07/t07-part1.md - Overview and prerequisites
- docs/cross-registry-todos/task-07/t07-part2.md - Detection and validation
- docs/cross-registry-todos/task-07/t07-part3.md - BSR and SDK generation
- docs/cross-registry-todos/task-07/t07-part4.md - Language registry publishing
- docs/cross-registry-todos/task-07/t07-part5.md - Release and documentation
- docs/cross-registry-todos/task-07/t07-part6.md - Troubleshooting and completion

Total: ~4,000 lines of detailed protobuf publishing documentation"
```

## Task 07 Complete! ✅

**Summary:**
- ✅ Complete workflow for protobuf package publishing
- ✅ Buf Schema Registry integration
- ✅ Multi-language SDK generation (4 languages)
- ✅ Publishing to 5+ package registries
- ✅ API documentation generation
- ✅ Comprehensive troubleshooting guide
- ✅ ~4,000 lines of detailed documentation

**Next Task:** Task 08 - CI Workflow Consolidation (Analyze and merge reusable-ci.yml implementations)

This completes the protobuf publishing task with everything needed for copy-paste execution!
