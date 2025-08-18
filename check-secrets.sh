#!/bin/bash
# file: check-secrets.sh
# version: 1.0.0
# guid: a1b2c3d4-e5f6-7890-abcd-ef1234567890

# Check if all repos have the JF_CI_GH_PAT secret

# Array of repository names
repos=(
    "jdfalk/gcommon"
    "jdfalk/ghcommon"
    "jdfalk/subtitle-manager"
    "jdfalk/copilot-agent-util-rust"
    "jdfalk/apt-cacher-go"
    "jdfalk/audiobook-organizer"
    "jdfalk/merge-srt-subtitles"
    "jdfalk/public-scratch"
)

echo "Checking JF_CI_GH_PAT secret in all repositories..."
echo "=================================================="

missing_repos=()

for repo in "${repos[@]}"; do
    echo -n "Checking $repo... "

    # Use GitHub CLI to check if the secret exists
    # This will return 0 if secret exists, non-zero if it doesn't
    if gh secret list --repo "$repo" | grep -q "JF_CI_GH_PAT"; then
        echo "✅ Found"
    else
        echo "❌ Missing"
        missing_repos+=("$repo")
    fi
done

echo ""
echo "Summary:"
echo "========"

if [ ${#missing_repos[@]} -eq 0 ]; then
    echo "✅ All repositories have the JF_CI_GH_PAT secret!"
else
    echo "❌ The following repositories are missing the JF_CI_GH_PAT secret:"
    for repo in "${missing_repos[@]}"; do
        echo "   - $repo"
    done
    echo ""
    echo "To add the secret to missing repositories, run:"
    for repo in "${missing_repos[@]}"; do
        echo "   gh secret set JF_CI_GH_PAT --repo $repo"
    done
fi
