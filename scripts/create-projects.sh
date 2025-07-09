#!/bin/bash
# file: scripts/create-projects.sh
# version: 1.0.0
# guid: f4797552-6742-490f-96f4-3d3f6436630a

set -euo pipefail

# Script to create GitHub Projects using the GitHub CLI.
# Requires GH_TOKEN with 'project' scope or authenticated gh CLI.

ORG="${ORG:-jdfalk}"
REPO="${REPO:-ghcommon}"

create_project() {
  local title="$1"
  local body="$2"
  echo "Creating project: $title"
  gh project create --owner "$ORG" --title "$title" --body "$body"
}

# Example projects based on TODO phases
create_project "ghcommon Cleanup" "Tasks for initial infrastructure cleanup and documentation fixes."
create_project "ghcommon Core Improvements" "Track enhancements and error handling for issue management and workflows."
create_project "ghcommon Testing & Quality" "Work to add unit tests and workflow validation." 

# Link repository to first project (Cleanup)
FIRST_PROJECT_NUMBER=$(gh project list --owner "$ORG" --limit 1 --format json | jq -r '.[0].number')
if [[ -n "$FIRST_PROJECT_NUMBER" ]]; then
  gh project link --owner "$ORG" --repo "$REPO" "$FIRST_PROJECT_NUMBER"
fi
