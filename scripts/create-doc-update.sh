#!/bin/bash
# file: scripts/create-doc-update.sh
# version: 1.0.0
# guid: 4db28a8c-33e2-4853-9f0c-1d8283720bd1

set -euo pipefail

print_usage() {
  echo "Usage: $0 FILE CONTENT [MODE]" >&2
  echo "MODE defaults to 'append'" >&2
}

generate_uuid() {
  if command -v uuidgen >/dev/null 2>&1; then
    uuidgen | tr '[:upper:]' '[:lower:]'
  else
    python3 -c 'import uuid; print(uuid.uuid4())'
  fi
}

create_update() {
  local file="$1"
  local content="$2"
  local mode="${3:-append}"
  local uuid="$(generate_uuid)"
  local dir=".github/doc-updates"
  mkdir -p "$dir"
  local path="$dir/${uuid}.json"
  jq -n --arg file "$file" --arg mode "$mode" --arg content "$content" \
    --arg guid "$uuid" '{file:$file, mode:$mode, content:$content, guid:$guid}' \
    > "$path"
  echo "Created doc update: $path"
}

if [[ $# -lt 2 ]]; then
  print_usage
  exit 1
fi

create_update "$1" "$2" "${3:-append}"
