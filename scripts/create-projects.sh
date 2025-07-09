#!/bin/bash
# file: scripts/create-projects.sh
# version: 2.0.0
# guid: f4797552-6742-490f-96f4-3d3f6436630a

set -euo pipefail

# Script to create GitHub Projects using the GitHub CLI.
# Automatically sets up authentication and creates projects with descriptions.

ORG="${ORG:-jdfalk}"
REPO="${REPO:-ghcommon}"

# Function to check and set up authentication
setup_auth() {
    echo "Checking GitHub CLI authentication..."

    # Try to get current auth token
    if ! gh auth token >/dev/null 2>&1; then
        echo "❌ GitHub CLI is not authenticated."
        echo "Please run: gh auth login"
        echo "Make sure to select 'repo' and 'project' scopes when prompted."
        exit 1
    fi

    # Check if we have the required project scopes by trying a simple project command
    echo "Checking project permissions..."
    if ! gh project list --owner "$ORG" >/dev/null 2>&1; then
        echo "⚠️ Missing required project scopes. Refreshing authentication..."
        echo "Requesting project and read:project scopes..."

        if gh auth refresh -s project,read:project; then
            echo "✅ Authentication refreshed with project scopes"
        else
            echo "❌ Failed to refresh authentication with project scopes"
            echo "Please run manually: gh auth refresh -s project,read:project"
            exit 1
        fi
    fi

    # Export token for consistency
    export GH_TOKEN=$(gh auth token)
    echo "✅ GitHub CLI authenticated successfully with project access"
}

# Function to create a project and add description
create_project() {
    local title="$1"
    local description="$2"

    echo "Creating project: $title"

    # Create the project and capture the project number
    local project_data=$(gh project create --owner "$ORG" --title "$title" --format json)
    local project_number=$(echo "$project_data" | jq -r '.number')

    if [[ -n "$project_number" && "$project_number" != "null" ]]; then
        echo "✅ Created project #${project_number}: $title"

        # Add description to the project
        echo "Adding description to project #${project_number}..."
        gh project edit "$project_number" --owner "$ORG" --description "$description"
        echo "✅ Added description to project #${project_number}"

        # Return the project number for linking (without extra output)
        return 0
    else
        echo "❌ Failed to create project: $title"
        return 1
    fi
}

# Function to get project number from a project title
get_project_number() {
    local title="$1"
    gh project list --owner "$ORG" --format json | jq -r ".projects[] | select(.title == \"$title\") | .number"
}

# Function to link repository to project
link_repository() {
    local project_number="$1"
    echo "Linking repository $REPO to project #${project_number}..."

    if gh project link --owner "$ORG" --repo "$REPO" "$project_number"; then
        echo "✅ Successfully linked repository $REPO to project #${project_number}"
    else
        echo "⚠️ Failed to link repository $REPO to project #${project_number}"
        echo "You may need to link it manually via the GitHub web interface"
    fi
}

# Main execution
main() {
    echo "🚀 Starting GitHub Projects creation for $ORG/$REPO"

    # Set up authentication
    setup_auth

    # Store project numbers for potential linking
    declare -a project_numbers=()

    # Create projects based on TODO phases
    echo ""
    echo "Creating projects..."

    if create_project "ghcommon Cleanup" "Tasks for initial infrastructure cleanup and documentation fixes. Includes fixing broken scripts, updating documentation, and resolving configuration issues."; then
        project_num=$(get_project_number "ghcommon Cleanup")
        project_numbers+=("$project_num")
    fi

    echo ""
    if create_project "ghcommon Core Improvements" "Track enhancements and error handling for issue management and workflows. Focus on improving robustness and adding new features to existing automation."; then
        project_num=$(get_project_number "ghcommon Core Improvements")
        project_numbers+=("$project_num")
    fi

    echo ""
    if create_project "ghcommon Testing & Quality" "Work to add unit tests and workflow validation. Ensure all automation is properly tested and maintainable."; then
        project_num=$(get_project_number "ghcommon Testing & Quality")
        project_numbers+=("$project_num")
    fi

    # Link repository to the first project (Cleanup) if it was created successfully
    if [[ ${#project_numbers[@]} -gt 0 ]]; then
        echo ""
        echo "Linking repository to primary project..."
        link_repository "${project_numbers[0]}"
    fi

    echo ""
    echo "🎉 Project creation completed!"
    echo "Created ${#project_numbers[@]} projects for $ORG/$REPO"

    # List the created projects
    echo ""
    echo "📋 Project summary:"
    gh project list --owner "$ORG" --format json | jq -r '.projects[] | "  • #\(.number): \(.title)"'
}

# Run main function
main "$@"
