<!-- file: docs/refactors/workflows/v2/maintenance-config.md -->
<!-- version: 1.0.0 -->
<!-- guid: e5f6a7b8-c9d0-1e2f-3a4b-5c6d7e8f9a0b -->
<!-- last-edited: 2026-01-19 -->

# Maintenance Configuration Guide

## Overview

The v2 maintenance system automates dependency hygiene, stale issue triage, and security visibility
across repositories. Configuration lives in `.github/repository-config.yml` and is consumed by
`maintenance_workflow.py` together with the reusable maintenance workflow.

## Enable Feature Flag

Activate the maintenance automation by enabling the repository flag:

```yaml
feature_flags:
  use_new_maintenance: true
```

## Maintenance Types

### Dependency Updates

Automatically inspects supported ecosystems (Go, Rust, Python, Node.js) and proposes update issues.

```yaml
maintenance:
  dependencies:
    schedule: '0 0 * * 1' # weekly Monday 00:00 UTC
    auto_merge_patch: false
    auto_merge_minor: false
    exemptions:
      - package: critical-package
        reason: Requires manual review
```

Trigger manually:

```bash
gh workflow run maintenance.yml \
  -f maintenance-type=dependency-updates \
  -f create-issues=true
```

### Stale Issue Management

Labels inactive issues / PRs and closes them after a grace period.

```yaml
maintenance:
  stale:
    schedule: '0 0 * * *' # daily 00:00 UTC
    days_until_stale: 90
    days_until_close: 30
    exempt_labels:
      - security
      - critical
    exempt_assignees: true
```

Trigger manually:

```bash
gh workflow run maintenance.yml -f maintenance-type=stale-cleanup
```

### Security Scanning

Surfaces Dependabot and advisory data and can raise alerts.

```yaml
maintenance:
  security:
    schedule: '0 */6 * * *' # every 6 hours
    auto_fix_patch: false
    severity_threshold: medium
    alert_slack: true
    slack_webhook_secret: SLACK_WEBHOOK_URL
```

Trigger manually:

```bash
gh workflow run maintenance.yml \
  -f maintenance-type=security-scan \
  -f create-issues=true
```

## Branch Policies

Override defaults per branch:

```yaml
branch_maintenance:
  main:
    dependencies:
      auto_merge_patch: true
    stale:
      days_until_stale: 60
  stable-1-go-1-24:
    dependencies:
      auto_merge_patch: false
    stale:
      days_until_stale: 120
```

## Reports

Weekly artifacts summarise dependency updates, stale items, and security posture.

```bash
gh run list --workflow=maintenance.yml --limit=5
gh run download <run-id> --name maintenance-report
```

## Exemptions

### Dependency Exemptions

```yaml
maintenance:
  dependencies:
    exemptions:
      - package: legacy-library
        reason: Version pinned for compatibility
        until: '2025-12-31'
```

### Stale Exemptions

```yaml
maintenance:
  stale:
    exempt_labels:
      - long-term
      - blocked
```

Add `/no-stale` comment on issues / PRs for ad-hoc exemptions.

## Notifications

```yaml
maintenance:
  notifications:
    slack:
      enabled: true
      webhook_secret: SLACK_WEBHOOK_URL
      channels:
        security: '#security-alerts'
        dependencies: '#dependency-updates'
    email:
      enabled: true
      recipients:
        - team@example.com
      severity_threshold: high
```

## Troubleshooting

- **Dependency checks returning nothing**: confirm ecosystem tools exist and dependency manifests
  are present (`go.mod`, `Cargo.toml`, etc.), then run
  `python .github/workflows/scripts/maintenance_workflow.py check-dependencies --language go`.
- **Stale detection inactive**: verify `GITHUB_TOKEN` permissions and thresholds, then run
  `python .github/workflows/scripts/maintenance_workflow.py find-stale --days 90`.
- **Security scan incomplete**: ensure Dependabot alerts are enabled and token has
  `security-events:write`.

## Best Practices

1. Start with manual approvals, then gradually enable `auto_merge_*`.
2. Review weekly reports to confirm automation health.
3. Track exemptions with context and set expiry dates.
4. Revisit configuration quarterly to align with policy changes.
