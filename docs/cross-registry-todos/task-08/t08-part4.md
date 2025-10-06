<!-- file: docs/cross-registry-todos/task-08/t08-part4.md -->
<!-- version: 1.0.0 -->
<!-- guid: t08-ci-consolidation-part4-e0f1g2h3-i4j5 -->

# Task 08 Part 4: Remaining Language Jobs & Docker

## Continuing reusable-ci-consolidated.yml

```yaml
  # ============================================================================
  # Job 6: TypeScript/Node.js - Build, Test, Coverage
  # ============================================================================
  test-typescript:
    name: Node.js ${{ matrix.node-version }}
    needs: detect-changes
    if: |
      inputs.enable-typescript == true &&
      (inputs.skip-change-detection == true || needs.detect-changes.outputs.has-typescript-changes == 'true')
    runs-on: ubuntu-latest
    timeout-minutes: ${{ fromJson(inputs.test-timeout) }}
    strategy:
      fail-fast: false
      matrix:
        node-version: ${{ fromJson(inputs.node-versions) }}

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'

      - name: Install dependencies
        run: |
          echo "### 📦 Installing Dependencies" >> $GITHUB_STEP_SUMMARY
          npm ci

      - name: Lint
        run: |
          echo "### 🔍 Linting TypeScript/JavaScript" >> $GITHUB_STEP_SUMMARY
          npm run lint

      - name: Type check
        run: |
          echo "### 🔍 Type Checking with TypeScript" >> $GITHUB_STEP_SUMMARY
          npx tsc --noEmit

      - name: Build
        run: |
          echo "### 🔨 Building Project" >> $GITHUB_STEP_SUMMARY
          npm run build

      - name: Test with coverage
        if: inputs.enable-coverage == true
        run: |
          echo "### 🧪 Running Tests with Coverage" >> $GITHUB_STEP_SUMMARY
          npm test -- --coverage --coverageReporters=text --coverageReporters=lcov

      - name: Test without coverage
        if: inputs.enable-coverage == false
        run: |
          echo "### 🧪 Running Tests" >> $GITHUB_STEP_SUMMARY
          npm test

      - name: Bundle size analysis
        if: inputs.enable-benchmarks == true
        run: |
          echo "### 📊 Analyzing Bundle Size" >> $GITHUB_STEP_SUMMARY
          if [ -f "dist/index.js" ]; then
            ls -lh dist/
            du -sh dist/
          fi

      - name: Check coverage threshold
        if: inputs.enable-coverage == true && inputs.coverage-threshold > 0
        run: |
          # Extract coverage from lcov.info
          if [ -f coverage/lcov.info ]; then
            total_lines=$(grep -o "LF:[0-9]*" coverage/lcov.info | cut -d: -f2 | awk '{s+=$1} END {print s}')
            covered_lines=$(grep -o "LH:[0-9]*" coverage/lcov.info | cut -d: -f2 | awk '{s+=$1} END {print s}')
            coverage=$(echo "scale=2; $covered_lines * 100 / $total_lines" | bc)
            threshold=${{ inputs.coverage-threshold }}

            echo "Coverage: ${coverage}%"
            echo "Threshold: ${threshold}%"

            if (( $(echo "$coverage < $threshold" | bc -l) )); then
              echo "❌ Coverage ${coverage}% is below threshold ${threshold}%"
              exit 1
            else
              echo "✅ Coverage ${coverage}% meets threshold ${threshold}%"
            fi
          fi

      - name: Upload coverage to Codecov
        if: |
          inputs.enable-coverage == true &&
          matrix.node-version == fromJson(inputs.node-versions)[0]
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage/lcov.info
          flags: typescript
          name: typescript-${{ matrix.node-version }}
          fail_ci_if_error: false

      - name: Upload build artifacts
        uses: actions/upload-artifact@v4
        with:
          name: typescript-build-${{ matrix.node-version }}
          path: |
            dist/
            coverage/
          retention-days: 30

  # ============================================================================
  # Job 7: Rust - Build, Test, Coverage
  # ============================================================================
  test-rust:
    name: Rust ${{ matrix.rust-version }}
    needs: detect-changes
    if: |
      inputs.enable-rust == true &&
      (inputs.skip-change-detection == true || needs.detect-changes.outputs.has-rust-changes == 'true')
    runs-on: ubuntu-latest
    timeout-minutes: ${{ fromJson(inputs.test-timeout) }}
    strategy:
      fail-fast: false
      matrix:
        rust-version: ${{ fromJson(inputs.rust-versions) }}

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Rust
        uses: dtolnay/rust-toolchain@master
        with:
          toolchain: ${{ matrix.rust-version }}
          components: rustfmt, clippy, llvm-tools-preview

      - name: Cache Rust dependencies
        uses: Swatinem/rust-cache@v2
        with:
          cache-all-crates: true
          cache-on-failure: true

      - name: Install cargo-llvm-cov
        if: inputs.enable-coverage == true
        run: cargo install cargo-llvm-cov

      - name: Format check
        run: |
          echo "### 🔍 Checking Rust Formatting" >> $GITHUB_STEP_SUMMARY
          cargo fmt -- --check

      - name: Clippy
        run: |
          echo "### 🔍 Running Clippy" >> $GITHUB_STEP_SUMMARY
          cargo clippy --all-features --all-targets -- -D warnings

      - name: Build
        run: |
          echo "### 🔨 Building Rust Project" >> $GITHUB_STEP_SUMMARY
          cargo build --release --all-features --verbose

      - name: Test with coverage
        if: inputs.enable-coverage == true
        run: |
          echo "### 🧪 Running Tests with Coverage" >> $GITHUB_STEP_SUMMARY
          mkdir -p htmlcov
          cargo llvm-cov --all-features --lcov --output-path lcov.info --verbose
          cargo llvm-cov --all-features --html --output-dir htmlcov

      - name: Test without coverage
        if: inputs.enable-coverage == false
        run: |
          echo "### 🧪 Running Tests" >> $GITHUB_STEP_SUMMARY
          cargo test --all-features --verbose

      - name: Run benchmarks
        if: |
          inputs.enable-benchmarks == true &&
          matrix.rust-version == 'nightly' &&
          github.event_name == 'push'
        run: |
          echo "### 📊 Running Benchmarks" >> $GITHUB_STEP_SUMMARY
          cargo bench --no-fail-fast | tee benchmark.txt

      - name: Check coverage threshold
        if: inputs.enable-coverage == true && inputs.coverage-threshold > 0
        run: |
          if [ -f lcov.info ]; then
            total_lines=$(grep -o "LF:[0-9]*" lcov.info | cut -d: -f2 | awk '{s+=$1} END {print s}')
            covered_lines=$(grep -o "LH:[0-9]*" lcov.info | cut -d: -f2 | awk '{s+=$1} END {print s}')
            coverage=$(echo "scale=2; $covered_lines * 100 / $total_lines" | bc)
            threshold=${{ inputs.coverage-threshold }}

            echo "Coverage: ${coverage}%"
            echo "Threshold: ${threshold}%"

            if (( $(echo "$coverage < $threshold" | bc -l) )); then
              echo "❌ Coverage ${coverage}% is below threshold ${threshold}%"
              exit 1
            else
              echo "✅ Coverage ${coverage}% meets threshold ${threshold}%"
            fi
          fi

      - name: Upload coverage to Codecov
        if: |
          inputs.enable-coverage == true &&
          matrix.rust-version == 'stable'
        uses: codecov/codecov-action@v4
        with:
          files: ./lcov.info
          flags: rust
          name: rust-${{ matrix.rust-version }}
          fail_ci_if_error: false

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: rust-test-results-${{ matrix.rust-version }}
          path: |
            lcov.info
            htmlcov/
            benchmark.txt
            target/release/
          retention-days: 30

  # ============================================================================
  # Job 8: Docker - Build, Scan, SBOM
  # ============================================================================
  build-docker:
    name: Build & Scan Docker Images
    needs: detect-changes
    if: |
      inputs.enable-docker == true &&
      (inputs.skip-change-detection == true || needs.detect-changes.outputs.has-docker-changes == 'true')
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write
      packages: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Generate image metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: |
            ${{ inputs.docker-registry }}/${{ github.repository }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha

      - name: Build Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          platforms: ${{ inputs.docker-platforms }}
          push: false
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          outputs: type=docker,dest=/tmp/image.tar

      - name: Load image for scanning
        run: |
          docker load --input /tmp/image.tar
          docker image ls -a

      - name: Run Trivy security scan
        if: inputs.enable-security-scan == true
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ inputs.docker-registry }}/${{ github.repository }}:${{ github.sha }}
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH,MEDIUM'
          vuln-type: 'os,library'
          ignore-unfixed: false

      - name: Upload Trivy results to GitHub Security
        if: inputs.enable-security-scan == true
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'
          category: 'trivy-docker'

      - name: Generate SBOM with syft
        if: inputs.enable-security-scan == true
        uses: anchore/sbom-action@v0
        with:
          image: ${{ inputs.docker-registry }}/${{ github.repository }}:${{ github.sha }}
          format: spdx-json
          output-file: sbom.spdx.json

      - name: Scan SBOM with grype
        if: inputs.enable-security-scan == true
        run: |
          curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin
          grype sbom:./sbom.spdx.json -o json > grype-results.json
          grype sbom:./sbom.spdx.json -o table

      - name: Display security summary
        if: inputs.enable-security-scan == true
        run: |
          echo "### 🔒 Docker Security Scan Results" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY

          # Trivy results
          if [ -f trivy-results.sarif ]; then
            critical=$(jq '.runs[0].results | map(select(.level == "error")) | length' trivy-results.sarif)
            high=$(jq '.runs[0].results | map(select(.level == "warning")) | length' trivy-results.sarif)
            echo "**Trivy Scan:**" >> $GITHUB_STEP_SUMMARY
            echo "- Critical: $critical" >> $GITHUB_STEP_SUMMARY
            echo "- High: $high" >> $GITHUB_STEP_SUMMARY
            echo "" >> $GITHUB_STEP_SUMMARY
          fi

          # Grype results
          if [ -f grype-results.json ]; then
            total=$(jq '.matches | length' grype-results.json)
            echo "**Grype Scan:**" >> $GITHUB_STEP_SUMMARY
            echo "- Total vulnerabilities: $total" >> $GITHUB_STEP_SUMMARY
          fi

      - name: Upload security artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: docker-security-results
          path: |
            trivy-results.sarif
            sbom.spdx.json
            grype-results.json
          retention-days: 90

      - name: Upload Docker image artifact
        uses: actions/upload-artifact@v4
        with:
          name: docker-image
          path: /tmp/image.tar
          retention-days: 7

  # ============================================================================
  # Job 9: Security Scanning (CodeQL, Dependency Review)
  # ============================================================================
  security-scan:
    name: Security Scanning
    if: inputs.enable-security-scan == true
    runs-on: ubuntu-latest
    permissions:
      security-events: write
      contents: read
      actions: read

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Detect languages for CodeQL
        id: detect-languages
        run: |
          languages=""

          if [ -n "$(find . -name '*.go' -not -path '*/vendor/*')" ]; then
            languages="${languages},go"
          fi

          if [ -n "$(find . -name '*.py' -not -path '*/__pycache__/*')" ]; then
            languages="${languages},python"
          fi

          if [ -n "$(find . -name '*.js' -o -name '*.ts' -not -path '*/node_modules/*')" ]; then
            languages="${languages},javascript"
          fi

          if [ -n "$(find . -name '*.rs' -not -path '*/target/*')" ]; then
            languages="${languages},rust"
          fi

          # Remove leading comma
          languages=$(echo "$languages" | sed 's/^,//')

          echo "languages=$languages" >> $GITHUB_OUTPUT
          echo "Detected languages: $languages"

      - name: Initialize CodeQL
        if: steps.detect-languages.outputs.languages != ''
        uses: github/codeql-action/init@v3
        with:
          languages: ${{ steps.detect-languages.outputs.languages }}
          queries: security-and-quality

      - name: Autobuild
        if: steps.detect-languages.outputs.languages != ''
        uses: github/codeql-action/autobuild@v3

      - name: Perform CodeQL Analysis
        if: steps.detect-languages.outputs.languages != ''
        uses: github/codeql-action/analyze@v3
        with:
          category: 'codeql-security'

      - name: Dependency Review
        if: |
          inputs.enable-dependency-review == true &&
          github.event_name == 'pull_request'
        uses: actions/dependency-review-action@v4
        with:
          fail-on-severity: high
          deny-licenses: GPL-3.0, AGPL-3.0

  # ============================================================================
  # Job 10: Protobuf (Optional)
  # ============================================================================
  build-protobuf:
    name: Build Protobuf
    needs: detect-changes
    if: |
      inputs.enable-protobuf == true &&
      (inputs.skip-change-detection == true || needs.detect-changes.outputs.has-protobuf-changes == 'true')
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Buf
        uses: bufbuild/buf-setup-action@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}

      - name: Buf lint
        run: |
          echo "### 🔍 Linting Protobuf Files" >> $GITHUB_STEP_SUMMARY
          buf lint

      - name: Buf breaking change detection
        if: github.event_name == 'pull_request'
        run: |
          echo "### 🔍 Checking Breaking Changes" >> $GITHUB_STEP_SUMMARY
          buf breaking --against '.git#branch=main'

      - name: Buf generate
        run: |
          echo "### 🔨 Generating Protobuf Code" >> $GITHUB_STEP_SUMMARY
          buf generate

      - name: Upload generated code
        uses: actions/upload-artifact@v4
        with:
          name: protobuf-generated
          path: |
            gen/
            pkg/
          retention-days: 30

# Continue in Part 5...
```

## Local Testing Scripts

### test-consolidated-workflow.sh

```bash
#!/bin/bash
# file: scripts/test-consolidated-workflow.sh
# version: 1.0.0
# guid: test-consolidated-workflow-script

set -e

echo "=== Testing Consolidated CI Workflow Locally ==="

# Test 1: Validate workflow syntax
echo "🔍 Validating workflow YAML syntax..."
yamllint .github/workflows/reusable-ci-consolidated.yml

# Test 2: Check for required inputs
echo "🔍 Checking required inputs..."
yq eval '.on.workflow_call.inputs | keys' .github/workflows/reusable-ci-consolidated.yml

# Test 3: Verify job structure
echo "🔍 Verifying job structure..."
jobs=$(yq eval '.jobs | keys' .github/workflows/reusable-ci-consolidated.yml)
echo "Jobs defined: $jobs"

# Test 4: Check output definitions
echo "🔍 Checking output definitions..."
yq eval '.on.workflow_call.outputs | keys' .github/workflows/reusable-ci-consolidated.yml

# Test 5: Validate conditionals
echo "🔍 Validating job conditionals..."
for job in $(yq eval '.jobs | keys | .[]' .github/workflows/reusable-ci-consolidated.yml); do
  condition=$(yq eval ".jobs.$job.if" .github/workflows/reusable-ci-consolidated.yml)
  if [ "$condition" != "null" ]; then
    echo "  $job: $condition"
  fi
done

echo "✅ Workflow validation complete!"
```

### Compare workflows script

```bash
#!/bin/bash
# file: scripts/compare-workflows.sh
# version: 1.0.0
# guid: compare-workflows-script

echo "=== Comparing Old vs New Workflows ==="

old_workflow=".github/workflows/reusable-ci.yml"
new_workflow=".github/workflows/reusable-ci-consolidated.yml"

echo "📊 Feature Comparison:"
echo ""

# Compare jobs
echo "Jobs in old workflow:"
yq eval '.jobs | keys' "$old_workflow"

echo ""
echo "Jobs in new workflow:"
yq eval '.jobs | keys' "$new_workflow"

echo ""
echo "📝 Input Comparison:"
echo "Old inputs:"
yq eval '.on.workflow_call.inputs | keys' "$old_workflow"

echo ""
echo "New inputs:"
yq eval '.on.workflow_call.inputs | keys' "$new_workflow"

echo ""
echo "📤 Output Comparison:"
echo "Old outputs:"
yq eval '.on.workflow_call.outputs | keys' "$old_workflow" || echo "None"

echo ""
echo "New outputs:"
yq eval '.on.workflow_call.outputs | keys' "$new_workflow"
```

## Continue to Part 5

Next part will cover:

- Result aggregation job
- Migration guide for existing workflows
- Testing procedures
- Complete workflow file
