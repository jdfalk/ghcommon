#!/bin/bash
# file: .github/workflows/scripts/generate-version.sh
# version: 1.0.0
# guid: 0c1d2e3f-4a5b-6c7d-8e9f-0a1b2c3d4e5f

set -euo pipefail

# Generate semantic release version
# Uses environment variables: RELEASE_TYPE, BRANCH_NAME, AUTO_PRERELEASE, AUTO_DRAFT

RELEASE_TYPE="${RELEASE_TYPE:-auto}"
BRANCH_NAME="${BRANCH_NAME}"
AUTO_PRERELEASE="${AUTO_PRERELEASE:-false}"
AUTO_DRAFT="${AUTO_DRAFT:-false}"

# Get the latest tag to determine version increment
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
echo "Latest tag: $LATEST_TAG"

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
