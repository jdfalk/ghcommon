<!-- file: docs/cross-registry-todos/task-06/t06-part1.md -->
<!-- version: 1.1.0 -->
<!-- guid: t06-frontend-packages-part1-j1k2l3m4-n5o6 -->

# Task 06 Part 1: Frontend Package Publishing Overview

> **Status:** ✅ Completed  
> **Updated:** `.github/workflows/release-frontend.yml` v1.3.0 adds detection, packaging, and
> publishing jobs for npm and GitHub Package Registry.  
> **Verification:** Workflow stages capture npm tarballs as artifacts and report registry publish
> attempts in the job summary.

## Task Summary

**Objective**: Implement npm package publishing to GitHub Packages and npm Registry for frontend
JavaScript/TypeScript packages.

**Scope**: Multi-framework support (React, Vue, Angular, Svelte, vanilla JS), scoped packages,
TypeScript compilation, ESM/CommonJS builds.

**Priority**: 2 (After Docker, Rust, Go, Python)

**Estimated Effort**: 6-8 hours

**Files to Modify**:

- `.github/workflows/release-frontend.yml` (create/update)
- Documentation: `docs/frontend-package-publishing.md`

## Prerequisites

### Required Knowledge

1. **npm Package Publishing**:
   - npm registry concepts
   - Scoped packages (`@owner/package-name`)
   - package.json metadata
   - Semantic versioning
   - npm dist-tags

2. **GitHub Packages for npm**:
   - GitHub Package Registry for npm
   - Authentication with GITHUB_TOKEN
   - .npmrc configuration
   - Package visibility (public/private)

3. **Frontend Build Tools**:
   - npm, yarn, pnpm package managers
   - TypeScript compilation (tsc)
   - Build tools (webpack, rollup, vite, esbuild)
   - Module formats (ESM, CommonJS, UMD)

4. **Package Structure**:
   - Entry points (main, module, types)
   - Bundling strategies
   - Tree-shaking support
   - Source maps

### Required Secrets

Configure in GitHub repository secrets:

| Secret Name    | Purpose                     | How to Get                 |
| -------------- | --------------------------- | -------------------------- |
| `NPM_TOKEN`    | npm registry publishing     | Create at npmjs.com        |
| `GITHUB_TOKEN` | GitHub Packages (automatic) | Provided by GitHub Actions |

### Required Files in Repository

For workflow to detect and publish frontend packages:

```
package.json          # Required - package metadata
tsconfig.json         # Optional - TypeScript config
.npmrc                # Optional - registry configuration
README.md             # Recommended - package documentation
LICENSE               # Recommended - license file
src/                  # Source code directory
dist/                 # Build output (generated)
```

## Background Reading

### npm Package Publishing Basics

**Official Documentation**:

- [npm CLI Documentation](https://docs.npmjs.com/cli/)
- [package.json Specification](https://docs.npmjs.com/cli/configuring-npm/package-json)
- [npm Publishing Guide](https://docs.npmjs.com/packages-and-modules/contributing-packages-to-the-registry)
- [Scoped Packages](https://docs.npmjs.com/cli/using-npm/scope)

**Key Concepts**:

1. **Package Metadata** (package.json):

   ```json
   {
     "name": "@owner/package-name",
     "version": "1.2.3",
     "description": "Package description",
     "main": "dist/index.js",
     "module": "dist/index.esm.js",
     "types": "dist/index.d.ts",
     "files": ["dist"],
     "scripts": {
       "build": "tsc",
       "prepublishOnly": "npm run build"
     }
   }
   ```

2. **Scoped Packages**:
   - Format: `@owner/package-name`
   - GitHub Packages requires scoped packages
   - npm registry supports both scoped and unscoped

3. **Package Versions**:
   - Follow semantic versioning: `MAJOR.MINOR.PATCH`
   - Pre-release versions: `1.0.0-alpha.1`, `1.0.0-beta.2`
   - npm dist-tags: `latest`, `next`, `beta`

### GitHub Packages for npm

**Official Documentation**:

- [GitHub Packages npm Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-npm-registry)
- [Publishing npm Packages](https://docs.github.com/en/packages/managing-github-packages-using-github-actions-workflows/publishing-and-installing-a-package-with-github-actions#publishing-a-package-using-an-action)
- [Authenticating to GitHub Packages](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-npm-registry#authenticating-to-github-packages)

**Key Concepts**:

1. **Registry URL**:
   - GitHub Packages: `https://npm.pkg.github.com/`
   - npm registry: `https://registry.npmjs.org/`

2. **Authentication**:

   ```bash
   # GitHub Packages uses GITHUB_TOKEN
   //npm.pkg.github.com/:_authToken=${GITHUB_TOKEN}

   # npm registry uses NPM_TOKEN
   //registry.npmjs.org/:_authToken=${NPM_TOKEN}
   ```

3. **Scoped Package Requirement**:
   - GitHub Packages requires `@owner/package-name` format
   - `owner` must match repository owner

4. **Package Visibility**:
   - Public packages: Visible to everyone
   - Private packages: Require authentication

### Frontend Build Tools and Module Formats

**Module Formats**:

1. **CommonJS (CJS)**:

   ```javascript
   // Older Node.js standard
   module.exports = myFunction;
   const myFunc = require('./module');
   ```

2. **ES Modules (ESM)**:

   ```javascript
   // Modern standard
   export default myFunction;
   import myFunc from './module';
   ```

3. **Universal Module Definition (UMD)**:
   ```javascript
   // Works in browsers and Node.js
   (function (root, factory) {
     if (typeof define === 'function' && define.amd) {
       define([], factory);
     } else if (typeof module === 'object' && module.exports) {
       module.exports = factory();
     } else {
       root.MyLib = factory();
     }
   })(typeof self !== 'undefined' ? self : this, function () {
     return {
       /* library code */
     };
   });
   ```

**Build Tools**:

1. **TypeScript (tsc)**:
   - Compiles TypeScript to JavaScript
   - Generates type declarations (.d.ts)
   - Multiple module formats support

2. **Rollup**:
   - Module bundler
   - Optimized for libraries
   - Tree-shaking support

3. **Webpack**:
   - Module bundler
   - Comprehensive plugin ecosystem
   - Best for applications

4. **Vite**:
   - Modern build tool
   - Fast development
   - Library mode support

5. **esbuild**:
   - Extremely fast bundler
   - Minimal configuration
   - Good for simple packages

## Current State Analysis

### Step 1: Check for Existing Frontend Workflows

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Check if release-frontend.yml exists
if [ -f ".github/workflows/release-frontend.yml" ]; then
    echo "✅ release-frontend.yml exists"
    cat .github/workflows/release-frontend.yml
else
    echo "❌ release-frontend.yml does not exist - will create"
fi
```

### Step 2: Check for package.json Files

```bash
# Search for package.json files in repository
echo "Searching for package.json files..."
find . -name "package.json" -not -path "*/node_modules/*" -exec echo "Found: {}" \;

# Check for frontend-specific directories
for dir in frontend/ ui/ web/ packages/; do
    if [ -d "$dir" ]; then
        echo "✅ Found frontend directory: $dir"
        if [ -f "$dir/package.json" ]; then
            echo "  Has package.json"
            cat "$dir/package.json" | grep -E '"name"|"version"|"main"|"module"'
        fi
    fi
done
```

### Step 3: Identify Package Manager

```bash
# Check which package manager is used
if [ -f "package-lock.json" ]; then
    echo "📦 Package manager: npm"
    PKG_MANAGER="npm"
elif [ -f "yarn.lock" ]; then
    echo "📦 Package manager: yarn"
    PKG_MANAGER="yarn"
elif [ -f "pnpm-lock.yaml" ]; then
    echo "📦 Package manager: pnpm"
    PKG_MANAGER="pnpm"
else
    echo "⚠️  No lock file found - will use npm as default"
    PKG_MANAGER="npm"
fi
```

### Step 4: Check Build Configuration

```bash
# Check for TypeScript
if [ -f "tsconfig.json" ]; then
    echo "✅ TypeScript configuration found"
    cat tsconfig.json | grep -E '"outDir"|"declaration"|"module"'
fi

# Check for build tools
if [ -f "rollup.config.js" ] || [ -f "rollup.config.mjs" ]; then
    echo "✅ Rollup configuration found"
fi

if [ -f "webpack.config.js" ]; then
    echo "✅ Webpack configuration found"
fi

if [ -f "vite.config.ts" ] || [ -f "vite.config.js" ]; then
    echo "✅ Vite configuration found"
fi
```

### Step 5: Analyze package.json Structure

```bash
# Extract key fields from package.json
if [ -f "package.json" ]; then
    echo "=== Package Metadata ==="
    echo ""

    # Name (check if scoped)
    NAME=$(jq -r '.name' package.json)
    if [[ "$NAME" == @*/* ]]; then
        echo "✅ Scoped package: $NAME"
    else
        echo "⚠️  Unscoped package: $NAME"
        echo "   GitHub Packages requires scoped packages"
    fi

    # Version
    VERSION=$(jq -r '.version' package.json)
    echo "Version: $VERSION"

    # Entry points
    echo ""
    echo "Entry Points:"
    jq -r '.main // "Not specified"' package.json | sed 's/^/  main: /'
    jq -r '.module // "Not specified"' package.json | sed 's/^/  module: /'
    jq -r '.types // "Not specified"' package.json | sed 's/^/  types: /'

    # Build script
    echo ""
    echo "Build Script:"
    jq -r '.scripts.build // "Not specified"' package.json | sed 's/^/  build: /'

    # Files included
    echo ""
    echo "Files Included:"
    jq -r '.files[]? // "Not specified"' package.json | sed 's/^/  - /'
fi
```

## Publishing Architecture Design

### Overview

The frontend package publishing workflow will:

1. **Detect** frontend packages (package.json presence)
2. **Install** dependencies using appropriate package manager
3. **Build** package (compile TypeScript, bundle, etc.)
4. **Validate** package structure and metadata
5. **Test** package installation
6. **Publish** to npm registry and GitHub Packages
7. **Create** GitHub Release with built artifacts

### Workflow Structure

```
release-frontend.yml
├── detect-frontend-package (job)
│   ├── Find package.json
│   ├── Detect package manager
│   ├── Extract metadata
│   └── Validate configuration
├── build-frontend-package (job)
│   ├── Install dependencies
│   ├── Run build script
│   ├── Generate declarations
│   └── Create tarball
├── validate-frontend-package (job)
│   ├── Check package structure
│   ├── Validate metadata
│   ├── Test installation
│   └── Check bundle size
├── publish-npm-registry (job)
│   ├── Configure npm authentication
│   ├── Publish to npm
│   └── Verify publication
├── publish-github-packages (job)
│   ├── Configure GitHub Packages
│   ├── Publish to GitHub Packages
│   └── Verify publication
└── create-release (job)
    ├── Attach npm tarball
    └── Generate installation instructions
```

### Detection Strategy

The workflow will detect frontend packages by:

1. **Primary indicator**: `package.json` file exists
2. **Package type verification**:
   - Check `package.json` has `name` and `version`
   - Verify build script exists
   - Check for dist/lib output directory
3. **Exclusion criteria**:
   - Skip if `private: true` in package.json
   - Skip if no build script defined
   - Skip workspace root packages (monorepo roots)

### Build Strategy

Support multiple build configurations:

1. **TypeScript Projects**:
   - Run `tsc` to compile
   - Generate type declarations
   - Support multiple tsconfig.json files

2. **Bundled Projects**:
   - Run build script from package.json
   - Support rollup, webpack, vite, esbuild
   - Generate multiple format outputs (ESM, CJS, UMD)

3. **Plain JavaScript Projects**:
   - Copy source files
   - Optionally minify
   - Generate source maps

### Multi-Registry Publishing

Publish to both registries sequentially:

1. **npm Registry** (optional, requires NPM_TOKEN):
   - Public by default
   - Wider distribution
   - Discoverable via npmjs.com

2. **GitHub Packages** (default, uses GITHUB_TOKEN):
   - Scoped packages required
   - Integrated with repository
   - Private packages supported

### Version Management

Synchronize versions between Git tags and package.json:

```
Git Tag: v1.2.3
↓
package.json: "version": "1.2.3"
↓
Published: @owner/package@1.2.3
```

Workflow validates version consistency before publishing.

## Implementation Design

### Job Dependencies

```
detect-frontend-package
    ↓
build-frontend-package
    ↓
validate-frontend-package
    ↓
    ├── publish-npm-registry
    └── publish-github-packages
    ↓
create-release
```

### Environment Variables

```yaml
env:
  NODE_VERSION: '20' # LTS version
  NPM_REGISTRY: 'https://registry.npmjs.org/'
  GITHUB_PACKAGES_REGISTRY: 'https://npm.pkg.github.com/'
  PUBLISH_TO_NPM: 'false' # Enable when NPM_TOKEN configured
  PUBLISH_TO_GITHUB_PACKAGES: 'true'
```

### Outputs

**detect-frontend-package outputs**:

- `has-package`: Whether frontend package exists
- `package-name`: Package name from package.json
- `package-version`: Package version
- `package-manager`: Detected package manager (npm/yarn/pnpm)
- `package-dir`: Directory containing package.json

**build-frontend-package outputs**:

- `tarball-name`: Generated .tgz filename
- `bundle-size`: Size of built package

## Next Steps

**Continue to Part 2:** Workflow header and package detection implementation with support for
multiple package managers.

## Quick Reference

### Key Files

- **Workflow**: `.github/workflows/release-frontend.yml`
- **Documentation**: `docs/frontend-package-publishing.md`
- **Example package.json**: Include complete example

### Validation Checklist

Before implementation:

- [ ] Understand npm package structure
- [ ] Know scoped package requirements for GitHub Packages
- [ ] Understand module formats (ESM, CJS, UMD)
- [ ] Familiar with TypeScript compilation
- [ ] Know package manager differences (npm, yarn, pnpm)

During implementation:

- [ ] Workflow detects package.json correctly
- [ ] Package manager auto-detection works
- [ ] Build completes successfully
- [ ] Package structure validated
- [ ] Both registries configured
- [ ] Publishing succeeds

After implementation:

- [ ] Package installable from npm
- [ ] Package installable from GitHub Packages
- [ ] Type definitions work correctly
- [ ] ESM and CJS imports both work
- [ ] Documentation updated
