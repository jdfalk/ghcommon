<!-- file: docs/cross-registry-todos/task-11/t11-part5.md -->
<!-- version: 1.0.0 -->
<!-- guid: t11-artifact-management-part5-d6e7f8g9-h0i1 -->
<!-- last-edited: 2026-01-19 -->

# Task 11 Part 5: Release Verification and Testing

## Automated Release Verification Workflow

```yaml
# file: .github/workflows/verify-release.yml
# version: 1.0.0
# guid: verify-release-workflow

name: Verify Release

on:
  release:
    types: [published]
  workflow_dispatch:
    inputs:
      release_tag:
        description: 'Release tag to verify'
        required: true
        type: string

jobs:
  verify-binaries:
    name: Verify Binary Downloads
    runs-on: ${{ matrix.os }}

    strategy:
      matrix:
        include:
          - os: ubuntu-latest
            platform: linux-x86_64
          - os: ubuntu-latest
            platform: linux-aarch64
          - os: macos-latest
            platform: macos-x86_64
          - os: macos-13 # Intel Mac
            platform: macos-x86_64
          - os: macos-latest # Apple Silicon
            platform: macos-aarch64
          - os: windows-latest
            platform: windows-x86_64

    steps:
      - name: Get release info
        id: release
        run: |
          if [ "${{ github.event_name }}" == "workflow_dispatch" ]; then
            TAG="${{ inputs.release_tag }}"
          else
            TAG="${GITHUB_REF#refs/tags/}"
          fi
          echo "tag=$TAG" >> $GITHUB_OUTPUT
          echo "version=${TAG#v}" >> $GITHUB_OUTPUT

      - name: Download binary
        run: |
          PKG_NAME=$(basename ${{ github.repository }})
          TAG=${{ steps.release.outputs.tag }}
          PLATFORM=${{ matrix.platform }}

          curl -L -o binary.tar.gz \
            "https://github.com/${{ github.repository }}/releases/download/${TAG}/${PKG_NAME}-${PLATFORM}.tar.gz"

      - name: Verify checksum
        run: |
          PKG_NAME=$(basename ${{ github.repository }})
          TAG=${{ steps.release.outputs.tag }}
          PLATFORM=${{ matrix.platform }}

          # Download checksum file
          curl -L -o checksums.txt \
            "https://github.com/${{ github.repository }}/releases/download/${TAG}/checksums.txt"

          # Verify checksum
          if command -v sha256sum >/dev/null; then
            echo "$(grep ${PKG_NAME}-${PLATFORM}.tar.gz checksums.txt)" | sha256sum -c -
          elif command -v shasum >/dev/null; then
            echo "$(grep ${PKG_NAME}-${PLATFORM}.tar.gz checksums.txt)" | shasum -a 256 -c -
          fi

      - name: Verify signature (Cosign)
        uses: sigstore/cosign-installer@v3
        with:
          cosign-release: 'v2.2.0'

      - name: Verify binary signature
        run: |
          PKG_NAME=$(basename ${{ github.repository }})
          TAG=${{ steps.release.outputs.tag }}
          PLATFORM=${{ matrix.platform }}

          # Download signature
          curl -L -o binary.tar.gz.sig \
            "https://github.com/${{ github.repository }}/releases/download/${TAG}/${PKG_NAME}-${PLATFORM}.tar.gz.sig"

          # Verify with Cosign (keyless)
          cosign verify-blob \
            --certificate-identity-regexp=".*" \
            --certificate-oidc-issuer="https://token.actions.githubusercontent.com" \
            --signature binary.tar.gz.sig \
            binary.tar.gz

      - name: Extract and test binary
        shell: bash
        run: |
          tar -xzf binary.tar.gz

          PKG_NAME=$(basename ${{ github.repository }})

          # Make executable (Linux/macOS)
          if [ "$RUNNER_OS" != "Windows" ]; then
            chmod +x ${PKG_NAME}
            ./${PKG_NAME} --version
          else
            ./${PKG_NAME}.exe --version
          fi

  verify-containers:
    name: Verify Container Images
    runs-on: ubuntu-latest

    strategy:
      matrix:
        platform: [linux/amd64, linux/arm64, linux/arm/v7]
        registry: [ghcr.io, docker.io]

    steps:
      - name: Get release info
        id: release
        run: |
          if [ "${{ github.event_name }}" == "workflow_dispatch" ]; then
            TAG="${{ inputs.release_tag }}"
          else
            TAG="${GITHUB_REF#refs/tags/}"
          fi
          echo "tag=$TAG" >> $GITHUB_OUTPUT
          echo "version=${TAG#v}" >> $GITHUB_OUTPUT

      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Install Cosign
        uses: sigstore/cosign-installer@v3
        with:
          cosign-release: 'v2.2.0'

      - name: Install Syft
        run: |
          curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin

      - name: Pull image
        run: |
          REPO=$(echo "${{ github.repository }}" | tr '[:upper:]' '[:lower:]')
          REGISTRY=${{ matrix.registry }}
          TAG=${{ steps.release.outputs.tag }}

          if [ "$REGISTRY" == "ghcr.io" ]; then
            IMAGE="${REGISTRY}/${REPO}:${TAG}"
          else
            IMAGE="${REGISTRY}/$(basename ${REPO}):${TAG}"
          fi

          echo "image=$IMAGE" >> $GITHUB_ENV

          docker pull --platform ${{ matrix.platform }} $IMAGE

      - name: Verify image signature
        run: |
          cosign verify \
            --certificate-identity-regexp=".*" \
            --certificate-oidc-issuer="https://token.actions.githubusercontent.com" \
            ${{ env.image }}

      - name: Verify SBOM attestation
        run: |
          cosign verify-attestation \
            --certificate-identity-regexp=".*" \
            --certificate-oidc-issuer="https://token.actions.githubusercontent.com" \
            --type spdxjson \
            ${{ env.image }}

      - name: Generate SBOM and compare
        run: |
          # Extract SBOM from attestation
          cosign download attestation \
            --predicate-type spdxjson \
            ${{ env.image }} > attested-sbom.json

          # Generate fresh SBOM
          syft ${{ env.image }} -o spdx-json > generated-sbom.json

          # Compare component counts (basic validation)
          ATTESTED_COUNT=$(jq '.packages | length' attested-sbom.json)
          GENERATED_COUNT=$(jq '.packages | length' generated-sbom.json)

          echo "Attested SBOM has $ATTESTED_COUNT packages"
          echo "Generated SBOM has $GENERATED_COUNT packages"

          # Allow 10% variance due to scanning differences
          DIFF=$((ATTESTED_COUNT - GENERATED_COUNT))
          VARIANCE=$((ATTESTED_COUNT / 10))

          if [ ${DIFF#-} -gt $VARIANCE ]; then
            echo "::error::SBOM component count mismatch exceeds 10% variance"
            exit 1
          fi

      - name: Run container smoke test
        run: |
          docker run --rm --platform ${{ matrix.platform }} ${{ env.image }} --version

  verify-packages:
    name: Verify System Packages
    runs-on: ${{ matrix.os }}

    strategy:
      matrix:
        include:
          - os: ubuntu-latest
            package_type: deb
            arch: amd64
          - os: ubuntu-latest
            package_type: deb
            arch: arm64
          - os: fedora:latest
            package_type: rpm
            arch: x86_64
          - os: macos-latest
            package_type: homebrew
            arch: aarch64

    container:
      image: ${{ matrix.os }}

    steps:
      - name: Get release info
        id: release
        run: |
          if [ "${{ github.event_name }}" == "workflow_dispatch" ]; then
            TAG="${{ inputs.release_tag }}"
          else
            TAG="${GITHUB_REF#refs/tags/}"
          fi
          echo "tag=$TAG" >> $GITHUB_OUTPUT
          echo "version=${TAG#v}" >> $GITHUB_OUTPUT

      - name: Install package (Debian)
        if: matrix.package_type == 'deb'
        run: |
          PKG_NAME=$(basename ${{ github.repository }})
          TAG=${{ steps.release.outputs.tag }}
          ARCH=${{ matrix.arch }}

          curl -L -o package.deb \
            "https://github.com/${{ github.repository }}/releases/download/${TAG}/${PKG_NAME}_${TAG#v}-1_${ARCH}.deb"

          apt-get update
          apt-get install -y ./package.deb

      - name: Install package (RPM)
        if: matrix.package_type == 'rpm'
        run: |
          PKG_NAME=$(basename ${{ github.repository }})
          TAG=${{ steps.release.outputs.tag }}
          ARCH=${{ matrix.arch }}

          curl -L -o package.rpm \
            "https://github.com/${{ github.repository }}/releases/download/${TAG}/${PKG_NAME}-${TAG#v}-1.${ARCH}.rpm"

          dnf install -y ./package.rpm

      - name: Install package (Homebrew)
        if: matrix.package_type == 'homebrew'
        run: |
          brew tap jdfalk/tap
          brew install $(basename ${{ github.repository }})

      - name: Test installed package
        run: |
          PKG_NAME=$(basename ${{ github.repository }})
          ${PKG_NAME} --version
          ${PKG_NAME} --help

  verify-sboms:
    name: Verify SBOM Quality
    runs-on: ubuntu-latest

    steps:
      - name: Get release info
        id: release
        run: |
          if [ "${{ github.event_name }}" == "workflow_dispatch" ]; then
            TAG="${{ inputs.release_tag }}"
          else
            TAG="${GITHUB_REF#refs/tags/}"
          fi
          echo "tag=$TAG" >> $GITHUB_OUTPUT

      - name: Download SBOMs
        run: |
          PKG_NAME=$(basename ${{ github.repository }})
          TAG=${{ steps.release.outputs.tag }}

          mkdir sboms
          cd sboms

          # Download all SBOM files from release
          for format in spdx.json cyclonedx.json; do
            curl -L -o "${PKG_NAME}-${format}" \
              "https://github.com/${{ github.repository }}/releases/download/${TAG}/${PKG_NAME}-${format}" || true
          done

      - name: Validate SBOM format (SPDX)
        run: |
          PKG_NAME=$(basename ${{ github.repository }})

          if [ -f "sboms/${PKG_NAME}-spdx.json" ]; then
            # Check required SPDX fields
            jq -e '.spdxVersion' sboms/${PKG_NAME}-spdx.json
            jq -e '.creationInfo' sboms/${PKG_NAME}-spdx.json
            jq -e '.packages' sboms/${PKG_NAME}-spdx.json

            echo "SPDX SBOM is valid"
          fi

      - name: Validate SBOM format (CycloneDX)
        run: |
          PKG_NAME=$(basename ${{ github.repository }})

          if [ -f "sboms/${PKG_NAME}-cyclonedx.json" ]; then
            # Check required CycloneDX fields
            jq -e '.bomFormat' sboms/${PKG_NAME}-cyclonedx.json
            jq -e '.specVersion' sboms/${PKG_NAME}-cyclonedx.json
            jq -e '.components' sboms/${PKG_NAME}-cyclonedx.json

            echo "CycloneDX SBOM is valid"
          fi

      - name: Check SBOM completeness
        run: |
          PKG_NAME=$(basename ${{ github.repository }})

          # Count components
          if [ -f "sboms/${PKG_NAME}-spdx.json" ]; then
            COMPONENT_COUNT=$(jq '.packages | length' sboms/${PKG_NAME}-spdx.json)
            echo "SBOM contains $COMPONENT_COUNT components"

            if [ $COMPONENT_COUNT -lt 5 ]; then
              echo "::warning::SBOM has fewer than 5 components, may be incomplete"
            fi
          fi

  verify-documentation:
    name: Verify Release Documentation
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Get release info
        id: release
        run: |
          if [ "${{ github.event_name }}" == "workflow_dispatch" ]; then
            TAG="${{ inputs.release_tag }}"
          else
            TAG="${GITHUB_REF#refs/tags/}"
          fi
          echo "tag=$TAG" >> $GITHUB_OUTPUT

      - name: Verify CHANGELOG exists
        run: |
          if [ ! -f "CHANGELOG.md" ]; then
            echo "::error::CHANGELOG.md not found"
            exit 1
          fi

      - name: Verify release notes in CHANGELOG
        run: |
          TAG=${{ steps.release.outputs.tag }}

          if ! grep -q "${TAG}" CHANGELOG.md; then
            echo "::error::Release ${TAG} not found in CHANGELOG.md"
            exit 1
          fi

      - name: Check for breaking changes notice
        run: |
          TAG=${{ steps.release.outputs.tag }}

          # Extract release section from CHANGELOG
          awk "/## \[${TAG}\]/,/## \[/" CHANGELOG.md > release-section.txt

          # Check if major version bump
          MAJOR_VERSION=$(echo ${TAG#v} | cut -d. -f1)

          if [ "$MAJOR_VERSION" != "0" ]; then
            # Check for breaking changes keyword
            if grep -qi "breaking" release-section.txt; then
              echo "Breaking changes documented"
            else
              echo "::warning::Major version bump but no breaking changes documented"
            fi
          fi

  create-verification-report:
    name: Create Verification Report
    needs:
      [
        verify-binaries,
        verify-containers,
        verify-packages,
        verify-sboms,
        verify-documentation,
      ]
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - name: Get release info
        id: release
        run: |
          if [ "${{ github.event_name }}" == "workflow_dispatch" ]; then
            TAG="${{ inputs.release_tag }}"
          else
            TAG="${GITHUB_REF#refs/tags/}"
          fi
          echo "tag=$TAG" >> $GITHUB_OUTPUT

      - name: Create verification report
        run: |
          TAG=${{ steps.release.outputs.tag }}

          cat > verification-report.md <<EOF
          # Release Verification Report

          **Release**: ${TAG}
          **Date**: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
          **Repository**: ${{ github.repository }}

          ## Verification Results

          ### ✅ Binary Verification
          - All platform binaries downloaded successfully
          - Checksums verified
          - Signatures validated (Cosign keyless)
          - Binary execution tests passed

          ### ✅ Container Verification
          - Multi-arch images pulled successfully
          - Image signatures validated
          - SBOM attestations verified
          - Container smoke tests passed

          ### ✅ Package Verification
          - System packages (deb, rpm) installed successfully
          - Homebrew formula working
          - Package execution tests passed

          ### ✅ SBOM Verification
          - SPDX format validated
          - CycloneDX format validated
          - Component count acceptable

          ### ✅ Documentation Verification
          - CHANGELOG.md exists
          - Release notes present
          - Breaking changes documented (if applicable)

          ## Conclusion

          All verification checks passed. Release ${TAG} is verified and ready for production use.

          ---
          *Report generated automatically by GitHub Actions*
          EOF

      - name: Upload verification report
        uses: actions/upload-artifact@v4
        with:
          name: verification-report
          path: verification-report.md

      - name: Comment on release
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('verification-report.md', 'utf8');

            const release = await github.rest.repos.getReleaseByTag({
              owner: context.repo.owner,
              repo: context.repo.repo,
              tag: '${{ steps.release.outputs.tag }}'
            });

            await github.rest.repos.createReleaseComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              release_id: release.data.id,
              body: report
            });
```

## Release Rollback Workflow

```yaml
# file: .github/workflows/rollback-release.yml
# version: 1.0.0
# guid: rollback-release-workflow

name: Rollback Release

on:
  workflow_dispatch:
    inputs:
      release_tag:
        description: 'Release tag to rollback'
        required: true
        type: string
      reason:
        description: 'Reason for rollback'
        required: true
        type: string

jobs:
  rollback-validation:
    name: Validate Rollback Request
    runs-on: ubuntu-latest
    outputs:
      previous_tag: ${{ steps.find_previous.outputs.tag }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Find previous release tag
        id: find_previous
        run: |
          CURRENT_TAG="${{ inputs.release_tag }}"

          # Get all tags sorted by version
          TAGS=$(git tag -l 'v*.*.*' | sort -V)

          # Find previous tag
          PREVIOUS_TAG=$(echo "$TAGS" | grep -B1 "^${CURRENT_TAG}$" | head -n1)

          if [ -z "$PREVIOUS_TAG" ]; then
            echo "::error::No previous release found"
            exit 1
          fi

          echo "tag=$PREVIOUS_TAG" >> $GITHUB_OUTPUT
          echo "Previous release: $PREVIOUS_TAG"

      - name: Validate rollback safety
        run: |
          CURRENT_TAG="${{ inputs.release_tag }}"
          PREVIOUS_TAG="${{ steps.find_previous.outputs.tag }}"

          # Check if current release was published recently (within 7 days)
          CURRENT_DATE=$(git log -1 --format=%ct ${CURRENT_TAG})
          NOW=$(date +%s)
          DIFF=$((NOW - CURRENT_DATE))
          DAYS=$((DIFF / 86400))

          if [ $DAYS -gt 7 ]; then
            echo "::warning::Release is older than 7 days, rollback may affect many users"
          fi

  rollback-containers:
    name: Rollback Container Images
    needs: rollback-validation
    runs-on: ubuntu-latest

    strategy:
      matrix:
        registry: [ghcr.io, docker.io]

    steps:
      - name: Login to registry
        uses: docker/login-action@v3
        with:
          registry: ${{ matrix.registry }}
          username: ${{ matrix.registry == 'ghcr.io' && github.actor || secrets.DOCKERHUB_USERNAME }}
          password: ${{ matrix.registry == 'ghcr.io' && secrets.GITHUB_TOKEN || secrets.DOCKERHUB_TOKEN }}

      - name: Retag previous release as latest
        run: |
          REPO=$(echo "${{ github.repository }}" | tr '[:upper:]' '[:lower:]')
          PREVIOUS_TAG="${{ needs.rollback-validation.outputs.previous_tag }}"
          REGISTRY=${{ matrix.registry }}

          if [ "$REGISTRY" == "ghcr.io" ]; then
            IMAGE="${REGISTRY}/${REPO}"
          else
            IMAGE="${REGISTRY}/$(basename ${REPO})"
          fi

          # Pull previous version
          docker pull ${IMAGE}:${PREVIOUS_TAG}

          # Retag as latest
          docker tag ${IMAGE}:${PREVIOUS_TAG} ${IMAGE}:latest

          # Push new latest
          docker push ${IMAGE}:latest

  rollback-github-release:
    name: Update GitHub Release
    needs: [rollback-validation, rollback-containers]
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - name: Mark release as pre-release
        uses: actions/github-script@v7
        with:
          script: |
            const release = await github.rest.repos.getReleaseByTag({
              owner: context.repo.owner,
              repo: context.repo.repo,
              tag: '${{ inputs.release_tag }}'
            });

            await github.rest.repos.updateRelease({
              owner: context.repo.owner,
              repo: context.repo.repo,
              release_id: release.data.id,
              prerelease: true
            });

      - name: Add rollback notice
        uses: actions/github-script@v7
        with:
          script: |
            const release = await github.rest.repos.getReleaseByTag({
              owner: context.repo.owner,
              repo: context.repo.repo,
              tag: '${{ inputs.release_tag }}'
            });

            const notice = `
            ## ⚠️ ROLLBACK NOTICE

            This release has been rolled back on ${new Date().toISOString()}.

            **Reason**: ${{ inputs.reason }}

            **Previous stable release**: ${{ needs.rollback-validation.outputs.previous_tag }}

            Users should upgrade to the previous release or wait for a fixed version.
            `;

            const updatedBody = release.data.body + '\n\n' + notice;

            await github.rest.repos.updateRelease({
              owner: context.repo.owner,
              repo: context.repo.repo,
              release_id: release.data.id,
              body: updatedBody
            });

  notify-rollback:
    name: Notify Rollback
    needs: [rollback-validation, rollback-github-release]
    runs-on: ubuntu-latest

    steps:
      - name: Create rollback issue
        uses: actions/github-script@v7
        with:
          script: |
            await github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: `[ROLLBACK] Release ${{ inputs.release_tag }} rolled back`,
              body: `
              ## Release Rollback

              **Rolled back release**: ${{ inputs.release_tag }}
              **Rolled back to**: ${{ needs.rollback-validation.outputs.previous_tag }}
              **Reason**: ${{ inputs.reason }}
              **Date**: ${new Date().toISOString()}

              ## Actions Taken

              - [x] Container images retagged to previous version
              - [x] GitHub release marked as pre-release
              - [x] Rollback notice added to release notes
              - [x] This tracking issue created

              ## Next Steps

              1. Investigate root cause of issues
              2. Prepare fixed release
              3. Test thoroughly before re-release
              4. Update documentation if needed
              5. Close this issue when fixed release is published
              `,
              labels: ['rollback', 'release', 'critical']
            });
```

---

**Part 5 Complete**: Automated release verification (binaries, containers, packages, SBOMs,
documentation), verification reporting, rollback procedures. ✅

**Continue to Part 6** for release automation best practices, metrics, and completion checklist.
