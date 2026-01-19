<!-- file: docs/cross-registry-todos/task-12/t12-part5.md -->
<!-- version: 1.0.0 -->
<!-- guid: t12-dependency-management-part5-j2k3l4m5-n6o7 -->
<!-- last-edited: 2026-01-19 -->

# Task 12 Part 5: Dependency Health Monitoring and Vulnerability Alerting

## Dependency Health Score Calculator

```python
# file: scripts/dependency-health-score.py
# version: 1.0.0
# guid: dependency-health-score-calculator

"""
Calculate comprehensive health scores for project dependencies.
Considers freshness, vulnerabilities, maintenance status, and usage.
"""

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests


@dataclass
class DependencyHealth:
    """Health metrics for a single dependency."""
    name: str
    current_version: str
    latest_version: str
    versions_behind: int
    last_update_days: int
    vulnerabilities: int
    critical_vulns: int
    high_vulns: int
    license: str
    github_stars: Optional[int] = None
    open_issues: Optional[int] = None
    maintenance_score: float = 0.0
    health_score: float = 0.0


class DependencyHealthCalculator:
    """Calculate health scores for dependencies."""

    def __init__(self, github_token: str):
        self.github_token = github_token
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def calculate_rust_health(self, cargo_toml_path: str) -> List[DependencyHealth]:
        """Calculate health for Rust dependencies."""
        deps = []

        # Run cargo-outdated
        result = subprocess.run(
            ["cargo", "outdated", "--format", "json"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return deps

        outdated = json.loads(result.stdout)

        for dep in outdated.get("dependencies", []):
            health = DependencyHealth(
                name=dep["name"],
                current_version=dep["version"],
                latest_version=dep.get("latest", dep["version"]),
                versions_behind=self._calculate_versions_behind(
                    dep["version"],
                    dep.get("latest", dep["version"])
                ),
                last_update_days=0,  # Would query crates.io API
                vulnerabilities=0,  # Would query RustSec
                critical_vulns=0,
                high_vulns=0,
                license=dep.get("license", "Unknown")
            )

            # Calculate maintenance score
            health.maintenance_score = self._calculate_maintenance_score(health)

            # Calculate overall health score
            health.health_score = self._calculate_health_score(health)

            deps.append(health)

        return deps

    def calculate_python_health(self, requirements_path: str) -> List[DependencyHealth]:
        """Calculate health for Python dependencies."""
        deps = []

        # Run pip list --outdated
        result = subprocess.run(
            ["pip", "list", "--outdated", "--format", "json"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return deps

        outdated = json.loads(result.stdout)

        for pkg in outdated:
            health = DependencyHealth(
                name=pkg["name"],
                current_version=pkg["version"],
                latest_version=pkg["latest_version"],
                versions_behind=self._calculate_versions_behind(
                    pkg["version"],
                    pkg["latest_version"]
                ),
                last_update_days=0,  # Would query PyPI API
                vulnerabilities=0,  # Would query safety DB
                critical_vulns=0,
                high_vulns=0,
                license="Unknown"  # Would query PyPI
            )

            health.maintenance_score = self._calculate_maintenance_score(health)
            health.health_score = self._calculate_health_score(health)

            deps.append(health)

        return deps

    def _calculate_versions_behind(self, current: str, latest: str) -> int:
        """Calculate how many versions behind current is from latest."""
        try:
            curr_parts = [int(x) for x in current.split(".")]
            latest_parts = [int(x) for x in latest.split(".")]

            # Major version difference
            if curr_parts[0] < latest_parts[0]:
                return (latest_parts[0] - curr_parts[0]) * 100

            # Minor version difference
            if len(curr_parts) > 1 and len(latest_parts) > 1:
                if curr_parts[1] < latest_parts[1]:
                    return (latest_parts[1] - curr_parts[1]) * 10

            # Patch version difference
            if len(curr_parts) > 2 and len(latest_parts) > 2:
                return latest_parts[2] - curr_parts[2]

            return 0
        except:
            return 0

    def _calculate_maintenance_score(self, health: DependencyHealth) -> float:
        """Calculate maintenance score (0-100)."""
        score = 100.0

        # Penalize for being outdated
        if health.versions_behind > 50:
            score -= 40
        elif health.versions_behind > 10:
            score -= 20
        elif health.versions_behind > 5:
            score -= 10

        # Penalize for old last update
        if health.last_update_days > 365:
            score -= 30
        elif health.last_update_days > 180:
            score -= 15

        return max(0.0, score)

    def _calculate_health_score(self, health: DependencyHealth) -> float:
        """Calculate overall health score (0-100)."""
        score = 100.0

        # Critical vulnerability: immediate -50
        if health.critical_vulns > 0:
            score -= 50

        # High vulnerabilities: -10 each
        score -= health.high_vulns * 10

        # Factor in maintenance score (30% weight)
        score = score * 0.7 + health.maintenance_score * 0.3

        # Restrictive license: -20
        if health.license in ["GPL-2.0", "GPL-3.0", "AGPL-3.0"]:
            score -= 20

        return max(0.0, min(100.0, score))

    def generate_report(self, dependencies: List[DependencyHealth]) -> str:
        """Generate health report."""
        report = ["# Dependency Health Report\n"]
        report.append(f"**Generated**: {datetime.utcnow().isoformat()}\n")
        report.append(f"**Total Dependencies**: {len(dependencies)}\n\n")

        # Calculate aggregate scores
        if dependencies:
            avg_health = sum(d.health_score for d in dependencies) / len(dependencies)
            avg_maintenance = sum(d.maintenance_score for d in dependencies) / len(dependencies)

            report.append("## Summary\n")
            report.append(f"- **Average Health Score**: {avg_health:.1f}/100\n")
            report.append(f"- **Average Maintenance Score**: {avg_maintenance:.1f}/100\n")
            report.append(f"- **Critical Vulnerabilities**: {sum(d.critical_vulns for d in dependencies)}\n")
            report.append(f"- **High Vulnerabilities**: {sum(d.high_vulns for d in dependencies)}\n\n")

        # Group by health score
        critical = [d for d in dependencies if d.health_score < 40]
        warning = [d for d in dependencies if 40 <= d.health_score < 70]
        healthy = [d for d in dependencies if d.health_score >= 70]

        if critical:
            report.append("## 🚨 Critical Dependencies\n")
            report.append("| Package | Score | Vulnerabilities | Versions Behind |\n")
            report.append("|---------|-------|-----------------|------------------|\n")
            for dep in critical:
                report.append(
                    f"| {dep.name} | {dep.health_score:.0f}/100 | "
                    f"{dep.critical_vulns}C/{dep.high_vulns}H | {dep.versions_behind} |\n"
                )
            report.append("\n")

        if warning:
            report.append("## ⚠️ Warning Dependencies\n")
            report.append("| Package | Score | Maintenance | License |\n")
            report.append("|---------|-------|-------------|----------|\n")
            for dep in warning:
                report.append(
                    f"| {dep.name} | {dep.health_score:.0f}/100 | "
                    f"{dep.maintenance_score:.0f}/100 | {dep.license} |\n"
                )
            report.append("\n")

        report.append(f"## ✅ Healthy Dependencies ({len(healthy)})\n")
        report.append("All other dependencies are in good health.\n")

        return "".join(report)


def main():
    """Main entry point."""
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Calculate dependency health scores")
    parser.add_argument("--github-token", default=os.getenv("GITHUB_TOKEN"), help="GitHub token")
    parser.add_argument("--output", default="dependency-health-report.md", help="Output file")

    args = parser.parse_args()

    calculator = DependencyHealthCalculator(args.github_token)

    all_deps = []

    # Check Rust dependencies
    if Path("Cargo.toml").exists():
        all_deps.extend(calculator.calculate_rust_health("Cargo.toml"))

    # Check Python dependencies
    if Path("requirements.txt").exists():
        all_deps.extend(calculator.calculate_python_health("requirements.txt"))

    # Generate report
    report = calculator.generate_report(all_deps)

    with open(args.output, "w") as f:
        f.write(report)

    print(f"Health report saved to {args.output}")


if __name__ == "__main__":
    from pathlib import Path
    main()
```

## Vulnerability Alert Workflow

```yaml
# file: .github/workflows/vulnerability-alerts.yml
# version: 1.0.0
# guid: vulnerability-alerts-workflow

name: Vulnerability Alerts

on:
  schedule:
    - cron: '0 */6 * * *' # Every 6 hours
  workflow_dispatch:

jobs:
  scan-vulnerabilities:
    name: Scan for Vulnerabilities
    runs-on: ubuntu-latest
    permissions:
      contents: read
      issues: write
      security-events: write
    outputs:
      has_critical: ${{ steps.aggregate.outputs.has_critical }}
      has_high: ${{ steps.aggregate.outputs.has_high }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up scanning tools
        run: |
          # Install all security scanning tools
          cargo install cargo-audit --locked || true
          pip install pip-audit safety || true
          npm install -g npm-audit-resolver || true

      - name: Scan Rust dependencies
        id: rust
        run: |
          if [ -f "Cargo.toml" ]; then
            cargo audit --json > rust-audit.json || true

            CRITICAL=$(jq '[.vulnerabilities.list[] | select(.advisory.severity == "critical")] | length' rust-audit.json)
            HIGH=$(jq '[.vulnerabilities.list[] | select(.advisory.severity == "high")] | length' rust-audit.json)

            echo "critical=$CRITICAL" >> $GITHUB_OUTPUT
            echo "high=$HIGH" >> $GITHUB_OUTPUT
          else
            echo "critical=0" >> $GITHUB_OUTPUT
            echo "high=0" >> $GITHUB_OUTPUT
          fi

      - name: Scan Python dependencies
        id: python
        run: |
          if [ -f "requirements.txt" ]; then
            pip-audit --format json > python-audit.json || true

            CRITICAL=$(jq '[.vulnerabilities[] | select(.severity == "critical")] | length' python-audit.json)
            HIGH=$(jq '[.vulnerabilities[] | select(.severity == "high")] | length' python-audit.json)

            echo "critical=$CRITICAL" >> $GITHUB_OUTPUT
            echo "high=$HIGH" >> $GITHUB_OUTPUT
          else
            echo "critical=0" >> $GITHUB_OUTPUT
            echo "high=0" >> $GITHUB_OUTPUT
          fi

      - name: Scan npm dependencies
        id: npm
        run: |
          if [ -f "package.json" ]; then
            npm audit --json > npm-audit.json || true

            CRITICAL=$(jq '.metadata.vulnerabilities.critical // 0' npm-audit.json)
            HIGH=$(jq '.metadata.vulnerabilities.high // 0' npm-audit.json)

            echo "critical=$CRITICAL" >> $GITHUB_OUTPUT
            echo "high=$HIGH" >> $GITHUB_OUTPUT
          else
            echo "critical=0" >> $GITHUB_OUTPUT
            echo "high=0" >> $GITHUB_OUTPUT
          fi

      - name: Aggregate results
        id: aggregate
        run: |
          TOTAL_CRITICAL=$((
            ${{ steps.rust.outputs.critical }} +
            ${{ steps.python.outputs.critical }} +
            ${{ steps.npm.outputs.critical }}
          ))

          TOTAL_HIGH=$((
            ${{ steps.rust.outputs.high }} +
            ${{ steps.python.outputs.high }} +
            ${{ steps.npm.outputs.high }}
          ))

          echo "has_critical=$([ $TOTAL_CRITICAL -gt 0 ] && echo 'true' || echo 'false')" >> $GITHUB_OUTPUT
          echo "has_high=$([ $TOTAL_HIGH -gt 0 ] && echo 'true' || echo 'false')" >> $GITHUB_OUTPUT
          echo "total_critical=$TOTAL_CRITICAL" >> $GITHUB_OUTPUT
          echo "total_high=$TOTAL_HIGH" >> $GITHUB_OUTPUT

      - name: Upload scan results
        uses: actions/upload-artifact@v4
        with:
          name: vulnerability-scan-results
          path: |
            rust-audit.json
            python-audit.json
            npm-audit.json

  create-alert:
    name: Create Security Alert
    needs: scan-vulnerabilities
    if: needs.scan-vulnerabilities.outputs.has_critical == 'true'
    runs-on: ubuntu-latest
    permissions:
      issues: write

    steps:
      - name: Download scan results
        uses: actions/download-artifact@v4
        with:
          name: vulnerability-scan-results

      - name: Generate alert message
        id: alert
        run: |
          cat > alert-message.md <<'EOF'
          # 🚨 Critical Security Vulnerabilities Detected

          **Scan Time**: $(date -u +"%Y-%m-%d %H:%M:%S UTC")

          ## Summary

          - **Critical Vulnerabilities**: ${{ needs.scan-vulnerabilities.outputs.total_critical }}
          - **High Vulnerabilities**: ${{ needs.scan-vulnerabilities.outputs.total_high }}

          ## Rust Dependencies

          $(if [ -f rust-audit.json ]; then
            jq -r '.vulnerabilities.list[] | select(.advisory.severity == "critical" or .advisory.severity == "high") |
            "- **\(.advisory.id)**: \(.package.name) v\(.package.version) - \(.advisory.title)"' rust-audit.json
          fi)

          ## Python Dependencies

          $(if [ -f python-audit.json ]; then
            jq -r '.vulnerabilities[] | select(.severity == "critical" or .severity == "high") |
            "- **\(.id)**: \(.name) v\(.version) - \(.vulnerability)"' python-audit.json
          fi)

          ## NPM Dependencies

          $(if [ -f npm-audit.json ]; then
            jq -r '.vulnerabilities | to_entries[] | select(.value.severity == "critical" or .value.severity == "high") |
            "- **\(.key)**: \(.value.severity) - \(.value.via[0].title)"' npm-audit.json
          fi)

          ## Action Required

          1. Review vulnerabilities above
          2. Check for available patches
          3. Update affected dependencies immediately
          4. Re-run security scans after updates

          ---
          *This alert was generated automatically by the vulnerability scanning workflow.*
          EOF

      - name: Create GitHub issue
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const alertMessage = fs.readFileSync('alert-message.md', 'utf8');

            // Check if an alert issue already exists
            const issues = await github.rest.issues.listForRepo({
              owner: context.repo.owner,
              repo: context.repo.repo,
              labels: 'critical-vulnerability',
              state: 'open'
            });

            if (issues.data.length > 0) {
              // Update existing issue
              await github.rest.issues.update({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: issues.data[0].number,
                body: alertMessage
              });

              // Add comment
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: issues.data[0].number,
                body: '🔄 **Alert Updated**: New scan results available.'
              });
            } else {
              // Create new issue
              await github.rest.issues.create({
                owner: context.repo.owner,
                repo: context.repo.repo,
                title: '🚨 Critical Security Vulnerabilities Detected',
                body: alertMessage,
                labels: ['critical-vulnerability', 'security', 'automated'],
                assignees: ['jdfalk']
              });
            }

  notify-slack:
    name: Send Slack Notification
    needs: scan-vulnerabilities
    if: needs.scan-vulnerabilities.outputs.has_critical == 'true'
    runs-on: ubuntu-latest

    steps:
      - name: Send Slack webhook
        run: |
          curl -X POST ${{ secrets.SLACK_WEBHOOK_URL }} \
            -H 'Content-Type: application/json' \
            -d '{
              "text": "🚨 Critical Security Alert",
              "blocks": [
                {
                  "type": "header",
                  "text": {
                    "type": "plain_text",
                    "text": "🚨 Critical Security Vulnerabilities Detected"
                  }
                },
                {
                  "type": "section",
                  "fields": [
                    {
                      "type": "mrkdwn",
                      "text": "*Repository:*\n${{ github.repository }}"
                    },
                    {
                      "type": "mrkdwn",
                      "text": "*Critical:*\n${{ needs.scan-vulnerabilities.outputs.total_critical }}"
                    }
                  ]
                },
                {
                  "type": "actions",
                  "elements": [
                    {
                      "type": "button",
                      "text": {
                        "type": "plain_text",
                        "text": "View Issues"
                      },
                      "url": "https://github.com/${{ github.repository }}/issues?q=is%3Aissue+is%3Aopen+label%3Acritical-vulnerability"
                    }
                  ]
                }
              ]
            }'
```

## Dependency Health Monitoring Workflow

```yaml
# file: .github/workflows/dependency-health-monitoring.yml
# version: 1.0.0
# guid: dependency-health-monitoring

name: Dependency Health Monitoring

on:
  schedule:
    - cron: '0 0 * * 1' # Weekly on Monday
  workflow_dispatch:

jobs:
  calculate-health:
    name: Calculate Dependency Health
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
          pip install requests

      - name: Run health calculator
        run: |
          python scripts/dependency-health-score.py \
            --github-token ${{ secrets.GITHUB_TOKEN }} \
            --output dependency-health-report.md

      - name: Upload report
        uses: actions/upload-artifact@v4
        with:
          name: dependency-health-report
          path: dependency-health-report.md

      - name: Commit report to repository
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

          git add dependency-health-report.md

          if git diff --staged --quiet; then
            echo "No changes to commit"
          else
            git commit -m "docs(deps): update dependency health report [skip ci]"
            git push
          fi

      - name: Create or update tracking issue
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('dependency-health-report.md', 'utf8');

            // Find existing health tracking issue
            const issues = await github.rest.issues.listForRepo({
              owner: context.repo.owner,
              repo: context.repo.repo,
              labels: 'dependency-health',
              state: 'open'
            });

            if (issues.data.length > 0) {
              await github.rest.issues.update({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: issues.data[0].number,
                body: report
              });
            } else {
              await github.rest.issues.create({
                owner: context.repo.owner,
                repo: context.repo.repo,
                title: '📊 Dependency Health Tracking',
                body: report,
                labels: ['dependency-health', 'automated']
              });
            }
```

---

**Part 5 Complete**: Dependency health scoring system, vulnerability alerting workflows, Slack
notifications, health monitoring and tracking. ✅

**Continue to Part 6** for dependency management best practices, completion checklist, and
documentation.
