<!-- file: docs/cross-registry-todos/task-14/t14-part3.md -->
<!-- version: 1.0.0 -->
<!-- guid: t14-documentation-automation-part3-t4u5v6w7-x8y9 -->
<!-- last-edited: 2026-01-19 -->

# Task 14 Part 3: Documentation Sites and Changelog Automation

## Documentation Site Generators

### mdBook Configuration

```toml
# file: book.toml
# version: 1.0.0
# guid: mdbook-configuration

[book]
title = "Ubuntu Autoinstall Agent Documentation"
authors = ["John Falk"]
description = "Comprehensive guide for Ubuntu Autoinstall Agent"
language = "en"
multilingual = false
src = "docs/src"
build-dir = "docs/book"

[output.html]
default-theme = "rust"
preferred-dark-theme = "navy"
curly-quotes = true
mathjax-support = true
copy-fonts = true
no-section-label = false
git-repository-url = "https://github.com/jdfalk/ubuntu-autoinstall-agent"
git-repository-icon = "fa-github"
edit-url-template = "https://github.com/jdfalk/ubuntu-autoinstall-agent/edit/main/docs/src/{path}"
site-url = "/ubuntu-autoinstall-agent/"
cname = "docs.example.com"

[output.html.print]
enable = true

[output.html.fold]
enable = true
level = 1

[output.html.search]
enable = true
limit-results = 30
teaser-word-count = 30
use-boolean-and = true
boost-title = 2
boost-hierarchy = 1
boost-paragraph = 1
expand = true
heading-split-level = 3

[output.html.playground]
editable = true
copyable = true
copy-js = true
line-numbers = true
runnable = true

[preprocessor.index]

[preprocessor.links]

[preprocessor.mermaid]
command = "mdbook-mermaid"

[preprocessor.katex]
command = "mdbook-katex"

[build]
create-missing = true
```

### mdBook Structure

```markdown
<!-- file: docs/src/SUMMARY.md -->
<!-- version: 1.0.0 -->
<!-- guid: mdbook-summary -->
<!-- last-edited: 2026-01-19 -->

# Summary

[Introduction](./introduction.md)

# Getting Started

- [Installation](./getting-started/installation.md)
- [Quick Start](./getting-started/quick-start.md)
- [Configuration](./getting-started/configuration.md)

# User Guide

- [Creating Installations](./user-guide/creating-installations.md)
  - [Basic Setup](./user-guide/basic-setup.md)
  - [Advanced Configuration](./user-guide/advanced-configuration.md)
  - [Cloud-init Integration](./user-guide/cloud-init.md)
- [Managing Disks](./user-guide/managing-disks.md)
- [Network Configuration](./user-guide/networking.md)
- [Post-Install Scripts](./user-guide/post-install.md)

# API Reference

- [Overview](./api/overview.md)
- [DiskManager](./api/disk-manager.md)
- [IsoManager](./api/iso-manager.md)
- [QemuUtils](./api/qemu-utils.md)
- [ConfigParser](./api/config-parser.md)

# Developer Guide

- [Architecture](./developer/architecture.md)
- [Building from Source](./developer/building.md)
- [Contributing](./developer/contributing.md)
- [Testing](./developer/testing.md)
- [Release Process](./developer/releases.md)

# Deployment

- [Production Setup](./deployment/production.md)
- [Docker Deployment](./deployment/docker.md)
- [Kubernetes](./deployment/kubernetes.md)
- [Monitoring](./deployment/monitoring.md)

# Troubleshooting

- [Common Issues](./troubleshooting/common-issues.md)
- [Error Messages](./troubleshooting/errors.md)
- [FAQ](./troubleshooting/faq.md)

# Reference

- [CLI Options](./reference/cli.md)
- [Configuration Reference](./reference/configuration.md)
- [Environment Variables](./reference/environment.md)
- [Glossary](./reference/glossary.md)

---

[Changelog](./changelog.md) [License](./license.md)
```

### MkDocs Configuration

```yaml
# file: mkdocs.yml
# version: 1.0.0
# guid: mkdocs-configuration

site_name: ghcommon Documentation
site_url: https://docs.example.com/ghcommon
site_description: GitHub common workflows and automation documentation
site_author: John Falk

repo_name: jdfalk/ghcommon
repo_url: https://github.com/jdfalk/ghcommon
edit_uri: edit/main/docs/

copyright: Copyright &copy; 2024 John Falk

theme:
  name: material
  language: en

  palette:
    # Light mode
    - media: '(prefers-color-scheme: light)'
      scheme: default
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode

    # Dark mode
    - media: '(prefers-color-scheme: dark)'
      scheme: slate
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-4
        name: Switch to light mode

  font:
    text: Roboto
    code: Roboto Mono

  features:
    - navigation.instant
    - navigation.tracking
    - navigation.tabs
    - navigation.tabs.sticky
    - navigation.sections
    - navigation.expand
    - navigation.path
    - navigation.indexes
    - navigation.top
    - search.suggest
    - search.highlight
    - search.share
    - header.autohide
    - content.code.copy
    - content.code.annotate
    - content.action.edit
    - content.action.view
    - toc.follow

  icon:
    repo: fontawesome/brands/github
    edit: material/pencil
    view: material/eye

extra:
  version:
    provider: mike
    default: stable

  social:
    - icon: fontawesome/brands/github
      link: https://github.com/jdfalk
    - icon: fontawesome/brands/twitter
      link: https://twitter.com/jdfalk

  analytics:
    provider: google
    property: G-XXXXXXXXXX

  consent:
    title: Cookie consent
    description: >-
      We use cookies to recognize your repeated visits and preferences, as well as to measure the
      effectiveness of our documentation and whether users find what they're searching for.

markdown_extensions:
  # Python Markdown
  - abbr
  - admonition
  - attr_list
  - def_list
  - footnotes
  - md_in_html
  - tables
  - toc:
      permalink: true
      toc_depth: 3

  # Python Markdown Extensions
  - pymdownx.arithmatex:
      generic: true
  - pymdownx.betterem:
      smart_enable: all
  - pymdownx.caret
  - pymdownx.details
  - pymdownx.emoji:
      emoji_index: !!python/name:material.extensions.emoji.twemoji
      emoji_generator: !!python/name:material.extensions.emoji.to_svg
  - pymdownx.highlight:
      anchor_linenums: true
      line_spans: __span
      pygments_lang_class: true
  - pymdownx.inlinehilite
  - pymdownx.keys
  - pymdownx.mark
  - pymdownx.smartsymbols
  - pymdownx.snippets:
      auto_append:
        - includes/abbreviations.md
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format
  - pymdownx.tabbed:
      alternate_style: true
  - pymdownx.tasklist:
      custom_checkbox: true
  - pymdownx.tilde

plugins:
  - search:
      separator: '[\s\-,:!=\[\]()"`/]+|\.(?!\d)|&[lg]t;|(?!\b)(?=[A-Z][a-z])'
  - minify:
      minify_html: true
  - git-revision-date-localized:
      enable_creation_date: true
      type: timeago
  - mkdocstrings:
      handlers:
        python:
          options:
            docstring_style: google
            show_source: true
            show_root_heading: true
            show_category_heading: true
            merge_init_into_class: true
  - awesome-pages
  - redirects:
      redirect_maps:
        'old-page.md': 'new-page.md'

extra_css:
  - stylesheets/extra.css

extra_javascript:
  - javascripts/mathjax.js
  - https://polyfill.io/v3/polyfill.min.js?features=es6
  - https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js

nav:
  - Home: index.md
  - Getting Started:
      - Installation: getting-started/installation.md
      - Quick Start: getting-started/quick-start.md
      - Configuration: getting-started/configuration.md
  - User Guide:
      - Overview: user-guide/index.md
      - Workflows: user-guide/workflows.md
      - Scripts: user-guide/scripts.md
      - Templates: user-guide/templates.md
  - API Reference:
      - Python: api/python.md
      - Workflows: api/workflows.md
  - Development:
      - Contributing: development/contributing.md
      - Architecture: development/architecture.md
      - Testing: development/testing.md
  - About:
      - Changelog: about/changelog.md
      - License: about/license.md
```

## Changelog Automation with git-cliff

### git-cliff Configuration

```toml
# file: cliff.toml
# version: 1.0.0
# guid: git-cliff-configuration

[changelog]
# Changelog header
header = """
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

"""

# Template for each release
body = """
{% if version %}\
    ## [{{ version | trim_start_matches(pat="v") }}] - {{ timestamp | date(format="%Y-%m-%d") }}
{% else %}\
    ## [unreleased]
{% endif %}\
{% for group, commits in commits | group_by(attribute="group") %}
    ### {{ group | upper_first }}
    {% for commit in commits %}
        - {% if commit.breaking %}[**breaking**] {% endif %}{{ commit.message | upper_first }}\
          {% if commit.github.pr_number %} ([#{{ commit.github.pr_number }}]({{ commit.github.pr_url }})){% endif %}\
    {% endfor %}
{% endfor %}\n
"""

# Changelog footer
footer = """
<!-- generated by git-cliff -->
"""

# Remove the leading and trailing whitespace
trim = true

[git]
# Parse commits based on Conventional Commits
conventional_commits = true

# Filter out commits with specific patterns
filter_commits = true

# Commit parsers to use
commit_parsers = [
    { message = "^feat", group = "Features" },
    { message = "^fix", group = "Bug Fixes" },
    { message = "^doc", group = "Documentation" },
    { message = "^perf", group = "Performance" },
    { message = "^refactor", group = "Refactoring" },
    { message = "^style", group = "Styling" },
    { message = "^test", group = "Testing" },
    { message = "^chore\\(release\\): prepare for", skip = true },
    { message = "^chore\\(deps\\)", skip = true },
    { message = "^chore\\(pr\\)", skip = true },
    { message = "^chore\\(pull\\)", skip = true },
    { message = "^chore", group = "Miscellaneous" },
    { message = "^ci", group = "CI/CD" },
    { message = "^build", group = "Build System" },
    { message = "^revert", group = "Reverts" },
    { body = ".*security", group = "Security" },
]

# Protect breaking changes from being skipped
protect_breaking_commits = false

# Filter out commits
filter_unconventional = true

# Sort commits
sort_commits = "oldest"

# Regex for parsing and grouping commits
commit_preprocessors = [
    # Replace issue numbers
    { pattern = '\((\w+\s)?#([0-9]+)\)', replace = "([#${2}](https://github.com/jdfalk/ghcommon/issues/${2}))" },
    # Check spelling of commits
    { pattern = 'garantee', replace = 'guarantee' },
]

# Link parsers for extracting external references
link_parsers = [
    { pattern = "#(\\d+)", href = "https://github.com/jdfalk/ghcommon/issues/$1" },
    { pattern = "RFC(\\d+)", text = "ietf-rfc$1", href = "https://datatracker.ietf.org/doc/html/rfc$1" },
]

[remote.github]
owner = "jdfalk"
repo = "ghcommon"
```

### Changelog Generation Workflow

```yaml
# file: .github/workflows/changelog.yml
# version: 1.0.0
# guid: changelog-workflow

name: Generate Changelog

on:
  push:
    branches: [main]
    tags:
      - 'v*.*.*'
  pull_request:
    branches: [main]
  workflow_dispatch:

env:
  CHANGELOG_FILE: CHANGELOG.md

jobs:
  generate-changelog:
    name: Generate Changelog
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Install git-cliff
        uses: taiki-e/install-action@v2
        with:
          tool: git-cliff

      - name: Generate changelog for tag
        if: startsWith(github.ref, 'refs/tags/')
        run: |
          git-cliff --tag ${{ github.ref_name }} --output ${{ env.CHANGELOG_FILE }}

      - name: Generate changelog (unreleased)
        if: github.event_name != 'push' || !startsWith(github.ref, 'refs/tags/')
        run: |
          git-cliff --unreleased --output ${{ env.CHANGELOG_FILE }}

      - name: Generate full changelog
        run: |
          git-cliff --output CHANGELOG-FULL.md

      - name: Upload changelog artifacts
        uses: actions/upload-artifact@v4
        with:
          name: changelog
          path: |
            ${{ env.CHANGELOG_FILE }}
            CHANGELOG-FULL.md
          retention-days: 30

      - name: Commit changelog
        if: github.event_name == 'push' && github.ref == 'refs/heads/main'
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

          if git diff --quiet ${{ env.CHANGELOG_FILE }}; then
            echo "No changes to changelog"
          else
            git add ${{ env.CHANGELOG_FILE }}
            git commit -m "docs(changelog): update changelog [skip ci]"
            git push
          fi

      - name: Create release notes
        if: startsWith(github.ref, 'refs/tags/')
        run: |
          git-cliff --tag ${{ github.ref_name }} --unreleased --strip all > release-notes.md
          cat release-notes.md >> $GITHUB_STEP_SUMMARY

      - name: Upload release notes
        if: startsWith(github.ref, 'refs/tags/')
        uses: actions/upload-artifact@v4
        with:
          name: release-notes
          path: release-notes.md
          retention-days: 90
```

## README Automation

### README Badge Generator

```python
#!/usr/bin/env python3
# file: scripts/update-readme-badges.py
# version: 1.0.0
# guid: readme-badge-generator

"""
Automatically update README.md badges with current status.

This script updates shields.io badges in README.md files with the latest
build status, coverage, version, and other metrics.
"""

import re
from pathlib import Path
from typing import Dict, List
import requests


class BadgeUpdater:
    """Updates badges in README files."""

    def __init__(self, repo: str, branch: str = "main"):
        """
        Initialize badge updater.

        Args:
            repo: Repository in format "owner/repo"
            branch: Default branch name
        """
        self.repo = repo
        self.branch = branch
        self.base_url = "https://img.shields.io"

    def generate_workflow_badge(self, workflow_name: str) -> str:
        """
        Generate GitHub Actions workflow status badge.

        Args:
            workflow_name: Name of the workflow file

        Returns:
            Badge markdown
        """
        url = f"https://github.com/{self.repo}/actions/workflows/{workflow_name}"
        badge = f"{self.base_url}/github/actions/workflow/status/{self.repo}/{workflow_name}?branch={self.branch}"
        return f"[![Workflow Status]({badge})]({url})"

    def generate_coverage_badge(self) -> str:
        """Generate code coverage badge from Codecov."""
        badge = f"{self.base_url}/codecov/c/github/{self.repo}/{self.branch}"
        url = f"https://codecov.io/gh/{self.repo}"
        return f"[![Coverage]({badge})]({url})"

    def generate_version_badge(self, version: str) -> str:
        """Generate version badge."""
        badge = f"{self.base_url}/badge/version-{version}-blue"
        return f"![Version]({badge})"

    def generate_license_badge(self, license_type: str) -> str:
        """Generate license badge."""
        badge = f"{self.base_url}/github/license/{self.repo}"
        return f"![License]({badge})"

    def generate_language_badge(self, language: str, percentage: float) -> str:
        """Generate language percentage badge."""
        color = "blue" if percentage > 50 else "green"
        badge = f"{self.base_url}/badge/{language}-{percentage:.1f}%25-{color}"
        return f"![{language}]({badge})"

    def generate_all_badges(self) -> Dict[str, str]:
        """
        Generate all standard badges.

        Returns:
            Dictionary of badge names to markdown
        """
        return {
            'ci': self.generate_workflow_badge('ci.yml'),
            'release': self.generate_workflow_badge('release.yml'),
            'coverage': self.generate_coverage_badge(),
            'license': self.generate_license_badge('MIT'),
        }

    def update_readme(self, readme_path: Path, badges: Dict[str, str]):
        """
        Update README file with new badges.

        Args:
            readme_path: Path to README.md
            badges: Dictionary of badges to update
        """
        content = readme_path.read_text()

        # Find badge section (between <!-- badges --> comments)
        badge_pattern = r'<!-- badges:start -->.*?<!-- badges:end -->'

        badge_section = "<!-- badges:start -->\n"
        for name, badge in badges.items():
            badge_section += f"{badge}\n"
        badge_section += "<!-- badges:end -->"

        if re.search(badge_pattern, content, re.DOTALL):
            # Replace existing badge section
            updated = re.sub(badge_pattern, badge_section, content, flags=re.DOTALL)
        else:
            # Add badge section at top
            lines = content.split('\n')
            # Insert after first heading
            for i, line in enumerate(lines):
                if line.startswith('#'):
                    lines.insert(i + 1, '\n' + badge_section + '\n')
                    break
            updated = '\n'.join(lines)

        readme_path.write_text(updated)
        print(f"Updated {readme_path}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Update README badges")
    parser.add_argument('--repo', required=True, help='Repository (owner/repo)')
    parser.add_argument('--branch', default='main', help='Default branch')
    parser.add_argument('--readme', type=Path, default=Path('README.md'),
                       help='Path to README file')

    args = parser.parse_args()

    updater = BadgeUpdater(args.repo, args.branch)
    badges = updater.generate_all_badges()
    updater.update_readme(args.readme, badges)


if __name__ == '__main__':
    main()
```

### Link Checker Workflow

```yaml
# file: .github/workflows/link-checker.yml
# version: 1.0.0
# guid: link-checker-workflow

name: Check Documentation Links

on:
  push:
    branches: [main]
    paths:
      - '**.md'
      - 'docs/**'
  pull_request:
    paths:
      - '**.md'
      - 'docs/**'
  schedule:
    - cron: '0 0 * * 0' # Weekly on Sunday
  workflow_dispatch:

jobs:
  link-check:
    name: Check Links
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check markdown links
        uses: gaurav-nelson/github-action-markdown-link-check@v1
        with:
          use-quiet-mode: 'yes'
          use-verbose-mode: 'yes'
          config-file: '.github/mlc_config.json'
          folder-path: 'docs/'
          file-extension: '.md'
          check-modified-files-only: 'no'

      - name: Check README links
        uses: gaurav-nelson/github-action-markdown-link-check@v1
        with:
          use-quiet-mode: 'yes'
          file-path: './README.md'

      - name: Create issue on failure
        if: failure()
        uses: actions/github-script@v7
        with:
          script: |
            const title = '🔗 Broken Links Detected';
            const body = `
            Broken links were detected in the documentation.

            **Workflow Run**: ${context.serverUrl}/${context.repo.owner}/${context.repo.repo}/actions/runs/${context.runId}
            **Branch**: ${context.ref}
            **Commit**: ${context.sha}

            Please review and fix the broken links.
            `;

            // Check if issue already exists
            const issues = await github.rest.issues.listForRepo({
              owner: context.repo.owner,
              repo: context.repo.repo,
              state: 'open',
              labels: 'documentation,broken-links'
            });

            if (issues.data.length === 0) {
              await github.rest.issues.create({
                owner: context.repo.owner,
                repo: context.repo.repo,
                title: title,
                body: body,
                labels: ['documentation', 'broken-links']
              });
            }
```

### Markdown Link Checker Config

```json
{
  "comment": "file: .github/mlc_config.json",
  "comment": "version: 1.0.0",
  "comment": "guid: mlc-configuration",

  "ignorePatterns": [
    {
      "pattern": "^http://localhost"
    },
    {
      "pattern": "^http://127.0.0.1"
    },
    {
      "pattern": "^https://example.com"
    }
  ],
  "replacementPatterns": [
    {
      "pattern": "^/",
      "replacement": "{{BASEURL}}/"
    }
  ],
  "httpHeaders": [
    {
      "urls": ["https://github.com"],
      "headers": {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0"
      }
    }
  ],
  "timeout": "20s",
  "retryOn429": true,
  "retryCount": 3,
  "fallbackRetryDelay": "30s",
  "aliveStatusCodes": [200, 206, 301, 302, 307, 308]
}
```

---

**Part 3 Complete**: Documentation sites (mdBook and MkDocs configurations with full feature sets),
changelog automation (git-cliff configuration and workflow), README badge automation, and link
checking. ✅

**Continue to Part 4** for documentation publishing (GitHub Pages deployment, versioned docs, CI
integration).
