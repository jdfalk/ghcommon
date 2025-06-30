#!/bin/bash
# file: scripts/create-issue-update-library.sh
# version: 1.1.0
# guid: 4a81c3e0-5f7b-4e2a-b92d-6c8a7c1d3e5f
#
# Library of functions for creating GitHub issue update files
# This file is meant to be sourced by other scripts, not executed directly

# Function to generate legacy GUID for backward compatibility
generate_legacy_guid() {
    local action="$1"
    local title_or_number="$2"
    local date=$(date +%Y-%m-%d)

    case "$action" in
        "create")
            # For create actions, use title
            local clean_title=$(echo "$title_or_number" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^\-|-$//g')
            echo "create-${clean_title}-${date}"
            ;;
        "update"|"comment"|"close")
            # For other actions, use issue number
            echo "${action}-issue-${title_or_number}-${date}"
            ;;
        *)
            echo "${action}-${date}"
            ;;
    esac
}

# Function to generate UUID
generate_uuid() {
    if command -v uuidgen >/dev/null 2>&1; then
        uuidgen | tr '[:upper:]' '[:lower:]'
    elif command -v python3 >/dev/null 2>&1; then
        python3 -c "import uuid; print(str(uuid.uuid4()))"
    else
        echo "Error: Neither uuidgen nor python3 is available for UUID generation" >&2
        exit 1
    fi
}

# Function to check if issue already exists on GitHub
check_github_issue_exists() {
    local title="$1"
    local repo="${GITHUB_REPOSITORY:-$(git remote get-url origin | sed 's/.*github.com[:/]\(.*\)\.git/\1/')}"
    local token="${GITHUB_TOKEN:-${GH_TOKEN}}"

    if [[ -z "$token" ]]; then
        echo "Warning: No GitHub token found. Skipping GitHub issue check." >&2
        return 1
    fi

    # Search for issues with matching title
    local search_result=$(curl -s -H "Authorization: token $token" \
        "https://api.github.com/repos/$repo/issues?state=all" | \
        python3 -c "
import sys, json
data = json.load(sys.stdin)
title = '''$title'''
for issue in data:
    if issue.get('title', '').strip() == title.strip():
        print(f\"exists:{issue['number']}:{issue['state']}:{issue['html_url']}\")
        sys.exit(0)
print('not_found')
")

    if [[ "$search_result" == exists:* ]]; then
        IFS=':' read -r _ issue_number state url <<< "$search_result"
        echo "⚠️  Issue already exists: #$issue_number (state: $state)" >&2
        echo "   URL: $url" >&2
        return 0
    fi

    return 1
}

# Function to check if GUID is unique across the project
check_guid_unique() {
    local guid="$1"
    local project_root="$(pwd)"

    # Check if Python smart migration script exists
    if [[ -f "scripts/smart-issue-migration.py" ]]; then
        # Use Python script to validate uniqueness
        python3 -c "
import sys
sys.path.append('scripts')
from smart_issue_migration import validate_guid_uniqueness_in_project, SmartMigrator
import os

migrator = SmartMigrator('$project_root')
analysis = migrator.analyze_guid_duplicates()

# Check if the GUID already exists
if '$guid' in analysis['guid_map']:
    print('duplicate')
    sys.exit(1)
else:
    print('unique')
    sys.exit(0)
" 2>/dev/null || {
            # Fallback if Python script fails
            if grep -r "\"$guid\"" .github/issue-updates/ >/dev/null 2>&1 || \
               grep -r "\"$guid\"" issue_updates.json >/dev/null 2>&1; then
                echo "duplicate"
                return 1
            else
                echo "unique"
                return 0
            fi
        }
    else
        # Fallback: simple grep search
        if grep -r "\"$guid\"" .github/issue-updates/ >/dev/null 2>&1 || \
           grep -r "\"$guid\"" issue_updates.json >/dev/null 2>&1; then
            echo "duplicate"
            return 1
        else
            echo "unique"
            return 0
        fi
    fi
}

# Function to generate a guaranteed unique GUID
generate_unique_guid() {
    local max_attempts=10
    local attempt=1

    while [[ $attempt -le $max_attempts ]]; do
        local new_guid
        new_guid=$(generate_uuid)

        if check_guid_unique "$new_guid" | grep -q "unique"; then
            echo "$new_guid"
            return 0
        fi

        echo "⚠️  GUID collision detected (attempt $attempt/$max_attempts), generating new one..." >&2
        ((attempt++))
    done

    echo "❌ Failed to generate unique GUID after $max_attempts attempts" >&2
    exit 1
}

# Function to create JSON file
create_issue_file() {
    local action="$1"
    local uuid="$2"
    local file_path=".github/issue-updates/${uuid}.json"

    # Ensure directory exists
    mkdir -p ".github/issue-updates"

    case "$action" in
        "create")
            local title="$3"
            local body="$4"
            local labels="$5"
            local parent_issue="$6"  # New parameter for sub-issues
            local guid
            local legacy_guid

            # Check if issue already exists on GitHub
            if check_github_issue_exists "$title"; then
                echo "❌ Skipping creation: Issue with this title already exists on GitHub" >&2
                return 1
            fi

            guid=$(generate_unique_guid)
            legacy_guid=$(generate_legacy_guid "create" "$title")

            # Build JSON with optional parent_issue field
            local json_content="{
  \"action\": \"create\",
  \"title\": \"$title\",
  \"body\": \"$body\",
  \"labels\": [$(echo "$labels" | sed 's/,/", "/g' | sed 's/^/"/;s/$/"/')],
  \"guid\": \"$guid\",
  \"legacy_guid\": \"$legacy_guid\""

            # Add parent_issue if provided
            if [[ -n "$parent_issue" ]]; then
                json_content+=",
  \"parent_issue\": $parent_issue"
            fi

            json_content+="
}"

            echo "$json_content" > "$file_path"
            ;;

        "update")
            local number="$3"
            local body="$4"
            local labels="$5"
            local guid
            local legacy_guid
            guid=$(generate_unique_guid)
            legacy_guid=$(generate_legacy_guid "update" "$number")

            cat > "$file_path" << EOF
{
  "action": "update",
  "number": $number,
  "body": "$body",
  "labels": [$(echo "$labels" | sed 's/,/", "/g' | sed 's/^/"/;s/$/"/')],
  "guid": "$guid",
  "legacy_guid": "$legacy_guid"
}
EOF
            ;;

        "comment")
            local number="$3"
            local body="$4"
            local guid
            local legacy_guid
            guid=$(generate_unique_guid)
            legacy_guid=$(generate_legacy_guid "comment" "$number")

            cat > "$file_path" << EOF
{
  "action": "comment",
  "number": $number,
  "body": "$body",
  "guid": "$guid",
  "legacy_guid": "$legacy_guid"
}
EOF
            ;;

        "close")
            local number="$3"
            local state_reason="${4:-completed}"
            local guid
            local legacy_guid
            guid=$(generate_unique_guid)
            legacy_guid=$(generate_legacy_guid "close" "$number")

            cat > "$file_path" << EOF
{
  "action": "close",
  "number": $number,
  "state_reason": "$state_reason",
  "guid": "$guid",
  "legacy_guid": "$legacy_guid"
}
EOF
            ;;

        *)
            echo "Error: Unknown action '$action'" >&2
            echo "Supported actions: create, update, comment, close" >&2
            exit 1
            ;;
    esac

    echo "✅ Created: $file_path"
    echo "📄 UUID: $uuid"
    echo "🔧 Action: $action"
}

# Main function to handle command line arguments
run_issue_update() {
    if [[ $# -lt 2 ]]; then
        echo "Usage:"
        echo "  $0 create \"Title\" \"Body\" \"label1,label2\" [parent_issue_number]"
        echo "  $0 update NUMBER \"Body\" \"label1,label2\""
        echo "  $0 comment NUMBER \"Comment text\""
        echo "  $0 close NUMBER [state_reason]"
        return 1
    fi

    local action="$1"
    local uuid=$(generate_uuid)

    case "$action" in
        "create")
            if [[ $# -lt 4 ]]; then
                echo "Error: create requires title, body, and labels" >&2
                echo "Usage: $0 create \"Title\" \"Body\" \"label1,label2\" [parent_issue_number]" >&2
                return 1
            fi
            create_issue_file "$action" "$uuid" "$2" "$3" "${4:-}" "${5:-}"
            ;;
        "update")
            if [[ $# -lt 4 ]]; then
                echo "Error: update requires number, body, and labels" >&2
                return 1
            fi
            create_issue_file "$action" "$uuid" "$2" "$3" "${4:-}"
            ;;
        "comment")
            if [[ $# -lt 3 ]]; then
                echo "Error: comment requires number and body" >&2
                return 1
            fi
            create_issue_file "$action" "$uuid" "$2" "$3"
            ;;
        "close")
            if [[ $# -lt 2 ]]; then
                echo "Error: close requires number" >&2
                return 1
            fi
            create_issue_file "$action" "$uuid" "$2" "${3:-completed}"
            ;;
        *)
            echo "Error: Unknown action '$action'" >&2
            echo "Supported actions: create, update, comment, close" >&2
            return 1
            ;;
    esac
}
