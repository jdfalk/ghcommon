#!/usr/bin/env python3
# file: .github/workflows/scripts/generate_release_summary.py
# version: 1.1.0
# guid: 9346b0d8-53f0-4a7e-95ff-bae25b782f6d

"""Generate GitHub Actions release summary from environment variables."""

from __future__ import annotations

import os
from collections import OrderedDict

from workflow_common import (
    append_summary,
    append_summary_line,
    build_release_summary,
    log_warning,
)


def _flag(name: str) -> bool:
    return os.environ.get(name, "false").lower() == "true"


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def main() -> None:
    components = OrderedDict(
        [
            ("Go", _env("SUMMARY_GO_RESULT", "skipped")),
            ("Python", _env("SUMMARY_PYTHON_RESULT", "skipped")),
            ("Rust", _env("SUMMARY_RUST_RESULT", "skipped")),
            ("Frontend", _env("SUMMARY_FRONTEND_RESULT", "skipped")),
            ("Docker", _env("SUMMARY_DOCKER_RESULT", "skipped")),
            ("Release", _env("SUMMARY_RELEASE_RESULT", "skipped")),
            (
                "GitHub Packages",
                _env("SUMMARY_PUBLISH_RESULT", "skipped"),
            ),
        ]
    )

    context = {
        "primary_language": _env("SUMMARY_PRIMARY_LANGUAGE", "unknown"),
        "build_target": _env("SUMMARY_BUILD_TARGET", "all"),
        "release_tag": _env("SUMMARY_RELEASE_TAG", "n/a"),
        "release_strategy": _env("SUMMARY_RELEASE_STRATEGY", "n/a"),
        "branch": _env("SUMMARY_BRANCH", "n/a"),
        "components": components,
        "release_created": _flag("SUMMARY_RELEASE_CREATED"),
        "auto_prerelease": _flag("SUMMARY_AUTO_PRERELEASE"),
        "auto_draft": _flag("SUMMARY_AUTO_DRAFT"),
    }

    append_summary(build_release_summary(context))

    failures = any(status.lower() == "failure" for status in components.values())
    if failures:
        append_summary_line("❌ **Some components failed**")
        log_warning("Some components failed - check the summary above")
        # Don't exit with error code - let the CI summary job determine overall status
    else:
        append_summary_line("✅ **All components completed successfully**")


if __name__ == "__main__":
    main()
