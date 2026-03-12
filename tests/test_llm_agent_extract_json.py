import json

import pytest

from ai_tester.llm_agent import LLMError, _extract_json_from_text


def test_extract_json_plain_object() -> None:
    payload = '{"suite": "Example", "cases": []}'
    result = _extract_json_from_text(payload)
    assert result["suite"] == "Example"
    assert "cases" in result


def test_extract_json_fenced_block() -> None:
    text = """Some intro
```json
{"suite": "Example", "cases": []}
```
Some footer
"""
    result = _extract_json_from_text(text)
    assert result["suite"] == "Example"


def test_extract_json_with_noise() -> None:
    text = "Noise before {\"suite\": \"Example\", \"cases\": []} noise after"
    result = _extract_json_from_text(text)
    assert result["suite"] == "Example"


def test_extract_json_invalid_raises_llmerror() -> None:
    with pytest.raises(LLMError):
        _extract_json_from_text("this is not json at all")

