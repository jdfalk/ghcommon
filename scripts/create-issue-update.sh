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
            local guid="create-$(echo "$title" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-\|-$//g')-$(date +%Y-%m-%d)"

            cat > "$file_path" << EOF
{
  "action": "create",
  "title": "$title",
  "body": "$body",
  "labels": [$(echo "$labels" | sed 's/,/", "/g' | sed 's/^/"/;s/$/"/')],
  "guid": "$guid"
}
EOF
            ;;

        "update")
            local number="$3"
            local body="$4"
            local labels="$5"
            local guid="update-issue-${number}-$(date +%Y-%m-%d)"

            cat > "$file_path" << EOF
{
  "action": "update",
  "number": $number,
  "body": "$body",
  "labels": [$(echo "$labels" | sed 's/,/", "/g' | sed 's/^/"/;s/$/"/')],
  "guid": "$guid"
}
EOF
            ;;

        "comment")
            local number="$3"
            local body="$4"
            local guid="comment-${number}-$(date +%Y-%m-%d-%H%M%S)"

            cat > "$file_path" << EOF
{
  "action": "comment",
  "number": $number,
  "body": "$body",
  "guid": "$guid"
}
EOF
            ;;

        "close")
            local number="$3"
            local state_reason="${4:-completed}"
            local guid="close-issue-${number}-$(date +%Y-%m-%d)"

            cat > "$file_path" << EOF
{
  "action": "close",
  "number": $number,
  "state_reason": "$state_reason",
  "guid": "$guid"
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
