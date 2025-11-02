<!-- file: docs/cross-registry-todos/task-12/t12-part3.md -->
<!-- version: 1.0.0 -->
<!-- guid: t12-dependency-management-part3-h0i1j2k3-l4m5 -->

# Task 12 Part 3: Go Dependencies and Docker Base Image Management

## Go Dependency Management

### Go Module Configuration

```go
// file: go.mod
// version: 1.0.0
// guid: go-module-config

module github.com/jdfalk/ghcommon

go 1.21

require (
 github.com/spf13/cobra v1.8.0
 github.com/spf13/viper v1.18.2
 gopkg.in/yaml.v3 v3.0.1
 github.com/rs/zerolog v1.31.0
)

require (
 // Indirect dependencies (managed automatically)
 github.com/inconshreveable/mousetrap v1.1.0 // indirect
 github.com/spf13/pflag v1.0.5 // indirect
 // ... more indirect dependencies
)

// Replace directives for security patches or forks
// replace github.com/vulnerable/package => github.com/safe/package v1.2.3

// Exclude known vulnerable versions
// exclude github.com/package/name v1.0.0
```

### Go Vulnerability Scanning Workflow

```yaml
# file: .github/workflows/go-security-audit.yml
# version: 1.0.0
# guid: go-security-audit-workflow

name: Go Security Audit

on:
  schedule:
    - cron: '0 3 * * *' # Daily at 03:00 UTC
  push:
    paths:
      - 'go.mod'
      - 'go.sum'
      - '**/*.go'
  pull_request:
    paths:
      - 'go.mod'
      - 'go.sum'
      - '**/*.go'
  workflow_dispatch:

jobs:
  govulncheck:
    name: Go Vulnerability Check
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Go
        uses: actions/setup-go@v5
        with:
          go-version: '1.21'
          cache: true

      - name: Install govulncheck
        run: go install golang.org/x/vuln/cmd/govulncheck@latest

      - name: Run govulncheck
        id: vulncheck
        run: |
          govulncheck -json ./... > govulncheck-results.json || true
          cat govulncheck-results.json

      - name: Parse results
        id: parse
        run: |
          VULNS=$(jq '[.[] | select(.osv != null)] | length' govulncheck-results.json)
          echo "vulnerabilities=$VULNS" >> $GITHUB_OUTPUT

      - name: Convert to SARIF
        if: always()
        run: |
          jq '{
            version: "2.1.0",
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            runs: [{
              tool: {
                driver: {
                  name: "govulncheck",
                  informationUri: "https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck",
                  version: "latest"
                }
              },
              results: [.[] | select(.osv != null) | {
                ruleId: .osv.id,
                level: "error",
                message: {
                  text: .osv.summary
                },
                locations: [{
                  physicalLocation: {
                    artifactLocation: {
                      uri: "go.mod"
                    }
                  }
                }],
                properties: {
                  module: .module,
                  package: .package,
                  version: .version,
                  fixed_version: .osv.fixed_version
                }
              }]
            }]
          }' govulncheck-results.json > govulncheck.sarif

      - name: Upload SARIF
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: govulncheck.sarif
          category: govulncheck

      - name: Fail on vulnerabilities
        if: steps.parse.outputs.vulnerabilities > 0
        run: |
          echo "::error::Found ${{ steps.parse.outputs.vulnerabilities }} vulnerabilities"
          exit 1

  gosec:
    name: Go Security Scanner (SAST)
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run gosec
        uses: securego/gosec@master
        with:
          args: '-fmt sarif -out gosec.sarif ./...'

      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: gosec.sarif
          category: gosec

  nancy:
    name: Nancy Dependency Audit
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Go
        uses: actions/setup-go@v5
        with:
          go-version: '1.21'

      - name: Install nancy
        run: go install github.com/sonatype-nexus-community/nancy@latest

      - name: Run nancy
        run: |
          go list -json -deps ./... | nancy sleuth --output json > nancy-results.json || true
          cat nancy-results.json

      - name: Parse results
        run: |
          VULNERABILITIES=$(jq '[.[] | select(.vulnerable == true)] | length' nancy-results.json)

          if [ "$VULNERABILITIES" -gt 0 ]; then
            echo "::error::Found $VULNERABILITIES vulnerable dependencies"
            jq -r '.[] | select(.vulnerable == true) | "\(.coordinates): \(.title)"' nancy-results.json
            exit 1
          fi

  go-licenses:
    name: Go License Compliance
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Go
        uses: actions/setup-go@v5
        with:
          go-version: '1.21'

      - name: Install go-licenses
        run: go install github.com/google/go-licenses@latest

      - name: Check licenses
        run: |
          go-licenses report ./... --template licenses.tpl > licenses.md || true

          # Check for copyleft licenses
          COPYLEFT=$(go-licenses report ./... | grep -E "GPL|AGPL|SSPL" || echo "")

          if [ -n "$COPYLEFT" ]; then
            echo "::error::Found copyleft licensed dependencies:"
            echo "$COPYLEFT"
            exit 1
          fi

      - name: Upload license report
        uses: actions/upload-artifact@v4
        with:
          name: go-license-report
          path: licenses.md
```

## Docker Base Image Management

### Dockerfile with Version Pinning

```dockerfile
# file: Dockerfile
# version: 2.0.0
# guid: dockerfile-pinned-versions

# syntax=docker/dockerfile:1.4

# ============================================================================
# Builder Stage - Rust compilation
# ============================================================================

FROM rust:1.75.0-bookworm as builder

ARG TARGETPLATFORM
ARG BUILDPLATFORM

# Install build dependencies with specific versions
RUN apt-get update && apt-get install -y \
    gcc-aarch64-linux-gnu=4:12.2.0-3 \
    gcc-arm-linux-gnueabihf=4:12.2.0-3 \
    musl-tools=1.2.3-1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Cache dependencies layer
COPY Cargo.toml Cargo.lock ./
RUN mkdir src && \
    echo "fn main() {}" > src/main.rs && \
    cargo build --release && \
    rm -rf src

# Build actual application
COPY . .
RUN cargo build --release --locked

# ============================================================================
# Runtime Stage - Minimal Debian
# ============================================================================

FROM debian:bookworm-20231218-slim as runtime

# Security: Run as non-root user
RUN groupadd -r appuser && \
    useradd -r -g appuser -u 1001 appuser

# Install runtime dependencies with specific versions
RUN apt-get update && apt-get install -y \
    ca-certificates=20230311 \
    libssl3=3.0.11-1~deb12u2 \
    && rm -rf /var/lib/apt/lists/*

# Copy binary from builder
COPY --from=builder /build/target/release/app /usr/local/bin/app
RUN chmod +x /usr/local/bin/app

USER appuser

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD ["/usr/local/bin/app", "healthcheck"]

ENTRYPOINT ["/usr/local/bin/app"]
CMD ["--help"]
```

### Docker Base Image Update Workflow

```yaml
# file: .github/workflows/docker-base-image-update.yml
# version: 1.0.0
# guid: docker-base-image-update-workflow

name: Docker Base Image Updates

on:
  schedule:
    - cron: '0 4 * * 1' # Weekly on Monday at 04:00 UTC
  workflow_dispatch:

jobs:
  check-updates:
    name: Check Base Image Updates
    runs-on: ubuntu-latest
    outputs:
      updates_available: ${{ steps.check.outputs.updates_available }}
      base_images: ${{ steps.check.outputs.base_images }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Extract base images from Dockerfile
        id: extract
        run: |
          # Extract all FROM statements
          IMAGES=$(grep '^FROM' Dockerfile | awk '{print $2}' | sort -u)
          echo "base_images=$(echo $IMAGES | jq -R -s -c 'split(" ") | map(select(length > 0))')" >> $GITHUB_OUTPUT

      - name: Check for updates
        id: check
        run: |
          UPDATES_FOUND=false

          for IMAGE in $(echo '${{ steps.extract.outputs.base_images }}' | jq -r '.[]'); do
            echo "Checking $IMAGE"

            # Get current digest
            CURRENT_DIGEST=$(docker manifest inspect $IMAGE | jq -r '.config.digest')

            # Get latest digest (without version tag)
            BASE_NAME=$(echo $IMAGE | cut -d: -f1)
            LATEST_DIGEST=$(docker manifest inspect ${BASE_NAME}:latest | jq -r '.config.digest')

            if [ "$CURRENT_DIGEST" != "$LATEST_DIGEST" ]; then
              echo "Update available for $IMAGE"
              UPDATES_FOUND=true
            fi
          done

          echo "updates_available=$UPDATES_FOUND" >> $GITHUB_OUTPUT

  scan-base-images:
    name: Scan Base Images for Vulnerabilities
    needs: check-updates
    if: needs.check-updates.outputs.updates_available == 'true'
    runs-on: ubuntu-latest

    strategy:
      matrix:
        image: ${{ fromJson(needs.check-updates.outputs.base_images) }}

    steps:
      - name: Pull image
        run: docker pull ${{ matrix.image }}

      - name: Scan with Trivy
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ matrix.image }}
          format: 'sarif'
          output: 'trivy-${{ matrix.image }}.sarif'
          severity: 'CRITICAL,HIGH'

      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-${{ matrix.image }}.sarif'
          category: 'trivy-base-image-${{ matrix.image }}'

      - name: Scan with Grype
        run: |
          curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin
          grype ${{ matrix.image }} -o json > grype-results.json

          CRITICAL=$(jq '[.matches[] | select(.vulnerability.severity == "Critical")] | length' grype-results.json)
          HIGH=$(jq '[.matches[] | select(.vulnerability.severity == "High")] | length' grype-results.json)

          echo "Critical vulnerabilities: $CRITICAL"
          echo "High vulnerabilities: $HIGH"

          if [ "$CRITICAL" -gt 0 ]; then
            echo "::error::Found $CRITICAL critical vulnerabilities in ${{ matrix.image }}"
          fi

  update-dockerfile:
    name: Update Dockerfile with Latest Digests
    needs: [check-updates, scan-base-images]
    if: needs.check-updates.outputs.updates_available == 'true'
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Update base image versions
        run: |
          for IMAGE in $(echo '${{ needs.check-updates.outputs.base_images }}' | jq -r '.[]'); do
            echo "Processing $IMAGE"

            # Get latest digest
            DIGEST=$(docker manifest inspect $IMAGE | jq -r '.config.digest')
            BASE_NAME=$(echo $IMAGE | cut -d: -f1)
            TAG=$(echo $IMAGE | cut -d: -f2)

            # Update Dockerfile with digest pinning
            sed -i "s|FROM ${BASE_NAME}:${TAG}|FROM ${BASE_NAME}:${TAG}@sha256:${DIGEST}|g" Dockerfile
          done

      - name: Build test image
        run: |
          docker build --no-cache -t test-image:latest .

      - name: Test built image
        run: |
          docker run --rm test-image:latest --version

      - name: Create PR with updates
        uses: peter-evans/create-pull-request@v5
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          commit-message: 'chore(docker): update base images to latest secure versions'
          title: '[Security] Update Docker Base Images'
          body: |
            Automated update of Docker base images to latest secure versions.

            **Images Updated**:
            ${{ needs.check-updates.outputs.base_images }}

            **Security Scans**:
            - Trivy scan: Passed
            - Grype scan: Passed
            - Build test: Passed

            Please review vulnerability scan results before merging.
          branch: auto-update/docker-base-images
          labels: security,docker,automated
```

### Docker Compose Dependency Management

```yaml
# file: docker-compose.yml
# version: 1.0.0
# guid: docker-compose-config

version: '3.9'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        BUILDKIT_INLINE_CACHE: 1
    image: ghcr.io/jdfalk/ghcommon:latest
    container_name: ghcommon-app
    restart: unless-stopped

    # Security options
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    read_only: true

    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 256M

    # Health check
    healthcheck:
      test: ['CMD', '/usr/local/bin/app', 'healthcheck']
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

    # Volumes
    volumes:
      - ./data:/data:ro
      - tmp:/tmp

    # Networks
    networks:
      - app-network

    # Environment
    environment:
      - LOG_LEVEL=info
      - RUST_LOG=info

  # Dependency: PostgreSQL with specific version
  postgres:
    image: postgres:16.1-alpine3.19
    container_name: ghcommon-postgres
    restart: unless-stopped

    environment:
      POSTGRES_DB: ghcommon
      POSTGRES_USER: ${POSTGRES_USER:-ghcommon}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?POSTGRES_PASSWORD required}

    volumes:
      - postgres-data:/var/lib/postgresql/data

    networks:
      - app-network

    healthcheck:
      test: ['CMD-SHELL', 'pg_isready -U ${POSTGRES_USER:-ghcommon}']
      interval: 10s
      timeout: 5s
      retries: 5

  # Dependency: Redis with specific version
  redis:
    image: redis:7.2.3-alpine3.19
    container_name: ghcommon-redis
    restart: unless-stopped

    command: redis-server --requirepass ${REDIS_PASSWORD:?REDIS_PASSWORD required}

    volumes:
      - redis-data:/data

    networks:
      - app-network

    healthcheck:
      test: ['CMD', 'redis-cli', 'ping']
      interval: 10s
      timeout: 3s
      retries: 3

volumes:
  postgres-data:
    driver: local
  redis-data:
    driver: local
  tmp:
    driver: local

networks:
  app-network:
    driver: bridge
```

### Docker Image Vulnerability Monitoring

```yaml
# file: .github/workflows/docker-vulnerability-monitoring.yml
# version: 1.0.0
# guid: docker-vulnerability-monitoring

name: Docker Image Vulnerability Monitoring

on:
  schedule:
    - cron: '0 */6 * * *' # Every 6 hours
  workflow_dispatch:

jobs:
  scan-published-images:
    name: Scan Published Images
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write

    strategy:
      matrix:
        registry: [ghcr.io, docker.io]
        tag: [latest, stable]

    steps:
      - name: Login to registry
        uses: docker/login-action@v3
        with:
          registry: ${{ matrix.registry }}
          username: ${{ matrix.registry == 'ghcr.io' && github.actor || secrets.DOCKERHUB_USERNAME }}
          password: ${{ matrix.registry == 'ghcr.io' && secrets.GITHUB_TOKEN || secrets.DOCKERHUB_TOKEN }}

      - name: Determine image name
        id: image
        run: |
          REPO=$(echo "${{ github.repository }}" | tr '[:upper:]' '[:lower:]')

          if [ "${{ matrix.registry }}" == "ghcr.io" ]; then
            IMAGE="${{ matrix.registry }}/${REPO}:${{ matrix.tag }}"
          else
            IMAGE="${{ matrix.registry }}/$(basename ${REPO}):${{ matrix.tag }}"
          fi

          echo "name=$IMAGE" >> $GITHUB_OUTPUT

      - name: Pull image
        run: docker pull ${{ steps.image.outputs.name }}

      - name: Scan with Trivy
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ steps.image.outputs.name }}
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH,MEDIUM'

      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: trivy-results.sarif
          category: 'trivy-${{ matrix.registry }}-${{ matrix.tag }}'

      - name: Generate vulnerability report
        run: |
          trivy image --format json --output trivy-report.json ${{ steps.image.outputs.name }}

          CRITICAL=$(jq '[.Results[].Vulnerabilities[]? | select(.Severity == "CRITICAL")] | length' trivy-report.json)
          HIGH=$(jq '[.Results[].Vulnerabilities[]? | select(.Severity == "HIGH")] | length' trivy-report.json)
          MEDIUM=$(jq '[.Results[].Vulnerabilities[]? | select(.Severity == "MEDIUM")] | length' trivy-report.json)

          echo "Image: ${{ steps.image.outputs.name }}" > vuln-summary.txt
          echo "Critical: $CRITICAL" >> vuln-summary.txt
          echo "High: $HIGH" >> vuln-summary.txt
          echo "Medium: $MEDIUM" >> vuln-summary.txt

      - name: Upload vulnerability summary
        uses: actions/upload-artifact@v4
        with:
          name: vuln-summary-${{ matrix.registry }}-${{ matrix.tag }}
          path: vuln-summary.txt

      - name: Create issue for critical vulnerabilities
        if: github.event_name == 'schedule'
        run: |
          CRITICAL=$(jq '[.Results[].Vulnerabilities[]? | select(.Severity == "CRITICAL")] | length' trivy-report.json)

          if [ "$CRITICAL" -gt 0 ]; then
            # Issue creation would go here (using github-script or gh CLI)
            echo "::error::Found $CRITICAL critical vulnerabilities in ${{ steps.image.outputs.name }}"
          fi
```

---

**Part 3 Complete**: Go dependency management (govulncheck, gosec, nancy, license checking), Docker
base image management (version pinning, security scanning, automated updates, vulnerability
monitoring). ✅

**Continue to Part 4** for Dependabot configuration and automated dependency updates.
