#!/usr/bin/env python3
"""
# file: scripts/issue_manager.py
Unified GitHub issue management script.

This script provides comprehensive issue management functionality:
1. Process issue updates from issue_updates.json (create, update, comment, close, delete)
2. Manage Copilot review comment tickets
3. Close duplicate issues by title
4. Generate tickets for CodeQL security alerts
5. Provide unified CLI interface for all operations

Environment Variables:
  GH_TOKEN - GitHub token with repo access
  REPO - repository in owner/name format
  GITHUB_EVENT_NAME - webhook event name (for event-driven operations)
  GITHUB_EVENT_PATH - path to the event payload (for event-driven operations)

Command Line Usage:
  python issue_manager.py update-issues    # Process issue_updates.json
  python issue_manager.py copilot-tickets  # Manage Copilot review tickets
  python issue_manager.py close-duplicates # Close duplicate issues
  python issue_manager.py codeql-alerts    # Generate tickets for CodeQL alerts
  python issue_manager.py event-handler    # Handle GitHub webhook events
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

try:
    import requests
except ImportError:
    print("Error: 'requests' module not found. Installing it now...", file=sys.stderr)
    import subprocess
    try:
        # Use --user flag to install in user directory (avoids externally-managed-environment error)
        subprocess.check_call(["uv", "pip", "install", "requests", "--quiet"])
        import requests
        print("✓ Successfully installed and imported 'requests' module")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install 'requests' module: {e}", file=sys.stderr)
        print("Please install it manually: pip install --user requests", file=sys.stderr)
        sys.exit(1)

# Configuration constants
API_VERSION = "2022-11-28"
COPILOT_USER = "github-copilot[bot]"
COPILOT_LABEL = "copilot-review"
CODEQL_LABEL = "security"
DUPLICATE_CHECK_LABEL = "duplicate-check"

# CodeQL alert configuration
AUTO_CLOSE_ON_FILE_CHANGE = False  # Set to True to automatically close CodeQL issues when their files are modified


class OperationSummary:
    """Track and format operation summaries for workflow reporting."""

    def __init__(self, operation: str):
        """Initialize operation summary tracker.

        Args:
            operation: The operation being performed (e.g., 'update-issues', 'copilot-tickets')
        """
        self.operation = operation
        self.issues_created = []
        self.issues_updated = []
        self.issues_closed = []
        self.issues_deleted = []
        self.comments_added = []
        self.duplicates_closed = []
        self.alerts_processed = []
        self.files_processed = []
        self.files_archived = []
        self.permalinks_updated = []
        self.errors = []
        self.warnings = []

    def add_issue_created(self, issue_number: int, title: str, url: str):
        """Record an issue creation."""
        self.issues_created.append({
            'number': issue_number,
            'title': title,
            'url': url
        })

    def add_issue_updated(self, issue_number: int, title: str, url: str):
        """Record an issue update."""
        self.issues_updated.append({
            'number': issue_number,
            'title': title,
            'url': url
        })

    def add_issue_closed(self, issue_number: int, title: str, url: str):
        """Record an issue closure."""
        self.issues_closed.append({
            'number': issue_number,
            'title': title,
            'url': url
        })

    def add_issue_deleted(self, issue_number: int, title: str):
        """Record an issue deletion."""
        self.issues_deleted.append({
            'number': issue_number,
            'title': title
        })

    def add_comment(self, issue_number: int, comment_url: str):
        """Record a comment addition."""
        self.comments_added.append({
            'issue_number': issue_number,
            'url': comment_url
        })

    def add_duplicate_closed(self, issue_number: int, title: str, url: str):
        """Record a duplicate issue closure."""
        self.duplicates_closed.append({
            'number': issue_number,
            'title': title,
            'url': url
        })

    def add_alert_processed(self, alert_id: str, title: str, issue_number: int = None, issue_url: str = None):
        """Record a CodeQL alert processing."""
        self.alerts_processed.append({
            'alert_id': alert_id,
            'title': title,
            'issue_number': issue_number,
            'issue_url': issue_url
        })

    def add_file_processed(self, file_path: str):
        """Record a file processing."""
        self.files_processed.append(file_path)

    def add_file_archived(self, file_path: str):
        """Record a file archival."""
        self.files_archived.append(file_path)

    def add_permalink_updated(self, file_path: str):
        """Record a permalink update."""
        self.permalinks_updated.append(file_path)

    def add_error(self, message: str):
        """Record an error."""
        self.errors.append(message)

    def add_warning(self, message: str):
        """Record a warning."""
        self.warnings.append(message)

    def get_total_changes(self) -> int:
        """Get total number of changes made."""
        return (len(self.issues_created) + len(self.issues_updated) +
                len(self.issues_closed) + len(self.issues_deleted) +
                len(self.comments_added) + len(self.duplicates_closed) +
                len(self.alerts_processed))

    def print_summary(self):
        """Print a formatted summary of the operation."""
        print(f"\n🎯 {self.operation.upper()} OPERATION SUMMARY")
        print("=" * 50)

        total_changes = self.get_total_changes()
        if total_changes == 0:
            print("ℹ️  No changes made")
        else:
            print(f"✅ Total changes: {total_changes}")

        # Issues created
        if self.issues_created:
            print(f"\n📝 Issues Created ({len(self.issues_created)}):")
            for issue in self.issues_created:
                print(f"  • #{issue['number']}: {issue['title']}")
                print(f"    🔗 {issue['url']}")

        # Issues updated
        if self.issues_updated:
            print(f"\n🔄 Issues Updated ({len(self.issues_updated)}):")
            for issue in self.issues_updated:
                print(f"  • #{issue['number']}: {issue['title']}")
                print(f"    🔗 {issue['url']}")

        # Issues closed
        if self.issues_closed:
            print(f"\n✅ Issues Closed ({len(self.issues_closed)}):")
            for issue in self.issues_closed:
                print(f"  • #{issue['number']}: {issue['title']}")
                print(f"    🔗 {issue['url']}")

        # Issues deleted
        if self.issues_deleted:
            print(f"\n🗑️  Issues Deleted ({len(self.issues_deleted)}):")
            for issue in self.issues_deleted:
                print(f"  • #{issue['number']}: {issue['title']}")

        # Comments added
        if self.comments_added:
            print(f"\n💬 Comments Added ({len(self.comments_added)}):")
            for comment in self.comments_added:
                print(f"  • Issue #{comment['issue_number']}")
                print(f"    🔗 {comment['url']}")

        # Duplicates closed
        if self.duplicates_closed:
            print(f"\n🔁 Duplicates Closed ({len(self.duplicates_closed)}):")
            for issue in self.duplicates_closed:
                print(f"  • #{issue['number']}: {issue['title']}")
                print(f"    🔗 {issue['url']}")

        # Alerts processed
        if self.alerts_processed:
            print(f"\n🔒 CodeQL Alerts Processed ({len(self.alerts_processed)}):")
            for alert in self.alerts_processed:
                print(f"  • Alert {alert['alert_id']}: {alert['title']}")
                if alert['issue_number']:
                    print(f"    📝 Created issue #{alert['issue_number']}")
                    print(f"    🔗 {alert['issue_url']}")

        # Files processed
        if self.files_processed:
            print(f"\n📄 Files Processed ({len(self.files_processed)}):")
            for file_path in self.files_processed:
                print(f"  • {file_path}")

        # Files archived
        if self.files_archived:
            print(f"\n📦 Files Archived ({len(self.files_archived)}):")
            for file_path in self.files_archived:
                print(f"  • {file_path}")

        # Permalinks updated
        if self.permalinks_updated:
            print(f"\n🔗 Permalink Files Updated ({len(self.permalinks_updated)}):")
            for file_path in self.permalinks_updated:
                print(f"  • {file_path}")

        # Warnings
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")

        # Errors
        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")

        print("=" * 50)

    def export_github_summary(self) -> str:
        """Export summary in GitHub Actions format for step summary."""
        lines = [
            f"## 🎯 {self.operation.upper()} Operation Results",
            ""
        ]

        total_changes = self.get_total_changes()
        if total_changes == 0:
            lines.extend([
                "ℹ️ **No changes made**",
                ""
            ])
        else:
            lines.extend([
                f"✅ **Total changes: {total_changes}**",
                ""
            ])

        # Add details for each type of change
        if self.issues_created:
            lines.append(f"### 📝 Issues Created ({len(self.issues_created)})")
            for issue in self.issues_created:
                lines.append(f"- [#{issue['number']}: {issue['title']}]({issue['url']})")
            lines.append("")

        if self.issues_updated:
            lines.append(f"### 🔄 Issues Updated ({len(self.issues_updated)})")
            for issue in self.issues_updated:
                lines.append(f"- [#{issue['number']}: {issue['title']}]({issue['url']})")
            lines.append("")

        if self.issues_closed:
            lines.append(f"### ✅ Issues Closed ({len(self.issues_closed)})")
            for issue in self.issues_closed:
                lines.append(f"- [#{issue['number']}: {issue['title']}]({issue['url']})")
            lines.append("")

        if self.issues_deleted:
            lines.append(f"### 🗑️ Issues Deleted ({len(self.issues_deleted)})")
            for issue in self.issues_deleted:
                lines.append(f"- #{issue['number']}: {issue['title']}")
            lines.append("")

        if self.comments_added:
            lines.append(f"### 💬 Comments Added ({len(self.comments_added)})")
            for comment in self.comments_added:
                lines.append(f"- [Comment on issue #{comment['issue_number']}]({comment['url']})")
            lines.append("")

        if self.duplicates_closed:
            lines.append(f"### 🔁 Duplicates Closed ({len(self.duplicates_closed)})")
            for issue in self.duplicates_closed:
                lines.append(f"- [#{issue['number']}: {issue['title']}]({issue['url']})")
            lines.append("")

        if self.alerts_processed:
            lines.append(f"### 🔒 CodeQL Alerts Processed ({len(self.alerts_processed)})")
            for alert in self.alerts_processed:
                if alert['issue_number']:
                    lines.append(f"- Alert {alert['alert_id']}: [#{alert['issue_number']} {alert['title']}]({alert['issue_url']})")
                else:
                    lines.append(f"- Alert {alert['alert_id']}: {alert['title']}")
            lines.append("")

        if self.files_processed:
            lines.append(f"### 📄 Files Processed ({len(self.files_processed)})")
            for file_path in self.files_processed:
                lines.append(f"- `{file_path}`")
            lines.append("")

        if self.files_archived:
            lines.append(f"### 📦 Files Archived ({len(self.files_archived)})")
            for file_path in self.files_archived:
                lines.append(f"- `{file_path}`")
            lines.append("")

        if self.permalinks_updated:
            lines.append(f"### 🔗 Files with Updated Permalinks ({len(self.permalinks_updated)})")
            for file_path in self.permalinks_updated:
                lines.append(f"- `{file_path}`")
            lines.append("")

        if self.warnings:
            lines.append(f"### ⚠️ Warnings ({len(self.warnings)})")
            for warning in self.warnings:
                lines.append(f"- {warning}")
            lines.append("")

        if self.errors:
            lines.append(f"### ❌ Errors ({len(self.errors)})")
            for error in self.errors:
                lines.append(f"- {error}")
            lines.append("")

        return "\n".join(lines)


class GitHubAPI:
    """GitHub API client with common functionality."""

    def __init__(self, token: str, repo: str):
        """
        Initialize GitHub API client.

        Args:
            token: GitHub personal access token
            repo: Repository in owner/name format
        """
        self.token = token
        self.repo = repo
        self.headers = self._get_headers()

    def _get_headers(self) -> Dict[str, str]:
        """Return HTTP headers for the GitHub API."""
        # Detect token type and set appropriate authorization header
        if self.token.startswith('github_pat_'):
            auth_header = f'token {self.token}'
        else:
            auth_header = f'Bearer {self.token}'

        return {
            "Authorization": auth_header,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": API_VERSION,
        }

    def test_access(self) -> bool:
        """Test API access and permissions."""
        try:
            url = f"https://api.github.com/repos/{self.repo}"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 401:
                print("Error: Invalid or expired GitHub token", file=sys.stderr)
                return False
            elif response.status_code == 404:
                print(f"Error: Repository '{self.repo}' not found or not accessible", file=sys.stderr)
                return False

            response.raise_for_status()
            print("✓ GitHub API access verified")
            return True
        except requests.RequestException as e:
            print(f"Error testing GitHub API access: {e}", file=sys.stderr)
            return False

    def create_issue(self, title: str, body: str, labels: List[str] = None) -> Optional[Dict[str, Any]]:
        """Create a new GitHub issue."""
        url = f"https://api.github.com/repos/{self.repo}/issues"
        data = {"title": title, "body": body}
        if labels:
            data["labels"] = labels

        try:
            response = requests.post(url, headers=self.headers, json=data, timeout=10)
            if response.status_code == 201:
                issue = response.json()
                print(f"Created issue #{issue['number']}: {title}")
                return issue
            else:
                print(f"Failed to create issue: {response.status_code}", file=sys.stderr)
                print(response.text, file=sys.stderr)
                return None
        except requests.RequestException as e:
            print(f"Network error creating issue: {e}", file=sys.stderr)
            return None

    def update_issue(self, issue_number: int, **kwargs) -> bool:
        """Update an existing GitHub issue."""
        url = f"https://api.github.com/repos/{self.repo}/issues/{issue_number}"
        try:
            response = requests.patch(url, headers=self.headers, json=kwargs, timeout=10)
            if response.status_code == 200:
                print(f"Updated issue #{issue_number}")
                return True
            else:
                print(f"Failed to update issue #{issue_number}: {response.status_code}", file=sys.stderr)
                print(response.text, file=sys.stderr)
                return False
        except requests.RequestException as e:
            print(f"Network error updating issue #{issue_number}: {e}", file=sys.stderr)
            return False

    def close_issue(self, issue_number: int, state_reason: str = "completed") -> bool:
        """Close an issue."""
        return self.update_issue(issue_number, state="closed", state_reason=state_reason)

    def add_comment(self, issue_number: int, body: str) -> bool:
        """Add a comment to an issue."""
        url = f"https://api.github.com/repos/{self.repo}/issues/{issue_number}/comments"
        try:
            response = requests.post(url, headers=self.headers, json={"body": body}, timeout=10)
            if response.status_code == 201:
                print(f"Added comment to issue #{issue_number}")
                return True
            else:
                print(f"Failed to add comment to issue #{issue_number}: {response.status_code}", file=sys.stderr)
                print(response.text, file=sys.stderr)
                return False
        except requests.RequestException as e:
            print(f"Network error adding comment to issue #{issue_number}: {e}", file=sys.stderr)
            return False

    def search_issues(self, query: str) -> List[Dict[str, Any]]:
        """Search for issues using GitHub's search API with fallback to list API."""
        url = "https://api.github.com/search/issues"
        params = {"q": f"repo:{self.repo} {query}"}
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            if response.status_code == 403:
                # Search API forbidden, fall back to listing all issues and filtering
                print("⚠️  Search API access denied, falling back to issue listing", file=sys.stderr)
                return self._search_issues_fallback(query)
            response.raise_for_status()
            return response.json().get("items", [])
        except requests.RequestException as e:
            print(f"Network error searching for issues: {e}", file=sys.stderr)
            # Try fallback method
            return self._search_issues_fallback(query)

    def _search_issues_fallback(self, query: str) -> List[Dict[str, Any]]:
        """Fallback method to search issues by listing all and filtering."""
        try:
            # Extract title from query if it contains 'in:title'
            if 'in:title' in query and '"' in query:
                title_start = query.find('"')
                title_end = query.rfind('"')
                if title_start != -1 and title_end != -1 and title_start < title_end:
                    target_title = query[title_start + 1:title_end]

                    # Get all issues and filter by title
                    all_issues = self.get_all_issues(state="all")
                    matching_issues = []
                    for issue in all_issues:
                        if target_title.lower() in issue.get('title', '').lower():
                            matching_issues.append(issue)
                    return matching_issues

            # For other queries, return empty list
            return []
        except Exception as e:
            print(f"Error in fallback search: {e}", file=sys.stderr)
            return []

    def get_all_issues(self, state: str = "open") -> List[Dict[str, Any]]:
        """Fetch all issues with pagination support."""
        all_issues = []
        page = 1
        per_page = 100

        while True:
            url = f"https://api.github.com/repos/{self.repo}/issues"
            params = {"state": state, "per_page": per_page, "page": page}

            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
                response.raise_for_status()

                issues = response.json()
                if not issues:
                    break

                # Filter out pull requests
                issues = [issue for issue in issues if 'pull_request' not in issue]
                all_issues.extend(issues)

                if len(issues) < per_page:
                    break

                page += 1
            except requests.RequestException as e:
                print(f"Error fetching issues page {page}: {e}", file=sys.stderr)
                break

        return all_issues

    def get_issue(self, issue_number: int) -> Optional[Dict[str, Any]]:
        """
        Fetch a single issue by its number.

        Args:
            issue_number: The issue number to fetch

        Returns:
            Issue data as a dictionary, or None if not found or error occurred
        """
        url = f"https://api.github.com/repos/{self.repo}/issues/{issue_number}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                print(f"Issue #{issue_number} not found", file=sys.stderr)
                return None
            else:
                print(f"Failed to fetch issue #{issue_number}: {response.status_code}", file=sys.stderr)
                print(response.text, file=sys.stderr)
                return None
        except requests.RequestException as e:
            print(f"Network error fetching issue #{issue_number}: {e}", file=sys.stderr)
            return None

    def get_codeql_alerts(self, state: str = "open") -> List[Dict[str, Any]]:
        """Fetch CodeQL security alerts."""
        url = f"https://api.github.com/repos/{self.repo}/code-scanning/alerts"
        params = {"state": state, "per_page": 100}

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching CodeQL alerts: {e}", file=sys.stderr)
            return []


class IssueUpdateProcessor:
    """Processes issue updates from issue_updates.json."""

    def __init__(self, github_api: GitHubAPI):
        self.api = github_api
        self.summary = OperationSummary("update-issues")

    def process_updates(self, updates_file: str = "issue_updates.json", updates_directory: str = ".github/issue-updates") -> bool:
        """
        Process issue updates from both legacy JSON file and new distributed directory format
        with GUID tracking and proper file state management.

        Args:
            updates_file: Path to legacy issue updates file
            updates_directory: Path to directory containing individual update files

        Returns:
            True if any updates were processed, False otherwise
        """
        all_updates = []
        processed_files = []

        # Check if legacy file has been processed before
        legacy_already_processed = self._is_legacy_file_processed(updates_file)

        # Load legacy file if it exists and hasn't been processed
        if not legacy_already_processed:
            legacy_updates = self._load_legacy_file(updates_file)
            if legacy_updates:
                all_updates.extend(legacy_updates)
                print(f"📄 Loaded {len(legacy_updates)} NEW updates from legacy file: {updates_file}")
        else:
            print(f"📄 Legacy file {updates_file} already processed, skipping")

        # Load distributed files from directory (only unprocessed files)
        distributed_updates, update_files = self._load_distributed_files(updates_directory)
        if distributed_updates:
            all_updates.extend(distributed_updates)
            processed_files.extend(update_files)
            print(f"📁 Loaded {len(distributed_updates)} updates from {len(update_files)} files in: {updates_directory}")

        if not all_updates:
            print("📝 No new updates to process")
            return True

        print(f"🚀 Processing {len(all_updates)} total updates...")
        success_count = 0

        for i, update in enumerate(all_updates, 1):
            action = update.get('action', 'unknown')
            source = update.get('_source_file', 'unknown')
            guid = update.get('guid', 'no-guid')
            print(f"\n📋 Update {i}/{len(all_updates)}: {action} (from {source}, guid: {guid})")

            result = self._process_single_update(update)
            if result:
                success_count += 1
            else:
                print(f"❌ Failed to process update {i}")

        print(f"\n✅ Successfully processed {success_count}/{len(all_updates)} updates")

        # Move processed distributed files to processed subdirectory
        if processed_files and success_count > 0:
            self._archive_processed_files(processed_files, updates_directory)

        # Mark legacy file as processed if we processed it successfully
        if not legacy_already_processed and success_count > 0:
            # Check if we had legacy updates to process
            legacy_updates = self._load_legacy_file(updates_file)
            if legacy_updates:
                self._mark_legacy_file_processed(updates_file)

        # Add file tracking to summary
        if processed_files:
            for file_path in processed_files:
                self.summary.add_file_processed(file_path)

        # Print operation summary
        self.summary.print_summary()

        # Export summary for GitHub Actions
        github_summary = self.summary.export_github_summary()
        summary_file = os.environ.get('GITHUB_STEP_SUMMARY')
        if summary_file:
            try:
                with open(summary_file, 'a', encoding='utf-8') as f:
                    f.write(github_summary + '\n')
            except Exception as e:
                print(f"⚠️  Failed to write to GitHub step summary: {e}")

        return success_count > 0

    def _update_file_with_permalinks(self, updates_file: str, original_data: Dict[str, Any],
                                   permalinks: List[Dict[str, Any]], format_type: str) -> None:
        """Update the issue updates file with permalinks to processed issues."""
        try:
            # Add processing metadata
            if format_type == "grouped":
                # Add a processed section to track what was done
                if "processed" not in original_data:
                    original_data["processed"] = []

                # Add new processed items
                for permalink_info in permalinks:
                    original_data["processed"].append({
                        "timestamp": permalink_info.get("timestamp"),
                        "action": permalink_info.get("action"),
                        "guid": permalink_info.get("guid"),
                        "issue_number": permalink_info.get("issue_number"),
                        "permalink": permalink_info.get("permalink"),
                        "workflow_run": os.environ.get("GITHUB_RUN_ID", "unknown")
                    })
            else:
                # For flat format, add a simple processed list
                if not isinstance(original_data, dict):
                    original_data = {"updates": original_data, "processed": []}

                if "processed" not in original_data:
                    original_data["processed"] = []

                for permalink_info in permalinks:
                    original_data["processed"].append(permalink_info)

            # Write updated file
            with open(updates_file, 'w', encoding='utf-8') as f:
                json.dump(original_data, f, indent=2)

            print(f"🔗 Updated {updates_file} with {len(permalinks)} permalinks")

        except Exception as e:
            print(f"⚠️  Failed to update {updates_file} with permalinks: {e}", file=sys.stderr)

    def _load_legacy_file(self, updates_file: str) -> List[Dict[str, Any]]:
        """Load updates from the legacy issue_updates.json file."""
        if not os.path.exists(updates_file):
            return []

        try:
            with open(updates_file, 'r', encoding='utf-8') as f:
                updates_data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"❌ Error reading {updates_file}: {e}", file=sys.stderr)
            return []

        updates = []

        # Handle both old flat format and new grouped format
        if isinstance(updates_data, list):
            # Old flat format - items already have action property
            print("⚠️  Using legacy flat format. Consider upgrading to grouped format.")
            updates = updates_data
        else:
            # New grouped format - process in order: create, update, comment, close, delete
            for action_type in ["create", "update", "comment", "close", "delete"]:
                if action_type in updates_data and updates_data[action_type]:
                    for item in updates_data[action_type]:
                        item["action"] = action_type
                        updates.append(item)

        # Add source file information for tracking
        for update in updates:
            update["_source_file"] = updates_file

        return updates

    def _load_distributed_files(self, updates_directory: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Load updates from individual JSON files in the updates directory.

        Returns:
            Tuple of (updates_list, processed_files_list)
        """
        if not os.path.exists(updates_directory):
            return [], []

        updates = []
        processed_files = []

        try:
            # Find all JSON files except README.json
            json_files = []
            for filename in os.listdir(updates_directory):
                if filename.endswith('.json') and filename != 'README.json':
                    file_path = os.path.join(updates_directory, filename)
                    if os.path.isfile(file_path):
                        json_files.append(file_path)

            json_files.sort()  # Process in consistent order

            for file_path in json_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        update_data = json.load(f)

                    # Handle both single objects and arrays of operations
                    file_updates = []

                    if isinstance(update_data, list):
                        # Array format - each item should have an action
                        for i, item in enumerate(update_data):
                            if isinstance(item, dict) and 'action' in item:
                                item["_source_file"] = f"{os.path.basename(file_path)}[{i}]"
                                file_updates.append(item)
                            else:
                                print(f"⚠️  Skipping item {i} in {file_path}: missing 'action' field or not an object")

                    elif isinstance(update_data, dict):
                        # Single object format
                        if 'action' in update_data:
                            update_data["_source_file"] = os.path.basename(file_path)
                            file_updates.append(update_data)
                        else:
                            print(f"⚠️  Skipping {file_path}: missing 'action' field")

                    else:
                        print(f"⚠️  Skipping {file_path}: invalid format (must be object or array)")
                        continue

                    # Add all valid updates from this file
                    if file_updates:
                        updates.extend(file_updates)
                        processed_files.append(file_path)
                    else:
                        print(f"⚠️  No valid updates found in {file_path}")

                except (json.JSONDecodeError, IOError) as e:
                    print(f"⚠️  Error reading {file_path}: {e}", file=sys.stderr)
                    continue

        except OSError as e:
            print(f"⚠️  Error accessing directory {updates_directory}: {e}", file=sys.stderr)
            return [], []

        return updates, processed_files

    def _archive_processed_files(self, processed_files: List[str], updates_directory: str) -> None:
        """Move processed files to a 'processed' subdirectory."""
        if not processed_files:
            return

        processed_dir = os.path.join(updates_directory, "processed")

        try:
            # Create processed directory if it doesn't exist
            os.makedirs(processed_dir, exist_ok=True)

            # Move each processed file
            for file_path in processed_files:
                if os.path.exists(file_path):
                    filename = os.path.basename(file_path)
                    destination = os.path.join(processed_dir, filename)

                    # If destination exists, add timestamp to avoid conflicts
                    if os.path.exists(destination):
                        import time
                        timestamp = int(time.time())
                        name, ext = os.path.splitext(filename)
                        destination = os.path.join(processed_dir, f"{name}_{timestamp}{ext}")

                    os.rename(file_path, destination)
                    print(f"📦 Moved {filename} to processed/")

        except OSError as e:
            print(f"⚠️  Error archiving processed files: {e}", file=sys.stderr)

    def _is_legacy_file_processed(self, updates_file: str) -> bool:
        """Check if legacy file has been processed before."""
        processed_marker = f"{updates_file}.processed"
        return os.path.exists(processed_marker)

    def _mark_legacy_file_processed(self, updates_file: str) -> None:
        """Mark legacy file as processed."""
        processed_marker = f"{updates_file}.processed"
        try:
            with open(processed_marker, 'w', encoding='utf-8') as f:
                f.write(f"Processed on {os.environ.get('GITHUB_RUN_ID', 'unknown')}\n")
            print(f"🏷️  Marked {updates_file} as processed")
        except Exception as e:
            print(f"⚠️  Failed to mark {updates_file} as processed: {e}")

    def _check_guid_in_existing_issues(self, guid: str) -> Optional[Dict[str, Any]]:
        """Check if an issue with the given GUID already exists."""
        if not guid:
            return None

        try:
            # Search in all issues (open and closed) for the GUID
            all_issues = self.api.get_all_issues(state="all")
            guid_marker = f"<!-- guid:{guid} -->"

            for issue in all_issues:
                if guid_marker in issue.get("body", ""):
                    print(f"🔍 Found existing issue #{issue['number']} with GUID: {guid}")
                    return issue

            return None
        except Exception as e:
            print(f"⚠️  Error checking for GUID {guid}: {e}")
            return None

    def _process_single_update(self, update: Dict[str, Any]) -> bool:
        """Process a single update action with GUID tracking."""
        action = update.get("action")
        guid = update.get("guid")

        # Check for duplicate operations using GUID
        if guid and self._is_duplicate_operation(action, guid, update):
            print(f"⏭️  Skipping duplicate operation with GUID: {guid}")
            return True

        try:
            if action == "create":
                return self._create_issue(update)
            elif action == "update":
                return self._update_issue(update)
            elif action == "comment":
                return self._add_comment(update)
            elif action == "close":
                return self._close_issue(update)
            elif action == "delete":
                return self._delete_issue(update)
            else:
                print(f"❌ Unknown action: {action}", file=sys.stderr)
                return False
        except Exception as e:
            print(f"❌ Error processing {action} action: {e}", file=sys.stderr)
            return False

    def _is_duplicate_operation(self, action: str, guid: str, update: Dict[str, Any]) -> bool:
        """Check if an operation with the same GUID was already performed."""
        if action == "comment":
            # For comments, check if GUID exists in issue comments
            issue_number = update.get("number")
            if issue_number:
                return self._comment_guid_exists(issue_number, guid)
        elif action == "create":
            # For creates, check if issue with GUID already exists
            return self._create_guid_exists(guid, update)

        # For update, close, delete - assume no duplicates for now
        return False

    def _comment_guid_exists(self, issue_number: int, guid: str) -> bool:
        """Check if a comment with the given GUID already exists on the issue."""
        try:
            url = f"https://api.github.com/repos/{self.api.repo}/issues/{issue_number}/comments"
            response = requests.get(url, headers=self.api.headers, timeout=10)

            if response.status_code != 200:
                return False

            comments = response.json()

            # Check for GUID in HTML comments
            guid_marker = f"<!-- guid:{guid} -->"
            for comment in comments:
                if guid_marker in comment.get("body", ""):
                    return True

            return False

        except Exception as e:
            print(f"⚠️  Error checking for duplicate comment GUID: {e}")
            return False

    def _create_guid_exists(self, guid: str, update: Dict[str, Any]) -> bool:
        """Check if an issue with the given GUID was already created."""
        title = update.get("title", "")
        try:
            # Search for existing issues with similar title
            existing = self.api.search_issues(f'is:issue in:title "{title}"')

            guid_marker = f"<!-- guid:{guid} -->"
            for issue in existing:
                if guid_marker in issue.get("body", ""):
                    return True

            return False

        except Exception:
            return False

    def _create_issue(self, update: Dict[str, Any]) -> bool:
        """Create a new issue with GUID tracking and duplicate prevention."""
        title = update.get("title", "")
        body = update.get("body", "")
        labels = update.get("labels", [])
        assignees = update.get("assignees", [])
        milestone = update.get("milestone")
        guid = update.get("guid")

        if not title:
            print("❌ Missing title for create operation")
            return False

        # First check for GUID duplicates if GUID is provided
        if guid:
            existing_by_guid = self._check_guid_in_existing_issues(guid)
            if existing_by_guid:
                print(f"⏭️  Issue with GUID '{guid}' already exists (#{existing_by_guid['number']}), skipping")
                return True  # Return True since this isn't an error, just already processed

        # Check if issue with this title already exists
        existing = self.api.search_issues(f'is:issue in:title "{title}"')
        if existing:
            # If we have a GUID, check if any existing issue has this GUID
            if guid:
                for issue in existing:
                    if f"<!-- guid:{guid} -->" in issue.get("body", ""):
                        print(f"⏭️  Issue '{title}' with GUID '{guid}' already exists (#{issue['number']}), skipping")
                        return True
            else:
                print(f"⚠️  Issue '{title}' already exists, skipping (no GUID to verify)")
                return False

        # Add GUID to body for tracking
        if guid:
            body += f"\n\n<!-- guid:{guid} -->"

        try:
            result = self.api.create_issue(title, body, labels)
            if result:
                print(f"✅ Created issue #{result['number']}: {title}")
                self.summary.add_issue_created(result['number'], title, result['html_url'])

                # Add assignees and milestone if specified
                if assignees or milestone:
                    update_data = {}
                    if assignees:
                        update_data["assignees"] = assignees
                    if milestone:
                        update_data["milestone"] = milestone
                    self.api.update_issue(result['number'], **update_data)

                return True
            else:
                print(f"❌ Failed to create issue: {title}")
                self.summary.add_error(f"Failed to create issue: {title}")
                return False

        except Exception as e:
            print(f"❌ Error creating issue: {e}")
            self.summary.add_error(f"Error creating issue: {e}")
            return False

    def _update_issue(self, update: Dict[str, Any]) -> bool:
        """Update an existing issue with GUID tracking."""
        issue_number = update.get("number")
        guid = update.get("guid")

        if not issue_number:
            print("❌ Update action missing issue number", file=sys.stderr)
            return False

        # Build update payload, excluding action, number, guid, and permalink
        update_data = {k: v for k, v in update.items() if k not in ["action", "number", "guid", "permalink"]}

        # Add GUID to body if provided
        if guid and "body" in update_data:
            update_data["body"] += f"\n\n<!-- guid:{guid} -->"

        try:
            success = self.api.update_issue(issue_number, **update_data)
            if success:
                issue_data = self.api.get_issue(issue_number)
                if issue_data:
                    title = issue_data.get('title', f'Issue {issue_number}')
                    url = issue_data.get('html_url', '')
                    print(f"✅ Updated issue #{issue_number}")
                    self.summary.add_issue_updated(issue_number, title, url)
                else:
                    print(f"✅ Updated issue #{issue_number}")
                    self.summary.add_issue_updated(issue_number, f'Issue {issue_number}', '')
                return True
            else:
                print(f"❌ Failed to update issue #{issue_number}")
                self.summary.add_error(f"Failed to update issue #{issue_number}")
                return False
        except Exception as e:
            print(f"❌ Error updating issue #{issue_number}: {e}")
            self.summary.add_error(f"Error updating issue #{issue_number}: {e}")
            return False

    def _add_comment(self, update: Dict[str, Any]) -> bool:
        """Add a comment to an issue with GUID tracking."""
        issue_number = update.get("number")
        body = update.get("body", "")
        guid = update.get("guid")

        if not issue_number:
            print("❌ Comment action missing issue number", file=sys.stderr)
            return False

        if not body:
            print("❌ Comment action missing body", file=sys.stderr)
            return False

        # Add GUID to comment for duplicate detection
        if guid:
            body = f"<!-- guid:{guid} -->\n{body}"

        try:
            result = self.api.add_comment(issue_number, body)
            if result:
                print(f"✅ Added comment to issue #{issue_number}")
                # Extract comment URL if available
                comment_url = result.get('html_url', '') if isinstance(result, dict) else ''
                self.summary.add_comment(issue_number, comment_url)
                return True
            else:
                print(f"❌ Failed to add comment to issue #{issue_number}")
                self.summary.add_error(f"Failed to add comment to issue #{issue_number}")
                return False
        except Exception as e:
            print(f"❌ Error adding comment to issue #{issue_number}: {e}")
            self.summary.add_error(f"Error adding comment to issue #{issue_number}: {e}")
            return False

    def _close_issue(self, update: Dict[str, Any]) -> bool:
        """Close an issue with GUID tracking."""
        issue_number = update.get("number")
        state_reason = update.get("state_reason", "completed")
        guid = update.get("guid")

        if not issue_number:
            print("❌ Close action missing issue number", file=sys.stderr)
            return False

        try:
            success = self.api.close_issue(issue_number, state_reason)
            if success:
                issue_data = self.api.get_issue(issue_number)
                if issue_data:
                    title = issue_data.get('title', f'Issue {issue_number}')
                    url = issue_data.get('html_url', '')
                else:
                    title = f'Issue {issue_number}'
                    url = ''

                print(f"✅ Closed issue #{issue_number} (reason: {state_reason})")
                self.summary.add_issue_closed(issue_number, title, url)

                # Add a tracking comment with GUID if provided
                if guid:
                    tracking_comment = f"<!-- guid:{guid} -->\nIssue closed via automated workflow."
                    self.api.add_comment(issue_number, tracking_comment)

                return True
            else:
                print(f"❌ Failed to close issue #{issue_number}")
                self.summary.add_error(f"Failed to close issue #{issue_number}")
                return False
        except Exception as e:
            print(f"❌ Error closing issue #{issue_number}: {e}")
            self.summary.add_error(f"Error closing issue #{issue_number}: {e}")
            return False

    def update_permalinks(self, updates_file: str = "issue_updates.json", updates_directory: str = ".github/issue-updates") -> bool:
        """
        Update issue files with permalinks to processed issues.

        This method searches for processed issues and updates the individual JSON files
        with permalink fields directly in each action object that has a GUID.

        Args:
            updates_file: Path to legacy issue updates file (not used for permalink updates)
            updates_directory: Path to directory containing individual update files

        Returns:
            True if any permalinks were updated, False otherwise
        """
        print("🔗 Updating permalinks for processed issues...")

        updated_count = 0

        # Process distributed files in processed directory
        if os.path.exists(updates_directory):
            processed_dir = os.path.join(updates_directory, "processed")
            if os.path.exists(processed_dir):
                try:
                    json_files = [f for f in os.listdir(processed_dir)
                                if f.endswith('.json') and f != 'README.json']

                    print(f"� Found {len(json_files)} processed files to update")

                    for filename in json_files:
                        file_path = os.path.join(processed_dir, filename)

                        with open(file_path, 'r', encoding='utf-8') as f:
                            file_data = json.load(f)

                        # Track if this file was modified
                        file_modified = False

                        # Handle both single objects and arrays of operations
                        if isinstance(file_data, list):
                            for action in file_data:
                                if self._update_action_permalink(action):
                                    file_modified = True
                                    updated_count += 1
                        elif isinstance(file_data, dict) and 'action' in file_data:
                            if self._update_action_permalink(file_data):
                                file_modified = True
                                updated_count += 1

                        # Write back the file if it was modified
                        if file_modified:
                            with open(file_path, 'w', encoding='utf-8') as f:
                                json.dump(file_data, f, indent=2)
                            print(f"📝 Updated permalinks in {filename}")

                except Exception as e:
                    print(f"⚠️  Error processing processed files: {e}")

        if updated_count > 0:
            print(f"✅ Updated {updated_count} permalink entries")
            return True
        else:
            print("📝 No permalink updates needed")
            return False

    def _update_action_permalink(self, action: Dict[str, Any]) -> bool:
        """
        Update a single action with permalink information if it has a GUID and no existing permalink.

        Args:
            action: The action object to potentially update

        Returns:
            True if the action was modified, False otherwise
        """
        # Skip if no GUID or already has permalink
        guid = action.get("guid")
        if not guid or "permalink" in action:
            return False

        # Try to find the issue for this action
        issue = self._find_issue_by_guid(guid)
        if issue:
            action["permalink"] = issue["html_url"]
            print(f"🔗 Added permalink for GUID {guid}: {issue['html_url']}")
            return True

        # For actions that reference an issue number, try to construct permalink
        issue_number = action.get("number")
        if issue_number:
            # Construct the permalink directly since we know the issue number
            permalink = f"https://github.com/{self.api.repo}/issues/{issue_number}"
            action["permalink"] = permalink
            print(f"🔗 Added constructed permalink for issue #{issue_number}: {permalink}")
            return True

        print(f"⚠️  Could not find issue for GUID {guid}")
        return False

    def _find_permalinks_for_updates(self, updates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Find permalinks for a list of updates by searching for matching issues.

        Args:
            updates: List of update operations

        Returns:
            List of permalink information dictionaries
        """
        permalinks = []

        for update in updates:
            action = update.get("action", "unknown")
            guid = update.get("guid")
            title = update.get("title", "")

            # Try to find the corresponding issue
            issue = None

            if guid:
                # Search by GUID first
                issue = self._find_issue_by_guid(guid)

            if not issue and title and action == "create":
                # Fall back to title search for create operations
                issues = self.api.search_issues(f'is:issue in:title "{title}"')
                if issues:
                    issue = issues[0]

            if issue:
                permalink_info = {
                    "timestamp": issue.get("created_at"),
                    "action": action,
                    "guid": guid,
                    "issue_number": issue["number"],
                    "permalink": issue["html_url"],
                    "title": issue["title"]
                }
                permalinks.append(permalink_info)
                print(f"🔍 Found issue #{issue['number']} for {action} operation")

        return permalinks

    def _find_permalinks_for_file_updates(self, file_data: Any) -> List[Dict[str, Any]]:
        """
        Find permalinks for updates in a single file.

        Args:
            file_data: The JSON data from a processed update file

        Returns:
            List of permalink information dictionaries
        """
        updates = []

        if isinstance(file_data, list):
            updates = file_data
        elif isinstance(file_data, dict) and "action" in file_data:
            updates = [file_data]

        return self._find_permalinks_for_updates(updates)

    def _find_issue_by_guid(self, guid: str) -> Optional[Dict[str, Any]]:
        """
        Find an issue by its GUID marker in the body.

        Args:
            guid: The GUID to search for

        Returns:
            Issue data if found, None otherwise
        """
        if not guid:
            return None

        try:
            # Search all issues for the GUID marker
            all_issues = self.api.get_all_issues(state="all")
            guid_marker = f"<!-- guid:{guid} -->"

            for issue in all_issues:
                if guid_marker in issue.get("body", ""):
                    return issue

            return None
        except Exception as e:
            print(f"⚠️  Error searching for GUID {guid}: {e}")
            return None

    def _has_permalink_metadata(self, file_data: Any) -> bool:
        """
        Check if a file already has permalink metadata.

        Args:
            file_data: The JSON data from a file

        Returns:
            True if permalink metadata is present
        """
        if isinstance(file_data, dict):
            return "permalink" in file_data or "processed_at" in file_data
        return False

    def _add_permalink_metadata(self, file_path: str, file_data: Any, permalinks: List[Dict[str, Any]]) -> None:
        """
        Add permalink metadata to a processed file.

        Args:
            file_path: Path to the file to update
            file_data: Current file data
            permalinks: List of permalink information
        """
        try:
            # Add metadata to the file
            if isinstance(file_data, dict):
                file_data["_permalink_metadata"] = {
                    "processed_at": os.environ.get("GITHUB_RUN_ID", "manual"),
                    "permalinks": permalinks
                }
            elif isinstance(file_data, list) and len(file_data) == 1:
                # Single item array, convert to object with metadata
                file_data = {
                    "update": file_data[0],
                    "_permalink_metadata": {
                        "processed_at": os.environ.get("GITHUB_RUN_ID", "manual"),
                        "permalinks": permalinks
                    }
                }

            # Write updated file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(file_data, f, indent=2)

            print(f"🔗 Added permalink metadata to {os.path.basename(file_path)}")

        except Exception as e:
            print(f"⚠️  Failed to add permalink metadata to {file_path}: {e}")

    def _delete_issue(self, update: Dict[str, Any]) -> bool:
        """Delete an issue (requires GraphQL API)."""
        issue_number = update.get("number")

        if not issue_number:
            print("Delete action missing issue number", file=sys.stderr)
            self.summary.add_error("Delete action missing issue number")
            return False

        # Get issue data before deletion for summary
        try:
            issue_data = self.api.get_issue(issue_number)
            title = issue_data.get('title', f'Issue {issue_number}') if issue_data else f'Issue {issue_number}'
        except Exception:
            title = f'Issue {issue_number}'

        # Get node_id for GraphQL deletion
        try:
            url = f"https://api.github.com/repos/{self.api.repo}/issues/{issue_number}"
            response = requests.get(url, headers=self.api.headers, timeout=10)
            response.raise_for_status()
            node_id = response.json()["node_id"]

            # Use GraphQL to delete
            mutation = {
                "query": f'mutation{{deleteIssue(input:{{issueId:"{node_id}"}}){{clientMutationId}}}}'
            }

            response = requests.post(
                "https://api.github.com/graphql",
                headers=self.api.headers,
                json=mutation,
                timeout=10
            )

            if response.status_code == 200:
                print(f"Deleted issue #{issue_number}")
                self.summary.add_issue_deleted(issue_number, title)
                return True
            else:
                error_msg = f"Failed to delete issue #{issue_number}: {response.status_code}"
                print(error_msg, file=sys.stderr)
                self.summary.add_error(error_msg)
                return False

        except requests.RequestException as e:
            error_msg = f"Error deleting issue #{issue_number}: {e}"
            print(error_msg, file=sys.stderr)
            self.summary.add_error(error_msg)
            return False


class CopilotTicketManager:
    """Manages tickets for Copilot review comments."""

    def __init__(self, github_api: GitHubAPI):
        self.api = github_api
        self.summary = OperationSummary("copilot-tickets")

    def handle_event(self, event_name: str, event_data: Dict[str, Any]) -> None:
        """Handle GitHub webhook events related to Copilot comments."""
        action = event_data.get("action")
        print(f"Processing {event_name} event with action: {action}")

        try:
            if event_name == "pull_request_review_comment":
                self._handle_review_comment(action, event_data)
            elif event_name == "pull_request_review":
                self._handle_review(action, event_data)
            elif event_name == "pull_request" and action == "closed":
                self._handle_pr_closed(event_data)
            elif event_name == "push":
                self._handle_push(event_data)
            else:
                print(f"Unhandled event: {event_name} with action: {action}")
        except Exception as e:
            print(f"Error handling {event_name} event: {e}", file=sys.stderr)
            self.summary.add_error(f"Error handling {event_name} event: {e}")
        finally:
            # Always print summary at the end
            self._print_summary()

    def _print_summary(self):
        """Print the operation summary."""
        self.summary.print_summary()

        # Export summary for GitHub Actions
        github_summary = self.summary.export_github_summary()
        summary_file = os.environ.get('GITHUB_STEP_SUMMARY')
        if summary_file:
            try:
                with open(summary_file, 'a', encoding='utf-8') as f:
                    f.write(github_summary + '\n')
            except Exception as e:
                print(f"⚠️  Failed to write to GitHub step summary: {e}")

    def _handle_review_comment(self, action: str, event_data: Dict[str, Any]) -> None:
        """Handle review comment events."""
        comment = event_data.get("comment", {})

        if comment.get("user", {}).get("login") != COPILOT_USER:
            print("Not a Copilot comment; skipping")
            return

        if action == "created":
            self._create_or_update_ticket(comment)
        elif action == "deleted":
            self._handle_comment_deleted(comment)

    def _handle_review(self, action: str, event_data: Dict[str, Any]) -> None:
        """Handle review events (minimal action currently)."""
        review = event_data.get("review", {})
        if review.get("user", {}).get("login") == COPILOT_USER:
            print(f"Copilot review {action}")

    def _handle_pr_closed(self, event_data: Dict[str, Any]) -> None:
        """Close all Copilot tickets for a merged PR."""
        pr = event_data.get("pull_request", {})
        if not pr.get("merged", False):
            print("PR not merged, skipping")
            return

        pr_number = pr["number"]
        print(f"Processing merged PR #{pr_number}")

        # Search for all open copilot issues mentioning this PR
        issues = self.api.search_issues(f"label:{COPILOT_LABEL} state:open {pr_number}")
        print(f"Found {len(issues)} open Copilot issues for PR #{pr_number}")

        closed_count = 0
        for issue in issues:
            if self.api.close_issue(issue["number"]):
                closed_count += 1

        if closed_count > 0:
            print(f"Closed {closed_count} Copilot issues for merged PR #{pr_number}")

    def _handle_push(self, event_data: Dict[str, Any]) -> None:
        """Handle pushes to main branch - comprehensive issue analysis."""
        ref = event_data.get("ref", "")
        if not ref.endswith("/main") and not ref.endswith("/master"):
            print(f"Push to {ref} - not main/master, skipping")
            return

        print(f"Processing push to {ref}")

        # Get all open Copilot issues and analyze them
        issues = self.api.search_issues(f"label:{COPILOT_LABEL} state:open")
        print(f"Found {len(issues)} open Copilot issues")

        # Here you could implement file change analysis and stale issue cleanup
        # For now, just log the activity
        print("Push analysis complete")

    def _create_or_update_ticket(self, comment: Dict[str, Any]) -> None:
        """Create or update a ticket for a Copilot comment."""
        comment_body = comment.get("body", "").strip()
        key = comment_body.split("\n", 1)[0]  # First line as key

        existing = self.api.search_issues(f"label:{COPILOT_LABEL} state:open {key}")

        line_info = {
            "id": comment["id"],
            "path": comment.get("path", ""),
            "line": comment.get("line", 0),
            "url": comment.get("html_url", ""),
        }

        if existing:
            # Update existing issue
            issue = existing[0]
            print(f"Updating existing Copilot issue #{issue['number']}")
            # Implementation would parse existing body and update it
            self.summary.add_issue_updated(issue['number'], issue['title'], issue['html_url'])
        else:
            # Create new issue
            title = f"Copilot Review: {key[:50]}..."
            body = self._build_ticket_body(comment, [line_info])
            result = self.api.create_issue(title, body, [COPILOT_LABEL])
            if result:
                self.summary.add_issue_created(result['number'], title, result['html_url'])
            else:
                self.summary.add_error(f"Failed to create Copilot ticket: {title}")

    def _handle_comment_deleted(self, comment: Dict[str, Any]) -> None:
        """Handle deletion of a Copilot comment."""
        comment_id = comment["id"]
        search_key = f"id:{comment_id}"

        issues = self.api.search_issues(f"label:{COPILOT_LABEL} state:open {search_key}")
        if not issues:
            print(f"No issue found for deleted comment {comment_id}")
            return

        issue = issues[0]
        # Implementation would update or close the issue based on remaining comments
        print(f"Handling deletion of comment {comment_id} from issue #{issue['number']}")

    def _build_ticket_body(self, comment: Dict[str, Any], lines: List[Dict[str, Any]]) -> str:
        """Build the issue body from comment text and metadata."""
        snippet = comment["body"]
        bullet_lines = [
            f"- id:{item['id']} [{item['path']}#L{item['line']}]({item['url']})"
            for item in lines
        ]
        data = {"comments": lines}
        json_block = json.dumps(data, separators=(",", ":"))

        return (
            f"Generated from [Copilot review comment]({comment['url']}).\n\n"
            f"```text\n{snippet}\n```\n\n"
            + "\n".join(bullet_lines)
            + f"\n\n<!-- copilot-data:{json_block} -->"
        )


class DuplicateIssueManager:
    """Manages duplicate issue detection and closure."""

    def __init__(self, github_api: GitHubAPI):
        self.api = github_api
        self.summary = OperationSummary("close-duplicates")

    def close_duplicates(self, dry_run: bool = False) -> int:
        """
        Close duplicate issues by title.

        Args:
            dry_run: If True, only print what would be done

        Returns:
            Number of duplicate issues that were (or would be) closed
        """
        print("Fetching open issues...")
        issues = self.api.get_all_issues(state="open")
        print(f"Found {len(issues)} open issues")

        # Group issues by title
        title_groups = self._group_by_title(issues)

        closed_count = 0
        duplicates_found = False

        for title, issue_list in title_groups.items():
            if len(issue_list) > 1:
                duplicates_found = True
                print(f"Found {len(issue_list)} issues with title: '{title}'")

                if dry_run:
                    self._print_duplicate_plan(issue_list)
                    closed_count += len(issue_list) - 1
                else:
                    closed_count += self._close_duplicate_group(issue_list)

        if not duplicates_found:
            print("No duplicate issues found")

        # Print operation summary
        self.summary.print_summary()

        # Export summary for GitHub Actions
        github_summary = self.summary.export_github_summary()
        summary_file = os.environ.get('GITHUB_STEP_SUMMARY')
        if summary_file:
            try:
                with open(summary_file, 'a', encoding='utf-8') as f:
                    f.write(github_summary + '\n')
            except Exception as e:
                print(f"⚠️  Failed to write to GitHub step summary: {e}")

        return closed_count

    def _group_by_title(self, issues: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group issues by their title."""
        title_groups = defaultdict(list)

        for issue in issues:
            title = issue['title'].strip()
            title_groups[title].append({
                'number': issue['number'],
                'title': title,
                'url': issue['html_url']
            })

        return title_groups

    def _close_duplicate_group(self, issue_list: List[Dict[str, Any]]) -> int:
        """Close duplicate issues, keeping the lowest numbered one."""
        issue_list.sort(key=lambda x: x['number'])
        canonical = issue_list[0]
        duplicates = issue_list[1:]

        print(f"Keeping issue #{canonical['number']} as canonical")

        closed_count = 0
        for duplicate in duplicates:
            print(f"Closing issue #{duplicate['number']} as duplicate of #{canonical['number']}")

            if self.api.close_issue(duplicate['number']):
                # Add duplicate comment
                comment_body = f"Duplicate of #{canonical['number']}"
                self.api.add_comment(duplicate['number'], comment_body)
                # Record in summary
                self.summary.add_duplicate_closed(duplicate['number'], duplicate['title'], duplicate['url'])
                closed_count += 1

        return closed_count

    def _print_duplicate_plan(self, issue_list: List[Dict[str, Any]]) -> None:
        """Print what would be done in dry-run mode."""
        issue_list.sort(key=lambda x: x['number'])
        canonical = issue_list[0]
        duplicates = issue_list[1:]

        print(f"  📌 Would keep issue #{canonical['number']} as canonical")
        for duplicate in duplicates:
            print(f"  🚫 Would close issue #{duplicate['number']} as duplicate")


class CodeQLAlertManager:
    """Manages tickets for CodeQL security alerts."""

    def __init__(self, github_api: GitHubAPI):
        self.api = github_api
        self.summary = OperationSummary("codeql-alerts")

    def generate_tickets(self) -> int:
        """
        Generate tickets for CodeQL security alerts that don't have associated issues.

        Returns:
            Number of tickets created
        """
        print("Fetching CodeQL alerts...")
        alerts = self.api.get_codeql_alerts(state="open")
        print(f"Found {len(alerts)} open CodeQL alerts")

        if not alerts:
            print("No CodeQL alerts found")
            return 0

        created_count = 0

        for alert in alerts:
            if self._should_create_ticket(alert):
                if self._create_alert_ticket(alert):
                    created_count += 1

        print(f"Created {created_count} tickets for CodeQL alerts")

        # Print operation summary
        self.summary.print_summary()

        # Export summary for GitHub Actions
        github_summary = self.summary.export_github_summary()
        summary_file = os.environ.get('GITHUB_STEP_SUMMARY')
        if summary_file:
            try:
                with open(summary_file, 'a', encoding='utf-8') as f:
                    f.write(github_summary + '\n')
            except Exception as e:
                print(f"⚠️  Failed to write to GitHub step summary: {e}")

        return created_count

    def _should_create_ticket(self, alert: Dict[str, Any]) -> bool:
        """Check if a ticket should be created for this alert."""
        alert_number = alert.get("number")
        rule_id = alert.get("rule", {}).get("id", "")

        # Search for existing issues for this alert
        search_query = f"label:{CODEQL_LABEL} state:open \"CodeQL Alert #{alert_number}\" OR \"Rule: {rule_id}\""
        existing = self.api.search_issues(search_query)

        if existing:
            print(f"Ticket already exists for CodeQL alert #{alert_number}")
            return False

        return True

    def _create_alert_ticket(self, alert: Dict[str, Any]) -> bool:
        """Create a ticket for a CodeQL alert."""
        rule = alert.get("rule", {})
        rule_description = rule.get("description", "No description available")
        alert_number = alert.get("number")

        # Build title and body
        title = f"CodeQL Alert #{alert_number}: {rule_description}"
        body = self._build_alert_body(alert)

        # Create issue with security label
        result = self.api.create_issue(title, body, [CODEQL_LABEL])
        if result:
            # Record in summary
            self.summary.add_alert_processed(
                str(alert_number),
                title,
                result.get('number'),
                result.get('html_url')
            )
            return True
        else:
            self.summary.add_error(f"Failed to create ticket for CodeQL alert #{alert_number}")
            return False

    def _build_alert_body(self, alert: Dict[str, Any]) -> str:
        """Build the issue body for a CodeQL alert."""
        alert_number = alert.get("number")
        rule = alert.get("rule", {})
        rule_id = rule.get("id", "unknown")
        rule_description = rule.get("description", "No description available")
        severity = rule.get("severity", "unknown")
        security_severity_level = rule.get("security_severity_level", "unknown")

        # Get location information
        most_recent_instance = alert.get("most_recent_instance", {})
        location = most_recent_instance.get("location", {})
        path = location.get("path", "unknown")
        start_line = location.get("start_line", 0)
        end_line = location.get("end_line", 0)

        # Get message
        message = most_recent_instance.get("message", {}).get("text", "No message available")

        # Build the body
        body = f"""## CodeQL Security Alert #{alert_number}

**Rule:** {rule_id}
**Description:** {rule_description}
**Severity:** {severity}
**Security Severity:** {security_severity_level}

### Location
**File:** `{path}`
**Lines:** {start_line}-{end_line}

### Details
{message}

### Alert Information
- Alert URL: {alert.get('html_url', 'N/A')}
- State: {alert.get('state', 'unknown')}
- Created: {alert.get('created_at', 'unknown')}

---
*This issue was automatically generated from CodeQL security alert #{alert_number}*

<!-- codeql-alert:{alert_number} -->"""

        return body


def load_event() -> Dict[str, Any]:
    """Load the GitHub event payload."""
    path = os.environ.get("GITHUB_EVENT_PATH")
    if not path:
        raise ValueError("GITHUB_EVENT_PATH not set")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Unified GitHub issue management script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python issue_manager.py update-issues
  python issue_manager.py copilot-tickets
  python issue_manager.py close-duplicates --dry-run
  python issue_manager.py codeql-alerts
  python issue_manager.py update-permalinks
  python issue_manager.py event-handler
        """
    )

    parser.add_argument(
        "command",
        choices=["update-issues", "copilot-tickets", "close-duplicates", "codeql-alerts", "update-permalinks", "event-handler"],
        help="Command to execute"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes (for close-duplicates)"
    )

    args = parser.parse_args()

    # Get environment variables
    token = os.environ.get("GH_TOKEN")
    repo = os.environ.get("REPO")

    if not token or not repo:
        print("GH_TOKEN and REPO environment variables must be set", file=sys.stderr)
        sys.exit(1)

    # Initialize API client
    github_api = GitHubAPI(token, repo)

    # Test API access
    if not github_api.test_access():
        sys.exit(1)

    # Execute the requested command
    try:
        if args.command == "update-issues":
            processor = IssueUpdateProcessor(github_api)

            # Get file and directory paths from environment or use defaults
            updates_file = os.environ.get("ISSUE_UPDATES_FILE", "issue_updates.json")
            updates_directory = os.environ.get("ISSUE_UPDATES_DIRECTORY", ".github/issue-updates")

            processed = processor.process_updates(updates_file, updates_directory)
            if processed:
                print("Issue updates processed successfully")
            else:
                print("No issue updates processed")

        elif args.command == "copilot-tickets":
            manager = CopilotTicketManager(github_api)
            event_name = os.environ.get("GITHUB_EVENT_NAME")
            if event_name:
                event_data = load_event()
                manager.handle_event(event_name, event_data)
            else:
                print("No GitHub event to process")
                # Still print summary even if no event
                manager._print_summary()

        elif args.command == "close-duplicates":
            manager = DuplicateIssueManager(github_api)
            manager.close_duplicates(dry_run=args.dry_run)
            # Summary is automatically printed by the manager

        elif args.command == "codeql-alerts":
            manager = CodeQLAlertManager(github_api)
            manager.generate_tickets()
            # Summary is automatically printed by the manager

        elif args.command == "update-permalinks":
            processor = IssueUpdateProcessor(github_api)
            # Reset the summary operation type for this specific operation
            processor.summary = OperationSummary("update-permalinks")

            # Get file and directory paths from environment or use defaults
            updates_file = os.environ.get("ISSUE_UPDATES_FILE", "issue_updates.json")
            updates_directory = os.environ.get("ISSUE_UPDATES_DIRECTORY", ".github/issue-updates")

            updated = processor.update_permalinks(updates_file, updates_directory)
            if updated:
                processor.summary.add_permalink_updated(updates_file)
                print("Permalinks updated successfully")
            else:
                print("No permalink updates needed")

            # Print summary
            processor.summary.print_summary()

            # Export summary for GitHub Actions
            github_summary = processor.summary.export_github_summary()
            summary_file = os.environ.get('GITHUB_STEP_SUMMARY')
            if summary_file:
                try:
                    with open(summary_file, 'a', encoding='utf-8') as f:
                        f.write(github_summary + '\n')
                except Exception as e:
                    print(f"⚠️  Failed to write to GitHub step summary: {e}")

        elif args.command == "event-handler":
            event_name = os.environ.get("GITHUB_EVENT_NAME")
            if not event_name:
                print("GITHUB_EVENT_NAME not set for event handling", file=sys.stderr)
                sys.exit(1)

            event_data = load_event()
            print(f"Processing {event_name} event for {repo}")

            # Route to appropriate handler based on event type
            if event_name in ["pull_request_review_comment", "pull_request_review", "pull_request", "push"]:
                manager = CopilotTicketManager(github_api)
                manager.handle_event(event_name, event_data)
            else:
                print(f"Unhandled event type: {event_name}")

    except Exception as e:
        print(f"Error executing {args.command}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
