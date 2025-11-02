import argparse
import subprocess

import sync_receiver


def test_set_parameters_repo_dispatch(tmp_path, monkeypatch):
    output_path = tmp_path / "output.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_path))
    monkeypatch.setenv("GITHUB_EVENT_NAME", "repository_dispatch")
    monkeypatch.setenv("CLIENT_PAYLOAD_SYNC_TYPE", "scripts")
    monkeypatch.setenv("CLIENT_PAYLOAD_SOURCE_REPO", "upstream/repo")
    monkeypatch.setenv("CLIENT_PAYLOAD_SOURCE_SHA", "deadbeef")
    monkeypatch.setenv("CLIENT_PAYLOAD_FORCE_SYNC", "true")
    monkeypatch.setenv("CLIENT_PAYLOAD_VERBOSE_LOGGING", "false")

    sync_receiver.set_parameters(argparse.Namespace())
    result = dict(
        line.split("=", 1) for line in output_path.read_text().splitlines()
    )
    assert result["sync_type"] == "scripts"
    assert result["source_repo"] == "upstream/repo"
    assert result["force_sync"] == "true"


def test_sync_files_fallback_copies_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source_root = tmp_path / "ghcommon-source"
    (source_root / ".github" / "instructions").mkdir(
        parents=True, exist_ok=True
    )
    (source_root / ".github" / "instructions" / "guide.md").write_text(
        "# Guide", encoding="utf-8"
    )
    (source_root / ".github" / "prompts").mkdir(parents=True, exist_ok=True)
    (source_root / ".github" / "prompts" / "prompt.txt").write_text(
        "Prompt", encoding="utf-8"
    )
    (source_root / "scripts").mkdir(parents=True, exist_ok=True)
    (source_root / "scripts" / "tool.py").write_text(
        "print('tool')", encoding="utf-8"
    )
    (source_root / ".github" / "scripts").mkdir(parents=True, exist_ok=True)
    (source_root / ".github" / "scripts" / "helper.py").write_text(
        "print('helper')", encoding="utf-8"
    )
    linters_root = source_root / ".github" / "linters"
    linters_root.mkdir(parents=True, exist_ok=True)
    (linters_root / "clippy.toml").write_text("content", encoding="utf-8")
    (linters_root / "extra.yml").write_text("yaml: true", encoding="utf-8")
    (source_root / "labels.json").write_text("{}", encoding="utf-8")
    (source_root / "labels.md").write_text("# labels", encoding="utf-8")
    (source_root / "scripts" / "sync-github-labels.py").write_text(
        "print('labels')", encoding="utf-8"
    )

    def fake_run(cmd, check=False, **kwargs):
        if cmd[:3] == [
            "python3",
            ".github/scripts/sync-receiver-sync-files.py",
            "all",
        ]:
            return subprocess.CompletedProcess(cmd, 1)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setenv("SYNC_TYPE", "all")
    monkeypatch.setenv("SYNC_VERBOSE", "true")
    monkeypatch.setenv("PAT_TOKEN", "token")
    monkeypatch.setenv("GITHUB_REPOSITORY_OWNER", "owner")
    monkeypatch.setenv("GITHUB_REPOSITORY_NAME", "repo")
    monkeypatch.setattr(sync_receiver.subprocess, "run", fake_run)

    sync_receiver.sync_files(argparse.Namespace())
    assert (tmp_path / ".github" / "instructions" / "guide.md").is_file()
    assert (tmp_path / ".github" / "scripts" / "helper.py").is_file()
    assert (tmp_path / "scripts" / "tool.py").is_file()
    assert (tmp_path / ".github" / "linters" / "extra.yml").is_file()
    assert (tmp_path / "clippy.toml").is_file()
    assert (tmp_path / "labels.json").is_file()
    assert not source_root.exists()


def test_check_changes_detects_changes(tmp_path, monkeypatch):
    output_path = tmp_path / "output.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_path))
    monkeypatch.setenv("FORCE_SYNC", "false")

    def fake_run(cmd, check=False, **kwargs):
        if cmd == ["git", "diff", "--quiet"]:
            return subprocess.CompletedProcess(cmd, 1)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(sync_receiver.subprocess, "run", fake_run)
    sync_receiver.check_changes(argparse.Namespace())
    assert "has_changes=true" in output_path.read_text()


def test_commit_and_push_success(monkeypatch):
    commands = []

    def fake_run(cmd, check=False, **kwargs):
        commands.append(tuple(cmd))
        if cmd[:2] == ["git", "push"]:
            return subprocess.CompletedProcess(cmd, 0)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(sync_receiver.subprocess, "run", fake_run)
    monkeypatch.setenv("SOURCE_REPO", "upstream/repo")
    monkeypatch.setenv("SOURCE_SHA", "abc123")
    monkeypatch.setenv("SYNC_TYPE", "scripts")

    sync_receiver.commit_and_push(argparse.Namespace())
    push_commands = [cmd for cmd in commands if cmd[:2] == ("git", "push")]
    assert push_commands


def test_write_summary_with_changes(tmp_path, monkeypatch):
    summary_path = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_path))
    monkeypatch.setenv("SYNC_TYPE", "scripts")
    monkeypatch.setenv("SOURCE_REPO", "upstream/repo")
    monkeypatch.setenv("SOURCE_SHA", "abc123")
    monkeypatch.setenv("FORCE_SYNC", "false")
    monkeypatch.setenv("VERBOSE_LOGGING", "true")
    monkeypatch.setenv("HAS_CHANGES", "true")

    def fake_run(cmd, capture_output=False, text=False, **kwargs):
        if capture_output and cmd == ["git", "diff", "--name-only"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="file.txt\n")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(sync_receiver.subprocess, "run", fake_run)
    sync_receiver.write_summary(argparse.Namespace())
    content = summary_path.read_text()
    assert "Sync Receiver Summary" in content
    assert "- `file.txt`" in content
