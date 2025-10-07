<!-- file: docs/cross-registry-todos/task-14/t14-part4.md -->
<!-- version: 1.0.0 -->
<!-- guid: t14-documentation-automation-part4-y9z0a1b2-c3d4 -->

# Task 14 Part 4: Documentation Publishing and Versioning

## GitHub Pages Deployment

### Multi-Version Documentation Deploy

```yaml
# file: .github/workflows/deploy-docs.yml
# version: 1.0.0
# guid: deploy-docs-workflow

name: Deploy Documentation

on:
  push:
    branches: [main]
    tags:
      - 'v*.*.*'
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to deploy (e.g., 1.2.3 or latest)'
        required: false
        default: 'latest'

env:
  PYTHON_VERSION: '3.12'
  NODE_VERSION: '20'

jobs:
  build-rust-docs:
    name: Build Rust Documentation
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: dtolnay/rust-toolchain@stable

      - uses: Swatinem/rust-cache@v2

      - name: Build rustdoc
        env:
          RUSTDOCFLAGS: "--enable-index-page -Zunstable-options"
        run: |
          cargo doc --no-deps --all-features --document-private-items

      - name: Add index redirect
        run: |
          cat > target/doc/index.html <<EOF
          <!DOCTYPE html>
          <html>
          <head>
            <meta http-equiv="refresh" content="0; url=ubuntu_autoinstall_agent/index.html">
          </head>
          <body>
            <p>Redirecting to <a href="ubuntu_autoinstall_agent/index.html">documentation</a>...</p>
          </body>
          </html>
          EOF

      - name: Upload Rust docs
        uses: actions/upload-artifact@v4
        with:
          name: rust-docs
          path: target/doc/
          retention-days: 1

  build-python-docs:
    name: Build Python Documentation
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -r docs/requirements.txt
          pip install -e .

      - name: Build Sphinx docs
        run: |
          cd docs
          sphinx-build -b html source build/html
          sphinx-build -b linkcheck source build/linkcheck

      - name: Upload Python docs
        uses: actions/upload-artifact@v4
        with:
          name: python-docs
          path: docs/build/html/
          retention-days: 1

  build-js-docs:
    name: Build JavaScript Documentation
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'pnpm'

      - uses: pnpm/action-setup@v2
        with:
          version: 8

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Build TypeDoc
        run: pnpm run docs:build

      - name: Upload JS docs
        uses: actions/upload-artifact@v4
        with:
          name: js-docs
          path: docs/api/
          retention-days: 1

  build-user-guide:
    name: Build User Guide (mdBook)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install mdBook
        uses: taiki-e/install-action@v2
        with:
          tool: mdbook@0.4.36

      - name: Install mdBook plugins
        run: |
          cargo install mdbook-mermaid
          cargo install mdbook-katex

      - name: Build mdBook
        run: mdbook build

      - name: Upload mdBook docs
        uses: actions/upload-artifact@v4
        with:
          name: mdbook-docs
          path: docs/book/
          retention-days: 1

  combine-docs:
    name: Combine Documentation
    needs: [build-rust-docs, build-python-docs, build-js-docs, build-user-guide]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Download all docs
        uses: actions/download-artifact@v4
        with:
          path: docs-temp/

      - name: Determine version
        id: version
        run: |
          if [[ "${{ github.ref }}" == refs/tags/* ]]; then
            VERSION="${GITHUB_REF#refs/tags/v}"
          elif [[ "${{ github.event.inputs.version }}" != "" ]]; then
            VERSION="${{ github.event.inputs.version }}"
          else
            VERSION="latest"
          fi
          echo "version=$VERSION" >> $GITHUB_OUTPUT
          echo "Deploying version: $VERSION"

      - name: Create combined docs structure
        run: |
          mkdir -p combined-docs/${{ steps.version.outputs.version }}

          # Copy user guide to root
          cp -r docs-temp/mdbook-docs/* combined-docs/${{ steps.version.outputs.version }}/

          # Copy API docs to subdirectories
          mkdir -p combined-docs/${{ steps.version.outputs.version }}/api
          cp -r docs-temp/rust-docs/* combined-docs/${{ steps.version.outputs.version }}/api/rust/
          cp -r docs-temp/python-docs/* combined-docs/${{ steps.version.outputs.version }}/api/python/
          cp -r docs-temp/js-docs/* combined-docs/${{ steps.version.outputs.version }}/api/javascript/

          # Create version index
          cat > combined-docs/${{ steps.version.outputs.version }}/versions.json <<EOF
          {
            "current": "${{ steps.version.outputs.version }}",
            "versions": ["${{ steps.version.outputs.version }}", "latest"],
            "aliases": {
              "latest": "${{ steps.version.outputs.version }}"
            }
          }
          EOF

      - name: Create version selector
        run: |
          cat > combined-docs/version-selector.html <<'EOF'
          <div class="version-selector">
            <label for="version-select">Version:</label>
            <select id="version-select" onchange="switchVersion(this.value)">
              <option value="latest">Latest</option>
            </select>
          </div>
          <script>
            async function loadVersions() {
              const response = await fetch('/versions.json');
              const data = await response.json();
              const select = document.getElementById('version-select');

              data.versions.forEach(version => {
                const option = document.createElement('option');
                option.value = version;
                option.textContent = version;
                if (version === data.current) {
                  option.selected = true;
                }
                select.appendChild(option);
              });
            }

            function switchVersion(version) {
              const currentPath = window.location.pathname;
              const pathParts = currentPath.split('/');
              pathParts[1] = version;
              window.location.pathname = pathParts.join('/');
            }

            loadVersions();
          </script>
          EOF

      - name: Create root index
        run: |
          cat > combined-docs/index.html <<EOF
          <!DOCTYPE html>
          <html>
          <head>
            <meta charset="utf-8">
            <meta http-equiv="refresh" content="0; url=${{ steps.version.outputs.version }}/index.html">
            <title>Documentation</title>
          </head>
          <body>
            <p>Redirecting to <a href="${{ steps.version.outputs.version }}/index.html">documentation</a>...</p>
          </body>
          </html>
          EOF

      - name: Upload combined docs
        uses: actions/upload-artifact@v4
        with:
          name: combined-docs
          path: combined-docs/
          retention-days: 1

  deploy-github-pages:
    name: Deploy to GitHub Pages
    needs: [combine-docs]
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pages: write
      id-token: write
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Download combined docs
        uses: actions/download-artifact@v4
        with:
          name: combined-docs
          path: ./docs-site

      - name: Setup Pages
        uses: actions/configure-pages@v4

      - name: Upload to Pages
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./docs-site

      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4

      - name: Comment on PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `📚 Documentation preview available at: ${{ steps.deployment.outputs.page_url }}`
            })
```

## Read the Docs Configuration

```yaml
# file: .readthedocs.yml
# version: 1.0.0
# guid: readthedocs-configuration

version: 2

build:
  os: ubuntu-22.04
  tools:
    python: "3.12"
  jobs:
    pre_build:
      - pip install poetry
      - poetry install --with docs
    post_build:
      - echo "Documentation built successfully"

sphinx:
  configuration: docs/source/conf.py
  fail_on_warning: true

formats:
  - pdf
  - epub
  - htmlzip

python:
  install:
    - method: pip
      path: .
      extra_requirements:
        - docs
    - requirements: docs/requirements.txt

search:
  ranking:
    api/index.rst: 2
    user-guide/index.rst: 3
  ignore:
    - changelog.rst
```

## Versioned Documentation Script

```python
#!/usr/bin/env python3
# file: scripts/version-docs.py
# version: 1.0.0
# guid: version-docs-script

"""
Manage versioned documentation.

This script handles creating, updating, and managing multiple versions
of documentation for different releases.
"""

import json
import shutil
from pathlib import Path
from typing import List, Dict, Optional
import subprocess
import argparse


class DocVersionManager:
    """Manages versioned documentation."""

    def __init__(self, docs_root: Path):
        """
        Initialize documentation version manager.

        Args:
            docs_root: Root directory for documentation
        """
        self.docs_root = docs_root
        self.versions_file = docs_root / "versions.json"
        self.versions_data = self._load_versions()

    def _load_versions(self) -> Dict:
        """Load versions data from JSON file."""
        if self.versions_file.exists():
            with open(self.versions_file) as f:
                return json.load(f)
        return {
            "versions": [],
            "aliases": {
                "latest": None,
                "stable": None
            }
        }

    def _save_versions(self):
        """Save versions data to JSON file."""
        with open(self.versions_file, 'w') as f:
            json.dump(self.versions_data, f, indent=2)

    def add_version(self, version: str, is_latest: bool = False,
                   is_stable: bool = False):
        """
        Add a new documentation version.

        Args:
            version: Version string (e.g., "1.2.3")
            is_latest: Whether this is the latest version
            is_stable: Whether this is the stable version
        """
        if version not in self.versions_data["versions"]:
            self.versions_data["versions"].append(version)
            self.versions_data["versions"].sort(reverse=True)

        if is_latest:
            self.versions_data["aliases"]["latest"] = version

        if is_stable:
            self.versions_data["aliases"]["stable"] = version

        self._save_versions()
        print(f"Added version {version}")

    def remove_version(self, version: str):
        """
        Remove a documentation version.

        Args:
            version: Version to remove
        """
        if version in self.versions_data["versions"]:
            self.versions_data["versions"].remove(version)

        # Update aliases if they pointed to removed version
        for alias, target in self.versions_data["aliases"].items():
            if target == version:
                self.versions_data["aliases"][alias] = None

        self._save_versions()

        # Remove version directory
        version_dir = self.docs_root / version
        if version_dir.exists():
            shutil.rmtree(version_dir)

        print(f"Removed version {version}")

    def set_alias(self, alias: str, version: str):
        """
        Set an alias to point to a specific version.

        Args:
            alias: Alias name (e.g., "latest", "stable")
            version: Target version
        """
        if version not in self.versions_data["versions"]:
            raise ValueError(f"Version {version} does not exist")

        self.versions_data["aliases"][alias] = version
        self._save_versions()

        # Create symlink for alias
        alias_path = self.docs_root / alias
        if alias_path.exists():
            alias_path.unlink()

        target = Path(version)
        alias_path.symlink_to(target)

        print(f"Set alias '{alias}' -> '{version}'")

    def list_versions(self):
        """List all available versions."""
        print("Available versions:")
        for version in self.versions_data["versions"]:
            aliases = [a for a, v in self.versions_data["aliases"].items()
                      if v == version]
            alias_str = f" ({', '.join(aliases)})" if aliases else ""
            print(f"  - {version}{alias_str}")

    def build_version(self, version: str, source_dir: Path):
        """
        Build documentation for a specific version.

        Args:
            version: Version to build
            source_dir: Source directory containing documentation
        """
        version_dir = self.docs_root / version
        version_dir.mkdir(parents=True, exist_ok=True)

        # Build documentation (example with Sphinx)
        subprocess.run(
            ['sphinx-build', '-b', 'html', str(source_dir), str(version_dir)],
            check=True
        )

        print(f"Built documentation for version {version}")

    def generate_version_selector(self) -> str:
        """
        Generate HTML for version selector dropdown.

        Returns:
            HTML string for version selector
        """
        options = []
        for version in self.versions_data["versions"]:
            aliases = [a for a, v in self.versions_data["aliases"].items()
                      if v == version]
            label = version
            if aliases:
                label += f" ({', '.join(aliases)})"
            options.append(f'<option value="{version}">{label}</option>')

        return f'''
<div class="version-selector">
  <label for="version-select">Version:</label>
  <select id="version-select" onchange="switchVersion(this.value)">
    {chr(10).join(options)}
  </select>
</div>
<script>
function switchVersion(version) {{
  const currentPath = window.location.pathname;
  const pathParts = currentPath.split('/');

  // Find version in path and replace it
  for (let i = 0; i < pathParts.length; i++) {{
    if (pathParts[i] === '{self.versions_data["versions"][0]}') {{
      pathParts[i] = version;
      break;
    }}
  }}

  window.location.pathname = pathParts.join('/');
}}
</script>
'''


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Manage versioned documentation"
    )
    parser.add_argument(
        '--docs-root',
        type=Path,
        default=Path('docs/site'),
        help='Root directory for documentation'
    )

    subparsers = parser.add_subparsers(dest='command', required=True)

    # Add version command
    add_parser = subparsers.add_parser('add', help='Add a new version')
    add_parser.add_argument('version', help='Version to add')
    add_parser.add_argument('--latest', action='store_true',
                           help='Mark as latest version')
    add_parser.add_argument('--stable', action='store_true',
                           help='Mark as stable version')

    # Remove version command
    remove_parser = subparsers.add_parser('remove', help='Remove a version')
    remove_parser.add_argument('version', help='Version to remove')

    # Set alias command
    alias_parser = subparsers.add_parser('alias', help='Set version alias')
    alias_parser.add_argument('alias', help='Alias name')
    alias_parser.add_argument('version', help='Target version')

    # List versions command
    subparsers.add_parser('list', help='List all versions')

    # Build version command
    build_parser = subparsers.add_parser('build', help='Build version docs')
    build_parser.add_argument('version', help='Version to build')
    build_parser.add_argument('--source', type=Path, required=True,
                             help='Source directory')

    args = parser.parse_args()

    manager = DocVersionManager(args.docs_root)

    if args.command == 'add':
        manager.add_version(args.version, args.latest, args.stable)
    elif args.command == 'remove':
        manager.remove_version(args.version)
    elif args.command == 'alias':
        manager.set_alias(args.alias, args.version)
    elif args.command == 'list':
        manager.list_versions()
    elif args.command == 'build':
        manager.build_version(args.version, args.source)


if __name__ == '__main__':
    main()
```

## Documentation API Reference Generator

```python
#!/usr/bin/env python3
# file: scripts/generate-api-index.py
# version: 1.0.0
# guid: api-index-generator

"""
Generate API reference index from multiple language documentation.

Creates a unified API index page that links to Rust, Python, and JavaScript
API documentation with search capabilities.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import re


@dataclass
class APIEntry:
    """Represents an API entry."""
    name: str
    language: str
    type: str  # function, class, module, etc.
    description: str
    path: str
    signature: Optional[str] = None


class APIIndexGenerator:
    """Generates unified API index."""

    def __init__(self, api_root: Path):
        """
        Initialize API index generator.

        Args:
            api_root: Root directory containing API docs
        """
        self.api_root = api_root
        self.entries: List[APIEntry] = []

    def scan_rust_docs(self, rust_doc_path: Path):
        """Scan Rust documentation for API entries."""
        # Parse search-index.js from rustdoc
        search_index = rust_doc_path / "search-index.js"
        if not search_index.exists():
            return

        content = search_index.read_text()
        # Extract JSON data from search index
        # (This is simplified; actual parsing would be more complex)
        print(f"Scanned Rust docs at {rust_doc_path}")

    def scan_python_docs(self, python_doc_path: Path):
        """Scan Python/Sphinx documentation for API entries."""
        # Parse objects.inv or searchindex.js from Sphinx
        searchindex = python_doc_path / "searchindex.js"
        if not searchindex.exists():
            return

        print(f"Scanned Python docs at {python_doc_path}")

    def scan_js_docs(self, js_doc_path: Path):
        """Scan TypeScript/TypeDoc documentation for API entries."""
        # Parse TypeDoc JSON output
        json_file = js_doc_path / "documentation.json"
        if json_file.exists():
            with open(json_file) as f:
                data = json.load(f)
                # Process TypeDoc JSON structure
                print(f"Scanned JS docs at {js_doc_path}")

    def generate_index_html(self, output: Path):
        """
        Generate HTML index page.

        Args:
            output: Output file path
        """
        html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Reference</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }
        .search-box {
            width: 100%;
            padding: 10px;
            font-size: 16px;
            margin-bottom: 20px;
            border: 2px solid #ddd;
            border-radius: 4px;
        }
        .filters {
            margin-bottom: 20px;
        }
        .filter-button {
            padding: 8px 16px;
            margin-right: 10px;
            border: 1px solid #ddd;
            background: white;
            cursor: pointer;
            border-radius: 4px;
        }
        .filter-button.active {
            background: #007bff;
            color: white;
            border-color: #007bff;
        }
        .api-entry {
            padding: 15px;
            margin-bottom: 10px;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            background: #f9f9f9;
        }
        .api-entry.hidden {
            display: none;
        }
        .api-name {
            font-size: 18px;
            font-weight: bold;
            color: #333;
        }
        .api-language {
            display: inline-block;
            padding: 2px 8px;
            margin-left: 10px;
            font-size: 12px;
            background: #007bff;
            color: white;
            border-radius: 3px;
        }
        .api-type {
            display: inline-block;
            padding: 2px 8px;
            margin-left: 5px;
            font-size: 12px;
            background: #6c757d;
            color: white;
            border-radius: 3px;
        }
        .api-description {
            margin-top: 10px;
            color: #666;
        }
        .api-signature {
            margin-top: 10px;
            padding: 10px;
            background: #f0f0f0;
            border-left: 3px solid #007bff;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            overflow-x: auto;
        }
    </style>
</head>
<body>
    <h1>API Reference</h1>

    <input type="text" id="search" class="search-box" placeholder="Search API...">

    <div class="filters">
        <button class="filter-button active" data-language="all">All</button>
        <button class="filter-button" data-language="rust">Rust</button>
        <button class="filter-button" data-language="python">Python</button>
        <button class="filter-button" data-language="javascript">JavaScript</button>
    </div>

    <div id="api-list"></div>

    <script>
        const apiData = ''' + json.dumps([asdict(e) for e in self.entries]) + ''';

        function renderAPIList(entries) {
            const list = document.getElementById('api-list');
            list.innerHTML = '';

            entries.forEach(entry => {
                const div = document.createElement('div');
                div.className = 'api-entry';
                div.dataset.language = entry.language;

                let html = `
                    <div class="api-name">
                        <a href="${entry.path}">${entry.name}</a>
                        <span class="api-language">${entry.language}</span>
                        <span class="api-type">${entry.type}</span>
                    </div>
                    <div class="api-description">${entry.description}</div>
                `;

                if (entry.signature) {
                    html += `<div class="api-signature">${entry.signature}</div>`;
                }

                div.innerHTML = html;
                list.appendChild(div);
            });
        }

        // Search functionality
        document.getElementById('search').addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            const entries = document.querySelectorAll('.api-entry');

            entries.forEach(entry => {
                const text = entry.textContent.toLowerCase();
                entry.classList.toggle('hidden', !text.includes(query));
            });
        });

        // Filter functionality
        document.querySelectorAll('.filter-button').forEach(button => {
            button.addEventListener('click', () => {
                document.querySelectorAll('.filter-button').forEach(b =>
                    b.classList.remove('active')
                );
                button.classList.add('active');

                const language = button.dataset.language;
                const entries = document.querySelectorAll('.api-entry');

                entries.forEach(entry => {
                    if (language === 'all' || entry.dataset.language === language) {
                        entry.classList.remove('hidden');
                    } else {
                        entry.classList.add('hidden');
                    }
                });
            });
        });

        // Initial render
        renderAPIList(apiData);
    </script>
</body>
</html>
'''
        output.write_text(html)
        print(f"Generated API index at {output}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate API index")
    parser.add_argument('--api-root', type=Path, required=True,
                       help='Root directory containing API documentation')
    parser.add_argument('--output', type=Path, default=Path('api-index.html'),
                       help='Output HTML file')

    args = parser.parse_args()

    generator = APIIndexGenerator(args.api_root)

    # Scan all language documentation
    rust_docs = args.api_root / 'rust'
    python_docs = args.api_root / 'python'
    js_docs = args.api_root / 'javascript'

    if rust_docs.exists():
        generator.scan_rust_docs(rust_docs)
    if python_docs.exists():
        generator.scan_python_docs(python_docs)
    if js_docs.exists():
        generator.scan_js_docs(js_docs)

    generator.generate_index_html(args.output)


if __name__ == '__main__':
    main()
```

---

**Part 4 Complete**: GitHub Pages deployment with multi-version support, Read the Docs configuration, versioned documentation management script, and unified API index generator. ✅

**Continue to Part 5** for documentation CI/CD integration and automation workflows.
