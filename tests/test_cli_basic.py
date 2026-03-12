from pathlib import Path

import pytest
from typer.testing import CliRunner

from ai_tester import cli


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_cli_validate_ok(tmp_path: Path, runner: CliRunner) -> None:
    # минимальный валидный TestSuite
    suite_path = tmp_path / "suite.yaml"
    suite_path.write_text(
        "suite: Example\ncases:\n  - id: \"C-1\"\n    title: \"Case\"\n"
        "    steps: []\n    expected_result: \"ok\"\n    priority: \"medium\"\n    tags: []\n",
        encoding="utf-8",
    )

    result = runner.invoke(cli.app, ["validate", str(suite_path)])
    assert result.exit_code == 0
    assert "OK" in result.stdout


def test_cli_docs_checklist_creates_md(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, runner: CliRunner) -> None:
    # конфиг указываем через AI_TESTER_CONFIG
    cfg = tmp_path / "ai-tester.config.yaml"
    cfg.write_text(
        "docs_dir: 'tests/ai-docs'\nsessions_dir: 'tests/ai-sessions'\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("AI_TESTER_CONFIG", str(cfg))

    docs_dir = tmp_path / "tests" / "ai-docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    suite_path = docs_dir / "Example.yaml"
    suite_path.write_text(
        "suite: Example\ncases:\n  - id: \"C-1\"\n    title: \"Case\"\n"
        "    steps: []\n    expected_result: \"ok\"\n    priority: \"medium\"\n    tags: []\n",
        encoding="utf-8",
    )

    with monkeypatch.context() as m:
        m.chdir(tmp_path)
        result = runner.invoke(cli.app, ["docs-checklist", str(suite_path)])

    assert result.exit_code == 0
    checklist_md = docs_dir / "Example-checklist.md"
    assert checklist_md.exists()

