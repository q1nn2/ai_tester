from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field


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
        """
        Загрузить конфигурацию AIConfig из YAML-файла.
        Если файл не найден, выбрасывается понятная ошибка с подсказкой.
        """
        if path is None:
            path = Path("ai-tester.config.yaml")

        if not path.exists():
            raise RuntimeError(
                f"Файл конфигурации {path} не найден. "
                "Создайте его вручную или выполните 'python -m ai_tester.cli init'."
            )

        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        return cls.model_validate(data)

