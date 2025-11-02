#!/usr/bin/env python3
"""Write Go module metadata JSON for release automation."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    module_path = os.environ["MODULE_PATH"]
    module_version = os.environ["MODULE_VERSION"]
    repository = os.environ["REPOSITORY"]
    tag_name = os.environ["TAG_NAME"]
    commit_sha = os.environ["COMMIT_SHA"]

    payload = {
        "module": module_path,
        "version": f"v{module_version}",
        "repository": repository,
        "commit": commit_sha,
        "tag": tag_name,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    output_path = Path("module-metadata.json")
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {output_path}")

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as handle:
            handle.write(f"metadata-file={output_path}\n")


if __name__ == "__main__":
    main()
