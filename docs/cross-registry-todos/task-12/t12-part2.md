<!-- file: docs/cross-registry-todos/task-12/t12-part2.md -->
<!-- version: 1.0.0 -->
<!-- guid: t12-dependency-management-part2-g9h0i1j2-k3l4 -->
<!-- last-edited: 2026-01-19 -->

# Task 12 Part 2: Python and JavaScript Dependency Management

## Python Dependency Management

### Python Dependencies Configuration

```toml
# file: pyproject.toml
# version: 1.0.0
# guid: python-project-config

[build-system]
requires = ["setuptools>=68.0.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "ghcommon-scripts"
version = "1.0.0"
description = "Common scripts and utilities for repository management"
authors = [
    {name = "jdfalk", email = "jdfalk@users.noreply.github.com"}
]
readme = "README.md"
license = {text = "MIT"}
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
requires-python = ">=3.10"

dependencies = [
    "requests>=2.31.0",
    "pyyaml>=6.0.1",
    "jinja2>=3.1.2",
    "python-dotenv>=1.0.0",
    "rich>=13.7.0",
    "typer>=0.9.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.3",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "black>=23.12.0",
    "ruff>=0.1.8",
    "mypy>=1.7.1",
    "types-requests>=2.31.0",
    "types-pyyaml>=6.0.12",
]

security = [
    "pip-audit>=2.6.1",
    "safety>=2.3.5",
    "bandit>=1.7.5",
]

[tool.setuptools.packages.find]
where = ["scripts"]

[tool.black]
line-length = 100
target-version = ['py310', 'py311', 'py312']
include = '\\.pyi?$'

[tool.ruff]
line-length = 100
target-version = "py310"
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
    "S",   # bandit (security)
]
ignore = [
    "E501",  # line too long (handled by black)
    "B008",  # function calls in argument defaults
]

[tool.ruff.per-file-ignores]
"tests/*" = ["S101"]  # allow assert in tests

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
check_untyped_defs = true
strict_optional = true
ignore_missing_imports = true

[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--cov=scripts",
    "--cov-report=html",
    "--cov-report=term-missing",
    "--strict-markers",
    "-v"
]

[tool.coverage.run]
source = ["scripts"]
omit = ["tests/*"]

[tool.coverage.report]
precision = 2
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

### Requirements Files with Pinned Versions

```text
# file: requirements.txt
# version: 1.0.0
# guid: python-requirements

# Core dependencies with exact versions for reproducibility
requests==2.31.0
pyyaml==6.0.1
jinja2==3.1.2
python-dotenv==1.0.1
rich==13.7.0
typer[all]==0.9.0

# Transitive dependencies (pinned for security)
certifi==2023.11.17
charset-normalizer==3.3.2
idna==3.6
urllib3==2.1.0
MarkupSafe==2.1.3
click==8.1.7
shellingham==1.5.4
```

```text
# file: requirements-dev.txt
# version: 1.0.0
# guid: python-dev-requirements

-r requirements.txt

# Testing
pytest==7.4.3
pytest-cov==4.1.0
pytest-mock==3.12.0
pytest-xdist==3.5.0

# Code quality
black==23.12.0
ruff==0.1.8
mypy==1.7.1
types-requests==2.31.0.10
types-pyyaml==6.0.12.12

# Security scanning
pip-audit==2.6.1
safety==2.3.5
bandit[toml]==1.7.5
```

### Python Security Audit Workflow

```yaml
# file: .github/workflows/python-security-audit.yml
# version: 1.0.0
# guid: python-security-audit-workflow

name: Python Security Audit

on:
  schedule:
    - cron: '0 1 * * *' # Daily at 01:00 UTC
  push:
    paths:
      - 'requirements*.txt'
      - 'pyproject.toml'
      - 'setup.py'
  pull_request:
    paths:
      - 'requirements*.txt'
      - 'pyproject.toml'
      - 'setup.py'
  workflow_dispatch:

jobs:
  pip-audit:
    name: Pip Audit (CVE Scanning)
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
          python-version: '3.12'
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pip-audit

      - name: Run pip-audit
        id: audit
        run: |
          pip-audit --format json --output audit-results.json || true
          cat audit-results.json

      - name: Convert to SARIF
        if: always()
        run: |
          pip-audit --format json | jq '{
            version: "2.1.0",
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            runs: [{
              tool: {
                driver: {
                  name: "pip-audit",
                  informationUri: "https://github.com/pypa/pip-audit",
                  version: "latest"
                }
              },
              results: [.vulnerabilities[] | {
                ruleId: .id,
                level: (if .severity == "high" then "error" else "warning" end),
                message: {
                  text: .description
                },
                locations: [{
                  physicalLocation: {
                    artifactLocation: {
                      uri: "requirements.txt"
                    }
                  }
                }],
                properties: {
                  package: .name,
                  version: .version,
                  fixed_versions: .fix_versions
                }
              }]
            }]
          }' > pip-audit.sarif

      - name: Upload SARIF
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: pip-audit.sarif
          category: pip-audit

  safety-check:
    name: Safety Check (Vulnerability Database)
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install safety

      - name: Run safety check
        run: |
          safety check --json --output safety-results.json || true
          cat safety-results.json

      - name: Parse results
        run: |
          VULNERABILITIES=$(jq '[.vulnerabilities[] | select(.severity != "low")] | length' safety-results.json)
          echo "Found $VULNERABILITIES medium/high vulnerabilities"

          if [ "$VULNERABILITIES" -gt 0 ]; then
            jq -r '.vulnerabilities[] | select(.severity != "low") | "\(.package) \(.version): \(.vulnerability)"' safety-results.json
            exit 1
          fi

  bandit-scan:
    name: Bandit SAST Scan
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
          python-version: '3.12'

      - name: Install bandit
        run: pip install bandit[toml]

      - name: Run bandit
        run: |
          bandit -r scripts/ -f json -o bandit-results.json || true
          cat bandit-results.json

      - name: Convert to SARIF
        if: always()
        run: |
          jq '{
            version: "2.1.0",
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            runs: [{
              tool: {
                driver: {
                  name: "bandit",
                  informationUri: "https://bandit.readthedocs.io/",
                  version: "latest"
                }
              },
              results: [.results[] | {
                ruleId: .test_id,
                level: (if .issue_severity == "HIGH" then "error"
                       elif .issue_severity == "MEDIUM" then "warning"
                       else "note" end),
                message: {
                  text: .issue_text
                },
                locations: [{
                  physicalLocation: {
                    artifactLocation: {
                      uri: .filename
                    },
                    region: {
                      startLine: .line_number
                    }
                  }
                }]
              }]
            }]
          }' bandit-results.json > bandit.sarif

      - name: Upload SARIF
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: bandit.sarif
          category: bandit

  license-check:
    name: Python License Compliance
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pip-licenses
          if [ -f requirements.txt ]; then
            pip install -r requirements.txt
          fi

      - name: Check licenses
        run: |
          pip-licenses --format=json --output-file=licenses.json

          # Check for copyleft licenses
          COPYLEFT=$(jq -r '.[] | select(.License | test("GPL|AGPL|SSPL")) | .Name' licenses.json)

          if [ -n "$COPYLEFT" ]; then
            echo "::error::Found copyleft licensed dependencies:"
            echo "$COPYLEFT"
            exit 1
          fi

          # Generate license report
          pip-licenses --format=markdown --output-file=licenses.md

      - name: Upload license report
        uses: actions/upload-artifact@v4
        with:
          name: python-license-report
          path: licenses.md
```

## JavaScript/TypeScript Dependency Management

### Package.json with Security Configuration

```json
{
  "name": "ghcommon-frontend",
  "version": "1.0.0",
  "description": "Frontend utilities for ghcommon",
  "private": true,
  "type": "module",
  "engines": {
    "node": ">=18.0.0",
    "npm": ">=9.0.0"
  },
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage",
    "lint": "eslint . --ext .ts,.tsx",
    "lint:fix": "eslint . --ext .ts,.tsx --fix",
    "format": "prettier --write .",
    "audit": "npm audit --audit-level=moderate",
    "audit:fix": "npm audit fix",
    "audit:licenses": "license-checker --production --json --out licenses.json"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.45",
    "@types/react-dom": "^18.2.18",
    "@typescript-eslint/eslint-plugin": "^6.15.0",
    "@typescript-eslint/parser": "^6.15.0",
    "@vitejs/plugin-react": "^4.2.1",
    "eslint": "^8.56.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.5",
    "prettier": "^3.1.1",
    "typescript": "^5.3.3",
    "vite": "^5.0.8",
    "vitest": "^1.0.4",
    "@vitest/coverage-v8": "^1.0.4",
    "license-checker": "^25.0.1"
  },
  "overrides": {
    "semver": "^7.5.4"
  },
  "resolutions": {
    "semver": "^7.5.4"
  }
}
```

### NPM Security Audit Workflow

```yaml
# file: .github/workflows/npm-security-audit.yml
# version: 1.0.0
# guid: npm-security-audit-workflow

name: NPM Security Audit

on:
  schedule:
    - cron: '0 2 * * *' # Daily at 02:00 UTC
  push:
    paths:
      - 'package.json'
      - 'package-lock.json'
  pull_request:
    paths:
      - 'package.json'
      - 'package-lock.json'
  workflow_dispatch:

jobs:
  npm-audit:
    name: NPM Audit
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Run npm audit
        id: audit
        run: |
          npm audit --json > audit-results.json || true
          cat audit-results.json

      - name: Parse audit results
        id: parse
        run: |
          CRITICAL=$(jq -r '.vulnerabilities | to_entries | map(select(.value.severity == "critical")) | length' audit-results.json)
          HIGH=$(jq -r '.vulnerabilities | to_entries | map(select(.value.severity == "high")) | length' audit-results.json)
          MODERATE=$(jq -r '.vulnerabilities | to_entries | map(select(.value.severity == "moderate")) | length' audit-results.json)

          echo "critical=$CRITICAL" >> $GITHUB_OUTPUT
          echo "high=$HIGH" >> $GITHUB_OUTPUT
          echo "moderate=$MODERATE" >> $GITHUB_OUTPUT

      - name: Convert to SARIF
        if: always()
        run: |
          npm audit --json | jq '{
            version: "2.1.0",
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            runs: [{
              tool: {
                driver: {
                  name: "npm-audit",
                  informationUri: "https://docs.npmjs.com/cli/v9/commands/npm-audit",
                  version: "latest"
                }
              },
              results: [.vulnerabilities | to_entries[] | {
                ruleId: .key,
                level: (if .value.severity == "critical" or .value.severity == "high" then "error"
                       elif .value.severity == "moderate" then "warning"
                       else "note" end),
                message: {
                  text: .value.via[0].title
                },
                locations: [{
                  physicalLocation: {
                    artifactLocation: {
                      uri: "package.json"
                    }
                  }
                }],
                properties: {
                  package: .key,
                  severity: .value.severity,
                  fixAvailable: (.value.fixAvailable != false)
                }
              }]
            }]
          }' > npm-audit.sarif

      - name: Upload SARIF
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: npm-audit.sarif
          category: npm-audit

      - name: Attempt automatic fix
        if: steps.parse.outputs.critical > 0 || steps.parse.outputs.high > 0
        run: |
          npm audit fix --audit-level=high || true

      - name: Check if fixes were applied
        id: check_fixes
        if: steps.parse.outputs.critical > 0 || steps.parse.outputs.high > 0
        run: |
          if git diff --quiet package.json package-lock.json; then
            echo "fixes_available=false" >> $GITHUB_OUTPUT
          else
            echo "fixes_available=true" >> $GITHUB_OUTPUT
          fi

      - name: Create PR with fixes
        if: steps.check_fixes.outputs.fixes_available == 'true' && github.event_name == 'schedule'
        uses: peter-evans/create-pull-request@v5
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          commit-message: 'fix(deps): apply npm audit fixes'
          title: '[Security] NPM Audit Auto-Fix'
          body: |
            Automated npm audit fixes for security vulnerabilities.

            **Vulnerabilities Fixed**:
            - Critical: ${{ steps.parse.outputs.critical }}
            - High: ${{ steps.parse.outputs.high }}
            - Moderate: ${{ steps.parse.outputs.moderate }}

            Please review changes before merging.
          branch: auto-fix/npm-audit
          labels: security,dependencies,automated

      - name: Fail on critical/high vulnerabilities
        if: steps.parse.outputs.critical > 0 || steps.parse.outputs.high > 0
        run: |
          echo "::error::Found ${{ steps.parse.outputs.critical }} critical and ${{ steps.parse.outputs.high }} high vulnerabilities"
          exit 1

  snyk-scan:
    name: Snyk Security Scan
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Run Snyk test
        uses: snyk/actions/node@master
        continue-on-error: true
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --severity-threshold=high

  license-check:
    name: NPM License Compliance
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: |
          npm ci
          npm install -g license-checker

      - name: Check licenses
        run: |
          license-checker --production --json --out licenses.json

          # Check for copyleft licenses
          COPYLEFT=$(jq -r 'to_entries[] | select(.value.licenses | test("GPL|AGPL|SSPL")) | .key' licenses.json || echo "")

          if [ -n "$COPYLEFT" ]; then
            echo "::error::Found copyleft licensed dependencies:"
            echo "$COPYLEFT"
            exit 1
          fi

          # Generate markdown report
          license-checker --production --markdown --out licenses.md

      - name: Upload license report
        uses: actions/upload-artifact@v4
        with:
          name: npm-license-report
          path: licenses.md
```

---

**Part 2 Complete**: Python dependency management (pip-audit, safety, bandit, license checking),
JavaScript/TypeScript dependency management (npm audit, Snyk, license compliance). ✅

**Continue to Part 3** for Go dependency management and Docker base image updates.
