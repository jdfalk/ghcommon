#!/bin/bash
# file: scripts/create-issue-update.sh
# version: 1.1.0
# guid: 7a8b9c0d-1e2f-3a4b-5c6d-7e8f9a0b1c2d
#
# Helper script to create new issue update files with proper UUIDs
#
# Usage:
#   ./scripts/create-issue-update.sh create "Issue Title" "Issue body" "label1,label2"
#   ./scripts/create-issue-update.sh update 123 "Updated body" "label1,label2"
#   ./scripts/create-issue-update.sh comment 123 "Comment text"
#   ./scripts/create-issue-update.sh close 123 "completed"

set -euo pipefail

# Try to locate the library in common locations
LIBRARY_LOCATIONS=(
  # Relative path from current script
  "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/create-issue-update-library.sh"
  # Common checkout locations
  "$HOME/repos/github.com/jdfalk/gcommon/scripts/create-issue-update-library.sh"
  "/Users/jdfalk/repos/github.com/jdfalk/gcommon/scripts/create-issue-update-library.sh"
  # Add other common locations here
)

# Try to download from GitHub if not found locally
GITHUB_RAW_URL="https://raw.githubusercontent.com/jdfalk/gcommon/main/scripts/create-issue-update-library.sh"
TEMP_LIBRARY_PATH="/tmp/create-issue-update-library-$$.sh"

# Function to try sourcing from each location
source_library() {
  for location in "${LIBRARY_LOCATIONS[@]}"; do
    if [[ -f "$location" ]]; then
      echo "Sourcing library from: $location" >&2
      source "$location"
      return 0
    fi
  done

  # If we get here, try downloading from GitHub
  echo "Library not found locally, attempting to download..." >&2
  if command -v curl >/dev/null 2>&1; then
    if curl -s -o "$TEMP_LIBRARY_PATH" "$GITHUB_RAW_URL"; then
      echo "Downloaded library from GitHub" >&2
      source "$TEMP_LIBRARY_PATH"
      rm -f "$TEMP_LIBRARY_PATH"
      return 0
    fi
  elif command -v wget >/dev/null 2>&1; then
    if wget -q -O "$TEMP_LIBRARY_PATH" "$GITHUB_RAW_URL"; then
      echo "Downloaded library from GitHub" >&2
      source "$TEMP_LIBRARY_PATH"
      rm -f "$TEMP_LIBRARY_PATH"
      return 0
    fi
  fi

  echo "Failed to locate or download the library" >&2
  return 1
}

# Try to source the library
if ! source_library; then
  echo "ERROR: Could not locate the create-issue-update-library.sh file." >&2
  echo "Please ensure it exists in one of these locations:" >&2
  for location in "${LIBRARY_LOCATIONS[@]}"; do
    echo "  - $location" >&2
  done
  echo "Or that the script can download it from:" >&2
  echo "  - $GITHUB_RAW_URL" >&2
  exit 1
fi

# Run the main function with all arguments
run_issue_update "$@"
