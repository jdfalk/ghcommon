<!-- file: docs/cross-registry-todos/task-11/t11-part2.md -->
<!-- version: 1.0.0 -->
<!-- guid: t11-artifact-management-part2-q3r4s5t6-u7v8 -->

# Task 11 Part 2: Comprehensive Release Workflow Implementation

## Universal Release Workflow

Create a reusable release workflow that handles all artifact types:

```yaml
# file: .github/workflows/reusable-release.yml
# version: 1.0.0
# guid: reusable-release-workflow

name: Reusable Release Workflow

on:
  workflow_call:
    inputs:
      language:
        description: 'Primary language: rust, go, python, javascript'
        required: true
        type: string
      platforms:
        description: 'JSON array of target platforms'
        required: false
        type: string
        default: '["linux-x86_64"]'
      publish-packages:
        description: 'Publish to package registries'
        required: false
        type: boolean
        default: true
      create-installers:
        description: 'Create platform installers'
        required: false
        type: boolean
        default: false
    secrets:
      CRATES_IO_TOKEN:
        required: false
      NPM_TOKEN:
        required: false
      PYPI_TOKEN:
        required: false

jobs:
  prepare-release:
    name: Prepare Release
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.version.outputs.version }}
      platforms: ${{ steps.platforms.outputs.matrix }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Extract version from tag
        id: version
        run: |
          VERSION=${GITHUB_REF#refs/tags/v}
          echo "version=$VERSION" >> $GITHUB_OUTPUT
          echo "Version: $VERSION"

      - name: Parse platforms matrix
        id: platforms
        run: |
          echo "matrix=${{ inputs.platforms }}" >> $GITHUB_OUTPUT

  build-artifacts:
    name: Build ${{ matrix.platform }}
    needs: prepare-release
    runs-on: ${{ matrix.os }}

    strategy:
      fail-fast: false
      matrix:
        include:
          # Linux x86_64
          - platform: linux-x86_64
            os: ubuntu-latest
            target: x86_64-unknown-linux-gnu
            use-cross: false

          # Linux aarch64
          - platform: linux-aarch64
            os: ubuntu-latest
            target: aarch64-unknown-linux-gnu
            use-cross: true

          # Linux musl x86_64
          - platform: linux-x86_64-musl
            os: ubuntu-latest
            target: x86_64-unknown-linux-musl
            use-cross: true

          # macOS x86_64
          - platform: macos-x86_64
            os: macos-latest
            target: x86_64-apple-darwin
            use-cross: false

          # macOS aarch64
          - platform: macos-aarch64
            os: macos-latest
            target: aarch64-apple-darwin
            use-cross: false

          # Windows x86_64
          - platform: windows-x86_64
            os: windows-latest
            target: x86_64-pc-windows-msvc
            use-cross: false

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install Rust toolchain
        if: inputs.language == 'rust'
        uses: dtolnay/rust-toolchain@stable
        with:
          targets: ${{ matrix.target }}

      - name: Install cross
        if: matrix.use-cross && inputs.language == 'rust'
        run: cargo install cross --git https://github.com/cross-rs/cross

      - name: Cache cargo registry
        if: inputs.language == 'rust'
        uses: actions/cache@v4
        with:
          path: |
            ~/.cargo/registry
            ~/.cargo/git
          key: ${{ runner.os }}-cargo-${{ hashFiles('**/Cargo.lock') }}

      - name: Cache build artifacts
        if: inputs.language == 'rust'
        uses: actions/cache@v4
        with:
          path: target/
          key: ${{ runner.os }}-${{ matrix.target }}-release-${{ hashFiles('**/Cargo.lock') }}

      - name: Build binary (Rust)
        if: inputs.language == 'rust'
        run: |
          if [ "${{ matrix.use-cross }}" = "true" ]; then
            cross build --release --target ${{ matrix.target }}
          else
            cargo build --release --target ${{ matrix.target }}
          fi
        shell: bash

      - name: Prepare binary artifact
        run: |
          mkdir -p artifacts

          # Get binary name from Cargo.toml or package.json
          if [ -f "Cargo.toml" ]; then
            BIN_NAME=$(grep '^name = ' Cargo.toml | head -n1 | cut -d'"' -f2)
            SRC_PATH="target/${{ matrix.target }}/release/$BIN_NAME"

            # Windows binaries have .exe extension
            if [[ "${{ matrix.platform }}" == windows-* ]]; then
              SRC_PATH="${SRC_PATH}.exe"
            fi
          else
            echo "Error: Could not determine binary name"
            exit 1
          fi

          # Copy binary to artifacts directory
          cp "$SRC_PATH" "artifacts/${BIN_NAME}-${{ matrix.platform }}"

          # Generate checksum
          cd artifacts
          sha256sum "${BIN_NAME}-${{ matrix.platform }}" > "${BIN_NAME}-${{ matrix.platform }}.sha256"
        shell: bash

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: binary-${{ matrix.platform }}
          path: artifacts/*
          retention-days: 7

  generate-sbom:
    name: Generate SBOMs
    needs: build-artifacts
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install Syft
        run: |
          curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin

      - name: Generate SPDX SBOM
        run: |
          syft . -o spdx-json > sbom-spdx.json

      - name: Generate CycloneDX SBOM
        run: |
          syft . -o cyclonedx-json > sbom-cyclonedx.json

      - name: Upload SBOMs
        uses: actions/upload-artifact@v4
        with:
          name: sboms
          path: |
            sbom-*.json
          retention-days: 90

  sign-artifacts:
    name: Sign Artifacts
    needs: [build-artifacts, generate-sbom]
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read

    steps:
      - name: Download all artifacts
        uses: actions/download-artifact@v4
        with:
          path: artifacts/

      - name: Install Cosign
        uses: sigstore/cosign-installer@v3

      - name: Sign artifacts with Cosign
        run: |
          for artifact in artifacts/binary-*/*; do
            if [[ "$artifact" != *.sha256 ]]; then
              echo "Signing: $artifact"
              cosign sign-blob --yes \
                --output-signature "${artifact}.sig" \
                --output-certificate "${artifact}.pem" \
                "$artifact"
            fi
          done

      - name: Sign SBOMs
        run: |
          for sbom in artifacts/sboms/*.json; do
            echo "Signing SBOM: $sbom"
            cosign sign-blob --yes \
              --output-signature "${sbom}.sig" \
              --output-certificate "${sbom}.pem" \
              "$sbom"
          done

      - name: Upload signed artifacts
        uses: actions/upload-artifact@v4
        with:
          name: signed-artifacts
          path: artifacts/**
          retention-days: 7

  generate-release-notes:
    name: Generate Release Notes
    needs: prepare-release
    runs-on: ubuntu-latest
    outputs:
      notes: ${{ steps.notes.outputs.notes }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Install git-cliff
        run: |
          wget https://github.com/orhun/git-cliff/releases/latest/download/git-cliff-0.11.0-x86_64-unknown-linux-gnu.tar.gz
          tar -xzf git-cliff-0.11.0-x86_64-unknown-linux-gnu.tar.gz
          sudo mv git-cliff /usr/local/bin/

      - name: Generate release notes
        id: notes
        run: |
          # Get previous tag
          PREV_TAG=$(git describe --tags --abbrev=0 HEAD^ 2>/dev/null || echo "")

          if [ -z "$PREV_TAG" ]; then
            # First release
            git-cliff --latest --strip all > release-notes.md
          else
            # Generate notes between tags
            git-cliff --latest --strip all > release-notes.md
          fi

          # Set output (escape newlines for GitHub Actions)
          echo "notes<<EOF" >> $GITHUB_OUTPUT
          cat release-notes.md >> $GITHUB_OUTPUT
          echo "EOF" >> $GITHUB_OUTPUT

      - name: Upload release notes
        uses: actions/upload-artifact@v4
        with:
          name: release-notes
          path: release-notes.md
          retention-days: 7

  create-release:
    name: Create GitHub Release
    needs: [prepare-release, sign-artifacts, generate-release-notes]
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Download all artifacts
        uses: actions/download-artifact@v4
        with:
          path: release-artifacts/

      - name: Create release archives
        run: |
          cd release-artifacts

          # Create archives for each platform
          for platform_dir in binary-*; do
            platform="${platform_dir#binary-}"

            # Create tar.gz for Unix platforms
            if [[ "$platform" != windows-* ]]; then
              tar -czf "../${platform}.tar.gz" -C "$platform_dir" .
            else
              # Create zip for Windows
              (cd "$platform_dir" && zip -r "../../${platform}.zip" .)
            fi
          done

          cd ..

          # Generate checksums for archives
          sha256sum *.tar.gz *.zip > checksums.txt 2>/dev/null || true

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          name: Release v${{ needs.prepare-release.outputs.version }}
          body: ${{ needs.generate-release-notes.outputs.notes }}
          files: |
            *.tar.gz
            *.zip
            checksums.txt
            release-artifacts/sboms/*.json
            release-artifacts/sboms/*.sig
            release-artifacts/sboms/*.pem
            release-artifacts/binary-*/*
            release-artifacts/signed-artifacts/**/*
          draft: false
          prerelease: false
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  publish-crate:
    name: Publish to crates.io
    if: inputs.language == 'rust' && inputs.publish-packages
    needs: create-release
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install Rust toolchain
        uses: dtolnay/rust-toolchain@stable

      - name: Publish to crates.io
        run: cargo publish --token ${{ secrets.CRATES_IO_TOKEN }}
        env:
          CARGO_REGISTRY_TOKEN: ${{ secrets.CRATES_IO_TOKEN }}
```

## git-cliff Configuration

Create `.cliff.toml` for release notes generation:

```toml
# file: cliff.toml
# version: 1.0.0
# guid: git-cliff-config

[changelog]
# changelog header
header = """
# Changelog\n
All notable changes to this project will be documented in this file.\n
"""
# template for the changelog body
body = """
{% if version %}\
    ## [{{ version | trim_start_matches(pat="v") }}] - {{ timestamp | date(format="%Y-%m-%d") }}
{% else %}\
    ## [unreleased]
{% endif %}\
{% for group, commits in commits | group_by(attribute="group") %}
    ### {{ group | upper_first }}
    {% for commit in commits %}
        - {% if commit.breaking %}[**breaking**] {% endif %}{{ commit.message | upper_first }}\
    {% endfor %}
{% endfor %}\n
"""
# remove the leading and trailing whitespace from the template
trim = true
# changelog footer
footer = """
<!-- generated by git-cliff -->
"""

[git]
# parse the commits based on https://www.conventionalcommits.org
conventional_commits = true
# filter out the commits that are not conventional
filter_unconventional = true
# process each line of a commit as an individual commit
split_commits = false
# regex for preprocessing the commit messages
commit_preprocessors = [
    { pattern = '\((\w+\s)?#([0-9]+)\)', replace = "([#${2}](https://github.com/jdfalk/repo/issues/${2}))"},
]
# regex for parsing and grouping commits
commit_parsers = [
    { message = "^feat", group = "Features"},
    { message = "^fix", group = "Bug Fixes"},
    { message = "^doc", group = "Documentation"},
    { message = "^perf", group = "Performance"},
    { message = "^refactor", group = "Refactor"},
    { message = "^style", group = "Styling"},
    { message = "^test", group = "Testing"},
    { message = "^chore\\(release\\): prepare for", skip = true},
    { message = "^chore", group = "Miscellaneous Tasks"},
    { body = ".*security", group = "Security"},
]
# protect breaking changes from being skipped due to matching a skipping commit_parser
protect_breaking_commits = false
# filter out the commits that are not matched by commit parsers
filter_commits = false
# glob pattern for matching git tags
tag_pattern = "v[0-9]*"
# regex for skipping tags
skip_tags = "v0.1.0-beta.1"
# regex for ignoring tags
ignore_tags = ""
# sort the tags topologically
topo_order = false
# sort the commits inside sections by oldest/newest order
sort_commits = "oldest"
```

---

**Part 2 Complete**: Comprehensive release workflow with cross-compilation, SBOM generation,
artifact signing, and automated release notes. ✅

**Continue to Part 3** for container image releases, multi-arch Docker builds, and registry
publishing.
