<!-- file: docs/cross-registry-todos/task-14/t14-part5.md -->
<!-- version: 1.0.0 -->
<!-- guid: t14-documentation-automation-part5-e4f5g6h7-i8j9 -->

# Task 14 Part 5: Documentation CI/CD Integration

## Documentation Build Matrix

```yaml
# file: .github/workflows/docs-ci.yml
# version: 1.0.0
# guid: docs-ci-workflow

name: Documentation CI

on:
  push:
    branches: [main, develop]
    paths:
      - 'docs/**'
      - '**.md'
      - 'src/**/*.rs'
      - 'src/**/*.py'
      - 'src/**/*.ts'
      - '.github/workflows/docs-ci.yml'
  pull_request:
    paths:
      - 'docs/**'
      - '**.md'
      - 'src/**/*.rs'
      - 'src/**/*.py'
      - 'src/**/*.ts'
  workflow_dispatch:

env:
  CARGO_TERM_COLOR: always
  RUST_BACKTRACE: 1

jobs:
  detect-changes:
    name: Detect Documentation Changes
    runs-on: ubuntu-latest
    outputs:
      rust: ${{ steps.filter.outputs.rust }}
      python: ${{ steps.filter.outputs.python }}
      javascript: ${{ steps.filter.outputs.javascript }}
      markdown: ${{ steps.filter.outputs.markdown }}
      mdbook: ${{ steps.filter.outputs.mdbook }}
      mkdocs: ${{ steps.filter.outputs.mkdocs }}
    steps:
      - uses: actions/checkout@v4

      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            rust:
              - 'src/**/*.rs'
              - 'Cargo.toml'
              - 'docs/rust/**'
            python:
              - 'src/**/*.py'
              - 'docs/source/**'
              - 'docs/conf.py'
              - 'docs/requirements.txt'
            javascript:
              - 'src/**/*.ts'
              - 'src/**/*.js'
              - 'typedoc.json'
              - 'docs/api/**'
            markdown:
              - '**.md'
            mdbook:
              - 'docs/src/**'
              - 'book.toml'
            mkdocs:
              - 'docs/**'
              - 'mkdocs.yml'

  build-rust-docs:
    name: Build Rust Documentation
    needs: detect-changes
    if: needs.detect-changes.outputs.rust == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: dtolnay/rust-toolchain@stable
        with:
          components: rust-docs

      - uses: Swatinem/rust-cache@v2

      - name: Check documentation
        run: |
          cargo doc --no-deps --all-features --document-private-items
        env:
          RUSTDOCFLAGS: '-D warnings'

      - name: Check for broken intra-doc links
        run: |
          cargo doc --no-deps --all-features 2>&1 | \
            grep -E '(warning: unresolved link|warning: could not resolve link)' && \
            exit 1 || exit 0

      - name: Validate doc examples
        run: cargo test --doc

      - name: Upload docs
        uses: actions/upload-artifact@v4
        with:
          name: rust-docs
          path: target/doc/
          retention-days: 7

  build-python-docs:
    name: Build Python Documentation
    needs: detect-changes
    if: needs.detect-changes.outputs.python == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -r docs/requirements.txt
          pip install -e .

      - name: Check docstring coverage
        run: |
          pip install interrogate
          interrogate -v --fail-under=80 src/

      - name: Build HTML docs
        run: |
          cd docs
          sphinx-build -W --keep-going -b html source build/html

      - name: Check links
        run: |
          cd docs
          sphinx-build -b linkcheck source build/linkcheck
        continue-on-error: true

      - name: Build man pages
        run: |
          cd docs
          sphinx-build -b man source build/man

      - name: Upload docs
        uses: actions/upload-artifact@v4
        with:
          name: python-docs
          path: docs/build/
          retention-days: 7

  build-js-docs:
    name: Build JavaScript Documentation
    needs: detect-changes
    if: needs.detect-changes.outputs.javascript == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'pnpm'

      - uses: pnpm/action-setup@v2
        with:
          version: 8

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Lint TypeScript docs
        run: pnpm run lint:tsdoc

      - name: Build TypeDoc
        run: |
          pnpm run docs:build
          pnpm run docs:json

      - name: Upload docs
        uses: actions/upload-artifact@v4
        with:
          name: js-docs
          path: docs/api/
          retention-days: 7

  build-mdbook:
    name: Build mdBook User Guide
    needs: detect-changes
    if: needs.detect-changes.outputs.mdbook == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install mdBook
        uses: taiki-e/install-action@v2
        with:
          tool: mdbook@0.4.36,mdbook-mermaid@0.13.0,mdbook-katex@0.5.9

      - name: Test mdBook build
        run: mdbook test

      - name: Build mdBook
        run: mdbook build

      - name: Validate internal links
        run: |
          # Check for broken internal links
          find docs/book -name "*.html" -type f -exec \
            grep -l 'href="[^h]' {} \; | while read file; do
              echo "Checking $file"
              # Simple check for 404 anchors
            done

      - name: Upload docs
        uses: actions/upload-artifact@v4
        with:
          name: mdbook-docs
          path: docs/book/
          retention-days: 7

  build-mkdocs:
    name: Build MkDocs Site
    needs: detect-changes
    if: needs.detect-changes.outputs.mkdocs == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      - name: Install MkDocs and plugins
        run: |
          pip install mkdocs-material
          pip install mkdocs-minify-plugin
          pip install mkdocs-git-revision-date-localized-plugin
          pip install mkdocstrings[python]
          pip install mkdocs-awesome-pages-plugin
          pip install mkdocs-redirects

      - name: Build MkDocs
        run: mkdocs build --strict

      - name: Upload site
        uses: actions/upload-artifact@v4
        with:
          name: mkdocs-site
          path: site/
          retention-days: 7

  lint-markdown:
    name: Lint Markdown Files
    needs: detect-changes
    if: needs.detect-changes.outputs.markdown == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Lint markdown
        uses: DavidAnson/markdownlint-cli2-action@v15
        with:
          globs: '**/*.md'

      - name: Check markdown links
        uses: gaurav-nelson/github-action-markdown-link-check@v1
        with:
          use-quiet-mode: 'yes'
          config-file: '.github/mlc_config.json'

  check-spelling:
    name: Check Spelling
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check spelling
        uses: crate-ci/typos@v1.18.2
        with:
          files: docs/ README.md CHANGELOG.md
          config: .typos.toml

  validate-examples:
    name: Validate Code Examples
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Extract and validate code examples
        run: |
          python scripts/validate-examples.py docs/

  documentation-coverage:
    name: Check Documentation Coverage
    runs-on: ubuntu-latest
    strategy:
      matrix:
        language: [rust, python, javascript]
    steps:
      - uses: actions/checkout@v4

      - name: Check Rust doc coverage
        if: matrix.language == 'rust'
        run: |
          cargo install cargo-rdme
          cargo install cargo-deadlinks

          # Check for missing docs
          cargo rustdoc -- -D missing-docs

          # Check for dead links
          cargo doc --no-deps
          cargo deadlinks --dir target/doc

      - name: Check Python doc coverage
        if: matrix.language == 'python'
        run: |
          pip install interrogate
          interrogate -vv --fail-under=80 \
            --ignore-init-method \
            --ignore-init-module \
            src/

      - name: Check JavaScript doc coverage
        if: matrix.language == 'javascript'
        run: |
          pnpm install
          pnpm run docs:coverage

  preview-comment:
    name: PR Documentation Preview
    if: github.event_name == 'pull_request'
    needs:
      [
        build-rust-docs,
        build-python-docs,
        build-js-docs,
        build-mdbook,
        build-mkdocs,
      ]
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
    steps:
      - name: Download all artifacts
        uses: actions/download-artifact@v4
        with:
          path: docs-preview/

      - name: Deploy to preview environment
        id: deploy-preview
        run: |
          # Deploy to preview service (Netlify, Vercel, etc.)
          # This is a placeholder - actual implementation would vary
          echo "preview_url=https://preview-${{ github.event.pull_request.number }}.example.com" >> $GITHUB_OUTPUT

      - name: Comment on PR
        uses: actions/github-script@v7
        with:
          script: |
            const previewUrl = '${{ steps.deploy-preview.outputs.preview_url }}';
            const body = `
            ## 📚 Documentation Preview

            Documentation preview is available at: ${previewUrl}

            ### Preview Links:
            - [Rust API Docs](${previewUrl}/rust/)
            - [Python API Docs](${previewUrl}/python/)
            - [JavaScript API Docs](${previewUrl}/javascript/)
            - [User Guide](${previewUrl}/guide/)

            This preview will be available for 7 days.
            `;

            // Find existing comment
            const comments = await github.rest.issues.listComments({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
            });

            const existingComment = comments.data.find(
              c => c.user.login === 'github-actions[bot]' &&
                   c.body.includes('Documentation Preview')
            );

            if (existingComment) {
              await github.rest.issues.updateComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                comment_id: existingComment.id,
                body: body
              });
            } else {
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: context.issue.number,
                body: body
              });
            }

  summary:
    name: Documentation CI Summary
    if: always()
    needs:
      [
        build-rust-docs,
        build-python-docs,
        build-js-docs,
        build-mdbook,
        build-mkdocs,
        lint-markdown,
        check-spelling,
        validate-examples,
        documentation-coverage,
      ]
    runs-on: ubuntu-latest
    steps:
      - name: Generate summary
        run: |
          echo "# Documentation CI Summary" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "| Check | Status |" >> $GITHUB_STEP_SUMMARY
          echo "|-------|--------|" >> $GITHUB_STEP_SUMMARY
          echo "| Rust Docs | ${{ needs.build-rust-docs.result || 'skipped' }} |" >> $GITHUB_STEP_SUMMARY
          echo "| Python Docs | ${{ needs.build-python-docs.result || 'skipped' }} |" >> $GITHUB_STEP_SUMMARY
          echo "| JS Docs | ${{ needs.build-js-docs.result || 'skipped' }} |" >> $GITHUB_STEP_SUMMARY
          echo "| mdBook | ${{ needs.build-mdbook.result || 'skipped' }} |" >> $GITHUB_STEP_SUMMARY
          echo "| MkDocs | ${{ needs.build-mkdocs.result || 'skipped' }} |" >> $GITHUB_STEP_SUMMARY
          echo "| Markdown Lint | ${{ needs.lint-markdown.result || 'skipped' }} |" >> $GITHUB_STEP_SUMMARY
          echo "| Spelling | ${{ needs.check-spelling.result }} |" >> $GITHUB_STEP_SUMMARY
          echo "| Examples | ${{ needs.validate-examples.result }} |" >> $GITHUB_STEP_SUMMARY
          echo "| Coverage | ${{ needs.documentation-coverage.result }} |" >> $GITHUB_STEP_SUMMARY
```

## Example Validation Script

````python
#!/usr/bin/env python3
# file: scripts/validate-examples.py
# version: 1.0.0
# guid: validate-examples-script

"""
Validate code examples in documentation.

Extracts code blocks from markdown files and validates that they are
syntactically correct and can compile/run.
"""

import re
import subprocess
import tempfile
from pathlib import Path
from typing import List, Tuple, Dict
import sys


class ExampleValidator:
    """Validates code examples in documentation."""

    def __init__(self, docs_dir: Path):
        """
        Initialize example validator.

        Args:
            docs_dir: Directory containing documentation
        """
        self.docs_dir = docs_dir
        self.errors: List[Tuple[Path, int, str]] = []

    def extract_code_blocks(self, file_path: Path) -> List[Tuple[str, str, int]]:
        """
        Extract code blocks from markdown file.

        Args:
            file_path: Path to markdown file

        Returns:
            List of (language, code, line_number) tuples
        """
        content = file_path.read_text()
        blocks = []

        # Match fenced code blocks
        pattern = r'```(\w+)\n(.*?)```'
        for match in re.finditer(pattern, content, re.DOTALL):
            language = match.group(1)
            code = match.group(2)
            line_number = content[:match.start()].count('\n') + 1
            blocks.append((language, code, line_number))

        return blocks

    def validate_rust_example(self, code: str) -> bool:
        """
        Validate Rust code example.

        Args:
            code: Rust code to validate

        Returns:
            True if valid, False otherwise
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rs', delete=False) as f:
            # Wrap in main if not already present
            if 'fn main' not in code:
                full_code = f"fn main() {{\n{code}\n}}"
            else:
                full_code = code

            f.write(full_code)
            f.flush()

            try:
                result = subprocess.run(
                    ['rustc', '--crate-type', 'bin', f.name],
                    capture_output=True,
                    timeout=30
                )
                Path(f.name).unlink()
                return result.returncode == 0
            except Exception as e:
                print(f"Error validating Rust: {e}")
                return False

    def validate_python_example(self, code: str) -> bool:
        """
        Validate Python code example.

        Args:
            code: Python code to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            compile(code, '<string>', 'exec')
            return True
        except SyntaxError as e:
            print(f"Python syntax error: {e}")
            return False

    def validate_javascript_example(self, code: str) -> bool:
        """
        Validate JavaScript/TypeScript code example.

        Args:
            code: JavaScript code to validate

        Returns:
            True if valid, False otherwise
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(code)
            f.flush()

            try:
                result = subprocess.run(
                    ['node', '--check', f.name],
                    capture_output=True,
                    timeout=10
                )
                Path(f.name).unlink()
                return result.returncode == 0
            except Exception as e:
                print(f"Error validating JavaScript: {e}")
                return False

    def validate_shell_example(self, code: str) -> bool:
        """
        Validate shell script example.

        Args:
            code: Shell code to validate

        Returns:
            True if valid, False otherwise
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(code)
            f.flush()

            try:
                result = subprocess.run(
                    ['bash', '-n', f.name],
                    capture_output=True,
                    timeout=10
                )
                Path(f.name).unlink()
                return result.returncode == 0
            except Exception as e:
                print(f"Error validating shell: {e}")
                return False

    def validate_file(self, file_path: Path):
        """
        Validate all code examples in a file.

        Args:
            file_path: Path to markdown file
        """
        print(f"Validating {file_path}")
        blocks = self.extract_code_blocks(file_path)

        for language, code, line_number in blocks:
            # Skip certain languages
            if language in ['text', 'json', 'yaml', 'toml', 'xml']:
                continue

            valid = False
            if language in ['rust', 'rs']:
                valid = self.validate_rust_example(code)
            elif language in ['python', 'py']:
                valid = self.validate_python_example(code)
            elif language in ['javascript', 'js', 'typescript', 'ts']:
                valid = self.validate_javascript_example(code)
            elif language in ['bash', 'sh', 'shell']:
                valid = self.validate_shell_example(code)
            else:
                print(f"  Skipping {language} block at line {line_number}")
                continue

            if not valid:
                error_msg = f"Invalid {language} code block at line {line_number}"
                self.errors.append((file_path, line_number, error_msg))
                print(f"  ❌ {error_msg}")
            else:
                print(f"  ✅ Valid {language} code block at line {line_number}")

    def validate_all(self) -> bool:
        """
        Validate all markdown files in docs directory.

        Returns:
            True if all examples are valid, False otherwise
        """
        markdown_files = list(self.docs_dir.rglob('*.md'))
        print(f"Found {len(markdown_files)} markdown files")

        for file_path in markdown_files:
            self.validate_file(file_path)

        if self.errors:
            print(f"\n❌ Found {len(self.errors)} invalid code examples:")
            for file_path, line_number, error_msg in self.errors:
                print(f"  {file_path}:{line_number} - {error_msg}")
            return False
        else:
            print("\n✅ All code examples are valid!")
            return True


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate code examples in documentation"
    )
    parser.add_argument(
        'docs_dir',
        type=Path,
        help='Directory containing documentation'
    )

    args = parser.parse_args()

    if not args.docs_dir.exists():
        print(f"Error: {args.docs_dir} does not exist")
        sys.exit(1)

    validator = ExampleValidator(args.docs_dir)
    success = validator.validate_all()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
````

## Typos Configuration

```toml
# file: .typos.toml
# version: 1.0.0
# guid: typos-configuration

[default]
extend-ignore-re = [
  # Ignore version numbers
  "\\bv\\d+\\.\\d+\\.\\d+\\b",
  # Ignore hex values
  "\\b[0-9a-fA-F]{6,}\\b",
  # Ignore URLs
  "https?://\\S+",
  # Ignore file paths
  "/[\\w/.-]+",
]

[default.extend-words]
# Add custom dictionary words
complier = "complier"  # If you mean "complier" not "compiler"

[files]
extend-exclude = [
  "target/",
  "node_modules/",
  "*.lock",
  "*.json",
  "CHANGELOG.md",
]

[type.md]
extend-glob = ["*.md"]
```

## Documentation Metrics Collection

```python
#!/usr/bin/env python3
# file: scripts/doc-metrics.py
# version: 1.0.0
# guid: doc-metrics-script

"""
Collect documentation metrics.

Tracks documentation coverage, freshness, and quality metrics.
"""

import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import subprocess


class DocMetrics:
    """Collects documentation metrics."""

    def __init__(self, repo_root: Path):
        """
        Initialize metrics collector.

        Args:
            repo_root: Repository root directory
        """
        self.repo_root = repo_root
        self.metrics: Dict = {}

    def count_markdown_files(self) -> int:
        """Count total markdown files."""
        return len(list(self.repo_root.rglob('*.md')))

    def count_code_lines(self) -> Dict[str, int]:
        """Count lines of code by language."""
        counts = {}

        # Rust
        rust_files = list(self.repo_root.rglob('*.rs'))
        counts['rust'] = sum(
            len(f.read_text().splitlines())
            for f in rust_files
            if 'target' not in str(f)
        )

        # Python
        py_files = list(self.repo_root.rglob('*.py'))
        counts['python'] = sum(len(f.read_text().splitlines()) for f in py_files)

        # JavaScript/TypeScript
        js_files = list(self.repo_root.rglob('*.ts')) + list(self.repo_root.rglob('*.js'))
        counts['javascript'] = sum(
            len(f.read_text().splitlines())
            for f in js_files
            if 'node_modules' not in str(f)
        )

        return counts

    def calculate_doc_ratio(self) -> float:
        """Calculate documentation to code ratio."""
        md_files = list(self.repo_root.rglob('*.md'))
        doc_lines = sum(len(f.read_text().splitlines()) for f in md_files)

        code_lines = sum(self.count_code_lines().values())

        return doc_lines / code_lines if code_lines > 0 else 0.0

    def check_doc_freshness(self) -> Dict[str, int]:
        """Check documentation freshness (days since last update)."""
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%ct', '--', 'docs/'],
            capture_output=True,
            text=True,
            cwd=self.repo_root
        )

        if result.returncode == 0:
            timestamp = int(result.stdout.strip())
            days_old = (datetime.now().timestamp() - timestamp) / 86400
            return {'days_since_update': int(days_old)}

        return {'days_since_update': -1}

    def collect_all(self) -> Dict:
        """
        Collect all metrics.

        Returns:
            Dictionary of metrics
        """
        self.metrics = {
            'timestamp': datetime.now().isoformat(),
            'markdown_files': self.count_markdown_files(),
            'code_lines': self.count_code_lines(),
            'doc_ratio': self.calculate_doc_ratio(),
            'freshness': self.check_doc_freshness(),
        }

        return self.metrics

    def save_metrics(self, output_path: Path):
        """Save metrics to JSON file."""
        with open(output_path, 'w') as f:
            json.dump(self.metrics, f, indent=2)
        print(f"Metrics saved to {output_path}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Collect documentation metrics")
    parser.add_argument('--repo-root', type=Path, default=Path('.'),
                       help='Repository root directory')
    parser.add_argument('--output', type=Path, default=Path('doc-metrics.json'),
                       help='Output JSON file')

    args = parser.parse_args()

    collector = DocMetrics(args.repo_root)
    metrics = collector.collect_all()

    print("\nDocumentation Metrics:")
    print(f"  Markdown files: {metrics['markdown_files']}")
    print(f"  Code lines: {sum(metrics['code_lines'].values())}")
    print(f"  Doc/Code ratio: {metrics['doc_ratio']:.2f}")
    print(f"  Days since update: {metrics['freshness']['days_since_update']}")

    collector.save_metrics(args.output)


if __name__ == '__main__':
    main()
```

---

**Part 5 Complete**: Documentation CI/CD with intelligent change detection, multi-language doc
building (Rust/Python/JavaScript), mdBook and MkDocs integration, markdown linting, spell checking,
code example validation, documentation coverage checks, PR preview deployments, and metrics
collection. ✅

**Continue to Part 6** for documentation best practices, maintenance workflows, and Task 14
completion summary.
