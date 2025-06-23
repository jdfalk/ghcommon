#!/bin/bash
# file: scripts/create-issue-update.sh
# version: 1.0.0
# last-updated: 2025-06-21
#
# Helper script to create new issue update files with proper UUIDs
#
# Usage:
#   ./scripts/create-issue-update.sh create "Issue Title" "Issue body" "label1,label2"
#   ./scripts/create-issue-update.sh update 123 "Updated body" "label1,label2"
#   ./scripts/create-issue-update.sh comment 123 "Comment text"
#   ./scripts/create-issue-update.sh close 123 "completed"

set -euo pipefail

# Function to generate legacy GUID for backward compatibility
generate_legacy_guid() {
    local action="$1"
    local title_or_number="$2"
    local date=$(date +%Y-%m-%d)

    case "$action" in
        "create")
            # For create actions, use title
            local clean_title=$(echo "$title_or_number" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-\|-$//g')
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

# Function to check if GUID is unique across the project
check_guid_unique() {
    local guid="$1"
    local project_root="$(pwd)"

    # Fallback: simple grep search (ghcommon doesn't have smart-issue-migration.py)
    if grep -r "\"$guid\"" .github/issue-updates/ >/dev/null 2>&1 || \
       grep -r "\"$guid\"" issue_updates.json >/dev/null 2>&1; then
        echo "duplicate"
        return 1
    else
        echo "unique"
        return 0
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
            local guid
            local legacy_guid
            guid=$(generate_unique_guid)
            legacy_guid=$(generate_legacy_guid "create" "$title")

            cat > "$file_path" << EOF
{
  "action": "create",
  "title": "$title",
  "body": "$body",
  "labels": [$(echo "$labels" | sed 's/,/", "/g' | sed 's/^/"/;s/$/"/')],
  "guid": "$guid",
  "legacy_guid": "$legacy_guid"
}
EOF
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

# Main script logic
if [[ $# -lt 2 ]]; then
    echo "Usage:"
    echo "  $0 create \"Title\" \"Body\" \"label1,label2\""
    echo "  $0 update NUMBER \"Body\" \"label1,label2\""
    echo "  $0 comment NUMBER \"Comment text\""
    echo "  $0 close NUMBER [state_reason]"
    exit 1
fi

action="$1"
uuid=$(generate_uuid)

case "$action" in
    "create")
        if [[ $# -lt 4 ]]; then
            echo "Error: create requires title, body, and labels" >&2
            exit 1
        fi
        create_issue_file "$action" "$uuid" "$2" "$3" "${4:-}"
        ;;
    "update")
        if [[ $# -lt 4 ]]; then
            echo "Error: update requires number, body, and labels" >&2
            exit 1
        fi
        create_issue_file "$action" "$uuid" "$2" "$3" "${4:-}"
        ;;
    "comment")
        if [[ $# -lt 3 ]]; then
            echo "Error: comment requires number and body" >&2
            exit 1
        fi
        create_issue_file "$action" "$uuid" "$2" "$3"
        ;;
    "close")
        if [[ $# -lt 2 ]]; then
            echo "Error: close requires number" >&2
            exit 1
        fi
        create_issue_file "$action" "$uuid" "$2" "${3:-completed}"
        ;;
    *)
        echo "Error: Unknown action '$action'" >&2
        exit 1
        ;;
esac
