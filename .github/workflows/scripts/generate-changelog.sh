#!/bin/bash
# file: .github/workflows/scripts/generate-changelog.sh
# version: 1.0.0
# guid: 1d2e3f4a-5b6c-7d8e-9f0a-1b2c3d4e5f6a

set -euo pipefail

# Generate changelog based on conventional commits and branch strategy
# Arguments: branch_name, primary_language, release_strategy, auto_prerelease, auto_draft

BRANCH_NAME="${1}"
PRIMARY_LANGUAGE="${2:-unknown}"
RELEASE_STRATEGY="${3:-stable}"
AUTO_PRERELEASE="${4:-false}"
AUTO_DRAFT="${5:-false}"

CHANGELOG="## 🚀 What's Changed\n\n"

# Get commits since last tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [[ -n "$LAST_TAG" ]]; then
    CHANGELOG+="### 📋 Commits since $LAST_TAG:\n"
    while IFS= read -r commit; do
        CHANGELOG+="- $commit\n"
    done < <(git log ${LAST_TAG}..HEAD --oneline --format="%s (%h)")
else
    CHANGELOG+="### 📋 Initial Release Commits:\n"
    while IFS= read -r commit; do
        CHANGELOG+="- $commit\n"
    done < <(git log --oneline --format="%s (%h)")
fi

CHANGELOG+="\n### 🎯 Release Information\n"
CHANGELOG+="- **Branch:** $BRANCH_NAME\n"
CHANGELOG+="- **Release Type:** $RELEASE_STRATEGY\n"
CHANGELOG+="- **Primary Language:** $PRIMARY_LANGUAGE\n"

if [[ "$AUTO_PRERELEASE" == "true" ]]; then
    CHANGELOG+="\n⚠️ **This is a pre-release version** - use for testing purposes.\n"
fi

if [[ "$AUTO_DRAFT" == "true" ]]; then
    CHANGELOG+="\n📝 **This is a draft release** - review before making public.\n"
fi

# Store changelog content for use in release
echo "changelog_content<<EOF" >> $GITHUB_OUTPUT
echo -e "$CHANGELOG" >> $GITHUB_OUTPUT
echo "EOF" >> $GITHUB_OUTPUT
