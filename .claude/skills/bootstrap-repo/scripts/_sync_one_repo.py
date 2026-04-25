#!/usr/bin/env python3
"""Run ghcommon's RepoSetupSyncer.sync_repository() against a single target.

ghcommon's `sync-repo-setup.py` only exposes `sync_all_repositories()` via its
CLI, which auto-discovers all repos. We need a single-target flow for bootstrap.
This shim imports the existing class and calls the existing per-repo method,
without modifying ghcommon's script.

Usage:
    _sync_one_repo.py <ghcommon_path> <target_repo_path>
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def load_syncer_module(ghcommon: Path):
    script = ghcommon / "scripts" / "sync-repo-setup.py"
    spec = importlib.util.spec_from_file_location("sync_repo_setup", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(f"usage: {argv[0]} <ghcommon_path> <target_repo_path>", file=sys.stderr)
        return 2
    ghcommon = Path(argv[1]).resolve()
    target = Path(argv[2]).resolve()
    if not (ghcommon / "scripts" / "sync-repo-setup.py").is_file():
        print(f"error: ghcommon sync-repo-setup.py not found under {ghcommon}", file=sys.stderr)
        return 1
    if not target.is_dir():
        print(f"error: target not a directory: {target}", file=sys.stderr)
        return 1

    module = load_syncer_module(ghcommon)
    syncer = module.RepoSetupSyncer(source_repo=ghcommon, dry_run=False)
    result = syncer.sync_repository(target_repo=target)
    print(f"sync result: {result.get('repo_name')}: {result.get('status', 'ok')}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
