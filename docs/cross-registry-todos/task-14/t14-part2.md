<!-- file: docs/cross-registry-todos/task-14/t14-part2.md -->
<!-- version: 1.0.0 -->
<!-- guid: t14-documentation-automation-part2-s4t5u6v7-w8x9 -->

# Task 14 Part 2: Python and JavaScript Documentation

## Python Documentation with Sphinx

### Sphinx Configuration

```python
# file: docs/conf.py
# version: 1.0.0
# guid: sphinx-configuration

"""Sphinx configuration for ghcommon documentation."""

import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath('..'))

# Project information
project = 'ghcommon'
copyright = f'{datetime.now().year}, John Falk'
author = 'John Falk'
version = '1.0.0'
release = '1.0.0'

# General configuration
extensions = [
    'sphinx.ext.autodoc',           # Auto-generate from docstrings
    'sphinx.ext.napoleon',          # Google/NumPy style docstrings
    'sphinx.ext.viewcode',          # Add source code links
    'sphinx.ext.intersphinx',       # Link to other docs
    'sphinx.ext.todo',              # TODO support
    'sphinx.ext.coverage',          # Documentation coverage
    'sphinx.ext.githubpages',       # GitHub Pages support
    'sphinx_autodoc_typehints',     # Type hint support
    'myst_parser',                  # Markdown support
]

# Autodoc configuration
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}
autodoc_typehints = 'description'
autodoc_type_aliases = {}

# Napoleon settings (Google/NumPy docstring style)
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = True
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = True
napoleon_type_aliases = None

# Intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'requests': ('https://requests.readthedocs.io/en/latest/', None),
    'pyyaml': ('https://pyyaml.org/wiki/PyYAMLDocumentation', None),
}

# MyST Parser (Markdown) configuration
myst_enable_extensions = [
    'colon_fence',
    'deflist',
    'fieldlist',
    'html_admonition',
    'html_image',
    'linkify',
    'replacements',
    'smartquotes',
    'strikethrough',
    'substitution',
    'tasklist',
]

# Templates
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# HTML output
html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'navigation_depth': 4,
    'collapse_navigation': False,
    'sticky_navigation': True,
    'includehidden': True,
    'titles_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': True,
}
html_static_path = ['_static']
html_logo = '_static/logo.png'
html_favicon = '_static/favicon.ico'
html_show_sourcelink = True
html_show_sphinx = False

# LaTeX output (PDF)
latex_elements = {
    'papersize': 'letterpaper',
    'pointsize': '10pt',
    'preamble': '',
    'figure_align': 'htbp',
}
latex_documents = [
    ('index', 'ghcommon.tex', 'ghcommon Documentation',
     'John Falk', 'manual'),
]

# Man page output
man_pages = [
    ('index', 'ghcommon', 'ghcommon Documentation',
     [author], 1)
]

# Texinfo output
texinfo_documents = [
    ('index', 'ghcommon', 'ghcommon Documentation',
     author, 'ghcommon', 'GitHub common workflows and scripts.',
     'Miscellaneous'),
]

# Epub output
epub_title = project
epub_exclude_files = ['search.html']

# Todo extension
todo_include_todos = True
```

### Python Docstring Examples

```python
#!/usr/bin/env python3
# file: scripts/workflow_debugger.py
# version: 2.0.0
# guid: python-docstring-example

"""
Workflow debugger for analyzing GitHub Actions failures.

This module provides tools for debugging failed GitHub Actions workflows,
categorizing failures, and generating fix tasks.

Example:
    Basic usage::

        from scripts.workflow_debugger import WorkflowDebugger

        debugger = WorkflowDebugger(org="jdfalk", token=os.getenv("GITHUB_TOKEN"))
        failures = debugger.scan_all_repos()
        debugger.generate_fix_tasks(failures, Path("output/"))

Attributes:
    DEFAULT_CATEGORIES (List[str]): Default failure categories.
    API_BASE_URL (str): GitHub API base URL.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union
import logging
import re

import requests

# Module-level constants
DEFAULT_CATEGORIES = ["PERMISSIONS", "DEPENDENCIES", "SYNTAX", "INFRASTRUCTURE", "UNKNOWN"]
API_BASE_URL = "https://api.github.com"

logger = logging.getLogger(__name__)


class FailureCategory(Enum):
    """
    Categories for workflow failures.

    This enum defines the main categories used to classify workflow failures
    based on error patterns and log analysis.

    Attributes:
        PERMISSIONS: Permission-related errors (token, scope)
        DEPENDENCIES: Dependency installation or resolution failures
        SYNTAX: YAML or configuration syntax errors
        INFRASTRUCTURE: CI infrastructure issues (disk space, network)
        UNKNOWN: Unclassified failures
    """

    PERMISSIONS = "PERMISSIONS"
    DEPENDENCIES = "DEPENDENCIES"
    SYNTAX = "SYNTAX"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    UNKNOWN = "UNKNOWN"


@dataclass
class WorkflowFailure:
    """
    Represents a single workflow failure.

    This dataclass contains all relevant information about a failed workflow run,
    including metadata and categorization details.

    Attributes:
        repo (str): Repository name in format "owner/repo"
        workflow (str): Workflow name
        run_id (int): Workflow run identifier
        status (str): Run status (e.g., "completed")
        category (FailureCategory): Failure category
        error_message (str): Primary error message
        failed_at (datetime): Timestamp of failure
        logs (Optional[str]): Full workflow logs if available

    Example:
        >>> failure = WorkflowFailure(
        ...     repo="jdfalk/ghcommon",
        ...     workflow="CI",
        ...     run_id=12345,
        ...     status="failure",
        ...     category=FailureCategory.PERMISSIONS,
        ...     error_message="Permission denied",
        ...     failed_at=datetime.now()
        ... )
    """

    repo: str
    workflow: str
    run_id: int
    status: str
    category: FailureCategory
    error_message: str
    failed_at: datetime
    logs: Optional[str] = None

    def to_dict(self) -> Dict[str, Union[str, int]]:
        """
        Convert failure to dictionary representation.

        Returns:
            Dict[str, Union[str, int]]: Dictionary containing all failure data

        Example:
            >>> failure.to_dict()
            {'repo': 'jdfalk/ghcommon', 'workflow': 'CI', ...}
        """
        return {
            'repo': self.repo,
            'workflow': self.workflow,
            'run_id': self.run_id,
            'status': self.status,
            'category': self.category.value,
            'error_message': self.error_message,
            'failed_at': self.failed_at.isoformat(),
        }


class WorkflowDebugger:
    """
    Debugs and analyzes failed GitHub Actions workflows.

    The WorkflowDebugger class provides comprehensive tools for analyzing workflow
    failures across GitHub repositories, categorizing errors, and generating
    actionable fix tasks.

    Args:
        org (str): GitHub organization name
        token (str): GitHub personal access token with repo scope
        base_url (str, optional): GitHub API base URL. Defaults to public GitHub.

    Attributes:
        org (str): Organization being analyzed
        session (requests.Session): HTTP session for API calls

    Raises:
        ValueError: If organization name is empty
        requests.HTTPError: If API authentication fails

    Example:
        Basic usage::

            debugger = WorkflowDebugger(
                org="jdfalk",
                token=os.getenv("GITHUB_TOKEN")
            )

            # Scan single repository
            failures = debugger.scan_repository("ghcommon")

            # Scan all repositories
            all_failures = debugger.scan_all_repos()

            # Generate fix tasks
            debugger.generate_fix_tasks(all_failures, Path("output/"))

    Note:
        Requires a GitHub token with `repo` scope for private repositories
        or `public_repo` scope for public repositories only.
    """

    def __init__(
        self,
        org: str,
        token: str,
        base_url: str = API_BASE_URL
    ):
        """
        Initialize WorkflowDebugger.

        Args:
            org: GitHub organization name
            token: GitHub personal access token
            base_url: GitHub API base URL (default: https://api.github.com)

        Raises:
            ValueError: If org is empty
        """
        if not org:
            raise ValueError("Organization name cannot be empty")

        self.org = org
        self.base_url = base_url

        # Set up authenticated session
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.github.v3+json'
        })

        logger.info(f"Initialized WorkflowDebugger for organization: {org}")

    def fetch_workflow_runs(
        self,
        repo: str,
        status: str = "failure",
        max_runs: int = 50
    ) -> List[Dict]:
        """
        Fetch workflow runs for a repository.

        Retrieves workflow runs from GitHub API, filtered by status.

        Args:
            repo: Repository name (without org prefix)
            status: Run status to filter by (default: "failure")
            max_runs: Maximum number of runs to fetch (default: 50)

        Returns:
            List[Dict]: List of workflow run data

        Raises:
            requests.HTTPError: If API request fails

        Example:
            >>> runs = debugger.fetch_workflow_runs("ghcommon", status="failure")
            >>> print(f"Found {len(runs)} failed runs")
        """
        url = f"{self.base_url}/repos/{self.org}/{repo}/actions/runs"
        params = {
            'status': status,
            'per_page': max_runs
        }

        logger.debug(f"Fetching workflow runs for {repo} with status={status}")

        response = self.session.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        runs = data.get('workflow_runs', [])

        logger.info(f"Found {len(runs)} {status} runs in {repo}")
        return runs

    def categorize_failure(self, error_log: str) -> FailureCategory:
        """
        Categorize a failure based on error log content.

        Analyzes error logs using pattern matching to determine the
        most likely failure category.

        Args:
            error_log: Error log content to analyze

        Returns:
            FailureCategory: Detected failure category

        Example:
            >>> log = "Error: Permission denied"
            >>> category = debugger.categorize_failure(log)
            >>> print(category)
            FailureCategory.PERMISSIONS

        Note:
            Uses regex pattern matching. May return UNKNOWN if no
            pattern matches.
        """
        patterns = {
            FailureCategory.PERMISSIONS: [
                r'permission denied',
                r'resource not accessible',
                r'forbidden',
                r'401 unauthorized',
                r'403 forbidden',
            ],
            FailureCategory.DEPENDENCIES: [
                r'could not find',
                r'failed to install',
                r'dependency.*not found',
                r'package.*does not exist',
                r'cargo.*failed',
            ],
            FailureCategory.SYNTAX: [
                r'yaml.*error',
                r'syntax error',
                r'invalid.*format',
                r'unexpected.*token',
            ],
            FailureCategory.INFRASTRUCTURE: [
                r'disk.*space',
                r'timeout',
                r'connection.*refused',
                r'network.*error',
            ],
        }

        log_lower = error_log.lower()

        for category, regex_list in patterns.items():
            for pattern in regex_list:
                if re.search(pattern, log_lower):
                    logger.debug(f"Matched pattern '{pattern}' for {category}")
                    return category

        logger.warning("No pattern matched, returning UNKNOWN category")
        return FailureCategory.UNKNOWN

    def generate_fix_task(
        self,
        failure: WorkflowFailure,
        output_dir: Path
    ) -> Path:
        """
        Generate a fix task file for a failure.

        Creates a JSON file containing failure details and suggested
        remediation steps.

        Args:
            failure: WorkflowFailure instance to generate task for
            output_dir: Directory to save task file

        Returns:
            Path: Path to generated task file

        Raises:
            OSError: If file cannot be written

        Example:
            >>> failure = WorkflowFailure(...)
            >>> task_path = debugger.generate_fix_task(failure, Path("tasks/"))
            >>> print(f"Task saved to: {task_path}")
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        task_file = output_dir / f"fix-{failure.repo.replace('/', '-')}-{failure.run_id}.json"

        task_data = {
            **failure.to_dict(),
            'suggested_actions': self._get_suggested_actions(failure.category)
        }

        task_file.write_text(json.dumps(task_data, indent=2))
        logger.info(f"Generated fix task: {task_file}")

        return task_file

    def _get_suggested_actions(self, category: FailureCategory) -> List[str]:
        """
        Get suggested remediation actions for a failure category.

        Args:
            category: Failure category

        Returns:
            List[str]: List of suggested actions

        Note:
            This is an internal method not intended for direct use.
        """
        actions = {
            FailureCategory.PERMISSIONS: [
                "Check GitHub token permissions",
                "Verify workflow has correct permissions block",
                "Review GITHUB_TOKEN usage",
            ],
            FailureCategory.DEPENDENCIES: [
                "Update dependency versions",
                "Check package manager lock files",
                "Verify dependency availability",
            ],
            # ... more categories
        }
        return actions.get(category, ["Manual investigation required"])
```

## JavaScript/TypeScript Documentation with TypeDoc

### TypeDoc Configuration

```json
{
  "// file": "typedoc.json",
  "// version": "1.0.0",
  "// guid": "typedoc-configuration",

  "entryPoints": ["src/index.ts"],
  "out": "docs/api",
  "name": "Workflow Manager API",
  "includeVersion": true,

  "readme": "README.md",
  "exclude": [
    "**/*+(index|.spec|.test).ts",
    "**/node_modules/**"
  ],

  "plugin": [
    "typedoc-plugin-markdown",
    "typedoc-plugin-mermaid"
  ],

  "excludePrivate": false,
  "excludeProtected": false,
  "excludeInternal": false,
  "categorizeByGroup": true,
  "defaultCategory": "Other",

  "categoryOrder": [
    "Core",
    "API",
    "Utils",
    "*"
  ],

  "sort": ["source-order"],
  "visibilityFilters": {
    "protected": true,
    "private": false,
    "inherited": true,
    "external": false
  },

  "searchInComments": true,
  "cleanOutputDir": true,
  "theme": "default",

  "navigation": {
    "includeCategories": true,
    "includeGroups": true
  },

  "markedOptions": {
    "tables": true,
    "breaks": false,
    "pedantic": false,
    "gfm": true
  }
}
```

### TypeScript Documentation Example

```typescript
// file: src/workflow-parser.ts
// version: 1.0.0
// guid: typescript-documentation-example

/**
 * Workflow parsing and validation module.
 *
 * This module provides comprehensive tools for parsing, validating, and
 * manipulating GitHub Actions workflow files.
 *
 * @module WorkflowParser
 * @category Core
 *
 * @example
 * Basic usage:
 * ```typescript
 * import { WorkflowParser } from './workflow-parser';
 *
 * const parser = new WorkflowParser();
 * const config = parser.parseYaml(yamlContent);
 * const validation = parser.validateWorkflow(config);
 * ```
 */

import * as yaml from 'js-yaml';

/**
 * Workflow configuration structure.
 *
 * Represents the complete structure of a GitHub Actions workflow file.
 *
 * @interface
 * @category Core
 */
export interface WorkflowConfig {
  /**
   * Workflow name displayed in GitHub Actions UI
   */
  name: string;

  /**
   * Events that trigger the workflow
   *
   * @example
   * ```typescript
   * on: ['push', 'pull_request']
   * ```
   */
  on: string[] | Record<string, unknown>;

  /**
   * Jobs defined in the workflow
   *
   * @example
   * ```typescript
   * jobs: {
   *   build: {
   *     'runs-on': 'ubuntu-latest',
   *     steps: [...]
   *   }
   * }
   * ```
   */
  jobs: Record<string, JobConfig>;

  /**
   * Environment variables available to all jobs
   * @optional
   */
  env?: Record<string, string>;
}

/**
 * Job configuration within a workflow.
 *
 * @interface
 * @category Core
 */
export interface JobConfig {
  /**
   * Runner environment (e.g., 'ubuntu-latest', 'macos-latest')
   */
  'runs-on': string;

  /**
   * Steps to execute in this job
   */
  steps: StepConfig[];

  /**
   * Other jobs this job depends on
   * @optional
   */
  needs?: string[];
}

/**
 * Validation result for a workflow.
 *
 * @interface
 * @category API
 */
export interface ValidationResult {
  /**
   * Whether the workflow is valid
   */
  valid: boolean;

  /**
   * List of validation errors
   */
  errors: string[];

  /**
   * List of validation warnings
   */
  warnings: string[];
}

/**
 * Parses and validates GitHub Actions workflow files.
 *
 * The WorkflowParser class provides methods for:
 * - Parsing YAML workflow files
 * - Validating workflow structure
 * - Extracting secrets and variables
 * - Analyzing workflow dependencies
 *
 * @class
 * @category Core
 *
 * @example
 * Complete workflow parsing:
 * ```typescript
 * const parser = new WorkflowParser();
 *
 * try {
 *   const config = parser.parseYaml(yamlContent);
 *   const validation = parser.validateWorkflow(config);
 *
 *   if (validation.valid) {
 *     console.log('Workflow is valid');
 *     const secrets = parser.extractSecrets(config);
 *     console.log(`Found ${secrets.length} secrets`);
 *   } else {
 *     console.error('Validation errors:', validation.errors);
 *   }
 * } catch (error) {
 *   console.error('Parse error:', error);
 * }
 * ```
 */
export class WorkflowParser {
  /**
   * Creates a new WorkflowParser instance.
   *
   * @constructor
   */
  constructor() {
    // Initialization code
  }

  /**
   * Parses a YAML workflow file into a WorkflowConfig object.
   *
   * @param yamlContent - Raw YAML content as string
   * @returns Parsed workflow configuration
   * @throws {Error} If YAML is invalid or malformed
   *
   * @example
   * ```typescript
   * const yaml = `
   *   name: CI
   *   on: [push]
   *   jobs:
   *     test:
   *       runs-on: ubuntu-latest
   *       steps:
   *         - uses: actions/checkout@v4
   * `;
   *
   * const config = parser.parseYaml(yaml);
   * console.log(config.name); // "CI"
   * ```
   */
  parseYaml(yamlContent: string): WorkflowConfig {
    try {
      const parsed = yaml.load(yamlContent) as WorkflowConfig;
      return parsed;
    } catch (error) {
      throw new Error(`Failed to parse YAML: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * Validates a workflow configuration.
   *
   * Checks for:
   * - Required fields (name, on, jobs)
   * - Valid job configurations
   * - Proper step definitions
   * - Secret and variable usage
   *
   * @param config - Workflow configuration to validate
   * @returns Validation result with errors and warnings
   *
   * @example
   * ```typescript
   * const config: WorkflowConfig = { ... };
   * const result = parser.validateWorkflow(config);
   *
   * if (!result.valid) {
   *   result.errors.forEach(error => console.error(error));
   * }
   *
   * result.warnings.forEach(warning => console.warn(warning));
   * ```
   */
  validateWorkflow(config: WorkflowConfig): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Required fields
    if (!config.name) {
      errors.push('Missing required field: name');
    }

    if (!config.on) {
      errors.push('Missing required field: on');
    }

    if (!config.jobs || Object.keys(config.jobs).length === 0) {
      errors.push('Missing required field: jobs');
    }

    // Validate jobs
    if (config.jobs) {
      for (const [jobName, jobConfig] of Object.entries(config.jobs)) {
        if (!jobConfig['runs-on']) {
          errors.push(`Job '${jobName}' missing required field: runs-on`);
        }

        if (!jobConfig.steps || jobConfig.steps.length === 0) {
          warnings.push(`Job '${jobName}' has no steps defined`);
        }
      }
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings,
    };
  }

  /**
   * Extracts all secrets referenced in a workflow.
   *
   * Searches through all steps and finds references to `secrets.*`.
   *
   * @param config - Workflow configuration
   * @returns Array of unique secret names
   *
   * @example
   * ```typescript
   * const secrets = parser.extractSecrets(config);
   * console.log(`Workflow uses ${secrets.length} secrets:`);
   * secrets.forEach(secret => console.log(`  - ${secret}`));
   * ```
   */
  extractSecrets(config: WorkflowConfig): string[] {
    const secrets = new Set<string>();
    const secretPattern = /\$\{\{\s*secrets\.(\w+)\s*\}\}/g;

    const searchString = JSON.stringify(config);
    let match;

    while ((match = secretPattern.exec(searchString)) !== null) {
      secrets.add(match[1]);
    }

    return Array.from(secrets);
  }
}
```

---

**Part 2 Complete**: Python documentation with Sphinx (comprehensive configuration and docstring examples), JavaScript/TypeScript documentation with TypeDoc (configuration and TSDoc examples). ✅

**Continue to Part 3** for documentation sites (mdBook, MkDocs, Docusaurus) and changelog automation.
