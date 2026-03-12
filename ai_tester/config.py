from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field, ValidationError


class LLMConfig(BaseModel):
    provider: str = Field(
        default="openai",
        description=(
            "Провайдер LLM: openai/other. По умолчанию используется API, "
            "совместимый с OpenAI HTTP API."
        ),
    )
    api_key_env: str = Field(
        default="AI_TESTER_LLM_API_KEY",
        description="Имя переменной окружения с API-ключом для LLM.",
    )
    base_url: str = Field(
        default="https://api.openai.com/v1",
        description="Базовый URL для LLM API.",
    )
    model: str = Field(
        default="gpt-4.1-mini",
        description="Модель LLM, используемая для генерации тестов.",
    )
    temperature: float = 0.2


class EnvConfig(BaseModel):
    name: str
    base_url: Optional[str] = None
    api_base_url: Optional[str] = None


class AIConfig(BaseModel):
    llm: LLMConfig = Field(default_factory=LLMConfig)
    docs_dir: Path = Path("tests/ai-docs")
    sessions_dir: Path = Path("tests/ai-sessions")
    envs: list[EnvConfig] = Field(default_factory=list)

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "AIConfig":
        # Оставлено для обратной совместимости с существующим кодом.
        # Реальная логика загрузки сконцентрирована в load_config().
        return load_config(path)


def _resolve_config_path(explicit: Optional[Path]) -> Path:
    """
    Определить путь к файлу конфигурации с приоритетами:
    1) явно переданный path
    2) переменная окружения AI_TESTER_CONFIG
    3) локальный файл ./ai-tester.config.yaml
    """
    if explicit is not None:
        return explicit

    env_path = os.getenv("AI_TESTER_CONFIG")
    if env_path:
        return Path(env_path)

    return Path("ai-tester.config.yaml")


def load_config(path: Optional[Path] = None) -> AIConfig:
    """
    Загрузить конфигурацию AIConfig из YAML-файла с дружественной обработкой ошибок.
    """
    cfg_path = _resolve_config_path(path)

    if not cfg_path.exists():
        raise RuntimeError(
            f"Файл конфигурации {cfg_path} не найден. "
            "Создайте его вручную или выполните 'python -m ai_tester.cli init'. "
            "Также можно указать путь через переменную окружения AI_TESTER_CONFIG."
        )

    try:
        with cfg_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Не удалось прочитать {cfg_path}: {exc!r}") from exc

    try:
        return AIConfig.model_validate(data)
    except ValidationError as exc:
        raise RuntimeError(f"Конфигурация {cfg_path} невалидна: {exc}") from exc

