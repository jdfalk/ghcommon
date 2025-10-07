<!-- file: docs/cross-registry-todos/task-03/t03-part1.md -->
<!-- version: 1.0.0 -->
<!-- guid: t03-rust-part1-a1b2c3d4-e5f6 -->

# Task 03 Part 1: Rust Crate Publishing Overview and Analysis

## Task Overview

**What**: Implement Rust crate publishing to GitHub Package Registry in release-rust.yml

**Why**: Rust binaries are built but crates are not published to a package registry, making it hard for other projects to depend on them as libraries

**Where**: `ghcommon` repository, file `.github/workflows/release-rust.yml`

**Expected Outcome**: Rust crates automatically published to GitHub Package Registry during releases, enabling dependency management across projects

**Estimated Time**: 45-60 minutes

**Risk Level**: Medium (modifying release workflow, requires testing)

## Understanding GitHub Package Registry for Rust

### Registry Architecture

GitHub provides a Cargo-compatible registry that integrates with the GitHub Packages ecosystem. Unlike crates.io (the default public Rust registry), GitHub Packages provides:

- **Private crates**: Control access to your crates
- **Organization-level packages**: Share across repos in an org
- **Integration with GitHub**: Uses existing authentication
- **Version management**: Full semver support with versioned packages

### Registry URL Structure

GitHub's Cargo registry uses a specific URL format:

```
Registry Index: sparse+https://api.github.com/{owner}/{repo}/cargo/
Package URL: https://github.com/{owner}/{repo}/packages
API Endpoint: https://api.github.com/orgs/{owner}/packages/cargo/{crate-name}
```

**Example for jdfalk/ghcommon:**

```
Index: sparse+https://api.github.com/jdfalk/ghcommon/cargo/
Packages: https://github.com/jdfalk/ghcommon/packages
API: https://api.github.com/orgs/jdfalk/packages/cargo/ubuntu-autoinstall-agent
```

The "sparse" protocol is the modern, efficient index format that Cargo uses by default since version 1.68.0.

### Authentication Methods

Three authentication options for GitHub Packages:

#### 1. GITHUB_TOKEN (Recommended for CI)

```yaml
env:
  CARGO_REGISTRY_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**Pros:**
- Automatically available in GitHub Actions
- No manual token creation needed
- Scoped to the current repository
- Secure by default

**Cons:**
- Limited to repository scope
- Cannot publish to other org's packages

**Best for:** CI/CD workflows (our use case)

#### 2. Personal Access Token (PAT)

```bash
# Create PAT with scopes:
# - write:packages
# - read:packages
# - repo (if private repositories)

# Store in GitHub Secrets as CARGO_REGISTRY_TOKEN
```

**Pros:**
- Can work across repositories
- Can publish to multiple orgs
- Full control over permissions

**Cons:**
- Manual creation required
- Must be stored securely
- Expires and needs renewal

**Best for:** Local development, cross-repo publishing

#### 3. GitHub App Token

```yaml
- uses: actions/create-github-app-token@v1
  with:
    app-id: ${{ secrets.APP_ID }}
    private-key: ${{ secrets.APP_PRIVATE_KEY }}
```

**Pros:**
- Fine-grained permissions
- Better audit trail
- Can be org-wide

**Cons:**
- Complex setup
- Overkill for simple use cases

**Best for:** Large organizations with strict security requirements

### Cargo Configuration for GitHub Registry

Cargo needs two configuration files to work with GitHub Packages:

#### config.toml

Defines the registry and its URL:

```toml
# ~/.cargo/config.toml

[registries.github]
index = "sparse+https://api.github.com/jdfalk/ghcommon/cargo/"

[registry]
default = "github"  # Makes this the default registry

[net]
git-fetch-with-cli = true  # Use git CLI for better auth
```

**Key points:**
- `registries.github` defines a named registry
- `index` points to the GitHub API endpoint
- `sparse+` prefix enables efficient sparse index
- `default = "github"` makes it the default (optional)
- `git-fetch-with-cli` improves authentication reliability

#### credentials.toml

Stores authentication token:

```toml
# ~/.cargo/credentials.toml

[registries.github]
token = "ghp_xxxxxxxxxxxxxxxxxxxx"
```

**Security considerations:**
- File permissions must be 600 (owner read/write only)
- Never commit this file
- Token should have minimal required scopes
- Rotate tokens regularly

## Prerequisites

### Required Access

- **Write access** to `jdfalk/ghcommon` repository
- **Ability to create and use GitHub Personal Access Tokens (PAT)** for testing
- **Permission to publish packages** to GitHub (usually automatic for repo collaborators)
- **Permission to create releases** (needed to trigger workflow)

### Required Tools

```bash
# Verify these are installed locally
git --version          # Any recent version (2.30+)
cargo --version        # Rust 1.68+ (for sparse index support)
rustc --version        # Matches cargo version
gh --version           # GitHub CLI 2.0+

# Optional: for local testing
docker --version       # For container-based testing
yamllint --version     # For YAML validation
actionlint --version   # For GitHub Actions validation
```

**Installation if missing:**

```bash
# macOS
brew install git gh yamllint actionlint
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Linux
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
# Then install gh, yamllint, actionlint from your package manager

# Verify Rust installation
cargo --version
rustc --version
rustfmt --version
```

### Knowledge Requirements

#### Essential Knowledge

- **Rust cargo publish process**: How `cargo publish` works
- **GitHub Package Registry for Rust/Cargo**: Registry authentication and configuration
- **GitHub Actions workflow syntax**: YAML, jobs, steps, conditionals
- **Cargo.toml configuration**: Package metadata fields
- **Authentication with GitHub Packages**: Token creation and usage

#### Helpful Knowledge

- **Semantic versioning**: Understanding version numbers (1.2.3)
- **Git tagging**: Creating and pushing tags
- **Cross-compilation**: If publishing multi-platform crates
- **Cargo workspaces**: If project has multiple crates

### Background Reading

**Official Documentation:**

- [GitHub Packages for Cargo](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-cargo-registry)
  - Comprehensive guide to GitHub's Cargo registry
  - Authentication setup
  - Publishing and consuming packages

- [Cargo Publish Documentation](https://doc.rust-lang.org/cargo/commands/cargo-publish.html)
  - Complete reference for `cargo publish` command
  - Options and flags
  - Error handling

- [Cargo Registry Authentication](https://doc.rust-lang.org/cargo/reference/registries.html)
  - How Cargo handles multiple registries
  - Authentication mechanisms
  - Configuration file formats

**Additional Resources:**

- [Cargo Book - Publishing to Registries](https://doc.rust-lang.org/cargo/reference/publishing.html)
- [GitHub Actions - Publishing Packages](https://docs.github.com/en/actions/publishing-packages)
- [Rust Package Registry Guide](https://rust-lang.github.io/rfcs/2141-alternative-registries.html)

## Current State Analysis

### Step 1: Review Current Workflow

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# View the entire release-rust.yml workflow
cat .github/workflows/release-rust.yml

# Or use less for better viewing
less .github/workflows/release-rust.yml

# Or open in your editor
code .github/workflows/release-rust.yml
```

**What to look for:**

1. **Workflow triggers**: When does it run?
   ```yaml
   on:
     push:
       tags:
         - 'v*'
   ```

2. **Jobs structure**: What jobs exist?
   ```yaml
   jobs:
     build-rust:
       strategy:
         matrix:
           # Multiple platforms
   ```

3. **Build steps**: How are binaries built?
   - Rust toolchain setup
   - Cross-compilation configuration
   - Build commands
   - Artifact uploads

4. **Missing**: No `cargo publish` steps

### Step 2: Identify What's Missing

**Current workflow includes:**

✅ **Multi-platform Rust builds**
- linux/amd64, linux/arm64
- Windows, macOS
- Cross-compilation setup with cross-rs

✅ **Clippy linting**
```yaml
- name: Run Clippy
  run: cargo clippy -- -D warnings
```

✅ **Test execution**
```yaml
- name: Run tests
  run: cargo test --verbose
```

✅ **Binary artifact creation**
```yaml
- name: Build release binary
  run: cargo build --release --target ${{ matrix.target }}
```

✅ **Binary upload to GitHub releases**
```yaml
- name: Upload to release
  uses: actions/upload-release-asset@v1
```

**Missing components:**

❌ **Cargo publish to registry**
- No `cargo publish` command
- No registry configuration

❌ **Crate publishing configuration**
- No `.cargo/config.toml` setup in workflow
- No credentials configuration

❌ **Registry authentication**
- No token configuration for publishing
- No permissions specified for packages

❌ **Version verification**
- No check for duplicate versions
- No validation that tag matches Cargo.toml version

### Step 3: Check for Publishing Blockers

```bash
# Check if workflows already attempt to publish (they shouldn't)
grep -n "cargo publish" .github/workflows/release-rust.yml

# Expected output: (no matches)
# If there ARE matches, review them carefully before proceeding
```

**If matches found:**
1. Review the existing publish step
2. Check if it's commented out or active
3. Determine if it conflicts with our new implementation
4. Document any existing behavior to preserve

```bash
# Check for any registry configuration
grep -n "registries" .github/workflows/release-rust.yml

# Check for credentials setup
grep -n "credentials" .github/workflows/release-rust.yml

# Check for package permissions
grep -n "packages:" .github/workflows/release-rust.yml
```

### Step 4: Analyze Target Repositories with Rust Code

```bash
# Find repositories that use this workflow
cd /Users/jdfalk/repos/github.com/jdfalk
grep -r "uses:.*release-rust.yml" . --include="*.yml" 2>/dev/null | \
  grep -v "ghcommon/.git"

# Expected: ubuntu-autoinstall-agent and possibly others
```

**Example output:**

```
./ubuntu-autoinstall-agent/.github/workflows/release.yml:
    uses: jdfalk/ghcommon/.github/workflows/release-rust.yml@main
```

**For each repository found:**

```bash
# Check if it has a Cargo.toml
ls -la ../ubuntu-autoinstall-agent/Cargo.toml

# Check the package name
grep "^name =" ../ubuntu-autoinstall-agent/Cargo.toml

# Check the current version
grep "^version =" ../ubuntu-autoinstall-agent/Cargo.toml
```

### Step 5: Review Cargo.toml in Target Repositories

```bash
# Check the ubuntu-autoinstall-agent Cargo.toml
cat ../ubuntu-autoinstall-agent/Cargo.toml
```

**Look for required publishing fields:**

```toml
[package]
name = "ubuntu-autoinstall-agent"       # ✅ Required
version = "0.1.0"                       # ✅ Required
edition = "2021"                        # ✅ Required
authors = ["Your Name <email@domain>"]  # ✅ Required for publishing
description = "A clear description"     # ✅ Required for publishing
license = "MIT"                         # ✅ Required for publishing
repository = "https://github.com/..."   # ✅ Required for publishing
readme = "README.md"                    # ⚪ Optional but recommended
keywords = ["keyword1", "keyword2"]     # ⚪ Optional but recommended
categories = ["category"]               # ⚪ Optional but recommended
```

**Critical fields for publishing:**

1. **name**: Crate identifier (must be unique in registry)
2. **version**: Semantic version (e.g., 0.1.0, 1.2.3)
3. **edition**: Rust edition (2018, 2021)
4. **authors**: List of maintainers
5. **description**: One-line description (max 100 chars)
6. **license**: SPDX license identifier or license file
7. **repository**: Source code URL

**Check for publishing blockers:**

```bash
# Required fields check script
cat > /tmp/check-cargo-toml.sh << 'EOF'
#!/bin/bash
CARGO_TOML="$1"

if [ ! -f "$CARGO_TOML" ]; then
  echo "❌ File not found: $CARGO_TOML"
  exit 1
fi

echo "Checking $CARGO_TOML for required publishing fields..."
echo ""

REQUIRED_FIELDS=("name" "version" "edition" "authors" "description" "license" "repository")
MISSING=0

for field in "${REQUIRED_FIELDS[@]}"; do
  if grep -q "^$field =" "$CARGO_TOML"; then
    VALUE=$(grep "^$field =" "$CARGO_TOML" | head -1)
    echo "✅ $field: $VALUE"
  else
    echo "❌ $field: MISSING"
    MISSING=$((MISSING + 1))
  fi
done

echo ""
if [ $MISSING -eq 0 ]; then
  echo "✅ All required fields present"
  exit 0
else
  echo "❌ $MISSING required fields missing"
  exit 1
fi
EOF

chmod +x /tmp/check-cargo-toml.sh

# Run for each target repository
/tmp/check-cargo-toml.sh ../ubuntu-autoinstall-agent/Cargo.toml
```

### Decision Point

**Proceed if:**

✅ No existing `cargo publish` steps in workflow (or they're clearly outdated/disabled)
✅ Target repositories have valid Cargo.toml with ALL required fields
✅ You understand GitHub Package Registry for Cargo authentication
✅ You can create/use GitHub PAT tokens (or will use GITHUB_TOKEN)
✅ Workflow syntax is valid (no YAML errors)

**Stop and fix if:**

❌ **Cargo.toml is missing required fields**
  - Fix in the target repository first
  - Add authors, description, license, repository fields
  - Commit and push changes
  - Then return to this task

❌ **Unclear about registry authentication**
  - Review "Authentication Methods" section above
  - Test local authentication first
  - Create test PAT token if needed

❌ **Existing publish steps that might conflict**
  - Document existing behavior
  - Determine if migration is needed
  - Plan for backward compatibility

❌ **Workflow has YAML syntax errors**
  - Fix syntax errors first
  - Validate with yamllint
  - Test with actionlint

**Example fix for missing Cargo.toml fields:**

```bash
cd ../ubuntu-autoinstall-agent

# Add missing fields to Cargo.toml
# Edit [package] section to include:

cat >> Cargo.toml << 'EOF'
authors = ["Jake Falk <jdfalk@github.com>"]
description = "Ubuntu autoinstall agent for automated server provisioning"
license = "MIT"
repository = "https://github.com/jdfalk/ubuntu-autoinstall-agent"
keywords = ["ubuntu", "autoinstall", "provisioning", "server"]
categories = ["command-line-utilities"]
readme = "README.md"
EOF

# Commit the changes
git add Cargo.toml
git commit -m "chore: add required Cargo.toml fields for publishing"
git push
```

## Next Steps

Once all prerequisites are met and decision point checks pass, proceed to **Part 2: Implementation Design and Workflow Configuration** to begin adding the publishing job to the workflow.

---

**Part 1 Complete**: Overview, prerequisites, authentication methods, current state analysis, and decision point verification. ✅

**Continue to Part 2** for detailed implementation design and workflow configuration steps.
