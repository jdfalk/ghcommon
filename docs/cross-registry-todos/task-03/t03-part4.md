<!-- file: docs/cross-registry-todos/task-03/t03-part4.md -->
<!-- version: 1.0.0 -->
<!-- guid: t03-rust-part4-d4e5f6g7-h8i9 -->

# Task 03 Part 4: Post-Merge Verification and Production Testing

## Post-Merge Verification

After merging the workflow changes, verify the updated workflow is recognized by GitHub:

### Step 1: Verify Workflow Recognition

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Check if GitHub recognizes the updated workflow
gh api repos/jdfalk/ghcommon/actions/workflows --jq '.workflows[] | select(.path == ".github/workflows/release-rust.yml") | {name, state, path}'

# Expected output:
# {
#   "name": "Release Rust Binaries and Crates",
#   "state": "active",
#   "path": ".github/workflows/release-rust.yml"
# }
```

**If workflow not active:**

```bash
# Check for syntax errors that prevent activation
gh api repos/jdfalk/ghcommon/actions/workflows/release-rust.yml 2>&1

# Check recent workflow runs for errors
gh run list --workflow=release-rust.yml --limit 5
```

### Step 2: Review Workflow File on GitHub

```bash
# Open the workflow file in browser
gh browse .github/workflows/release-rust.yml

# Or view raw content
gh api repos/jdfalk/ghcommon/contents/.github/workflows/release-rust.yml \
  --jq '.content' | base64 -d | head -50
```

**Verify:**

- ✅ File shows the new `publish-rust-crate` job
- ✅ Version number is updated (1.9.0)
- ✅ Documentation comments are present
- ✅ No syntax highlighting errors in GitHub UI

### Step 3: Check Workflow Permissions

The new job requires `packages: write` permission. Verify it's configured:

```bash
# View the workflow permissions section
gh api repos/jdfalk/ghcommon/contents/.github/workflows/release-rust.yml \
  --jq '.content' | base64 -d | grep -A 5 "permissions:"

# Expected in publish-rust-crate job:
# permissions:
#   contents: read
#   packages: write
```

### Step 4: Verify in Calling Repositories

Check that repositories using this reusable workflow can access it:

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ubuntu-autoinstall-agent

# Check the calling workflow
cat .github/workflows/release.yml | grep -A 10 "release-rust"

# Expected:
#   uses: jdfalk/ghcommon/.github/workflows/release-rust.yml@main
```

**Test accessibility:**

```bash
# Try to fetch the workflow from the calling repo's perspective
gh api repos/jdfalk/ghcommon/contents/.github/workflows/release-rust.yml \
  --jq '.download_url'

# Should return a valid URL
# Example: https://raw.githubusercontent.com/jdfalk/ghcommon/main/.github/workflows/release-rust.yml
```

## Production Testing Strategy

### Test Approach

We'll test the publishing functionality by creating a test release:

1. **Prepare target repository** (ubuntu-autoinstall-agent)
2. **Ensure Cargo.toml is complete**
3. **Create a test version tag**
4. **Monitor the workflow execution**
5. **Verify package publication**
6. **Test package installation**

### Phase 1: Pre-Release Preparation

#### Check Current State

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ubuntu-autoinstall-agent

# Check current version
grep "^version =" Cargo.toml

# Check existing tags
git tag -l | sort -V | tail -5

# Check existing releases
gh release list --limit 5

# Check if package already exists
gh api repos/jdfalk/ubuntu-autoinstall-agent/packages 2>&1 | jq -r '.[] | select(.package_type == "CARGO") | {name, version}'
```

#### Verify Cargo.toml Completeness

```bash
# Run the verification script
cat > /tmp/verify-cargo-toml.sh << 'EOF'
#!/bin/bash
REQUIRED_FIELDS=("name" "version" "edition" "authors" "description" "license" "repository")

echo "Verifying Cargo.toml completeness..."
echo ""

MISSING=0
for field in "${REQUIRED_FIELDS[@]}"; do
  if grep -q "^$field =" Cargo.toml; then
    VALUE=$(grep "^$field =" Cargo.toml | head -1)
    echo "✅ $field: $VALUE"
  else
    echo "❌ $field: MISSING"
    MISSING=$((MISSING + 1))
  fi
done

echo ""
if [ $MISSING -eq 0 ]; then
  echo "✅ Ready for publishing"
  exit 0
else
  echo "❌ Fix missing fields before publishing"
  exit 1
fi
EOF

chmod +x /tmp/verify-cargo-toml.sh
/tmp/verify-cargo-toml.sh
```

**If fields are missing, add them:**

```bash
# Example: Add missing fields to Cargo.toml
cat >> Cargo.toml << 'EOF'

# Required for publishing
authors = ["Jake Falk <jdfalk@github.com>"]
description = "Ubuntu autoinstall agent for automated server provisioning"
license = "MIT"
repository = "https://github.com/jdfalk/ubuntu-autoinstall-agent"
keywords = ["ubuntu", "autoinstall", "provisioning"]
categories = ["command-line-utilities"]
EOF

# Commit the changes
git add Cargo.toml
git commit -m "chore: add required Cargo.toml fields for publishing"
git push
```

#### Decide on Test Version

```bash
# Check current version
CURRENT_VERSION=$(grep "^version =" Cargo.toml | sed 's/version = "\(.*\)"/\1/')
echo "Current version: $CURRENT_VERSION"

# Suggest test version (bump patch)
echo "Suggested test version: ${CURRENT_VERSION%.*}.$((${CURRENT_VERSION##*.} + 1))"

# Or use a pre-release version for testing
echo "Suggested pre-release version: $CURRENT_VERSION-test.1"
```

**For testing, we'll use a pre-release version to avoid polluting the main version space:**

```bash
# Example: if current is 0.1.0, use 0.1.1-test.1
TEST_VERSION="${CURRENT_VERSION%.*}.$((${CURRENT_VERSION##*.} + 1))-test.1"
echo "Test version: $TEST_VERSION"
```

### Phase 2: Create Test Release

#### Update Version in Cargo.toml

```bash
# Update version to test version
sed -i.bak "s/^version = \".*\"/version = \"$TEST_VERSION\"/" Cargo.toml

# Verify change
grep "^version =" Cargo.toml

# Commit version bump
git add Cargo.toml
git commit -m "chore: bump version to $TEST_VERSION for publishing test"
git push
```

#### Create and Push Tag

```bash
# Create annotated tag
git tag -a "v$TEST_VERSION" -m "Test release for Rust crate publishing

This is a test release to verify the new GitHub Package Registry
publishing functionality in the release-rust.yml workflow.

Testing:
- Cargo crate publishing
- GitHub Package Registry integration
- Package visibility and accessibility
- Installation from GitHub registry"

# Verify tag
git show "v$TEST_VERSION"

# Push tag (this triggers the workflow)
git push origin "v$TEST_VERSION"

echo ""
echo "✅ Tag pushed: v$TEST_VERSION"
echo "🚀 Workflow will start shortly"
```

### Phase 3: Monitor Workflow Execution

#### Watch Workflow Start

```bash
# Wait a few seconds for workflow to trigger
sleep 5

# Check if workflow started
gh run list --workflow=release.yml --limit 1

# Get the run ID
RUN_ID=$(gh run list --workflow=release.yml --limit 1 --json databaseId --jq '.[0].databaseId')

echo "Workflow run ID: $RUN_ID"

# Watch the workflow in real-time
gh run watch $RUN_ID
```

#### Monitor Specific Job

```bash
# List jobs in the run
gh run view $RUN_ID --json jobs --jq '.jobs[] | {name, status, conclusion}'

# Watch the publish job specifically
gh run view $RUN_ID --log | grep -A 50 "Publish Rust Crate"
```

**Expected log output:**

```text
Publish Rust Crate  Checkout repository
Publish Rust Crate  Set up Rust
Publish Rust Crate  Detect crate information
Publish Rust Crate  📦 Crate: ubuntu-autoinstall-agent
Publish Rust Crate  🏷️  Version: 0.1.1-test.1
Publish Rust Crate  ✅ Git tag matches Cargo.toml version
Publish Rust Crate  Configure Cargo for GitHub Registry
Publish Rust Crate  ✅ Cargo configured for GitHub Package Registry
Publish Rust Crate  Verify Cargo.toml completeness
Publish Rust Crate  ✅ All required fields present
Publish Rust Crate  Check if version already published
Publish Rust Crate  📭 Package not found (first publish for this crate)
Publish Rust Crate  Publish crate
Publish Rust Crate  📤 Publishing crate to GitHub Package Registry...
Publish Rust Crate      Updating crates.io index
Publish Rust Crate     Packaging ubuntu-autoinstall-agent v0.1.1-test.1
Publish Rust Crate     Uploading ubuntu-autoinstall-agent v0.1.1-test.1
Publish Rust Crate  ✅ Crate published successfully!
Publish Rust Crate  Verify publication
Publish Rust Crate  ✅ Package verified in GitHub Package Registry
```

#### Check for Errors

```bash
# If workflow fails, get full logs
gh run view $RUN_ID --log > /tmp/workflow-$RUN_ID.log

# Search for errors
grep -i "error\|fail\|❌" /tmp/workflow-$RUN_ID.log

# View specific job logs
gh run view $RUN_ID --log --job <job-id>
```

**Common errors and solutions:**

**Error**: `missing field 'authors'`

```bash
# Add to Cargo.toml and re-tag
echo 'authors = ["Your Name <email@example.com>"]' >> Cargo.toml
git add Cargo.toml && git commit -m "chore: add authors field"
git push
# Delete old tag and create new one
git tag -d "v$TEST_VERSION"
git push origin ":refs/tags/v$TEST_VERSION"
git tag -a "v$TEST_VERSION" -m "Test release"
git push origin "v$TEST_VERSION"
```

**Error**: `crate name already exists`

```bash
# Use a different test version
TEST_VERSION="${CURRENT_VERSION}-test.2"
# Update Cargo.toml and re-tag
```

**Error**: `authentication failed`

```bash
# Check repository settings → Actions → General → Workflow permissions
# Must be set to "Read and write permissions"
```

### Phase 4: Verify Package Publication

#### Check Package via API

```bash
# Wait for publication to complete
sleep 30

# Check package exists
gh api repos/jdfalk/ubuntu-autoinstall-agent/packages \
  --jq '.[] | select(.package_type == "CARGO") | {name, visibility, created_at}'

# Get package details
CRATE_NAME="ubuntu-autoinstall-agent"
gh api repos/jdfalk/ubuntu-autoinstall-agent/packages/cargo/$CRATE_NAME \
  --jq '{name, package_type, visibility, html_url}'

# List versions
gh api repos/jdfalk/ubuntu-autoinstall-agent/packages/cargo/$CRATE_NAME/versions \
  --jq '.[] | {name, created_at}'
```

**Expected output:**

```json
{
  "name": "ubuntu-autoinstall-agent",
  "package_type": "CARGO",
  "visibility": "public",
  "html_url": "https://github.com/jdfalk/ubuntu-autoinstall-agent/packages/..."
}
```

#### Check Package in UI

```bash
# Open packages page in browser
gh browse /packages

# Or construct URL
echo "https://github.com/jdfalk/ubuntu-autoinstall-agent/packages"
```

**Verify in UI:**

- ✅ Package appears in list
- ✅ Version shows correctly (0.1.1-test.1)
- ✅ "Published" timestamp is recent
- ✅ Package visibility is public
- ✅ Installation instructions are shown

### Phase 5: Test Package Installation

#### Set Up Test Environment

```bash
# Create a test project
mkdir -p /tmp/test-rust-package
cd /tmp/test-rust-package

# Initialize new Rust project
cargo init --name test-consumer

# Configure GitHub registry
mkdir -p .cargo
cat > .cargo/config.toml << EOF
[registries.github]
index = "sparse+https://api.github.com/jdfalk/ubuntu-autoinstall-agent/cargo/"

[net]
git-fetch-with-cli = true
EOF
```

#### Authenticate for Private Packages

If your packages are private, configure authentication:

```bash
# Create credentials file
cat > ~/.cargo/credentials.toml << EOF
[registries.github]
token = "${GITHUB_TOKEN}"
EOF

chmod 600 ~/.cargo/credentials.toml
```

**Note**: For public packages, authentication is not required for installation, only for publishing.

#### Add Dependency

```bash
# Add the published crate as a dependency
cat >> Cargo.toml << EOF

[dependencies]
ubuntu-autoinstall-agent = { version = "$TEST_VERSION", registry = "github" }
EOF
```

#### Test Installation

```bash
# Try to build (will download the package)
cargo build

# Expected output:
#     Updating `sparse+https://api.github.com/jdfalk/ubuntu-autoinstall-agent/cargo/` index
#    Downloading ubuntu-autoinstall-agent v0.1.1-test.1 (registry `github`)
#     Compiling ubuntu-autoinstall-agent v0.1.1-test.1
#     Compiling test-consumer v0.1.0 (/tmp/test-rust-package)
#      Finished dev [unoptimized + debuginfo] target(s) in 5.23s
```

**If successful:**

```bash
echo "✅ Package installation successful!"
echo "✅ Crate can be downloaded from GitHub Package Registry"
echo "✅ Publishing functionality verified"
```

**If fails:**

```bash
# Common issues:
# 1. Package not yet indexed (wait a few minutes)
# 2. Authentication required (add token)
# 3. Registry URL incorrect (check config.toml)
# 4. Network issues (check internet connection)

# Debug: Try manual download
curl -L -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/jdfalk/ubuntu-autoinstall-agent/tarball/v$TEST_VERSION"
```

## Cleanup Test Release

After successful testing, clean up the test release:

### Option 1: Keep Test Release (Recommended)

```bash
# Keep the test release as documentation that publishing works
# Just add a note to the release
gh release edit "v$TEST_VERSION" --notes "✅ Test release for Rust crate publishing verification

This release was created to test and verify the GitHub Package Registry
publishing functionality. The crate was successfully published and can
be consumed by other Rust projects.

**Status**: Test successful ✅

The publishing workflow is working correctly and ready for production releases."
```

### Option 2: Delete Test Release

```bash
# Delete the GitHub release
gh release delete "v$TEST_VERSION" --yes

# Delete the Git tag
git tag -d "v$TEST_VERSION"
git push origin ":refs/tags/v$TEST_VERSION"

# Note: Package version will remain in GitHub Packages
# To delete package version (irreversible):
gh api repos/jdfalk/ubuntu-autoinstall-agent/packages/cargo/ubuntu-autoinstall-agent/versions \
  --jq '.[] | select(.name == "'$TEST_VERSION'") | .id' | xargs -I {} \
  gh api -X DELETE repos/jdfalk/ubuntu-autoinstall-agent/packages/cargo/ubuntu-autoinstall-agent/versions/{}
```

### Revert Version in Cargo.toml

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ubuntu-autoinstall-agent

# Revert to original version
git checkout Cargo.toml

# Or manually set back to development version
sed -i.bak "s/^version = \".*\"/version = \"$CURRENT_VERSION\"/" Cargo.toml

# Commit
git add Cargo.toml
git commit -m "chore: revert to development version after publishing test"
git push
```

---

**Part 4 Complete**: Post-merge verification, production testing strategy, package verification,
installation testing, and cleanup procedures. ✅

**Continue to Part 5** for optimization strategies, troubleshooting guide, and performance
considerations.
