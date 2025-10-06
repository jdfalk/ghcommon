<!-- file: docs/cross-registry-todos/task-07/t07-part2.md -->
<!-- version: 1.0.0 -->
<!-- guid: t07-protobuf-packages-part2-r1s2t3u4-v5w6 -->

# Task 07 Part 2: Workflow Setup and Protobuf Detection

## Workflow File Creation

### Create: `.github/workflows/protobuf-release.yml`

```yaml
<!-- file: .github/workflows/protobuf-release.yml -->
<!-- version: 1.0.0 -->
<!-- guid: protobuf-release-workflow-x7y8z9a0-b1c2 -->

name: Release Protobuf Packages

on:
  push:
    tags:
      - 'proto-v*'
  workflow_dispatch:
    inputs:
      version:
        description: 'Protobuf version to release (e.g., 1.0.0)'
        required: true
      dry_run:
        description: 'Dry run (skip publishing)'
        required: false
        default: 'false'
      publish_go:
        description: 'Publish Go SDK'
        required: false
        default: 'true'
      publish_python:
        description: 'Publish Python SDK'
        required: false
        default: 'true'
      publish_typescript:
        description: 'Publish TypeScript SDK'
        required: false
        default: 'true'
      publish_rust:
        description: 'Publish Rust SDK'
        required: false
        default: 'true'

env:
  # Buf Configuration
  BUF_VERSION: '1.28.1'
  BUF_MODULE_NAME: 'buf.build/jdfalk/ghcommon'

  # Language Versions
  GO_VERSION: '1.21'
  PYTHON_VERSION: '3.11'
  NODE_VERSION: '20'
  RUST_VERSION: 'stable'

  # Publishing Configuration
  PUBLISH_TO_BSR: 'true'
  PUBLISH_GO_SDK: ${{ github.event.inputs.publish_go || 'true' }}
  PUBLISH_PYTHON_SDK: ${{ github.event.inputs.publish_python || 'true' }}
  PUBLISH_TYPESCRIPT_SDK: ${{ github.event.inputs.publish_typescript || 'true' }}
  PUBLISH_RUST_SDK: ${{ github.event.inputs.publish_rust || 'true' }}
  DRY_RUN: ${{ github.event.inputs.dry_run || 'false' }}

permissions:
  contents: write
  packages: write

jobs:
```

## Stage 1: Detect Protobuf Changes

### Step 1: Protobuf Detection Job

```yaml
  detect-protobuf:
    name: Detect Protobuf Files
    runs-on: ubuntu-latest
    outputs:
      has-proto: ${{ steps.detect.outputs.has-proto }}
      proto-files: ${{ steps.detect.outputs.proto-files }}
      proto-dirs: ${{ steps.detect.outputs.proto-dirs }}
      buf-config-exists: ${{ steps.detect.outputs.buf-config-exists }}
      buf-gen-config-exists: ${{ steps.detect.outputs.buf-gen-config-exists }}
      version: ${{ steps.version.outputs.version }}
      major: ${{ steps.version.outputs.major }}
      minor: ${{ steps.version.outputs.minor }}
      patch: ${{ steps.version.outputs.patch }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Detect protobuf files
        id: detect
        run: |
          echo "=== Detecting Protobuf Files ==="
          echo ""

          # Find .proto files
          PROTO_FILES=$(find . -name "*.proto" -type f -not -path "*/vendor/*" -not -path "*/node_modules/*" -not -path "*/.git/*" | sort)

          if [ -z "$PROTO_FILES" ]; then
              echo "has-proto=false" >> $GITHUB_OUTPUT
              echo "❌ No .proto files found"
              exit 0
          fi

          echo "has-proto=true" >> $GITHUB_OUTPUT

          # Count files
          FILE_COUNT=$(echo "$PROTO_FILES" | wc -l | tr -d ' ')
          echo "✅ Found $FILE_COUNT protobuf files"
          echo ""

          # List files
          echo "Protobuf files:"
          echo "$PROTO_FILES" | while read file; do
              echo "  - $file"
          done

          # Save to output
          PROTO_FILES_JSON=$(echo "$PROTO_FILES" | jq -R -s -c 'split("\n") | map(select(length > 0))')
          echo "proto-files=$PROTO_FILES_JSON" >> $GITHUB_OUTPUT

          # Find unique directories
          PROTO_DIRS=$(echo "$PROTO_FILES" | xargs -n1 dirname | sort -u)
          PROTO_DIRS_JSON=$(echo "$PROTO_DIRS" | jq -R -s -c 'split("\n") | map(select(length > 0))')
          echo "proto-dirs=$PROTO_DIRS_JSON" >> $GITHUB_OUTPUT

          echo ""
          echo "Protobuf directories:"
          echo "$PROTO_DIRS" | while read dir; do
              echo "  - $dir"
          done

      - name: Check Buf configuration
        id: buf-config
        run: |
          echo "=== Checking Buf Configuration ==="
          echo ""

          # Check buf.yaml
          if [ -f "buf.yaml" ]; then
              echo "buf-config-exists=true" >> $GITHUB_OUTPUT
              echo "✅ buf.yaml found"

              echo ""
              echo "buf.yaml contents:"
              cat buf.yaml
          else
              echo "buf-config-exists=false" >> $GITHUB_OUTPUT
              echo "⚠️  buf.yaml not found"
              echo "   Will need to create before publishing to BSR"
          fi

          echo ""

          # Check buf.gen.yaml
          if [ -f "buf.gen.yaml" ]; then
              echo "buf-gen-config-exists=true" >> $GITHUB_OUTPUT
              echo "✅ buf.gen.yaml found"

              echo ""
              echo "buf.gen.yaml contents:"
              cat buf.gen.yaml
          else
              echo "buf-gen-config-exists=false" >> $GITHUB_OUTPUT
              echo "⚠️  buf.gen.yaml not found"
              echo "   Will need to create for code generation"
          fi

          # Check buf.lock
          if [ -f "buf.lock" ]; then
              echo ""
              echo "✅ buf.lock found"
          fi

      - name: Extract version
        id: version
        run: |
          echo "=== Extracting Version ==="
          echo ""

          if [ "${{ github.event_name }}" = "workflow_dispatch" ]; then
              VERSION="${{ github.event.inputs.version }}"
              echo "Using manual version: $VERSION"
          else
              # Extract from tag (proto-v1.2.3 -> 1.2.3)
              TAG_NAME="${{ github.ref_name }}"
              VERSION="${TAG_NAME#proto-v}"
              echo "Extracted from tag: $VERSION"
          fi

          echo "version=$VERSION" >> $GITHUB_OUTPUT

          # Parse semantic version
          if [[ $VERSION =~ ^([0-9]+)\.([0-9]+)\.([0-9]+) ]]; then
              MAJOR="${BASH_REMATCH[1]}"
              MINOR="${BASH_REMATCH[2]}"
              PATCH="${BASH_REMATCH[3]}"

              echo "major=$MAJOR" >> $GITHUB_OUTPUT
              echo "minor=$MINOR" >> $GITHUB_OUTPUT
              echo "patch=$PATCH" >> $GITHUB_OUTPUT

              echo ""
              echo "Semantic version:"
              echo "  Major: $MAJOR"
              echo "  Minor: $MINOR"
              echo "  Patch: $PATCH"
          else
              echo "❌ ERROR: Invalid semantic version: $VERSION"
              exit 1
          fi

      - name: Analyze protobuf structure
        run: |
          echo "=== Analyzing Protobuf Structure ==="
          echo ""

          # Find all packages
          PACKAGES=$(find . -name "*.proto" -type f -exec grep -h "^package " {} \; | sed 's/package \(.*\);/\1/' | sort -u)

          if [ -n "$PACKAGES" ]; then
              echo "Protobuf packages:"
              echo "$PACKAGES" | while read pkg; do
                  COUNT=$(find . -name "*.proto" -exec grep -l "^package $pkg;" {} \; | wc -l | tr -d ' ')
                  echo "  - $pkg ($COUNT files)"
              done
          fi

          echo ""

          # Find all services
          SERVICES=$(find . -name "*.proto" -exec grep -h "^service " {} \; | sed 's/service \([^ ]*\).*/\1/' | sort -u)

          if [ -n "$SERVICES" ]; then
              echo "gRPC services:"
              echo "$SERVICES" | while read svc; do
                  echo "  - $svc"
              done
          else
              echo "No gRPC services defined"
          fi

          echo ""

          # Find all messages
          MESSAGE_COUNT=$(find . -name "*.proto" -exec grep -c "^message " {} \; | awk '{sum+=$1} END {print sum}')
          echo "Total message types: $MESSAGE_COUNT"

          # Find all enums
          ENUM_COUNT=$(find . -name "*.proto" -exec grep -c "^enum " {} \; | awk '{sum+=$1} END {print sum}')
          echo "Total enum types: $ENUM_COUNT"
```

## Stage 2: Validate Protobuf with Buf

### Step 1: Install and Configure Buf

```yaml
  validate-protobuf:
    name: Validate Protobuf
    runs-on: ubuntu-latest
    needs: detect-protobuf
    if: needs.detect-protobuf.outputs.has-proto == 'true'

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Install Buf
        run: |
          echo "=== Installing Buf CLI ==="
          echo ""

          VERSION="${{ env.BUF_VERSION }}"

          # Download Buf
          curl -sSL \
            "https://github.com/bufbuild/buf/releases/download/v${VERSION}/buf-Linux-x86_64" \
            -o /usr/local/bin/buf

          chmod +x /usr/local/bin/buf

          # Verify installation
          echo "✅ Buf installed"
          buf --version

      - name: Setup Buf configuration
        if: needs.detect-protobuf.outputs.buf-config-exists == 'false'
        run: |
          echo "=== Creating Default Buf Configuration ==="
          echo ""

          cat > buf.yaml << 'EOF'
          version: v2
          modules:
            - path: proto
              name: ${{ env.BUF_MODULE_NAME }}
          lint:
            use:
              - DEFAULT
              - COMMENTS
          breaking:
            use:
              - FILE
          EOF

          echo "✅ Created buf.yaml"
          cat buf.yaml
```

### Step 2: Buf Linting

```yaml
      - name: Buf lint
        id: lint
        run: |
          echo "=== Running Buf Lint ==="
          echo ""

          # Run lint
          if buf lint; then
              echo "✅ Linting passed"
              echo "lint-passed=true" >> $GITHUB_OUTPUT
          else
              echo "❌ Linting failed"
              echo "lint-passed=false" >> $GITHUB_OUTPUT
              exit 1
          fi

      - name: Buf format check
        continue-on-error: true
        run: |
          echo "=== Checking Buf Format ==="
          echo ""

          # Check if files are formatted
          if buf format --diff --exit-code; then
              echo "✅ All files are properly formatted"
          else
              echo "⚠️  Some files need formatting"
              echo ""
              echo "To fix, run:"
              echo "  buf format -w"
          fi
```

### Step 3: Breaking Change Detection

```yaml
      - name: Detect breaking changes
        id: breaking
        continue-on-error: true
        run: |
          echo "=== Checking for Breaking Changes ==="
          echo ""

          # Get previous tag
          CURRENT_TAG="${{ github.ref_name }}"
          PREV_TAG=$(git tag --sort=-version:refname | grep "^proto-v" | grep -v "^${CURRENT_TAG}$" | head -1)

          if [ -z "$PREV_TAG" ]; then
              echo "ℹ️  No previous tag found, skipping breaking change detection"
              echo "has-breaking-changes=false" >> $GITHUB_OUTPUT
              exit 0
          fi

          echo "Comparing against: $PREV_TAG"
          echo ""

          # Check breaking changes
          if buf breaking --against ".git#tag=$PREV_TAG"; then
              echo "✅ No breaking changes detected"
              echo "has-breaking-changes=false" >> $GITHUB_OUTPUT
          else
              echo "⚠️  Breaking changes detected!"
              echo "has-breaking-changes=true" >> $GITHUB_OUTPUT

              echo ""
              echo "Breaking changes found. This requires a major version bump."
              echo "Current version: ${{ needs.detect-protobuf.outputs.version }}"
              echo "Expected major: ${{ needs.detect-protobuf.outputs.major }}"

              # Don't fail, just warn
              exit 0
          fi

      - name: Generate breaking change report
        if: steps.breaking.outputs.has-breaking-changes == 'true'
        run: |
          echo "=== Breaking Change Report ==="
          echo ""

          PREV_TAG=$(git tag --sort=-version:refname | grep "^proto-v" | grep -v "^${{ github.ref_name }}$" | head -1)

          buf breaking --against ".git#tag=$PREV_TAG" 2>&1 | tee breaking-changes.txt

          echo ""
          echo "⚠️  This report will be included in the GitHub release"

      - name: Upload breaking change report
        if: steps.breaking.outputs.has-breaking-changes == 'true'
        uses: actions/upload-artifact@v4
        with:
          name: breaking-changes-report
          path: breaking-changes.txt
          retention-days: 90
```

## Stage 3: Generate Protobuf Statistics

### Step 1: Statistics Collection

```yaml
  collect-protobuf-stats:
    name: Collect Protobuf Statistics
    runs-on: ubuntu-latest
    needs: [detect-protobuf, validate-protobuf]
    if: needs.detect-protobuf.outputs.has-proto == 'true'

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install analysis tools
        run: |
          sudo apt-get update
          sudo apt-get install -y jq cloc

      - name: Analyze protobuf files
        run: |
          echo "=== Protobuf Analysis ==="
          echo ""

          # Lines of code
          echo "Lines of code:"
          cloc --include-lang=Protocol\ Buffers . 2>/dev/null || echo "cloc failed"

          echo ""

          # File count by directory
          echo "Files by directory:"
          find . -name "*.proto" | sed 's|/[^/]*$||' | sort | uniq -c | sort -rn

          echo ""

          # Message definitions
          echo "Message definitions:"
          find . -name "*.proto" -exec grep -h "^message " {} \; | wc -l

          # Enum definitions
          echo "Enum definitions:"
          find . -name "*.proto" -exec grep -h "^enum " {} \; | wc -l

          # Service definitions
          echo "Service definitions:"
          find . -name "*.proto" -exec grep -h "^service " {} \; | wc -l

          # RPC methods
          echo "RPC methods:"
          find . -name "*.proto" -exec grep -h "  rpc " {} \; | wc -l

          echo ""

      - name: Extract dependencies
        run: |
          echo "=== Protobuf Dependencies ==="
          echo ""

          # Find all imports
          IMPORTS=$(find . -name "*.proto" -exec grep -h "^import " {} \; | sed 's/import "\(.*\)";/\1/' | sort -u)

          if [ -n "$IMPORTS" ]; then
              echo "External imports:"
              echo "$IMPORTS" | while read imp; do
                  # Count usage
                  COUNT=$(find . -name "*.proto" -exec grep -l "^import \"$imp\";" {} \; | wc -l | tr -d ' ')
                  echo "  - $imp (used in $COUNT files)"
              done
          else
              echo "No external imports"
          fi

      - name: Generate statistics report
        run: |
          cat > protobuf-stats.json << EOF
          {
            "version": "${{ needs.detect-protobuf.outputs.version }}",
            "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
            "files": {
              "total": $(find . -name "*.proto" | wc -l),
              "directories": $(find . -name "*.proto" | sed 's|/[^/]*$||' | sort -u | wc -l)
            },
            "definitions": {
              "messages": $(find . -name "*.proto" -exec grep -c "^message " {} \; | awk '{sum+=$1} END {print sum}'),
              "enums": $(find . -name "*.proto" -exec grep -c "^enum " {} \; | awk '{sum+=$1} END {print sum}'),
              "services": $(find . -name "*.proto" -exec grep -c "^service " {} \; | awk '{sum+=$1} END {print sum}'),
              "rpcs": $(find . -name "*.proto" -exec grep -c "  rpc " {} \; | awk '{sum+=$1} END {print sum}')
            },
            "validation": {
              "lint_passed": true,
              "breaking_changes": ${{ steps.breaking.outputs.has-breaking-changes || false }}
            }
          }
          EOF

          echo "Statistics report:"
          cat protobuf-stats.json | jq .

      - name: Upload statistics
        uses: actions/upload-artifact@v4
        with:
          name: protobuf-statistics
          path: protobuf-stats.json
          retention-days: 90
```

## Local Testing Scripts

### Test Protobuf Detection

```bash
#!/bin/bash
# test-protobuf-detection.sh

echo "=== Testing Protobuf Detection ==="
echo ""

# Find proto files
PROTO_FILES=$(find . -name "*.proto" -type f -not -path "*/vendor/*" -not -path "*/node_modules/*" | sort)

if [ -z "$PROTO_FILES" ]; then
    echo "❌ No .proto files found"
    exit 1
fi

FILE_COUNT=$(echo "$PROTO_FILES" | wc -l | tr -d ' ')
echo "✅ Found $FILE_COUNT protobuf files"
echo ""

echo "Protobuf files:"
echo "$PROTO_FILES"
echo ""

# Check Buf config
if [ -f "buf.yaml" ]; then
    echo "✅ buf.yaml exists"
else
    echo "⚠️  buf.yaml missing"
fi

if [ -f "buf.gen.yaml" ]; then
    echo "✅ buf.gen.yaml exists"
else
    echo "⚠️  buf.gen.yaml missing"
fi

echo ""
echo "✅ Detection test complete"
```

### Test Buf Linting

```bash
#!/bin/bash
# test-buf-lint.sh

echo "=== Testing Buf Lint ==="
echo ""

if ! command -v buf &> /dev/null; then
    echo "❌ Buf not installed"
    echo "Install: brew install bufbuild/buf/buf"
    exit 1
fi

echo "Buf version: $(buf --version)"
echo ""

# Run lint
if buf lint; then
    echo ""
    echo "✅ Linting passed"
else
    echo ""
    echo "❌ Linting failed"
    exit 1
fi
```

### Test Breaking Changes

```bash
#!/bin/bash
# test-breaking-changes.sh

echo "=== Testing Breaking Change Detection ==="
echo ""

if ! command -v buf &> /dev/null; then
    echo "❌ Buf not installed"
    exit 1
fi

# Get previous tag
PREV_TAG=$(git tag --sort=-version:refname | grep "^proto-v" | head -1)

if [ -z "$PREV_TAG" ]; then
    echo "ℹ️  No previous proto tag found"
    echo "First release, skipping breaking change check"
    exit 0
fi

echo "Comparing against: $PREV_TAG"
echo ""

# Check breaking changes
if buf breaking --against ".git#tag=$PREV_TAG"; then
    echo ""
    echo "✅ No breaking changes"
else
    echo ""
    echo "⚠️  Breaking changes detected"
    echo "Requires major version bump"
    exit 1
fi
```

## Commit Workflow Changes

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Stage workflow
git add .github/workflows/protobuf-release.yml

# Commit with conventional format
git commit -m "feat(protobuf): add protobuf detection and validation workflow

Created protobuf-release.yml with detection and validation:

Added Jobs:
- detect-protobuf: Finds and analyzes .proto files
- validate-protobuf: Buf linting and breaking change detection
- collect-protobuf-stats: Statistical analysis

Detection Features:
- Find all .proto files (excluding vendor/node_modules)
- Extract protobuf directories
- Check Buf configuration files (buf.yaml, buf.gen.yaml)
- Parse semantic version from tag
- Analyze protobuf structure (packages, services, messages, enums)

Validation Features:
- Buf CLI installation (v1.28.1)
- Auto-create buf.yaml if missing
- Buf linting with DEFAULT + COMMENTS rules
- Buf format checking
- Breaking change detection against previous tag
- Breaking change report generation

Statistics Collection:
- Lines of code analysis
- File distribution by directory
- Message/enum/service/RPC counts
- Dependency extraction and usage analysis
- JSON statistics report

Outputs:
- has-proto: Boolean indicating .proto files found
- proto-files: JSON array of protobuf file paths
- proto-dirs: JSON array of protobuf directories
- buf-config-exists: Boolean for buf.yaml existence
- version/major/minor/patch: Semantic version components
- has-breaking-changes: Boolean for breaking change detection

Artifacts:
- breaking-changes-report: Breaking change details (if detected)
- protobuf-statistics: JSON statistics report

Workflow Triggers:
- push: Tags matching 'proto-v*'
- workflow_dispatch: Manual trigger with version input

Environment Variables:
- BUF_VERSION: Buf CLI version
- BUF_MODULE_NAME: Full BSR module path
- Language versions (Go, Python, Node, Rust)
- Publishing flags per language

Local Testing:
- test-protobuf-detection.sh: Verify .proto file detection
- test-buf-lint.sh: Test linting locally
- test-breaking-changes.sh: Check breaking changes

Files changed:
- .github/workflows/protobuf-release.yml - Detection and validation jobs"
```

## Next Steps

**Continue to Part 3:** Buf BSR publishing and multi-language SDK generation setup.
