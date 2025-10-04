#!/bin/bash
# file: .github/workflows/scripts/generate-version.sh
# version: 1.2.0
# guid: 0c1d2e3f-4a5b-6c7d-8e9f-0a1b2c3d4e5f

set -euo pipefail

# Generate semantic release version
# Uses environment variables: RELEASE_TYPE, BRANCH_NAME, AUTO_PRERELEASE, AUTO_DRAFT

RELEASE_TYPE="${RELEASE_TYPE:-auto}"
BRANCH_NAME="${BRANCH_NAME}"
AUTO_PRERELEASE="${AUTO_PRERELEASE:-false}"
AUTO_DRAFT="${AUTO_DRAFT:-false}"

echo "🔍 Detecting latest version..."

# Method 1: Try GitHub API first (more reliable for releases)
if [[ -n "${GITHUB_TOKEN:-}" ]]; then
    echo "📡 Using GitHub API to get latest release..."
    API_RESPONSE=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
        "https://api.github.com/repos/${GITHUB_REPOSITORY}/releases/latest" 2>/dev/null || echo "")

    # Parse JSON without jq dependency
    LATEST_TAG=$(echo "$API_RESPONSE" | grep '"tag_name"' | cut -d'"' -f4 || echo "")

    if [[ -n "$LATEST_TAG" && "$LATEST_TAG" != "null" ]]; then
        echo "✅ Found latest release via API: $LATEST_TAG"
    else
        echo "⚠️ No releases found via API, trying git tags..."
        LATEST_TAG=""
    fi
else
    echo "⚠️ No GITHUB_TOKEN available, skipping API method"
    LATEST_TAG=""
fi

# Method 2: Fallback to git describe
if [[ -z "$LATEST_TAG" ]]; then
    echo "🔧 Using git to find latest tag..."

    # Get all tags sorted by version
    LATEST_TAG=$(git tag -l --sort=-version:refname | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+' | head -n1 || echo "")

    if [[ -n "$LATEST_TAG" ]]; then
        echo "✅ Found latest tag via git: $LATEST_TAG"
    else
        echo "⚠️ No version tags found, using git describe..."
        LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
        echo "📋 Git describe result: $LATEST_TAG"
    fi
fi

# Final fallback
if [[ -z "$LATEST_TAG" || "$LATEST_TAG" == "null" ]]; then
    echo "🆕 No existing tags found, starting with v0.0.0"
    LATEST_TAG="v0.0.0"
fi

echo "📌 Using base version: $LATEST_TAG"

# Extract version numbers (remove 'v' prefix and any suffix)
VERSION_CORE=$(echo "$LATEST_TAG" | sed 's/^v//' | sed 's/-.*//')
IFS='.' read -r MAJOR MINOR PATCH <<< "$VERSION_CORE"

# Default to 0 if any version component is missing
MAJOR=${MAJOR:-0}
MINOR=${MINOR:-0}
PATCH=${PATCH:-0}

echo "Current version: $MAJOR.$MINOR.$PATCH"

# Determine version increment based on release type and branch
if [[ "$RELEASE_TYPE" == "major" ]]; then
    NEW_MAJOR=$((MAJOR + 1))
    NEW_MINOR=0
    NEW_PATCH=0
elif [[ "$RELEASE_TYPE" == "minor" ]]; then
    NEW_MAJOR=$MAJOR
    NEW_MINOR=$((MINOR + 1))
    NEW_PATCH=0
elif [[ "$RELEASE_TYPE" == "patch" ]]; then
    NEW_MAJOR=$MAJOR
    NEW_MINOR=$MINOR
    NEW_PATCH=$((PATCH + 1))
else
    # Auto versioning based on branch and commits
    if [[ "$BRANCH_NAME" == "main" ]]; then
        # Stable release: increment patch
        NEW_MAJOR=$MAJOR
        NEW_MINOR=$MINOR
        NEW_PATCH=$((PATCH + 1))
    elif [[ "$BRANCH_NAME" == "develop" ]]; then
        # Pre-release: increment minor
        NEW_MAJOR=$MAJOR
        NEW_MINOR=$((MINOR + 1))
        NEW_PATCH=0
    else
        # Draft/feature branch: increment patch with branch suffix
        NEW_MAJOR=$MAJOR
        NEW_MINOR=$MINOR
        NEW_PATCH=$((PATCH + 1))
    fi
fi

# Build version string with appropriate suffixes
if [[ "$AUTO_PRERELEASE" == "true" ]]; then
    if [[ "$BRANCH_NAME" == "develop" ]]; then
        VERSION_TAG="v${NEW_MAJOR}.${NEW_MINOR}.${NEW_PATCH}-dev.$(date +%Y%m%d%H%M)"
    else
        # Feature branches get alpha pre-release versions
        SAFE_BRANCH=$(echo "$BRANCH_NAME" | sed 's/[^a-zA-Z0-9]/-/g')
        VERSION_TAG="v${NEW_MAJOR}.${NEW_MINOR}.${NEW_PATCH}-alpha.$(date +%Y%m%d%H%M)"
    fi
else
    # Stable release (will be created as draft)
    VERSION_TAG="v${NEW_MAJOR}.${NEW_MINOR}.${NEW_PATCH}"
fi

echo "Generated version tag: $VERSION_TAG"
echo "tag=$VERSION_TAG" >> $GITHUB_OUTPUT
