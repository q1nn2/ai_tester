from pathlib import Path

import yaml

from ai_tester.suites import filter_suite_by_tags, load_suite


def test_filter_suite_by_tags_only(tmp_path: Path) -> None:
    data = {
        "suite": "Example",
        "cases": [
            {
                "id": "A",
                "title": "A",
                "expected_result": "ok",
                "steps": [],
                "tags": ["smoke"],
            },
            {
                "id": "B",
                "title": "B",
                "expected_result": "ok",
                "steps": [],
                "tags": ["regression"],
            },
        ],
    }
    path = tmp_path / "suite.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")

    suite = load_suite(path)
    filtered = filter_suite_by_tags(suite, only_tags=["smoke"], exclude_tags=None)

    assert [c.id for c in filtered.cases] == ["A"]

