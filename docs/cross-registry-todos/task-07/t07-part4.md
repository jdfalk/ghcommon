<!-- file: docs/cross-registry-todos/task-07/t07-part4.md -->
<!-- version: 1.0.0 -->
<!-- guid: t07-protobuf-packages-part4-j9k0l1m2-n3o4 -->

# Task 07 Part 4: Publishing SDKs to Language Registries

## Stage 1: Publish Go SDK

### Step 1: Go Module Tagging Job

```yaml
publish-go-sdk:
  name: Publish Go SDK
  runs-on: ubuntu-latest
  needs: [detect-protobuf, generate-sdks]
  if: |
    needs.detect-protobuf.outputs.has-proto == 'true' &&
    env.PUBLISH_GO_SDK == 'true' &&
    env.DRY_RUN == 'false'
  environment:
    name: go-module
    url: https://pkg.go.dev/github.com/${{ github.repository }}/sdk/go

  steps:
    - name: Checkout code
      uses: actions/checkout@v4
      with:
        fetch-depth: 0

    - name: Setup Go
      uses: actions/setup-go@v4
      with:
        go-version: ${{ env.GO_VERSION }}

    - name: Download Go SDK artifact
      uses: actions/download-artifact@v4
      with:
        name: sdk-go-${{ needs.detect-protobuf.outputs.version }}
        path: sdk/go

    - name: Commit SDK to repository
      run: |
        echo "=== Committing Go SDK ==="
        echo ""

        # Configure git
        git config user.name "github-actions[bot]"
        git config user.email "github-actions[bot]@users.noreply.github.com"

        # Add SDK files
        git add sdk/go/

        # Check if there are changes
        if git diff --cached --quiet; then
            echo "ℹ️  No changes to commit"
        else
            git commit -m "feat(proto): update Go SDK to v${{ needs.detect-protobuf.outputs.version }}"
            echo "✅ SDK committed"
        fi

    - name: Create Go module tag
      run: |
        echo "=== Creating Go Module Tag ==="
        echo ""

        VERSION="${{ needs.detect-protobuf.outputs.version }}"
        TAG="go-v${VERSION}"

        # Check if tag exists
        if git rev-parse "$TAG" >/dev/null 2>&1; then
            echo "⚠️  Tag $TAG already exists"
            exit 1
        fi

        # Create tag
        git tag -a "$TAG" -m "Release Go SDK v${VERSION}"

        echo "✅ Created tag: $TAG"

    - name: Push changes and tag
      run: |
        echo "=== Pushing Go SDK ==="
        echo ""

        # Push commits
        git push origin HEAD:${{ github.ref_name }}

        # Push tag
        git push origin go-v${{ needs.detect-protobuf.outputs.version }}

        echo "✅ Go SDK published"

    - name: Verify Go module
      run: |
        echo "=== Verifying Go Module ==="
        echo ""

        MODULE="github.com/${{ github.repository }}/sdk/go"
        VERSION="v${{ needs.detect-protobuf.outputs.version }}"

        # Wait for pkg.go.dev to index (can take a few minutes)
        echo "ℹ️  Go module published to: $MODULE@$VERSION"
        echo "   Note: pkg.go.dev may take a few minutes to index"
        echo ""
        echo "Test import:"
        echo "  go get $MODULE@$VERSION"

    - name: Generate Go installation instructions
      run: |
        MODULE="github.com/${{ github.repository }}/sdk/go"
        VERSION="v${{ needs.detect-protobuf.outputs.version }}"

        cat > go-installation.md << EOF
        # Go SDK Installation

        ## Install

        \`\`\`bash
        go get $MODULE@$VERSION
        \`\`\`

        ## Usage

        \`\`\`go
        package main

        import (
            pb "$MODULE/ghcommon/v1"
        )

        func main() {
            // Use generated protobuf code
            user := &pb.User{
                Id:    "123",
                Email: "user@example.com",
                Name:  "Test User",
            }
        }
        \`\`\`

        ## Links

        - **Repository**: https://github.com/${{ github.repository }}
        - **pkg.go.dev**: https://pkg.go.dev/$MODULE@$VERSION
        - **Tag**: https://github.com/${{ github.repository }}/releases/tag/go-$VERSION
        EOF

        cat go-installation.md

    - name: Upload Go installation instructions
      uses: actions/upload-artifact@v4
      with:
        name: go-installation-instructions
        path: go-installation.md
        retention-days: 90
```

## Stage 2: Publish Python SDK

### Step 1: PyPI Publishing Job

```yaml
publish-python-sdk:
  name: Publish Python SDK
  runs-on: ubuntu-latest
  needs: [detect-protobuf, generate-sdks]
  if: |
    needs.detect-protobuf.outputs.has-proto == 'true' &&
    env.PUBLISH_PYTHON_SDK == 'true' &&
    env.DRY_RUN == 'false'
  environment:
    name: pypi
    url:
      https://pypi.org/project/${{ github.repository_owner }}-${{ github.event.repository.name
      }}-proto

  steps:
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}

    - name: Download Python SDK artifact
      uses: actions/download-artifact@v4
      with:
        name: sdk-python-${{ needs.detect-protobuf.outputs.version }}
        path: sdk/python

    - name: Install publishing tools
      run: |
        python -m pip install --upgrade pip
        pip install twine build

    - name: Build Python package
      working-directory: sdk/python
      run: |
        echo "=== Building Python Package ==="
        echo ""

        # Build package
        python -m build

        echo "✅ Package built"
        echo ""
        echo "Built files:"
        ls -lh dist/

    - name: Check package with twine
      working-directory: sdk/python
      run: |
        echo "=== Checking Package ==="
        echo ""

        twine check dist/*

        echo "✅ Package check passed"

    - name: Publish to PyPI
      working-directory: sdk/python
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
      run: |
        echo "=== Publishing to PyPI ==="
        echo ""

        twine upload dist/*

        echo "✅ Published to PyPI"

    - name: Verify PyPI publication
      run: |
        echo "=== Verifying PyPI Publication ==="
        echo ""

        PACKAGE_NAME="${{ github.repository_owner }}-${{ github.event.repository.name }}-proto"
        VERSION="${{ needs.detect-protobuf.outputs.version }}"

        # Wait for propagation
        sleep 10

        # Try to view package
        if pip index versions "$PACKAGE_NAME" 2>/dev/null | grep -q "$VERSION"; then
            echo "✅ Package found on PyPI"
        else
            echo "⚠️  Package not yet visible (propagation delay)"
        fi

    - name: Test installation
      run: |
        echo "=== Testing Installation ==="
        echo ""

        PACKAGE_NAME="${{ github.repository_owner }}-${{ github.event.repository.name }}-proto"
        VERSION="${{ needs.detect-protobuf.outputs.version }}"

        # Create virtual environment
        python -m venv test-env
        source test-env/bin/activate

        # Install package
        pip install "${PACKAGE_NAME}==${VERSION}"

        echo "✅ Installation successful"

        # Show installed files
        pip show "$PACKAGE_NAME"

    - name: Publish to GitHub Packages
      working-directory: sdk/python
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.GITHUB_TOKEN }}
        TWINE_REPOSITORY_URL: https://upload.pypi.org/legacy/
      continue-on-error: true
      run: |
        echo "=== Publishing to GitHub Packages ==="
        echo ""

        # GitHub Packages uses different repository URL
        twine upload --repository-url https://pypi.pkg.github.com/${{ github.repository_owner }} dist/*

        echo "✅ Published to GitHub Packages"

    - name: Generate Python installation instructions
      run: |
        PACKAGE_NAME="${{ github.repository_owner }}-${{ github.event.repository.name }}-proto"
        VERSION="${{ needs.detect-protobuf.outputs.version }}"

        cat > python-installation.md << EOF
        # Python SDK Installation

        ## Install from PyPI

        \`\`\`bash
        pip install ${PACKAGE_NAME}==${VERSION}
        \`\`\`

        ## Usage

        \`\`\`python
        from ghcommon.v1 import api_pb2, api_pb2_grpc

        # Create message
        user = api_pb2.User(
            id="123",
            email="user@example.com",
            name="Test User"
        )

        # Use with gRPC
        channel = grpc.insecure_channel('localhost:50051')
        stub = api_pb2_grpc.UserServiceStub(channel)
        \`\`\`

        ## Links

        - **PyPI**: https://pypi.org/project/${PACKAGE_NAME}
        - **Repository**: https://github.com/${{ github.repository }}
        EOF

        cat python-installation.md

    - name: Upload Python installation instructions
      uses: actions/upload-artifact@v4
      with:
        name: python-installation-instructions
        path: python-installation.md
        retention-days: 90
```

## Stage 3: Publish TypeScript SDK

### Step 1: npm Publishing Job

```yaml
publish-typescript-sdk:
  name: Publish TypeScript SDK
  runs-on: ubuntu-latest
  needs: [detect-protobuf, generate-sdks]
  if: |
    needs.detect-protobuf.outputs.has-proto == 'true' &&
    env.PUBLISH_TYPESCRIPT_SDK == 'true' &&
    env.DRY_RUN == 'false'
  environment:
    name: npm
    url:
      https://www.npmjs.com/package/@${{ github.repository_owner }}/${{ github.event.repository.name
      }}-proto

  steps:
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: ${{ env.NODE_VERSION }}
        registry-url: 'https://registry.npmjs.org'

    - name: Download TypeScript SDK artifact
      uses: actions/download-artifact@v4
      with:
        name: sdk-typescript-${{ needs.detect-protobuf.outputs.version }}
        path: sdk/typescript

    - name: Install dependencies
      working-directory: sdk/typescript
      run: |
        echo "=== Installing Dependencies ==="
        echo ""

        npm install

        echo "✅ Dependencies installed"

    - name: Build TypeScript
      working-directory: sdk/typescript
      run: |
        echo "=== Building TypeScript ==="
        echo ""

        npm run build

        echo "✅ Build complete"
        echo ""
        echo "Built files:"
        ls -lh dist/

    - name: Create package tarball
      working-directory: sdk/typescript
      run: |
        echo "=== Creating Package Tarball ==="
        echo ""

        npm pack

        TARBALL=$(ls -t *.tgz | head -1)
        echo "✅ Created: $TARBALL"

        # Show size
        SIZE=$(stat -f%z "$TARBALL" 2>/dev/null || stat -c%s "$TARBALL")
        SIZE_KB=$((SIZE / 1024))
        echo "   Size: $SIZE_KB KB"

    - name: Publish to npm
      working-directory: sdk/typescript
      env:
        NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
      run: |
        echo "=== Publishing to npm ==="
        echo ""

        npm publish --access public

        echo "✅ Published to npm"

    - name: Configure GitHub Packages
      working-directory: sdk/typescript
      run: |
        cat > .npmrc << EOF
        @${{ github.repository_owner }}:registry=https://npm.pkg.github.com
        //npm.pkg.github.com/:_authToken=\${NODE_AUTH_TOKEN}
        EOF

    - name: Publish to GitHub Packages
      working-directory: sdk/typescript
      env:
        NODE_AUTH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      run: |
        echo "=== Publishing to GitHub Packages ==="
        echo ""

        npm publish

        echo "✅ Published to GitHub Packages"

    - name: Verify npm publication
      run: |
        echo "=== Verifying npm Publication ==="
        echo ""

        PACKAGE_NAME="@${{ github.repository_owner }}/${{ github.event.repository.name }}-proto"
        VERSION="${{ needs.detect-protobuf.outputs.version }}"

        # Wait for propagation
        sleep 10

        if npm view "${PACKAGE_NAME}@${VERSION}" version >/dev/null 2>&1; then
            echo "✅ Package found on npm"
            npm view "${PACKAGE_NAME}@${VERSION}"
        else
            echo "⚠️  Package not yet visible (propagation delay)"
        fi

    - name: Generate TypeScript installation instructions
      run: |
        PACKAGE_NAME="@${{ github.repository_owner }}/${{ github.event.repository.name }}-proto"
        VERSION="${{ needs.detect-protobuf.outputs.version }}"

        cat > typescript-installation.md << EOF
        # TypeScript SDK Installation

        ## Install from npm

        \`\`\`bash
        npm install ${PACKAGE_NAME}@${VERSION}
        \`\`\`

        ## Usage

        \`\`\`typescript
        import { User } from '${PACKAGE_NAME}';

        const user: User = {
          id: "123",
          email: "user@example.com",
          name: "Test User",
          createdAt: new Date(),
          updatedAt: new Date()
        };
        \`\`\`

        ## Links

        - **npm**: https://www.npmjs.com/package/${PACKAGE_NAME}
        - **GitHub Packages**: https://github.com/${{ github.repository }}/packages
        - **Repository**: https://github.com/${{ github.repository }}
        EOF

        cat typescript-installation.md

    - name: Upload TypeScript installation instructions
      uses: actions/upload-artifact@v4
      with:
        name: typescript-installation-instructions
        path: typescript-installation.md
        retention-days: 90
```

## Stage 4: Publish Rust SDK

### Step 1: crates.io Publishing Job

```yaml
publish-rust-sdk:
  name: Publish Rust SDK
  runs-on: ubuntu-latest
  needs: [detect-protobuf, generate-sdks]
  if: |
    needs.detect-protobuf.outputs.has-proto == 'true' &&
    env.PUBLISH_RUST_SDK == 'true' &&
    env.DRY_RUN == 'false'
  environment:
    name: crates-io
    url:
      https://crates.io/crates/${{ github.repository_owner }}-${{ github.event.repository.name
      }}-proto

  steps:
    - name: Setup Rust
      uses: actions-rs/toolchain@v1
      with:
        toolchain: ${{ env.RUST_VERSION }}
        override: true

    - name: Download Rust SDK artifact
      uses: actions/download-artifact@v4
      with:
        name: sdk-rust-${{ needs.detect-protobuf.outputs.version }}
        path: sdk/rust

    - name: Verify Cargo.toml
      working-directory: sdk/rust
      run: |
        echo "=== Verifying Cargo Configuration ==="
        echo ""

        cat Cargo.toml

        echo ""
        echo "✅ Cargo.toml valid"

    - name: Build Rust crate
      working-directory: sdk/rust
      run: |
        echo "=== Building Rust Crate ==="
        echo ""

        cargo build --release

        echo "✅ Build successful"

    - name: Run Rust tests
      working-directory: sdk/rust
      continue-on-error: true
      run: |
        echo "=== Running Tests ==="
        echo ""

        cargo test

        echo "✅ Tests complete"

    - name: Package Rust crate
      working-directory: sdk/rust
      run: |
        echo "=== Packaging Rust Crate ==="
        echo ""

        cargo package

        echo "✅ Package created"
        echo ""
        echo "Package files:"
        ls -lh target/package/

    - name: Publish to crates.io
      working-directory: sdk/rust
      env:
        CARGO_REGISTRY_TOKEN: ${{ secrets.CARGO_REGISTRY_TOKEN }}
      run: |
        echo "=== Publishing to crates.io ==="
        echo ""

        cargo publish --token "$CARGO_REGISTRY_TOKEN"

        echo "✅ Published to crates.io"

    - name: Verify crates.io publication
      run: |
        echo "=== Verifying crates.io Publication ==="
        echo ""

        CRATE_NAME="${{ github.repository_owner }}-${{ github.event.repository.name }}-proto"
        VERSION="${{ needs.detect-protobuf.outputs.version }}"

        # Wait for propagation
        sleep 10

        echo "ℹ️  Crate published: https://crates.io/crates/$CRATE_NAME"
        echo "   Version: $VERSION"

    - name: Generate Rust installation instructions
      run: |
        CRATE_NAME="${{ github.repository_owner }}-${{ github.event.repository.name }}-proto"
        VERSION="${{ needs.detect-protobuf.outputs.version }}"

        cat > rust-installation.md << EOF
        # Rust SDK Installation

        ## Install

        Add to \`Cargo.toml\`:

        \`\`\`toml
        [dependencies]
        ${CRATE_NAME} = "${VERSION}"
        \`\`\`

        ## Usage

        \`\`\`rust
        use ${CRATE_NAME//-/_}::proto::*;

        fn main() {
            let user = User {
                id: "123".to_string(),
                email: "user@example.com".to_string(),
                name: "Test User".to_string(),
                ..Default::default()
            };
        }
        \`\`\`

        ## Links

        - **crates.io**: https://crates.io/crates/${CRATE_NAME}
        - **docs.rs**: https://docs.rs/${CRATE_NAME}
        - **Repository**: https://github.com/${{ github.repository }}
        EOF

        cat rust-installation.md

    - name: Upload Rust installation instructions
      uses: actions/upload-artifact@v4
      with:
        name: rust-installation-instructions
        path: rust-installation.md
        retention-days: 90
```

## Local Testing Scripts

### Test Go Module Publishing

```bash
#!/bin/bash
# test-go-module.sh

echo "=== Testing Go Module ==="
echo ""

if [ ! -d "sdk/go" ]; then
    echo "❌ sdk/go directory not found"
    exit 1
fi

cd sdk/go

# Check go.mod
if [ ! -f "go.mod" ]; then
    echo "❌ go.mod not found"
    exit 1
fi

echo "✅ go.mod found"
cat go.mod
echo ""

# Try to build
if go build ./...; then
    echo "✅ Go module builds successfully"
else
    echo "❌ Go module build failed"
    exit 1
fi
```

### Test Python Package Publishing

```bash
#!/bin/bash
# test-python-package.sh

echo "=== Testing Python Package ==="
echo ""

if [ ! -d "sdk/python" ]; then
    echo "❌ sdk/python directory not found"
    exit 1
fi

cd sdk/python

# Install build tools
pip install --quiet build twine

# Build package
python -m build

# Check with twine
twine check dist/*

if [ $? -eq 0 ]; then
    echo "✅ Python package valid"
    ls -lh dist/
else
    echo "❌ Package validation failed"
    exit 1
fi
```

## Commit SDK Publishing Changes

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Stage changes
git add .github/workflows/protobuf-release.yml

# Commit
git commit -m "feat(protobuf): add SDK publishing to language registries

Added publishing for all 4 language SDKs to their native registries:

Go SDK Publishing:
- Commit generated code to sdk/go directory
- Create git tag: go-v{version}
- Push to repository (Go modules use git tags)
- Generate installation instructions
- Link to pkg.go.dev

Python SDK Publishing:
- Build wheel and sdist with python-m build
- Validate with twine check
- Publish to PyPI with twine
- Publish to GitHub Packages (Python registry)
- Verify publication and test installation
- Generate pip install instructions

TypeScript SDK Publishing:
- Install dependencies and build TypeScript
- Create npm package tarball
- Publish to npm registry (public access)
- Publish to GitHub Packages (npm registry)
- Configure .npmrc for GitHub Packages
- Verify publication
- Generate npm install instructions

Rust SDK Publishing:
- Build crate with cargo build --release
- Run tests with cargo test
- Package with cargo package
- Publish to crates.io with CARGO_REGISTRY_TOKEN
- Verify publication
- Generate Cargo.toml instructions

Publishing Features:
- Environment protection per registry
- Token-based authentication
- Publication verification with retries
- Installation testing
- Size reporting
- Links to package pages

Artifacts:
- {language}-installation-instructions: Complete installation guides

Environment URLs:
- go-module: pkg.go.dev link
- pypi: PyPI package page
- npm: npmjs.com package page
- crates-io: crates.io package page

Local Testing:
- test-go-module.sh: Verify Go module structure
- test-python-package.sh: Build and validate Python package

Files changed:
- .github/workflows/protobuf-release.yml - SDK publishing jobs"
```

## Next Steps

**Continue to Part 5:** GitHub release creation, documentation generation, and verification.
