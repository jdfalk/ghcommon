<!-- file: docs/cross-registry-todos/task-11/t11-part4.md -->
<!-- version: 1.0.0 -->
<!-- guid: t11-artifact-management-part4-c5d6e7f8-g9h0 -->

# Task 11 Part 4: System Package Generation and Distribution

## Debian Package (.deb) Generation

```yaml
# file: .github/workflows/release-deb.yml
# version: 1.0.0
# guid: release-deb-workflow

name: Release Debian Packages

on:
  push:
    tags:
      - 'v*.*.*'
  workflow_dispatch:

jobs:
  build-deb:
    name: Build Debian Package
    runs-on: ubuntu-latest

    strategy:
      matrix:
        arch: [amd64, arm64, armhf]

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y \
            build-essential \
            debhelper \
            devscripts \
            fakeroot \
            lintian

      - name: Extract version
        id: version
        run: |
          VERSION=${GITHUB_REF#refs/tags/v}
          echo "version=$VERSION" >> $GITHUB_OUTPUT

      - name: Create debian package structure
        run: |
          PKG_NAME=$(grep '^name = ' Cargo.toml | head -n1 | cut -d'"' -f2)
          VERSION=${{ steps.version.outputs.version }}
          ARCH=${{ matrix.arch }}

          mkdir -p debian-build/${PKG_NAME}_${VERSION}-1_${ARCH}/DEBIAN
          mkdir -p debian-build/${PKG_NAME}_${VERSION}-1_${ARCH}/usr/local/bin
          mkdir -p debian-build/${PKG_NAME}_${VERSION}-1_${ARCH}/usr/share/doc/${PKG_NAME}
          mkdir -p debian-build/${PKG_NAME}_${VERSION}-1_${ARCH}/lib/systemd/system

      - name: Create control file
        run: |
          PKG_NAME=$(grep '^name = ' Cargo.toml | head -n1 | cut -d'"' -f2)
          VERSION=${{ steps.version.outputs.version }}
          ARCH=${{ matrix.arch }}
          DESCRIPTION=$(grep '^description = ' Cargo.toml | head -n1 | cut -d'"' -f2)

          cat > debian-build/${PKG_NAME}_${VERSION}-1_${ARCH}/DEBIAN/control <<EOF
          Package: ${PKG_NAME}
          Version: ${VERSION}
          Section: utils
          Priority: optional
          Architecture: ${ARCH}
          Maintainer: jdfalk <jdfalk@users.noreply.github.com>
          Description: ${DESCRIPTION}
          Homepage: https://github.com/${{ github.repository }}
          Depends: libc6 (>= 2.31)
          EOF

      - name: Create postinst script
        run: |
          PKG_NAME=$(grep '^name = ' Cargo.toml | head -n1 | cut -d'"' -f2)
          VERSION=${{ steps.version.outputs.version }}
          ARCH=${{ matrix.arch }}

          cat > debian-build/${PKG_NAME}_${VERSION}-1_${ARCH}/DEBIAN/postinst <<'EOF'
          #!/bin/bash
          set -e

          # Reload systemd daemon if systemd is present
          if [ -x /bin/systemctl ]; then
            systemctl daemon-reload || true
          fi

          exit 0
          EOF

          chmod 755 debian-build/${PKG_NAME}_${VERSION}-1_${ARCH}/DEBIAN/postinst

      - name: Download binary
        uses: actions/download-artifact@v4
        with:
          name: binary-linux-${{ matrix.arch }}
          path: binaries/

      - name: Copy binary to package
        run: |
          PKG_NAME=$(grep '^name = ' Cargo.toml | head -n1 | cut -d'"' -f2)
          VERSION=${{ steps.version.outputs.version }}
          ARCH=${{ matrix.arch }}

          cp binaries/${PKG_NAME}-linux-${ARCH} \
             debian-build/${PKG_NAME}_${VERSION}-1_${ARCH}/usr/local/bin/${PKG_NAME}
          chmod 755 debian-build/${PKG_NAME}_${VERSION}-1_${ARCH}/usr/local/bin/${PKG_NAME}

      - name: Create copyright file
        run: |
          PKG_NAME=$(grep '^name = ' Cargo.toml | head -n1 | cut -d'"' -f2)
          VERSION=${{ steps.version.outputs.version }}
          ARCH=${{ matrix.arch }}

          cat > debian-build/${PKG_NAME}_${VERSION}-1_${ARCH}/usr/share/doc/${PKG_NAME}/copyright <<EOF
          Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
          Upstream-Name: ${PKG_NAME}
          Source: https://github.com/${{ github.repository }}

          Files: *
          Copyright: $(date +%Y) jdfalk
          License: MIT
          EOF

      - name: Build deb package
        run: |
          PKG_NAME=$(grep '^name = ' Cargo.toml | head -n1 | cut -d'"' -f2)
          VERSION=${{ steps.version.outputs.version }}
          ARCH=${{ matrix.arch }}

          cd debian-build
          dpkg-deb --build ${PKG_NAME}_${VERSION}-1_${ARCH}

          # Run lintian to check package
          lintian ${PKG_NAME}_${VERSION}-1_${ARCH}.deb || true

      - name: Upload deb package
        uses: actions/upload-artifact@v4
        with:
          name: deb-${{ matrix.arch }}
          path: debian-build/*.deb
          retention-days: 7
```

## RPM Package Generation

```yaml
# file: .github/workflows/release-rpm.yml
# version: 1.0.0
# guid: release-rpm-workflow

name: Release RPM Packages

on:
  push:
    tags:
      - 'v*.*.*'
  workflow_dispatch:

jobs:
  build-rpm:
    name: Build RPM Package
    runs-on: ubuntu-latest
    container:
      image: fedora:latest

    strategy:
      matrix:
        arch: [x86_64, aarch64]

    steps:
      - name: Install dependencies
        run: |
          dnf install -y \
            rpm-build \
            rpmdevtools \
            git

      - name: Checkout code
        uses: actions/checkout@v4

      - name: Extract version
        id: version
        run: |
          VERSION=${GITHUB_REF#refs/tags/v}
          echo "version=$VERSION" >> $GITHUB_OUTPUT

      - name: Set up RPM build environment
        run: |
          rpmdev-setuptree

      - name: Create RPM spec file
        run: |
          PKG_NAME=$(grep '^name = ' Cargo.toml | head -n1 | cut -d'"' -f2)
          VERSION=${{ steps.version.outputs.version }}
          DESCRIPTION=$(grep '^description = ' Cargo.toml | head -n1 | cut -d'"' -f2)

          cat > ~/rpmbuild/SPECS/${PKG_NAME}.spec <<EOF
          Name:           ${PKG_NAME}
          Version:        ${VERSION}
          Release:        1%{?dist}
          Summary:        ${DESCRIPTION}

          License:        MIT
          URL:            https://github.com/${{ github.repository }}
          Source0:        %{name}-%{version}.tar.gz

          BuildArch:      ${{ matrix.arch }}

          %description
          ${DESCRIPTION}

          %prep
          %setup -q

          %build
          # Binary is pre-built

          %install
          mkdir -p %{buildroot}%{_bindir}
          install -m 755 ${PKG_NAME} %{buildroot}%{_bindir}/${PKG_NAME}

          %files
          %{_bindir}/${PKG_NAME}

          %changelog
          * $(date +'%a %b %d %Y') jdfalk <jdfalk@users.noreply.github.com> - ${VERSION}-1
          - Release ${VERSION}
          EOF

      - name: Download binary
        uses: actions/download-artifact@v4
        with:
          name: binary-linux-${{ matrix.arch }}
          path: binaries/

      - name: Prepare sources
        run: |
          PKG_NAME=$(grep '^name = ' Cargo.toml | head -n1 | cut -d'"' -f2)
          VERSION=${{ steps.version.outputs.version }}

          mkdir -p ~/rpmbuild/BUILD/${PKG_NAME}-${VERSION}
          cp binaries/${PKG_NAME}-linux-${{ matrix.arch }} \
             ~/rpmbuild/BUILD/${PKG_NAME}-${VERSION}/${PKG_NAME}

      - name: Build RPM
        run: |
          PKG_NAME=$(grep '^name = ' Cargo.toml | head -n1 | cut -d'"' -f2)
          rpmbuild -bb ~/rpmbuild/SPECS/${PKG_NAME}.spec

      - name: Upload RPM package
        uses: actions/upload-artifact@v4
        with:
          name: rpm-${{ matrix.arch }}
          path: ~/rpmbuild/RPMS/${{ matrix.arch }}/*.rpm
          retention-days: 7
```

## Homebrew Formula Generation

```yaml
# file: .github/workflows/release-homebrew.yml
# version: 1.0.0
# guid: release-homebrew-workflow

name: Update Homebrew Formula

on:
  release:
    types: [published]
  workflow_dispatch:

jobs:
  update-formula:
    name: Update Homebrew Formula
    runs-on: macos-latest

    steps:
      - name: Checkout homebrew tap
        uses: actions/checkout@v4
        with:
          repository: jdfalk/homebrew-tap
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract release info
        id: release
        run: |
          VERSION=${GITHUB_REF#refs/tags/v}
          echo "version=$VERSION" >> $GITHUB_OUTPUT

          # Get release URL
          RELEASE_URL="https://github.com/${{ github.repository }}/releases/download/v${VERSION}"
          echo "release_url=$RELEASE_URL" >> $GITHUB_OUTPUT

      - name: Download release artifacts
        run: |
          VERSION=${{ steps.release.outputs.version }}
          RELEASE_URL=${{ steps.release.outputs.release_url }}

          # Download macOS binaries
          curl -L -o macos-x86_64.tar.gz "${RELEASE_URL}/macos-x86_64.tar.gz"
          curl -L -o macos-aarch64.tar.gz "${RELEASE_URL}/macos-aarch64.tar.gz"

      - name: Calculate checksums
        id: checksums
        run: |
          SHA256_X86_64=$(shasum -a 256 macos-x86_64.tar.gz | cut -d' ' -f1)
          SHA256_AARCH64=$(shasum -a 256 macos-aarch64.tar.gz | cut -d' ' -f1)

          echo "sha256_x86_64=$SHA256_X86_64" >> $GITHUB_OUTPUT
          echo "sha256_aarch64=$SHA256_AARCH64" >> $GITHUB_OUTPUT

      - name: Create/Update Homebrew formula
        run: |
          PKG_NAME=$(basename ${{ github.repository }})
          VERSION=${{ steps.release.outputs.version }}
          RELEASE_URL=${{ steps.release.outputs.release_url }}
          SHA256_X86_64=${{ steps.checksums.outputs.sha256_x86_64 }}
          SHA256_AARCH64=${{ steps.checksums.outputs.sha256_aarch64 }}

          mkdir -p Formula

          cat > Formula/${PKG_NAME}.rb <<EOF
          class $(echo $PKG_NAME | sed 's/-/ /g' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) tolower(substr($i,2))}1' | tr -d ' ') < Formula
            desc "Description of ${PKG_NAME}"
            homepage "https://github.com/${{ github.repository }}"
            version "${VERSION}"

            on_macos do
              if Hardware::CPU.intel?
                url "${RELEASE_URL}/macos-x86_64.tar.gz"
                sha256 "${SHA256_X86_64}"
              elsif Hardware::CPU.arm?
                url "${RELEASE_URL}/macos-aarch64.tar.gz"
                sha256 "${SHA256_AARCH64}"
              end
            end

            def install
              bin.install "${PKG_NAME}"
            end

            test do
              system "#{bin}/${PKG_NAME}", "--version"
            end
          end
          EOF

      - name: Commit and push formula
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

          PKG_NAME=$(basename ${{ github.repository }})
          VERSION=${{ steps.release.outputs.version }}

          git add Formula/${PKG_NAME}.rb
          git commit -m "chore(formula): update ${PKG_NAME} to v${VERSION}"
          git push
```

## AppImage Generation (Linux Universal)

```yaml
# file: .github/workflows/release-appimage.yml
# version: 1.0.0
# guid: release-appimage-workflow

name: Release AppImage

on:
  push:
    tags:
      - 'v*.*.*'
  workflow_dispatch:

jobs:
  build-appimage:
    name: Build AppImage
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Extract version
        id: version
        run: |
          VERSION=${GITHUB_REF#refs/tags/v}
          echo "version=$VERSION" >> $GITHUB_OUTPUT

      - name: Download binary
        uses: actions/download-artifact@v4
        with:
          name: binary-linux-x86_64
          path: binaries/

      - name: Install AppImage tools
        run: |
          wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
          chmod +x appimagetool-x86_64.AppImage
          sudo mv appimagetool-x86_64.AppImage /usr/local/bin/appimagetool

      - name: Create AppDir structure
        run: |
          PKG_NAME=$(grep '^name = ' Cargo.toml | head -n1 | cut -d'"' -f2)

          mkdir -p AppDir/usr/bin
          mkdir -p AppDir/usr/share/applications
          mkdir -p AppDir/usr/share/icons/hicolor/256x256/apps

      - name: Copy binary
        run: |
          PKG_NAME=$(grep '^name = ' Cargo.toml | head -n1 | cut -d'"' -f2)
          cp binaries/${PKG_NAME}-linux-x86_64 AppDir/usr/bin/${PKG_NAME}
          chmod +x AppDir/usr/bin/${PKG_NAME}

      - name: Create desktop entry
        run: |
          PKG_NAME=$(grep '^name = ' Cargo.toml | head -n1 | cut -d'"' -f2)
          DESCRIPTION=$(grep '^description = ' Cargo.toml | head -n1 | cut -d'"' -f2)

          cat > AppDir/usr/share/applications/${PKG_NAME}.desktop <<EOF
          [Desktop Entry]
          Type=Application
          Name=${PKG_NAME}
          Comment=${DESCRIPTION}
          Exec=${PKG_NAME}
          Icon=${PKG_NAME}
          Categories=Utility;
          Terminal=true
          EOF

      - name: Create AppRun script
        run: |
          PKG_NAME=$(grep '^name = ' Cargo.toml | head -n1 | cut -d'"' -f2)

          cat > AppDir/AppRun <<EOF
          #!/bin/bash
          SELF=\$(readlink -f "\$0")
          HERE=\${SELF%/*}
          export PATH="\${HERE}/usr/bin:\${PATH}"
          exec "\${HERE}/usr/bin/${PKG_NAME}" "\$@"
          EOF

          chmod +x AppDir/AppRun

      - name: Build AppImage
        run: |
          PKG_NAME=$(grep '^name = ' Cargo.toml | head -n1 | cut -d'"' -f2)
          VERSION=${{ steps.version.outputs.version }}

          ARCH=x86_64 appimagetool AppDir ${PKG_NAME}-${VERSION}-x86_64.AppImage

      - name: Upload AppImage
        uses: actions/upload-artifact@v4
        with:
          name: appimage-x86_64
          path: '*.AppImage'
          retention-days: 7
```

## Unified Package Release Workflow

```yaml
# file: .github/workflows/release-packages.yml
# version: 1.0.0
# guid: release-packages-unified

name: Release All Packages

on:
  push:
    tags:
      - 'v*.*.*'
  workflow_dispatch:

jobs:
  build-binaries:
    name: Build Binaries
    uses: ./.github/workflows/reusable-release.yml
    with:
      language: rust
      platforms:
        '["linux-x86_64", "linux-aarch64", "macos-x86_64", "macos-aarch64", "windows-x86_64"]'
      publish-packages: true
    secrets: inherit

  build-deb:
    name: Build Debian Packages
    needs: build-binaries
    uses: ./.github/workflows/release-deb.yml

  build-rpm:
    name: Build RPM Packages
    needs: build-binaries
    uses: ./.github/workflows/release-rpm.yml

  build-appimage:
    name: Build AppImage
    needs: build-binaries
    uses: ./.github/workflows/release-appimage.yml

  update-homebrew:
    name: Update Homebrew Formula
    needs: build-binaries
    uses: ./.github/workflows/release-homebrew.yml

  aggregate-packages:
    name: Aggregate All Packages
    needs: [build-deb, build-rpm, build-appimage, update-homebrew]
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - name: Download all packages
        uses: actions/download-artifact@v4
        with:
          path: packages/

      - name: Create package manifest
        run: |
          cat > packages/MANIFEST.md <<EOF
          # Package Manifest

          ## Debian Packages (.deb)
          $(find packages/deb-* -name '*.deb' -exec basename {} \; | sed 's/^/- /')

          ## RPM Packages (.rpm)
          $(find packages/rpm-* -name '*.rpm' -exec basename {} \; | sed 's/^/- /')

          ## AppImage
          $(find packages/appimage-* -name '*.AppImage' -exec basename {} \; | sed 's/^/- /')

          ## Homebrew
          - Formula updated in homebrew-tap repository
          EOF

      - name: Upload to GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          files: |
            packages/**/*.deb
            packages/**/*.rpm
            packages/**/*.AppImage
            packages/MANIFEST.md
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

**Part 4 Complete**: System package generation (deb, rpm, Homebrew, AppImage), unified package
release workflow. ✅

**Continue to Part 5** for release verification, testing, and rollback procedures.
