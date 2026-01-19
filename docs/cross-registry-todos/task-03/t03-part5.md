<!-- file: docs/cross-registry-todos/task-03/t03-part5.md -->
<!-- version: 1.0.0 -->
<!-- guid: t03-rust-part5-e5f6g7h8-i9j0 -->
<!-- last-edited: 2026-01-19 -->

# Task 03 Part 5: Optimization and Advanced Configuration

## Performance Optimization

### Build Caching Strategy

The publishing job can benefit from Cargo's build cache to speed up verification (if enabled):

```yaml
- name: Cache cargo registry
  uses: actions/cache@v4
  with:
    path: ~/.cargo/registry
    key: ${{ runner.os }}-cargo-registry-${{ hashFiles('**/Cargo.lock') }}

- name: Cache cargo index
  uses: actions/cache@v4
  with:
    path: ~/.cargo/git
    key: ${{ runner.os }}-cargo-index-${{ hashFiles('**/Cargo.lock') }}

- name: Cache cargo build
  uses: actions/cache@v4
  with:
    path: target
    key: ${{ runner.os }}-cargo-build-target-${{ hashFiles('**/Cargo.lock') }}
```

**Benefits:**

- Faster dependency resolution
- Reduced network I/O
- Quicker verification builds (if `--no-verify` is removed)

**Tradeoffs:**

- Uses GitHub Actions cache storage (10 GB limit per repo)
- May not be needed if using `--no-verify`
- Adds complexity to workflow

**Recommendation**: Skip caching for publishing job since we use `--no-verify` and the build-rust
job already validates everything.

### Parallel Execution

The publishing job already runs in parallel with the build-rust job's matrix builds by design.
However, we can optimize the verification steps:

```yaml
- name: Parallel verification checks
  run: |
    # Run multiple checks concurrently
    (
      # Check 1: Verify Cargo.toml in background
      grep -q "^name =" Cargo.toml && echo "✅ Name present" &

      # Check 2: Verify git status
      git diff --exit-code && echo "✅ Clean working tree" &

      # Check 3: Verify no uncommitted changes
      git status --porcelain | wc -l | grep -q "^0$" && echo "✅ No changes" &

      # Wait for all background checks
      wait
    )
```

**Benefits:**

- Faster validation
- Better resource utilization

**Tradeoffs:**

- More complex error handling
- Harder to debug failures

**Recommendation**: Current sequential approach is clear and fast enough. Parallel optimization
provides minimal benefit (< 5 seconds).

### Network Optimization

Reduce API calls by combining operations:

```yaml
- name: Optimized package check
  id: package-check
  run: |
    # Single API call to get all package info
    PACKAGE_INFO=$(curl -s \
      -H "Authorization: Bearer ${{ secrets.GITHUB_TOKEN }}" \
      -H "Accept: application/vnd.github.v3+json" \
      "https://api.github.com/orgs/${{ github.repository_owner }}/packages/cargo/$CRATE_NAME")

    # Extract multiple fields from single response
    PACKAGE_EXISTS=$(echo "$PACKAGE_INFO" | jq -r '.name != null')
    VERSION_COUNT=$(echo "$PACKAGE_INFO" | jq -r '.version_count // 0')

    echo "package-exists=$PACKAGE_EXISTS" >> $GITHUB_OUTPUT
    echo "version-count=$VERSION_COUNT" >> $GITHUB_OUTPUT
```

**Benefits:**

- Fewer API calls (single request vs multiple)
- Faster execution
- Reduced rate limit impact

**Current implementation already optimized**: We make minimal API calls and cache results.

## Advanced Configuration Options

### Multi-Registry Publishing

Publish to both GitHub Packages and crates.io:

```yaml
- name: Publish to multiple registries
  env:
    CARGO_REGISTRY_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    CRATES_IO_TOKEN: ${{ secrets.CRATES_IO_TOKEN }}
  run: |
    # Publish to GitHub Packages
    cargo publish --registry github --verbose --allow-dirty --no-verify

    # Wait a bit to avoid rate limiting
    sleep 5

    # Publish to crates.io (if token available)
    if [ -n "$CRATES_IO_TOKEN" ]; then
      cargo publish --registry crates-io --verbose --allow-dirty --no-verify
    else
      echo "⏭️ Skipping crates.io publish (no token configured)"
    fi
```

**Configuration for crates.io:**

```toml
# .cargo/config.toml
[registries.crates-io]
index = "sparse+https://index.crates.io/"

[registries.github]
index = "sparse+https://api.github.com/$REPO/cargo/"
```

**Secrets to add:**

- `CRATES_IO_TOKEN`: Create at <https://crates.io/me/tokens>

### Workspace Publishing

For Cargo workspaces with multiple crates:

```yaml
- name: Detect workspace crates
  id: workspace
  run: |
    if grep -q '\[workspace\]' Cargo.toml; then
      echo "is-workspace=true" >> $GITHUB_OUTPUT

      # List workspace members
      MEMBERS=$(grep -A 10 '\[workspace\]' Cargo.toml | \
        grep 'members = ' | \
        sed 's/members = \[//' | sed 's/\]//' | sed 's/"//g')

      echo "members=$MEMBERS" >> $GITHUB_OUTPUT
    else
      echo "is-workspace=false" >> $GITHUB_OUTPUT
    fi

- name: Publish workspace crates
  if: steps.workspace.outputs.is-workspace == 'true'
  run: |
    # Publish in dependency order
    for member in ${{ steps.workspace.outputs.members }}; do
      echo "Publishing $member..."
      cd "$member"
      cargo publish --registry github --verbose --allow-dirty --no-verify
      cd ..
      sleep 10  # Wait between publishes
    done
```

### Conditional Publishing

Publish only for certain tag patterns:

```yaml
publish-rust-crate:
  if: |
    startsWith(github.ref, 'refs/tags/v') &&
    !contains(github.ref, '-alpha') &&
    !contains(github.ref, '-beta')
```

**Example tag handling:**

- `v1.2.3` → Publishes ✅
- `v1.2.3-alpha.1` → Skips ⏭️
- `v1.2.3-beta.2` → Skips ⏭️
- `v1.2.3-rc.1` → Publishes ✅ (remove from condition if unwanted)

### Pre-Release Handling

Publish pre-releases to a separate registry or with different configuration:

```yaml
- name: Detect release type
  id: release-type
  run: |
    TAG="${GITHUB_REF#refs/tags/v}"
    if echo "$TAG" | grep -q -E '(alpha|beta|rc|pre)'; then
      echo "is-prerelease=true" >> $GITHUB_OUTPUT
      echo "🔖 Pre-release detected: $TAG"
    else
      echo "is-prerelease=false" >> $GITHUB_OUTPUT
      echo "🏷️ Stable release: $TAG"
    fi

- name: Publish stable release
  if: steps.release-type.outputs.is-prerelease == 'false'
  run: |
    cargo publish --registry github --verbose --allow-dirty --no-verify

- name: Publish pre-release
  if: steps.release-type.outputs.is-prerelease == 'true'
  run: |
    # For pre-releases, maybe just skip or use different registry
    echo "⏭️ Skipping pre-release publication to registry"
    echo "Pre-releases are available as GitHub release assets only"
```

## Package Metadata Enhancement

### Enhanced Cargo.toml

Add comprehensive metadata for better discoverability:

```toml
[package]
name = "ubuntu-autoinstall-agent"
version = "0.1.0"
edition = "2021"
authors = ["Jake Falk <jdfalk@github.com>"]
description = "Ubuntu autoinstall agent for automated server provisioning and configuration management"
license = "MIT"
repository = "https://github.com/jdfalk/ubuntu-autoinstall-agent"
homepage = "https://github.com/jdfalk/ubuntu-autoinstall-agent"
documentation = "https://docs.rs/ubuntu-autoinstall-agent"
readme = "README.md"
keywords = ["ubuntu", "autoinstall", "provisioning", "automation", "server"]
categories = ["command-line-utilities", "config", "development-tools"]

# Package metadata
[package.metadata]
# Minimum Rust version
rust-version = "1.70"

[package.metadata.docs.rs]
# Features to enable for docs.rs builds
all-features = true
rustdoc-args = ["--cfg", "docsrs"]
```

**Benefits:**

- Better searchability on registries
- Clear compatibility requirements
- Professional appearance
- Automated documentation generation

### README Enhancement

Create a comprehensive README for package users:

````markdown
# Ubuntu Autoinstall Agent

[![Crates.io](https://img.shields.io/crates/v/ubuntu-autoinstall-agent.svg)](https://crates.io/crates/ubuntu-autoinstall-agent)
[![Documentation](https://docs.rs/ubuntu-autoinstall-agent/badge.svg)](https://docs.rs/ubuntu-autoinstall-agent)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Ubuntu autoinstall agent for automated server provisioning.

## Installation

### From GitHub Packages

Add to your `Cargo.toml`:

```toml
[dependencies]
ubuntu-autoinstall-agent = { version = "0.1.0", registry = "github" }
```
````

Configure the registry in `.cargo/config.toml`:

```toml
[registries.github]
index = "sparse+https://api.github.com/jdfalk/ubuntu-autoinstall-agent/cargo/"
```

### From crates.io (if published)

```toml
[dependencies]
ubuntu-autoinstall-agent = "0.1.0"
```

## Usage

```rust
use ubuntu_autoinstall_agent::Agent;

fn main() {
    let agent = Agent::new();
    agent.run();
}
```

## Features

- 🚀 Fast automated provisioning
- 🔐 Secure configuration management
- 🛠️ Extensible plugin system

## License

MIT

````

### Badges and Metadata

Add status badges to your repository README and crate documentation:

```markdown
[![CI](https://github.com/jdfalk/ubuntu-autoinstall-agent/workflows/CI/badge.svg)](https://github.com/jdfalk/ubuntu-autoinstall-agent/actions)
[![Release](https://github.com/jdfalk/ubuntu-autoinstall-agent/workflows/Release/badge.svg)](https://github.com/jdfalk/ubuntu-autoinstall-agent/actions)
[![Packages](https://img.shields.io/badge/packages-GitHub-blue)](https://github.com/jdfalk/ubuntu-autoinstall-agent/packages)
````

## Security Considerations

### Token Security

**Current approach (GITHUB_TOKEN) is secure:**

- ✅ Automatically rotated
- ✅ Scoped to repository
- ✅ No manual storage needed
- ✅ Expires after job completes

**If using PAT (Personal Access Token):**

```yaml
# Store as repository secret
env:
  CARGO_REGISTRY_TOKEN: ${{ secrets.CARGO_PAT }}
```

**Best practices:**

1. **Use fine-grained PAT** with minimal scopes:
   - `packages:write`
   - `packages:read`

2. **Rotate regularly**: Set expiration and rotate every 90 days

3. **Audit access**: Review PAT usage in GitHub settings

4. **Use organization secrets**: For multi-repo workflows

### Package Visibility

Control who can access your packages:

```bash
# Make package public (default for GitHub Packages)
gh api -X PATCH repos/jdfalk/ubuntu-autoinstall-agent/packages/cargo/ubuntu-autoinstall-agent \
  -f visibility=public

# Make package private (requires Pro/Enterprise)
gh api -X PATCH repos/jdfalk/ubuntu-autoinstall-agent/packages/cargo/ubuntu-autoinstall-agent \
  -f visibility=private
```

**Access control for private packages:**

```yaml
# In consuming repository
- name: Authenticate to GitHub Packages
  run: |
    echo "[registries.github]" > ~/.cargo/credentials.toml
    echo "token = \"${{ secrets.GITHUB_TOKEN }}\"" >> ~/.cargo/credentials.toml
    chmod 600 ~/.cargo/credentials.toml
```

### Dependency Security

Add security checks before publishing:

```yaml
- name: Security audit
  run: |
    # Install cargo-audit if not present
    cargo install cargo-audit --quiet

    # Run security audit
    cargo audit

    # Fail if high/critical vulnerabilities found
    cargo audit --deny warnings --deny high --deny critical
```

### Supply Chain Security

Sign packages with Cosign (if supported by registry):

```yaml
- name: Sign package with Cosign
  uses: sigstore/cosign-installer@v3

- name: Sign crate
  env:
    COSIGN_EXPERIMENTAL: 'true'
  run: |
    # Sign the package tarball
    cosign sign-blob \
      target/package/ubuntu-autoinstall-agent-${{ steps.crate-info.outputs.crate-version }}.crate
```

## Monitoring and Alerting

### Package Download Tracking

Monitor package usage:

```bash
#!/bin/bash
# file: scripts/monitor-package-downloads.sh
# version: 1.0.0
# guid: monitor-package-downloads

set -e

CRATE_NAME="ubuntu-autoinstall-agent"

echo "=== Package Download Statistics ==="
echo ""

# Get package info
PACKAGE_INFO=$(gh api repos/jdfalk/ubuntu-autoinstall-agent/packages/cargo/$CRATE_NAME)

# Extract stats
echo "Package: $(echo "$PACKAGE_INFO" | jq -r '.name')"
echo "Visibility: $(echo "$PACKAGE_INFO" | jq -r '.visibility')"
echo "Total Downloads: $(echo "$PACKAGE_INFO" | jq -r '.download_count // 0')"
echo ""

# List versions with download counts
echo "Versions:"
gh api repos/jdfalk/ubuntu-autoinstall-agent/packages/cargo/$CRATE_NAME/versions \
  --jq '.[] | "  - \(.name): \(.download_count // 0) downloads (published \(.created_at))"'

echo ""
echo "✅ Statistics retrieved"
```

### Publication Monitoring

Create a workflow to monitor publishing status:

```yaml
name: Monitor Package Registry

on:
  schedule:
    # Run daily at midnight
    - cron: '0 0 * * *'
  workflow_dispatch:

jobs:
  check-packages:
    runs-on: ubuntu-latest
    steps:
      - name: Check package status
        run: |
          CRATE_NAME="ubuntu-autoinstall-agent"

          # Get package info
          HTTP_STATUS=$(curl -s -o /tmp/package.json -w "%{http_code}" \
            -H "Authorization: Bearer ${{ secrets.GITHUB_TOKEN }}" \
            "https://api.github.com/orgs/${{ github.repository_owner }}/packages/cargo/$CRATE_NAME")

          if [ "$HTTP_STATUS" = "200" ]; then
            echo "✅ Package is accessible"
            cat /tmp/package.json | jq .
          else
            echo "❌ Package not accessible (HTTP $HTTP_STATUS)"
            exit 1
          fi

      - name: Verify latest version
        run: |
          # Get Cargo.toml version from main branch
          EXPECTED_VERSION=$(curl -s https://raw.githubusercontent.com/${{ github.repository }}/main/Cargo.toml | \
            grep -m1 '^version =' | sed 's/version = "\(.*\)"/\1/')

          # Get latest published version
          LATEST_VERSION=$(gh api repos/${{ github.repository }}/packages/cargo/ubuntu-autoinstall-agent/versions \
            --jq '.[0].name')

          echo "Expected version (from Cargo.toml): $EXPECTED_VERSION"
          echo "Latest published version: $LATEST_VERSION"

          if [ "$EXPECTED_VERSION" = "$LATEST_VERSION" ]; then
            echo "✅ Versions match"
          else
            echo "⚠️ Version mismatch - may need to publish"
          fi
```

### Alert on Publishing Failures

Add alerting to the publishing job:

```yaml
- name: Notify on failure
  if: failure()
  uses: actions/github-script@v7
  with:
    script: |
      const issue = await github.rest.issues.create({
        owner: context.repo.owner,
        repo: context.repo.repo,
        title: `🚨 Rust Crate Publishing Failed for ${context.ref}`,
        body: `
        ## Publishing Failure

        The Rust crate publishing job failed during release.

        **Tag**: \`${context.ref}\`
        **Workflow Run**: ${context.serverUrl}/${context.repo.owner}/${context.repo.repo}/actions/runs/${context.runId}

        **Next Steps**:
        1. Review the workflow logs
        2. Check Cargo.toml completeness
        3. Verify GITHUB_TOKEN permissions
        4. Re-run the workflow or create a new tag

        cc @${context.actor}
        `,
        labels: ['ci', 'publishing', 'urgent']
      });

      console.log('Created issue:', issue.data.html_url);
```

---

**Part 5 Complete**: Performance optimization strategies, advanced configuration options, package
metadata enhancement, security considerations, and monitoring setup. ✅

**Continue to Part 6** for troubleshooting guide, lessons learned, and task completion checklist.
