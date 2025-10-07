<!-- file: docs/cross-registry-todos/task-09/t09-part5.md -->
<!-- version: 1.0.0 -->
<!-- guid: t09-ci-migration-part5-e5f6g7h8-i9j0 -->

# Task 09 Part 5: Monitoring and Performance Analysis

## Migration Monitoring Dashboard

Create a monitoring system to track migration progress across all repositories:

```python
#!/usr/bin/env python3
# file: scripts/migration-dashboard.py
# version: 1.0.0
# guid: migration-dashboard

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List

def get_workflow_status(repo: str, branch: str = 'main') -> Dict:
    """Get latest CI workflow status for a repository."""
    result = subprocess.run(
        ['gh', 'run', 'list',
         '--repo', f'jdfalk/{repo}',
         '--branch', branch,
         '--workflow', 'ci.yml',
         '--limit', '1',
         '--json', 'databaseId,status,conclusion,createdAt,updatedAt,displayTitle'],
        capture_output=True,
        text=True
    )

    if result.returncode != 0 or not result.stdout.strip():
        return {'status': 'unknown'}

    runs = json.loads(result.stdout)
    if not runs:
        return {'status': 'no_runs'}

    run = runs[0]
    return {
        'id': run['databaseId'],
        'status': run['status'],
        'conclusion': run['conclusion'],
        'created_at': run['createdAt'],
        'updated_at': run['updatedAt'],
        'title': run['displayTitle'],
    }

def check_uses_reusable_workflow(repo: str) -> bool:
    """Check if repository uses reusable CI workflow."""
    result = subprocess.run(
        ['gh', 'api', f'repos/jdfalk/{repo}/contents/.github/workflows/ci.yml'],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return False

    content_data = json.loads(result.stdout)
    import base64
    content = base64.b64decode(content_data['content']).decode('utf-8')

    return 'jdfalk/ghcommon/.github/workflows/reusable-ci.yml' in content

def generate_dashboard():
    """Generate migration status dashboard."""
    inventory_file = Path('migration-inventory.json')

    if not inventory_file.exists():
        print("❌ migration-inventory.json not found")
        return

    with open(inventory_file) as f:
        inventory = json.load(f)

    print("=" * 80)
    print("CI WORKFLOW MIGRATION DASHBOARD")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print("")

    migrated_count = 0
    pending_count = 0
    failed_count = 0

    for repo_data in inventory:
        repo = repo_data['name']
        has_ci = repo_data.get('has_ci_workflow', False)

        if not has_ci:
            continue

        print(f"Repository: {repo}")
        print("-" * 40)

        # Check if using reusable workflow
        uses_reusable = check_uses_reusable_workflow(repo)
        print(f"  Uses reusable workflow: {'✅ Yes' if uses_reusable else '❌ No'}")

        # Get CI status
        status = get_workflow_status(repo)
        if status.get('status') == 'unknown':
            print(f"  Latest CI run: ⚠️  Unknown")
            failed_count += 1
        elif status.get('status') == 'no_runs':
            print(f"  Latest CI run: 📭 No runs")
            pending_count += 1
        else:
            conclusion_emoji = {
                'success': '✅',
                'failure': '❌',
                'cancelled': '⏭️',
                'skipped': '⏭️',
            }.get(status.get('conclusion', ''), '⚠️')

            print(f"  Latest CI run: {conclusion_emoji} {status.get('conclusion', 'unknown')}")
            print(f"  Run ID: {status.get('id')}")
            print(f"  Title: {status.get('title')}")

            if status.get('conclusion') == 'success' and uses_reusable:
                migrated_count += 1
            elif status.get('conclusion') == 'failure':
                failed_count += 1
            else:
                pending_count += 1

        print("")

    # Summary
    total = migrated_count + pending_count + failed_count
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Migrated successfully: {migrated_count}")
    print(f"⏳ Pending/In progress: {pending_count}")
    print(f"❌ Failed/Needs attention: {failed_count}")
    print(f"📊 Total: {total}")
    print("")

    if total > 0:
        progress = (migrated_count / total) * 100
        print(f"Progress: {progress:.1f}%")
        print(f"[{'█' * int(progress // 2)}{'░' * (50 - int(progress // 2))}]")

if __name__ == '__main__':
    generate_dashboard()
```

## Performance Comparison

Compare CI performance before and after migration:

```bash
#!/bin/bash
# file: scripts/compare-ci-performance.sh
# version: 1.0.0
# guid: compare-ci-performance

set -e

REPO="$1"
MAIN_BRANCH="${2:-main}"
PR_BRANCH="${3:-feat/migrate-to-reusable-ci}"

if [ -z "$REPO" ]; then
  echo "Usage: $0 <repo> [main-branch] [pr-branch]"
  exit 1
fi

echo "=== CI Performance Comparison ==="
echo "Repository: $REPO"
echo "Main branch: $MAIN_BRANCH"
echo "PR branch: $PR_BRANCH"
echo ""

# Get last 10 runs from main branch
echo "Fetching main branch runs..."
MAIN_RUNS=$(gh run list \
  --repo "jdfalk/$REPO" \
  --branch "$MAIN_BRANCH" \
  --workflow ci.yml \
  --limit 10 \
  --json databaseId,createdAt,updatedAt,conclusion)

# Get last 10 runs from PR branch
echo "Fetching PR branch runs..."
PR_RUNS=$(gh run list \
  --repo "jdfalk/$REPO" \
  --branch "$PR_BRANCH" \
  --workflow ci.yml \
  --limit 10 \
  --json databaseId,createdAt,updatedAt,conclusion)

# Calculate average duration for main branch
echo ""
echo "=== Main Branch Statistics ==="
echo "$MAIN_RUNS" | jq -r '
  map(
    select(.conclusion == "success") |
    ((.updatedAt | fromdateiso8601) - (.createdAt | fromdateiso8601))
  ) |
  {
    count: length,
    total_seconds: add,
    average_seconds: (add / length),
    average_minutes: ((add / length) / 60 | floor),
    min_seconds: min,
    max_seconds: max
  } |
  "Successful runs: \(.count)",
  "Average duration: \(.average_minutes) minutes",
  "Min duration: \(.min_seconds / 60 | floor) minutes",
  "Max duration: \(.max_seconds / 60 | floor) minutes"
'

# Calculate average duration for PR branch
echo ""
echo "=== PR Branch Statistics ==="
echo "$PR_RUNS" | jq -r '
  map(
    select(.conclusion == "success") |
    ((.updatedAt | fromdateiso8601) - (.createdAt | fromdateiso8601))
  ) |
  {
    count: length,
    total_seconds: add,
    average_seconds: (add / length),
    average_minutes: ((add / length) / 60 | floor),
    min_seconds: min,
    max_seconds: max
  } |
  "Successful runs: \(.count)",
  "Average duration: \(.average_minutes) minutes",
  "Min duration: \(.min_seconds / 60 | floor) minutes",
  "Max duration: \(.max_seconds / 60 | floor) minutes"
'

# Compare
echo ""
echo "=== Performance Comparison ==="

MAIN_AVG=$(echo "$MAIN_RUNS" | jq -r 'map(select(.conclusion == "success") | ((.updatedAt | fromdateiso8601) - (.createdAt | fromdateiso8601))) | add / length')

PR_AVG=$(echo "$PR_RUNS" | jq -r 'map(select(.conclusion == "success") | ((.updatedAt | fromdateiso8601) - (.createdAt | fromdateiso8601))) | add / length')

DIFF=$(echo "$PR_AVG - $MAIN_AVG" | bc)
PERCENT=$(echo "scale=2; ($DIFF / $MAIN_AVG) * 100" | bc)

if (( $(echo "$DIFF > 0" | bc -l) )); then
  echo "⚠️  PR branch is slower by ${DIFF}s (${PERCENT}%)"
elif (( $(echo "$DIFF < 0" | bc -l) )); then
  DIFF_ABS=$(echo "$DIFF * -1" | bc)
  PERCENT_ABS=$(echo "$PERCENT * -1" | bc)
  echo "✅ PR branch is faster by ${DIFF_ABS}s (${PERCENT_ABS}%)"
else
  echo "✅ Performance is the same"
fi
```

## Rollback Procedures

### Automated Rollback Script

```bash
#!/bin/bash
# file: scripts/rollback-migration.sh
# version: 1.0.0
# guid: rollback-migration

set -e

REPO="$1"
BACKUP_BRANCH="${2:-backup-before-migration}"

if [ -z "$REPO" ]; then
  echo "Usage: $0 <repo> [backup-branch]"
  exit 1
fi

echo "=== Rolling Back CI Migration ==="
echo "Repository: $REPO"
echo "Backup branch: $BACKUP_BRANCH"
echo ""

read -p "Are you sure you want to rollback? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
  echo "❌ Rollback cancelled"
  exit 1
fi

cd "/tmp/$REPO" 2>/dev/null || {
  echo "Cloning repository..."
  gh repo clone "jdfalk/$REPO" "/tmp/$REPO"
  cd "/tmp/$REPO"
}

# Check if backup branch exists
if ! git show-ref --verify --quiet "refs/remotes/origin/$BACKUP_BRANCH"; then
  echo "❌ Backup branch not found: $BACKUP_BRANCH"
  echo "Available branches:"
  git branch -r | grep backup
  exit 1
fi

# Create rollback branch
git checkout main
git pull origin main
git checkout -b "rollback/ci-migration-$(date +%Y%m%d)"

# Restore files from backup branch
echo "Restoring files from backup..."
git checkout "origin/$BACKUP_BRANCH" -- .github/workflows/ci.yml

# Remove repository-config.yml if it exists
if [ -f ".github/repository-config.yml" ]; then
  git rm .github/repository-config.yml
fi

# Commit rollback
git add .github/workflows/ci.yml
git commit -m "revert(ci): rollback migration to reusable workflow

Rolling back CI workflow migration due to issues.

Restored:
- .github/workflows/ci.yml from $BACKUP_BRANCH

Removed:
- .github/repository-config.yml

The workflow now uses the previous standalone CI configuration."

# Push rollback branch
git push origin "rollback/ci-migration-$(date +%Y%m%d)"

# Create PR
gh pr create \
  --title "revert(ci): rollback migration to reusable workflow" \
  --body "Rolling back CI migration due to issues. Restoring previous workflow configuration." \
  --label ci,rollback \
  --base main

echo ""
echo "✅ Rollback PR created"
echo "Review and merge the PR to complete rollback"
```

## Migration Success Metrics

Track key metrics to measure migration success:

```python
#!/usr/bin/env python3
# file: scripts/migration-metrics.py
# version: 1.0.0
# guid: migration-metrics

import json
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List

def get_workflow_runs(repo: str, days: int = 30) -> List[Dict]:
    """Get workflow runs for the last N days."""
    since_date = (datetime.now() - timedelta(days=days)).isoformat()

    result = subprocess.run(
        ['gh', 'api',
         f'repos/jdfalk/{repo}/actions/workflows/ci.yml/runs',
         '--paginate',
         '-f', f'created=>{since_date}'],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return []

    data = json.loads(result.stdout)
    return data.get('workflow_runs', [])

def calculate_metrics(runs: List[Dict]) -> Dict:
    """Calculate metrics from workflow runs."""
    if not runs:
        return {}

    total_runs = len(runs)
    successful_runs = len([r for r in runs if r.get('conclusion') == 'success'])
    failed_runs = len([r for r in runs if r.get('conclusion') == 'failure'])

    # Calculate average duration for successful runs
    durations = []
    for run in runs:
        if run.get('conclusion') == 'success':
            created = datetime.fromisoformat(run['created_at'].replace('Z', '+00:00'))
            updated = datetime.fromisoformat(run['updated_at'].replace('Z', '+00:00'))
            duration = (updated - created).total_seconds()
            durations.append(duration)

    avg_duration = sum(durations) / len(durations) if durations else 0

    # Success rate
    success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0

    return {
        'total_runs': total_runs,
        'successful_runs': successful_runs,
        'failed_runs': failed_runs,
        'success_rate': success_rate,
        'average_duration_minutes': avg_duration / 60,
        'average_duration_seconds': avg_duration,
    }

def main():
    repos = ['ghcommon', 'ubuntu-autoinstall-agent']

    print("=" * 80)
    print("CI MIGRATION SUCCESS METRICS")
    print(f"Period: Last 30 days")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print("")

    for repo in repos:
        print(f"Repository: {repo}")
        print("-" * 40)

        runs = get_workflow_runs(repo, days=30)
        metrics = calculate_metrics(runs)

        if not metrics:
            print("  ⚠️  No data available")
            print("")
            continue

        print(f"  Total runs: {metrics['total_runs']}")
        print(f"  Successful: {metrics['successful_runs']} ({metrics['success_rate']:.1f}%)")
        print(f"  Failed: {metrics['failed_runs']}")
        print(f"  Avg duration: {metrics['average_duration_minutes']:.1f} minutes")
        print("")

    print("=" * 80)
    print("KEY PERFORMANCE INDICATORS")
    print("=" * 80)
    print("✅ Target success rate: > 95%")
    print("✅ Target avg duration: < 15 minutes")
    print("✅ Target failed runs: < 5%")

if __name__ == '__main__':
    main()
```

---

**Part 5 Complete**: Monitoring dashboard, performance comparison tools, rollback procedures, and success metrics tracking. ✅

**Continue to Part 6** for troubleshooting, lessons learned, and task completion.
