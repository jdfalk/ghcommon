import json

import configure_cargo_registry
import detect_frontend_package
import intelligent_labeling
import load_repository_config
import parse_protobuf_config
import write_go_module_metadata
import write_pypirc


def test_configure_cargo_registry_writes_files(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("CARGO_REGISTRY_TOKEN", "secret")
    monkeypatch.setattr(configure_cargo_registry.Path, "home", lambda: tmp_path)

    configure_cargo_registry.main()
    config = (tmp_path / ".cargo" / "config.toml").read_text()
    credentials = (tmp_path / ".cargo" / "credentials.toml").read_text()
    assert "owner/repo" in config
    assert "secret" in credentials


def test_detect_frontend_package_reports_package(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "package.json").write_text(
        json.dumps({"name": "app", "version": "1.2.3"}), encoding="utf-8"
    )
    (tmp_path / "yarn.lock").write_text("lock", encoding="utf-8")
    output_path = tmp_path / "output.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_path))

    detect_frontend_package.main()
    lines = output_path.read_text().splitlines()
    output_map = dict(line.split("=", 1) for line in lines)
    assert output_map["package-name"] == "app"
    assert output_map["package-manager"] == "yarn"


def test_load_repository_config_reads_yaml(tmp_path, monkeypatch):
    config_path = tmp_path / ".github" / "repository-config.yml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("feature: true\n", encoding="utf-8")
    output_path = tmp_path / "output.txt"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_path))

    class FakeYaml:
        @staticmethod
        def safe_load(_: str):
            return {"feature": True}

    monkeypatch.setattr(load_repository_config, "yaml", FakeYaml)
    load_repository_config.main()
    outputs = dict(
        line.split("=", 1) for line in output_path.read_text().splitlines()
    )
    assert outputs["has-config"] == "true"
    assert '"feature":true' in outputs["config"]


def test_parse_protobuf_config_outputs(tmp_path, monkeypatch):
    config_path = tmp_path / ".github" / "repository-config.yml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        "protobuf: {enabled: true, buf_version: 1.0.0}\n", encoding="utf-8"
    )
    output_path = tmp_path / "output.txt"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_path))

    class FakeYaml:
        @staticmethod
        def safe_load(_: str):
            return {
                "languages": {"go": {"enabled": True}},
                "protobuf": {"enabled": True, "buf_version": "1.0.0"},
            }

    monkeypatch.setattr(parse_protobuf_config, "yaml", FakeYaml)
    parse_protobuf_config.main()
    outputs = dict(
        line.split("=", 1) for line in output_path.read_text().splitlines()
    )
    assert outputs["protobuf-enabled"] == "true"
    assert outputs["go-enabled"] == "true"
    assert '"buf_version":"1.0.0"' in outputs["protobuf-config"]


def test_analyze_pr_content_adds_labels():
    labels = intelligent_labeling.analyze_pr_content(
        "Add feature",
        "This PR adds docs and tests",
        ["src/main.go", "docs/readme.md", "tests/test_app.py"],
    )
    assert set(labels) == {
        "documentation",
        "enhancement",
        "go",
        "python",
        "tests",
    }


def test_write_go_module_metadata(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MODULE_PATH", "github.com/example/mod")
    monkeypatch.setenv("MODULE_VERSION", "1.2.3")
    monkeypatch.setenv("REPOSITORY", "owner/repo")
    monkeypatch.setenv("TAG_NAME", "v1.2.3")
    monkeypatch.setenv("COMMIT_SHA", "abc123")
    output_path = tmp_path / "output.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_path))

    write_go_module_metadata.main()
    metadata = json.loads((tmp_path / "module-metadata.json").read_text())
    assert metadata["module"] == "github.com/example/mod"
    assert metadata["version"] == "v1.2.3"
    outputs = dict(
        line.split("=", 1) for line in output_path.read_text().splitlines()
    )
    assert outputs["metadata-file"] == "module-metadata.json"


def test_write_pypirc_writes_file(tmp_path, monkeypatch):
    monkeypatch.setenv("PYPI_TOKEN", "pypi")
    monkeypatch.setenv("GH_TOKEN", "gh")
    monkeypatch.setattr(write_pypirc.Path, "home", lambda: tmp_path)

    write_pypirc.main()
    content = (tmp_path / ".pypirc").read_text()
    assert "pypi" in content
    assert "gh" in content
