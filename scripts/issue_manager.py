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
from typing import Any, Dict, List, Optional

import requests

# Configuration constants
API_VERSION = "2022-11-28"
COPILOT_USER = "github-copilot[bot]"
COPILOT_LABEL = "copilot-review"
CODEQL_LABEL = "security"
DUPLICATE_CHECK_LABEL = "duplicate-check"

# CodeQL alert configuration
AUTO_CLOSE_ON_FILE_CHANGE = False  # Set to True to automatically close CodeQL issues when their files are modified


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
        """Search for issues using GitHub's search API."""
        url = "https://api.github.com/search/issues"
        params = {"q": f"repo:{self.repo} {query}"}
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json().get("items", [])
        except requests.RequestException as e:
            print(f"Network error searching for issues: {e}", file=sys.stderr)
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

    def process_updates(self, updates_file: str = "issue_updates.json") -> bool:
        """
        Process issue updates from JSON file supporting both legacy flat format
        and new grouped format with GUID tracking. Updates the file with permalinks
        to processed issues for tracking purposes.

        Returns:
            True if any updates were processed, False otherwise
        """
        if not os.path.exists(updates_file):
            print(f"❌ No {updates_file} found")
            return False

        try:
            with open(updates_file, 'r', encoding='utf-8') as f:
                updates_data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"❌ Error reading {updates_file}: {e}", file=sys.stderr)
            return False

        # Handle both old flat format and new grouped format
        if isinstance(updates_data, list):
            # Old flat format - convert to new format
            print("⚠️  Using legacy flat format. Consider upgrading to grouped format.")
            updates = updates_data
            original_format = "flat"
        else:
            # New grouped format - process in order: create, update, comment, close, delete
            updates = []
            for action_type in ["create", "update", "comment", "close", "delete"]:
                if action_type in updates_data and updates_data[action_type]:
                    for item in updates_data[action_type]:
                        item["action"] = action_type
                        updates.append(item)
            original_format = "grouped"

        if not updates:
            print("📝 No updates to process")
            return True

        print(f"🚀 Processing {len(updates)} updates...")
        success_count = 0
        processed_permalinks = []

        for i, update in enumerate(updates, 1):
            action = update.get('action', 'unknown')
            print(f"\n📋 Update {i}/{len(updates)}: {action}")

            result = self._process_single_update(update)
            if result:
                success_count += 1
                # Store permalink information for successful operations
                if isinstance(result, dict) and 'permalink' in result:
                    processed_permalinks.append(result)
            else:
                print(f"❌ Failed to process update {i}")

        print(f"\n✅ Successfully processed {success_count}/{len(updates)} updates")
        
        # Update the file with permalinks for processed issues
        if processed_permalinks:
            self._update_file_with_permalinks(updates_file, updates_data, processed_permalinks, original_format)
            
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
        """Create a new issue with GUID tracking."""
        title = update.get("title", "")
        body = update.get("body", "")
        labels = update.get("labels", [])
        assignees = update.get("assignees", [])
        milestone = update.get("milestone")
        guid = update.get("guid")

        if not title:
            print("❌ Missing title for create operation")
            return False

        # Check if issue with this title already exists (without GUID check)
        existing = self.api.search_issues(f'is:issue in:title "{title}"')
        if existing and not guid:
            print(f"⚠️  Issue '{title}' already exists, skipping")
            return False

        # Add GUID to body for tracking
        if guid:
            body += f"\n\n<!-- guid:{guid} -->"

        try:
            result = self.api.create_issue(title, body, labels)
            if result:
                print(f"✅ Created issue #{result['number']}: {title}")

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
                return False

        except Exception as e:
            print(f"❌ Error creating issue: {e}")
            return False

    def _update_issue(self, update: Dict[str, Any]) -> bool:
        """Update an existing issue with GUID tracking."""
        issue_number = update.get("number")
        guid = update.get("guid")

        if not issue_number:
            print("❌ Update action missing issue number", file=sys.stderr)
            return False

        # Build update payload, excluding action, number, and guid
        update_data = {k: v for k, v in update.items() if k not in ["action", "number", "guid"]}

        # Add GUID to body if provided
        if guid and "body" in update_data:
            update_data["body"] += f"\n\n<!-- guid:{guid} -->"

        try:
            success = self.api.update_issue(issue_number, **update_data)
            if success:
                print(f"✅ Updated issue #{issue_number}")
                return True
            else:
                print(f"❌ Failed to update issue #{issue_number}")
                return False
        except Exception as e:
            print(f"❌ Error updating issue #{issue_number}: {e}")
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
            success = self.api.add_comment(issue_number, body)
            if success:
                print(f"✅ Added comment to issue #{issue_number}")
                return True
            else:
                print(f"❌ Failed to add comment to issue #{issue_number}")
                return False
        except Exception as e:
            print(f"❌ Error adding comment to issue #{issue_number}: {e}")
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
                print(f"✅ Closed issue #{issue_number} (reason: {state_reason})")

                # Add a tracking comment with GUID if provided
                if guid:
                    tracking_comment = f"<!-- guid:{guid} -->\nIssue closed via automated workflow."
                    self.api.add_comment(issue_number, tracking_comment)

                return True
            else:
                print(f"❌ Failed to close issue #{issue_number}")
                return False
        except Exception as e:
            print(f"❌ Error closing issue #{issue_number}: {e}")
            return False

    def _delete_issue(self, update: Dict[str, Any]) -> bool:
        """Delete an issue (requires GraphQL API)."""
        issue_number = update.get("number")

        if not issue_number:
            print("Delete action missing issue number", file=sys.stderr)
            return False

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
                return True
            else:
                print(f"Failed to delete issue #{issue_number}: {response.status_code}", file=sys.stderr)
                return False

        except requests.RequestException as e:
            print(f"Error deleting issue #{issue_number}: {e}", file=sys.stderr)
            return False


class CopilotTicketManager:
    """Manages tickets for Copilot review comments."""

    def __init__(self, github_api: GitHubAPI):
        self.api = github_api

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
        else:
            # Create new issue
            title = f"Copilot Review: {key[:50]}..."
            body = self._build_ticket_body(comment, [line_info])
            self.api.create_issue(title, body, [COPILOT_LABEL])

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

        # Build title and body
        title = f"CodeQL Alert #{alert.get('number')}: {rule_description}"
        body = self._build_alert_body(alert)

        # Create issue with security label
        result = self.api.create_issue(title, body, [CODEQL_LABEL])
        return result is not None

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
  python issue_manager.py event-handler
        """
    )

    parser.add_argument(
        "command",
        choices=["update-issues", "copilot-tickets", "close-duplicates", "codeql-alerts", "event-handler"],
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
            processed = processor.process_updates()
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

        elif args.command == "close-duplicates":
            manager = DuplicateIssueManager(github_api)
            closed_count = manager.close_duplicates(dry_run=args.dry_run)
            if args.dry_run:
                print(f"Would close {closed_count} duplicate issues")
            else:
                print(f"Closed {closed_count} duplicate issues")

        elif args.command == "codeql-alerts":
            manager = CodeQLAlertManager(github_api)
            created_count = manager.generate_tickets()
            print(f"Created {created_count} tickets for CodeQL alerts")

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
