<!-- file: docs/cross-registry-todos/task-10/t10-part6.md -->
<!-- version: 1.0.0 -->
<!-- guid: t10-security-scanning-part6-e1f2g3h4-i5j6 -->
<!-- last-edited: 2026-01-19 -->

# Task 10 Part 6: Policy Enforcement and Completion

## Branch Protection Rules with Security Requirements

### Automated Branch Protection Setup

```bash
#!/bin/bash
# file: scripts/setup-branch-protection.sh
# version: 1.0.0
# guid: setup-branch-protection

set -e

REPO="$1"

if [ -z "$REPO" ]; then
  echo "Usage: $0 <repo>"
  exit 1
fi

echo "Setting up branch protection for $REPO..."

# Enable branch protection for main branch
gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  "/repos/jdfalk/$REPO/branches/main/protection" \
  -f required_status_checks='{"strict":true,"contexts":["CodeQL","Dependabot","Trivy","cargo-audit","pip-audit","npm-audit","govulncheck"]}' \
  -f enforce_admins=true \
  -f required_pull_request_reviews='{"dismissal_restrictions":{},"dismiss_stale_reviews":true,"require_code_owner_reviews":true,"required_approving_review_count":1}' \
  -f restrictions=null \
  -f required_linear_history=true \
  -f allow_force_pushes=false \
  -f allow_deletions=false \
  -f required_conversation_resolution=true

echo "✅ Branch protection enabled for $REPO"
```

## Security Policy Documentation

Create `SECURITY.md` for each repository:

```markdown
<!-- file: SECURITY.md -->
<!-- version: 1.0.0 -->
<!-- guid: security-policy -->
<!-- last-edited: 2026-01-19 -->

# Security Policy

## Supported Versions

We release security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via one of the following methods:

1. **GitHub Security Advisories** (Preferred):
   - Go to the Security tab
   - Click "Report a vulnerability"
   - Fill out the form with details

2. **Email**:
   - Send details to: security@example.com
   - Use subject line: "[SECURITY] Repository: <repo-name>"
   - Include:
     - Description of the vulnerability
     - Steps to reproduce
     - Potential impact
     - Suggested fix (if available)

## Security Update Process

1. **Acknowledgment**: Within 48 hours
2. **Initial Assessment**: Within 1 week
3. **Fix Development**: Within 2-4 weeks (depending on severity)
4. **Release**: Coordinated disclosure with reporter

## Security Scanning

This repository uses the following security scanning tools:

- **Dependabot**: Automated dependency updates
- **CodeQL**: Static code analysis
- **Trivy**: Container and filesystem vulnerability scanning
- **Gitleaks**: Secret scanning
- **Language-specific tools**:
  - Rust: cargo-audit, cargo-deny
  - Python: pip-audit, bandit, safety
  - JavaScript: npm audit, Snyk
  - Go: govulncheck, gosec

## Security Best Practices

### For Contributors

1. Never commit secrets, API keys, or credentials
2. Keep dependencies up-to-date
3. Follow secure coding guidelines
4. Run security scans locally before submitting PR
5. Review Dependabot PRs promptly

### For Maintainers

1. Review security scan results regularly
2. Respond to security advisories within SLA
3. Keep branch protection rules enforced
4. Maintain security documentation
5. Conduct security audits quarterly

## Vulnerability Disclosure Timeline

- **Critical**: Patch within 48 hours, disclose within 7 days
- **High**: Patch within 1 week, disclose within 30 days
- **Medium**: Patch within 2 weeks, disclose within 60 days
- **Low**: Patch within 1 month, disclose within 90 days

## Security Contacts

- Security Team: security@example.com
- Repository Owner: @jdfalk
- Security Advisories: https://github.com/jdfalk/<repo>/security/advisories

## Past Security Advisories

See [Security Advisories](https://github.com/jdfalk/<repo>/security/advisories) for disclosed
vulnerabilities.
```

## Compliance Monitoring Dashboard

```python
#!/usr/bin/env python3
# file: scripts/compliance-dashboard.py
# version: 1.0.0
# guid: compliance-dashboard

import json
import subprocess
from datetime import datetime
from typing import Dict, List

def check_dependabot_enabled(repo: str) -> bool:
    """Check if Dependabot is enabled."""
    result = subprocess.run(
        ['gh', 'api', f'repos/jdfalk/{repo}/contents/.github/dependabot.yml'],
        capture_output=True,
        text=True
    )
    return result.returncode == 0

def check_codeql_enabled(repo: str) -> bool:
    """Check if CodeQL is enabled."""
    result = subprocess.run(
        ['gh', 'api', f'repos/jdfalk/{repo}/code-scanning/alerts'],
        capture_output=True,
        text=True
    )
    return result.returncode == 0

def check_secret_scanning_enabled(repo: str) -> bool:
    """Check if secret scanning is enabled."""
    result = subprocess.run(
        ['gh', 'api', f'repos/jdfalk/{repo}/secret-scanning/alerts'],
        capture_output=True,
        text=True
    )
    return result.returncode == 0

def check_branch_protection(repo: str) -> Dict:
    """Check branch protection status."""
    result = subprocess.run(
        ['gh', 'api', f'repos/jdfalk/{repo}/branches/main/protection'],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return {'enabled': False}

    protection = json.loads(result.stdout)
    return {
        'enabled': True,
        'required_reviews': protection.get('required_pull_request_reviews', {}).get('required_approving_review_count', 0),
        'required_status_checks': len(protection.get('required_status_checks', {}).get('contexts', [])),
        'enforce_admins': protection.get('enforce_admins', {}).get('enabled', False),
    }

def check_security_policy(repo: str) -> bool:
    """Check if SECURITY.md exists."""
    result = subprocess.run(
        ['gh', 'api', f'repos/jdfalk/{repo}/contents/SECURITY.md'],
        capture_output=True,
        text=True
    )
    return result.returncode == 0

def generate_compliance_report():
    """Generate compliance dashboard report."""
    repos = ['ghcommon', 'ubuntu-autoinstall-agent']

    print("=" * 80)
    print("SECURITY COMPLIANCE DASHBOARD")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print("")

    for repo in repos:
        print(f"Repository: {repo}")
        print("-" * 40)

        # Check each compliance requirement
        dependabot = check_dependabot_enabled(repo)
        codeql = check_codeql_enabled(repo)
        secret_scanning = check_secret_scanning_enabled(repo)
        branch_protection = check_branch_protection(repo)
        security_policy = check_security_policy(repo)

        print(f"  Dependabot: {'✅' if dependabot else '❌'}")
        print(f"  CodeQL: {'✅' if codeql else '❌'}")
        print(f"  Secret Scanning: {'✅' if secret_scanning else '❌'}")
        print(f"  Branch Protection: {'✅' if branch_protection['enabled'] else '❌'}")
        if branch_protection['enabled']:
            print(f"    - Required reviews: {branch_protection['required_reviews']}")
            print(f"    - Required status checks: {branch_protection['required_status_checks']}")
            print(f"    - Enforce admins: {'✅' if branch_protection['enforce_admins'] else '❌'}")
        print(f"  Security Policy: {'✅' if security_policy else '❌'}")

        # Calculate compliance score
        score = sum([
            1 if dependabot else 0,
            1 if codeql else 0,
            1 if secret_scanning else 0,
            1 if branch_protection['enabled'] else 0,
            1 if security_policy else 0,
        ])
        percentage = (score / 5) * 100

        print(f"  Compliance Score: {score}/5 ({percentage:.0f}%)")
        print("")

    print("=" * 80)
    print("COMPLIANCE REQUIREMENTS")
    print("=" * 80)
    print("✅ Dependabot: Automated dependency updates")
    print("✅ CodeQL: Static code analysis")
    print("✅ Secret Scanning: Detect exposed secrets")
    print("✅ Branch Protection: Enforce PR reviews and status checks")
    print("✅ Security Policy: Document vulnerability reporting process")

if __name__ == '__main__':
    generate_compliance_report()
```

## Security Metrics Collection

```yaml
# file: .github/workflows/security-metrics.yml
# version: 1.0.0
# guid: security-metrics-workflow

name: Security Metrics Collection

on:
  schedule:
    # Run every Monday at 08:00 UTC
    - cron: '0 8 * * 1'
  workflow_dispatch:

jobs:
  collect-metrics:
    name: Collect Security Metrics
    runs-on: ubuntu-latest
    permissions:
      contents: write
      security-events: read

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install requests jq

      - name: Collect metrics
        run: |
          cat > collect_metrics.py <<'EOF'
          #!/usr/bin/env python3
          import json
          import subprocess
          from datetime import datetime

          def get_metrics():
              repo = "jdfalk/ghcommon"

              # Dependabot alerts
              result = subprocess.run(
                  ['gh', 'api', f'repos/{repo}/dependabot/alerts'],
                  capture_output=True, text=True
              )
              dependabot_alerts = len(json.loads(result.stdout)) if result.returncode == 0 else 0

              # Code scanning alerts
              result = subprocess.run(
                  ['gh', 'api', f'repos/{repo}/code-scanning/alerts'],
                  capture_output=True, text=True
              )
              code_scanning_alerts = len(json.loads(result.stdout)) if result.returncode == 0 else 0

              # Secret scanning alerts
              result = subprocess.run(
                  ['gh', 'api', f'repos/{repo}/secret-scanning/alerts'],
                  capture_output=True, text=True
              )
              secret_scanning_alerts = len(json.loads(result.stdout)) if result.returncode == 0 else 0

              metrics = {
                  'timestamp': datetime.now().isoformat(),
                  'dependabot_alerts': dependabot_alerts,
                  'code_scanning_alerts': code_scanning_alerts,
                  'secret_scanning_alerts': secret_scanning_alerts,
                  'total_alerts': dependabot_alerts + code_scanning_alerts + secret_scanning_alerts,
              }

              # Append to metrics file
              try:
                  with open('security-metrics.json', 'r') as f:
                      all_metrics = json.load(f)
              except FileNotFoundError:
                  all_metrics = []

              all_metrics.append(metrics)

              with open('security-metrics.json', 'w') as f:
                  json.dump(all_metrics, f, indent=2)

              print(f"Metrics collected: {metrics}")

          if __name__ == '__main__':
              get_metrics()
          EOF

          python collect_metrics.py
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Commit metrics
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add security-metrics.json
          git commit -m "chore(security): update security metrics [skip ci]" || echo "No changes"
          git push

      - name: Generate metrics report
        run: |
          python -c "
          import json
          from datetime import datetime

          with open('security-metrics.json') as f:
              metrics = json.load(f)

          latest = metrics[-1]

          print(f'# Security Metrics Report')
          print(f'')
          print(f'**Generated:** {datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\")}')
          print(f'')
          print(f'## Current Status')
          print(f'- Dependabot Alerts: {latest[\"dependabot_alerts\"]}')
          print(f'- Code Scanning Alerts: {latest[\"code_scanning_alerts\"]}')
          print(f'- Secret Scanning Alerts: {latest[\"secret_scanning_alerts\"]}')
          print(f'- **Total Alerts:** {latest[\"total_alerts\"]}')
          print(f'')

          if len(metrics) > 1:
              previous = metrics[-2]
              diff = latest['total_alerts'] - previous['total_alerts']
              print(f'## Trend')
              if diff > 0:
                  print(f'⚠️ Increased by {diff} alerts')
              elif diff < 0:
                  print(f'✅ Decreased by {abs(diff)} alerts')
              else:
                  print(f'➡️ No change')
          " > security-metrics-report.md

      - name: Upload metrics report
        uses: actions/upload-artifact@v4
        with:
          name: security-metrics-${{ github.run_id }}
          path: security-metrics-report.md
          retention-days: 90
```

## Security Automation Scripts

```bash
#!/bin/bash
# file: scripts/security-setup-all-repos.sh
# version: 1.0.0
# guid: security-setup-all-repos

set -e

REPOS=(
  "ghcommon"
  "ubuntu-autoinstall-agent"
)

echo "Setting up security features for all repositories..."
echo ""

for REPO in "${REPOS[@]}"; do
  echo "=================================================="
  echo "Repository: $REPO"
  echo "=================================================="

  # 1. Enable Dependabot
  echo "Checking Dependabot configuration..."
  if gh api repos/jdfalk/$REPO/contents/.github/dependabot.yml &>/dev/null; then
    echo "✅ Dependabot already configured"
  else
    echo "⚠️  Dependabot not configured - manual setup required"
  fi

  # 2. Enable Secret Scanning
  echo "Enabling secret scanning..."
  gh api \
    --method PUT \
    -H "Accept: application/vnd.github+json" \
    "/repos/jdfalk/$REPO/secret-scanning" \
    -f enabled=true || echo "⚠️  Already enabled or insufficient permissions"

  # 3. Enable Secret Scanning Push Protection
  echo "Enabling push protection..."
  gh api \
    --method PUT \
    -H "Accept: application/vnd.github+json" \
    "/repos/jdfalk/$REPO/secret-scanning/push-protection" \
    -f enabled=true || echo "⚠️  Already enabled or insufficient permissions"

  # 4. Check for CodeQL workflow
  echo "Checking CodeQL workflow..."
  if gh api repos/jdfalk/$REPO/contents/.github/workflows/codeql.yml &>/dev/null; then
    echo "✅ CodeQL workflow exists"
  else
    echo "⚠️  CodeQL workflow not found - manual setup required"
  fi

  # 5. Check for SECURITY.md
  echo "Checking SECURITY.md..."
  if gh api repos/jdfalk/$REPO/contents/SECURITY.md &>/dev/null; then
    echo "✅ SECURITY.md exists"
  else
    echo "⚠️  SECURITY.md not found - manual creation required"
  fi

  # 6. Setup branch protection (if not already set)
  echo "Setting up branch protection..."
  bash scripts/setup-branch-protection.sh $REPO || echo "⚠️  Branch protection setup failed"

  echo ""
done

echo "=================================================="
echo "Security setup complete!"
echo "=================================================="
```

## Post-Implementation Checklist

### Repository-Level Checklist

For each repository, verify:

- [ ] Dependabot configuration created (`.github/dependabot.yml`)
- [ ] Dependabot security updates enabled
- [ ] Dependabot version updates enabled
- [ ] CodeQL workflow created (`.github/workflows/codeql.yml`)
- [ ] CodeQL running on schedule and PRs
- [ ] Secret scanning enabled in repository settings
- [ ] Secret scanning push protection enabled
- [ ] Container scanning integrated (Trivy)
- [ ] SBOM generation workflow added
- [ ] Language-specific security tools added:
  - [ ] Rust: cargo-audit, cargo-deny
  - [ ] Python: pip-audit, bandit, safety
  - [ ] JavaScript: npm audit, Snyk
  - [ ] Go: govulncheck, gosec
- [ ] Secret scanning tools added (Gitleaks, TruffleHog)
- [ ] SAST tools integrated (Semgrep, Snyk Code)
- [ ] IaC scanning added (if applicable):
  - [ ] Checkov
  - [ ] tfsec
  - [ ] Terrascan
  - [ ] kube-score
  - [ ] Hadolint
- [ ] `SECURITY.md` created and up-to-date
- [ ] Branch protection rules configured
- [ ] Required status checks include security scans
- [ ] Security policy documented
- [ ] Security metrics collection enabled
- [ ] Compliance dashboard running

### Organization-Level Checklist

- [ ] All repositories have Dependabot enabled
- [ ] All repositories have CodeQL enabled (where supported)
- [ ] All repositories have secret scanning enabled
- [ ] Security advisories monitored across org
- [ ] Security metrics aggregated
- [ ] Compliance reports generated weekly
- [ ] Security training completed by team
- [ ] Incident response plan documented
- [ ] Vulnerability disclosure process established
- [ ] Security contacts documented

## Task 10 Complete ✅

**Summary:**

Implemented comprehensive security scanning infrastructure covering:

1. **GitHub Native Tools**:
   - Dependabot (security & version updates)
   - CodeQL (static code analysis)
   - Secret scanning (with push protection)

2. **Container Security**:
   - Trivy (vulnerability scanning)
   - Grype (redundant scanning)
   - Syft (SBOM generation)
   - Docker Scout (GitHub Packages integration)

3. **Language-Specific Scanning**:
   - Rust: cargo-audit, cargo-deny, cargo-outdated
   - Python: pip-audit, bandit, safety
   - JavaScript/TypeScript: npm audit, Snyk
   - Go: govulncheck, gosec, nancy

4. **Secret Scanning**:
   - Gitleaks (pre-commit & CI)
   - TruffleHog (comprehensive detection)
   - Custom patterns and allowlists

5. **SAST Tools**:
   - Semgrep (custom rules)
   - Snyk Code
   - SonarCloud

6. **IaC Security**:
   - Checkov (multi-cloud)
   - tfsec (Terraform)
   - Terrascan (policy-as-code)
   - kube-score (Kubernetes)
   - Hadolint (Dockerfile)

7. **Policy & Compliance**:
   - Branch protection automation
   - Security policy templates
   - Compliance monitoring dashboard
   - Security metrics collection
   - Automated setup scripts

**Deliverables:**

- 15+ reusable security workflows
- Custom security policies and rules
- Compliance dashboard and reporting
- Automation scripts for bulk setup
- Documentation and best practices

**Next Steps:**

1. Roll out security scanning to all repositories
2. Monitor security metrics weekly
3. Review and triage security alerts regularly
4. Update security policies quarterly
5. Conduct security audits semi-annually

---

**Task 10 Complete**: Comprehensive security scanning integration (~3,800 lines across 6 parts). ✅

**Ready for Task 11**: Next task will focus on artifact management and release automation.
