from __future__ import annotations

from typing import Any, Protocol

from .api_executor import APIExecutor
from .browser_executor import BrowserExecutor
from .models import APIAction, StepResult, StepStatus, StepType, TestCase, TestStep, UIAction


class StepExecutor(Protocol):
    def supports(self, step: TestStep) -> bool: ...

    async def run(self, step: TestStep, context: dict[str, Any]) -> StepResult: ...


_EXECUTORS: list[StepExecutor] = []


def register_executor(executor: StepExecutor) -> None:
    _EXECUTORS.append(executor)


def get_executor_for(step: TestStep) -> StepExecutor | None:
    for executor in _EXECUTORS:
        if executor.supports(step):
            return executor
    return None


class UIStepExecutor:
    def supports(self, step: TestStep) -> bool:
        return step.type is StepType.UI and step.action is not None

    async def run(self, step: TestStep, context: dict[str, Any]) -> StepResult:
        browser: BrowserExecutor = context["browser"]
        action = UIAction.model_validate(step.action or {})
        actual = await browser.run_action(action)
        return StepResult(step_id=step.id, status=StepStatus.PASSED, actual=actual)


class APIStepExecutor:
    def supports(self, step: TestStep) -> bool:
        return step.type is StepType.API and step.action is not None

    async def run(self, step: TestStep, context: dict[str, Any]) -> StepResult:
        api_exec: APIExecutor = context["api"]
        action = APIAction.model_validate(step.action or {})
        actual = await api_exec.run_action(action)
        status = StepStatus.PASSED
        return StepResult(step_id=step.id, status=status, actual=actual)


def register_default_executors() -> None:
    if not _EXECUTORS:
        register_executor(UIStepExecutor())
        register_executor(APIStepExecutor())

