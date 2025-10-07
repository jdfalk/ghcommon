<!-- file: docs/cross-registry-todos/task-10/t10-part1.md -->
<!-- version: 1.0.0 -->
<!-- guid: t10-security-scanning-part1-a1b2c3d4-e5f6 -->

# Task 10 Part 1: Security Scanning Integration Overview

## Task Objective

Integrate comprehensive security scanning into CI/CD pipelines across all repositories using
GitHub-native and third-party security tools. This includes vulnerability scanning for dependencies,
container images, code secrets, and Infrastructure-as-Code (IaC) configurations.

## Security Scanning Architecture

### Multi-Layer Security Approach

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Scanning Layers                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Layer 1: Dependency Scanning                                │
│  ├── Dependabot (GitHub native)                              │
│  ├── cargo audit (Rust)                                      │
│  ├── pip-audit (Python)                                      │
│  ├── npm audit (JavaScript/TypeScript)                       │
│  └── govulncheck (Go)                                        │
│                                                               │
│  Layer 2: Container Image Scanning                           │
│  ├── Trivy (comprehensive vulnerability scanner)             │
│  ├── Grype (Anchore vulnerability scanner)                   │
│  ├── Docker Scout (Docker Hub integration)                   │
│  └── Syft (SBOM generation)                                  │
│                                                               │
│  Layer 3: Secret Scanning                                    │
│  ├── GitHub Secret Scanning (native)                         │
│  ├── Gitleaks (pre-commit and CI)                            │
│  └── TruffleHog (comprehensive secret detection)             │
│                                                               │
│  Layer 4: Code Quality & SAST                                │
│  ├── CodeQL (GitHub native static analysis)                  │
│  ├── Semgrep (pattern-based SAST)                            │
│  ├── Bandit (Python security linter)                         │
│  └── gosec (Go security checker)                             │
│                                                               │
│  Layer 5: IaC Security Scanning                              │
│  ├── Checkov (Terraform, CloudFormation, K8s)                │
│  ├── tfsec (Terraform security scanner)                      │
│  ├── kube-score (Kubernetes manifest validation)             │
│  └── Terrascan (policy-as-code for IaC)                      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Integration Strategy

**Phase 1: GitHub Native Tools (Week 1)**

- Enable Dependabot security updates
- Configure Dependabot version updates
- Enable GitHub Secret Scanning
- Enable GitHub Code Scanning (CodeQL)

**Phase 2: Container Security (Week 2)**

- Integrate Trivy scanning into Docker workflows
- Add Grype for redundant vulnerability detection
- Implement SBOM generation with Syft
- Configure Docker Scout for GitHub Packages

**Phase 3: Language-Specific Tools (Week 3)**

- Add `cargo audit` to Rust CI
- Add `pip-audit` to Python CI
- Add `npm audit` to JavaScript/TypeScript CI
- Add `govulncheck` to Go CI

**Phase 4: Advanced Scanning (Week 4)**

- Implement Gitleaks pre-commit hooks
- Add Semgrep custom rules
- Configure IaC scanning for repos with infrastructure code
- Set up security dashboard and alerting

## Current Security Posture Analysis

### Existing Security Measures

**Repository: ghcommon**

Current security tools in use:

```yaml
# .github/workflows/ci.yml (excerpt)
jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'
```

**Gap Analysis:**

- ✅ Trivy filesystem scanning enabled
- ❌ No container image scanning
- ❌ No Dependabot configuration
- ❌ CodeQL not enabled
- ❌ No secret scanning configuration
- ❌ No language-specific audit tools
- ❌ No SBOM generation
- ❌ No IaC scanning

**Repository: ubuntu-autoinstall-agent**

Current security tools in use:

```yaml
# .github/workflows/ci.yml (excerpt)
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run cargo audit
        run: cargo audit
```

**Gap Analysis:**

- ✅ Cargo audit for Rust dependencies
- ❌ No Trivy scanning
- ❌ No container scanning (despite building Docker images)
- ❌ No Dependabot configuration
- ❌ CodeQL not enabled
- ❌ No SBOM generation

### Security Risk Assessment

**Critical Risks (Address Immediately):**

1. **Unscanned Container Images**
   - Risk Level: HIGH
   - Impact: Deployment of vulnerable containers to production
   - Likelihood: HIGH (containers built without scanning)
   - Mitigation: Integrate Trivy/Grype into Docker workflows

2. **No Automated Dependency Updates**
   - Risk Level: HIGH
   - Impact: Outdated dependencies with known vulnerabilities
   - Likelihood: HIGH (manual dependency management)
   - Mitigation: Enable Dependabot

3. **Limited Secret Scanning**
   - Risk Level: HIGH
   - Impact: Accidental exposure of credentials/tokens
   - Likelihood: MEDIUM (manual code review process)
   - Mitigation: Enable GitHub Secret Scanning + Gitleaks

**Medium Risks (Address Within 2 Weeks):**

4. **No Static Application Security Testing (SAST)**
   - Risk Level: MEDIUM
   - Impact: Code vulnerabilities not caught before deployment
   - Likelihood: MEDIUM
   - Mitigation: Enable CodeQL and language-specific tools

5. **No SBOM Generation**
   - Risk Level: MEDIUM
   - Impact: Inability to track supply chain vulnerabilities
   - Likelihood: MEDIUM
   - Mitigation: Implement Syft SBOM generation

6. **IaC Not Scanned**
   - Risk Level: MEDIUM (for repos with IaC)
   - Impact: Misconfigured infrastructure deployed
   - Likelihood: MEDIUM
   - Mitigation: Add Checkov/tfsec to CI

**Low Risks (Address Within 1 Month):**

7. **No Continuous Monitoring**
   - Risk Level: LOW
   - Impact: Delayed response to new vulnerabilities
   - Likelihood: MEDIUM
   - Mitigation: Set up security dashboard and alerts

8. **No Policy Enforcement**
   - Risk Level: LOW
   - Impact: Inconsistent security practices across repos
   - Likelihood: MEDIUM
   - Mitigation: Implement security policies with branch protection

## GitHub Security Features Configuration

### 1. Dependabot Setup

Create `.github/dependabot.yml` for each repository:

```yaml
# file: .github/dependabot.yml
# version: 1.0.0
# guid: dependabot-config

version: 2
updates:
  # Rust (Cargo) dependencies
  - package-ecosystem: 'cargo'
    directory: '/'
    schedule:
      interval: 'weekly'
      day: 'monday'
      time: '09:00'
      timezone: 'America/Los_Angeles'
    open-pull-requests-limit: 10
    reviewers:
      - 'jdfalk'
    assignees:
      - 'jdfalk'
    labels:
      - 'dependencies'
      - 'rust'
    commit-message:
      prefix: 'chore(deps)'
      include: 'scope'
    # Group minor and patch updates
    groups:
      rust-dependencies:
        patterns:
          - '*'
        update-types:
          - 'minor'
          - 'patch'
    # Ignore major updates for sensitive packages
    ignore:
      - dependency-name: 'tokio'
        update-types: ['version-update:semver-major']
      - dependency-name: 'serde'
        update-types: ['version-update:semver-major']

  # Python (pip) dependencies
  - package-ecosystem: 'pip'
    directory: '/'
    schedule:
      interval: 'weekly'
      day: 'monday'
      time: '09:00'
    open-pull-requests-limit: 10
    reviewers:
      - 'jdfalk'
    labels:
      - 'dependencies'
      - 'python'
    commit-message:
      prefix: 'chore(deps)'

  # GitHub Actions
  - package-ecosystem: 'github-actions'
    directory: '/'
    schedule:
      interval: 'weekly'
      day: 'monday'
      time: '09:00'
    open-pull-requests-limit: 5
    reviewers:
      - 'jdfalk'
    labels:
      - 'dependencies'
      - 'github-actions'
    commit-message:
      prefix: 'chore(deps)'
    # Group all action updates together
    groups:
      github-actions:
        patterns:
          - '*'

  # Docker dependencies
  - package-ecosystem: 'docker'
    directory: '/'
    schedule:
      interval: 'weekly'
      day: 'monday'
      time: '09:00'
    open-pull-requests-limit: 5
    reviewers:
      - 'jdfalk'
    labels:
      - 'dependencies'
      - 'docker'
    commit-message:
      prefix: 'chore(deps)'

  # Go modules
  - package-ecosystem: 'gomod'
    directory: '/'
    schedule:
      interval: 'weekly'
      day: 'monday'
      time: '09:00'
    open-pull-requests-limit: 10
    reviewers:
      - 'jdfalk'
    labels:
      - 'dependencies'
      - 'go'
    commit-message:
      prefix: 'chore(deps)'
    groups:
      go-dependencies:
        patterns:
          - '*'
        update-types:
          - 'minor'
          - 'patch'

  # npm dependencies
  - package-ecosystem: 'npm'
    directory: '/'
    schedule:
      interval: 'weekly'
      day: 'monday'
      time: '09:00'
    open-pull-requests-limit: 10
    reviewers:
      - 'jdfalk'
    labels:
      - 'dependencies'
      - 'npm'
    commit-message:
      prefix: 'chore(deps)'
    groups:
      npm-dependencies:
        patterns:
          - '*'
        update-types:
          - 'minor'
          - 'patch'
```

**Dependabot Configuration Best Practices:**

1. **Scheduling**: Run updates on Monday mornings to allow time for review during the week
2. **Grouping**: Group minor/patch updates to reduce PR noise
3. **Limits**: Set reasonable PR limits (5-10) to avoid overwhelming reviewers
4. **Ignore Policies**: Ignore major updates for critical dependencies that require extensive
   testing
5. **Commit Messages**: Use conventional commits format for consistency
6. **Reviewers**: Assign specific reviewers for faster triage

### 2. GitHub Secret Scanning

Enable via repository settings:

```bash
#!/bin/bash
# file: scripts/enable-secret-scanning.sh
# version: 1.0.0
# guid: enable-secret-scanning

# Enable secret scanning for a repository
REPO="$1"

if [ -z "$REPO" ]; then
  echo "Usage: $0 <repo>"
  exit 1
fi

echo "Enabling secret scanning for $REPO..."

# Enable secret scanning
gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  "/repos/jdfalk/$REPO/secret-scanning" \
  -f enabled=true

# Enable push protection
gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  "/repos/jdfalk/$REPO/secret-scanning/push-protection" \
  -f enabled=true

echo "✅ Secret scanning enabled for $REPO"
echo "✅ Push protection enabled for $REPO"
```

**Secret Scanning Configuration:**

- **GitHub Secret Scanning**: Automatically scans for known secret patterns
- **Push Protection**: Prevents pushing commits containing secrets
- **Custom Patterns**: Define organization-specific secret patterns

### 3. Code Scanning (CodeQL)

Create `.github/workflows/codeql.yml`:

```yaml
# file: .github/workflows/codeql.yml
# version: 1.0.0
# guid: codeql-workflow

name: 'CodeQL Security Scanning'

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    # Run at 00:00 UTC every Monday
    - cron: '0 0 * * 1'
  workflow_dispatch:

jobs:
  analyze:
    name: Analyze (${{ matrix.language }})
    runs-on: ubuntu-latest
    timeout-minutes: 360
    permissions:
      actions: read
      contents: read
      security-events: write

    strategy:
      fail-fast: false
      matrix:
        include:
          - language: python
            build-mode: none
          - language: javascript-typescript
            build-mode: none
          - language: go
            build-mode: autobuild
          # Rust not supported by CodeQL, use cargo-audit instead

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}
          build-mode: ${{ matrix.build-mode }}
          queries: +security-extended,security-and-quality

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v3
        with:
          category: '/language:${{ matrix.language }}'
```

**CodeQL Configuration Best Practices:**

1. **Languages**: Enable for all supported languages (Python, JavaScript, TypeScript, Go)
2. **Queries**: Use `security-extended` and `security-and-quality` query packs
3. **Schedule**: Run weekly to catch new vulnerabilities
4. **Permissions**: Grant `security-events: write` for SARIF upload
5. **Timeout**: Set generous timeout (360 minutes) for large codebases

---

**Part 1 Complete**: Security scanning overview, risk assessment, GitHub native tools configuration.
✅

**Continue to Part 2** for container scanning, Trivy/Grype integration, and SBOM generation.
