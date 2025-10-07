<!-- file: docs/cross-registry-todos/task-10/t10-part2.md -->
<!-- version: 1.0.0 -->
<!-- guid: t10-security-scanning-part2-g7h8i9j0-k1l2 -->

# Task 10 Part 2: Container Security Scanning

## Trivy Integration for Container Images

### Comprehensive Trivy Workflow

Create reusable Trivy scanning workflow:

```yaml
# file: .github/workflows/reusable-trivy-scan.yml
# version: 1.0.0
# guid: reusable-trivy-scan

name: Reusable Trivy Security Scan

on:
  workflow_call:
    inputs:
      image-ref:
        description: 'Container image reference to scan'
        required: true
        type: string
      scan-type:
        description: 'Scan type: image, fs, rootfs, config'
        required: false
        type: string
        default: 'image'
      severity:
        description: 'Severity levels to report'
        required: false
        type: string
        default: 'CRITICAL,HIGH'
      exit-code:
        description: 'Exit code when vulnerabilities are found'
        required: false
        type: number
        default: 1
      upload-sarif:
        description: 'Upload results to GitHub Security'
        required: false
        type: boolean
        default: true

jobs:
  trivy-scan:
    name: Trivy Security Scan
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write
      actions: read

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@0.28.0
        with:
          scan-type: ${{ inputs.scan-type }}
          image-ref: ${{ inputs.image-ref }}
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: ${{ inputs.severity }}
          exit-code: ${{ inputs.exit-code }}
          vuln-type: 'os,library'
          scanners: 'vuln,secret,config'
          timeout: '10m'
          # Cache database for faster scans
          cache-dir: '/tmp/trivy-cache'

      - name: Upload Trivy results to GitHub Security
        if: inputs.upload-sarif == true
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'
          category: 'trivy'

      - name: Run Trivy in table mode
        uses: aquasecurity/trivy-action@0.28.0
        with:
          scan-type: ${{ inputs.scan-type }}
          image-ref: ${{ inputs.image-ref }}
          format: 'table'
          severity: ${{ inputs.severity }}
          exit-code: '0'  # Don't fail, just report
          vuln-type: 'os,library'
          scanners: 'vuln,secret,config'

      - name: Run Trivy in JSON mode for artifacts
        uses: aquasecurity/trivy-action@0.28.0
        with:
          scan-type: ${{ inputs.scan-type }}
          image-ref: ${{ inputs.image-ref }}
          format: 'json'
          output: 'trivy-results.json'
          severity: 'UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL'
          exit-code: '0'

      - name: Upload Trivy JSON results
        uses: actions/upload-artifact@v4
        with:
          name: trivy-results-${{ github.run_id }}
          path: trivy-results.json
          retention-days: 30
```

### Integrate Trivy into Docker Workflow

Update `.github/workflows/reusable-docker.yml`:

```yaml
# Add to reusable-docker.yml after build job
  trivy-scan:
    name: Trivy Security Scan
    needs: build
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write

    strategy:
      matrix:
        platform:
          - linux/amd64
          - linux/arm64

    steps:
      - name: Download Docker image
        uses: actions/download-artifact@v4
        with:
          name: docker-image-${{ matrix.platform }}
          path: /tmp

      - name: Load Docker image
        run: docker load -i /tmp/image.tar

      - name: Get image reference
        id: image-ref
        run: |
          IMAGE_REF=$(docker images --format "{{.Repository}}:{{.Tag}}" | head -n1)
          echo "image-ref=${IMAGE_REF}" >> $GITHUB_OUTPUT

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@0.28.0
        with:
          scan-type: 'image'
          image-ref: ${{ steps.image-ref.outputs.image-ref }}
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'

      - name: Upload Trivy results to GitHub Security
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'
          category: 'trivy-${{ matrix.platform }}'
```

## Grype Integration for Redundant Scanning

Add Grype as a secondary scanner for comprehensive coverage:

```yaml
# file: .github/workflows/reusable-grype-scan.yml
# version: 1.0.0
# guid: reusable-grype-scan

name: Reusable Grype Security Scan

on:
  workflow_call:
    inputs:
      image-ref:
        description: 'Container image reference to scan'
        required: true
        type: string
      fail-on:
        description: 'Fail on severity: negligible, low, medium, high, critical'
        required: false
        type: string
        default: 'high'
      output-format:
        description: 'Output format: table, json, sarif'
        required: false
        type: string
        default: 'sarif'

jobs:
  grype-scan:
    name: Grype Vulnerability Scan
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install Grype
        run: |
          curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin

      - name: Scan container image with Grype (SARIF)
        run: |
          grype ${{ inputs.image-ref }} \
            -o sarif \
            --file grype-results.sarif \
            --fail-on ${{ inputs.fail-on }}

      - name: Upload Grype results to GitHub Security
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'grype-results.sarif'
          category: 'grype'

      - name: Scan container image with Grype (Table)
        if: always()
        run: |
          grype ${{ inputs.image-ref }} -o table

      - name: Scan container image with Grype (JSON)
        if: always()
        run: |
          grype ${{ inputs.image-ref }} -o json --file grype-results.json

      - name: Upload Grype JSON results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: grype-results-${{ github.run_id }}
          path: grype-results.json
          retention-days: 30
```

## SBOM Generation with Syft

Generate Software Bill of Materials for supply chain transparency:

```yaml
# file: .github/workflows/reusable-sbom-generation.yml
# version: 1.0.0
# guid: reusable-sbom-generation

name: Reusable SBOM Generation

on:
  workflow_call:
    inputs:
      image-ref:
        description: 'Container image reference for SBOM generation'
        required: true
        type: string
      output-formats:
        description: 'SBOM output formats: spdx-json, cyclonedx-json, syft-json'
        required: false
        type: string
        default: 'spdx-json,cyclonedx-json'

jobs:
  generate-sbom:
    name: Generate SBOM
    runs-on: ubuntu-latest
    permissions:
      contents: write
      packages: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install Syft
        run: |
          curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin

      - name: Generate SPDX SBOM
        run: |
          syft ${{ inputs.image-ref }} \
            -o spdx-json \
            --file sbom-spdx.json

      - name: Generate CycloneDX SBOM
        run: |
          syft ${{ inputs.image-ref }} \
            -o cyclonedx-json \
            --file sbom-cyclonedx.json

      - name: Generate Syft JSON SBOM
        run: |
          syft ${{ inputs.image-ref }} \
            -o syft-json \
            --file sbom-syft.json

      - name: Upload SBOM artifacts
        uses: actions/upload-artifact@v4
        with:
          name: sbom-${{ github.run_id }}
          path: |
            sbom-*.json
          retention-days: 90

      - name: Attach SBOM to GitHub Release
        if: startsWith(github.ref, 'refs/tags/')
        uses: softprops/action-gh-release@v1
        with:
          files: |
            sbom-spdx.json
            sbom-cyclonedx.json
            sbom-syft.json
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Docker Scout Integration

For repositories using GitHub Container Registry:

```yaml
# Add to Docker workflow after push to ghcr.io
  docker-scout:
    name: Docker Scout Analysis
    needs: push
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: read
      security-events: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Docker Scout CVE Analysis
        uses: docker/scout-action@v1
        with:
          command: cves
          image: ghcr.io/${{ github.repository }}:${{ github.sha }}
          only-severities: critical,high
          exit-code: true
          sarif-file: docker-scout-results.sarif

      - name: Upload Docker Scout results to GitHub Security
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'docker-scout-results.sarif'
          category: 'docker-scout'

      - name: Docker Scout Recommendations
        if: always()
        uses: docker/scout-action@v1
        with:
          command: recommendations
          image: ghcr.io/${{ github.repository }}:${{ github.sha }}
```

## Multi-Stage Security Scanning Strategy

Implement defense-in-depth with multiple scanning stages:

```yaml
# file: .github/workflows/container-security.yml
# version: 1.0.0
# guid: container-security-workflow

name: Container Security

on:
  push:
    branches: [main]
    paths:
      - 'Dockerfile'
      - '.dockerignore'
      - '**/Dockerfile'
  pull_request:
    branches: [main]
    paths:
      - 'Dockerfile'
      - '.dockerignore'
      - '**/Dockerfile'
  schedule:
    # Run every day at 02:00 UTC
    - cron: '0 2 * * *'
  workflow_dispatch:

jobs:
  build-image:
    name: Build Container Image
    runs-on: ubuntu-latest
    outputs:
      image-digest: ${{ steps.build.outputs.digest }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build and export
        id: build
        uses: docker/build-push-action@v5
        with:
          context: .
          tags: test-image:latest
          outputs: type=docker,dest=/tmp/image.tar
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Upload image artifact
        uses: actions/upload-artifact@v4
        with:
          name: docker-image
          path: /tmp/image.tar
          retention-days: 1

  # Stage 1: Trivy scan
  trivy-scan:
    name: Trivy Vulnerability Scan
    needs: build-image
    uses: ./.github/workflows/reusable-trivy-scan.yml
    with:
      image-ref: 'test-image:latest'
      scan-type: 'image'
      severity: 'CRITICAL,HIGH'
      exit-code: 1

  # Stage 2: Grype scan (redundant)
  grype-scan:
    name: Grype Vulnerability Scan
    needs: build-image
    uses: ./.github/workflows/reusable-grype-scan.yml
    with:
      image-ref: 'test-image:latest'
      fail-on: 'high'

  # Stage 3: SBOM generation
  generate-sbom:
    name: Generate SBOM
    needs: build-image
    uses: ./.github/workflows/reusable-sbom-generation.yml
    with:
      image-ref: 'test-image:latest'

  # Stage 4: Docker Scout (if pushing to ghcr.io)
  docker-scout:
    name: Docker Scout Analysis
    needs: [build-image, trivy-scan, grype-scan]
    runs-on: ubuntu-latest
    if: github.event_name == 'push'

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Download image
        uses: actions/download-artifact@v4
        with:
          name: docker-image
          path: /tmp

      - name: Load image
        run: docker load -i /tmp/image.tar

      - name: Tag image for Docker Hub
        run: docker tag test-image:latest jdfalk/test:latest

      - name: Log in to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Push to Docker Hub
        run: docker push jdfalk/test:latest

      - name: Docker Scout CVE Analysis
        uses: docker/scout-action@v1
        with:
          command: cves
          image: jdfalk/test:latest
          exit-code: false  # Don't fail, just report

  # Stage 5: Security summary
  security-summary:
    name: Security Summary
    needs: [trivy-scan, grype-scan, generate-sbom]
    runs-on: ubuntu-latest
    if: always()

    steps:
      - name: Download Trivy results
        uses: actions/download-artifact@v4
        with:
          name: trivy-results-${{ github.run_id }}

      - name: Download Grype results
        uses: actions/download-artifact@v4
        with:
          name: grype-results-${{ github.run_id }}

      - name: Download SBOM
        uses: actions/download-artifact@v4
        with:
          name: sbom-${{ github.run_id }}

      - name: Generate security summary
        run: |
          echo "# Security Scan Summary" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY

          echo "## Trivy Scan Results" >> $GITHUB_STEP_SUMMARY
          trivy_critical=$(jq '[.Results[].Vulnerabilities[] | select(.Severity == "CRITICAL")] | length' trivy-results.json)
          trivy_high=$(jq '[.Results[].Vulnerabilities[] | select(.Severity == "HIGH")] | length' trivy-results.json)
          echo "- **Critical**: $trivy_critical" >> $GITHUB_STEP_SUMMARY
          echo "- **High**: $trivy_high" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY

          echo "## Grype Scan Results" >> $GITHUB_STEP_SUMMARY
          grype_critical=$(jq '[.matches[] | select(.vulnerability.severity == "Critical")] | length' grype-results.json)
          grype_high=$(jq '[.matches[] | select(.vulnerability.severity == "High")] | length' grype-results.json)
          echo "- **Critical**: $grype_critical" >> $GITHUB_STEP_SUMMARY
          echo "- **High**: $grype_high" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY

          echo "## SBOM Generated" >> $GITHUB_STEP_SUMMARY
          echo "- SPDX: sbom-spdx.json" >> $GITHUB_STEP_SUMMARY
          echo "- CycloneDX: sbom-cyclonedx.json" >> $GITHUB_STEP_SUMMARY
          echo "- Syft: sbom-syft.json" >> $GITHUB_STEP_SUMMARY
```

---

**Part 2 Complete**: Trivy/Grype integration, SBOM generation, Docker Scout, multi-stage container security scanning. ✅

**Continue to Part 3** for language-specific dependency scanning tools (cargo-audit, pip-audit, npm audit, govulncheck).
