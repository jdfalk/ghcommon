import argparse
import subprocess
from pathlib import Path
from typing import Any

import pytest

import ci_workflow


def test_debug_filter_outputs(monkeypatch, capsys):
    env_values = {
        "CI_GO_FILES": "true",
        "CI_FRONTEND_FILES": "false",
        "CI_PYTHON_FILES": "true",
        "CI_RUST_FILES": "false",
        "CI_DOCKER_FILES": "false",
        "CI_DOCS_FILES": "true",
        "CI_WORKFLOW_FILES": "true",
        "CI_LINT_FILES": "false",
    }
    for key, value in env_values.items():
        monkeypatch.setenv(key, value)

    ci_workflow.debug_filter(argparse.Namespace())
    output = capsys.readouterr().out
    assert "Go files changed: true" in output
    assert "Docs files changed: true" in output


def test_determine_execution_sets_outputs(tmp_path, monkeypatch):
    output_file = tmp_path / "output.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))
    monkeypatch.setenv("GITHUB_HEAD_COMMIT_MESSAGE", "fix bug [skip ci]")
    monkeypatch.setenv("CI_GO_FILES", "true")
    monkeypatch.setenv("CI_FRONTEND_FILES", "false")
    monkeypatch.setenv("CI_PYTHON_FILES", "true")
    monkeypatch.setenv("CI_RUST_FILES", "false")
    monkeypatch.setenv("CI_DOCKER_FILES", "true")

    ci_workflow.determine_execution(argparse.Namespace())
    lines = output_file.read_text().splitlines()
    assert "skip_ci=true" in lines
    assert "should_test_go=true" in lines
    assert "should_test_frontend=false" in lines


class DummyResponse:
    def __init__(self, status_code: int, payload: dict[str, Any]):
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict[str, Any]:
        return self._payload


def test_wait_for_pr_automation_completed(monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    monkeypatch.setenv("TARGET_SHA", "abc123")
    monkeypatch.setenv("WORKFLOW_NAME", "PR Automation")
    monkeypatch.setenv("MAX_ATTEMPTS", "1")

    def fake_get(url: str, **kwargs):
        assert "owner/repo" in url
        return DummyResponse(
            200,
            {
                "workflow_runs": [
                    {"head_sha": "abc123", "name": "PR Automation", "status": "completed"}
                ]
            },
        )

    monkeypatch.setattr(ci_workflow.requests, "get", fake_get)
    ci_workflow.wait_for_pr_automation(argparse.Namespace())
    captured = capsys.readouterr().out
    assert "✅ PR automation has completed" in captured


def test_load_super_linter_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "super-linter-ci.env").write_text("FOO=bar\n", encoding="utf-8")
    env_file = tmp_path / "env.txt"
    output_file = tmp_path / "output.txt"

    monkeypatch.setenv("EVENT_NAME", "push")
    monkeypatch.setenv("CI_ENV_FILE", "super-linter-ci.env")
    monkeypatch.setenv("PR_ENV_FILE", "super-linter-pr.env")
    monkeypatch.setenv("GITHUB_ENV", str(env_file))
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))

    ci_workflow.load_super_linter_config(argparse.Namespace())
    assert env_file.read_text() == "FOO=bar\n"
    assert "config-file=super-linter-ci.env" in output_file.read_text()


def test_go_setup_skips_without_go_mod(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    def fake_run(*args, **kwargs):  # pragma: no cover - should not be called
        raise AssertionError("go commands should not run")

    monkeypatch.setattr(ci_workflow.subprocess, "run", fake_run)
    ci_workflow.go_setup(argparse.Namespace())
    assert "skipping Go step" in capsys.readouterr().out


def test_go_test_runs_commands(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "go.mod").write_text("module example.com/test\n", encoding="utf-8")
    commands = []

    def fake_run(cmd, check=False, capture_output=False, text=False, **kwargs):
        commands.append((tuple(cmd), check, capture_output))
        if "-func" in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout="total: (statements) 75.0%\n")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setenv("COVERAGE_THRESHOLD", "70")
    monkeypatch.setattr(ci_workflow.subprocess, "run", fake_run)
    monkeypatch.setattr(ci_workflow.shutil, "which", lambda name: "go")

    ci_workflow.go_test(argparse.Namespace())
    go_commands = [cmd for cmd, *_ in commands if cmd and cmd[0] == "go"]
    assert any("test" in cmd for cmd in go_commands)
    assert any("tool" in cmd for cmd in go_commands)


def test_python_run_tests_skips_when_no_tests(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "requirements.txt").write_text("pytest\n", encoding="utf-8")
    commands = []

    def fake_run(cmd, check=False, **kwargs):
        commands.append(tuple(cmd))
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(ci_workflow.subprocess, "run", fake_run)
    ci_workflow.python_install(argparse.Namespace())
    ci_workflow.python_run_tests(argparse.Namespace())
    assert any("pip" in part for cmd in commands for part in cmd)
    assert "ℹ️ No Python tests found" in capsys.readouterr().out


def test_generate_ci_summary(tmp_path, monkeypatch):
    summary_path = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_path))
    monkeypatch.setenv("JOB_GO", "success")
    monkeypatch.setenv("JOB_PYTHON", "skipped")
    monkeypatch.setenv("JOB_RUST", "failure")
    monkeypatch.setenv("JOB_FRONTEND", "success")
    monkeypatch.setenv("CI_GO_FILES", "true")
    monkeypatch.setenv("CI_PYTHON_FILES", "false")
    monkeypatch.setenv("CI_RUST_FILES", "true")
    monkeypatch.setenv("CI_FRONTEND_FILES", "false")
    monkeypatch.setenv("CI_DOCKER_FILES", "false")
    monkeypatch.setenv("CI_DOCS_FILES", "true")
    monkeypatch.setenv("CI_WORKFLOW_FILES", "false")

    ci_workflow.generate_ci_summary(argparse.Namespace())
    content = summary_path.read_text()
    assert "CI Pipeline Summary" in content
    assert "| Rust | failure |" in content


def test_check_ci_status_failure(monkeypatch):
    monkeypatch.setenv("JOB_GO", "success")
    monkeypatch.setenv("JOB_PYTHON", "failure")
    monkeypatch.setenv("JOB_RUST", "success")
    monkeypatch.setenv("JOB_FRONTEND", "success")
    with pytest.raises(SystemExit):
        ci_workflow.check_ci_status(argparse.Namespace())
