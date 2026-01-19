<!-- file: docs/cross-registry-todos/task-06/t06-part6.md -->
<!-- version: 1.0.0 -->
<!-- guid: t06-frontend-packages-part6-z3a4b5c6-d7e8 -->
<!-- last-edited: 2026-01-19 -->

# Task 06 Part 6: Documentation, Troubleshooting, and Completion

## Complete Workflow File

### Save as: `.github/workflows/release-frontend.yml`

```yaml
<!-- file: .github/workflows/release-frontend.yml -->
<!-- version: 1.0.0 -->
<!-- guid: release-frontend-workflow-f9g0h1i2-j3k4 -->
<!-- last-edited: 2026-01-19 -->

name: Release Frontend Packages

on:
  push:
    tags:
      - 'v*'
      - 'frontend-v*'
  workflow_dispatch:
    inputs:
      dry_run:
        description: 'Dry run (skip publishing)'
        required: false
        default: 'false'

env:
  NODE_VERSION: '20'
  NPM_REGISTRY: 'https://registry.npmjs.org'
  GITHUB_PACKAGES_REGISTRY: 'https://npm.pkg.github.com'
  PUBLISH_TO_NPM: 'true'
  PUBLISH_TO_GITHUB_PACKAGES: 'true'
  NPM_PUBLISH_TAG: 'latest'

permissions:
  contents: write
  packages: write

jobs:
  # [All jobs from parts 2-5 go here]
  # detect-frontend-package
  # build-frontend-package
  # validate-frontend-package
  # publish-npm
  # publish-github-packages
  # create-github-release
  # verify-publication
  # collect-metrics
```

## Troubleshooting Guide

### Issue 1: Package Not Found After Publishing

**Symptoms:**

- `npm view` returns 404
- `npm install` fails with "package not found"
- Published successfully but not visible

**Causes:**

1. npm registry propagation delay
2. Package name typo
3. Scope configuration issue
4. Authentication problems

**Solutions:**

```bash
# 1. Wait and retry (propagation takes 30-60 seconds)
sleep 60
npm view @scope/package@version

# 2. Verify package name
npm view @scope/package  # Check exact name

# 3. Check scope configuration
npm config get @scope:registry

# 4. Clear cache
npm cache clean --force
npm view @scope/package@version
```

### Issue 2: GitHub Packages Authentication Failed

**Symptoms:**

- 401 Unauthorized
- "authentication required"
- GITHUB_TOKEN issues

**Causes:**

1. GITHUB_TOKEN missing
2. Wrong registry URL
3. .npmrc misconfigured
4. Token permissions insufficient

**Solutions:**

```yaml
# In workflow:
- name: Fix GitHub Packages auth
  run: |
    cat > .npmrc << EOF
    @${{ github.repository_owner }}:registry=https://npm.pkg.github.com
    //npm.pkg.github.com/:_authToken=\${NODE_AUTH_TOKEN}
    EOF
  env:
    NODE_AUTH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

# Verify token permissions
permissions:
  packages: write  # Required!
```

### Issue 3: Build Fails in CI

**Symptoms:**

- `npm run build` fails
- Missing dependencies
- TypeScript errors

**Causes:**

1. Missing devDependencies
2. Node version mismatch
3. Environment-specific code

**Solutions:**

```yaml
# 1. Install all dependencies including dev
- name: Install dependencies
  run: |
    # Use ci for reproducible builds
    npm ci

    # Or explicitly install dev deps
    npm install --include=dev

# 2. Match Node version
- uses: actions/setup-node@v4
  with:
    node-version: '20' # Match local dev

# 3. Check environment
- name: Debug environment
  run: |
    node --version
    npm --version
    echo "NODE_ENV: $NODE_ENV"
```

### Issue 4: Tarball Too Large

**Symptoms:**

- Tarball >5MB
- Slow installation
- Unpacked size warnings

**Causes:**

1. Source files included
2. Test files in package
3. Missing .npmignore
4. Development assets included

**Solutions:**

Create `.npmignore`:

```
# .npmignore
src/
tests/
*.test.js
*.spec.js
.github/
.vscode/
*.log
coverage/
docs/
examples/
*.map
*.md
!README.md
tsconfig.json
.eslintrc.js
.prettierrc
```

Or use `package.json` files field:

```json
{
  "files": ["dist/", "lib/", "README.md", "LICENSE"]
}
```

### Issue 5: TypeScript Declarations Missing

**Symptoms:**

- No type hints in IDE
- `Could not find declaration file`
- Types not found

**Causes:**

1. Missing `types` field in package.json
2. Declaration files not generated
3. Declaration files not included

**Solutions:**

```json
// package.json
{
  "main": "./dist/index.js",
  "types": "./dist/index.d.ts",
  "files": ["dist/"]
}
```

```json
// tsconfig.json
{
  "compilerOptions": {
    "declaration": true,
    "declarationMap": true,
    "outDir": "./dist"
  }
}
```

### Issue 6: Scoped Package Publishing Fails

**Symptoms:**

- "scope not found"
- "payment required" for public scoped package
- 402 error

**Causes:**

1. Scope organization not configured
2. Package not marked as public
3. npm account issue

**Solutions:**

```bash
# Publish as public (required for free accounts)
npm publish --access public

# In workflow:
- name: Publish
  run: npm publish --access public
```

```json
// package.json
{
  "name": "@scope/package",
  "publishConfig": {
    "access": "public"
  }
}
```

### Issue 7: Package Manager Detection Fails

**Symptoms:**

- Wrong package manager used
- Lock file conflicts
- Installation failures

**Causes:**

1. Multiple lock files present
2. Lock file detection logic issues
3. Package manager not installed

**Solutions:**

```bash
# Clean up lock files
rm -f package-lock.json yarn.lock pnpm-lock.yaml
npm install  # Recreate with preferred manager

# Or commit only one lock file
git rm yarn.lock pnpm-lock.yaml
git add package-lock.json
git commit -m "fix: use npm as package manager"
```

### Issue 8: Import Fails After Installation

**Symptoms:**

- `Cannot find module`
- Import errors in consuming project
- Module format issues

**Causes:**

1. Missing exports in package.json
2. Wrong entry point
3. ES Module vs CommonJS issues

**Solutions:**

```json
// package.json - Modern dual package
{
  "name": "@scope/package",
  "version": "1.0.0",
  "type": "module",
  "main": "./dist/index.cjs",
  "module": "./dist/index.js",
  "exports": {
    ".": {
      "import": "./dist/index.js",
      "require": "./dist/index.cjs",
      "types": "./dist/index.d.ts"
    }
  },
  "types": "./dist/index.d.ts"
}
```

## Documentation Updates

### Update README.md

```markdown
## Installation

### From npm

\`\`\`bash npm install @scope/package \`\`\`

### From GitHub Packages

1. Create `.npmrc` in your project: \`\`\` @scope:registry=https://npm.pkg.github.com
   //npm.pkg.github.com/:\_authToken=${GITHUB_TOKEN} \`\`\`

2. Install: \`\`\`bash npm install @scope/package \`\`\`

## Usage

### ES Modules

\`\`\`javascript import { feature } from '@scope/package'; \`\`\`

### CommonJS

\`\`\`javascript const { feature } = require('@scope/package'); \`\`\`

### TypeScript

\`\`\`typescript import { feature } from '@scope/package'; // Types are automatically available
\`\`\`

## Development

\`\`\`bash

# Install dependencies

npm install

# Build

npm run build

# Test

npm test

# Publish (requires authentication)

npm publish --access public \`\`\`
```

### Create CONTRIBUTING.md

```markdown
# Contributing

## Publishing Releases

Releases are automated via GitHub Actions:

1. Update version: \`\`\`bash npm version patch|minor|major \`\`\`

2. Push tag: \`\`\`bash git push --tags \`\`\`

3. GitHub Actions will:
   - Build package
   - Run validation
   - Publish to npm
   - Publish to GitHub Packages
   - Create GitHub Release

## Manual Publishing

If needed, you can publish manually:

\`\`\`bash

# Build

npm run build

# Test

npm pack npm install ./package-name-version.tgz

# Publish to npm

npm publish --access public

# Publish to GitHub Packages

npm config set @scope:registry https://npm.pkg.github.com npm publish \`\`\`
```

## Pre-Flight Checklist

### Before First Publish

- [ ] Package name is available on npm (`npm view @scope/name`)
- [ ] Scope matches GitHub organization
- [ ] `package.json` has all required fields (name, version, main, types)
- [ ] `.npmignore` or `files` configured correctly
- [ ] TypeScript declarations generated
- [ ] Build produces correct output
- [ ] Local installation test passes
- [ ] README has installation instructions
- [ ] LICENSE file present
- [ ] GitHub repo is public (or npm account configured)

### Before Each Release

- [ ] Version number updated (`npm version`)
- [ ] CHANGELOG updated
- [ ] All tests pass
- [ ] Build successful
- [ ] No uncommitted changes
- [ ] Tag created and pushed
- [ ] NPM_TOKEN secret configured (for npm)
- [ ] GITHUB_TOKEN permissions correct (for GitHub Packages)

## Success Criteria

### After Successful Publication

You should see:

1. **GitHub Actions**: All jobs green
2. **npm**: Package visible at `https://www.npmjs.com/package/@scope/name`
3. **GitHub Packages**: Package listed in repository packages
4. **GitHub Release**: Release created with tarball attached
5. **Installation Test**: `npm install @scope/name@version` works

### Verification Commands

```bash
# Check npm
npm view @scope/name@version

# Check installation
mkdir test-install
cd test-install
npm init -y
npm install @scope/name@version
node -e "const pkg = require('@scope/name'); console.log(pkg)"

# Check GitHub Packages
npm config set @scope:registry https://npm.pkg.github.com
npm view @scope/name@version

# Check GitHub Release
curl -s https://api.github.com/repos/owner/repo/releases/latest | jq '.tag_name'
```

## Monitoring and Maintenance

### Monitor Package Health

```bash
# npm downloads
npm info @scope/name

# Package size
npm view @scope/name dist.tarball

# Dependencies
npm view @scope/name dependencies

# Versions
npm view @scope/name versions
```

### Update Dependencies

```bash
# Check outdated
npm outdated

# Update dependencies
npm update

# Update to latest
npm install package@latest

# Rebuild and test
npm run build
npm test
```

## Final Commit

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Stage all changes
git add \
  .github/workflows/release-frontend.yml \
  docs/cross-registry-todos/task-06/

# Commit with comprehensive message
git commit -m "docs(task-06): complete frontend package publishing documentation

Completed Task 06: Frontend/npm Package Publishing to Multiple Registries

Documentation Structure:
- Part 1: Overview, prerequisites, npm and GitHub Packages basics
- Part 2: Workflow setup, package detection, multi-package-manager support
- Part 3: Dependency installation, building, tarball creation
- Part 4: Package validation, import testing, metadata verification
- Part 5: GitHub release, publication verification, metrics collection
- Part 6: Troubleshooting, documentation, completion checklist

Workflow Features:
- Multi-registry publishing (npm + GitHub Packages)
- Package manager detection (npm/yarn/pnpm/yarn-berry)
- Comprehensive validation (installation, ESM, CJS, TypeScript)
- Automated GitHub releases with changelogs
- Publication verification with retries
- Package metrics and size analysis

Publishing Capabilities:
- npm registry with public/scoped packages
- GitHub Packages with automatic .npmrc configuration
- Configurable dist-tags (latest, next, beta)
- Prerelease detection and marking
- Multi-format support (ESM, CommonJS, UMD)
- TypeScript declaration handling

Troubleshooting Guide:
- Package not found after publishing
- GitHub Packages authentication issues
- Build failures in CI
- Tarball size optimization
- TypeScript declarations
- Scoped package publishing
- Package manager detection
- Import failures after installation

Quality Assurance:
- Installation testing from tarball
- ESM and CommonJS import verification
- Metadata validation (required + recommended fields)
- TypeScript support checking
- Size analysis and warnings
- Entry point verification

Documentation Includes:
- Complete workflow configuration
- Local testing scripts
- Troubleshooting for 8 common issues
- README and CONTRIBUTING templates
- Pre-flight checklists
- Success criteria
- Monitoring commands

Files changed:
- docs/cross-registry-todos/task-06/t06-part4.md - Validation and publishing
- docs/cross-registry-todos/task-06/t06-part5.md - GitHub release and verification
- docs/cross-registry-todos/task-06/t06-part6.md - Documentation and troubleshooting

Total: ~3,500 lines of detailed documentation for frontend package publishing"
```

## Task 06 Complete! ✅

**Summary:**

- ✅ Created complete workflow for frontend package publishing
- ✅ Supports npm and GitHub Packages
- ✅ Handles multiple package managers (npm, yarn, pnpm)
- ✅ Comprehensive validation and testing
- ✅ Automated GitHub releases
- ✅ Publication verification
- ✅ Complete troubleshooting guide
- ✅ ~3,500 lines of detailed documentation

**Next Task:** Task 07 - Protobuf Package Publishing to BSR and Multiple Registries

This completes the frontend/npm package publishing task with all necessary documentation for
copy-paste execution!
