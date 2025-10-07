<!-- file: docs/cross-registry-todos/task-09/t09-part4.md -->
<!-- version: 1.0.0 -->
<!-- guid: t09-ci-migration-part4-d4e5f6g7-h8i9 -->

# Task 09 Part 4: Batch Migration and Automation Tools

## Batch Migration Strategy

After successfully migrating ghcommon and ubuntu-autoinstall-agent, prepare for migrating additional
repositories.

### Repository Inventory

Create an inventory of repositories to migrate:

```bash
#!/bin/bash
# file: scripts/create-migration-inventory.sh
# version: 1.0.0
# guid: create-migration-inventory

set -e

OUTPUT_FILE="migration-inventory.json"

echo "Creating repository migration inventory..."

# Get all repositories for user
gh repo list jdfalk --limit 100 --json name,defaultBranchRef,url | \
  jq -r '
  .[] |
  select(.defaultBranchRef.name != null) |
  {
    name: .name,
    default_branch: .defaultBranchRef.name,
    url: .url,
    has_ci_workflow: false,
    migrated: false
  }
  ' > "$OUTPUT_FILE"

echo "✅ Inventory created: $OUTPUT_FILE"

# Check each repo for CI workflow
jq -r '.name' "$OUTPUT_FILE" | while read repo; do
  echo "Checking $repo for CI workflow..."

  if gh api repos/jdfalk/$repo/contents/.github/workflows/ci.yml >/dev/null 2>&1; then
    # Update JSON to mark has_ci_workflow = true
    jq --arg repo "$repo" \
      '(.[] | select(.name == $repo) | .has_ci_workflow) = true' \
      "$OUTPUT_FILE" > "$OUTPUT_FILE.tmp"
    mv "$OUTPUT_FILE.tmp" "$OUTPUT_FILE"
    echo "  ✅ Has CI workflow"
  else
    echo "  ⏭️ No CI workflow"
  fi
done

echo ""
echo "=== Migration Inventory Summary ==="
jq -r '
  "Total repositories: \(length)",
  "Has CI workflow: \(map(select(.has_ci_workflow == true)) | length)",
  "Needs migration: \(map(select(.has_ci_workflow == true and .migrated == false)) | length)"
' "$OUTPUT_FILE"

echo ""
echo "Repositories with CI workflows:"
jq -r '.[] | select(.has_ci_workflow == true) | "  - \(.name)"' "$OUTPUT_FILE"
```

**Run the inventory:**

```bash
chmod +x scripts/create-migration-inventory.sh
scripts/create-migration-inventory.sh
```

### Migration Template Generator

Create a tool to generate migration files for any repository:

```python
#!/usr/bin/env python3
# file: scripts/generate-migration-files.py
# version: 1.0.0
# guid: generate-migration-files

import argparse
import json
import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional

def detect_languages(repo_path: Path) -> Dict[str, bool]:
    """Detect programming languages in repository."""
    languages = {
        'rust': False,
        'go': False,
        'python': False,
        'javascript': False,
        'typescript': False,
    }

    # Check for language-specific files
    if (repo_path / 'Cargo.toml').exists():
        languages['rust'] = True

    if (repo_path / 'go.mod').exists():
        languages['go'] = True

    if (repo_path / 'pyproject.toml').exists() or \
       (repo_path / 'setup.py').exists() or \
       (repo_path / 'requirements.txt').exists():
        languages['python'] = True

    if (repo_path / 'package.json').exists():
        package_json = json.loads((repo_path / 'package.json').read_text())
        if 'typescript' in package_json.get('devDependencies', {}) or \
           'typescript' in package_json.get('dependencies', {}):
            languages['typescript'] = True
        else:
            languages['javascript'] = True

    return languages

def generate_repository_config(
    repo_name: str,
    languages: Dict[str, bool],
    custom_settings: Optional[Dict] = None
) -> Dict:
    """Generate repository-config.yml content."""
    config = {
        'languages': languages,
        'workflow': {
            'fail_fast': False,
            'cancel_in_progress': True,
            'timeout_minutes': 30,
        },
        'cache': {
            'enabled': True,
            'key_prefix': 'v1',
        },
    }

    # Add language-specific settings
    if languages.get('rust'):
        config['rust'] = {
            'toolchain': 'stable',
            'components': ['rustfmt', 'clippy'],
            'test_args': '--verbose',
        }

    if languages.get('go'):
        config['go'] = {
            'version': '1.21',
            'test_args': '-v -race -coverprofile=coverage.txt',
        }

    if languages.get('python'):
        config['python'] = {
            'version': '3.11',
            'test_command': 'pytest -v --cov',
        }

    # Merge custom settings
    if custom_settings:
        config.update(custom_settings)

    return config

def generate_ci_workflow(
    repo_name: str,
    languages: Dict[str, bool]
) -> str:
    """Generate ci.yml workflow content."""
    workflow = {
        'name': 'CI',
        'on': {
            'push': {'branches': ['main', 'develop']},
            'pull_request': {'branches': ['main', 'develop']},
            'workflow_dispatch': None,
        },
        'permissions': {
            'contents': 'read',
            'pull-requests': 'write',
            'security-events': 'write',
        },
        'jobs': {
            'ci': {
                'uses': 'jdfalk/ghcommon/.github/workflows/reusable-ci.yml@main',
                'with': {
                    'repository': '${{ github.repository }}',
                    'ref': '${{ github.ref }}',
                    'enable_rust': languages.get('rust', False),
                    'enable_go': languages.get('go', False),
                    'enable_python': languages.get('python', False),
                    'enable_frontend': languages.get('javascript', False) or languages.get('typescript', False),
                    'run_tests': True,
                    'run_linters': True,
                },
                'secrets': {
                    'GITHUB_TOKEN': '${{ secrets.GITHUB_TOKEN }}',
                },
            },
        },
    }

    return yaml.dump(workflow, default_flow_style=False, sort_keys=False)

def main():
    parser = argparse.ArgumentParser(description='Generate migration files for repositories')
    parser.add_argument('repo_path', type=Path, help='Path to repository')
    parser.add_argument('--output-dir', type=Path, default=Path('.'), help='Output directory')
    parser.add_argument('--custom-config', type=Path, help='Path to custom config JSON')

    args = parser.parse_args()

    if not args.repo_path.exists():
        print(f"❌ Repository path not found: {args.repo_path}")
        return 1

    repo_name = args.repo_path.name
    print(f"Generating migration files for: {repo_name}")

    # Detect languages
    languages = detect_languages(args.repo_path)
    print(f"Detected languages: {', '.join([k for k, v in languages.items() if v])}")

    # Load custom config if provided
    custom_settings = None
    if args.custom_config and args.custom_config.exists():
        with open(args.custom_config) as f:
            custom_settings = json.load(f)

    # Generate repository config
    repo_config = generate_repository_config(repo_name, languages, custom_settings)
    config_output = args.output_dir / f'{repo_name}-repository-config.yml'
    with open(config_output, 'w') as f:
        yaml.dump(repo_config, f, default_flow_style=False, sort_keys=False)
    print(f"✅ Generated: {config_output}")

    # Generate CI workflow
    ci_workflow = generate_ci_workflow(repo_name, languages)
    workflow_output = args.output_dir / f'{repo_name}-ci.yml'
    with open(workflow_output, 'w') as f:
        f.write(ci_workflow)
    print(f"✅ Generated: {workflow_output}")

    print("")
    print("Next steps:")
    print(f"1. Review generated files in {args.output_dir}")
    print(f"2. Copy {config_output.name} to {repo_name}/.github/repository-config.yml")
    print(f"3. Copy {workflow_output.name} to {repo_name}/.github/workflows/ci.yml")
    print(f"4. Test locally and create PR")

    return 0

if __name__ == '__main__':
    exit(main())
```

**Usage:**

```bash
chmod +x scripts/generate-migration-files.py

# Generate files for a repository
python3 scripts/generate-migration-files.py \
  /path/to/repo \
  --output-dir /tmp/migration-files

# With custom configuration
cat > /tmp/custom-rust-config.json << 'EOF'
{
  "rust": {
    "targets": ["x86_64-unknown-linux-gnu", "aarch64-unknown-linux-gnu"],
    "features": ["cross-compilation"]
  },
  "testing": {
    "coverage": {
      "enabled": true,
      "tool": "llvm-cov"
    }
  }
}
EOF

python3 scripts/generate-migration-files.py \
  /path/to/rust-repo \
  --output-dir /tmp/migration-files \
  --custom-config /tmp/custom-rust-config.json
```

### Bulk Migration Script

Automate migration across multiple repositories:

```bash
#!/bin/bash
# file: scripts/bulk-migrate-repos.sh
# version: 1.0.0
# guid: bulk-migrate-repos

set -e

REPOS_FILE="${1:-migration-inventory.json}"
DRY_RUN="${2:-true}"

if [ ! -f "$REPOS_FILE" ]; then
  echo "❌ Repos file not found: $REPOS_FILE"
  exit 1
fi

echo "=== Bulk Repository Migration ==="
echo "Repos file: $REPOS_FILE"
echo "Dry run: $DRY_RUN"
echo ""

# Get repos that need migration
REPOS=$(jq -r '.[] | select(.has_ci_workflow == true and .migrated == false) | .name' "$REPOS_FILE")

if [ -z "$REPOS" ]; then
  echo "✅ No repositories need migration"
  exit 0
fi

echo "Repositories to migrate:"
echo "$REPOS"
echo ""

# Process each repository
echo "$REPOS" | while read repo; do
  echo "=== Processing: $repo ==="

  # Clone or update repo
  if [ -d "/tmp/$repo" ]; then
    echo "Updating existing clone..."
    cd "/tmp/$repo"
    git fetch origin
    git checkout main
    git pull origin main
  else
    echo "Cloning repository..."
    gh repo clone "jdfalk/$repo" "/tmp/$repo"
    cd "/tmp/$repo"
  fi

  # Generate migration files
  echo "Generating migration files..."
  python3 "$(dirname "$0")/generate-migration-files.py" \
    "/tmp/$repo" \
    --output-dir "/tmp/migration-files-$repo"

  if [ "$DRY_RUN" = "false" ]; then
    # Create feature branch
    git checkout -b feat/migrate-to-reusable-ci || git checkout feat/migrate-to-reusable-ci

    # Copy generated files
    cp "/tmp/migration-files-$repo/$repo-repository-config.yml" .github/repository-config.yml
    cp "/tmp/migration-files-$repo/$repo-ci.yml" .github/workflows/ci.yml

    # Commit and push
    git add .github/repository-config.yml .github/workflows/ci.yml
    git commit -m "feat(ci): migrate to reusable CI workflow

Automated migration generated by bulk-migrate-repos.sh script."

    git push origin feat/migrate-to-reusable-ci

    # Create PR
    gh pr create \
      --title "feat(ci): migrate to reusable CI workflow" \
      --body "Automated migration to centralized reusable CI workflow." \
      --label ci,enhancement \
      --draft

    echo "✅ PR created for $repo"
  else
    echo "⏭️ Dry run - skipping actual migration"
  fi

  echo ""
done

echo "=== Migration Complete ==="
```

**Usage:**

```bash
# Dry run (default)
scripts/bulk-migrate-repos.sh migration-inventory.json true

# Actual migration
scripts/bulk-migrate-repos.sh migration-inventory.json false
```

## Migration Validation

### Validation Script

Create a comprehensive validation tool:

```python
#!/usr/bin/env python3
# file: scripts/validate-migration.py
# version: 1.0.0
# guid: validate-migration

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

def run_command(cmd: List[str], cwd: Path = None) -> Tuple[int, str, str]:
    """Run command and return exit code, stdout, stderr."""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout, result.stderr

def validate_yaml_syntax(file_path: Path) -> bool:
    """Validate YAML syntax using yamllint."""
    code, _, _ = run_command(['yamllint', str(file_path)])
    return code == 0

def validate_workflow_syntax(file_path: Path) -> bool:
    """Validate GitHub Actions workflow syntax using actionlint."""
    code, _, _ = run_command(['actionlint', str(file_path)])
    return code == 0

def compare_ci_runs(repo: str, main_branch: str, pr_branch: str) -> Dict:
    """Compare CI runs between main and PR branches."""
    # Get latest run on main
    code, stdout, _ = run_command([
        'gh', 'run', 'list',
        '--repo', f'jdfalk/{repo}',
        '--branch', main_branch,
        '--workflow', 'ci.yml',
        '--limit', '1',
        '--json', 'databaseId,conclusion,jobs'
    ])

    if code != 0:
        return {'error': 'Failed to get main branch run'}

    main_run = json.loads(stdout)[0] if stdout.strip() else None

    # Get latest run on PR branch
    code, stdout, _ = run_command([
        'gh', 'run', 'list',
        '--repo', f'jdfalk/{repo}',
        '--branch', pr_branch,
        '--workflow', 'ci.yml',
        '--limit', '1',
        '--json', 'databaseId,conclusion,jobs'
    ])

    if code != 0:
        return {'error': 'Failed to get PR branch run'}

    pr_run = json.loads(stdout)[0] if stdout.strip() else None

    if not main_run or not pr_run:
        return {'error': 'Missing run data'}

    # Compare
    comparison = {
        'main': {
            'id': main_run['databaseId'],
            'conclusion': main_run['conclusion'],
            'job_count': len(main_run.get('jobs', [])),
        },
        'pr': {
            'id': pr_run['databaseId'],
            'conclusion': pr_run['conclusion'],
            'job_count': len(pr_run.get('jobs', [])),
        },
        'same_conclusion': main_run['conclusion'] == pr_run['conclusion'],
        'same_job_count': len(main_run.get('jobs', [])) == len(pr_run.get('jobs', [])),
    }

    return comparison

def main():
    parser = argparse.ArgumentParser(description='Validate CI migration')
    parser.add_argument('repo_path', type=Path, help='Path to repository')
    parser.add_argument('--compare-branches', nargs=2, metavar=('MAIN', 'PR'),
                       help='Compare CI runs between branches')

    args = parser.parse_args()

    if not args.repo_path.exists():
        print(f"❌ Repository not found: {args.repo_path}")
        return 1

    repo_name = args.repo_path.name
    print(f"Validating migration for: {repo_name}")
    print("")

    # Validate files
    checks_passed = 0
    checks_failed = 0

    # Check repository-config.yml
    config_file = args.repo_path / '.github' / 'repository-config.yml'
    if config_file.exists():
        if validate_yaml_syntax(config_file):
            print(f"✅ repository-config.yml: Valid YAML")
            checks_passed += 1
        else:
            print(f"❌ repository-config.yml: Invalid YAML")
            checks_failed += 1
    else:
        print(f"⚠️  repository-config.yml: Not found")

    # Check ci.yml
    ci_file = args.repo_path / '.github' / 'workflows' / 'ci.yml'
    if ci_file.exists():
        if validate_yaml_syntax(ci_file):
            print(f"✅ ci.yml: Valid YAML")
            checks_passed += 1
        else:
            print(f"❌ ci.yml: Invalid YAML")
            checks_failed += 1

        if validate_workflow_syntax(ci_file):
            print(f"✅ ci.yml: Valid workflow syntax")
            checks_passed += 1
        else:
            print(f"❌ ci.yml: Invalid workflow syntax")
            checks_failed += 1
    else:
        print(f"❌ ci.yml: Not found")
        checks_failed += 1

    # Compare branches if requested
    if args.compare_branches:
        main_branch, pr_branch = args.compare_branches
        print(f"\nComparing CI runs: {main_branch} vs {pr_branch}")

        comparison = compare_ci_runs(repo_name, main_branch, pr_branch)

        if 'error' in comparison:
            print(f"❌ Comparison failed: {comparison['error']}")
            checks_failed += 1
        else:
            print(f"Main branch run: {comparison['main']['id']}")
            print(f"  Conclusion: {comparison['main']['conclusion']}")
            print(f"  Jobs: {comparison['main']['job_count']}")
            print(f"PR branch run: {comparison['pr']['id']}")
            print(f"  Conclusion: {comparison['pr']['conclusion']}")
            print(f"  Jobs: {comparison['pr']['job_count']}")

            if comparison['same_conclusion'] and comparison['same_job_count']:
                print("✅ CI behavior matches")
                checks_passed += 1
            else:
                print("⚠️  CI behavior differs")
                checks_failed += 1

    # Summary
    print(f"\n=== Validation Summary ===")
    print(f"Passed: {checks_passed}")
    print(f"Failed: {checks_failed}")

    return 0 if checks_failed == 0 else 1

if __name__ == '__main__':
    exit(main())
```

**Usage:**

```bash
chmod +x scripts/validate-migration.py

# Validate files only
python3 scripts/validate-migration.py /path/to/repo

# Validate and compare branches
python3 scripts/validate-migration.py /path/to/repo \
  --compare-branches main feat/migrate-to-reusable-ci
```

---

**Part 4 Complete**: Batch migration strategy, template generation tool, bulk migration script, and
validation automation. ✅

**Continue to Part 5** for monitoring, rollback procedures, and migration tracking.
