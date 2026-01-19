<!-- file: docs/cross-registry-todos/task-11/t11-part3.md -->
<!-- version: 1.0.0 -->
<!-- guid: t11-artifact-management-part3-w9x0y1z2-a3b4 -->
<!-- last-edited: 2026-01-19 -->

# Task 11 Part 3: Container Image Release Automation

## Multi-Arch Container Release Workflow

````yaml
# file: .github/workflows/release-docker.yml
# version: 1.0.0
# guid: release-docker-workflow

name: Release Docker Images

on:
  push:
    tags:
      - 'v*.*.*'
  workflow_dispatch:

env:
  REGISTRY_GHCR: ghcr.io
  REGISTRY_DOCKERHUB: docker.io

jobs:
  build-and-push:
    name: Build and Push Multi-Arch Images
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
      id-token: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Extract metadata
        id: meta
        run: |
          VERSION=${GITHUB_REF#refs/tags/v}
          echo "version=$VERSION" >> $GITHUB_OUTPUT
          echo "short_sha=${GITHUB_SHA::7}" >> $GITHUB_OUTPUT

      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY_GHCR }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Log in to Docker Hub
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY_DOCKERHUB }}
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Extract Docker metadata
        id: docker-meta
        uses: docker/metadata-action@v5
        with:
          images: |
            ${{ env.REGISTRY_GHCR }}/${{ github.repository }}
            ${{ env.REGISTRY_DOCKERHUB }}/${{ github.repository }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=semver,pattern={{major}}
            type=sha,prefix={{branch}}-
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Build and push multi-arch image
        id: build-push
        uses: docker/build-push-action@v5
        with:
          context: .
          platforms: linux/amd64,linux/arm64,linux/arm/v7
          push: true
          tags: ${{ steps.docker-meta.outputs.tags }}
          labels: ${{ steps.docker-meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          provenance: true
          sbom: true

      - name: Generate SBOM for image
        run: |
          # Install Syft
          curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin

          # Generate SBOM for each registry
          syft ${{ env.REGISTRY_GHCR }}/${{ github.repository }}:${{ steps.meta.outputs.version }} \
            -o spdx-json > sbom-ghcr-spdx.json

          syft ${{ env.REGISTRY_DOCKERHUB }}/${{ github.repository }}:${{ steps.meta.outputs.version }} \
            -o cyclonedx-json > sbom-dockerhub-cyclonedx.json

      - name: Sign images with Cosign
        run: |
          # Install Cosign
          curl -sLO https://github.com/sigstore/cosign/releases/latest/download/cosign-linux-amd64
          chmod +x cosign-linux-amd64
          sudo mv cosign-linux-amd64 /usr/local/bin/cosign

          # Sign GHCR image
          cosign sign --yes \
            ${{ env.REGISTRY_GHCR }}/${{ github.repository }}@${{ steps.build-push.outputs.digest }}

          # Sign Docker Hub image
          cosign sign --yes \
            ${{ env.REGISTRY_DOCKERHUB }}/${{ github.repository }}@${{ steps.build-push.outputs.digest }}

      - name: Attest SBOM to images
        run: |
          # Attest SBOM to GHCR image
          cosign attest --yes \
            --predicate sbom-ghcr-spdx.json \
            --type spdx \
            ${{ env.REGISTRY_GHCR }}/${{ github.repository }}@${{ steps.build-push.outputs.digest }}

          # Attest SBOM to Docker Hub image
          cosign attest --yes \
            --predicate sbom-dockerhub-cyclonedx.json \
            --type cyclonedx \
            ${{ env.REGISTRY_DOCKERHUB }}/${{ github.repository }}@${{ steps.build-push.outputs.digest }}

      - name: Scan images with Trivy
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.REGISTRY_GHCR }}/${{ github.repository }}:${{ steps.meta.outputs.version }}
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'
          category: 'container-release'

      - name: Create release with Docker metadata
        uses: softprops/action-gh-release@v1
        with:
          files: |
            sbom-*.json
          body: |
            ## Container Images

            ### GitHub Container Registry
            ```bash
            docker pull ${{ env.REGISTRY_GHCR }}/${{ github.repository }}:${{ steps.meta.outputs.version }}
            ```

            ### Docker Hub
            ```bash
            docker pull ${{ env.REGISTRY_DOCKERHUB }}/${{ github.repository }}:${{ steps.meta.outputs.version }}
            ```

            ### Verification

            Verify image signature:
            ```bash
            cosign verify \
              --certificate-identity-regexp="https://github.com/${{ github.repository }}" \
              --certificate-oidc-issuer=https://token.actions.githubusercontent.com \
              ${{ env.REGISTRY_GHCR }}/${{ github.repository }}:${{ steps.meta.outputs.version }}
            ```

            Verify SBOM attestation:
            ```bash
            cosign verify-attestation \
              --type spdx \
              --certificate-identity-regexp="https://github.com/${{ github.repository }}" \
              --certificate-oidc-issuer=https://token.actions.githubusercontent.com \
              ${{ env.REGISTRY_GHCR }}/${{ github.repository }}:${{ steps.meta.outputs.version }}
            ```

            ### Platforms
            - linux/amd64
            - linux/arm64
            - linux/arm/v7

            ### Digest
            ```
            ${{ steps.build-push.outputs.digest }}
            ```
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  update-docker-hub-readme:
    name: Update Docker Hub README
    needs: build-and-push
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Update Docker Hub Description
        uses: peter-evans/dockerhub-description@v4
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
          repository: ${{ github.repository }}
          readme-filepath: ./README.md
````

## Optimized Dockerfile for Multi-Arch Builds

```dockerfile
# file: Dockerfile
# version: 1.0.0
# guid: dockerfile-multiarch

# Build stage
FROM --platform=$BUILDPLATFORM rust:1.75-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Set up cross-compilation
ARG TARGETPLATFORM
ARG BUILDPLATFORM
RUN echo "Building for $TARGETPLATFORM on $BUILDPLATFORM"

# Install cross-compilation toolchain
RUN case "$TARGETPLATFORM" in \
    "linux/amd64") echo "x86_64-unknown-linux-gnu" > /target.txt ;; \
    "linux/arm64") echo "aarch64-unknown-linux-gnu" > /target.txt && \
                   apt-get update && apt-get install -y gcc-aarch64-linux-gnu ;; \
    "linux/arm/v7") echo "armv7-unknown-linux-gnueabihf" > /target.txt && \
                    apt-get update && apt-get install -y gcc-arm-linux-gnueabihf ;; \
    *) echo "Unsupported platform: $TARGETPLATFORM" && exit 1 ;; \
    esac

# Set working directory
WORKDIR /build

# Copy dependency manifests
COPY Cargo.toml Cargo.lock ./

# Create dummy source to cache dependencies
RUN mkdir src && echo "fn main() {}" > src/main.rs && \
    CARGO_TARGET=$(cat /target.txt) && \
    rustup target add $CARGO_TARGET && \
    cargo build --release --target $CARGO_TARGET && \
    rm -rf src

# Copy actual source
COPY src ./src

# Build release binary
RUN CARGO_TARGET=$(cat /target.txt) && \
    cargo build --release --target $CARGO_TARGET && \
    cp target/$CARGO_TARGET/release/$(grep '^name = ' Cargo.toml | head -n1 | cut -d'"' -f2) /app

# Runtime stage
FROM --platform=$TARGETPLATFORM debian:bookworm-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash appuser

# Copy binary from builder
COPY --from=builder /app /usr/local/bin/app
RUN chmod +x /usr/local/bin/app

# Switch to non-root user
USER appuser

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/app"]
```

## Docker Compose for Local Testing

```yaml
# file: docker-compose.yml
# version: 1.0.0
# guid: docker-compose

version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
      platforms:
        - linux/amd64
        - linux/arm64
    image: ${REGISTRY:-ghcr.io}/${REPOSITORY:-jdfalk/app}:${VERSION:-latest}
    container_name: app
    restart: unless-stopped
    environment:
      - LOG_LEVEL=info
    ports:
      - '8080:8080'
    volumes:
      - app-data:/data
    healthcheck:
      test: ['CMD', 'curl', '-f', 'http://localhost:8080/health']
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - app-network

volumes:
  app-data:
    driver: local

networks:
  app-network:
    driver: bridge
```

## Container Registry Cleanup Workflow

```yaml
# file: .github/workflows/cleanup-old-images.yml
# version: 1.0.0
# guid: cleanup-old-images-workflow

name: Cleanup Old Container Images

on:
  schedule:
    # Run weekly on Sunday at 00:00 UTC
    - cron: '0 0 * * 0'
  workflow_dispatch:

jobs:
  cleanup-ghcr:
    name: Cleanup GHCR Images
    runs-on: ubuntu-latest
    permissions:
      packages: write

    steps:
      - name: Delete old untagged images
        uses: actions/delete-package-versions@v5
        with:
          package-name: ${{ github.event.repository.name }}
          package-type: 'container'
          min-versions-to-keep: 10
          delete-only-untagged-versions: true

      - name: Delete old pre-release images
        uses: actions/delete-package-versions@v5
        with:
          package-name: ${{ github.event.repository.name }}
          package-type: 'container'
          min-versions-to-keep: 5
          ignore-versions: '^(latest|v\\d+\\.\\d+\\.\\d+)$'

  cleanup-dockerhub:
    name: Cleanup Docker Hub Images
    runs-on: ubuntu-latest

    steps:
      - name: Install Docker Hub API tools
        run: |
          pip install requests

      - name: Cleanup old tags
        env:
          DOCKERHUB_USERNAME: ${{ secrets.DOCKERHUB_USERNAME }}
          DOCKERHUB_TOKEN: ${{ secrets.DOCKERHUB_TOKEN }}
        run: |
          python - <<'EOF'
          import os
          import requests
          from datetime import datetime, timedelta

          username = os.environ['DOCKERHUB_USERNAME']
          token = os.environ['DOCKERHUB_TOKEN']
          repository = '${{ github.repository }}'

          # Get auth token
          auth_response = requests.post(
              'https://hub.docker.com/v2/users/login',
              json={'username': username, 'password': token}
          )
          jwt_token = auth_response.json()['token']

          headers = {'Authorization': f'Bearer {jwt_token}'}

          # Get tags
          tags_response = requests.get(
              f'https://hub.docker.com/v2/repositories/{repository}/tags',
              headers=headers
          )
          tags = tags_response.json()['results']

          # Delete old tags (keep last 10)
          cutoff_date = datetime.now() - timedelta(days=90)

          for tag in tags:
              tag_date = datetime.fromisoformat(tag['last_updated'].replace('Z', '+00:00'))
              if tag_date < cutoff_date and tag['name'] not in ['latest', 'stable']:
                  print(f"Deleting tag: {tag['name']}")
                  delete_response = requests.delete(
                      f"https://hub.docker.com/v2/repositories/{repository}/tags/{tag['name']}",
                      headers=headers
                  )
                  print(f"Status: {delete_response.status_code}")
          EOF
```

## Image Verification Script

```bash
#!/bin/bash
# file: scripts/verify-container-release.sh
# version: 1.0.0
# guid: verify-container-release

set -e

VERSION="$1"
REGISTRY="${2:-ghcr.io}"
REPOSITORY="${3:-jdfalk/app}"

if [ -z "$VERSION" ]; then
  echo "Usage: $0 <version> [registry] [repository]"
  exit 1
fi

IMAGE="${REGISTRY}/${REPOSITORY}:${VERSION}"

echo "==================================="
echo "Verifying Container Image"
echo "==================================="
echo "Image: $IMAGE"
echo ""

# 1. Pull image
echo "📥 Pulling image..."
docker pull "$IMAGE"

# 2. Verify signature with Cosign
echo ""
echo "🔐 Verifying signature..."
cosign verify \
  --certificate-identity-regexp="https://github.com/${REPOSITORY}" \
  --certificate-oidc-issuer=https://token.actions.githubusercontent.com \
  "$IMAGE"

# 3. Verify SBOM attestation
echo ""
echo "📋 Verifying SBOM attestation..."
cosign verify-attestation \
  --type spdx \
  --certificate-identity-regexp="https://github.com/${REPOSITORY}" \
  --certificate-oidc-issuer=https://token.actions.githubusercontent.com \
  "$IMAGE"

# 4. Extract SBOM
echo ""
echo "📄 Extracting SBOM..."
cosign verify-attestation \
  --type spdx \
  --certificate-identity-regexp="https://github.com/${REPOSITORY}" \
  --certificate-oidc-issuer=https://token.actions.githubusercontent.com \
  "$IMAGE" | jq -r '.payload' | base64 -d | jq '.predicate' > sbom-extracted.json

echo "✅ SBOM extracted to sbom-extracted.json"

# 5. Scan with Trivy
echo ""
echo "🔍 Scanning with Trivy..."
trivy image --severity HIGH,CRITICAL "$IMAGE"

# 6. Inspect image
echo ""
echo "🔎 Image details:"
docker inspect "$IMAGE" | jq '.[0] | {
  Architecture: .Architecture,
  Os: .Os,
  Size: .Size,
  Created: .Created,
  Author: .Author,
  Config: {
    User: .Config.User,
    ExposedPorts: .Config.ExposedPorts,
    Env: .Config.Env,
    Cmd: .Config.Cmd,
    Entrypoint: .Config.Entrypoint
  }
}'

echo ""
echo "✅ Verification complete!"
```

---

**Part 3 Complete**: Multi-arch container release workflow, Dockerfile optimization, image signing
with Cosign, SBOM attestation, registry cleanup. ✅

**Continue to Part 4** for system package generation (deb, rpm, Homebrew), installers, and
distribution automation.
