#!/bin/bash
# file: .github/workflows/scripts/release-strategy.sh
# version: 1.1.0
# guid: 9b0c1d2e-3f4a-5b6c-7d8e-9f0a1b2c3d4e

set -euo pipefail

# Determine release strategy based on branch
# Uses environment variables: BRANCH_NAME, INPUT_PRERELEASE, INPUT_DRAFT

BRANCH_NAME="${BRANCH_NAME}"
INPUT_PRERELEASE="${INPUT_PRERELEASE:-false}"
INPUT_DRAFT="${INPUT_DRAFT:-false}"

# Determine release strategy based on branch and manual inputs
if [[ "$BRANCH_NAME" == "main" ]]; then
    STRATEGY="stable"
    AUTO_PRERELEASE="false"
    AUTO_DRAFT="true"  # Stable releases are drafts for review
elif [[ "$BRANCH_NAME" == "develop" ]]; then
    STRATEGY="prerelease"
    AUTO_PRERELEASE="true"
    AUTO_DRAFT="false"  # Pre-releases are published directly
else
    # Feature branches should create pre-releases (published directly)
    STRATEGY="prerelease"
    AUTO_PRERELEASE="true"
    AUTO_DRAFT="false"  # Pre-releases are published directly
fi

# Override with manual inputs if provided
if [[ "$INPUT_PRERELEASE" == "true" ]]; then
    AUTO_PRERELEASE="true"
fi
if [[ "$INPUT_DRAFT" == "true" ]]; then
    AUTO_DRAFT="true"
fi

echo "strategy=$STRATEGY" >> $GITHUB_OUTPUT
echo "auto-prerelease=$AUTO_PRERELEASE" >> $GITHUB_OUTPUT
echo "auto-draft=$AUTO_DRAFT" >> $GITHUB_OUTPUT

echo "🔄 Release strategy for branch '$BRANCH_NAME': $STRATEGY"
echo "📋 Auto-prerelease: $AUTO_PRERELEASE"
echo "📋 Auto-draft: $AUTO_DRAFT"
