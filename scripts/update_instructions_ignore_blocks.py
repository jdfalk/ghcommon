#!/usr/bin/env python3
# file: scripts/update_instructions_ignore_blocks.py
# version: 1.0.1
# guid: 7f3c9a3e-1b2c-4d5e-8f90-abc123def456

"""Batch-update .github/instructions/*.instructions.md files across repositories to:
1) Wrap the YAML frontmatter (applyTo/description) block with ignore markers:
   <!-- prettier-ignore-start --> / <!-- prettier-ignore-end -->
   <!-- markdownlint-disable --> / <!-- markdownlint-enable -->
2) Bump the version header (HTML comment: <!-- version: x.y.z -->) by a patch version.

Safety:
- Skips files already wrapped (detects 'prettier-ignore-start' near frontmatter)
- Preserves content and spacing
"""

from __future__ import annotations

import os
import re
from pathlib import Path

WORKSPACE_REPOS = [
    "subtitle-manager",
    "gcommon",
    "autoinstall-dir",
    "apt-cacher-go",
    "audiobook-organizer",
    "copilot-agent-util-rust",
    "ghcommon",
    "public-scratch",
    "ubuntu-autoinstall-webhook",
]

# Base path to the local workspace repositories (use environment variable or detect from script location)
ROOT = Path(os.getenv("REPO_BASE_DIR", Path(__file__).parent.parent.parent.resolve()))


def bump_version_header(text: str) -> tuple[str, bool]:
    """Bump <!-- version: x.y.z --> to x.y.(z+1). Returns (new_text, changed)."""
    m = re.search(r"(<!--\s*version:\s*)(\d+)\.(\d+)\.(\d+)(\s*-->)", text)
    if not m:
        return text, False
    major, minor, patch = int(m.group(2)), int(m.group(3)), int(m.group(4))
    new = f"{m.group(1)}{major}.{minor}.{patch + 1}{m.group(5)}"
    start, end = m.span()
    return text[:start] + new + text[end:], True


def already_wrapped(lines: list[str], fm_start_idx: int) -> bool:
    # Check a few lines before frontmatter for existing markers
    look_back = max(0, fm_start_idx - 4)
    window = "\n".join(lines[look_back : fm_start_idx + 1]).lower()
    return "prettier-ignore-start" in window or "markdownlint-disable" in window


def wrap_frontmatter(text: str) -> tuple[str, bool]:
    lines = text.splitlines()
    # Find first frontmatter block delimited by --- ... --- starting near top
    fm_start = None
    for i, line in enumerate(lines[:50]):
        if line.strip() == "---":
            fm_start = i
            break
    if fm_start is None:
        return text, False
    # Find closing --- after start
    fm_end = None
    for j in range(fm_start + 1, min(len(lines), fm_start + 200)):
        if lines[j].strip() == "---":
            fm_end = j
            break
    if fm_end is None:
        return text, False

    if already_wrapped(lines, fm_start):
        return text, False

    start_markers = [
        "<!-- prettier-ignore-start -->",
        "<!-- markdownlint-disable -->",
    ]
    end_markers = [
        "<!-- markdownlint-enable -->",
        "<!-- prettier-ignore-end -->",
    ]

    # Insert above fm_start and below fm_end
    new_lines = (
        lines[:fm_start]
        + start_markers
        + lines[fm_start : fm_end + 1]
        + end_markers
        + lines[fm_end + 1 :]
    )
    return "\n".join(new_lines) + ("\n" if text.endswith("\n") else ""), True


def process_file(path: Path) -> bool:
    txt = path.read_text(encoding="utf-8")
    changed_any = False
    new_txt, fm_changed = wrap_frontmatter(txt)
    if fm_changed:
        changed_any = True
    new_txt, ver_changed = bump_version_header(new_txt)
    if ver_changed:
        changed_any = True
    if changed_any:
        path.write_text(new_txt, encoding="utf-8")
    return changed_any


def main() -> None:
    total = 0
    changed = 0
    for repo in WORKSPACE_REPOS:
        base = ROOT / repo
        for path in base.rglob(".github/instructions/*.instructions.md"):
            total += 1
            if process_file(path):
                changed += 1
                print(f"UPDATED: {path}")
    print(f"Done. {changed}/{total} files updated.")


if __name__ == "__main__":
    main()
