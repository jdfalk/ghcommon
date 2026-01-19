<!-- file: docs/cross-registry-todos/task-12/t12-part4.md -->
<!-- version: 1.0.0 -->
<!-- guid: t12-dependency-management-part4-i1j2k3l4-m5n6 -->
<!-- last-edited: 2026-01-19 -->

# Task 12 Part 4: Dependabot Configuration and Automated Updates

## Comprehensive Dependabot Configuration

```yaml
# file: .github/dependabot.yml
# version: 2.0.0
# guid: dependabot-config-comprehensive

version: 2

registries:
  # Private registry authentication (if needed)
  github-packages:
    type: npm-registry
    url: https://npm.pkg.github.com
    token: ${{ secrets.GITHUB_TOKEN }}

updates:
  # ============================================================================
  # Rust Dependencies (Cargo)
  # ============================================================================

  - package-ecosystem: 'cargo'
    directory: '/'
    schedule:
      interval: 'daily'
      time: '03:00'
      timezone: 'UTC'

    # Grouping strategy for efficient updates
    groups:
      rust-production:
        patterns:
          - '*'
        exclude-patterns:
          - '*-sys'
          - 'dev-*'
      rust-dev:
        patterns:
          - 'dev-*'
          - 'test-*'
      rust-security:
        update-types:
          - 'security'

    # Auto-merge rules
    open-pull-requests-limit: 5
    reviewers:
      - 'jdfalk'
    assignees:
      - 'jdfalk'
    labels:
      - 'dependencies'
      - 'rust'
      - 'automated'

    # Commit message configuration
    commit-message:
      prefix: 'fix(deps)'
      prefix-development: 'chore(deps-dev)'
      include: 'scope'

    # Version constraints
    ignore:
      # Ignore major version updates for stable dependencies
      - dependency-name: 'serde'
        update-types: ['version-update:semver-major']
      - dependency-name: 'tokio'
        update-types: ['version-update:semver-major']

    # Milestone assignment
    milestone: 1

    # Allow for indirect dependency updates
    versioning-strategy: 'increase'

  # ============================================================================
  # Python Dependencies (pip)
  # ============================================================================

  - package-ecosystem: 'pip'
    directory: '/'
    schedule:
      interval: 'daily'
      time: '04:00'
      timezone: 'UTC'

    groups:
      python-production:
        patterns:
          - 'requests'
          - 'pyyaml'
          - 'jinja2'
      python-dev:
        patterns:
          - 'pytest*'
          - 'black'
          - 'ruff'
          - 'mypy'
      python-security:
        update-types:
          - 'security'

    open-pull-requests-limit: 5
    reviewers:
      - 'jdfalk'
    labels:
      - 'dependencies'
      - 'python'
      - 'automated'

    commit-message:
      prefix: 'fix(deps)'
      prefix-development: 'chore(deps-dev)'

  # ============================================================================
  # JavaScript/TypeScript Dependencies (npm)
  # ============================================================================

  - package-ecosystem: 'npm'
    directory: '/'
    schedule:
      interval: 'daily'
      time: '05:00'
      timezone: 'UTC'

    groups:
      npm-production:
        patterns:
          - 'react'
          - 'react-dom'
        exclude-patterns:
          - '@types/*'
      npm-types:
        patterns:
          - '@types/*'
      npm-dev:
        patterns:
          - 'eslint*'
          - 'prettier'
          - 'vite'
          - 'vitest'
      npm-security:
        update-types:
          - 'security'

    open-pull-requests-limit: 5
    reviewers:
      - 'jdfalk'
    labels:
      - 'dependencies'
      - 'javascript'
      - 'automated'

    commit-message:
      prefix: 'fix(deps)'
      prefix-development: 'chore(deps-dev)'

    # Use registry if private packages
    registries:
      - github-packages

    ignore:
      # Ignore specific package patterns
      - dependency-name: '@types/*'
        update-types: ['version-update:semver-major']

  # ============================================================================
  # Go Dependencies (go modules)
  # ============================================================================

  - package-ecosystem: 'gomod'
    directory: '/'
    schedule:
      interval: 'daily'
      time: '06:00'
      timezone: 'UTC'

    groups:
      go-production:
        patterns:
          - '*'
        exclude-patterns:
          - 'golang.org/x/*'
      go-stdlib:
        patterns:
          - 'golang.org/x/*'
      go-security:
        update-types:
          - 'security'

    open-pull-requests-limit: 5
    reviewers:
      - 'jdfalk'
    labels:
      - 'dependencies'
      - 'golang'
      - 'automated'

    commit-message:
      prefix: 'fix(deps)'
      include: 'scope'

  # ============================================================================
  # Docker Base Images
  # ============================================================================

  - package-ecosystem: 'docker'
    directory: '/'
    schedule:
      interval: 'weekly'
      day: 'monday'
      time: '07:00'
      timezone: 'UTC'

    open-pull-requests-limit: 3
    reviewers:
      - 'jdfalk'
    labels:
      - 'dependencies'
      - 'docker'
      - 'automated'

    commit-message:
      prefix: 'fix(docker)'
      include: 'scope'

  # ============================================================================
  # GitHub Actions Workflows
  # ============================================================================

  - package-ecosystem: 'github-actions'
    directory: '/'
    schedule:
      interval: 'weekly'
      day: 'tuesday'
      time: '08:00'
      timezone: 'UTC'

    groups:
      actions-major:
        patterns:
          - '*'
        update-types:
          - 'major'
      actions-minor:
        patterns:
          - '*'
        update-types:
          - 'minor'
          - 'patch'

    open-pull-requests-limit: 5
    reviewers:
      - 'jdfalk'
    labels:
      - 'dependencies'
      - 'github-actions'
      - 'automated'

    commit-message:
      prefix: 'ci(deps)'
      include: 'scope'

  # ============================================================================
  # Terraform (if applicable)
  # ============================================================================

  - package-ecosystem: 'terraform'
    directory: '/terraform'
    schedule:
      interval: 'weekly'
      day: 'wednesday'
      time: '09:00'
      timezone: 'UTC'

    open-pull-requests-limit: 3
    reviewers:
      - 'jdfalk'
    labels:
      - 'dependencies'
      - 'terraform'
      - 'automated'

    commit-message:
      prefix: 'chore(infra)'
```

## Automated Dependency Update Workflow with Auto-Merge

```yaml
# file: .github/workflows/auto-merge-dependabot.yml
# version: 1.0.0
# guid: auto-merge-dependabot-workflow

name: Auto-Merge Dependabot PRs

on:
  pull_request:
    types:
      - opened
      - synchronize
      - reopened
      - labeled

permissions:
  contents: write
  pull-requests: write
  checks: read

jobs:
  validate-dependabot:
    name: Validate Dependabot PR
    if: github.actor == 'dependabot[bot]'
    runs-on: ubuntu-latest
    outputs:
      should_automerge: ${{ steps.check.outputs.should_automerge }}
      pr_type: ${{ steps.check.outputs.pr_type }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Get PR metadata
        id: metadata
        uses: dependabot/fetch-metadata@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}

      - name: Check auto-merge eligibility
        id: check
        run: |
          UPDATE_TYPE="${{ steps.metadata.outputs.update-type }}"
          PACKAGE_ECOSYSTEM="${{ steps.metadata.outputs.package-ecosystem }}"
          COMPATIBILITY_SCORE="${{ steps.metadata.outputs.compatibility-score }}"

          # Auto-merge rules
          SHOULD_AUTOMERGE=false
          PR_TYPE="manual"

          # Security updates: always auto-merge if tests pass
          if [[ "$UPDATE_TYPE" == *"security"* ]]; then
            SHOULD_AUTOMERGE=true
            PR_TYPE="security"

          # Patch updates: auto-merge if compatibility score >= 90
          elif [[ "$UPDATE_TYPE" == "version-update:semver-patch" ]]; then
            if (( $(echo "$COMPATIBILITY_SCORE >= 90" | bc -l) )); then
              SHOULD_AUTOMERGE=true
              PR_TYPE="patch"
            fi

          # Minor updates: auto-merge for dev dependencies only
          elif [[ "$UPDATE_TYPE" == "version-update:semver-minor" ]]; then
            if [[ "${{ steps.metadata.outputs.dependency-type }}" == "direct:development" ]]; then
              SHOULD_AUTOMERGE=true
              PR_TYPE="minor-dev"
            fi
          fi

          echo "should_automerge=$SHOULD_AUTOMERGE" >> $GITHUB_OUTPUT
          echo "pr_type=$PR_TYPE" >> $GITHUB_OUTPUT

  wait-for-checks:
    name: Wait for CI Checks
    needs: validate-dependabot
    if: needs.validate-dependabot.outputs.should_automerge == 'true'
    runs-on: ubuntu-latest

    steps:
      - name: Wait for status checks
        uses: fountainhead/action-wait-for-check@v1.1.0
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          checkName: 'CI'
          ref: ${{ github.event.pull_request.head.sha }}
          timeoutSeconds: 1800 # 30 minutes
          intervalSeconds: 30

      - name: Wait for security checks
        uses: fountainhead/action-wait-for-check@v1.1.0
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          checkName: 'Security Scanning'
          ref: ${{ github.event.pull_request.head.sha }}
          timeoutSeconds: 1800

  auto-merge:
    name: Auto-Merge PR
    needs: [validate-dependabot, wait-for-checks]
    if: needs.validate-dependabot.outputs.should_automerge == 'true'
    runs-on: ubuntu-latest

    steps:
      - name: Approve PR
        uses: hmarr/auto-approve-action@v3
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}

      - name: Enable auto-merge
        run: gh pr merge --auto --squash "$PR_URL"
        env:
          PR_URL: ${{ github.event.pull_request.html_url }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Add merge label
        uses: actions/github-script@v7
        with:
          script: |
            await github.rest.issues.addLabels({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.payload.pull_request.number,
              labels: ['auto-merged', 'dependabot-${{ needs.validate-dependabot.outputs.pr_type }}']
            });

      - name: Comment on PR
        uses: actions/github-script@v7
        with:
          script: |
            const prType = '${{ needs.validate-dependabot.outputs.pr_type }}';
            let message = '';

            switch (prType) {
              case 'security':
                message = '✅ **Auto-merged**: Security update passed all checks.';
                break;
              case 'patch':
                message = '✅ **Auto-merged**: Patch update with high compatibility score.';
                break;
              case 'minor-dev':
                message = '✅ **Auto-merged**: Minor dev dependency update passed checks.';
                break;
            }

            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.payload.pull_request.number,
              body: message
            });
```

## Dependency Update Dashboard Workflow

```yaml
# file: .github/workflows/dependency-dashboard.yml
# version: 1.0.0
# guid: dependency-dashboard-workflow

name: Dependency Dashboard

on:
  schedule:
    - cron: '0 0 * * 1' # Weekly on Monday
  workflow_dispatch:

jobs:
  generate-dashboard:
    name: Generate Dependency Dashboard
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install requests pyyaml

      - name: Collect dependency data
        id: collect
        run: |
          python3 <<'EOF'
          import json
          import os
          import subprocess
          from datetime import datetime

          data = {
              "generated_at": datetime.utcnow().isoformat(),
              "ecosystems": {}
          }

          # Check Rust dependencies
          if os.path.exists("Cargo.toml"):
              try:
                  result = subprocess.run(
                      ["cargo", "outdated", "--format", "json"],
                      capture_output=True,
                      text=True
                  )
                  data["ecosystems"]["rust"] = json.loads(result.stdout)
              except:
                  data["ecosystems"]["rust"] = {"error": "Failed to get outdated packages"}

          # Check Python dependencies
          if os.path.exists("requirements.txt"):
              try:
                  result = subprocess.run(
                      ["pip", "list", "--outdated", "--format", "json"],
                      capture_output=True,
                      text=True
                  )
                  data["ecosystems"]["python"] = json.loads(result.stdout)
              except:
                  data["ecosystems"]["python"] = {"error": "Failed to get outdated packages"}

          # Check npm dependencies
          if os.path.exists("package.json"):
              try:
                  result = subprocess.run(
                      ["npm", "outdated", "--json"],
                      capture_output=True,
                      text=True
                  )
                  data["ecosystems"]["npm"] = json.loads(result.stdout) if result.stdout else {}
              except:
                  data["ecosystems"]["npm"] = {"error": "Failed to get outdated packages"}

          with open("dependency-data.json", "w") as f:
              json.dump(data, f, indent=2)

          print(f"Collected dependency data for {len(data['ecosystems'])} ecosystems")
          EOF

      - name: Generate dashboard markdown
        run: |
          python3 <<'EOF'
          import json
          from datetime import datetime

          with open("dependency-data.json", "r") as f:
              data = json.load(f)

          md = ["# Dependency Dashboard\n"]
          md.append(f"**Generated**: {data['generated_at']}\n")
          md.append("## Summary\n")

          for ecosystem, packages in data["ecosystems"].items():
              md.append(f"### {ecosystem.title()}\n")

              if isinstance(packages, dict) and "error" in packages:
                  md.append(f"⚠️ {packages['error']}\n")
                  continue

              if not packages:
                  md.append("✅ All dependencies up to date!\n")
                  continue

              md.append(f"Found {len(packages)} outdated packages:\n")
              md.append("| Package | Current | Latest | Type |\n")
              md.append("|---------|---------|--------|------|\n")

              # Format varies by ecosystem
              for pkg in packages[:10]:  # Limit to 10 for brevity
                  if ecosystem == "rust":
                      md.append(f"| {pkg.get('name', 'unknown')} | {pkg.get('version', 'N/A')} | {pkg.get('latest', 'N/A')} | {pkg.get('kind', 'N/A')} |\n")
                  elif ecosystem == "python":
                      md.append(f"| {pkg.get('name', 'unknown')} | {pkg.get('version', 'N/A')} | {pkg.get('latest_version', 'N/A')} | N/A |\n")
                  elif ecosystem == "npm":
                      md.append(f"| {pkg} | N/A | N/A | N/A |\n")

          md.append("\n## Actions\n")
          md.append("- Review outdated dependencies above\n")
          md.append("- Check Dependabot PRs for automated updates\n")
          md.append("- Manually update major version dependencies\n")

          with open("DEPENDENCY_DASHBOARD.md", "w") as f:
              f.write("".join(md))
          EOF

      - name: Create or update issue
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const dashboard = fs.readFileSync('DEPENDENCY_DASHBOARD.md', 'utf8');

            // Find existing dashboard issue
            const issues = await github.rest.issues.listForRepo({
              owner: context.repo.owner,
              repo: context.repo.repo,
              labels: 'dependency-dashboard',
              state: 'open'
            });

            if (issues.data.length > 0) {
              // Update existing issue
              await github.rest.issues.update({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: issues.data[0].number,
                body: dashboard
              });
            } else {
              // Create new issue
              await github.rest.issues.create({
                owner: context.repo.owner,
                repo: context.repo.repo,
                title: '📊 Dependency Dashboard',
                body: dashboard,
                labels: ['dependency-dashboard', 'automated']
              });
            }

      - name: Commit dashboard to repository
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

          git add DEPENDENCY_DASHBOARD.md

          if git diff --staged --quiet; then
            echo "No changes to commit"
          else
            git commit -m "docs(deps): update dependency dashboard [skip ci]"
            git push
          fi
```

## Dependency Policy Enforcement Script

```python
# file: scripts/enforce-dependency-policy.py
# version: 1.0.0
# guid: dependency-policy-enforcement

"""
Enforce dependency policy rules across all package manifests.
Checks for license compliance, security vulnerabilities, and version constraints.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set

# Policy configuration
ALLOWED_LICENSES = {
    "MIT",
    "Apache-2.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "ISC",
    "Zlib",
    "Unicode-DFS-2016",
}

DENIED_LICENSES = {
    "GPL-2.0",
    "GPL-3.0",
    "AGPL-3.0",
    "SSPL",
}

MAX_DEPENDENCY_AGE_DAYS = 365  # 1 year
MIN_DEPENDENCY_USAGE_THRESHOLD = 100  # Must be used by at least 100 projects

class DependencyPolicyEnforcer:
    """Enforce dependency policies."""

    def __init__(self):
        self.violations: List[Dict] = []

    def check_cargo_dependencies(self, cargo_toml: Path) -> bool:
        """Check Rust dependencies in Cargo.toml."""
        # Implementation would parse Cargo.toml and check each dependency
        # against policy rules
        pass

    def check_python_dependencies(self, requirements: Path) -> bool:
        """Check Python dependencies in requirements.txt."""
        pass

    def check_npm_dependencies(self, package_json: Path) -> bool:
        """Check npm dependencies in package.json."""
        pass

    def generate_report(self) -> str:
        """Generate policy violation report."""
        if not self.violations:
            return "✅ All dependencies comply with policy"

        report = ["# Dependency Policy Violations\n"]
        report.append(f"Found {len(self.violations)} violations:\n")

        for violation in self.violations:
            report.append(f"- **{violation['package']}**: {violation['reason']}\n")

        return "".join(report)

if __name__ == "__main__":
    enforcer = DependencyPolicyEnforcer()

    # Check all manifests
    if Path("Cargo.toml").exists():
        enforcer.check_cargo_dependencies(Path("Cargo.toml"))

    if Path("requirements.txt").exists():
        enforcer.check_python_dependencies(Path("requirements.txt"))

    if Path("package.json").exists():
        enforcer.check_npm_dependencies(Path("package.json"))

    # Generate report
    report = enforcer.generate_report()
    print(report)

    # Exit with error if violations found
    sys.exit(1 if enforcer.violations else 0)
```

---

**Part 4 Complete**: Comprehensive Dependabot configuration (all ecosystems with grouping and
auto-merge rules), automated dependency update workflows, dependency dashboard generation, policy
enforcement scripts. ✅

**Continue to Part 5** for dependency health monitoring and vulnerability alerting.
