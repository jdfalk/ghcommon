#!/bin/bash
# file: .github/workflows/scripts/test-scripts.sh
# version: 1.1.0
# guid: 2e3f4a5b-6c7d-8e9f-0a1b-2c3d4e5f6a7b

set -euo pipefail

# Test script for workflow scripts
echo "🧪 Testing workflow scripts..."

# Create temporary directory for testing
TEST_DIR=$(mktemp -d)
cd "$TEST_DIR"

# Initialize test git repo
git init
git config user.email "test@example.com"
git config user.name "Test User"

# Create some test files to simulate different project types
echo '{}' >package.json
echo 'module example.com/test' >go.mod
touch main.go
echo '[package]' >Cargo.toml
echo 'name = "test"' >>Cargo.toml
echo 'version = "0.1.0"' >>Cargo.toml
echo 'edition = "2021"' >>Cargo.toml
touch buf.yaml

# Test language detection script
echo "Testing language detection..."
GITHUB_OUTPUT="$TEST_DIR/github_output"
export GITHUB_OUTPUT

# Set environment variables for testing
export SKIP_LANGUAGE_DETECTION="false"
export GO_ENABLED="false"
export PYTHON_ENABLED="false"
export RUST_ENABLED="false"
export FRONTEND_ENABLED="false"
export DOCKER_ENABLED="false"
export PROTOBUF_ENABLED="false"

# Run the detect-languages script
bash "$OLDPWD/.github/workflows/scripts/detect-languages.sh"

# Check output
if grep -q "has-go=true" "$GITHUB_OUTPUT"; then
  echo "✅ Go detection working"
else
  echo "❌ Go detection failed"
fi

if grep -q "has-frontend=true" "$GITHUB_OUTPUT"; then
  echo "✅ Frontend detection working"
else
  echo "❌ Frontend detection failed"
fi

if grep -q "has-rust=true" "$GITHUB_OUTPUT"; then
  echo "✅ Rust detection working"
else
  echo "❌ Rust detection failed"
fi

if grep -q "protobuf-needed=true" "$GITHUB_OUTPUT"; then
  echo "✅ Protobuf detection working"
else
  echo "❌ Protobuf detection failed"
fi

# Test release strategy script
echo "Testing release strategy..."
rm -f "$GITHUB_OUTPUT"

export BRANCH_NAME="main"
export INPUT_PRERELEASE="false"
export INPUT_DRAFT="false"
bash "$OLDPWD/.github/workflows/scripts/release-strategy.sh"
if grep -q "strategy=stable" "$GITHUB_OUTPUT" && grep -q "auto-draft=true" "$GITHUB_OUTPUT"; then
  echo "✅ Main branch strategy working (stable release as draft)"
else
  echo "❌ Main branch strategy failed"
  echo "Expected: strategy=stable, auto-draft=true"
  grep "strategy=\|auto-draft=" "$GITHUB_OUTPUT" || echo "No strategy/draft output found"
fi

rm -f "$GITHUB_OUTPUT"
export BRANCH_NAME="develop"
export INPUT_PRERELEASE="false"
export INPUT_DRAFT="false"
bash "$OLDPWD/.github/workflows/scripts/release-strategy.sh"
if grep -q "strategy=prerelease" "$GITHUB_OUTPUT" && grep -q "auto-draft=false" "$GITHUB_OUTPUT"; then
  echo "✅ Develop branch strategy working (prerelease published directly)"
else
  echo "❌ Develop branch strategy failed"
  echo "Expected: strategy=prerelease, auto-draft=false"
  grep "strategy=\|auto-draft=" "$GITHUB_OUTPUT" || echo "No strategy/draft output found"
fi

rm -f "$GITHUB_OUTPUT"
export BRANCH_NAME="feature/test"
export INPUT_PRERELEASE="false"
export INPUT_DRAFT="false"
bash "$OLDPWD/.github/workflows/scripts/release-strategy.sh"
if grep -q "strategy=prerelease" "$GITHUB_OUTPUT" && grep -q "auto-draft=false" "$GITHUB_OUTPUT"; then
  echo "✅ Feature branch strategy working (prerelease published directly)"
else
  echo "❌ Feature branch strategy failed"
  echo "Expected: strategy=prerelease, auto-draft=false"
  grep "strategy=\|auto-draft=" "$GITHUB_OUTPUT" || echo "No strategy/draft output found"
fi

# Create a test commit and tag for version testing
echo "test" >test.txt
git add test.txt
git commit -m "test: initial commit"
git tag v1.0.0

# Test version generation script
echo "Testing version generation..."
rm -f "$GITHUB_OUTPUT"

export RELEASE_TYPE="auto"
export BRANCH_NAME="main"
export AUTO_PRERELEASE="false"
export AUTO_DRAFT="false"
bash "$OLDPWD/.github/workflows/scripts/generate-version.sh"
if grep -q "tag=v1.0.1" "$GITHUB_OUTPUT"; then
  echo "✅ Main branch version increment working"
else
  echo "❌ Main branch version increment failed"
  grep "tag=" "$GITHUB_OUTPUT" || echo "No tag output found"
fi

# Test changelog generation
echo "Testing changelog generation..."
rm -f "$GITHUB_OUTPUT"

export BRANCH_NAME="main"
export PRIMARY_LANGUAGE="go"
export RELEASE_STRATEGY="stable"
export AUTO_PRERELEASE="false"
export AUTO_DRAFT="false"
bash "$OLDPWD/.github/workflows/scripts/generate-changelog.sh"
if grep -q "changelog_content" "$GITHUB_OUTPUT"; then
  echo "✅ Changelog generation working"
else
  echo "❌ Changelog generation failed"
fi

# Cleanup
cd "$OLDPWD"
rm -rf "$TEST_DIR"

echo "🎉 All tests completed!"
