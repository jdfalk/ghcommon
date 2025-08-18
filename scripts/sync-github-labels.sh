#!/bin/bash
# file: scripts/sync-github-labels.sh
# version: 1.0.0
# guid: a1b2c3d4-e5f6-7890-abcd-ef1234567890

# GitHub Labels Sync Script
# This script actually manages GitHub repository labels (not just files)
# It reads labels.json and applies them to the repository

set -e

REPO_OWNER="${1:-jdfalk}"
REPO_NAME="${2}"
LABELS_FILE="${3:-labels.json}"
GITHUB_TOKEN="${GITHUB_TOKEN}"

if [ -z "$REPO_NAME" ]; then
    echo "❌ Usage: $0 <owner> <repo-name> [labels-file]"
    echo "   Example: $0 jdfalk gcommon labels.json"
    exit 1
fi

if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ GITHUB_TOKEN environment variable is required"
    exit 1
fi

if [ ! -f "$LABELS_FILE" ]; then
    echo "❌ Labels file not found: $LABELS_FILE"
    exit 1
fi

echo "🏷️  GitHub Labels Sync"
echo "📁 Repository: $REPO_OWNER/$REPO_NAME"
echo "📄 Labels file: $LABELS_FILE"
echo ""

API_BASE="https://api.github.com/repos/$REPO_OWNER/$REPO_NAME"

# Function to make GitHub API calls
github_api() {
    local method="$1"
    local endpoint="$2"
    local data="$3"
    
    if [ -n "$data" ]; then
        curl -s -X "$method" \
            -H "Authorization: token $GITHUB_TOKEN" \
            -H "Accept: application/vnd.github.v3+json" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$API_BASE$endpoint"
    else
        curl -s -X "$method" \
            -H "Authorization: token $GITHUB_TOKEN" \
            -H "Accept: application/vnd.github.v3+json" \
            "$API_BASE$endpoint"
    fi
}

# Get existing labels
echo "📋 Fetching existing labels..."
existing_labels=$(github_api "GET" "/labels")

# Check if we got valid JSON
if ! echo "$existing_labels" | jq empty 2>/dev/null; then
    echo "❌ Failed to fetch existing labels. API response:"
    echo "$existing_labels"
    exit 1
fi

echo "✅ Found $(echo "$existing_labels" | jq length) existing labels"

# Process each label from the JSON file
echo "🔄 Processing labels from $LABELS_FILE..."

jq -c '.[]' "$LABELS_FILE" | while read -r label; do
    name=$(echo "$label" | jq -r '.name')
    color=$(echo "$label" | jq -r '.color')
    description=$(echo "$label" | jq -r '.description // ""')
    
    echo "🏷️  Processing label: $name"
    
    # Check if label already exists
    existing_label=$(echo "$existing_labels" | jq --arg name "$name" '.[] | select(.name == $name)')
    
    if [ -n "$existing_label" ]; then
        # Update existing label
        echo "   📝 Updating existing label..."
        update_data=$(jq -n \
            --arg name "$name" \
            --arg color "$color" \
            --arg description "$description" \
            '{name: $name, color: $color, description: $description}')
        
        response=$(github_api "PATCH" "/labels/$(echo "$name" | jq -r @uri)" "$update_data")
        
        if echo "$response" | jq -e '.name' >/dev/null 2>&1; then
            echo "   ✅ Updated label: $name"
        else
            echo "   ❌ Failed to update label: $name"
            echo "   Response: $response"
        fi
    else
        # Create new label
        echo "   ➕ Creating new label..."
        create_data=$(jq -n \
            --arg name "$name" \
            --arg color "$color" \
            --arg description "$description" \
            '{name: $name, color: $color, description: $description}')
        
        response=$(github_api "POST" "/labels" "$create_data")
        
        if echo "$response" | jq -e '.name' >/dev/null 2>&1; then
            echo "   ✅ Created label: $name"
        else
            echo "   ❌ Failed to create label: $name"
            echo "   Response: $response"
        fi
    fi
done

echo ""
echo "✅ GitHub labels sync completed!"
echo "🔗 View labels: https://github.com/$REPO_OWNER/$REPO_NAME/labels"
