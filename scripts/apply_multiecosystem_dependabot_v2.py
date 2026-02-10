#!/usr/bin/env python3
"""Apply multi-ecosystem Dependabot configuration to repositories.

Applies consolidated multi-ecosystem-groups Dependabot config to all jdfalk repositories.
Version: 1.0.0
"""

import json
import sys
from pathlib import Path

REPOS_BASE = Path("/Users/jdfalk/repos/github.com/jdfalk")
SCHEDULE_DAY = "tuesday"
SCHEDULE_TIME = "10:00"
TIMEZONE = "America/New_York"

# Ecosystem detection: map file/dir patterns to package-ecosystem
ECOSYSTEM_DETECTORS = {
    "github-actions": [".github/workflows/*.yml", ".github/workflows/*.yaml"],
    "devcontainers": [".devcontainers/devcontainer.json", ".devcontainers/devcontainer.yml"],
    "docker": ["Dockerfile", "Dockerfile.*"],
    "docker-compose": ["docker-compose.yml", "docker-compose.yaml"],
    "gitsubmodule": [".gitmodules"],
    "gomod": ["go.mod"],
    "npm": ["package.json"],
    "rust-toolchain": ["rust-toolchain", "rust-toolchain.toml"],
    "cargo": ["Cargo.toml"],
    "uv": ["pyproject.toml", "uv.lock"],
    "pip": ["requirements.txt", "requirements*.txt"],
}

ECOSYSTEM_LABELS = {
    "github-actions": ["github-actions", "ci-cd"],
    "devcontainers": ["devcontainers"],
    "docker": ["containers"],
    "docker-compose": ["containers"],
    "gitsubmodule": ["submodules"],
    "gomod": ["tech:go"],
    "npm": ["tech:nodejs"],
    "rust-toolchain": ["tech:rust"],
    "cargo": ["tech:rust"],
    "uv": ["tech:python"],
    "pip": ["tech:python"],
}

ECOSYSTEM_IGNORE_SEMVER_MAJOR = {"npm", "cargo", "uv", "pip"}

ECOSYSTEM_SCHEDULES = {
    "devcontainers": {"interval": "monthly"},
    "docker": {"interval": "monthly"},
    "docker-compose": {"interval": "monthly"},
    "gitsubmodule": {"interval": "monthly", "day": "tuesday"},
    "rust-toolchain": {"interval": "monthly"},
}


def detect_ecosystems(repo_path: Path) -> list[str]:
    """Detect which package ecosystems are present in the repository."""
    detected = set()

    for ecosystem, patterns in ECOSYSTEM_DETECTORS.items():
        for pattern in patterns:
            # Handle glob patterns
            if "*" in pattern:
                dir_part = pattern.split("*")[0].rstrip("/")
                search_dir = repo_path / dir_part
                if search_dir.exists():
                    # For .github/workflows, check if any yml/yaml files exist
                    if ecosystem == "github-actions":
                        workflows_dir = repo_path / ".github" / "workflows"
                        if workflows_dir.exists() and (
                            any(workflows_dir.glob("*.yml")) or any(workflows_dir.glob("*.yaml"))
                        ):
                            detected.add(ecosystem)
                    elif ecosystem == "pip":
                        # Check for any requirements*.txt
                        if any(repo_path.glob("requirements*.txt")):
                            detected.add(ecosystem)
            elif (repo_path / pattern).exists():
                # Exact file match
                detected.add(ecosystem)

    return sorted(detected)


def build_ecosystem_entries(ecosystems: list[str]) -> str:
    """Build YAML ecosystem entries for detected ecosystems."""
    entries = []

    for ecosystem in ecosystems:
        labels = ECOSYSTEM_LABELS.get(ecosystem, [])
        label_yaml = "\n".join([f"      - {label}" for label in labels])

        # Determine directory
        directory = "/"

        schedule_yaml = ""
        if ecosystem in ECOSYSTEM_SCHEDULES:
            sched = ECOSYSTEM_SCHEDULES[ecosystem]
            schedule_yaml = "\n    schedule:"
            for key, val in sched.items():
                if key == "interval":
                    schedule_yaml += f"\n      interval: {val}"
                elif key == "day":
                    schedule_yaml += f"\n      day: {val}"

        ignore_yaml = ""
        if ecosystem in ECOSYSTEM_IGNORE_SEMVER_MAJOR:
            ignore_yaml = """
    ignore:
      - dependency-name: "*"
        update-types:
          - version-update:semver-major"""

        entry = f"""  # {ecosystem.replace("-", " ").title()}
  - package-ecosystem: {ecosystem}
    directory: {directory}
    patterns: ["*"]
    multi-ecosystem-group: dependencies
    labels:
{label_yaml}{schedule_yaml}{ignore_yaml}
"""
        entries.append(entry)

    return "\n".join(entries)


def build_dependabot_config(ecosystems: list[str]) -> str:
    """Build complete dependabot.yml content."""
    ecosystem_entries = build_ecosystem_entries(ecosystems)

    return f"""# Dependabot Configuration
# version: 1.0.0
# guid: a1b2c3d4-e5f6-7890-abcd-ef1234567890

version: 2

multi-ecosystem-groups:
  dependencies:
    schedule:
      interval: weekly
      day: {SCHEDULE_DAY}
      time: "{SCHEDULE_TIME}"
      timezone: {TIMEZONE}
    labels:
      - dependencies
      - dependabot
    commit-message:
      prefix: deps
      include: scope

updates:
{ecosystem_entries}
"""


def process_repository(repo_path: Path) -> dict:
    """Process a single repository, detect ecosystems and generate config."""
    repo_name = repo_path.name

    # Skip certain directories
    if repo_name in {"release-protobuf-action.worktrees"}:
        return {"repo": repo_name, "status": "skipped", "reason": "worktree"}

    # Check if repo has .git
    if not (repo_path / ".git").exists():
        return {"repo": repo_name, "status": "skipped", "reason": "not a git repo"}

    # Detect ecosystems
    ecosystems = detect_ecosystems(repo_path)

    if not ecosystems:
        return {
            "repo": repo_name,
            "status": "skipped",
            "reason": "no compatible ecosystems detected",
        }

    # Build config
    config = build_dependabot_config(ecosystems)

    # Write config
    config_path = repo_path / ".github" / "dependabot.yml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(config)

    return {
        "repo": repo_name,
        "status": "updated",
        "ecosystems": ecosystems,
        "config_path": str(config_path),
    }


def main() -> int:
    """Main entry point."""
    print("🔄 Applying multi-ecosystem Dependabot config to all repositories...\n")

    results = {
        "updated": 0,
        "skipped": 0,
        "errors": 0,
        "details": [],
    }

    # Get all repo directories
    if not REPOS_BASE.exists():
        print(f"❌ Repos directory not found: {REPOS_BASE}")
        return 1

    repos = sorted([d for d in REPOS_BASE.iterdir() if d.is_dir()])
    print(f"📦 Found {len(repos)} potential repositories\n")

    for repo_path in repos:
        try:
            result = process_repository(repo_path)
            results["details"].append(result)

            if result["status"] == "updated":
                results["updated"] += 1
                ecosystems = ", ".join(result["ecosystems"])
                print(f"✅ {result['repo']:<40} [{ecosystems}]")
            elif result["status"] == "skipped":
                results["skipped"] += 1
                print(f"⏭️  {result['repo']:<40} ({result['reason']})")
        except Exception as e:
            results["errors"] += 1
            results["details"].append(
                {
                    "repo": repo_path.name,
                    "status": "error",
                    "error": str(e),
                }
            )
            print(f"❌ {repo_path.name:<40} ERROR: {e}")

    # Summary
    print("\n📊 Summary:")
    print(f"  ✅ Updated: {results['updated']}")
    print(f"  ⏭️  Skipped: {results['skipped']}")
    print(f"  ❌ Errors: {results['errors']}")

    # Save detailed results
    home = Path.home()
    results_file = home / "dependabot_update_results.json"
    results_file.write_text(json.dumps(results, indent=2))
    print(f"\n📝 Detailed results saved to: {results_file}")

    return 0 if results["errors"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
