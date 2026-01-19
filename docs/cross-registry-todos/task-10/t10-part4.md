<!-- file: docs/cross-registry-todos/task-10/t10-part4.md -->
<!-- version: 1.0.0 -->
<!-- guid: t10-security-scanning-part4-s9t0u1v2-w3x4 -->
<!-- last-edited: 2026-01-19 -->

# Task 10 Part 4: Secret Scanning and SAST

## Gitleaks Integration

### Pre-Commit Hook Setup

Create `.pre-commit-config.yaml` for local secret scanning:

```yaml
# file: .pre-commit-config.yaml
# version: 1.0.0
# guid: pre-commit-config

repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.4
    hooks:
      - id: gitleaks
        name: Gitleaks Secret Scanner
        entry: gitleaks protect --verbose --redact --staged
        language: system
        pass_filenames: false

  - repo: https://github.com/trufflesecurity/trufflehog
    rev: v3.63.7
    hooks:
      - id: trufflehog
        name: TruffleHog Secret Scanner
        entry: trufflehog filesystem --directory=.
        language: system
        pass_filenames: false
```

### Gitleaks CI Workflow

```yaml
# file: .github/workflows/gitleaks.yml
# version: 1.0.0
# guid: gitleaks-workflow

name: Gitleaks Secret Scanning

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  workflow_dispatch:

jobs:
  gitleaks:
    name: Gitleaks Scan
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0 # Full history for comprehensive scan

      - name: Run Gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITLEAKS_LICENSE: ${{ secrets.GITLEAKS_LICENSE }}

      - name: Run Gitleaks with custom config
        run: |
          docker run --rm -v $(pwd):/scan \
            zricethezav/gitleaks:latest \
            detect \
            --source /scan \
            --report-format sarif \
            --report-path /scan/gitleaks-results.sarif \
            --verbose \
            --redact

      - name: Upload Gitleaks results to GitHub Security
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'gitleaks-results.sarif'
          category: 'gitleaks'

      - name: Generate Gitleaks report
        if: always()
        run: |
          docker run --rm -v $(pwd):/scan \
            zricethezav/gitleaks:latest \
            detect \
            --source /scan \
            --report-format json \
            --report-path /scan/gitleaks-results.json \
            --verbose

      - name: Upload Gitleaks JSON results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: gitleaks-results-${{ github.run_id }}
          path: gitleaks-results.json
          retention-days: 90
```

### Custom Gitleaks Configuration

Create `.gitleaks.toml` for project-specific rules:

```toml
# file: .gitleaks.toml
# version: 1.0.0
# guid: gitleaks-config

title = "Gitleaks Configuration"

[extend]
useDefault = true

[[rules]]
id = "generic-api-key"
description = "Generic API Key"
regex = '''(?i)api[_-]?key[_-]?[=:]\s*['\"]?[a-zA-Z0-9]{32,}['\"]?'''
tags = ["key", "API"]

[[rules]]
id = "github-pat"
description = "GitHub Personal Access Token"
regex = '''ghp_[0-9a-zA-Z]{36}'''
tags = ["key", "GitHub"]

[[rules]]
id = "github-fine-grained-pat"
description = "GitHub Fine-Grained Personal Access Token"
regex = '''github_pat_[0-9a-zA-Z_]{82}'''
tags = ["key", "GitHub"]

[[rules]]
id = "aws-access-key"
description = "AWS Access Key"
regex = '''AKIA[0-9A-Z]{16}'''
tags = ["key", "AWS"]

[[rules]]
id = "private-key"
description = "Private Key"
regex = '''-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----'''
tags = ["key", "private"]

[allowlist]
description = "Allowlist for false positives"
paths = [
  '''\.git/''',
  '''node_modules/''',
  '''vendor/''',
  '''target/''',
  '''dist/''',
  '''build/''',
]
regexes = [
  '''EXAMPLE_API_KEY''',
  '''YOUR_API_KEY_HERE''',
  '''<YOUR_TOKEN>''',
]
```

## TruffleHog Integration

```yaml
# file: .github/workflows/trufflehog.yml
# version: 1.0.0
# guid: trufflehog-workflow

name: TruffleHog Secret Scanning

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    # Run every day at 08:00 UTC
    - cron: '0 8 * * *'
  workflow_dispatch:

jobs:
  trufflehog:
    name: TruffleHog Scan
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0 # Full history

      - name: Run TruffleHog
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: ${{ github.event.repository.default_branch }}
          head: HEAD
          extra_args: --json --only-verified

      - name: Run TruffleHog filesystem scan
        run: |
          docker run --rm -v $(pwd):/scan \
            trufflesecurity/trufflehog:latest \
            filesystem /scan \
            --json \
            --only-verified \
            > trufflehog-results.json || true

      - name: Upload TruffleHog results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: trufflehog-results-${{ github.run_id }}
          path: trufflehog-results.json
          retention-days: 90

      - name: Check for verified secrets
        run: |
          if [ -s trufflehog-results.json ]; then
            echo "⚠️ Verified secrets found!"
            cat trufflehog-results.json | jq '.'
            exit 1
          else
            echo "✅ No verified secrets found"
          fi
```

## Semgrep SAST Integration

```yaml
# file: .github/workflows/semgrep.yml
# version: 1.0.0
# guid: semgrep-workflow

name: Semgrep SAST

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    # Run every day at 09:00 UTC
    - cron: '0 9 * * *'
  workflow_dispatch:

jobs:
  semgrep:
    name: Semgrep Scan
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write

    container:
      image: returntocorp/semgrep

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run Semgrep (SARIF)
        run: |
          semgrep scan \
            --config auto \
            --sarif \
            --output semgrep-results.sarif \
            --severity ERROR \
            --severity WARNING

      - name: Upload Semgrep results to GitHub Security
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'semgrep-results.sarif'
          category: 'semgrep'

      - name: Run Semgrep (JSON)
        run: |
          semgrep scan \
            --config auto \
            --json \
            --output semgrep-results.json

      - name: Upload Semgrep JSON results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: semgrep-results-${{ github.run_id }}
          path: semgrep-results.json
          retention-days: 30

      - name: Run Semgrep with custom rules
        run: |
          semgrep scan \
            --config "p/security-audit" \
            --config "p/secrets" \
            --config "p/owasp-top-ten" \
            --json \
            --output semgrep-custom-results.json

      - name: Upload custom Semgrep results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: semgrep-custom-results-${{ github.run_id }}
          path: semgrep-custom-results.json
          retention-days: 30
```

### Custom Semgrep Rules

Create `.semgrep/rules.yml` for project-specific patterns:

```yaml
# file: .semgrep/rules.yml
# version: 1.0.0
# guid: semgrep-custom-rules

rules:
  - id: hardcoded-secret
    patterns:
      - pattern-either:
          - pattern: password = "..."
          - pattern: api_key = "..."
          - pattern: secret = "..."
          - pattern: token = "..."
    message: Potential hardcoded secret detected
    severity: ERROR
    languages:
      - python
      - javascript
      - typescript
      - go
      - rust

  - id: sql-injection-risk
    patterns:
      - pattern-either:
          - pattern: |
              $QUERY = f"SELECT * FROM ... WHERE ... = {$VAR}"
          - pattern: |
              $QUERY = "SELECT * FROM ... WHERE ... = " + $VAR
    message: Potential SQL injection vulnerability
    severity: ERROR
    languages:
      - python
      - javascript
      - typescript

  - id: command-injection-risk
    patterns:
      - pattern-either:
          - pattern: os.system($VAR)
          - pattern: subprocess.call($VAR, shell=True)
          - pattern: exec($VAR)
    message: Potential command injection vulnerability
    severity: ERROR
    languages:
      - python

  - id: insecure-random
    patterns:
      - pattern-either:
          - pattern: random.random()
          - pattern: Math.random()
    message: Using insecure random number generator for security-sensitive operations
    severity: WARNING
    languages:
      - python
      - javascript
      - typescript

  - id: debug-code
    patterns:
      - pattern-either:
          - pattern: console.log(...)
          - pattern: print(...)
          - pattern: println!(...)
    message: Debug code should be removed before production
    severity: INFO
    languages:
      - python
      - javascript
      - typescript
      - rust
```

## Advanced SAST with Snyk Code

```yaml
# file: .github/workflows/snyk-code.yml
# version: 1.0.0
# guid: snyk-code-workflow

name: Snyk Code SAST

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    # Run every day at 10:00 UTC
    - cron: '0 10 * * *'
  workflow_dispatch:

jobs:
  snyk-code:
    name: Snyk Code Scan
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run Snyk Code Test
        uses: snyk/actions@master
        continue-on-error: true
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          command: code test
          args: --sarif-file-output=snyk-code-results.sarif

      - name: Upload Snyk Code results to GitHub Security
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'snyk-code-results.sarif'
          category: 'snyk-code'

      - name: Run Snyk Code Test (JSON)
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        run: |
          npm install -g snyk
          snyk code test --json > snyk-code-results.json || true

      - name: Upload Snyk Code JSON results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: snyk-code-results-${{ github.run_id }}
          path: snyk-code-results.json
          retention-days: 30
```

## SonarCloud Integration

```yaml
# file: .github/workflows/sonarcloud.yml
# version: 1.0.0
# guid: sonarcloud-workflow

name: SonarCloud Analysis

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened]
  workflow_dispatch:

jobs:
  sonarcloud:
    name: SonarCloud Scan
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: read

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0 # Full history for blame information

      - name: SonarCloud Scan
        uses: SonarSource/sonarcloud-github-action@master
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
        with:
          args: >
            -Dsonar.projectKey=jdfalk_ghcommon -Dsonar.organization=jdfalk -Dsonar.sources=.
            -Dsonar.exclusions=**/node_modules/**,**/target/**,**/vendor/** -Dsonar.tests=tests/
            -Dsonar.python.coverage.reportPaths=coverage.xml
            -Dsonar.javascript.lcov.reportPaths=coverage/lcov.info

      - name: SonarCloud Quality Gate check
        uses: SonarSource/sonarqube-quality-gate-action@master
        timeout-minutes: 5
        env:
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
```

## Unified Security Scanning Dashboard

Create a unified workflow that aggregates all security scan results:

```yaml
# file: .github/workflows/security-dashboard.yml
# version: 1.0.0
# guid: security-dashboard-workflow

name: Security Dashboard

on:
  schedule:
    # Run every day at 00:00 UTC
    - cron: '0 0 * * *'
  workflow_dispatch:

jobs:
  aggregate-results:
    name: Aggregate Security Results
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: read

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Get Dependabot alerts
        id: dependabot
        run: |
          ALERTS=$(gh api repos/${{ github.repository }}/dependabot/alerts --jq 'length')
          echo "count=$ALERTS" >> $GITHUB_OUTPUT
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Get Code Scanning alerts
        id: code-scanning
        run: |
          ALERTS=$(gh api repos/${{ github.repository }}/code-scanning/alerts --jq 'length')
          echo "count=$ALERTS" >> $GITHUB_OUTPUT
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Get Secret Scanning alerts
        id: secret-scanning
        run: |
          ALERTS=$(gh api repos/${{ github.repository }}/secret-scanning/alerts --jq 'length')
          echo "count=$ALERTS" >> $GITHUB_OUTPUT
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Generate Security Dashboard
        run: |
          cat > security-dashboard.md <<EOF
          # Security Dashboard Report

          **Generated:** $(date -u +"%Y-%m-%d %H:%M:%S UTC")

          ## Summary

          | Category        | Open Alerts                                |
          | --------------- | ------------------------------------------ |
          | Dependabot      | ${{ steps.dependabot.outputs.count }}      |
          | Code Scanning   | ${{ steps.code-scanning.outputs.count }}   |
          | Secret Scanning | ${{ steps.secret-scanning.outputs.count }} |

          ## Recent Activity

          ### Dependabot Alerts (Last 10)
          $(gh api repos/${{ github.repository }}/dependabot/alerts --jq '.[:10] | .[] | "- [\(.security_advisory.severity | ascii_upcase)] \(.security_advisory.summary)"')

          ### Code Scanning Alerts (Last 10)
          $(gh api repos/${{ github.repository }}/code-scanning/alerts --jq '.[:10] | .[] | "- [\(.rule.severity | ascii_upcase)] \(.rule.description)"')

          ### Secret Scanning Alerts (Last 10)
          $(gh api repos/${{ github.repository }}/secret-scanning/alerts --jq '.[:10] | .[] | "- [\(.secret_type)] Detected in \(.locations[0].details.path)"')

          EOF
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Upload Security Dashboard
        uses: actions/upload-artifact@v4
        with:
          name: security-dashboard-${{ github.run_id }}
          path: security-dashboard.md
          retention-days: 90

      - name: Create Issue if Critical Vulnerabilities Found
        if:
          steps.dependabot.outputs.count > 0 || steps.code-scanning.outputs.count > 0 ||
          steps.secret-scanning.outputs.count > 0
        run: |
          gh issue create \
            --title "Security Alert: Critical Vulnerabilities Detected" \
            --body "$(cat security-dashboard.md)" \
            --label security,critical \
            --assignee jdfalk
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

**Part 4 Complete**: Secret scanning (Gitleaks, TruffleHog), SAST (Semgrep, Snyk Code, SonarCloud),
unified security dashboard. ✅

**Continue to Part 5** for IaC scanning (Checkov, tfsec, kube-score) and policy enforcement.
