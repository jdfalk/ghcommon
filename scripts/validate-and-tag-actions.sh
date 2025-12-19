#!/bin/bash
# file: scripts/validate-and-tag-actions.sh
# version: 1.0.0
# guid: 8a3c4567-e89b-12d3-a456-426614174001

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Action repositories
ACTIONS=(
  "release-docker-action"
  "release-go-action"
  "release-frontend-action"
  "release-python-action"
  "release-rust-action"
  "release-protobuf-action"
  "auto-module-tagging-action"
)

BASE_DIR="/Users/jdfalk/repos/github.com/jdfalk"

echo "🔍 GitHub Actions Validation and Tagging Script"
echo "================================================"
echo ""

validate_action() {
  local action_name=$1
  local action_dir="${BASE_DIR}/${action_name}"

  echo "📦 Validating ${action_name}..."

  # Check if directory exists
  if [[ ! -d ${action_dir} ]]; then
    echo -e "${RED}❌ Directory not found: ${action_dir}${NC}"
    return 1
  fi

  cd "${action_dir}"

  # Check for required files
  local required_files=("action.yml" "README.md" ".github/workflows/ci.yml" ".github/workflows/release.yml")
  for file in "${required_files[@]}"; do
    if [[ ! -f ${file} ]]; then
      echo -e "${RED}❌ Missing required file: ${file}${NC}"
      return 1
    fi
  done

  # Validate action.yml syntax
  if ! python3 -c "import yaml; yaml.safe_load(open('action.yml'))" 2>/dev/null; then
    echo -e "${RED}❌ Invalid YAML in action.yml${NC}"
    return 1
  fi

  # Check if git repo is clean
  if [[ -n $(git status --porcelain) ]]; then
    echo -e "${YELLOW}⚠️  Working directory has uncommitted changes${NC}"
    git status --short
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      return 1
    fi
  fi

  echo -e "${GREEN}✅ Validation passed${NC}"
  return 0
}

tag_action() {
  local action_name=$1
  local action_dir="${BASE_DIR}/${action_name}"

  echo "🏷️  Tagging ${action_name}..."

  cd "${action_dir}"

  # Check if tags already exist
  if git tag | grep -q "^v1.0.0$"; then
    echo -e "${YELLOW}⚠️  Tag v1.0.0 already exists${NC}"
    read -p "Delete existing tags and recreate? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      git tag -d v1.0.0 v1.0 v1 2>/dev/null || true
      git push origin :refs/tags/v1.0.0 :refs/tags/v1.0 :refs/tags/v1 2>/dev/null || true
    else
      echo -e "${YELLOW}⏭️  Skipping tagging${NC}"
      return 0
    fi
  fi

  # Create tags (force to allow updates)
  git tag -f -a v1.0.0 -m "Release v1.0.0 - Initial stable release"
  git tag -f v1.0 -m "Release v1.0 - Latest v1.0.x release"
  git tag -f v1 -m "Release v1 - Latest v1.x.x release"

  # Push tags (force to update remote)
  git push -f origin v1.0.0 v1.0 v1

  echo -e "${GREEN}✅ Tags created and pushed${NC}"
}

create_github_release() {
  local action_name=$1
  local action_dir="${BASE_DIR}/${action_name}"

  echo "🚀 Creating GitHub Release for ${action_name}..."

  cd "${action_dir}"

  # Check if release already exists
  if gh release view v1.0.0 &>/dev/null; then
    echo -e "${YELLOW}⚠️  Release v1.0.0 already exists${NC}"
    return 0
  fi

  # Create release
  gh release create v1.0.0 \
    --title "v1.0.0" \
    --notes "Initial stable release of ${action_name}.

## Features
- Fully functional GitHub Action ready for production use
- Comprehensive CI/CD workflows
- Integration tests
- Complete documentation

See README.md for usage details." \
    --latest

  echo -e "${GREEN}✅ GitHub Release created${NC}"
}

# Main execution
main() {
  echo "Starting validation and tagging process..."
  echo ""

  local failed_actions=()

  # Validate all actions first
  for action in "${ACTIONS[@]}"; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    if ! validate_action "${action}"; then
      failed_actions+=("${action}")
      echo -e "${RED}❌ Validation failed for ${action}${NC}"
    fi
    echo ""
  done

  # If any validations failed, stop
  if [[ ${#failed_actions[@]} -gt 0 ]]; then
    echo -e "${RED}❌ Validation failed for the following actions:${NC}"
    for action in "${failed_actions[@]}"; do
      echo -e "${RED}   - ${action}${NC}"
    done
    echo ""
    echo "Please fix the issues and run again."
    exit 1
  fi

  echo -e "${GREEN}✅ All actions validated successfully!${NC}"
  echo ""

  # Ask for confirmation before tagging
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Ready to tag all actions with v1.0.0, v1.0, v1"
  read -p "Proceed with tagging and GitHub releases? (y/N) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
  fi

  # Tag and release all actions
  for action in "${ACTIONS[@]}"; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    tag_action "${action}"
    create_github_release "${action}"
    echo ""
  done

  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo -e "${GREEN}🎉 All actions successfully tagged and released!${NC}"
  echo ""
  echo "Next steps:"
  echo "1. Update ghcommon workflows to use the new actions"
  echo "2. Test the actions in a real workflow"
  echo "3. Update documentation with action references"
}

main
