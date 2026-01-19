<!-- file: docs/refactors/workflows/v2/implementation/release-workflows.md -->
<!-- version: 1.0.0 -->
<!-- guid: b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e -->
<!-- last-edited: 2026-01-19 -->

# Release Workflows Implementation Guide

## Overview

This guide provides comprehensive instructions for implementing branch-aware release workflows with
parallel release tracks, version targeting, and multi-platform builds.

**Target Audience**: Developers and release managers **Prerequisites**:

- Completed Phase 0 (Foundation) and Phase 2 (Release Consolidation)
- Understanding of semantic versioning
- GitHub Actions and repository permissions

## Quick Start

### Basic Release Workflow

Create `.github/workflows/release.yml`:

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'
      - 'v*-go-*'
      - 'v*-rust-*'

permissions:
  contents: write
  packages: write

jobs:
  determine-language:
    name: Determine Release Type
    runs-on: ubuntu-latest
    outputs:
      language: ${{ steps.detect.outputs.language }}
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Detect language
        id: detect
        run: |
          python .github/workflows/scripts/release_workflow.py detect-language

  release-go:
    name: Release Go
    needs: determine-language
    if: needs.determine-language.outputs.language == 'go'
    uses: ./.github/workflows/reusable-release-go.yml
    secrets: inherit

  release-rust:
    name: Release Rust
    needs: determine-language
    if: needs.determine-language.outputs.language == 'rust'
    uses: ./.github/workflows/reusable-release-rust.yml
    secrets: inherit
```

## Branch-Aware Releases

### Version Targeting

Releases automatically target the correct version based on the branch:

**Main branch** (`main`):

- Tags: `v1.2.3`
- Targets: Go 1.25, Python 3.14, Rust stable

**Stable branch** (`stable-1-go-1.24`):

- Tags: `v1.2.3-go-1.24`
- Targets: Go 1.24, Python 3.13/3.14

### Tag Format

Use appropriate tag formats for each branch:

```bash
# Main branch release
git tag v1.0.0
git push origin v1.0.0

# Stable-1 Go 1.24 release
git tag v1.0.0-go-1.24
git push origin v1.0.0-go-1.24

# Stable-1 Rust 1.75 release
git tag v1.0.0-rust-1.75
git push origin v1.0.0-rust-1.75
```

The release workflow automatically:

1. Detects branch from tag
2. Loads version configuration
3. Builds for appropriate versions
4. Creates branch-specific GitHub release

## Go Releases

### Configuration

Create `.github/workflows/reusable-release-go.yml`:

```yaml
# file: .github/workflows/reusable-release-go.yml
# version: 1.0.0

name: Reusable Go Release

on:
  workflow_call:
    inputs:
      go-version:
        description: 'Go version to use'
        required: false
        type: string
        default: ''

permissions:
  contents: write
  packages: write

jobs:
  build:
    name: Build Go Binaries
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        include:
          - os: ubuntu-latest
            goos: linux
            goarch: amd64
          - os: ubuntu-latest
            goos: linux
            goarch: arm64
          - os: macos-latest
            goos: darwin
            goarch: amd64
          - os: macos-latest
            goos: darwin
            goarch: arm64
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Determine Go version
        id: go-version
        run: |
          if [ -n "${{ inputs.go-version }}" ]; then
            echo "version=${{ inputs.go-version }}" >> $GITHUB_OUTPUT
          else
            python .github/workflows/scripts/release_workflow.py get-version \
              --language go
          fi

      - name: Set up Go
        uses: actions/setup-go@v5
        with:
          go-version: ${{ steps.go-version.outputs.version }}

      - name: Build
        env:
          GOOS: ${{ matrix.goos }}
          GOARCH: ${{ matrix.goarch }}
        run: |
          go build -o bin/app-${{ matrix.goos }}-${{ matrix.goarch }} ./cmd/app

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: app-${{ matrix.goos }}-${{ matrix.goarch }}
          path: bin/app-${{ matrix.goos }}-${{ matrix.goarch }}

  release:
    name: Create Release
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Download artifacts
        uses: actions/download-artifact@v4

      - name: Create checksums
        run: |
          for dir in app-*; do
            cd "$dir"
            shasum -a 256 * > ../checksums-$dir.txt
            cd ..
          done

      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: |
            app-*/app-*
            checksums-*.txt
          body: |
            Release ${{ github.ref_name }}

            Built with Go ${{ needs.build.outputs.go-version }}
```

### Go Module Releases

For libraries, update go.mod and create module-specific tags:

```bash
# Release main module
git tag v1.0.0
git push origin v1.0.0

# Release submodule
git tag pkg/submodule/v1.0.0
git push origin pkg/submodule/v1.0.0
```

Configure module release in workflow:

```yaml
jobs:
  release-modules:
    name: Release Go Modules
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Detect modules
        id: modules
        run: |
          python .github/workflows/scripts/release_workflow.py detect-modules

      - name: Update module versions
        run: |
          for module in ${{ steps.modules.outputs.modules }}; do
            echo "Releasing module: $module"
            # Update go.mod version references
            # Create module-specific tag
          done
```

## Rust Releases

### Configuration

Create `.github/workflows/reusable-release-rust.yml`:

```yaml
# file: .github/workflows/reusable-release-rust.yml
# version: 1.0.0

name: Reusable Rust Release

on:
  workflow_call:
    inputs:
      rust-version:
        description: 'Rust version to use'
        required: false
        type: string
        default: 'stable'

permissions:
  contents: write
  packages: write

jobs:
  build:
    name: Build Rust Binaries
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        include:
          - os: ubuntu-latest
            target: x86_64-unknown-linux-gnu
          - os: ubuntu-latest
            target: aarch64-unknown-linux-gnu
          - os: ubuntu-latest
            target: x86_64-unknown-linux-musl
          - os: macos-latest
            target: x86_64-apple-darwin
          - os: macos-latest
            target: aarch64-apple-darwin
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Rust
        uses: actions-rust-lang/setup-rust-toolchain@v1
        with:
          toolchain: ${{ inputs.rust-version }}
          target: ${{ matrix.target }}

      - name: Install cross-compilation tools
        if: matrix.os == 'ubuntu-latest'
        run: |
          sudo apt-get update
          sudo apt-get install -y gcc-aarch64-linux-gnu musl-tools

      - name: Build
        run: |
          cargo build --release --target ${{ matrix.target }}

      - name: Package binary
        run: |
          cd target/${{ matrix.target }}/release
          tar czf app-${{ matrix.target }}.tar.gz app

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: app-${{ matrix.target }}
          path: target/${{ matrix.target }}/release/app-${{ matrix.target }}.tar.gz

  crates-io:
    name: Publish to crates.io
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Rust
        uses: actions-rust-lang/setup-rust-toolchain@v1

      - name: Publish
        env:
          CARGO_REGISTRY_TOKEN: ${{ secrets.CARGO_REGISTRY_TOKEN }}
        run: cargo publish

  release:
    name: Create Release
    needs: [build, crates-io]
    runs-on: ubuntu-latest
    steps:
      - name: Download artifacts
        uses: actions/download-artifact@v4

      - name: Create checksums
        run: |
          shasum -a 256 **/*.tar.gz > checksums.txt

      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: |
            **/*.tar.gz
            checksums.txt
```

### Cargo Version Management

Update Cargo.toml version automatically:

```yaml
jobs:
  bump-version:
    name: Bump Cargo Version
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Update version
        run: |
          VERSION="${{ github.ref_name }}"
          VERSION="${VERSION#v}"  # Remove 'v' prefix

          # Update Cargo.toml
          sed -i "s/^version = .*/version = \"$VERSION\"/" Cargo.toml

          # Commit if changed
          if git diff --quiet Cargo.toml; then
            echo "Version already correct"
          else
            git config user.name "GitHub Actions"
            git config user.email "actions@github.com"
            git add Cargo.toml
            git commit -m "chore(release): bump version to $VERSION"
            git push
          fi
```

## GitHub Packages Publishing

### Container Images

Publish Docker images to GitHub Container Registry:

```yaml
jobs:
  docker:
    name: Build and Push Docker Image
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=semver,pattern={{major}}
            type=ref,event=branch
            type=sha

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
```

### Go Modules to GitHub Packages

Publish Go modules:

```yaml
jobs:
  publish-go-module:
    name: Publish Go Module
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Go
        uses: actions/setup-go@v5
        with:
          go-version: '1.25'

      - name: Publish to GitHub Packages
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          go list -m github.com/${{ github.repository }}@${{ github.ref_name }}
```

## Version Automation

### Automated Version Bumping

Use release-please or semantic-release:

```yaml
name: Release Please

on:
  push:
    branches: [main, 'stable-1-**']

permissions:
  contents: write
  pull-requests: write

jobs:
  release-please:
    runs-on: ubuntu-latest
    steps:
      - uses: google-github-actions/release-please-action@v3
        with:
          release-type: go
          package-name: myapp
          include-v-in-tag: true
```

### Changelog Generation

Automatically generate changelogs:

```yaml
jobs:
  changelog:
    name: Generate Changelog
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0 # Full history for changelog

      - name: Generate changelog
        run: |
          python .github/workflows/scripts/release_workflow.py generate-changelog \
            --from-tag v1.0.0 \
            --to-tag v1.1.0 \
            --output CHANGELOG.md

      - name: Upload changelog
        uses: actions/upload-artifact@v4
        with:
          name: changelog
          path: CHANGELOG.md
```

## Multi-Platform Builds

### Cross-Compilation Setup

**Go cross-compilation**:

```yaml
strategy:
  matrix:
    include:
      - goos: linux
        goarch: amd64
      - goos: linux
        goarch: arm64
      - goos: darwin
        goarch: amd64
      - goos: darwin
        goarch: arm64

steps:
  - name: Build
    env:
      GOOS: ${{ matrix.goos }}
      GOARCH: ${{ matrix.goarch }}
      CGO_ENABLED: 0
    run: |
      go build -ldflags="-s -w" -o app-${{ matrix.goos }}-${{ matrix.goarch }}
```

**Rust cross-compilation**:

```yaml
strategy:
  matrix:
    include:
      - target: x86_64-unknown-linux-gnu
        linker: gcc
      - target: aarch64-unknown-linux-gnu
        linker: aarch64-linux-gnu-gcc
      - target: x86_64-unknown-linux-musl
        linker: musl-gcc

steps:
  - name: Build
    env:
      CARGO_TARGET_${{ matrix.target_upper }}_LINKER: ${{ matrix.linker }}
    run: |
      cargo build --release --target ${{ matrix.target }}
```

## Release Verification

### Automated Testing

Test releases before publishing:

```yaml
jobs:
  test-release:
    name: Test Release Build
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
    steps:
      - name: Download release binary
        uses: actions/download-artifact@v4

      - name: Test binary
        run: |
          chmod +x app-*
          ./app-* --version
          ./app-* --help

      - name: Run smoke tests
        run: |
          ./app-* test --quick
```

### Checksums and Signatures

Generate and verify checksums:

```yaml
jobs:
  checksums:
    name: Generate Checksums
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Download all artifacts
        uses: actions/download-artifact@v4

      - name: Generate SHA256 checksums
        run: |
          shasum -a 256 **/* > SHA256SUMS.txt

      - name: Generate SHA512 checksums
        run: |
          shasum -a 512 **/* > SHA512SUMS.txt

      - name: Upload checksums
        uses: actions/upload-artifact@v4
        with:
          name: checksums
          path: SHA*SUMS.txt
```

## Release Notes

### Automated Release Notes

Generate release notes from commits:

```yaml
jobs:
  release-notes:
    name: Generate Release Notes
    runs-on: ubuntu-latest
    outputs:
      notes: ${{ steps.notes.outputs.notes }}
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Generate notes
        id: notes
        run: |
          NOTES=$(python .github/workflows/scripts/release_workflow.py release-notes \
            --tag ${{ github.ref_name }})
          echo "notes<<EOF" >> $GITHUB_OUTPUT
          echo "$NOTES" >> $GITHUB_OUTPUT
          echo "EOF" >> $GITHUB_OUTPUT

      - name: Create release
        uses: softprops/action-gh-release@v1
        with:
          body: ${{ steps.notes.outputs.notes }}
```

### Release Template

Create `.github/release-template.md`:

```markdown
## What's Changed

$CHANGES

## Installation

### Go

\`\`\`bash go install github.com/${{ github.repository }}/cmd/app@${{ github.ref_name }} \`\`\`

### Rust

\`\`\`bash cargo install app --version ${{ github.ref_name }} \`\`\`

### Binary

Download from assets below.

## Checksums

See `SHA256SUMS.txt` in assets.

**Full Changelog**: https://github.com/${{ github.repository
}}/compare/v$PREVIOUS_VERSION...${{ github.ref_name }}
```

## Branch-Specific Releases

### Parallel Release Tracks

Maintain releases for multiple versions:

```text
main branch (v1.5.0)
├── Go 1.25
├── Python 3.14
└── Rust stable

stable-1-go-1.24 (v1.4.2-go-1.24)
├── Go 1.24
├── Python 3.13
└── Rust stable-1

stable-1-go-1.23 (v1.3.5-go-1.23)
├── Go 1.23
├── Python 3.12
└── Rust stable-2
```

### Release Strategy

1. **Main branch**: New features, latest versions
2. **Stable-1 branches**: Bug fixes only, locked versions
3. **Backports**: Cherry-pick fixes to stable branches

```bash
# Cherry-pick fix to stable branch
git checkout stable-1-go-1.24
git cherry-pick abc123
git push origin stable-1-go-1.24

# Create stable branch release
git tag v1.4.3-go-1.24
git push origin v1.4.3-go-1.24
```

## Troubleshooting

### Release Fails on Version Mismatch

**Problem**: Version in code doesn't match tag

**Solution**:

```yaml
- name: Validate version
  run: |
    TAG_VERSION="${{ github.ref_name }}"
    CODE_VERSION=$(grep 'version =' Cargo.toml | cut -d'"' -f2)

    if [ "v$CODE_VERSION" != "$TAG_VERSION" ]; then
      echo "Version mismatch: tag=$TAG_VERSION code=$CODE_VERSION"
      exit 1
    fi
```

### Cross-Compilation Errors

**Problem**: Linker errors on cross-compilation

**Solution for Rust**:

```toml
# .cargo/config.toml
[target.aarch64-unknown-linux-gnu]
linker = "aarch64-linux-gnu-gcc"

[target.x86_64-unknown-linux-musl]
linker = "musl-gcc"
```

**Solution for Go**:

```yaml
- name: Install cross-compile tools
  run: |
    sudo apt-get install -y gcc-aarch64-linux-gnu
```

### Artifact Upload Fails

**Problem**: Artifacts exceed size limit

**Solution**:

```yaml
- name: Compress artifacts
  run: |
    gzip -9 bin/*

- name: Upload compressed
  uses: actions/upload-artifact@v4
  with:
    name: binaries
    path: bin/*.gz
    compression-level: 0 # Already compressed
```

## Best Practices

1. **Semantic Versioning**: Follow semver strictly
2. **Branch-Aware Tags**: Use version suffixes for stable branches
3. **Automated Testing**: Test all builds before release
4. **Checksums**: Always generate and publish checksums
5. **Release Notes**: Auto-generate from conventional commits
6. **Parallel Tracks**: Maintain stable branches for major versions
7. **Backport Policy**: Clear rules for what gets backported
8. **Deprecation**: Document deprecations in release notes

## Examples

### Complete Release Workflow

See `examples/complete-release.yml` for full implementation.

### Language-Specific Examples

- `examples/go-release.yml` - Go module and binary releases
- `examples/rust-release.yml` - Cargo and binary releases
- `examples/docker-release.yml` - Container image releases

## Next Steps

1. Configure release workflow with branch awareness
2. Set up version automation (release-please)
3. Test cross-platform builds
4. Configure GitHub Packages publishing
5. Establish backport policy
6. Read [Testing Strategy Guide](testing-strategy.md)

## References

- [Phase 2: Release Consolidation](../phases/phase-2-release-consolidation.md)
- [Helper Scripts API](../reference/helper-scripts-api.md)
- [Configuration Schema](../reference/config-schema.md)
- [Migration Guide](../operations/migration-guide.md)
