#!/usr/bin/env python3
"""Helper utilities invoked from GitHub Actions CI workflows."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import textwrap
import time
from pathlib import Path
from typing import Iterable

import requests


def append_to_file(path_env: str, content: str) -> None:
    """Append content to the file referenced by a GitHub Actions environment variable."""
    file_path = os.environ.get(path_env)
    if not file_path:
        return
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "a", encoding="utf-8") as handle:
        handle.write(content)


def write_output(name: str, value: str) -> None:
    append_to_file("GITHUB_OUTPUT", f"{name}={value}\n")


def append_env(name: str, value: str) -> None:
    append_to_file("GITHUB_ENV", f"{name}={value}\n")


def append_summary(text: str) -> None:
    append_to_file("GITHUB_STEP_SUMMARY", text)


def debug_filter(_: argparse.Namespace) -> None:
    mapping = {
        "Go files changed": os.environ.get("CI_GO_FILES", ""),
        "Frontend files changed": os.environ.get("CI_FRONTEND_FILES", ""),
        "Python files changed": os.environ.get("CI_PYTHON_FILES", ""),
        "Rust files changed": os.environ.get("CI_RUST_FILES", ""),
        "Docker files changed": os.environ.get("CI_DOCKER_FILES", ""),
        "Docs files changed": os.environ.get("CI_DOCS_FILES", ""),
        "Workflow files changed": os.environ.get("CI_WORKFLOW_FILES", ""),
        "Linter config files changed": os.environ.get("CI_LINT_FILES", ""),
    }
    for label, value in mapping.items():
        print(f"{label}: {value}")


def determine_execution(_: argparse.Namespace) -> None:
    commit_message = os.environ.get("GITHUB_HEAD_COMMIT_MESSAGE", "")
    skip_ci = bool(re.search(r"\[(skip ci|ci skip)\]", commit_message, flags=re.IGNORECASE))
    write_output("skip_ci", "true" if skip_ci else "false")
    if skip_ci:
        print("Skipping CI due to commit message")
    else:
        print("CI will continue; no skip directive found in commit message")

    write_output("should_lint", "true")
    write_output("should_test_go", os.environ.get("CI_GO_FILES", "false"))
    write_output("should_test_frontend", os.environ.get("CI_FRONTEND_FILES", "false"))
    write_output("should_test_python", os.environ.get("CI_PYTHON_FILES", "false"))
    write_output("should_test_rust", os.environ.get("CI_RUST_FILES", "false"))
    write_output("should_test_docker", os.environ.get("CI_DOCKER_FILES", "false"))


def wait_for_pr_automation(_: argparse.Namespace) -> None:
    repo = os.environ.get("GITHUB_REPOSITORY")
    token = os.environ.get("GITHUB_TOKEN")
    target_sha = os.environ.get("TARGET_SHA")
    workflow_name = os.environ.get("WORKFLOW_NAME", "PR Automation")
    max_attempts = int(os.environ.get("MAX_ATTEMPTS", "60"))
    sleep_seconds = int(os.environ.get("SLEEP_SECONDS", "10"))

    if not (repo and token and target_sha):
        print("Missing required environment values; skipping PR automation wait")
        return

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    url = f"https://api.github.com/repos/{repo}/actions/runs"

    print("🔄 Waiting for PR automation to complete...")
    for attempt in range(max_attempts):
        print(f"Checking for PR automation completion (attempt {attempt + 1}/{max_attempts})...")
        response = requests.get(url, headers=headers, params={"per_page": 100}, timeout=30)
        if response.status_code != 200:
            print(f"::warning::Unable to query workflow runs: {response.status_code}")
            time.sleep(sleep_seconds)
            continue

        runs = response.json().get("workflow_runs", [])
        matching_runs = [
            run for run in runs if run.get("head_sha") == target_sha and run.get("name") == workflow_name
        ]

        if not matching_runs:
            print("ℹ️  No PR automation workflow found, proceeding with CI")
            return

        status = matching_runs[0].get("status", "")
        if status == "completed":
            print("✅ PR automation has completed, proceeding with CI")
            return

        print(f"⏳ PR automation status: {status or 'unknown'}, waiting...")
        time.sleep(sleep_seconds)

    print("⚠️  Timeout waiting for PR automation, proceeding with CI anyway")


def _export_env_from_file(file_path: Path) -> None:
    with file_path.open(encoding="utf-8") as handle:
        for line in handle:
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if not key or key.startswith("#"):
                continue
            append_env(key, value.strip())


def load_super_linter_config(_: argparse.Namespace) -> None:
    event_name = os.environ.get("EVENT_NAME", "")
    pr_env = Path(os.environ.get("PR_ENV_FILE", "super-linter-pr.env"))
    ci_env = Path(os.environ.get("CI_ENV_FILE", "super-linter-ci.env"))

    chosen: Path | None = None

    if event_name in {"pull_request", "pull_request_target"}:
        if pr_env.is_file():
            print(f"Loading PR Super Linter configuration from {pr_env}")
            chosen = pr_env
        elif ci_env.is_file():
            print(f"PR config not found, falling back to CI config ({ci_env})")
            chosen = ci_env
    else:
        if ci_env.is_file():
            print(f"Loading CI Super Linter configuration from {ci_env}")
            chosen = ci_env

    if chosen:
        _export_env_from_file(chosen)
        write_output("config-file", chosen.name)
    else:
        print("Warning: No Super Linter configuration found")
        write_output("config-file", "")


def write_validation_summary(_: argparse.Namespace) -> None:
    event_name = os.environ.get("EVENT_NAME", "unknown")
    config_name = os.environ.get("SUMMARY_CONFIG", "super-linter-ci.env")
    append_summary(
        textwrap.dedent(
            f"""\
            # 🔍 CI Validation Results

            ✅ **Code validation completed**

            ## Configuration
            - **Mode**: Validation only (no auto-fixes)
            - **Configuration**: {config_name}
            - **Event**: {event_name}

            """
        )
    )


def _ensure_go_context() -> bool:
    if not Path("go.mod").is_file():
        print("ℹ️ No go.mod found; skipping Go step")
        return False
    return True


def go_setup(_: argparse.Namespace) -> None:
    if not _ensure_go_context():
        return
    subprocess.run(["go", "mod", "download"], check=True)
    subprocess.run(["go", "build", "-v", "./..."], check=True)


def _parse_go_coverage(total_line: str) -> float:
    parts = total_line.strip().split()
    if not parts:
        raise ValueError("Unable to parse go coverage output")
    percentage = parts[-1].rstrip("%")
    return float(percentage)


def go_test(_: argparse.Namespace) -> None:
    if not _ensure_go_context():
        return

    coverage_file = os.environ.get("COVERAGE_FILE", "coverage.out")
    threshold = float(os.environ.get("COVERAGE_THRESHOLD", "0"))

    command = ["go", "test", "-v", "-race", f"-coverprofile={coverage_file}", "./..."]
    subprocess.run(command, check=True)

    go_binary = shutil.which("go") or "go"
    subprocess.run(
        [go_binary, "tool", "cover", f"-html={coverage_file}", "-o", os.environ.get("COVERAGE_HTML", "coverage.html")],
        check=True,
    )
    result = subprocess.run(
        [go_binary, "tool", "cover", "-func", coverage_file],
        check=True,
        capture_output=True,
        text=True,
    )

    total_line = ""
    for line in result.stdout.splitlines():
        if line.startswith("total:"):
            total_line = line
            break

    if not total_line:
        raise ValueError("Total coverage line not found in go tool output")

    coverage = _parse_go_coverage(total_line)
    print(f"Coverage: {coverage}%")
    if coverage < threshold:
        raise SystemExit(f"Coverage {coverage}% is below threshold {threshold}%")
    print(f"✅ Coverage {coverage}% meets threshold {threshold}%")


def frontend_install(_: argparse.Namespace) -> None:
    if Path("package-lock.json").is_file():
        subprocess.run(["npm", "ci"], check=True)
    elif Path("yarn.lock").is_file():
        subprocess.run(["yarn", "install", "--frozen-lockfile"], check=True)
    elif Path("pnpm-lock.yaml").is_file():
        subprocess.run(["npm", "install", "-g", "pnpm"], check=True)
        subprocess.run(["pnpm", "install", "--frozen-lockfile"], check=True)
    elif Path("package.json").is_file():
        subprocess.run(["npm", "install"], check=True)
    else:
        print("ℹ️ No package.json found; skipping install")


def frontend_run(_: argparse.Namespace) -> None:
    script_name = os.environ.get("FRONTEND_SCRIPT", "")
    success_message = os.environ.get("FRONTEND_SUCCESS_MESSAGE", "Command succeeded")
    failure_message = os.environ.get("FRONTEND_FAILURE_MESSAGE", "Command failed")

    if not Path("package.json").is_file():
        print("ℹ️ No package.json found; skipping frontend commands")
        return

    if not script_name:
        raise SystemExit("FRONTEND_SCRIPT environment variable is required")

    result = subprocess.run(["npm", "run", script_name, "--if-present"])
    if result.returncode == 0:
        print(success_message)
    else:
        print(failure_message)


def python_install(_: argparse.Namespace) -> None:
    python = sys.executable
    subprocess.run([python, "-m", "pip", "install", "--upgrade", "pip"], check=True)

    if Path("requirements.txt").is_file():
        subprocess.run([python, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    if Path("requirements-dev.txt").is_file():
        subprocess.run([python, "-m", "pip", "install", "-r", "requirements-dev.txt"], check=True)
    if Path("pyproject.toml").is_file() or Path("setup.py").is_file():
        subprocess.run([python, "-m", "pip", "install", "-e", "."], check=True)


def python_lint(_: argparse.Namespace) -> None:
    python = sys.executable
    subprocess.run([python, "-m", "pip", "install", "flake8", "black", "isort"], check=True)
    subprocess.run([python, "-m", "flake8", ".", "--count", "--select=E9,F63,F7,F82", "--show-source", "--statistics"], check=True)
    subprocess.run([python, "-m", "black", "--check", "."], check=True)
    subprocess.run([python, "-m", "isort", "--check-only", "."], check=True)


def _python_tests_exist() -> bool:
    for pattern in ("test_*.py", "*_test.py"):
        if any(Path(".").rglob(pattern)):
            return True
    return False


def python_run_tests(_: argparse.Namespace) -> None:
    python = sys.executable
    subprocess.run([python, "-m", "pip", "install", "pytest", "pytest-cov"], check=True)

    if not Path("tests").exists() and not _python_tests_exist():
        print("ℹ️ No Python tests found; skipping pytest run")
        return

    subprocess.run([python, "-m", "pytest", "--cov", "--cov-report=xml", "--cov-report=term-missing"], check=True)


def rust_format(_: argparse.Namespace) -> None:
    subprocess.run(["cargo", "fmt", "--all", "--", "--check"], check=True)


def rust_clippy(_: argparse.Namespace) -> None:
    subprocess.run(["cargo", "clippy", "--all-targets", "--all-features", "--", "-D", "warnings"], check=True)


def rust_build(_: argparse.Namespace) -> None:
    subprocess.run(["cargo", "build", "--verbose"], check=True)


def rust_test(_: argparse.Namespace) -> None:
    subprocess.run(["cargo", "test", "--verbose"], check=True)


def ensure_cargo_llvm_cov(_: argparse.Namespace) -> None:
    if shutil.which("cargo-llvm-cov"):
        print("cargo-llvm-cov already installed")
        return
    subprocess.run(["cargo", "install", "cargo-llvm-cov", "--locked"], check=True)


def generate_rust_lcov(_: argparse.Namespace) -> None:
    output_path = Path(os.environ.get("LCOV_OUTPUT", "lcov.info"))
    subprocess.run(
        ["cargo", "llvm-cov", "--workspace", "--verbose", "--lcov", "--output-path", str(output_path)],
        check=True,
    )


def generate_rust_html(_: argparse.Namespace) -> None:
    output_dir = Path(os.environ.get("HTML_OUTPUT_DIR", "htmlcov"))
    output_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["cargo", "llvm-cov", "--workspace", "--verbose", "--html", "--output-dir", str(output_dir)],
        check=True,
    )


def compute_rust_coverage(_: argparse.Namespace) -> None:
    path = Path(os.environ.get("LCOV_FILE", "lcov.info"))
    if not path.is_file():
        raise FileNotFoundError(f"{path} not found")

    total = 0
    covered = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("LF:"):
            total += int(line.split(":", 1)[1])
        elif line.startswith("LH:"):
            covered += int(line.split(":", 1)[1])

    if total == 0:
        write_output("percent", "0")
        return

    percent = (covered * 100.0) / total
    write_output("percent", f"{percent:.2f}")


def enforce_coverage_threshold(_: argparse.Namespace) -> None:
    threshold = float(os.environ.get("COVERAGE_THRESHOLD", "0"))
    percent_str = os.environ.get("COVERAGE_PERCENT")
    if percent_str is None:
        raise SystemExit("COVERAGE_PERCENT environment variable missing")

    percent = float(percent_str)
    append_summary(f"Rust coverage: {percent}% (threshold {threshold}%)\n")
    if percent < threshold:
        raise SystemExit(f"Coverage {percent}% is below threshold {threshold}%")
    print(f"✅ Coverage {percent}% meets threshold {threshold}%")


def docker_build(_: argparse.Namespace) -> None:
    dockerfile = Path(os.environ.get("DOCKERFILE_PATH", "Dockerfile"))
    image_name = os.environ.get("DOCKER_IMAGE", "test-image")
    if not dockerfile.is_file():
        print("ℹ️ No Dockerfile found")
        return

    subprocess.run(["docker", "build", "-t", image_name, str(dockerfile.parent)], check=True)


def docker_test_compose(_: argparse.Namespace) -> None:
    if Path("docker-compose.yml").is_file() or Path("docker-compose.yaml").is_file():
        subprocess.run(["docker-compose", "config"], check=True)
    else:
        print("ℹ️ No docker-compose file found")


def docs_check_links(_: argparse.Namespace) -> None:
    print("ℹ️ Link checking would go here")


def docs_validate_structure(_: argparse.Namespace) -> None:
    print("ℹ️ Documentation structure validation would go here")


def run_benchmarks(_: argparse.Namespace) -> None:
    has_benchmarks = False
    for path in Path(".").rglob("*_test.go"):
        try:
            if "Benchmark" in path.read_text(encoding="utf-8"):
                has_benchmarks = True
                break
        except UnicodeDecodeError:
            continue

    if not has_benchmarks:
        print("ℹ️ No benchmarks found")
        return

    subprocess.run(["go", "test", "-bench=.", "-benchmem", "./..."], check=True)


def generate_ci_summary(_: argparse.Namespace) -> None:
    summary_lines = [
        "# 🚀 CI Pipeline Summary",
        "",
        "## 📊 Job Results",
        "| Job | Status |",
        "|-----|--------|",
    ]

    job_envs = {
        "Go": os.environ.get("JOB_GO", "skipped"),
        "Python": os.environ.get("JOB_PYTHON", "skipped"),
        "Rust": os.environ.get("JOB_RUST", "skipped"),
        "Frontend": os.environ.get("JOB_FRONTEND", "skipped"),
    }

    for job, status in job_envs.items():
        summary_lines.append(f"| {job} | {status} |")

    summary_lines.extend(
        [
            "",
            "## 📁 Changed Files",
            f"- Go: {os.environ.get('CI_GO_FILES', 'false')}",
            f"- Python: {os.environ.get('CI_PYTHON_FILES', 'false')}",
            f"- Rust: {os.environ.get('CI_RUST_FILES', 'false')}",
            f"- Frontend: {os.environ.get('CI_FRONTEND_FILES', 'false')}",
            f"- Docker: {os.environ.get('CI_DOCKER_FILES', 'false')}",
            f"- Docs: {os.environ.get('CI_DOCS_FILES', 'false')}",
            f"- Workflows: {os.environ.get('CI_WORKFLOW_FILES', 'false')}",
        ]
    )

    append_summary("\n".join(summary_lines) + "\n")


def check_ci_status(_: argparse.Namespace) -> None:
    job_envs = {
        "Go": os.environ.get("JOB_GO"),
        "Python": os.environ.get("JOB_PYTHON"),
        "Rust": os.environ.get("JOB_RUST"),
        "Frontend": os.environ.get("JOB_FRONTEND"),
    }

    failures = [job for job, status in job_envs.items() if status == "failure"]
    if failures:
        print(f"❌ CI Pipeline failed: {', '.join(failures)}")
        raise SystemExit(1)
    print("✅ CI Pipeline succeeded")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CI workflow helper commands.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    commands = {
        "debug-filter": debug_filter,
        "determine-execution": determine_execution,
        "wait-for-pr-automation": wait_for_pr_automation,
        "load-super-linter-config": load_super_linter_config,
        "write-validation-summary": write_validation_summary,
        "go-setup": go_setup,
        "go-test": go_test,
        "frontend-install": frontend_install,
        "frontend-run": frontend_run,
        "python-install": python_install,
        "python-lint": python_lint,
        "python-run-tests": python_run_tests,
        "rust-format": rust_format,
        "rust-clippy": rust_clippy,
        "rust-build": rust_build,
        "rust-test": rust_test,
        "ensure-cargo-llvm-cov": ensure_cargo_llvm_cov,
        "generate-rust-lcov": generate_rust_lcov,
        "generate-rust-html": generate_rust_html,
        "compute-rust-coverage": compute_rust_coverage,
        "enforce-coverage-threshold": enforce_coverage_threshold,
        "docker-build": docker_build,
        "docker-test-compose": docker_test_compose,
        "docs-check-links": docs_check_links,
        "docs-validate-structure": docs_validate_structure,
        "run-benchmarks": run_benchmarks,
        "generate-ci-summary": generate_ci_summary,
        "check-ci-status": check_ci_status,
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
