<!-- file: docs/cross-registry-todos/task-10/t10-part5.md -->
<!-- version: 1.0.0 -->
<!-- guid: t10-security-scanning-part5-y5z6a7b8-c9d0 -->
<!-- last-edited: 2026-01-19 -->

# Task 10 Part 5: Infrastructure-as-Code Security Scanning

## Checkov Integration for Multi-Cloud IaC

```yaml
# file: .github/workflows/checkov.yml
# version: 1.0.0
# guid: checkov-workflow

name: Checkov IaC Security

on:
  push:
    branches: [main, develop]
    paths:
      - '**.tf'
      - '**.yaml'
      - '**.yml'
      - '**.json'
      - 'Dockerfile'
  pull_request:
    branches: [main]
    paths:
      - '**.tf'
      - '**.yaml'
      - '**.yml'
      - '**.json'
      - 'Dockerfile'
  workflow_dispatch:

jobs:
  checkov:
    name: Checkov Scan
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

      - name: Install Checkov
        run: pip install checkov

      - name: Run Checkov (SARIF)
        run: |
          checkov \
            --directory . \
            --output sarif \
            --output-file-path . \
            --framework terraform \
            --framework cloudformation \
            --framework kubernetes \
            --framework dockerfile \
            --framework github_actions \
            --soft-fail

      - name: Upload Checkov results to GitHub Security
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: './results_sarif.sarif'
          category: 'checkov'

      - name: Run Checkov (JSON)
        run: |
          checkov \
            --directory . \
            --output json \
            --output-file-path . \
            --framework all

      - name: Upload Checkov JSON results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: checkov-results-${{ github.run_id }}
          path: results_json.json
          retention-days: 30

      - name: Run Checkov with custom policies
        run: |
          checkov \
            --directory . \
            --external-checks-dir ./.checkov/policies \
            --output cli \
            --soft-fail

  checkov-summary:
    name: Checkov Summary
    needs: checkov
    runs-on: ubuntu-latest
    if: always()

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Download Checkov results
        uses: actions/download-artifact@v4
        with:
          name: checkov-results-${{ github.run_id }}

      - name: Generate Checkov summary
        run: |
          echo "# Checkov IaC Security Summary" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY

          PASSED=$(jq '.summary.passed' results_json.json)
          FAILED=$(jq '.summary.failed' results_json.json)
          SKIPPED=$(jq '.summary.skipped' results_json.json)

          echo "## Results" >> $GITHUB_STEP_SUMMARY
          echo "- ✅ Passed: $PASSED" >> $GITHUB_STEP_SUMMARY
          echo "- ❌ Failed: $FAILED" >> $GITHUB_STEP_SUMMARY
          echo "- ⏭️  Skipped: $SKIPPED" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY

          echo "## Top 5 Failed Checks" >> $GITHUB_STEP_SUMMARY
          jq -r '.results.failed_checks[:5] | .[] | "- [\(.severity)] \(.check_id): \(.check_name)"' results_json.json >> $GITHUB_STEP_SUMMARY
```

### Custom Checkov Policies

Create `.checkov/policies/custom_policy.py`:

```python
#!/usr/bin/env python3
# file: .checkov/policies/custom_policy.py
# version: 1.0.0
# guid: checkov-custom-policy

from checkov.common.models.enums import CheckResult, CheckCategories
from checkov.terraform.checks.resource.base_resource_check import BaseResourceCheck

class RequireTagsCheck(BaseResourceCheck):
    def __init__(self):
        name = "Ensure all resources have required tags"
        id = "CKV_CUSTOM_1"
        supported_resources = ['*']
        categories = [CheckCategories.GENERAL_SECURITY]
        super().__init__(name=name, id=id, categories=categories, supported_resources=supported_resources)

    def scan_resource_conf(self, conf):
        required_tags = ['Environment', 'Owner', 'Project']

        if 'tags' in conf:
            tags = conf['tags'][0] if isinstance(conf['tags'], list) else conf['tags']
            for required_tag in required_tags:
                if required_tag not in tags:
                    return CheckResult.FAILED
            return CheckResult.PASSED

        return CheckResult.FAILED

check = RequireTagsCheck()
```

## tfsec for Terraform Security

```yaml
# file: .github/workflows/tfsec.yml
# version: 1.0.0
# guid: tfsec-workflow

name: tfsec Terraform Security

on:
  push:
    branches: [main, develop]
    paths:
      - '**.tf'
      - '**.tfvars'
  pull_request:
    branches: [main]
    paths:
      - '**.tf'
      - '**.tfvars'
  workflow_dispatch:

jobs:
  tfsec:
    name: tfsec Scan
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run tfsec
        uses: aquasecurity/tfsec-action@v1.0.3
        with:
          soft_fail: false
          format: sarif
          additional_args: --minimum-severity MEDIUM

      - name: Upload tfsec results to GitHub Security
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'tfsec.sarif'
          category: 'tfsec'

      - name: Run tfsec (JSON)
        uses: aquasecurity/tfsec-action@v1.0.3
        with:
          soft_fail: true
          format: json
          additional_args: --out tfsec-results.json

      - name: Upload tfsec JSON results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: tfsec-results-${{ github.run_id }}
          path: tfsec-results.json
          retention-days: 30

      - name: Run tfsec with custom checks
        run: |
          docker run --rm -v $(pwd):/src aquasec/tfsec:latest \
            /src \
            --custom-check-dir /src/.tfsec/custom \
            --format lovely
```

### Custom tfsec Configuration

Create `.tfsec/config.yml`:

```yaml
# file: .tfsec/config.yml
# version: 1.0.0
# guid: tfsec-config

minimum_severity: MEDIUM

exclude:
  - AWS001 # S3 Bucket has an ACL defined which allows public access
  - AWS002 # S3 Bucket does not have logging enabled

severity_overrides:
  AWS003: HIGH # Upgrade severity for unencrypted S3 buckets

custom_checks:
  - name: require-tags
    description: Ensure all resources have required tags
    severity: HIGH
    resources:
      - aws_instance
      - aws_s3_bucket
      - aws_rds_instance
    check: |
      resource has tags.Environment
      resource has tags.Owner
      resource has tags.Project
```

## Terrascan for Policy-as-Code

```yaml
# file: .github/workflows/terrascan.yml
# version: 1.0.0
# guid: terrascan-workflow

name: Terrascan IaC Security

on:
  push:
    branches: [main, develop]
    paths:
      - '**.tf'
      - '**.yaml'
      - '**.yml'
      - '**.json'
  pull_request:
    branches: [main]
  workflow_dispatch:

jobs:
  terrascan:
    name: Terrascan Scan
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run Terrascan
        uses: tenable/terrascan-action@main
        with:
          iac_type: 'terraform'
          iac_version: 'v14'
          policy_type: 'all'
          only_warn: true
          sarif_upload: true

      - name: Upload Terrascan results to GitHub Security
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'terrascan.sarif'
          category: 'terrascan'

      - name: Run Terrascan (JSON)
        run: |
          docker run --rm -v $(pwd):/iac \
            tenable/terrascan scan \
            -i terraform \
            -d /iac \
            -o json \
            > terrascan-results.json || true

      - name: Upload Terrascan JSON results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: terrascan-results-${{ github.run_id }}
          path: terrascan-results.json
          retention-days: 30
```

## kube-score for Kubernetes Manifests

```yaml
# file: .github/workflows/kube-score.yml
# version: 1.0.0
# guid: kube-score-workflow

name: kube-score Kubernetes Security

on:
  push:
    branches: [main, develop]
    paths:
      - 'k8s/**/*.yaml'
      - 'k8s/**/*.yml'
      - 'manifests/**/*.yaml'
      - 'manifests/**/*.yml'
  pull_request:
    branches: [main]
  workflow_dispatch:

jobs:
  kube-score:
    name: kube-score Scan
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install kube-score
        run: |
          wget https://github.com/zegl/kube-score/releases/latest/download/kube-score_linux_amd64
          chmod +x kube-score_linux_amd64
          sudo mv kube-score_linux_amd64 /usr/local/bin/kube-score

      - name: Run kube-score
        run: |
          find . -type f \( -name "*.yaml" -o -name "*.yml" \) \
            -path "*/k8s/*" -o -path "*/manifests/*" \
            -exec kube-score score {} \; || true

      - name: Run kube-score (JSON)
        run: |
          find . -type f \( -name "*.yaml" -o -name "*.yml" \) \
            -path "*/k8s/*" -o -path "*/manifests/*" \
            -exec kube-score score --output-format json {} \; \
            > kube-score-results.json || true

      - name: Upload kube-score results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: kube-score-results-${{ github.run_id }}
          path: kube-score-results.json
          retention-days: 30

  kubelinter:
    name: KubeLinter Scan
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run KubeLinter
        uses: stackrox/kube-linter-action@v1
        with:
          directory: k8s/
          format: sarif
          output-file: kubelinter-results.sarif

      - name: Upload KubeLinter results to GitHub Security
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'kubelinter-results.sarif'
          category: 'kubelinter'
```

## Hadolint for Dockerfile Linting

```yaml
# file: .github/workflows/hadolint.yml
# version: 1.0.0
# guid: hadolint-workflow

name: Hadolint Dockerfile Security

on:
  push:
    branches: [main, develop]
    paths:
      - '**/Dockerfile*'
      - '.hadolint.yaml'
  pull_request:
    branches: [main]
    paths:
      - '**/Dockerfile*'
  workflow_dispatch:

jobs:
  hadolint:
    name: Hadolint Scan
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run Hadolint
        uses: hadolint/hadolint-action@v3.1.0
        with:
          dockerfile: Dockerfile
          format: sarif
          output-file: hadolint-results.sarif
          no-fail: true

      - name: Upload Hadolint results to GitHub Security
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'hadolint-results.sarif'
          category: 'hadolint'

      - name: Run Hadolint (JSON)
        run: |
          docker run --rm -i hadolint/hadolint:latest \
            hadolint --format json - < Dockerfile \
            > hadolint-results.json || true

      - name: Upload Hadolint JSON results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: hadolint-results-${{ github.run_id }}
          path: hadolint-results.json
          retention-days: 30
```

### Hadolint Configuration

Create `.hadolint.yaml`:

```yaml
# file: .hadolint.yaml
# version: 1.0.0
# guid: hadolint-config

ignored:
  - DL3008 # Pin versions in apt-get install
  - DL3009 # Delete apt cache after installing

trustedRegistries:
  - docker.io
  - ghcr.io
  - quay.io

failure-threshold: warning

override:
  error:
    - DL3001 # Avoid using sudo
    - DL3002 # Last USER should not be root
    - DL3003 # Use WORKDIR to switch directories
  warning:
    - DL3007 # Using latest is prone to errors
    - DL3018 # Pin package versions
  info:
    - DL3013 # Pin versions in pip
  style:
    - DL3015 # Avoid additional packages in apt-get
```

## Unified IaC Security Workflow

```yaml
# file: .github/workflows/iac-security.yml
# version: 1.0.0
# guid: iac-security-unified

name: IaC Security

on:
  push:
    branches: [main, develop]
    paths:
      - '**.tf'
      - '**.yaml'
      - '**.yml'
      - '**/Dockerfile*'
  pull_request:
    branches: [main]
  schedule:
    # Run every day at 11:00 UTC
    - cron: '0 11 * * *'
  workflow_dispatch:

jobs:
  detect-iac:
    name: Detect IaC Files
    runs-on: ubuntu-latest
    outputs:
      has-terraform: ${{ steps.detect.outputs.has-terraform }}
      has-kubernetes: ${{ steps.detect.outputs.has-kubernetes }}
      has-dockerfile: ${{ steps.detect.outputs.has-dockerfile }}
      has-cloudformation: ${{ steps.detect.outputs.has-cloudformation }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Detect IaC types
        id: detect
        run: |
          echo "has-terraform=$(find . -name '*.tf' -type f | head -n1 | wc -l)" >> $GITHUB_OUTPUT
          echo "has-kubernetes=$(find . -path '*/k8s/*.yaml' -o -path '*/manifests/*.yaml' | head -n1 | wc -l)" >> $GITHUB_OUTPUT
          echo "has-dockerfile=$(find . -name 'Dockerfile*' -type f | head -n1 | wc -l)" >> $GITHUB_OUTPUT
          echo "has-cloudformation=$(find . -name '*cloudformation*.yaml' -o -name '*cfn*.yaml' | head -n1 | wc -l)" >> $GITHUB_OUTPUT

  checkov:
    name: Checkov Scan
    needs: detect-iac
    if:
      needs.detect-iac.outputs.has-terraform == '1' || needs.detect-iac.outputs.has-kubernetes ==
      '1' || needs.detect-iac.outputs.has-cloudformation == '1'
    uses: ./.github/workflows/checkov.yml

  tfsec:
    name: tfsec Scan
    needs: detect-iac
    if: needs.detect-iac.outputs.has-terraform == '1'
    uses: ./.github/workflows/tfsec.yml

  terrascan:
    name: Terrascan Scan
    needs: detect-iac
    if: needs.detect-iac.outputs.has-terraform == '1'
    uses: ./.github/workflows/terrascan.yml

  kube-score:
    name: kube-score Scan
    needs: detect-iac
    if: needs.detect-iac.outputs.has-kubernetes == '1'
    uses: ./.github/workflows/kube-score.yml

  hadolint:
    name: Hadolint Scan
    needs: detect-iac
    if: needs.detect-iac.outputs.has-dockerfile == '1'
    uses: ./.github/workflows/hadolint.yml

  iac-summary:
    name: IaC Security Summary
    needs: [checkov, tfsec, terrascan, kube-score, hadolint]
    runs-on: ubuntu-latest
    if: always()

    steps:
      - name: Generate IaC Security Summary
        run: |
          echo "# IaC Security Summary" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "## Scans Completed" >> $GITHUB_STEP_SUMMARY
          echo "- Checkov: ${{ needs.checkov.result }}" >> $GITHUB_STEP_SUMMARY
          echo "- tfsec: ${{ needs.tfsec.result }}" >> $GITHUB_STEP_SUMMARY
          echo "- Terrascan: ${{ needs.terrascan.result }}" >> $GITHUB_STEP_SUMMARY
          echo "- kube-score: ${{ needs.kube-score.result }}" >> $GITHUB_STEP_SUMMARY
          echo "- Hadolint: ${{ needs.hadolint.result }}" >> $GITHUB_STEP_SUMMARY
```

---

**Part 5 Complete**: IaC security scanning (Checkov, tfsec, Terrascan, kube-score, Hadolint) with
custom policies and unified workflow. ✅

**Continue to Part 6** for policy enforcement, compliance monitoring, and task completion.
