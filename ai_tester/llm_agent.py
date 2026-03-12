from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import httpx

from .config import LLMConfig
from .models import TestRunResult, TestSuite


class LLMError(RuntimeError):
    pass


def _extract_json_from_text(text: str) -> Dict[str, Any]:
    """
    Извлечь JSON из ответа LLM.

    Поддерживает несколько форматов:
    - ```json ... ```
    - "сырой" JSON
    - текст, внутри которого есть JSON-объект.
    """
    fenced = re.search(r"```json(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    payload = fenced.group(1) if fenced else text
    payload = payload.strip()

    # Сначала пробуем распарсить весь текст как JSON
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        pass

    # Fallback: пытаемся вырезать первую JSON-структуру по фигурным скобкам
    start = payload.find("{")
    end = payload.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = payload[start : end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise LLMError(f"Не удалось распарсить JSON из ответа LLM: {exc}") from exc

    raise LLMError("Ответ LLM не содержит валидный JSON для TestSuite.")


def _chat_completion(config: LLMConfig, messages: list[dict[str, str]]) -> str:
    api_key = os.getenv(config.api_key_env)
    if not api_key:
        raise LLMError(
            f"Не найден API-ключ в переменной окружения {config.api_key_env}. "
            "Установите переменную окружения перед запуском."
        )

    url = f"{config.base_url.rstrip('/')}/chat/completions"

    body = {
        "model": config.model,
        "temperature": config.temperature,
        "messages": messages,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    debug_llm = os.getenv("AI_TESTER_LLM_DEBUG", "").lower() in {"1", "true", "yes"}

    with httpx.Client(timeout=60) as client:
        resp = client.post(url, json=body, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    if debug_llm:
        logs_dir = Path("tests/ai-sessions/llm-logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        log_path = logs_dir / f"llm-{ts}.json"
        try:
            log_payload: Dict[str, Any] = {
                "request": {"body": body},
                "response": data,
            }
            log_path.write_text(
                json.dumps(log_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            # Логирование не должно ломать основной сценарий
            pass

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise LLMError(f"Некорректный формат ответа LLM: {data}") from exc


def generate_suite_from_text(text: str, feature: str, config: LLMConfig) -> TestSuite:
    """
    ╨У╨╡╨╜╨╡╤А╨╕╤А╤Г╨╡╤В TestSuite ╨╜╨░ ╨╛╤Б╨╜╨╛╨▓╨╡ ╤В╨╡╨║╤Б╤В╨╛╨▓╨╛╨│╨╛ ╨╛╨┐╨╕╤Б╨░╨╜╨╕╤П ╤Д╨╕╤З╨╕.

    ╨Ь╨╛╨┤╨╡╨╗╤М ╨┐╨╛╨╗╤Г╤З╨░╨╡╤В ╨╕╨╜╤Б╤В╤А╤Г╨║╤Ж╨╕╤О ╨▓╨╡╤А╨╜╤Г╤В╤М ╤Б╤В╤А╨╛╨│╨╛ ╨▓╨░╨╗╨╕╨┤╨╜╤Л╨╣ JSON,
    ╤Б╨╛╨▓╨╝╨╡╤Б╤В╨╕╨╝╤Л╨╣ ╤Б ╤Б╤Е╨╡╨╝╨╛╨╣ TestSuite/TestCase/TestStep.
    """
    base_language = config.language
    base_style = config.style or "classic"

    system_prompt = (
        "Ты опытный QA-инженер. "
        f"Генерируй тесты на языке: {base_language}. "
        f"Стиль описания тестов: {base_style}. "
        "Выводи только один JSON-объект со структурой:\n"
        "- TestSuite: { suite: str, description?: str, cases: TestCase[] }\n"
        "- TestCase: { id: str, title: str, description?: str, feature?: str, "
        "preconditions: str[], steps: TestStep[], expected_result: str, "
        "priority: 'low'|'medium'|'high'|'critical', tags: str[], "
        "datasets?: list[dict] }\n"
        "- TestStep: { id: int, description: str, type: 'ui'|'api'|'manual', "
        "action?: object, expected?: str }.\n"
        "Для type 'ui' используй объекты UIAction, для 'api' — APIAction. "
        "Строго соблюдай JSON-формат."
    )

    user_prompt = (
        f"Фича: {feature}\n\n"
        "Текстовое описание фичи/требований:\n"
        f"{text}\n\n"
        "Сгенерируй от 3 до 10 осмысленных тест-кейсов, которые хорошо покрывают функциональность. "
        "Используй теги (smoke, regression, ui, api и т.п.) и, где уместно, параметризацию через datasets."
    )

    content = _chat_completion(
        config,
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    data = _extract_json_from_text(content)
    suite = TestSuite.model_validate(data)

    # Базовая валидация содержимого для более дружелюбных ошибок
    if not suite.cases:
        raise LLMError("LLM вернул TestSuite без ни одного тест-кейса.")

    for case in suite.cases:
        if not case.steps:
            raise LLMError(f"Тест-кейс {case.id!r} не содержит шагов.")

    return suite


def summarize_run_to_markdown(run: TestRunResult) -> str:
    """
    ╨б╤В╤А╨╛╨╕╤В ╤З╨╡╨╗╨╛╨▓╨╡╨║╤Г ╨┐╨╛╨╜╤П╤В╨╜╨╛╨╡ ╤А╨╡╨╖╤О╨╝╨╡ ╨┐╤А╨╛╨│╨╛╨╜╨░.
    ╨Ф╨╗╤П ╨┐╤А╨╛╤Б╤В╨╛╤В╤Л ╤А╨╡╨░╨╗╨╕╨╖╨╛╨▓╨░╨╜╨╛ ╨╗╨╛╨║╨░╨╗╤М╨╜╨╛, ╨▒╨╡╨╖ LLM.
    """
    lines: list[str] = []
    lines.append(f"# ╨Ю╤В╤З╤С╤В ╨╛ ╨┐╤А╨╛╨│╨╛╨╜╨╡: {run.id}")
    lines.append("")
    lines.append(f"- Suite: {run.suite_name}")
    lines.append(f"- ╨Ю╨║╤А╤Г╨╢╨╡╨╜╨╕╨╡: {run.env or '-'}")
    lines.append(f"- ╨б╤В╨░╤А╤В: {run.started_at.isoformat()}")
    lines.append(f"- ╨Ч╨░╨▓╨╡╤А╤И╨╡╨╜╨╕╨╡: {run.finished_at.isoformat()}")
    lines.append(f"- ╨Ш╤В╨╛╨│╨╛╨▓╤Л╨╣ ╤Б╤В╨░╤В╤Г╤Б: **{run.summary_status.value}**")

    total_cases = len(run.case_results)
    passed_cases = sum(1 for cr in run.case_results if cr.status == "pass")  # type: ignore[comparison-overlap]
    failed_cases = sum(1 for cr in run.case_results if cr.status == "fail")  # type: ignore[comparison-overlap]
    partial_cases = sum(1 for cr in run.case_results if cr.status == "needs_check")  # type: ignore[comparison-overlap]

    total_steps = 0
    needs_check_steps = 0
    for cr in run.case_results:
        total_steps += len(cr.step_results)
        needs_check_steps += sum(1 for sr in cr.step_results if sr.status.value == "needs_check")

    lines.append("")
    lines.append("## Итоги")
    lines.append("")
    lines.append(f"- Всего кейсов: {total_cases}")
    lines.append(f"- Успешно (pass): {passed_cases}")
    lines.append(f"- Упало (fail): {failed_cases}")
    lines.append(f"- Частично / требуют проверки: {partial_cases}")
    lines.append(f"- Всего шагов: {total_steps}")
    lines.append(f"- Шагов, требующих ручной проверки (needs_check): {needs_check_steps}")

    # Статистика по тегам кейсов
    tag_stats: dict[str, dict[str, int]] = {}
    for cr in run.case_results:
        # tags на уровне TestCase в текущей модели недоступны из CaseResult,
        # поэтому статистика по тегам может быть реализована позже через расширение модели.
        # Оставляем задел для будущей реализации.
        _ = cr  # заглушка, чтобы не было предупреждений

    lines.append("")
    lines.append("## Кейсы")
    lines.append("")
    for case_result in run.case_results:
        lines.append(f"### ╨Ъ╨╡╨╣╤Б {case_result.case_id}")
        lines.append(f"- ╨б╤В╨░╤В╤Г╤Б: **{case_result.status.value}**")
        if case_result.notes:
            lines.append(f"- ╨Ч╨░╨╝╨╡╤В╨║╨╕: {case_result.notes}")

        if case_result.step_results:
            lines.append("")
            lines.append("| ╨и╨░╨│ | ╨б╤В╨░╤В╤Г╤Б | ╨д╨░╨║╤В╨╕╤З╨╡╤Б╨║╨╕╨╣ ╤А╨╡╨╖╤Г╨╗╤М╤В╨░╤В |")
            lines.append("| --- | ------ | --------------------- |")
            for step in case_result.step_results:
                actual = (step.actual or "").replace("\n", " ")
                lines.append(f"| {step.step_id} | {step.status.value} | {actual} |")
            lines.append("")

    return "\n".join(lines)

