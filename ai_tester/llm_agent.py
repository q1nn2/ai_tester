from __future__ import annotations

import json
import os
import re
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
            f"╨Э╨╡ ╨╜╨░╨╣╨┤╨╡╨╜ API-╨║╨╗╤О╤З ╨▓ ╨┐╨╡╤А╨╡╨╝╨╡╨╜╨╜╨╛╨╣ ╨╛╨║╤А╤Г╨╢╨╡╨╜╨╕╤П {config.api_key_env}. "
            "╨Ч╨░╨┤╨░╨╣╤В╨╡ ╨║╨╗╤О╤З ╨╕ ╨┐╨╛╨▓╤В╨╛╤А╨╕╤В╨╡ ╨┐╨╛╨┐╤Л╤В╨║╤Г."
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

    with httpx.Client(timeout=60) as client:
        resp = client.post(url, json=body, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise LLMError(f"╨Э╨╡╨╛╨╢╨╕╨┤╨░╨╜╨╜╤Л╨╣ ╤Д╨╛╤А╨╝╨░╤В ╨╛╤В╨▓╨╡╤В╨░ LLM: {data}") from exc


def generate_suite_from_text(text: str, feature: str, config: LLMConfig) -> TestSuite:
    """
    ╨У╨╡╨╜╨╡╤А╨╕╤А╤Г╨╡╤В TestSuite ╨╜╨░ ╨╛╤Б╨╜╨╛╨▓╨╡ ╤В╨╡╨║╤Б╤В╨╛╨▓╨╛╨│╨╛ ╨╛╨┐╨╕╤Б╨░╨╜╨╕╤П ╤Д╨╕╤З╨╕.

    ╨Ь╨╛╨┤╨╡╨╗╤М ╨┐╨╛╨╗╤Г╤З╨░╨╡╤В ╨╕╨╜╤Б╤В╤А╤Г╨║╤Ж╨╕╤О ╨▓╨╡╤А╨╜╤Г╤В╤М ╤Б╤В╤А╨╛╨│╨╛ ╨▓╨░╨╗╨╕╨┤╨╜╤Л╨╣ JSON,
    ╤Б╨╛╨▓╨╝╨╡╤Б╤В╨╕╨╝╤Л╨╣ ╤Б ╤Б╤Е╨╡╨╝╨╛╨╣ TestSuite/TestCase/TestStep.
    """
    system_prompt = (
        "╨в╤Л ╨╛╨┐╤Л╤В╨╜╤Л╨╣ QA-╨╕╨╜╨╢╨╡╨╜╨╡╤А. ╨Я╨╛ ╤В╨╡╨║╤Б╤В╨╛╨▓╨╛╨╝╤Г ╨╛╨┐╨╕╤Б╨░╨╜╨╕╤О ╤Д╨╕╤З╨╕ ╤В╤Л ╤Б╨╛╤Б╤В╨░╨▓╨╗╤П╨╡╤И╤М "
        "╤Б╤В╤А╤Г╨║╤В╤Г╤А╨╕╤А╨╛╨▓╨░╨╜╨╜╤Л╨╡ ╤В╨╡╤Б╤В-╨║╨╡╨╣╤Б╤Л ╨▓ ╤Д╨╛╤А╨╝╨░╤В╨╡ JSON, ╨║╨╛╤В╨╛╤А╤Л╨╣ ╤Б╨╛╨╛╤В╨▓╨╡╤В╤Б╤В╨▓╤Г╨╡╤В "
        "╤Б╤Е╨╡╨╝╨╡ TestSuite/TestCase/TestStep:\n"
        "- TestSuite: { suite: str, description?: str, cases: TestCase[] }\n"
        "- TestCase: { id: str, title: str, description?: str, feature?: str, "
        "preconditions: str[], steps: TestStep[], expected_result: str, "
        "priority: 'low'|'medium'|'high'|'critical', tags: str[] }\n"
        "- TestStep: { id: int, description: str, type: 'ui'|'api'|'manual', "
        "action?: object, expected?: str }.\n"
        "╨Ф╨╗╤П type 'ui' ╨┐╨╛╨╗╨╡ action ╨┤╨╛╨╗╨╢╨╜╨╛ ╤Б╨╛╨╛╤В╨▓╨╡╤В╤Б╤В╨▓╨╛╨▓╨░╤В╤М UIAction, ╨┤╨╗╤П 'api' тАФ APIAction. "
        "╨Т╨╡╤А╨╜╨╕ ╨в╨Ю╨Ы╨м╨Ъ╨Ю JSON, ╨▒╨╡╨╖ ╨┐╨╛╤П╤Б╨╜╨╡╨╜╨╕╨╣."
    )

    user_prompt = (
        f"╨д╨╕╤З╨░: {feature}\n\n"
        "╨Ю╨┐╨╕╤Б╨░╨╜╨╕╨╡ ╤Д╨╕╤З╨╕/╤В╤А╨╡╨▒╨╛╨▓╨░╨╜╨╕╨╣:\n"
        f"{text}\n\n"
        "╨б╨╛╤Б╤В╨░╨▓╤М ╨╜╨╡╨▒╨╛╨╗╤М╤И╨╛╨╣, ╨╜╨╛ ╨┐╨╛╨║╨░╨╖╨░╤В╨╡╨╗╤М╨╜╤Л╨╣ ╨╜╨░╨▒╨╛╤А ╤В╨╡╤Б╤В-╨║╨╡╨╣╤Б╨╛╨▓ (3-10 ╤И╤В╤Г╨║), "
        "╨┐╨╛╨║╤А╤Л╨▓╨░╤О╤Й╨╕╤Е ╨┐╨╛╨╖╨╕╤В╨╕╨▓╨╜╤Л╨╡ ╨╕ ╨║╨╗╤О╤З╨╡╨▓╤Л╨╡ ╨╜╨╡╨│╨░╤В╨╕╨▓╨╜╤Л╨╡ ╤Б╤Ж╨╡╨╜╨░╤А╨╕╨╕."
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
    lines.append("")

    lines.append("## ╨Ъ╨╡╨╣╤Б╤Л")
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

