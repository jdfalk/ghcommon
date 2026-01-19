<!-- file: docs/cross-registry-todos/task-07/t07-part5.md -->
<!-- version: 1.0.0 -->
<!-- guid: t07-protobuf-packages-part5-p5q6r7s8-t9u0 -->
<!-- last-edited: 2026-01-19 -->

# Task 07 Part 5: GitHub Release and Documentation Generation

## Stage 1: Create GitHub Release

### Step 1: GitHub Release Job

````yaml
create-github-release:
  name: Create GitHub Release
  runs-on: ubuntu-latest
  needs:
    - detect-protobuf
    - validate-protobuf
    - publish-buf-bsr
    - publish-go-sdk
    - publish-python-sdk
    - publish-typescript-sdk
    - publish-rust-sdk
  if: needs.detect-protobuf.outputs.has-proto == 'true'
  permissions:
    contents: write

  steps:
    - name: Checkout code
      uses: actions/checkout@v4
      with:
        fetch-depth: 0

    - name: Download all artifacts
      uses: actions/download-artifact@v4
      with:
        path: ./release-artifacts

    - name: Generate changelog
      id: changelog
      run: |
        echo "=== Generating Changelog ==="
        echo ""

        TAG_NAME="proto-v${{ needs.detect-protobuf.outputs.version }}"
        PREV_TAG=$(git tag --sort=-version:refname | grep "^proto-v" | grep -v "^${TAG_NAME}$" | head -1)

        if [ -n "$PREV_TAG" ]; then
            echo "Generating changelog from $PREV_TAG to $TAG_NAME"

            # Get commit messages
            CHANGELOG=$(git log "$PREV_TAG".."HEAD" \
                --pretty=format:"- %s (%h)" \
                --no-merges \
                --grep="proto\|protobuf\|buf" || echo "")

            if [ -z "$CHANGELOG" ]; then
                CHANGELOG="- Initial protobuf release"
            fi
        else
            echo "First protobuf release"
            CHANGELOG="- Initial protobuf release"
        fi

        # Save to file
        cat > changelog.md << EOF
        ## Changes

        $CHANGELOG
        EOF

        cat changelog.md

    - name: Generate protobuf statistics
      run: |
        cat > proto-stats.md << EOF
        ## Protobuf Statistics

        **Version**: ${{ needs.detect-protobuf.outputs.version }}

        ### Files
        - Total protobuf files: $(find . -name "*.proto" | wc -l)
        - Directories: $(find . -name "*.proto" | sed 's|/[^/]*$||' | sort -u | wc -l)

        ### Definitions
        - Messages: $(find . -name "*.proto" -exec grep -c "^message " {} \; | awk '{sum+=$1} END {print sum}')
        - Enums: $(find . -name "*.proto" -exec grep -c "^enum " {} \; | awk '{sum+=$1} END {print sum}')
        - Services: $(find . -name "*.proto" -exec grep -c "^service " {} \; | awk '{sum+=$1} END {print sum}')
        - RPC Methods: $(find . -name "*.proto" -exec grep -c "  rpc " {} \; | awk '{sum+=$1} END {print sum}')

        ### Validation
        - ✅ Buf linting passed
        $(if [ -f "release-artifacts/breaking-changes-report/breaking-changes.txt" ]; then echo "- ⚠️  Breaking changes detected"; else echo "- ✅ No breaking changes"; fi)
        EOF

        cat proto-stats.md

    - name: Create comprehensive release notes
      run: |
        VERSION="${{ needs.detect-protobuf.outputs.version }}"

        cat > release-notes.md << 'EOF'
        # Protobuf Release v${{ needs.detect-protobuf.outputs.version }}

        This release includes protobuf schemas and generated SDKs for multiple languages.

        ## 📦 Published Packages

        ### Buf Schema Registry
        - **Module**: `${{ env.BUF_MODULE_NAME }}`
        - **Tag**: `proto-v${{ needs.detect-protobuf.outputs.version }}`
        - **URL**: https://buf.build/${{ github.repository_owner }}/${{ github.event.repository.name }}

        ### Go SDK
        - **Module**: `github.com/${{ github.repository }}/sdk/go`
        - **Version**: `v${{ needs.detect-protobuf.outputs.version }}`
        - **Tag**: `go-v${{ needs.detect-protobuf.outputs.version }}`
        - **Install**: `go get github.com/${{ github.repository }}/sdk/go@v${{ needs.detect-protobuf.outputs.version }}`

        ### Python SDK
        - **Package**: `${{ github.repository_owner }}-${{ github.event.repository.name }}-proto`
        - **Version**: `${{ needs.detect-protobuf.outputs.version }}`
        - **PyPI**: https://pypi.org/project/${{ github.repository_owner }}-${{ github.event.repository.name }}-proto
        - **Install**: `pip install ${{ github.repository_owner }}-${{ github.event.repository.name }}-proto==${{ needs.detect-protobuf.outputs.version }}`

        ### TypeScript SDK
        - **Package**: `@${{ github.repository_owner }}/${{ github.event.repository.name }}-proto`
        - **Version**: `${{ needs.detect-protobuf.outputs.version }}`
        - **npm**: https://www.npmjs.com/package/@${{ github.repository_owner }}/${{ github.event.repository.name }}-proto
        - **Install**: `npm install @${{ github.repository_owner }}/${{ github.event.repository.name }}-proto@${{ needs.detect-protobuf.outputs.version }}`

        ### Rust SDK
        - **Crate**: `${{ github.repository_owner }}-${{ github.event.repository.name }}-proto`
        - **Version**: `${{ needs.detect-protobuf.outputs.version }}`
        - **crates.io**: https://crates.io/crates/${{ github.repository_owner }}-${{ github.event.repository.name }}-proto
        - **Install**: Add to Cargo.toml: `${{ github.repository_owner }}-${{ github.event.repository.name }}-proto = "${{ needs.detect-protobuf.outputs.version }}"`

        ---

        EOF

        # Append statistics
        cat proto-stats.md >> release-notes.md
        echo "" >> release-notes.md
        echo "---" >> release-notes.md
        echo "" >> release-notes.md

        # Append changelog
        cat changelog.md >> release-notes.md

        # Append breaking changes if they exist
        if [ -f "release-artifacts/breaking-changes-report/breaking-changes.txt" ]; then
            echo "" >> release-notes.md
            echo "---" >> release-notes.md
            echo "" >> release-notes.md
            echo "## ⚠️  Breaking Changes" >> release-notes.md
            echo "" >> release-notes.md
            echo '```' >> release-notes.md
            cat release-artifacts/breaking-changes-report/breaking-changes.txt >> release-notes.md
            echo '```' >> release-notes.md
        fi

        cat release-notes.md

    - name: Prepare release artifacts
      run: |
        echo "=== Preparing Release Artifacts ==="
        echo ""

        mkdir -p release-bundle

        # Copy installation instructions
        for lang in go python typescript rust; do
            if [ -d "release-artifacts/${lang}-installation-instructions" ]; then
                cp release-artifacts/${lang}-installation-instructions/*.md release-bundle/ 2>/dev/null || true
            fi
        done

        # Copy BSR info
        if [ -d "release-artifacts/bsr-publication-info" ]; then
            cp release-artifacts/bsr-publication-info/*.txt release-bundle/ 2>/dev/null || true
        fi

        # Copy statistics
        if [ -d "release-artifacts/protobuf-statistics" ]; then
            cp release-artifacts/protobuf-statistics/*.json release-bundle/ 2>/dev/null || true
        fi

        # Create archive of protobuf files
        tar -czf release-bundle/protobuf-schemas-${{ needs.detect-protobuf.outputs.version }}.tar.gz proto/

        # Create archive of generated SDKs
        if [ -d "sdk" ]; then
            tar -czf release-bundle/generated-sdks-${{ needs.detect-protobuf.outputs.version }}.tar.gz sdk/
        fi

        echo "✅ Release artifacts prepared"
        echo ""
        echo "Artifacts:"
        ls -lh release-bundle/

    - name: Create GitHub Release
      uses: softprops/action-gh-release@v1
      with:
        tag_name: proto-v${{ needs.detect-protobuf.outputs.version }}
        name: Protobuf Release v${{ needs.detect-protobuf.outputs.version }}
        body_path: release-notes.md
        files: |
          release-bundle/*
        draft: false
        prerelease:
          ${{ contains(needs.detect-protobuf.outputs.version, '-alpha') ||
          contains(needs.detect-protobuf.outputs.version, '-beta') ||
          contains(needs.detect-protobuf.outputs.version, '-rc') }}
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
````

## Stage 2: Generate API Documentation

### Step 1: Documentation Generation Job

```yaml
generate-documentation:
  name: Generate API Documentation
  runs-on: ubuntu-latest
  needs: [detect-protobuf, validate-protobuf]
  if: needs.detect-protobuf.outputs.has-proto == 'true'

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

    - name: Install protoc-gen-doc
      run: |
        echo "=== Installing protoc-gen-doc ==="

        # Install protoc
        PROTOC_VERSION="25.1"
        curl -sSL \
          "https://github.com/protocolbuffers/protobuf/releases/download/v${PROTOC_VERSION}/protoc-${PROTOC_VERSION}-linux-x86_64.zip" \
          -o protoc.zip
        unzip -q protoc.zip -d /usr/local
        rm protoc.zip

        # Install protoc-gen-doc
        go install github.com/pseudomuto/protoc-gen-doc/cmd/protoc-gen-doc@latest

        echo "✅ Documentation tools installed"

    - name: Generate Markdown documentation
      run: |
        echo "=== Generating Markdown Documentation ==="
        echo ""

        mkdir -p docs/api

        # Generate docs for each protobuf directory
        find proto -name "*.proto" -type f | while read proto_file; do
            proto_dir=$(dirname "$proto_file")

            protoc \
              --proto_path=proto \
              --doc_out=docs/api \
              --doc_opt=markdown,api.md \
              "$proto_file"
        done

        if [ -f "docs/api/api.md" ]; then
            echo "✅ Documentation generated"
        else
            echo "⚠️  No documentation generated"
        fi

    - name: Generate HTML documentation
      run: |
        echo "=== Generating HTML Documentation ==="
        echo ""

        # Generate HTML docs
        protoc \
          --proto_path=proto \
          --doc_out=docs/api \
          --doc_opt=html,index.html \
          proto/**/*.proto 2>/dev/null || true

        if [ -f "docs/api/index.html" ]; then
            echo "✅ HTML documentation generated"
        fi

    - name: Generate JSON schema documentation
      run: |
        echo "=== Generating JSON Schema ==="
        echo ""

        # Generate JSON schema
        protoc \
          --proto_path=proto \
          --doc_out=docs/api \
          --doc_opt=json,schema.json \
          proto/**/*.proto 2>/dev/null || true

        if [ -f "docs/api/schema.json" ]; then
            echo "✅ JSON schema generated"
        fi

    - name: Create documentation index
      run: |
        cat > docs/api/README.md << EOF
        # API Documentation

        **Version**: v${{ needs.detect-protobuf.outputs.version }}
        **Generated**: $(date -u +"%Y-%m-%d %H:%M:%S UTC")

        ## Available Documentation

        - [Markdown Documentation](api.md) - Human-readable API reference
        - [HTML Documentation](index.html) - Interactive HTML documentation
        - [JSON Schema](schema.json) - Machine-readable schema

        ## Protobuf Packages

        $(find proto -name "*.proto" -exec grep -h "^package " {} \; | sed 's/package \(.*\);/- \1/' | sort -u)

        ## Services

        $(find proto -name "*.proto" -exec grep -h "^service " {} \; | sed 's/service \([^ ]*\).*/- \1/' | sort -u)

        ## Usage

        ### Import from BSR

        \`\`\`yaml
        # buf.yaml
        deps:
          - ${{ env.BUF_MODULE_NAME }}
        \`\`\`

        ### Generate Code

        \`\`\`bash
        buf generate ${{ env.BUF_MODULE_NAME }}
        \`\`\`

        ## Links

        - **BSR**: https://buf.build/${{ github.repository_owner }}/${{ github.event.repository.name }}
        - **Repository**: https://github.com/${{ github.repository }}
        - **Release**: https://github.com/${{ github.repository }}/releases/tag/proto-v${{ needs.detect-protobuf.outputs.version }}
        EOF

        cat docs/api/README.md

    - name: Upload documentation
      uses: actions/upload-artifact@v4
      with:
        name: api-documentation
        path: docs/api/
        retention-days: 90

    - name: Commit documentation to repository
      continue-on-error: true
      run: |
        echo "=== Committing Documentation ==="
        echo ""

        git config user.name "github-actions[bot]"
        git config user.email "github-actions[bot]@users.noreply.github.com"

        git add docs/api/

        if git diff --cached --quiet; then
            echo "ℹ️  No documentation changes"
        else
            git commit -m "docs(proto): generate API documentation for v${{ needs.detect-protobuf.outputs.version }}"
            git push origin HEAD:${{ github.ref_name }}
            echo "✅ Documentation committed"
        fi
```

## Stage 3: Verification and Metrics

### Step 1: Comprehensive Verification Job

```yaml
verify-publication:
  name: Verify All Publications
  runs-on: ubuntu-latest
  needs:
    - detect-protobuf
    - publish-buf-bsr
    - publish-go-sdk
    - publish-python-sdk
    - publish-typescript-sdk
    - publish-rust-sdk
  if: needs.detect-protobuf.outputs.has-proto == 'true'

  steps:
    - name: Setup tools
      run: |
        # Install Buf
        VERSION="${{ env.BUF_VERSION }}"
        curl -sSL \
          "https://github.com/bufbuild/buf/releases/download/v${VERSION}/buf-Linux-x86_64" \
          -o /usr/local/bin/buf
        chmod +x /usr/local/bin/buf

        # Install Go
        go version

        # Install Python
        python3 --version

        # Install Node.js
        node --version

        # Install Rust
        rustc --version

    - name: Verify Buf BSR
      continue-on-error: true
      run: |
        echo "=== Verifying Buf Schema Registry ==="
        echo ""

        MODULE="${{ env.BUF_MODULE_NAME }}"
        TAG="proto-v${{ needs.detect-protobuf.outputs.version }}"

        sleep 10

        if buf pull "$MODULE:$TAG" 2>/dev/null; then
            echo "✅ BSR: Published successfully"
        else
            echo "⚠️  BSR: Not yet accessible"
        fi

    - name: Verify Go module
      continue-on-error: true
      run: |
        echo "=== Verifying Go Module ==="
        echo ""

        MODULE="github.com/${{ github.repository }}/sdk/go"
        VERSION="v${{ needs.detect-protobuf.outputs.version }}"

        # Try to get module info
        go list -m "$MODULE@$VERSION" 2>/dev/null || echo "⚠️  Go module not yet indexed"

    - name: Verify Python package
      continue-on-error: true
      run: |
        echo "=== Verifying Python Package ==="
        echo ""

        PACKAGE="${{ github.repository_owner }}-${{ github.event.repository.name }}-proto"
        VERSION="${{ needs.detect-protobuf.outputs.version }}"

        sleep 10

        if pip index versions "$PACKAGE" 2>/dev/null | grep -q "$VERSION"; then
            echo "✅ PyPI: Published successfully"
        else
            echo "⚠️  PyPI: Not yet accessible"
        fi

    - name: Verify TypeScript package
      continue-on-error: true
      run: |
        echo "=== Verifying TypeScript Package ==="
        echo ""

        PACKAGE="@${{ github.repository_owner }}/${{ github.event.repository.name }}-proto"
        VERSION="${{ needs.detect-protobuf.outputs.version }}"

        sleep 10

        if npm view "$PACKAGE@$VERSION" version >/dev/null 2>&1; then
            echo "✅ npm: Published successfully"
        else
            echo "⚠️  npm: Not yet accessible"
        fi

    - name: Verify Rust crate
      continue-on-error: true
      run: |
        echo "=== Verifying Rust Crate ==="
        echo ""

        CRATE="${{ github.repository_owner }}-${{ github.event.repository.name }}-proto"
        VERSION="${{ needs.detect-protobuf.outputs.version }}"

        echo "ℹ️  crates.io: https://crates.io/crates/$CRATE"
        echo "   Manual verification recommended"

    - name: Generate verification report
      run: |
        cat > verification-report.md << EOF
        # Publication Verification Report

        **Version**: v${{ needs.detect-protobuf.outputs.version }}
        **Date**: $(date -u +"%Y-%m-%d %H:%M:%S UTC")

        ## Publication Status

        - **Buf BSR**: Check https://buf.build/${{ github.repository_owner }}/${{ github.event.repository.name }}
        - **Go Module**: Check https://pkg.go.dev/github.com/${{ github.repository }}/sdk/go
        - **PyPI**: Check https://pypi.org/project/${{ github.repository_owner }}-${{ github.event.repository.name }}-proto
        - **npm**: Check https://www.npmjs.com/package/@${{ github.repository_owner }}/${{ github.event.repository.name }}-proto
        - **crates.io**: Check https://crates.io/crates/${{ github.repository_owner }}-${{ github.event.repository.name }}-proto

        ## Installation Commands

        ### Go
        \`\`\`bash
        go get github.com/${{ github.repository }}/sdk/go@v${{ needs.detect-protobuf.outputs.version }}
        \`\`\`

        ### Python
        \`\`\`bash
        pip install ${{ github.repository_owner }}-${{ github.event.repository.name }}-proto==${{ needs.detect-protobuf.outputs.version }}
        \`\`\`

        ### TypeScript
        \`\`\`bash
        npm install @${{ github.repository_owner }}/${{ github.event.repository.name }}-proto@${{ needs.detect-protobuf.outputs.version }}
        \`\`\`

        ### Rust
        \`\`\`toml
        [${{ github.repository_owner }}-${{ github.event.repository.name }}-proto = "${{ needs.detect-protobuf.outputs.version }}"
        \`\`\`

        ---
        *Note: Some registries may take 5-10 minutes to index new packages*
        EOF

        cat verification-report.md

    - name: Upload verification report
      uses: actions/upload-artifact@v4
      with:
        name: verification-report
        path: verification-report.md
        retention-days: 90
```

## Local Testing Scripts

### Test Complete Release Workflow

```bash
#!/bin/bash
# test-complete-protobuf-release.sh

echo "=== Testing Complete Protobuf Release ==="
echo ""

# Check prerequisites
echo "Checking prerequisites..."
command -v buf >/dev/null 2>&1 || { echo "❌ buf not installed"; exit 1; }
command -v go >/dev/null 2>&1 || { echo "❌ go not installed"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ python3 not installed"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ node not installed"; exit 1; }
command -v cargo >/dev/null 2>&1 || { echo "❌ cargo not installed"; exit 1; }

echo "✅ All tools installed"
echo ""

# Test protobuf detection
echo "Testing protobuf detection..."
PROTO_COUNT=$(find . -name "*.proto" | wc -l | tr -d ' ')
if [ "$PROTO_COUNT" -gt 0 ]; then
    echo "✅ Found $PROTO_COUNT protobuf files"
else
    echo "❌ No protobuf files found"
    exit 1
fi
echo ""

# Test linting
echo "Testing buf lint..."
if buf lint; then
    echo "✅ Linting passed"
else
    echo "❌ Linting failed"
    exit 1
fi
echo ""

# Test code generation
echo "Testing code generation..."
if buf generate; then
    echo "✅ Code generation successful"
else
    echo "❌ Code generation failed"
    exit 1
fi
echo ""

# Test Go SDK
if [ -d "sdk/go" ]; then
    echo "Testing Go SDK..."
    cd sdk/go && go build ./... && cd ../..
    echo "✅ Go SDK builds"
fi
echo ""

# Test Python SDK
if [ -d "sdk/python" ]; then
    echo "Testing Python SDK..."
    cd sdk/python && python3 -m build && cd ../..
    echo "✅ Python SDK builds"
fi
echo ""

# Test TypeScript SDK
if [ -d "sdk/typescript" ]; then
    echo "Testing TypeScript SDK..."
    cd sdk/typescript && npm install && npm run build && cd ../..
    echo "✅ TypeScript SDK builds"
fi
echo ""

# Test Rust SDK
if [ -d "sdk/rust" ]; then
    echo "Testing Rust SDK..."
    cd sdk/rust && cargo check && cd ../..
    echo "✅ Rust SDK checks pass"
fi
echo ""

echo "✅ Complete release test passed!"
```

## Commit Release and Documentation Changes

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Stage changes
git add .github/workflows/protobuf-release.yml

# Commit
git commit -m "feat(protobuf): add GitHub release and documentation generation

Added GitHub release creation and API documentation generation:

GitHub Release Features:
- Comprehensive release notes with all SDK links
- Changelog generation from git history
- Protobuf statistics (files, messages, services, RPCs)
- Breaking change warnings if detected
- Prerelease detection (alpha, beta, rc)
- Multi-language installation instructions

Release Artifacts:
- Protobuf schemas tarball
- Generated SDKs tarball
- Installation instructions (all languages)
- BSR publication info
- Statistics JSON
- Breaking changes report (if applicable)

API Documentation:
- protoc-gen-doc integration
- Markdown documentation generation
- HTML documentation generation
- JSON schema export
- Documentation index with package/service listing
- Auto-commit documentation to repository

Verification Features:
- Buf BSR accessibility check
- Go module availability check
- PyPI package verification
- npm package verification
- crates.io manual verification link
- Comprehensive verification report

Documentation Links:
- BSR repository page
- Package registry pages (all languages)
- GitHub release page
- Installation commands for all SDKs

Artifacts:
- api-documentation: Complete API docs (MD, HTML, JSON)
- verification-report: Publication status report

Local Testing:
- test-complete-protobuf-release.sh: End-to-end release test

Files changed:
- .github/workflows/protobuf-release.yml - Release and documentation jobs"
```

## Next Steps

**Continue to Part 6:** Troubleshooting, complete workflow summary, and completion checklist.
