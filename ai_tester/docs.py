from __future__ import annotations

from typing import List

from .models import Checklist, ChecklistItem, Priority, TestSuite


def checklist_from_suite(suite: TestSuite) -> Checklist:
    """
    Построить чек-лист из TestSuite:
    один элемент чек-листа на каждый тест-кейс.
    """
    items: List[ChecklistItem] = []
    for case in suite.cases:
        items.append(
            ChecklistItem(
                id=case.id,
                title=case.title,
                description=case.description or case.expected_result,
                priority=case.priority or Priority.MEDIUM,
                tags=case.tags,
            )
        )
    return Checklist(feature=suite.suite, items=items)


def checklist_to_markdown(
    checklist: Checklist,
    include_descriptions: bool = True,
    include_tags: bool = True,
) -> str:
    """
    Преобразовать чек-лист в Markdown:
    - заголовок с названием фичи/набора
    - список пунктов с приоритетом и, опционально, тегами и описанием.
    """
    lines: list[str] = []
    lines.append(f"# Чек-лист: {checklist.feature}")
    lines.append("")

    for item in checklist.items:
        tags = ""
        if include_tags and item.tags:
            tags = f" [tags: {', '.join(item.tags)}]"
        lines.append(
            f"- [ ] **{item.id} – {item.title}** (priority: {item.priority.value}){tags}"
        )
        if include_descriptions and item.description:
            lines.append(f"  - {item.description}")

    lines.append("")
    return "\n".join(lines)

