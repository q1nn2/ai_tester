from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    provider: str = Field(
        default="openai",
        description="╨в╨╕╨┐ ╨┐╤А╨╛╨▓╨░╨╣╨┤╨╡╤А╨░ LLM: openai/other. ╨б╨╡╨╣╤З╨░╤Б ╨╕╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╡╤В╤Б╤П openai-╤Б╨╛╨▓╨╝╨╡╤Б╤В╨╕╨╝╤Л╨╣ HTTP API.",
    )
    api_key_env: str = Field(
        default="AI_TESTER_LLM_API_KEY",
        description="╨Ш╨╝╤П ╨┐╨╡╤А╨╡╨╝╨╡╨╜╨╜╨╛╨╣ ╨╛╨║╤А╤Г╨╢╨╡╨╜╨╕╤П ╤Б API-╨║╨╗╤О╤З╨╛╨╝.",
    )
    base_url: str = Field(
        default="https://api.openai.com/v1",
        description="╨С╨░╨╖╨╛╨▓╤Л╨╣ URL ╨┤╨╗╤П LLM API.",
    )
    model: str = Field(
        default="gpt-4.1-mini",
        description="╨Ш╨╝╤П ╨╝╨╛╨┤╨╡╨╗╨╕ ╨┐╨╛ ╤Г╨╝╨╛╨╗╤З╨░╨╜╨╕╤О.",
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
        ╨Ч╨░╨│╤А╤Г╨╢╨░╨╡╤В ╨║╨╛╨╜╤Д╨╕╨│ ╨╕╨╖ YAML.
        ╨Х╤Б╨╗╨╕ ╤Д╨░╨╣╨╗ ╨╛╤В╤Б╤Г╤В╤Б╤В╨▓╤Г╨╡╤В, ╨▓╨╛╨╖╨▓╤А╨░╤Й╨░╨╡╤В ╨║╨╛╨╜╤Д╨╕╨│ ╨┐╨╛ ╤Г╨╝╨╛╨╗╤З╨░╨╜╨╕╤О.
        """
        if path is None:
            path = Path("ai-tester.config.yaml")

        if not path.exists():
            return cls()

        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        return cls.model_validate(data)

