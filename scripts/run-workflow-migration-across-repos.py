#!/usr/bin/env python3
# file: scripts/run-workflow-migration-across-repos.py
# version: 1.0.0
# guid: b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e

"""
Run workflow permissions migration across multiple repositories.

This script:
1. Discovers all repositories in the workspace
2. Runs the migration scripts on each repository
3. Provides a comprehensive summary
4. Validates the results
"""

import subprocess
from pathlib import Path
from typing import Dict, Any, List
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_repositories(workspace_root: Path) -> List[Path]:
    """Find all repositories in the workspace."""
    repositories = []
    
    # Look for directories with .git subdirectories
    for item in workspace_root.iterdir():
        if item.is_dir() and (item / '.git').exists():
            repositories.append(item)
    
    return repositories

def has_github_workflows(repo_path: Path) -> bool:
    """Check if a repository has GitHub workflows."""
    workflows_dir = repo_path / '.github' / 'workflows'
    return workflows_dir.exists() and any(workflows_dir.glob('*.yml'))

def run_script(script_path: Path, repo_path: Path, extra_args: List[str] = None) -> Dict[str, Any]:
    """Run a script in a repository and return the result."""
    if extra_args is None:
        extra_args = []
    
    try:
        cmd = ['python3', str(script_path)] + extra_args
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        return {
            'success': result.returncode == 0,
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
    
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Script timed out after 60 seconds'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def parse_script_output(output: str) -> Dict[str, Any]:
    """Parse the summary section from script output."""
    lines = output.split('\n')
    summary = {}
    
    # Look for summary section
    in_summary = False
    for line in lines:
        if 'SUMMARY' in line and '=' in line:
            in_summary = True
            continue
        
        if in_summary:
            if 'Files processed:' in line:
                summary['files_processed'] = int(line.split(':')[1].strip())
            elif 'Modified:' in line:
                summary['modified'] = int(line.split(':')[1].strip())
            elif 'Already correct:' in line:
                summary['already_correct'] = int(line.split(':')[1].strip())
            elif 'Errors:' in line:
                summary['errors'] = int(line.split(':')[1].strip())
            elif 'Not reusable workflows:' in line:
                summary['not_reusable'] = int(line.split(':')[1].strip())
    
    return summary

def main():
    parser = argparse.ArgumentParser(description="Run workflow migration across repositories")
    parser.add_argument('--workspace-root', type=Path,
                       default=Path('/Users/jdfalk/repos/github.com/jdfalk'),
                       help='Root directory containing repositories')
    parser.add_argument('--scripts-repo', type=Path,
                       default=Path('/Users/jdfalk/repos/github.com/jdfalk/ghcommon'),
                       help='Repository containing the migration scripts')
    parser.add_argument('--dry-run', action='store_true',
                       help='Run in dry-run mode (show what would be changed)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check if scripts repository exists
    scripts_repo = args.scripts_repo
    if not scripts_repo.exists():
        logger.error(f"Scripts repository not found: {scripts_repo}")
        return 1
    
    # Define script paths
    remove_permissions_script = scripts_repo / 'scripts' / 'remove-reusable-workflow-permissions.py'
    update_calling_script = scripts_repo / 'scripts' / 'update-calling-workflows.py'
    validate_script = scripts_repo / 'scripts' / 'validate-workflow-permissions.py'
    analysis_file = scripts_repo / 'workflow-permissions-analysis.json'
    
    # Check if scripts exist
    for script in [remove_permissions_script, update_calling_script, validate_script]:
        if not script.exists():
            logger.error(f"Script not found: {script}")
            return 1
    
    if not analysis_file.exists():
        logger.error(f"Analysis file not found: {analysis_file}")
        logger.info("Please run the analysis script first in the ghcommon repository")
        return 1
    
    # Find repositories
    repositories = find_repositories(args.workspace_root)
    
    if not repositories:
        logger.error(f"No repositories found in {args.workspace_root}")
        return 1
    
    logger.info(f"Found {len(repositories)} repositories")
    
    # Filter repositories with GitHub workflows
    repos_with_workflows = []
    for repo in repositories:
        if has_github_workflows(repo):
            repos_with_workflows.append(repo)
        else:
            logger.debug(f"Skipping {repo.name} (no GitHub workflows)")
    
    logger.info(f"Found {len(repos_with_workflows)} repositories with GitHub workflows")
    
    # Process each repository
    results = {}
    
    for repo_path in repos_with_workflows:
        repo_name = repo_path.name
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing repository: {repo_name}")
        logger.info(f"{'='*60}")
        
        repo_results = {
            'path': str(repo_path),
            'remove_permissions': {},
            'update_calling': {},
            'validation': {}
        }
        
        # Step 1: Remove permissions from reusable workflows
        logger.info("Step 1: Removing permissions from reusable workflows...")
        script_args = ['--dry-run'] if args.dry_run else []
        result = run_script(remove_permissions_script, repo_path, script_args)
        repo_results['remove_permissions'] = result
        
        if result['success']:
            summary = parse_script_output(result['stdout'])
            logger.info(f"  - Files processed: {summary.get('files_processed', 0)}")
            logger.info(f"  - Modified: {summary.get('modified', 0)}")
            logger.info(f"  - Already correct: {summary.get('already_correct', 0)}")
            logger.info(f"  - Errors: {summary.get('errors', 0)}")
        else:
            logger.error(f"  - Failed: {result.get('error', 'Unknown error')}")
        
        # Step 2: Update calling workflows
        logger.info("Step 2: Updating calling workflows...")
        script_args = [
            f'--analysis-file={analysis_file}',
            '--dry-run' if args.dry_run else ''
        ]
        script_args = [arg for arg in script_args if arg]  # Remove empty strings
        
        result = run_script(update_calling_script, repo_path, script_args)
        repo_results['update_calling'] = result
        
        if result['success']:
            summary = parse_script_output(result['stdout'])
            logger.info(f"  - Files processed: {summary.get('files_processed', 0)}")
            logger.info(f"  - Modified: {summary.get('modified', 0)}")
            logger.info(f"  - Already correct: {summary.get('already_correct', 0)}")
            logger.info(f"  - Errors: {summary.get('errors', 0)}")
        else:
            logger.error(f"  - Failed: {result.get('error', 'Unknown error')}")
        
        # Step 3: Validate (only if not dry-run)
        if not args.dry_run:
            logger.info("Step 3: Validating workflows...")
            script_args = [f'--analysis-file={analysis_file}']
            result = run_script(validate_script, repo_path, script_args)
            repo_results['validation'] = result
            
            if result['success']:
                if '🎉 All workflows are valid!' in result['stdout']:
                    logger.info("  - ✅ All workflows are valid!")
                else:
                    logger.warning("  - ⚠️  Some workflows have issues")
            else:
                logger.error(f"  - Failed: {result.get('error', 'Unknown error')}")
        
        results[repo_name] = repo_results
    
    # Overall summary
    print(f"\n{'='*80}")
    print("OVERALL MIGRATION SUMMARY")
    print(f"{'='*80}")
    
    total_repos = len(results)
    successful_repos = 0
    total_files_modified = 0
    total_files_processed = 0
    
    for repo_name, repo_results in results.items():
        print(f"\n📁 {repo_name}")
        
        # Check if repository migration was successful
        remove_success = repo_results['remove_permissions'].get('success', False)
        update_success = repo_results['update_calling'].get('success', False)
        validate_success = repo_results.get('validation', {}).get('success', True)  # Default True for dry-run
        
        if remove_success and update_success and validate_success:
            successful_repos += 1
            print("   ✅ Migration successful")
            
            # Extract file counts
            remove_summary = parse_script_output(repo_results['remove_permissions'].get('stdout', ''))
            update_summary = parse_script_output(repo_results['update_calling'].get('stdout', ''))
            
            modified = remove_summary.get('modified', 0) + update_summary.get('modified', 0)
            processed = remove_summary.get('files_processed', 0) + update_summary.get('files_processed', 0)
            
            total_files_modified += modified
            total_files_processed += processed
            
            if modified > 0:
                print(f"   📝 Modified {modified} workflow files")
            else:
                print("   ✅ All workflows already correct")
        else:
            print("   ❌ Migration failed")
            
            if not remove_success:
                print("      - Remove permissions step failed")
            if not update_success:
                print("      - Update calling workflows step failed")
            if not validate_success:
                print("      - Validation step failed")
    
    print("\n📊 FINAL SUMMARY")
    print(f"   Repositories processed: {total_repos}")
    print(f"   Successful migrations: {successful_repos}")
    print(f"   Total workflow files processed: {total_files_processed}")
    print(f"   Total workflow files modified: {total_files_modified}")
    
    if args.dry_run:
        print("\n⚠️  This was a dry run. Remove --dry-run to apply changes.")
    
    success_rate = (successful_repos / total_repos) * 100 if total_repos > 0 else 0
    print(f"   Success rate: {success_rate:.1f}%")
    
    if successful_repos == total_repos:
        print("\n🎉 All repositories migrated successfully!")
        return 0
    else:
        print(f"\n⚠️  {total_repos - successful_repos} repositories had issues.")
        return 1

if __name__ == '__main__':
    exit(main())
