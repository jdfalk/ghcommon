#!/usr/bin/env python3
"""Upsert an entry into the bootstrapped-repos registry.

Lives at `${GHCOMMON}/.github/bootstrapped-repos.json`. Records every repo
that has been through `bootstrap_repo.sh` so we can iterate the set later
(drift sweeps, mass standards updates, etc).

Schema:
    {"version": 1, "repos": [{owner, name, flavor, mode, first_bootstrapped, last_bootstrapped}, ...]}

Idempotent: an existing (owner, name) pair has its `flavor`, `mode`, and
`last_bootstrapped` updated; `first_bootstrapped` is preserved.

Usage:
    _update_registry.py --registry PATH --owner OWNER --name NAME \\
                        --flavor FLAVOR --mode MODE
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

SCHEMA_VERSION = 1


def load_registry(path: Path) -> dict:
    if not path.exists():
        return {"version": SCHEMA_VERSION, "repos": []}
    with path.open() as f:
        data = json.load(f)
    data.setdefault("version", SCHEMA_VERSION)
    data.setdefault("repos", [])
    return data


def upsert(data: dict, owner: str, name: str, flavor: str, mode: str) -> dict:
    now = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    for entry in data["repos"]:
        if entry.get("owner") == owner and entry.get("name") == name:
            entry["flavor"] = flavor
            entry["mode"] = mode
            entry["last_bootstrapped"] = now
            return data
    data["repos"].append(
        {
            "owner": owner,
            "name": name,
            "flavor": flavor,
            "mode": mode,
            "first_bootstrapped": now,
            "last_bootstrapped": now,
        }
    )
    data["repos"].sort(key=lambda e: (e.get("owner", ""), e.get("name", "")))
    return data


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--owner", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--flavor", required=True)
    parser.add_argument("--mode", required=True)
    args = parser.parse_args(argv[1:])

    args.registry.parent.mkdir(parents=True, exist_ok=True)
    data = load_registry(args.registry)
    data = upsert(data, args.owner, args.name, args.flavor, args.mode)
    with args.registry.open("w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
