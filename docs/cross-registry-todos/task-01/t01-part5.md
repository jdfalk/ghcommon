<!-- file: docs/cross-registry-todos/task-01/t01-part5.md -->
<!-- version: 1.0.0 -->
<!-- guid: t01-yaml-fix-part5-e5f6g7h8-i9j0 -->
<!-- last-edited: 2026-01-19 -->

# Task 01 Part 5: Post-Merge Verification and Monitoring

## Verification Procedures

### Verify Merge Completion

```bash
#!/bin/bash
# file: scripts/verify-merge.sh
# version: 1.0.0
# guid: verify-merge

set -e

echo "=== Verifying Merge Completion ==="

# Ensure on main branch
git checkout main
git pull origin main

# Check if fix is in main
echo ""
echo "Checking if fix commit is in main..."
if git log --oneline --grep "trailing hyphens" --all | grep -q "fix(ci)"; then
  echo "✅ Fix commit found in history"
  git log --oneline --grep "trailing hyphens" -n 1
else
  echo "❌ Fix commit not found"
  exit 1
fi

# Verify file contents
echo ""
echo "Verifying file contents..."
FILE=".github/workflows/release-rust.yml"

if grep -A 3 "restore-keys:" "$FILE" | grep -qE "\-$"; then
  echo "❌ Trailing hyphens still present!"
  exit 1
else
  echo "✅ No trailing hyphens found"
fi

# Extract and display restore-keys sections
echo ""
echo "Current restore-keys configuration:"
grep -A 3 "restore-keys:" "$FILE"

echo ""
echo "✅ Merge verification complete"
```

### Expected Verification Output

```text
=== Verifying Merge Completion ===
Already on 'main'
Your branch is up to date with 'origin/main'.
Already up to date.

Checking if fix commit is in main...
✅ Fix commit found in history
abc1234 fix(ci): remove trailing hyphens from YAML restore-keys (#123)

Verifying file contents...
✅ No trailing hyphens found

Current restore-keys configuration:
          restore-keys: |
            ${{ runner.os }}-cargo-${{ matrix.rust }}
            ${{ runner.os }}-cargo
          restore-keys: |
            ${{ runner.os }}-cargo-${{ matrix.rust }}
            ${{ runner.os }}-cargo
          restore-keys: |
            ${{ runner.os }}-cargo

✅ Merge verification complete
```

## Workflow Monitoring

### Monitor First Workflow Run

```bash
#!/bin/bash
# file: scripts/monitor-first-run.sh
# version: 1.0.0
# guid: monitor-first-run

set -e

echo "=== Monitoring First Workflow Run After Fix ==="

# Get latest workflow run
echo ""
echo "Fetching latest release-rust workflow run..."
LATEST_RUN=$(gh run list --workflow=release-rust --limit 1 --json databaseId,status,conclusion,createdAt --jq '.[0]')

RUN_ID=$(echo "$LATEST_RUN" | jq -r '.databaseId')
STATUS=$(echo "$LATEST_RUN" | jq -r '.status')
CONCLUSION=$(echo "$LATEST_RUN" | jq -r '.conclusion')
CREATED=$(echo "$LATEST_RUN" | jq -r '.createdAt')

echo "Run ID: $RUN_ID"
echo "Status: $STATUS"
echo "Conclusion: $CONCLUSION"
echo "Created: $CREATED"

# If running, watch it
if [ "$STATUS" = "in_progress" ] || [ "$STATUS" = "queued" ]; then
  echo ""
  echo "Workflow is running, watching..."
  gh run watch "$RUN_ID"
fi

# Check final status
echo ""
echo "Final status:"
gh run view "$RUN_ID" --log

echo ""
echo "✅ Workflow monitoring complete"
```

### Analyze Cache Performance

```bash
#!/bin/bash
# file: scripts/analyze-cache-performance.sh
# version: 1.0.0
# guid: analyze-cache-performance

set -e

echo "=== Analyzing Cache Performance ==="

# Get recent workflow runs
echo ""
echo "Fetching recent workflow runs..."
gh run list --workflow=release-rust --limit 10 --json databaseId,conclusion,createdAt > /tmp/recent-runs.json

# Analyze each run
echo ""
echo "Analyzing cache performance..."

cat > /tmp/analyze-cache.py << 'EOF'
#!/usr/bin/env python3

import json
import subprocess
import sys

with open('/tmp/recent-runs.json', 'r') as f:
    runs = json.load(f)

print("| Run ID   | Status  | Cache Behavior | Date |")
print("|----------|---------|----------------|------|")

for run in runs[:5]:  # Analyze last 5 runs
    run_id = run['databaseId']
    status = run['conclusion'] or 'running'
    created = run['createdAt'][:10]  # Just date

    # Get logs and check for cache hits/misses
    try:
        result = subprocess.run(
            ['gh', 'run', 'view', str(run_id), '--log'],
            capture_output=True,
            text=True,
            timeout=30
        )

        log = result.stdout

        # Count cache hits and misses
        cache_hits = log.count('Cache restored successfully')
        cache_misses = log.count('Cache not found')

        if cache_hits > 0:
            cache_status = f"✅ Hit ({cache_hits})"
        elif cache_misses > 0:
            cache_status = f"❌ Miss ({cache_misses})"
        else:
            cache_status = "Unknown"

        print(f"| {run_id} | {status:7} | {cache_status:14} | {created} |")

    except Exception as e:
        print(f"| {run_id} | {status:7} | Error          | {created} |", file=sys.stderr)

print()
print("✅ Cache analysis complete")
EOF

python3 /tmp/analyze-cache.py

echo ""
echo "✅ Cache performance analysis complete"
```

### Expected Cache Performance Output

```text
=== Analyzing Cache Performance ===

Fetching recent workflow runs...

Analyzing cache performance...

| Run ID   | Status  | Cache Behavior | Date       |
| -------- | ------- | -------------- | ---------- |
| 12345678 | success | ✅ Hit (3)      | 2024-01-15 |
| 12345677 | success | ✅ Hit (3)      | 2024-01-15 |
| 12345676 | success | ❌ Miss (3)     | 2024-01-15 |
| 12345675 | success | ✅ Hit (3)      | 2024-01-14 |
| 12345674 | success | ✅ Hit (3)      | 2024-01-14 |

✅ Cache analysis complete

✅ Cache performance analysis complete
```

## Cache Hit Rate Tracking

### Set Up Cache Monitoring

```bash
#!/bin/bash
# file: scripts/setup-cache-monitoring.sh
# version: 1.0.0
# guid: setup-cache-monitoring

set -e

echo "=== Setting Up Cache Monitoring ==="

# Create monitoring directory
mkdir -p .github/monitoring

# Create cache stats script
cat > .github/monitoring/cache-stats.sh << 'EOF'
#!/bin/bash
# file: .github/monitoring/cache-stats.sh
# version: 1.0.0
# guid: cache-stats-monitor

set -e

WORKFLOW="release-rust"
DAYS=${1:-7}

echo "=== Cache Statistics (Last $DAYS days) ==="

# Get runs from last N days
SINCE=$(date -u -v -${DAYS}d +"%Y-%m-%dT%H:%M:%SZ")
echo "Analyzing runs since: $SINCE"

# Fetch runs
gh run list \
  --workflow="$WORKFLOW" \
  --limit 100 \
  --json databaseId,conclusion,createdAt,startedAt,updatedAt \
  --jq ".[] | select(.createdAt > \"$SINCE\")" > /tmp/cache-runs.json

# Analyze
python3 << 'PYTHON'
import json
import sys

with open('/tmp/cache-runs.json', 'r') as f:
    runs = [json.loads(line) for line in f]

total = len(runs)
successful = len([r for r in runs if r['conclusion'] == 'success'])
failed = len([r for r in runs if r['conclusion'] == 'failure'])

print(f"\nTotal Runs: {total}")
print(f"Successful: {successful} ({successful/total*100:.1f}%)")
print(f"Failed: {failed} ({failed/total*100:.1f}%)")
print()

# Note: Detailed cache hit/miss analysis requires parsing workflow logs
print("Note: For detailed cache hit/miss rates, run analyze-cache-performance.sh")
PYTHON

echo ""
echo "✅ Cache statistics complete"
EOF

chmod +x .github/monitoring/cache-stats.sh

echo ""
echo "✅ Cache monitoring setup complete"
echo "Run: .github/monitoring/cache-stats.sh [days]"
```

### Daily Cache Report

```bash
#!/bin/bash
# file: scripts/daily-cache-report.sh
# version: 1.0.0
# guid: daily-cache-report

set -e

echo "=== Daily Cache Report ==="
echo "Date: $(date +"%Y-%m-%d")"

# Run cache stats
.github/monitoring/cache-stats.sh 1

# Get detailed cache analysis for today's runs
echo ""
echo "=== Today's Cache Details ==="

TODAY=$(date +"%Y-%m-%d")
gh run list --workflow=release-rust --limit 20 --json databaseId,createdAt,conclusion \
  --jq ".[] | select(.createdAt | startswith(\"$TODAY\"))" > /tmp/today-runs.json

if [ ! -s /tmp/today-runs.json ]; then
  echo "No runs today"
  exit 0
fi

# Analyze each run
python3 << 'EOF'
import json
import subprocess

with open('/tmp/today-runs.json', 'r') as f:
    runs = [json.loads(line) for line in f]

for run in runs:
    run_id = run['databaseId']
    conclusion = run['conclusion']

    print(f"\nRun {run_id} ({conclusion}):")

    # Get cache-related log lines
    result = subprocess.run(
        ['gh', 'run', 'view', str(run_id), '--log'],
        capture_output=True,
        text=True,
        timeout=30
    )

    for line in result.stdout.split('\n'):
        if 'cache' in line.lower() and ('hit' in line.lower() or 'miss' in line.lower() or 'restored' in line.lower()):
            print(f"  {line.strip()}")
EOF

echo ""
echo "✅ Daily cache report complete"
```

## Performance Benchmarking

### Benchmark Build Times

```bash
#!/bin/bash
# file: scripts/benchmark-build-times.sh
# version: 1.0.0
# guid: benchmark-build-times

set -e

echo "=== Benchmarking Build Times ==="

# Get last 10 successful runs
gh run list \
  --workflow=release-rust \
  --limit 10 \
  --json databaseId,conclusion,startedAt,updatedAt \
  --jq '.[] | select(.conclusion == "success")' > /tmp/benchmark-runs.json

# Calculate durations
python3 << 'EOF'
import json
from datetime import datetime

with open('/tmp/benchmark-runs.json', 'r') as f:
    runs = [json.loads(line) for line in f]

print("| Run ID   | Duration | Started            |")
print("|----------|----------|--------------------|")

durations = []

for run in runs:
    run_id = run['databaseId']
    started = datetime.fromisoformat(run['startedAt'].replace('Z', '+00:00'))
    updated = datetime.fromisoformat(run['updatedAt'].replace('Z', '+00:00'))

    duration = (updated - started).total_seconds()
    durations.append(duration)

    minutes = int(duration // 60)
    seconds = int(duration % 60)

    print(f"| {run_id} | {minutes}m {seconds}s | {started.strftime('%Y-%m-%d %H:%M')} |")

print()
print(f"Average: {sum(durations)/len(durations):.1f}s ({sum(durations)/len(durations)/60:.1f}m)")
print(f"Min: {min(durations):.1f}s ({min(durations)/60:.1f}m)")
print(f"Max: {max(durations):.1f}s ({max(durations)/60:.1f}m)")
EOF

echo ""
echo "✅ Build time benchmarking complete"
```

### Expected Benchmark Output

```text
=== Benchmarking Build Times ===

| Run ID   | Duration | Started          |
| -------- | -------- | ---------------- |
| 12345678 | 4m 23s   | 2024-01-15 10:30 |
| 12345677 | 4m 18s   | 2024-01-15 09:15 |
| 12345676 | 15m 42s  | 2024-01-15 08:00 |
| 12345675 | 4m 25s   | 2024-01-14 16:45 |
| 12345674 | 4m 19s   | 2024-01-14 14:30 |
| 12345673 | 4m 27s   | 2024-01-14 12:15 |
| 12345672 | 4m 22s   | 2024-01-14 10:00 |
| 12345671 | 16m 05s  | 2024-01-14 08:30 |
| 12345670 | 4m 21s   | 2024-01-13 16:20 |
| 12345669 | 4m 24s   | 2024-01-13 14:10 |

Average: 320.6s (5.3m)
Min: 258.0s (4.3m)
Max: 942.0s (15.7m)

✅ Build time benchmarking complete
```

## Ongoing Monitoring

### Set Up Alerts

```bash
#!/bin/bash
# file: scripts/setup-cache-alerts.sh
# version: 1.0.0
# guid: setup-cache-alerts

set -e

echo "=== Setting Up Cache Alerts ==="

# Create alerting script
cat > .github/monitoring/check-cache-health.sh << 'EOF'
#!/bin/bash
# file: .github/monitoring/check-cache-health.sh
# version: 1.0.0
# guid: check-cache-health

set -e

WORKFLOW="release-rust"
THRESHOLD=70  # Alert if cache hit rate < 70%

echo "=== Cache Health Check ==="

# Get last 10 runs
gh run list --workflow="$WORKFLOW" --limit 10 --json databaseId,conclusion > /tmp/health-runs.json

# Count successful runs
SUCCESS_COUNT=$(jq '[.[] | select(.conclusion == "success")] | length' /tmp/health-runs.json)
TOTAL_COUNT=$(jq 'length' /tmp/health-runs.json)

SUCCESS_RATE=$((SUCCESS_COUNT * 100 / TOTAL_COUNT))

echo "Success Rate: $SUCCESS_RATE% ($SUCCESS_COUNT/$TOTAL_COUNT)"

if [ "$SUCCESS_RATE" -lt "$THRESHOLD" ]; then
  echo "⚠️  WARNING: Success rate below threshold ($THRESHOLD%)"
  echo "Recent failed runs:"
  jq -r '.[] | select(.conclusion != "success") | "\(.databaseId): \(.conclusion)"' /tmp/health-runs.json
  exit 1
else
  echo "✅ Cache health good"
fi

echo ""
echo "✅ Health check complete"
EOF

chmod +x .github/monitoring/check-cache-health.sh

echo ""
echo "✅ Cache alerts setup complete"
echo "Run: .github/monitoring/check-cache-health.sh"
```

### Schedule Health Checks

Create a GitHub Action to run health checks:

```yaml
# file: .github/workflows/cache-health-check.yml
# version: 1.0.0
# guid: cache-health-check-workflow

name: Cache Health Check

on:
  schedule:
    # Run daily at 9 AM UTC
    - cron: '0 9 * * *'
  workflow_dispatch:

permissions:
  actions: read
  contents: read

jobs:
  health-check:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up GitHub CLI
        run: |
          gh auth status
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Run health check
        run: |
          .github/monitoring/check-cache-health.sh
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Create issue on failure
        if: failure()
        uses: actions/github-script@v7
        with:
          script: |
            await github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: '🚨 Cache Health Check Failed',
              body: 'Cache health check failed. Please investigate.\n\nRun: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}',
              labels: ['bug', 'ci', 'automated']
            });
```

## Documentation Updates

### Update Workflow Documentation

```bash
#!/bin/bash
# file: scripts/update-workflow-docs.sh
# version: 1.0.0
# guid: update-workflow-docs

set -e

echo "=== Updating Workflow Documentation ==="

# Update CHANGELOG.md
cat >> CHANGELOG.md << 'EOF'

## [Unreleased]

### Fixed
- **CI**: Removed trailing hyphens from YAML restore-keys in release-rust.yml ([#123](https://github.com/jdfalk/ghcommon/pull/123))
  - Improved YAML syntax compliance
  - No functional changes to cache behavior

EOF

# Update workflow README
cat >> .github/workflows/README.md << 'EOF'

## Recent Changes

### 2024-01-15: YAML Syntax Improvements
- Removed trailing hyphens from `restore-keys` in `release-rust.yml`
- Improves YAML lint compliance
- No behavior changes

EOF

echo ""
echo "✅ Documentation updated"
```

## Completion Checklist

### Final Verification Checklist

- [ ] Merge completed successfully
- [ ] Fix commit in main branch
- [ ] No trailing hyphens in restore-keys
- [ ] First workflow run after fix successful
- [ ] Cache hit rate monitored
- [ ] Build times benchmarked
- [ ] Health check script created
- [ ] Monitoring workflow added
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No new issues reported

### Success Metrics

**Immediate (Day 1):**

- [ ] Fix merged without conflicts
- [ ] CI checks all passing
- [ ] First workflow run successful
- [ ] No cache-related errors in logs

**Short-term (Week 1):**

- [ ] Cache hit rate ≥ 70%
- [ ] Build times within normal range (4-6 minutes with cache hit)
- [ ] No regressions reported
- [ ] Monitoring scripts operational

**Long-term (Month 1):**

- [ ] Consistent cache performance
- [ ] No related issues filed
- [ ] Documentation complete and accurate
- [ ] Health checks running daily

## Continue to Part 6

Next part covers troubleshooting and lessons learned.
