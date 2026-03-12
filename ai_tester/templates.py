from __future__ import annotations

from importlib.resources import files


def load_text(name: str) -> str:
    """
    Загрузить текстовый шаблон из пакета ai_tester.templates.
    """
    return (files("ai_tester.templates") / name).read_text(encoding="utf-8")

