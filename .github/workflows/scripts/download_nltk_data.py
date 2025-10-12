#!/usr/bin/env python3
"""Download required NLTK datasets."""

from __future__ import annotations

import os

PACKAGES = ["punkt", "stopwords", "vader_lexicon"]


def main() -> None:
    if os.environ.get("NLTK_SKIP_DOWNLOAD") == "1":
        print("Skipping NLTK downloads (NLTK_SKIP_DOWNLOAD=1)")
        return

    try:
        import nltk
    except ImportError as exc:  # pragma: no cover
        print(f"::error::Failed to import nltk: {exc}")
        raise SystemExit(1)

    data_dir = os.environ.get("NLTK_DATA_HOME")
    if data_dir:
        nltk.data.path.append(data_dir)

    for package in PACKAGES:
        print(f"Downloading NLTK package: {package}")
        nltk.download(package, quiet=True)


if __name__ == "__main__":
    main()
