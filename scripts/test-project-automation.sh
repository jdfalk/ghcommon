#!/bin/bash
# file: scripts/test-project-automation.sh
# version: 1.0.0
# guid: a7b8c9d0-e1f2-3456-a012-789012345678

set -euo pipefail

# Script to test GitHub Projects automation by creating test issues

ORG="${ORG:-jdfalk}"
REPOS=("ghcommon" "subtitle-manager" "gcommon" "codex-cli")
LABELS=("bug" "enhancement" "documentation" "testing" "automation")

echo "🧪 Testing GitHub Projects automation across repositories"
echo "This script will create test issues to verify project automation works"
echo ""

# Function to create a test issue
create_test_issue() {
    local repo="$1"
    local label="$2"
    local title="Test Issue for $label automation"
    local body="This is a test issue created to verify that GitHub Projects automation works correctly.

Labels: $label
Repository: $repo
Created by: test-project-automation.sh

This issue should automatically be added to the appropriate GitHub Project based on its label.

Please close this issue after verifying the automation worked."

    echo "Creating test issue in $repo with label '$label'..."

    if gh issue create \
        --repo "$ORG/$repo" \
        --title "$title" \
        --body "$body" \
        --label "$label"; then
        echo "✅ Created test issue in $repo with label '$label'"
    else
        echo "❌ Failed to create test issue in $repo with label '$label'"
    fi
}

# Function to verify authentication
verify_auth() {
    if ! gh auth status >/dev/null 2>&1; then
        echo "❌ GitHub CLI is not authenticated"
        echo "Please run: gh auth login"
        exit 1
    fi
    echo "✅ GitHub CLI authenticated"
}

# Main execution
main() {
    verify_auth

    echo ""
    echo "🚀 Creating test issues across repositories..."
    echo ""

    for repo in "${REPOS[@]}"; do
        echo "Testing repository: $repo"

        # Create one test issue per repo with different labels
        case $repo in
            "ghcommon")
                create_test_issue "$repo" "bug"
                create_test_issue "$repo" "enhancement"
                ;;
            "subtitle-manager")
                create_test_issue "$repo" "feature"
                ;;
            "gcommon")
                create_test_issue "$repo" "documentation"
                ;;
            "codex-cli")
                create_test_issue "$repo" "automation"
                ;;
        esac

        echo ""
    done

    echo "🎉 Test issues created!"
    echo ""
    echo "Next steps:"
    echo "1. Check the Actions tab in each repository to see if workflows triggered"
    echo "2. Verify issues appear in the correct GitHub Projects"
    echo "3. Close test issues after verification"
    echo ""
    echo "Project URLs to check:"
    echo "- Cleanup: https://github.com/users/jdfalk/projects/9"
    echo "- Core Improvements: https://github.com/users/jdfalk/projects/10"
    echo "- Testing & Quality: https://github.com/users/jdfalk/projects/11"
    echo "- Subtitle Manager: https://github.com/users/jdfalk/projects/5"
    echo "- gCommon: https://github.com/users/jdfalk/projects/2"
}

# Run main function
main "$@"
