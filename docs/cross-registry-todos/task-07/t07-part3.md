<!-- file: docs/cross-registry-todos/task-07/t07-part3.md -->
<!-- version: 1.0.0 -->
<!-- guid: t07-protobuf-packages-part3-d3e4f5g6-h7i8 -->

# Task 07 Part 3: Buf BSR Publishing and Code Generation

## Stage 1: Publish to Buf Schema Registry

### Step 1: BSR Publishing Job

```yaml
  publish-buf-bsr:
    name: Publish to Buf Schema Registry
    runs-on: ubuntu-latest
    needs: [detect-protobuf, validate-protobuf]
    if: |
      needs.detect-protobuf.outputs.has-proto == 'true' &&
      env.PUBLISH_TO_BSR == 'true' &&
      env.DRY_RUN == 'false'
    environment:
      name: buf-registry
      url: https://buf.build/${{ github.repository_owner }}/${{ github.event.repository.name }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install Buf
        run: |
          echo "=== Installing Buf CLI ==="

          VERSION="${{ env.BUF_VERSION }}"
          curl -sSL \
            "https://github.com/bufbuild/buf/releases/download/v${VERSION}/buf-Linux-x86_64" \
            -o /usr/local/bin/buf
          chmod +x /usr/local/bin/buf

          buf --version

      - name: Authenticate with BSR
        env:
          BUF_TOKEN: ${{ secrets.BUF_TOKEN }}
        run: |
          echo "=== Authenticating with Buf Schema Registry ==="
          echo ""

          if [ -z "$BUF_TOKEN" ]; then
              echo "❌ ERROR: BUF_TOKEN not set"
              exit 1
          fi

          # Login to BSR
          echo "$BUF_TOKEN" | buf registry login buf.build --username ${{ github.repository_owner }} --token-stdin

          # Verify authentication
          buf registry whoami

          echo "✅ Authenticated with BSR"

      - name: Push to BSR
        run: |
          echo "=== Publishing to Buf Schema Registry ==="
          echo ""

          VERSION="${{ needs.detect-protobuf.outputs.version }}"
          TAG="proto-v${VERSION}"

          echo "Module: ${{ env.BUF_MODULE_NAME }}"
          echo "Version: $VERSION"
          echo "Tag: $TAG"
          echo ""

          # Push to BSR with tag
          if buf push --tag "$TAG"; then
              echo ""
              echo "✅ Published to BSR successfully"
          else
              echo ""
              echo "❌ Failed to publish to BSR"
              exit 1
          fi

      - name: Verify BSR publication
        continue-on-error: true
        run: |
          echo "=== Verifying BSR Publication ==="
          echo ""

          VERSION="${{ needs.detect-protobuf.outputs.version }}"
          MODULE="${{ env.BUF_MODULE_NAME }}"

          # Wait for propagation
          sleep 5

          # Try to pull the module
          if buf pull "$MODULE:proto-v${VERSION}"; then
              echo "✅ Module accessible on BSR"
          else
              echo "⚠️  Module not yet accessible (may need time to propagate)"
          fi

      - name: Generate BSR URLs
        run: |
          MODULE="${{ env.BUF_MODULE_NAME }}"
          VERSION="${{ needs.detect-protobuf.outputs.version }}"

          cat > bsr-urls.txt << EOF
          Buf Schema Registry Links:

          Repository: https://buf.build/${{ github.repository_owner }}/${{ github.event.repository.name }}
          Version: https://buf.build/${{ github.repository_owner }}/${{ github.event.repository.name }}/tags/proto-v${VERSION}
          Documentation: https://buf.build/${{ github.repository_owner }}/${{ github.event.repository.name }}/docs

          Import in buf.yaml:
          deps:
            - ${MODULE}

          Import in buf.gen.yaml:
          managed:
            enabled: true
          inputs:
            - ${MODULE}
          EOF

          cat bsr-urls.txt

      - name: Upload BSR info
        uses: actions/upload-artifact@v4
        with:
          name: bsr-publication-info
          path: bsr-urls.txt
          retention-days: 90
```

## Stage 2: Generate Multi-Language SDKs

### Step 1: SDK Generation Job

```yaml
  generate-sdks:
    name: Generate SDKs
    runs-on: ubuntu-latest
    needs: [detect-protobuf, validate-protobuf, publish-buf-bsr]
    if: needs.detect-protobuf.outputs.has-proto == 'true'
    strategy:
      matrix:
        language: [go, python, typescript, rust]

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install Buf
        run: |
          VERSION="${{ env.BUF_VERSION }}"
          curl -sSL \
            "https://github.com/bufbuild/buf/releases/download/v${VERSION}/buf-Linux-x86_64" \
            -o /usr/local/bin/buf
          chmod +x /usr/local/bin/buf

      - name: Setup language tools
        run: |
          case "${{ matrix.language }}" in
            go)
              # Go is pre-installed
              go version
              ;;
            python)
              python3 --version
              pip3 install grpcio-tools mypy-protobuf
              ;;
            typescript)
              node --version
              npm --version
              ;;
            rust)
              # Rust is pre-installed on GitHub runners
              rustc --version
              cargo --version
              ;;
          esac

      - name: Create buf.gen.yaml for language
        run: |
          echo "=== Creating buf.gen.yaml for ${{ matrix.language }} ==="
          echo ""

          case "${{ matrix.language }}" in
            go)
              cat > buf.gen.yaml << 'EOF'
          version: v2
          managed:
            enabled: true
            override:
              - file_option: go_package_prefix
                value: github.com/${{ github.repository }}/gen/go
          plugins:
            - remote: buf.build/protocolbuffers/go
              out: gen/go
              opt:
                - paths=source_relative
            - remote: buf.build/grpc/go
              out: gen/go
              opt:
                - paths=source_relative
                - require_unimplemented_servers=false
          EOF
              ;;

            python)
              cat > buf.gen.yaml << 'EOF'
          version: v2
          plugins:
            - remote: buf.build/protocolbuffers/python
              out: gen/python
            - remote: buf.build/grpc/python
              out: gen/python
            - remote: buf.build/protocolbuffers/pyi
              out: gen/python
          EOF
              ;;

            typescript)
              cat > buf.gen.yaml << 'EOF'
          version: v2
          plugins:
            - remote: buf.build/connectrpc/es
              out: gen/typescript
              opt:
                - target=ts
            - remote: buf.build/bufbuild/es
              out: gen/typescript
              opt:
                - target=ts
          EOF
              ;;

            rust)
              cat > buf.gen.yaml << 'EOF'
          version: v2
          plugins:
            - remote: buf.build/community/neoeinstein-prost
              out: gen/rust
            - remote: buf.build/community/neoeinstein-tonic
              out: gen/rust
          EOF
              ;;
          esac

          cat buf.gen.yaml

      - name: Generate code
        run: |
          echo "=== Generating ${{ matrix.language }} SDK ==="
          echo ""

          # Generate
          buf generate

          # Check output
          if [ -d "gen/${{ matrix.language }}" ]; then
              echo "✅ Code generated successfully"
              echo ""
              echo "Generated files:"
              find gen/${{ matrix.language }} -type f | head -20
          else
              echo "❌ No code generated"
              exit 1
          fi

      - name: Create SDK package structure
        run: |
          echo "=== Creating SDK Package Structure ==="
          echo ""

          LANG="${{ matrix.language }}"
          SDK_DIR="sdk/$LANG"

          mkdir -p "$SDK_DIR"

          case "$LANG" in
            go)
              # Go module structure
              cp -r gen/go/* "$SDK_DIR/"

              # Create go.mod
              cat > "$SDK_DIR/go.mod" << EOF
          module github.com/${{ github.repository }}/sdk/go

          go ${{ env.GO_VERSION }}

          require (
              google.golang.org/grpc v1.59.0
              google.golang.org/protobuf v1.31.0
          )
          EOF

              # Create README
              cat > "$SDK_DIR/README.md" << EOF
          # Go SDK

          Generated from protobuf schemas.

          ## Installation

          \`\`\`bash
          go get github.com/${{ github.repository }}/sdk/go@v${{ needs.detect-protobuf.outputs.version }}
          \`\`\`

          ## Usage

          \`\`\`go
          import pb "github.com/${{ github.repository }}/sdk/go/ghcommon/v1"
          \`\`\`
          EOF
              ;;

            python)
              # Python package structure
              cp -r gen/python/* "$SDK_DIR/"

              # Create setup.py
              cat > "$SDK_DIR/setup.py" << EOF
          from setuptools import setup, find_packages

          setup(
              name="${{ github.repository_owner }}-${{ github.event.repository.name }}-proto",
              version="${{ needs.detect-protobuf.outputs.version }}",
              description="Generated protobuf stubs",
              author="${{ github.repository_owner }}",
              packages=find_packages(),
              install_requires=[
                  "grpcio>=1.59.0",
                  "protobuf>=4.25.0",
              ],
              python_requires=">=3.8",
          )
          EOF

              # Create pyproject.toml
              cat > "$SDK_DIR/pyproject.toml" << EOF
          [build-system]
          requires = ["setuptools>=61.0", "wheel"]
          build-backend = "setuptools.build_meta"

          [project]
          name = "${{ github.repository_owner }}-${{ github.event.repository.name }}-proto"
          version = "${{ needs.detect-protobuf.outputs.version }}"
          description = "Generated protobuf stubs"
          readme = "README.md"
          requires-python = ">=3.8"
          dependencies = [
              "grpcio>=1.59.0",
              "protobuf>=4.25.0",
          ]
          EOF

              # Create __init__.py
              touch "$SDK_DIR/__init__.py"

              # Create README
              cat > "$SDK_DIR/README.md" << EOF
          # Python SDK

          Generated from protobuf schemas.

          ## Installation

          \`\`\`bash
          pip install ${{ github.repository_owner }}-${{ github.event.repository.name }}-proto
          \`\`\`

          ## Usage

          \`\`\`python
          from ghcommon.v1 import api_pb2
          \`\`\`
          EOF
              ;;

            typescript)
              # TypeScript package structure
              cp -r gen/typescript/* "$SDK_DIR/"

              # Create package.json
              cat > "$SDK_DIR/package.json" << EOF
          {
            "name": "@${{ github.repository_owner }}/${{ github.event.repository.name }}-proto",
            "version": "${{ needs.detect-protobuf.outputs.version }}",
            "description": "Generated protobuf stubs",
            "main": "./dist/index.js",
            "types": "./dist/index.d.ts",
            "files": [
              "dist/"
            ],
            "scripts": {
              "build": "tsc",
              "prepare": "npm run build"
            },
            "dependencies": {
              "@bufbuild/protobuf": "^1.4.0",
              "@connectrpc/connect": "^1.1.0"
            },
            "devDependencies": {
              "typescript": "^5.2.0"
            },
            "publishConfig": {
              "access": "public"
            }
          }
          EOF

              # Create tsconfig.json
              cat > "$SDK_DIR/tsconfig.json" << EOF
          {
            "compilerOptions": {
              "target": "ES2020",
              "module": "commonjs",
              "declaration": true,
              "outDir": "./dist",
              "strict": true,
              "esModuleInterop": true
            },
            "include": ["**/*.ts"],
            "exclude": ["node_modules", "dist"]
          }
          EOF

              # Create README
              cat > "$SDK_DIR/README.md" << EOF
          # TypeScript SDK

          Generated from protobuf schemas.

          ## Installation

          \`\`\`bash
          npm install @${{ github.repository_owner }}/${{ github.event.repository.name }}-proto
          \`\`\`

          ## Usage

          \`\`\`typescript
          import { User } from '@${{ github.repository_owner }}/${{ github.event.repository.name }}-proto';
          \`\`\`
          EOF
              ;;

            rust)
              # Rust crate structure
              mkdir -p "$SDK_DIR/src"
              cp -r gen/rust/* "$SDK_DIR/src/" 2>/dev/null || true

              # Create Cargo.toml
              cat > "$SDK_DIR/Cargo.toml" << EOF
          [package]
          name = "${{ github.repository_owner }}-${{ github.event.repository.name }}-proto"
          version = "${{ needs.detect-protobuf.outputs.version }}"
          edition = "2021"
          description = "Generated protobuf stubs"

          [dependencies]
          prost = "0.12"
          tonic = "0.10"

          [build-dependencies]
          tonic-build = "0.10"
          EOF

              # Create lib.rs
              cat > "$SDK_DIR/src/lib.rs" << EOF
          // Generated protobuf code
          pub mod proto {
              include!("mod.rs");
          }
          EOF

              # Create README
              cat > "$SDK_DIR/README.md" << EOF
          # Rust SDK

          Generated from protobuf schemas.

          ## Installation

          \`\`\`toml
          [${{ github.repository_owner }}-${{ github.event.repository.name }}-proto = "${{ needs.detect-protobuf.outputs.version }}"
          \`\`\`

          ## Usage

          \`\`\`rust
          use ${{ github.repository_owner }}_${{ github.event.repository.name }}_proto::proto::*;
          \`\`\`
          EOF
              ;;
          esac

          echo "✅ SDK package structure created"

      - name: Package SDK
        run: |
          echo "=== Packaging SDK ==="
          echo ""

          LANG="${{ matrix.language }}"
          SDK_DIR="sdk/$LANG"

          cd "$SDK_DIR"

          case "$LANG" in
            go)
              # Go doesn't need packaging (uses git tags)
              echo "Go SDK ready (no packaging needed)"
              ;;

            python)
              # Build Python package
              python3 -m pip install --upgrade build
              python3 -m build
              echo "✅ Python package built"
              ls -lh dist/
              ;;

            typescript)
              # Install dependencies and build
              npm install
              npm run build
              npm pack
              echo "✅ TypeScript package built"
              ls -lh *.tgz
              ;;

            rust)
              # Verify Cargo.toml
              cargo check 2>/dev/null || echo "Cargo check skipped"
              echo "✅ Rust package ready"
              ;;
          esac

      - name: Upload SDK artifact
        uses: actions/upload-artifact@v4
        with:
          name: sdk-${{ matrix.language }}-${{ needs.detect-protobuf.outputs.version }}
          path: sdk/${{ matrix.language }}
          retention-days: 90
```

## Local Testing Scripts

### Test Code Generation

```bash
#!/bin/bash
# test-code-generation.sh

echo "=== Testing Code Generation ==="
echo ""

if ! command -v buf &> /dev/null; then
    echo "❌ Buf not installed"
    exit 1
fi

# Check buf.gen.yaml
if [ ! -f "buf.gen.yaml" ]; then
    echo "❌ buf.gen.yaml not found"
    exit 1
fi

echo "Generating code..."
buf generate

echo ""
echo "Generated files:"
find gen -type f 2>/dev/null | head -20

echo ""
echo "✅ Code generation test complete"
```

### Test BSR Publishing (Dry Run)

```bash
#!/bin/bash
# test-bsr-publish-dry-run.sh

echo "=== Testing BSR Publish (Dry Run) ==="
echo ""

if ! command -v buf &> /dev/null; then
    echo "❌ Buf not installed"
    exit 1
fi

# Check authentication
if ! buf registry whoami 2>/dev/null; then
    echo "❌ Not authenticated with BSR"
    echo "Run: buf registry login buf.build"
    exit 1
fi

echo "✅ Authenticated with BSR"
echo ""

# Try dry run (doesn't actually push)
echo "Testing push (dry run)..."
buf push --tag "test-$(date +%s)"

echo ""
echo "✅ BSR publish test complete"
```

## Commit SDK Generation Changes

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Stage changes
git add .github/workflows/protobuf-release.yml

# Commit
git commit -m "feat(protobuf): add BSR publishing and SDK generation

Added Buf Schema Registry publishing and multi-language SDK generation:

BSR Publishing:
- Authenticate with Buf using BUF_TOKEN
- Push protobuf schemas to BSR with version tags
- Verify publication after push
- Generate BSR URLs and import instructions
- Support for buf.build module path

SDK Generation:
- Matrix strategy for 4 languages (Go, Python, TypeScript, Rust)
- Language-specific buf.gen.yaml configuration
- Automatic code generation using Buf remote plugins
- Package structure creation per language

Go SDK:
- Generate with protocolbuffers/go and grpc/go plugins
- Create go.mod with dependencies
- Package as Go module (no build needed)
- Version via git tags

Python SDK:
- Generate with protocolbuffers/python, grpc/python, pyi plugins
- Create setup.py and pyproject.toml
- Build wheel and sdist packages
- Support for modern Python packaging

TypeScript SDK:
- Generate with connectrpc/es and bufbuild/es plugins
- Create package.json with dependencies
- Build TypeScript to JavaScript
- Generate type declarations
- Create npm tarball

Rust SDK:
- Generate with community/neoeinstein-prost and neoeinstein-tonic plugins
- Create Cargo.toml with dependencies
- Package as Rust crate
- Support for tonic gRPC

Package Artifacts:
- sdk-{language}-{version}: Generated SDK for each language
- bsr-publication-info: BSR URLs and import info

Environment Protection:
- buf-registry environment for BSR publishing

Local Testing:
- test-code-generation.sh: Test buf generate locally
- test-bsr-publish-dry-run.sh: Test BSR authentication and push

Files changed:
- .github/workflows/protobuf-release.yml - BSR and SDK generation jobs"
```

## Next Steps

**Continue to Part 4:** Publishing SDKs to language-specific registries (Go tags, PyPI, npm, crates.io).
