from pathlib import Path

import pytest

from ai_tester.config import AIConfig, load_config


def test_load_config_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg_file = tmp_path / "ai-tester.config.yaml"
    cfg_file.write_text(
        "docs_dir: 'tests/ai-docs'\nsessions_dir: 'tests/ai-sessions'\n", encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)

    cfg = load_config()
    assert isinstance(cfg, AIConfig)
    assert cfg.docs_dir.name == "ai-docs"
    assert cfg.sessions_dir.name == "ai-sessions"

