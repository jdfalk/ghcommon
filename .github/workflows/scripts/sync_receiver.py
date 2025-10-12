#!/usr/bin/env python3
"""Utilities for the sync-receiver workflow."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import time
from pathlib import Path


def append_to_file(path_env: str, content: str) -> None:
    file_path = os.environ.get(path_env)
    if not file_path:
        return
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "a", encoding="utf-8") as handle:
        handle.write(content)


def write_output(name: str, value: str) -> None:
    append_to_file("GITHUB_OUTPUT", f"{name}={value}\n")


def set_parameters(_: argparse.Namespace) -> None:
    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    if event_name == "repository_dispatch":
        sync_type = os.environ.get("CLIENT_PAYLOAD_SYNC_TYPE", "all")
        source_repo = os.environ.get("CLIENT_PAYLOAD_SOURCE_REPO", "")
        source_sha = os.environ.get("CLIENT_PAYLOAD_SOURCE_SHA", "")
        force_sync = os.environ.get("CLIENT_PAYLOAD_FORCE_SYNC", "false")
        verbose_logging = os.environ.get("CLIENT_PAYLOAD_VERBOSE_LOGGING", "true")
    else:
        sync_type = os.environ.get("INPUT_SYNC_TYPE", "all")
        source_repo = os.environ.get("INPUT_SOURCE_REPO", "jdfalk/ghcommon")
        source_sha = os.environ.get("INPUT_SOURCE_SHA", "manual-dispatch")
        force_sync = os.environ.get("INPUT_FORCE_SYNC", "false")
        verbose_logging = os.environ.get("INPUT_VERBOSE_LOGGING", "true")

    write_output("sync_type", sync_type)
    write_output("source_repo", source_repo or "jdfalk/ghcommon")
    write_output("source_sha", source_sha or "manual-dispatch")
    write_output("force_sync", force_sync)
    write_output("verbose_logging", verbose_logging)


def install_python_deps(_: argparse.Namespace) -> None:
    print("🐍 Installing Python dependencies for sync script...")
    subprocess.run(["pip3", "install", "pyyaml"], check=True)


def _copy_directory(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for file in sorted(source.iterdir()):
        if file.is_file():
            shutil.copy(file, destination / file.name)
            print(f"✅ Copied {file.name}")


def sync_files(_: argparse.Namespace) -> None:
    sync_type = os.environ.get("SYNC_TYPE", "all")
    verbose_logging = os.environ.get("SYNC_VERBOSE", "true").lower() == "true"
    pat_token = os.environ.get("PAT_TOKEN")
    repo_owner = os.environ.get("GITHUB_REPOSITORY_OWNER", "")
    repo_name = os.environ.get("GITHUB_REPOSITORY_NAME", "")

    print(f"🔄 Performing sync of type: {sync_type}")
    print(f"📊 Verbose logging: {verbose_logging}")

    source_root = Path("ghcommon-source")
    if verbose_logging and source_root.exists():
        print("📁 Source directory contents:")
        for path in sorted(source_root.iterdir()):
            print(f"- {path.name}")

    command = ["python3", ".github/scripts/sync-receiver-sync-files.py", sync_type]
    result = subprocess.run(command)
    if result.returncode == 0:
        shutil.rmtree(source_root, ignore_errors=True)
        print("✅ Sync operation completed")
        return

    print("❌ Python sync script failed, trying manual sync...")
    print("📁 Creating directory structure...")
    (Path(".github/workflows")).mkdir(parents=True, exist_ok=True)
    (Path(".github/instructions")).mkdir(parents=True, exist_ok=True)
    (Path(".github/prompts")).mkdir(parents=True, exist_ok=True)
    Path("scripts").mkdir(parents=True, exist_ok=True)
    (Path(".github/scripts")).mkdir(parents=True, exist_ok=True)
    (Path(".github/linters")).mkdir(parents=True, exist_ok=True)

    if sync_type in {"all", "workflows"}:
        print("🔄 Processing workflows section...")
        print("⚠️  Skipping workflow files due to GitHub App permission limitations")

    if sync_type in {"all", "instructions"}:
        print("🔄 Processing instructions section...")
        instructions_root = source_root / ".github" / "instructions"
        copilot_instructions = source_root / ".github" / "copilot-instructions.md"
        if copilot_instructions.is_file():
            shutil.copy(copilot_instructions, Path(".github") / "copilot-instructions.md")
            print("✅ Copied copilot-instructions.md")
        if instructions_root.exists():
            _copy_directory(instructions_root, Path(".github/instructions"))

    if sync_type in {"all", "prompts"}:
        print("🔄 Processing prompts section...")
        prompts_root = source_root / ".github" / "prompts"
        if prompts_root.exists():
            _copy_directory(prompts_root, Path(".github/prompts"))

    if sync_type in {"all", "scripts", "github-scripts"}:
        print("🔄 Processing scripts section...")
        scripts_root = source_root / "scripts"
        github_scripts_root = source_root / ".github" / "scripts"
        if scripts_root.exists():
            _copy_directory(scripts_root, Path("scripts"))
        if github_scripts_root.exists():
            _copy_directory(github_scripts_root, Path(".github/scripts"))

    if sync_type in {"all", "linters"}:
        print("🔄 Processing linters section...")
        linters_root = source_root / ".github" / "linters"
        if linters_root.exists():
            for file in sorted(linters_root.iterdir()):
                if not file.is_file():
                    continue
                filename = file.name
                if filename in {
                    "rustfmt.toml",
                    "clippy.toml",
                    ".markdownlint.json",
                    ".yaml-lint.yml",
                } or filename.startswith("super-linter-"):
                    shutil.copy(file, Path(".") / filename)
                else:
                    shutil.copy(file, Path(".github/linters") / filename)
                print(f"✅ Copied {filename}")
            print("✅ Linter configuration files available in root directory")

    if sync_type in {"all", "labels"}:
        print("🔄 Processing labels section...")
        labels_json = source_root / "labels.json"
        labels_md = source_root / "labels.md"
        sync_script = source_root / "scripts" / "sync-github-labels.py"
        if labels_json.is_file():
            shutil.copy(labels_json, Path("labels.json"))
            print("✅ Copied labels.json")
        if labels_md.is_file():
            shutil.copy(labels_md, Path("labels.md"))
            print("✅ Copied labels.md")
        if sync_script.is_file():
            shutil.copy(sync_script, Path("scripts") / "sync-github-labels.py")
            print("✅ Copied sync-github-labels.py")

        if sync_type in {"labels", "all"} and repo_owner and repo_name:
            print("🏷️  Attempting to sync GitHub repository labels...")
            env = os.environ.copy()
            if pat_token:
                env["GITHUB_TOKEN"] = pat_token
            result = subprocess.run(
                ["python3", "scripts/sync-github-labels.py", repo_owner, repo_name],
                env=env,
                check=False,
            )
            if result.returncode == 0:
                print("✅ Successfully synced GitHub repository labels")
            else:
                print("⚠️  GitHub label sync failed, but file sync completed")
                print("💡 This may be due to insufficient token permissions")

    shutil.rmtree(source_root, ignore_errors=True)
    print("✅ Sync operation completed")


def check_changes(_: argparse.Namespace) -> None:
    force_sync = os.environ.get("FORCE_SYNC", "false").lower() == "true"
    print("🔍 Checking for changes...")
    print(f"🔧 Force sync enabled: {force_sync}")

    diff_result = subprocess.run(["git", "diff", "--quiet"], check=False)
    has_changes = diff_result.returncode != 0

    if not has_changes and not force_sync:
        write_output("has_changes", "false")
        print("ℹ️  No changes detected and force sync not enabled")
        print("📊 Git status:")
        subprocess.run(["git", "status", "--porcelain"], check=False)
        return

    write_output("has_changes", "true")
    if force_sync:
        print("🔧 Force sync enabled - proceeding with commit")
    else:
        print("✅ Changes detected - proceeding with commit")
    print("📋 Files that will be committed:")
    subprocess.run(["git", "diff", "--name-only"], check=False)
    print("📊 Detailed git status:")
    subprocess.run(["git", "status", "--porcelain"], check=False)
    print("📝 Git diff summary:")
    subprocess.run(["git", "diff", "--stat"], check=False)


def commit_and_push(_: argparse.Namespace) -> None:
    source_repo = os.environ.get("SOURCE_REPO", "")
    source_sha = os.environ.get("SOURCE_SHA", "")
    sync_type = os.environ.get("SYNC_TYPE", "")

    subprocess.run(["git", "config", "--local", "user.email", "action@github.com"], check=True)
    subprocess.run(["git", "config", "--local", "user.name", "GitHub Action"], check=True)

    print("🔄 Pulling latest changes from remote...")
    pull_result = subprocess.run(["git", "pull", "origin", "main"], check=False)
    if pull_result.returncode != 0:
        print("⚠️  Pull failed, attempting rebase...")
        rebase_result = subprocess.run(["git", "pull", "--rebase", "origin", "main"], check=False)
        if rebase_result.returncode != 0:
            print("❌ Rebase failed, attempting merge strategy...")
            merge_result = subprocess.run(
                ["git", "pull", "--no-rebase", "--strategy-option=ours", "origin", "main"],
                check=False,
            )
            if merge_result.returncode != 0:
                print("❌ All pull strategies failed. Manual intervention may be required.")
                raise SystemExit(1)

    subprocess.run(["git", "add", "."], check=True)
    commit_message = (
        "sync: update files from ghcommon\n\n"
        f"Source: {source_repo}\n"
        f"SHA: {source_sha}\n"
        f"Sync type: {sync_type}"
    )
    subprocess.run(["git", "commit", "-m", commit_message], check=True)

    print("⬆️  Pushing changes to remote...")
    for attempt in range(1, 4):
        push_result = subprocess.run(["git", "push"], check=False)
        if push_result.returncode == 0:
            print("✅ Successfully pushed changes")
            break
        print(f"⚠️  Push attempt {attempt} failed, pulling latest changes and retrying...")
        rebase_pull = subprocess.run(["git", "pull", "--rebase", "origin", "main"], check=False)
        if rebase_pull.returncode != 0:
            subprocess.run(["git", "pull", "origin", "main"], check=False)
        if attempt == 3:
            print("❌ Failed to push after 3 attempts")
            raise SystemExit(1)
        time.sleep(2)


def write_summary(_: argparse.Namespace) -> None:
    sync_type = os.environ.get("SYNC_TYPE", "")
    source_repo = os.environ.get("SOURCE_REPO", "")
    source_sha = os.environ.get("SOURCE_SHA", "")
    force_sync = os.environ.get("FORCE_SYNC", "false")
    verbose_logging = os.environ.get("VERBOSE_LOGGING", "true")
    has_changes = os.environ.get("HAS_CHANGES", "false")

    append_to_file(
        "GITHUB_STEP_SUMMARY",
        (
            "## 📊 Sync Receiver Summary\n"
            f"- **Sync Type:** {sync_type}\n"
            f"- **Source Repo:** {source_repo}\n"
            f"- **Source SHA:** {source_sha}\n"
            f"- **Force Sync:** {force_sync}\n"
            f"- **Verbose Logging:** {verbose_logging}\n"
            f"- **Changes Made:** {has_changes}\n"
        ),
    )

    if has_changes == "true":
        result = subprocess.run(["git", "diff", "--name-only"], capture_output=True, text=True, check=False)
        lines = "".join(f"- `{line}`\n" for line in result.stdout.splitlines() if line)
        if lines:
            append_to_file("GITHUB_STEP_SUMMARY", "\n### 📋 Files Modified:\n" + lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync receiver helper commands.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    commands = {
        "set-parameters": set_parameters,
        "install-python-deps": install_python_deps,
        "sync-files": sync_files,
        "check-changes": check_changes,
        "commit-and-push": commit_and_push,
        "write-summary": write_summary,
    }

    for command, handler in commands.items():
        subparsers.add_parser(command).set_defaults(handler=handler)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        raise SystemExit(1)
    handler(args)


if __name__ == "__main__":
    main()
