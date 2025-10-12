#!/usr/bin/env python3
"""Configure Cargo to publish using GitHub Packages."""

from __future__ import annotations

import os
from pathlib import Path

CONFIG_TEMPLATE = """[registries.github]
index = "sparse+https://api.github.com/{repository}/cargo/"

[registry]
default = "github"

[net]
git-fetch-with-cli = true
"""

CREDENTIALS_TEMPLATE = """[registries.github]
token = "{token}"
"""


def main() -> None:
    repository = os.environ["GITHUB_REPOSITORY"]
    token = os.environ["CARGO_REGISTRY_TOKEN"]

    cargo_dir = Path.home() / ".cargo"
    cargo_dir.mkdir(parents=True, exist_ok=True)

    config_path = cargo_dir / "config.toml"
    config_path.write_text(CONFIG_TEMPLATE.format(repository=repository), encoding="utf-8")

    credentials_path = cargo_dir / "credentials.toml"
    credentials_path.write_text(CREDENTIALS_TEMPLATE.format(token=token), encoding="utf-8")
    credentials_path.chmod(0o600)

    print(f"Configured Cargo registry credentials at {credentials_path}")


if __name__ == "__main__":
    main()
