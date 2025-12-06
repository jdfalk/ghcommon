#!/bin/bash
# file: .github/workflows/scripts/generate-version.sh
# version: 1.3.1
# guid: 0c1d2e3f-4a5b-6c7d-8e9f-0a1b2c3d4e5f

set -euo pipefail

# Generate semantic release version
# Uses environment variables: RELEASE_TYPE, BRANCH_NAME, AUTO_PRERELEASE, AUTO_DRAFT

RELEASE_TYPE="${RELEASE_TYPE:-auto}"
BRANCH_NAME="${BRANCH_NAME}"
AUTO_PRERELEASE="${AUTO_PRERELEASE:-false}"
AUTO_DRAFT="${AUTO_DRAFT:-false}"
OUTPUT_PATH="${GITHUB_OUTPUT:-}"

echo "🔍 Detecting latest version..."

# Method 1: Try GitHub API first (more reliable for releases)
if [[ -n ${GITHUB_TOKEN:-} ]]; then
  echo "📡 Using GitHub API to get latest release..."
  API_RESPONSE=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
    "https://api.github.com/repos/${GITHUB_REPOSITORY}/releases/latest" 2>/dev/null || echo "")

  # Parse JSON without jq dependency
  LATEST_TAG=$(echo "$API_RESPONSE" | grep '"tag_name"' | cut -d'"' -f4 || echo "")

  if [[ -n $LATEST_TAG && $LATEST_TAG != "null" ]]; then
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
if [[ -z $LATEST_TAG ]]; then
  echo "🔧 Using git to find latest tag..."

  # Get all tags sorted by version
  LATEST_TAG=$(git tag -l --sort=-version:refname | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+' | head -n1 || echo "")

  if [[ -n $LATEST_TAG ]]; then
    echo "✅ Found latest tag via git: $LATEST_TAG"
  else
    echo "⚠️ No version tags found, using git describe..."
    LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
    echo "📋 Git describe result: $LATEST_TAG"
  fi
fi

# Final fallback
if [[ -z $LATEST_TAG || $LATEST_TAG == "null" ]]; then
  echo "🆕 No existing tags found, starting with v0.0.0"
  LATEST_TAG="v0.0.0"
fi

echo "📌 Using base version: $LATEST_TAG"

# Extract version numbers (remove 'v' prefix and any suffix)
VERSION_CORE=$(echo "$LATEST_TAG" | sed 's/^v//' | sed 's/-.*//')
IFS='.' read -r MAJOR MINOR PATCH <<<"$VERSION_CORE"

# Default to 0 if any version component is missing
MAJOR=${MAJOR:-0}
MINOR=${MINOR:-0}
PATCH=${PATCH:-0}

echo "Current version: $MAJOR.$MINOR.$PATCH"

# Determine version increment based on release type and branch
if [[ $RELEASE_TYPE == "major" ]]; then
  NEW_MAJOR=$((MAJOR + 1))
  NEW_MINOR=0
  NEW_PATCH=0
elif [[ $RELEASE_TYPE == "minor" ]]; then
  NEW_MAJOR=$MAJOR
  NEW_MINOR=$((MINOR + 1))
  NEW_PATCH=0
elif [[ $RELEASE_TYPE == "patch" ]]; then
  NEW_MAJOR=$MAJOR
  NEW_MINOR=$MINOR
  NEW_PATCH=$((PATCH + 1))
else
  # Auto versioning based on branch and commits
  if [[ $BRANCH_NAME == "main" ]]; then
    # Stable release: increment patch
    NEW_MAJOR=$MAJOR
    NEW_MINOR=$MINOR
    NEW_PATCH=$((PATCH + 1))
  elif [[ $BRANCH_NAME == "develop" ]]; then
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
if [[ $AUTO_PRERELEASE == "true" ]]; then
  if [[ $BRANCH_NAME == "develop" ]]; then
    VERSION_TAG="v${NEW_MAJOR}.${NEW_MINOR}.${NEW_PATCH}-dev.$(date +%Y%m%d%H%M)"
  else
    # Feature branches get alpha pre-release versions
    SAFE_BRANCH=${BRANCH_NAME//[^a-zA-Z0-9]/-}
    VERSION_TAG="v${NEW_MAJOR}.${NEW_MINOR}.${NEW_PATCH}-alpha.$(date +%Y%m%d%H%M)"
  fi
else
  # Stable release (will be created as draft)
  VERSION_TAG="v${NEW_MAJOR}.${NEW_MINOR}.${NEW_PATCH}"
fi

echo "Generated version tag: $VERSION_TAG"

# Check if the tag already exists and handle conflicts
echo "🔍 Checking for existing tag conflicts..."
if git tag -l | grep -q "^${VERSION_TAG}$"; then
  echo "⚠️ Tag $VERSION_TAG already exists!"

  # For workflow_dispatch or manual releases, we'll force overwrite
  if [[ ${GITHUB_EVENT_NAME:-} == "workflow_dispatch" ]]; then
    echo "🔄 Manual release detected, will force-overwrite existing tag"

    # Delete local tag if it exists
    if git tag -l | grep -q "^${VERSION_TAG}$"; then
      echo "🗑️ Deleting local tag $VERSION_TAG"
      git tag -d "$VERSION_TAG" || echo "⚠️ Could not delete local tag"
    fi

    # Delete remote tag if it exists (requires GITHUB_TOKEN)
    if [[ -n ${GITHUB_TOKEN:-} ]]; then
      echo "🗑️ Deleting remote tag $VERSION_TAG"
      git push origin ":refs/tags/$VERSION_TAG" 2>/dev/null || echo "⚠️ Remote tag may not exist or could not be deleted"
    fi

    echo "✅ Tag cleanup complete, will create fresh tag"
  else
    # For automatic releases, increment to avoid conflicts
    echo "🔢 Automatic release detected, incrementing to avoid conflict"
    CONFLICT_COUNTER=1
    ORIGINAL_VERSION_TAG="$VERSION_TAG"

    while git tag -l | grep -q "^${VERSION_TAG}$"; do
      if [[ $AUTO_PRERELEASE == "true" ]]; then
        # For prerelease, add to the suffix
        if [[ $BRANCH_NAME == "develop" ]]; then
          VERSION_TAG="v${NEW_MAJOR}.${NEW_MINOR}.${NEW_PATCH}-dev.$(date +%Y%m%d%H%M).${CONFLICT_COUNTER}"
        else
          VERSION_TAG="v${NEW_MAJOR}.${NEW_MINOR}.${NEW_PATCH}-alpha.$(date +%Y%m%d%H%M).${CONFLICT_COUNTER}"
        fi
      else
        # For stable release, increment patch
        NEW_PATCH=$((NEW_PATCH + 1))
        VERSION_TAG="v${NEW_MAJOR}.${NEW_MINOR}.${NEW_PATCH}"
      fi
      CONFLICT_COUNTER=$((CONFLICT_COUNTER + 1))

      # Safety valve to prevent infinite loops
      if [[ $CONFLICT_COUNTER -gt 10 ]]; then
        echo "❌ Too many tag conflicts, using timestamp-based version"
        VERSION_TAG="v${NEW_MAJOR}.${NEW_MINOR}.${NEW_PATCH}-build.$(date +%Y%m%d%H%M%S)"
        break
      fi
    done

    echo "🆕 Resolved to new version: $VERSION_TAG"
  fi
else
  echo "✅ No tag conflicts found"
fi

if [ -n "$OUTPUT_PATH" ]; then
  echo "tag=$VERSION_TAG" >>"$OUTPUT_PATH"
fi
