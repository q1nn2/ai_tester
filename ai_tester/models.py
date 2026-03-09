from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class StepType(str, Enum):
    UI = "ui"
    API = "api"
    MANUAL = "manual"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "pass"
    FAILED = "fail"
    BLOCKED = "blocked"
    NEEDS_CHECK = "needs_check"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class UIAction(BaseModel):
    """╨б╤В╤А╤Г╨║╤В╤Г╤А╨░ ╨┤╨╡╨╣╤Б╤В╨▓╨╕╨╣ ╨┤╨╗╤П browser_executor."""

    kind: str = Field(
        ...,
        description="╨в╨╕╨┐ ╨┤╨╡╨╣╤Б╤В╨▓╨╕╤П: open_url, click, fill, wait_for_text ╨╕ ╤В.╨┐.",
    )
    selector: Optional[str] = Field(
        None, description="CSS / ╤В╨╡╤Б╤В╨╛╨▓╤Л╨╣ ╤Б╨╡╨╗╨╡╨║╤В╨╛╤А ╨┤╨╗╤П ╨┤╨╡╨╣╤Б╤В╨▓╨╕╤П, ╨╡╤Б╨╗╨╕ ╨┐╤А╨╕╨╝╨╡╨╜╨╕╨╝╨╛."
    )
    text: Optional[str] = Field(None, description="╨в╨╡╨║╤Б╤В ╨┤╨╗╤П ╨▓╨▓╨╛╨┤╨░/╨┐╤А╨╛╨▓╨╡╤А╨║╨╕.")
    url: Optional[str] = Field(
        None, description="URL ╨┤╨╗╤П ╨╛╤В╨║╤А╤Л╤В╨╕╤П, ╨╡╤Б╨╗╨╕ kind == open_url."
    )
    extra: Dict[str, Any] = Field(
        default_factory=dict, description="╨Ф╨╛╨┐╨╛╨╗╨╜╨╕╤В╨╡╨╗╤М╨╜╤Л╨╡ ╨┐╨░╤А╨░╨╝╨╡╤В╤А╤Л ╨┤╨╗╤П ╨╕╤Б╨┐╨╛╨╗╨╜╨╕╤В╨╡╨╗╤П."
    )


class APIAction(BaseModel):
    """╨б╤В╤А╤Г╨║╤В╤Г╤А╨░ ╨┤╨╡╨╣╤Б╤В╨▓╨╕╨╣ ╨┤╨╗╤П api_executor."""

    method: str = Field(..., description="HTTP-╨╝╨╡╤В╨╛╨┤: GET, POST, PUT ╨╕ ╤В.╨┤.")
    path: str = Field(..., description="╨Я╤Г╤В╤М ╨╛╤В╨╜╨╛╤Б╨╕╤В╨╡╨╗╤М╨╜╨╛ base_url (╨╜╨░╨┐╤А╨╕╨╝╨╡╤А, /auth).")
    query: Dict[str, Any] = Field(
        default_factory=dict, description="╨Я╨░╤А╨░╨╝╨╡╤В╤А╤Л ╤Б╤В╤А╨╛╨║╨╕ ╨╖╨░╨┐╤А╨╛╤Б╨░."
    )
    headers: Dict[str, str] = Field(
        default_factory=dict, description="╨Ф╨╛╨┐╨╛╨╗╨╜╨╕╤В╨╡╨╗╤М╨╜╤Л╨╡ ╨╖╨░╨│╨╛╨╗╨╛╨▓╨║╨╕."
    )
    body: Optional[Dict[str, Any]] = Field(
        default=None, description="╨в╨╡╨╗╨╛ ╨╖╨░╨┐╤А╨╛╤Б╨░ (JSON)."
    )
    expected_status: int = Field(
        200, description="╨Ю╨╢╨╕╨┤╨░╨╡╨╝╤Л╨╣ HTTP-╤Б╤В╨░╤В╤Г╤Б ╨╛╤В╨▓╨╡╤В╨░."
    )
    expected_body_contains: Optional[Dict[str, Any]] = Field(
        default=None,
        description="╨Ъ╨╗╤О╤З╨╕/╨╖╨╜╨░╤З╨╡╨╜╨╕╤П, ╨║╨╛╤В╨╛╤А╤Л╨╡ ╨┤╨╛╨╗╨╢╨╜╤Л ╨┐╤А╨╕╤Б╤Г╤В╤Б╤В╨▓╨╛╨▓╨░╤В╤М ╨▓ JSON-╨╛╤В╨▓╨╡╤В╨╡.",
    )


class TestStep(BaseModel):
    """╨Ю╨┤╨╕╨╜ ╤И╨░╨│ ╤В╨╡╤Б╤В-╨║╨╡╨╣╤Б╨░."""

    id: int = Field(..., description="╨Я╨╛╤А╤П╨┤╨║╨╛╨▓╤Л╨╣ ╨╜╨╛╨╝╨╡╤А ╤И╨░╨│╨░ ╨▓ ╨║╨╡╨╣╤Б╨╡.")
    description: str = Field(..., description="╨з╨╡╨╗╨╛╨▓╨╡╨║╨╛╤З╨╕╤В╨░╨╡╨╝╨╛╨╡ ╨╛╨┐╨╕╤Б╨░╨╜╨╕╨╡ ╤И╨░╨│╨░.")
    type: StepType = Field(..., description="╨в╨╕╨┐ ╤И╨░╨│╨░: ui/api/manual.")
    action: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "╨б╤В╤А╤Г╨║╤В╤Г╤А╨╕╤А╨╛╨▓╨░╨╜╨╜╨╛╨╡ ╨╛╨┐╨╕╤Б╨░╨╜╨╕╨╡ ╨┤╨╡╨╣╤Б╤В╨▓╨╕╤П. ╨Ф╨╗╤П ui ╨╛╨╢╨╕╨┤╨░╨╡╤В╤Б╤П ╤Д╨╛╤А╨╝╨░ UIAction,"
            " ╨┤╨╗╤П api тАФ APIAction. ╨Ф╨╗╤П manual ╨╝╨╛╨╢╨╡╤В ╨▒╤Л╤В╤М None."
        ),
    )
    expected: Optional[str] = Field(
        default=None,
        description="╨Ъ╤А╨░╤В╨║╨╛╨╡ ╨╛╨┐╨╕╤Б╨░╨╜╨╕╨╡ ╨╛╨╢╨╕╨┤╨░╨╡╨╝╨╛╨│╨╛ ╤А╨╡╨╖╤Г╨╗╤М╤В╨░╤В╨░ ╨╕╨╝╨╡╨╜╨╜╨╛ ╨┤╨╗╤П ╤Н╤В╨╛╨│╨╛ ╤И╨░╨│╨░.",
    )


class TestCase(BaseModel):
    """╨в╨╡╤Б╤В-╨║╨╡╨╣╤Б ╨┤╨╗╤П ╨║╨╛╨╜╨║╤А╨╡╤В╨╜╨╛╨╣ ╤Д╨╕╤З╨╕."""

    id: str = Field(..., description="╨г╨╜╨╕╨║╨░╨╗╤М╨╜╤Л╨╣ ╨╕╨┤╨╡╨╜╤В╨╕╤Д╨╕╨║╨░╤В╨╛╤А ╤В╨╡╤Б╤В-╨║╨╡╨╣╤Б╨░.")
    title: str = Field(..., description="╨Ъ╤А╨░╤В╨║╨╛╨╡ ╨╜╨░╨╖╨▓╨░╨╜╨╕╨╡ ╨║╨╡╨╣╤Б╨░.")
    description: Optional[str] = Field(
        default=None, description="╨а╨░╤Б╤И╨╕╤А╨╡╨╜╨╜╨╛╨╡ ╨╛╨┐╨╕╤Б╨░╨╜╨╕╨╡/╤Ж╨╡╨╗╤М ╨║╨╡╨╣╤Б╨░."
    )
    feature: Optional[str] = Field(
        default=None, description="╨б╨▓╤П╨╖╨░╨╜╨╜╨░╤П ╤Д╨╕╤З╨░/╨╝╨╛╨┤╤Г╨╗╤М ╤Б╨╕╤Б╤В╨╡╨╝╤Л."
    )
    preconditions: List[str] = Field(
        default_factory=list,
        description="╨Я╤А╨╡╨┤╤Г╤Б╨╗╨╛╨▓╨╕╤П: ╤З╤В╨╛ ╨┤╨╛╨╗╨╢╨╜╨╛ ╨▒╤Л╤В╤М ╨▓╤Л╨┐╨╛╨╗╨╜╨╡╨╜╨╛/╨╜╨░╤Б╤В╤А╨╛╨╡╨╜╨╛ ╨┤╨╛ ╤Б╤В╨░╤А╤В╨░.",
    )
    steps: List[TestStep] = Field(
        default_factory=list, description="╨и╨░╨│╨╕ ╤Б╤Ж╨╡╨╜╨░╤А╨╕╤П."
    )
    expected_result: str = Field(
        ..., description="╨Ш╤В╨╛╨│╨╛╨▓╤Л╨╣ ╨╛╨╢╨╕╨┤╨░╨╡╨╝╤Л╨╣ ╤А╨╡╨╖╤Г╨╗╤М╤В╨░╤В ╨▓╤Б╨╡╨│╨╛ ╨║╨╡╨╣╤Б╨░."
    )
    priority: Priority = Field(
        default=Priority.MEDIUM, description="╨Я╤А╨╕╨╛╤А╨╕╤В╨╡╤В ╨║╨╡╨╣╤Б╨░."
    )
    tags: List[str] = Field(
        default_factory=list,
        description="╨Я╤А╨╛╨╕╨╖╨▓╨╛╨╗╤М╨╜╤Л╨╡ ╤В╨╡╨│╨╕: smoke, regression, api, ui ╨╕ ╤В.╨┐.",
    )


class TestSuite(BaseModel):
    """╨Э╨░╨▒╨╛╤А ╤В╨╡╤Б╤В-╨║╨╡╨╣╤Б╨╛╨▓ ╨┤╨╗╤П ╨╛╨┤╨╜╨╛╨╣ ╤Д╨╕╤З╨╕ ╨╕╨╗╨╕ ╨╝╨╛╨┤╤Г╨╗╤П."""

    suite: str = Field(..., description="╨Э╨░╨╖╨▓╨░╨╜╨╕╨╡ ╨╜╨░╨▒╨╛╤А╨░/╤Д╨╕╤З╨╕.")
    feature: Optional[str] = Field(
        default=None, description="╨Ф╨╛╨┐╨╛╨╗╨╜╨╕╤В╨╡╨╗╤М╨╜╨╛╨╡ ╨╜╨░╨╖╨▓╨░╨╜╨╕╨╡ ╤Д╨╕╤З╨╕, ╨╡╤Б╨╗╨╕ ╨╜╤Г╨╢╨╜╨╛."
    )
    description: Optional[str] = Field(
        default=None, description="╨Ю╨▒╤Й╨╡╨╡ ╨╛╨┐╨╕╤Б╨░╨╜╨╕╨╡ ╨╛╨▒╨╗╨░╤Б╤В╨╕ ╤В╨╡╤Б╤В╨╕╤А╨╛╨▓╨░╨╜╨╕╤П."
    )
    cases: List[TestCase] = Field(
        default_factory=list, description="╨б╨┐╨╕╤Б╨╛╨║ ╤В╨╡╤Б╤В-╨║╨╡╨╣╤Б╨╛╨▓."
    )


class StepResult(BaseModel):
    step_id: int
    status: StepStatus
    actual: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    attachments: List[str] = Field(
        default_factory=list,
        description="╨б╤Б╤Л╨╗╨║╨╕ ╨╜╨░ ╤Б╨║╤А╨╕╨╜╤И╨╛╤В╤Л, ╤Д╨░╨╣╨╗╤Л ╨╗╨╛╨│╨╛╨▓ ╨╕ ╨┤╤А. ╨░╤А╤В╨╡╤Д╨░╨║╤В╤Л.",
    )


class CaseResult(BaseModel):
    case_id: str
    status: StepStatus
    step_results: List[StepResult] = Field(default_factory=list)
    notes: Optional[str] = None


class TestRunStatus(str, Enum):
    PASSED = "pass"
    FAILED = "fail"
    PARTIAL = "partial"


class TestRunResult(BaseModel):
    """╨а╨╡╨╖╤Г╨╗╤М╤В╨░╤В ╨╛╨┤╨╜╨╛╨│╨╛ ╨┐╤А╨╛╨│╨╛╨╜╨░ ╨╜╨░╨▒╨╛╤А╨░ ╤В╨╡╤Б╤В-╨║╨╡╨╣╤Б╨╛╨▓."""

    id: str = Field(..., description="╨Ш╨┤╨╡╨╜╤В╨╕╤Д╨╕╨║╨░╤В╨╛╤А ╨┐╤А╨╛╨│╨╛╨╜╨░ (╨╜╨░╨┐╤А╨╕╨╝╨╡╤А, timestamp).")
    suite_name: str
    started_at: datetime
    finished_at: datetime
    env: Optional[str] = Field(default=None, description="╨Ю╨║╤А╤Г╨╢╨╡╨╜╨╕╨╡: dev/stage/prod.")
    summary_status: TestRunStatus
    case_results: List[CaseResult] = Field(default_factory=list)
    extra: Dict[str, Any] = Field(default_factory=dict)


class ChecklistItem(BaseModel):
    """╨н╨╗╨╡╨╝╨╡╨╜╤В ╤З╨╡╨║-╨╗╨╕╤Б╤В╨░ ╨┤╨╗╤П ╨▒╤Л╤Б╤В╤А╨╛╨│╨╛ ╨┐╤А╨╛╨│╨╛╨╜╨░."""

    id: str = Field(..., description="╨Э╨░╨┐╤А╨╕╨╝╨╡╤А, ╤Б╤Б╤Л╨╗╨║╨░ ╨╜╨░ test case id.")
    title: str
    description: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    tags: List[str] = Field(default_factory=list)


class Checklist(BaseModel):
    """╨з╨╡╨║-╨╗╨╕╤Б╤В ╨┤╨╗╤П ╤А╤Г╤З╨╜╨╛╨│╨╛ ╤В╨╡╤Б╤В╨╕╤А╨╛╨▓╨░╨╜╨╕╤П."""

    feature: str
    items: List[ChecklistItem] = Field(default_factory=list)

