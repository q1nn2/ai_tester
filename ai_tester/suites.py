from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional, Set

import yaml

from .models import TestRunResult, TestSuite


def load_suite(path: Path) -> TestSuite:
    """
    Загрузить TestSuite из YAML или JSON-файла.
    """
    if not path.exists():
        raise FileNotFoundError(f"Файл с TestSuite не найден: {path}")

    text = path.read_text(encoding="utf-8")

    if path.suffix.lower() in {".yml", ".yaml"}:
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)

    return TestSuite.model_validate(data)


def save_run_result(result: TestRunResult, path: Path) -> None:
    """
    Сохранить результат прогона набора тестов в JSON-файл.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = result.model_dump(mode="json")
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def filter_suite_by_tags(
    suite: TestSuite,
    only_tags: Optional[Iterable[str]] = None,
    exclude_tags: Optional[Iterable[str]] = None,
) -> TestSuite:
    """
    Отфильтровать кейсы TestSuite по тегам.

    only_tags  – оставить кейсы, содержащие хотя бы один из указанных тегов.
    exclude_tags – выкинуть кейсы, содержащие хотя бы один из указанных тегов.
    """
    only: Set[str] = {t.strip() for t in (only_tags or []) if t and t.strip()}
    excl: Set[str] = {t.strip() for t in (exclude_tags or []) if t and t.strip()}

    if not only and not excl:
        return suite

    filtered_cases = []
    for case in suite.cases:
        case_tags = set(case.tags or [])
        if only and not (case_tags & only):
            continue
        if excl and (case_tags & excl):
            continue
        filtered_cases.append(case)

    return TestSuite(**{**suite.model_dump(), "cases": filtered_cases})

