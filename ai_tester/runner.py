from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Optional

from .api_executor import APIExecutor
from .browser_executor import BrowserExecutor
from .models import APIAction, CaseResult, StepResult, StepStatus, TestCase, TestRunResult, TestRunStatus, TestSuite, UIAction


async def _run_ui_step(executor: BrowserExecutor, raw_action: dict) -> str:
    action = UIAction.model_validate(raw_action)
    return await executor.run_action(action)


async def _run_api_step(executor: APIExecutor, raw_action: dict) -> str:
    action = APIAction.model_validate(raw_action)
    return await executor.run_action(action)


def create_empty_case_result(case: TestCase) -> CaseResult:
    return CaseResult(case_id=case.id, status=StepStatus.PENDING, step_results=[])


def mark_manual_step(case_result: CaseResult, step_id: int, passed: bool, note: str = "") -> None:
    status = StepStatus.PASSED if passed else StepStatus.FAILED
    case_result.step_results.append(
        StepResult(
            step_id=step_id,
            status=status,
            actual=note or None,
        )
    )
    if not passed:
        case_result.status = StepStatus.FAILED


async def run_single_case(
    case: TestCase,
    env_name: Optional[str] = None,
    base_url: Optional[str] = None,
    api_base_url: Optional[str] = None,
) -> CaseResult:
    """
    ╨Ч╨░╨┐╤Г╤Б╨║╨░╨╡╤В ╨╛╨┤╨╕╨╜ TestCase, ╨▓╤Л╨┐╨╛╨╗╨╜╤П╤П ui/api ╤И╨░╨│╨╕.
    Manual ╤И╨░╨│╨╕ ╨┐╨╛╨╝╨╡╤З╨░╤О╤В╤Б╤П ╨║╨░╨║ needs_check.
    """
    started_at = datetime.now()
    case_result = CaseResult(case_id=case.id, status=StepStatus.PASSED, step_results=[])

    api_exec = APIExecutor(base_url=api_base_url)

    async with BrowserExecutor(base_url=base_url) as browser:
        for step in case.steps:
            sr = StepResult(step_id=step.id, status=StepStatus.PENDING, started_at=datetime.now())
            try:
                if step.type.value == "ui" and step.action is not None:
                    actual = await _run_ui_step(browser, step.action)
                    sr.status = StepStatus.PASSED
                    sr.actual = actual
                elif step.type.value == "api" and step.action is not None:
                    actual = await _run_api_step(api_exec, step.action)
                    # ╨╡╤Б╨╗╨╕ ╤В╨╡╨║╤Б╤В ╤Б╨╛╨┤╨╡╤А╨╢╨╕╤В ╨╛╤И╨╕╨▒╨║╤Г тАФ ╤Б╤З╨╕╤В╨░╨╡╨╝ fail
                    if actual.lower().startswith("╨╛╨╢╨╕╨┤╨░╨╗╤Б╤П ╤Б╤В╨░╤В╤Г╤Б") or "╨Ю╨╢╨╕╨┤╨░╨╗╨╛╤Б╤М ╨┐╨╛╨╗╨╡" in actual:
                        sr.status = StepStatus.FAILED
                        sr.actual = actual
                        case_result.status = StepStatus.FAILED
                    else:
                        sr.status = StepStatus.PASSED
                        sr.actual = actual
                else:
                    sr.status = StepStatus.NEEDS_CHECK
                    sr.actual = "╨и╨░╨│ manual тАФ ╤В╤А╨╡╨▒╤Г╨╡╤В╤Б╤П ╤А╤Г╤З╨╜╨░╤П ╨┐╤А╨╛╨▓╨╡╤А╨║╨░."
            except Exception as exc:  # noqa: BLE001
                sr.status = StepStatus.FAILED
                sr.actual = f"╨Ш╤Б╨║╨╗╤О╤З╨╡╨╜╨╕╨╡ ╨┐╤А╨╕ ╨▓╤Л╨┐╨╛╨╗╨╜╨╡╨╜╨╕╨╕ ╤И╨░╨│╨░: {exc!r}"
                case_result.status = StepStatus.FAILED
            finally:
                sr.finished_at = datetime.now()
                case_result.step_results.append(sr)

    # ╨╡╤Б╨╗╨╕ ╨║╨╡╨╣╤Б ╨┐╨╛╨╝╨╡╤З╨╡╨╜ ╨║╨░╨║ PASSED, ╨╜╨╛ ╨╡╤Б╤В╤М steps ╤Б╨╛ ╤Б╤В╨░╤В╤Г╤Б╨╛╨╝ NEEDS_CHECK,
    # ╤Б╤З╨╕╤В╨░╨╡╨╝ ╨╛╨▒╤Й╨╕╨╣ ╤Б╤В╨░╤В╤Г╤Б PARTIAL ╨╜╨░ ╤Г╤А╨╛╨▓╨╜╨╡ ╨▓╤Б╨╡╨│╨╛ ╨┐╤А╨╛╨│╨╛╨╜╨░, ╨░ ╨╜╨╡ ╨║╨╡╨╣╤Б╨░
    return case_result


async def run_suite(
    suite: TestSuite,
    env_name: Optional[str] = None,
    base_url: Optional[str] = None,
    api_base_url: Optional[str] = None,
) -> TestRunResult:
    """
    ╨Ч╨░╨┐╤Г╤Б╨║╨░╨╡╤В ╨▓╤Б╨╡ ╨║╨╡╨╣╤Б╤Л ╨╕╨╖ TestSuite.
    """
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    started_at = datetime.now()

    case_results: list[CaseResult] = []

    for case in suite.cases:
        case_result = await run_single_case(
            case=case,
            env_name=env_name,
            base_url=base_url,
            api_base_url=api_base_url,
        )
        case_results.append(case_result)

    finished_at = datetime.now()

    has_fail = any(cr.status == StepStatus.FAILED for cr in case_results)
    has_needs_check = any(
        any(sr.status == StepStatus.NEEDS_CHECK for sr in cr.step_results) for cr in case_results
    )

    if has_fail:
        summary = TestRunStatus.FAILED
    elif has_needs_check:
        summary = TestRunStatus.PARTIAL
    else:
        summary = TestRunStatus.PASSED

    return TestRunResult(
        id=run_id,
        suite_name=suite.suite,
        started_at=started_at,
        finished_at=finished_at,
        env=env_name,
        summary_status=summary,
        case_results=case_results,
    )


def run_suite_sync(
    suite: TestSuite,
    env_name: Optional[str] = None,
    base_url: Optional[str] = None,
    api_base_url: Optional[str] = None,
) -> TestRunResult:
    """
    ╨б╨╕╨╜╤Е╤А╨╛╨╜╨╜╨░╤П ╨╛╨▒╤С╤А╤В╨║╨░ ╨┤╨╗╤П ╨╕╤Б╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╨╜╨╕╤П ╨▓╨╜╨╡ Typer.
    """
    return asyncio.run(
        run_suite(suite=suite, env_name=env_name, base_url=base_url, api_base_url=api_base_url)
    )

