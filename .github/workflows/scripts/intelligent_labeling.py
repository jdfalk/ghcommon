#!/usr/bin/env python3
"""Apply intelligent labels to GitHub PRs."""

from __future__ import annotations

import os
from typing import Iterable, List

import requests


def analyze_pr_content(title: str, body: str | None, changed_files: Iterable[str]) -> List[str]:
    labels: list[str] = []
    text = (title + " " + (body or "")).lower()

    if any(word in text for word in ["fix", "bug", "error", "issue", "problem"]):
        labels.append("bug")
    if any(word in text for word in ["feature", "add", "new", "implement"]):
        labels.append("enhancement")
    if any(word in text for word in ["doc", "readme", "documentation"]):
        labels.append("documentation")
    if any(word in text for word in ["test", "testing", "spec"]):
        labels.append("tests")

    for file in changed_files:
        file_lower = file.lower()
        if file_lower.endswith((".md", ".rst")):
            labels.append("documentation")
        elif file_lower.endswith(".go"):
            labels.append("go")
        elif file_lower.endswith((".js", ".ts", ".jsx", ".tsx")):
            labels.append("frontend")
        elif file_lower.endswith(".py"):
            labels.append("python")
        elif file_lower.endswith(("dockerfile", ".docker")):
            labels.append("docker")
        elif "test" in file_lower:
            labels.append("tests")

    return sorted(set(labels))


def main() -> None:
    github_token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    pr_number = os.environ.get("PR_NUMBER")

    if not all([github_token, repo, pr_number]):
        print("Missing required environment variables; skipping intelligent labeling")
        return

    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    pr_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    pr_response = requests.get(pr_url, headers=headers, timeout=30)
    if pr_response.status_code != 200:
        print(f"Failed to get PR details: {pr_response.status_code}")
        return

    pr_data = pr_response.json()

    files_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
    files_response = requests.get(files_url, headers=headers, timeout=30)
    if files_response.status_code != 200:
        print(f"Failed to get changed files: {files_response.status_code}")
        return

    changed_files = [item["filename"] for item in files_response.json()]
    suggested_labels = analyze_pr_content(pr_data["title"], pr_data.get("body"), changed_files)

    print(f"Suggested labels for PR #{pr_number}: {suggested_labels}")
    if not suggested_labels:
        return

    labels_url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/labels"
    labels_response = requests.post(
        labels_url,
        headers=headers,
        json={"labels": suggested_labels},
        timeout=30,
    )

    if labels_response.status_code == 200:
        print(f"✅ Successfully applied labels: {suggested_labels}")
    else:
        print(f"❌ Failed to apply labels: {labels_response.status_code}")


if __name__ == "__main__":
    main()
