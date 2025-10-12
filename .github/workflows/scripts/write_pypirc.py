#!/usr/bin/env python3
"""Generate a ~/.pypirc file for publishing."""

from __future__ import annotations

import os
from pathlib import Path


def main() -> None:
    pypi_token = os.environ.get("PYPI_TOKEN", "")
    github_token = os.environ.get("GH_TOKEN", "")

    config_dir = Path.home() / ".config" / "pip"
    config_dir.mkdir(parents=True, exist_ok=True)

    pypirc_path = Path.home() / ".pypirc"
    content = (
        "[distutils]\n"
        "index-servers =\n"
        "    pypi\n"
        "    github\n\n"
        "[pypi]\n"
        "repository = https://upload.pypi.org/legacy/\n"
        "username = __token__\n"
        f"password = {pypi_token}\n\n"
        "[github]\n"
        "repository = https://upload.pypi.org/legacy/\n"
        "username = __token__\n"
        f"password = {github_token}\n"
    )
    pypirc_path.write_text(content, encoding="utf-8")
    pypirc_path.chmod(0o600)
    print(f"Wrote {pypirc_path}")


if __name__ == "__main__":
    main()
