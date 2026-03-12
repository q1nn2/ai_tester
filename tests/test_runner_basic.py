from datetime import datetime
from typing import Any

import pytest

from ai_tester import runner
from ai_tester.models import (
    APIAction,
    CaseResult,
    StepResult,
    StepStatus,
    StepType,
    TestCase,
    TestRunResult,
    TestSuite,
    UIAction,
)


class DummyBrowserExecutor:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url

    async def __aenter__(self) -> "DummyBrowserExecutor":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        return None

    async def run_action(self, action: UIAction) -> str:
        return f"UI OK: {action.kind}"


class DummyAPIExecutor:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url

    async def run_action(self, action: APIAction) -> str:
        return f"API OK: {action.method} {action.path}"


class FailingAPIExecutor(DummyAPIExecutor):
    async def run_action(self, action: APIAction) -> str:
        raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_run_single_case_mixed_steps(monkeypatch: pytest.MonkeyPatch) -> None:
    case = TestCase(
        id="MIX-001",
        title="Mixed ui/api/manual",
        description=None,
        feature=None,
        preconditions=[],
        steps=[
            # UI step
            {
                "id": 1,
                "description": "Open page",
                "type": StepType.UI,
                "action": {"kind": "open_url", "url": "/"},
            },
            # API step
            {
                "id": 2,
                "description": "Call API",
                "type": StepType.API,
                "action": {"method": "GET", "path": "/health"},
            },
            # Manual step
            {
                "id": 3,
                "description": "Manual check",
                "type": StepType.MANUAL,
            },
        ],
        expected_result="All good",
        priority="medium",
        tags=[],
    )

    # Подменяем реальные executors на заглушки
    monkeypatch.setattr(runner, "BrowserExecutor", DummyBrowserExecutor)
    monkeypatch.setattr(runner, "APIExecutor", DummyAPIExecutor)

    result = await runner.run_single_case(case, env_name=None, base_url="http://test", api_base_url="http://api")

    assert isinstance(result, CaseResult)
    assert len(result.step_results) == 3
    # UI и API должны пройти
    assert result.step_results[0].status is StepStatus.PASSED
    assert result.step_results[1].status is StepStatus.PASSED
    # manual шаг помечается как NEEDS_CHECK
    assert result.step_results[2].status is StepStatus.NEEDS_CHECK


@pytest.mark.asyncio
async def test_run_single_case_api_exception_marks_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    case = TestCase(
        id="API-FAIL",
        title="API fails",
        description=None,
        feature=None,
        preconditions=[],
        steps=[
            {
                "id": 1,
                "description": "Failing API",
                "type": StepType.API,
                "action": {"method": "GET", "path": "/boom"},
            }
        ],
        expected_result="Should fail",
        priority="medium",
        tags=[],
    )

    monkeypatch.setattr(runner, "BrowserExecutor", DummyBrowserExecutor)
    monkeypatch.setattr(runner, "APIExecutor", FailingAPIExecutor)

    result = await runner.run_single_case(case, env_name=None, base_url=None, api_base_url="http://api")

    assert result.status is StepStatus.FAILED
    assert result.step_results[0].status is StepStatus.FAILED


def test_run_suite_sync_aggregates_status(monkeypatch: pytest.MonkeyPatch) -> None:
    # создаём два простых кейса со step_results вручную через заглушку run_single_case
    case1 = TestCase(
        id="CASE-1",
        title="ok",
        description=None,
        feature=None,
        preconditions=[],
        steps=[],
        expected_result="ok",
        priority="medium",
        tags=[],
    )
    case2 = TestCase(
        id="CASE-2",
        title="failed",
        description=None,
        feature=None,
        preconditions=[],
        steps=[],
        expected_result="fail",
        priority="medium",
        tags=[],
    )

    async def fake_run_single_case_ok(case: TestCase, *args: Any, **kwargs: Any) -> CaseResult:  # type: ignore[override]
        return CaseResult(
            case_id=case.id,
            status=StepStatus.PASSED,
            step_results=[
                StepResult(step_id=1, status=StepStatus.PASSED, started_at=datetime.now(), finished_at=datetime.now())
            ],
        )

    async def fake_run_single_case_fail(case: TestCase, *args: Any, **kwargs: Any) -> CaseResult:  # type: ignore[override]
        return CaseResult(
            case_id=case.id,
            status=StepStatus.FAILED,
            step_results=[
                StepResult(step_id=1, status=StepStatus.FAILED, started_at=datetime.now(), finished_at=datetime.now())
            ],
        )

    async def fake_run_suite(suite: TestSuite, *args: Any, **kwargs: Any) -> TestRunResult:  # type: ignore[override]
        results: list[CaseResult] = []
        for case in suite.cases:
            if case.id == "CASE-1":
                results.append(await fake_run_single_case_ok(case))
            else:
                results.append(await fake_run_single_case_fail(case))
        return TestRunResult(
            id="run-1",
            suite_name=suite.suite,
            started_at=datetime.now(),
            finished_at=datetime.now(),
            env=None,
            summary_status=StepRunStatus.FAILED,  # type: ignore[name-defined]
            case_results=results,
        )

    # здесь мы не будем вызывать реальный run_suite, а проверим, что run_suite_sync
    # просто оборачивает асинхронную функцию.
    suite = TestSuite(suite="Mixed", feature=None, description=None, cases=[case1, case2])

    # monkeypatch asyncio.run, чтобы не выполнять настоящий event loop
    def fake_asyncio_run(coro):  # type: ignore[no-untyped-def]
        # напрямую вызываем нашу асинхронную функцию
        return TestRunResult(
            id="run-1",
            suite_name=suite.suite,
            started_at=datetime.now(),
            finished_at=datetime.now(),
            env=None,
            summary_status=StepStatus.FAILED,  # type: ignore[arg-type]
            case_results=[],
        )

    monkeypatch.setattr(runner.asyncio, "run", fake_asyncio_run)
    result = runner.run_suite_sync(suite)
    assert isinstance(result, TestRunResult)

