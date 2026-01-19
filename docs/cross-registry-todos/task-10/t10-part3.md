<!-- file: docs/cross-registry-todos/task-10/t10-part3.md -->
<!-- version: 1.0.0 -->
<!-- guid: t10-security-scanning-part3-m3n4o5p6-q7r8 -->
<!-- last-edited: 2026-01-19 -->

# Task 10 Part 3: Language-Specific Dependency Scanning

## Rust: cargo-audit Integration

### Comprehensive Rust Security Workflow

```yaml
# file: .github/workflows/rust-security.yml
# version: 1.0.0
# guid: rust-security-workflow

name: Rust Security

on:
  push:
    branches: [main, develop]
    paths:
      - 'Cargo.toml'
      - 'Cargo.lock'
      - 'src/**'
  pull_request:
    branches: [main]
    paths:
      - 'Cargo.toml'
      - 'Cargo.lock'
      - 'src/**'
  schedule:
    # Run every day at 03:00 UTC
    - cron: '0 3 * * *'
  workflow_dispatch:

jobs:
  cargo-audit:
    name: Cargo Audit
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install Rust toolchain
        uses: dtolnay/rust-toolchain@stable

      - name: Cache cargo registry
        uses: actions/cache@v4
        with:
          path: ~/.cargo/registry
          key: cargo-registry-${{ runner.os }}-${{ hashFiles('**/Cargo.lock') }}

      - name: Install cargo-audit
        run: cargo install cargo-audit --locked

      - name: Run cargo audit (JSON format)
        run: |
          cargo audit --json > cargo-audit-results.json || true

      - name: Run cargo audit (human-readable)
        run: |
          cargo audit || true

      - name: Convert cargo-audit results to SARIF
        run: |
          # Install sarif converter
          cargo install cargo-sarif --locked

          # Convert to SARIF
          cargo audit --json | cargo-sarif > cargo-audit.sarif || true

      - name: Upload cargo-audit results to GitHub Security
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'cargo-audit.sarif'
          category: 'cargo-audit'

      - name: Upload cargo-audit JSON results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: cargo-audit-results-${{ github.run_id }}
          path: cargo-audit-results.json
          retention-days: 30

      - name: Check for vulnerabilities
        run: |
          if cargo audit --deny warnings; then
            echo "✅ No vulnerabilities found"
          else
            echo "⚠️ Vulnerabilities found"
            exit 1
          fi

  cargo-deny:
    name: Cargo Deny
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install Rust toolchain
        uses: dtolnay/rust-toolchain@stable

      - name: Install cargo-deny
        run: cargo install cargo-deny --locked

      - name: Create deny.toml config
        run: |
          cat > deny.toml <<'EOF'
          [advisories]
          db-path = "~/.cargo/advisory-db"
          db-urls = ["https://github.com/rustsec/advisory-db"]
          vulnerability = "deny"
          unmaintained = "warn"
          yanked = "warn"
          notice = "warn"
          ignore = []

          [licenses]
          unlicensed = "deny"
          allow = [
              "MIT",
              "Apache-2.0",
              "BSD-2-Clause",
              "BSD-3-Clause",
              "ISC",
              "Unicode-DFS-2016",
          ]
          deny = []
          copyleft = "warn"
          default = "deny"

          [bans]
          multiple-versions = "warn"
          wildcards = "allow"
          highlight = "all"

          [sources]
          unknown-registry = "deny"
          unknown-git = "deny"
          allow-registry = ["https://github.com/rust-lang/crates.io-index"]
          EOF

      - name: Run cargo deny
        run: cargo deny check

  cargo-outdated:
    name: Check for Outdated Dependencies
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install Rust toolchain
        uses: dtolnay/rust-toolchain@stable

      - name: Install cargo-outdated
        run: cargo install cargo-outdated --locked

      - name: Check for outdated dependencies
        run: |
          cargo outdated --exit-code 1 || true

      - name: Generate outdated dependencies report
        run: |
          echo "# Outdated Dependencies Report" > outdated-report.md
          echo "" >> outdated-report.md
          cargo outdated --format markdown >> outdated-report.md || true

      - name: Upload outdated dependencies report
        uses: actions/upload-artifact@v4
        with:
          name: outdated-dependencies-${{ github.run_id }}
          path: outdated-report.md
          retention-days: 7
```

## Python: pip-audit and safety Integration

```yaml
# file: .github/workflows/python-security.yml
# version: 1.0.0
# guid: python-security-workflow

name: Python Security

on:
  push:
    branches: [main, develop]
    paths:
      - 'requirements.txt'
      - 'pyproject.toml'
      - 'setup.py'
      - '**/*.py'
  pull_request:
    branches: [main]
    paths:
      - 'requirements.txt'
      - 'pyproject.toml'
      - 'setup.py'
      - '**/*.py'
  schedule:
    # Run every day at 04:00 UTC
    - cron: '0 4 * * *'
  workflow_dispatch:

jobs:
  pip-audit:
    name: pip-audit
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install pip-audit
        run: pip install pip-audit

      - name: Run pip-audit (JSON format)
        run: |
          pip-audit --format json --output pip-audit-results.json || true

      - name: Run pip-audit (human-readable)
        run: |
          pip-audit || true

      - name: Convert pip-audit results to SARIF
        uses: pypa/gh-action-pip-audit@v1.0.8
        with:
          inputs: requirements.txt
          format: sarif
          output: pip-audit.sarif

      - name: Upload pip-audit results to GitHub Security
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'pip-audit.sarif'
          category: 'pip-audit'

      - name: Upload pip-audit JSON results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: pip-audit-results-${{ github.run_id }}
          path: pip-audit-results.json
          retention-days: 30

  safety:
    name: Safety Check
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install safety
        run: pip install safety

      - name: Run safety check
        run: |
          safety check --json --output safety-results.json || true

      - name: Run safety check (human-readable)
        run: |
          safety check || true

      - name: Upload safety results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: safety-results-${{ github.run_id }}
          path: safety-results.json
          retention-days: 30

  bandit:
    name: Bandit Security Linter
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install bandit
        run: pip install bandit[sarif]

      - name: Run bandit (SARIF format)
        run: |
          bandit -r . -f sarif -o bandit-results.sarif || true

      - name: Upload bandit results to GitHub Security
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'bandit-results.sarif'
          category: 'bandit'

      - name: Run bandit (human-readable)
        run: |
          bandit -r . || true
```

## JavaScript/TypeScript: npm audit and Snyk

```yaml
# file: .github/workflows/npm-security.yml
# version: 1.0.0
# guid: npm-security-workflow

name: npm Security

on:
  push:
    branches: [main, develop]
    paths:
      - 'package.json'
      - 'package-lock.json'
      - 'yarn.lock'
      - 'pnpm-lock.yaml'
      - '**/*.js'
      - '**/*.ts'
  pull_request:
    branches: [main]
    paths:
      - 'package.json'
      - 'package-lock.json'
      - 'yarn.lock'
      - 'pnpm-lock.yaml'
  schedule:
    # Run every day at 05:00 UTC
    - cron: '0 5 * * *'
  workflow_dispatch:

jobs:
  npm-audit:
    name: npm audit
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Run npm audit (JSON format)
        run: |
          npm audit --json > npm-audit-results.json || true

      - name: Run npm audit (human-readable)
        run: |
          npm audit || true

      - name: Upload npm audit results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: npm-audit-results-${{ github.run_id }}
          path: npm-audit-results.json
          retention-days: 30

      - name: Check for high/critical vulnerabilities
        run: |
          npm audit --audit-level=high || true

  npm-audit-fix:
    name: npm audit fix (Auto-PR)
    runs-on: ubuntu-latest
    if: github.event_name == 'schedule'

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Run npm audit fix
        run: |
          npm audit fix --package-lock-only || true

      - name: Create Pull Request
        uses: peter-evans/create-pull-request@v6
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          commit-message: 'chore(deps): npm audit fix'
          title: 'chore(deps): fix npm vulnerabilities'
          body: |
            Automated npm audit fix to resolve security vulnerabilities.

            **Changes:**
            - Updated dependencies to fix known vulnerabilities
            - Only package-lock.json is updated (no breaking changes)

            **Testing:**
            - All CI checks must pass before merging
            - Review changes carefully for any unexpected updates
          branch: automated-npm-audit-fix
          labels: dependencies,security,automated

  snyk:
    name: Snyk Security Scan
    runs-on: ubuntu-latest
    if: github.repository_owner == 'jdfalk'

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run Snyk to check for vulnerabilities
        uses: snyk/actions/node@master
        continue-on-error: true
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --severity-threshold=high --sarif-file-output=snyk-results.sarif

      - name: Upload Snyk results to GitHub Security
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'snyk-results.sarif'
          category: 'snyk'
```

## Go: govulncheck Integration

```yaml
# file: .github/workflows/go-security.yml
# version: 1.0.0
# guid: go-security-workflow

name: Go Security

on:
  push:
    branches: [main, develop]
    paths:
      - 'go.mod'
      - 'go.sum'
      - '**/*.go'
  pull_request:
    branches: [main]
    paths:
      - 'go.mod'
      - 'go.sum'
      - '**/*.go'
  schedule:
    # Run every day at 06:00 UTC
    - cron: '0 6 * * *'
  workflow_dispatch:

jobs:
  govulncheck:
    name: govulncheck
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Go
        uses: actions/setup-go@v5
        with:
          go-version: '1.22'

      - name: Install govulncheck
        run: go install golang.org/x/vuln/cmd/govulncheck@latest

      - name: Run govulncheck (JSON format)
        run: |
          govulncheck -json ./... > govulncheck-results.json || true

      - name: Run govulncheck (human-readable)
        run: |
          govulncheck ./... || true

      - name: Upload govulncheck results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: govulncheck-results-${{ github.run_id }}
          path: govulncheck-results.json
          retention-days: 30

      - name: Check for vulnerabilities
        run: |
          if govulncheck ./...; then
            echo "✅ No vulnerabilities found"
          else
            echo "⚠️ Vulnerabilities found"
            exit 1
          fi

  gosec:
    name: gosec Security Scanner
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Go
        uses: actions/setup-go@v5
        with:
          go-version: '1.22'

      - name: Run gosec
        uses: securego/gosec@v2.19.0
        with:
          args: '-fmt sarif -out gosec-results.sarif ./...'

      - name: Upload gosec results to GitHub Security
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'gosec-results.sarif'
          category: 'gosec'

  nancy:
    name: Nancy Dependency Scanner
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Go
        uses: actions/setup-go@v5
        with:
          go-version: '1.22'

      - name: Install nancy
        run: |
          curl -L https://github.com/sonatype-nexus-community/nancy/releases/latest/download/nancy-linux-amd64 -o nancy
          chmod +x nancy

      - name: Run nancy
        run: |
          go list -json -m all | ./nancy sleuth || true
```

## Unified Language-Specific Security Workflow

Create a unified workflow that calls language-specific reusable workflows:

```yaml
# file: .github/workflows/security-scan.yml
# version: 1.0.0
# guid: security-scan-unified

name: Security Scan

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    # Run every day at 07:00 UTC
    - cron: '0 7 * * *'
  workflow_dispatch:

jobs:
  detect-languages:
    name: Detect Languages
    runs-on: ubuntu-latest
    outputs:
      has-rust: ${{ steps.detect.outputs.has-rust }}
      has-python: ${{ steps.detect.outputs.has-python }}
      has-javascript: ${{ steps.detect.outputs.has-javascript }}
      has-go: ${{ steps.detect.outputs.has-go }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Detect languages
        id: detect
        run: |
          echo "has-rust=$(test -f Cargo.toml && echo 'true' || echo 'false')" >> $GITHUB_OUTPUT
          echo "has-python=$(test -f requirements.txt -o -f pyproject.toml && echo 'true' || echo 'false')" >> $GITHUB_OUTPUT
          echo "has-javascript=$(test -f package.json && echo 'true' || echo 'false')" >> $GITHUB_OUTPUT
          echo "has-go=$(test -f go.mod && echo 'true' || echo 'false')" >> $GITHUB_OUTPUT

  rust-security:
    name: Rust Security
    needs: detect-languages
    if: needs.detect-languages.outputs.has-rust == 'true'
    uses: ./.github/workflows/rust-security.yml

  python-security:
    name: Python Security
    needs: detect-languages
    if: needs.detect-languages.outputs.has-python == 'true'
    uses: ./.github/workflows/python-security.yml

  javascript-security:
    name: JavaScript Security
    needs: detect-languages
    if: needs.detect-languages.outputs.has-javascript == 'true'
    uses: ./.github/workflows/npm-security.yml

  go-security:
    name: Go Security
    needs: detect-languages
    if: needs.detect-languages.outputs.has-go == 'true'
    uses: ./.github/workflows/go-security.yml
```

---

**Part 3 Complete**: Language-specific dependency scanning (Rust, Python, JavaScript, Go) with
cargo-audit, pip-audit, npm audit, govulncheck, and more. ✅

**Continue to Part 4** for secret scanning (Gitleaks, TruffleHog), SAST (Semgrep), and IaC scanning
(Checkov, tfsec).
