from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich import print
from rich.prompt import Confirm

from . import __version__
from .config import AIConfig, EnvConfig, load_config
from .models import TestRunResult, TestSuite
from . import llm_agent  # type: ignore[reportMissingImports]
from . import docs as docs_module  # type: ignore[reportMissingImports]
from . import runner as runner_module  # type: ignore[reportMissingImports]
from .suites import filter_suite_by_tags, load_suite, save_run_result


app = typer.Typer(
    help=(
        "AI-агент для тестовой документации и ручного тестирования: "
        "генерация тест-кейсов, чек-листов и полу-автоматический прогон UI/API-сценариев."
    )
)


def _select_env(cfg: AIConfig, env_option: Optional[str]) -> Optional[EnvConfig]:
    """
    Выбрать окружение по имени опции CLI или AI_TESTER_ENV.
    """
    effective_env = env_option or os.getenv("AI_TESTER_ENV")
    if effective_env is None:
        return None

    env_cfg = next((e for e in cfg.envs if e.name == effective_env), None)
    if env_cfg is None:
        available = ", ".join(e.name for e in cfg.envs) or "-"
        raise typer.BadParameter(
            f"Окружение '{effective_env}' не найдено в ai-tester.config.yaml. "
            f"Доступные окружения: {available}"
        )
    return env_cfg


@app.command(help="╨П╤Б╨╛╨▒╨╡╨╜╨╛╤З╨╕╨╡ ╨┐╨╛╨┤╨┤╨╡╤А╨╢╨║╨╛╨╣ JSON/YAML-╤Д╨░╨╣╨╗╤Г TestSuite.")
def validate(
    suite_path: Path = typer.Argument(..., help="╨Я╤Г╤В╤М ╨║ JSON/YAML-╤Д╨░╨╣╨╗╤Г ╤Б TestSuite."),
) -> None:
    try:
        suite = _load_suite(suite_path)
    except Exception as exc:  # noqa: BLE001
        print(f"[red]Файл невалиден:[/red] {exc!r}")
        raise typer.Exit(code=1)

    print(f"[green]OK[/green]: загружен suite '{suite.suite}', кейсов: {len(suite.cases)}")


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Показать версию и выйти.",
    ),
    info: Optional[bool] = typer.Option(
        None,
        "--info",
        help="Показать информацию о конфигурации ai_tester и выйти.",
    ),
) -> None:
    if version:
        print(f"[bold]ai-tester[/bold] v{__version__}")
        raise typer.Exit()

    if info:
        try:
            cfg = load_config()
        except RuntimeError as exc:
            print(f"[red]{exc}[/red]")
            raise typer.Exit(code=1)

        print("[bold]ai-tester configuration[/bold]")
        print(f"- docs_dir: {cfg.docs_dir}")
        print(f"- sessions_dir: {cfg.sessions_dir}")
        if cfg.envs:
            print("- envs:")
            for env in cfg.envs:
                print(
                    f"  - {env.name}: base_url={env.base_url or '-'}, "
                    f"api_base_url={env.api_base_url or '-'}"
                )
        else:
            print("- envs: (none)")
        print(f"- LLM base_url: {cfg.llm.base_url}")
        print(f"- LLM model: {cfg.llm.model}")
        print(f"- LLM api_key_env: {cfg.llm.api_key_env}")
        raise typer.Exit()


@app.command(
    help=(
        "Сгенерировать документацию по описанию фичи: "
        "TestSuite (JSON/YAML) и чек-лист (Markdown) с использованием LLM."
    )
)
def docs(
    feature: str = typer.Argument(
        ...,
        help="Название фичи/области функциональности.",
    ),
    source: Optional[Path] = typer.Option(
        None,
        "--source",
        "-s",
        help=(
            "Файл с описанием фичи/требований. Если не указан, текст читается из stdin."
        ),
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--out",
        "-o",
        help=(
            "Путь для сохранения JSON/YAML с TestSuite. "
            "По умолчанию — tests/ai-docs/<feature>.yaml."
        ),
    ),
    checklist_md: Optional[Path] = typer.Option(
        None,
        "--checklist-md",
        help=(
            "Путь для сохранения чек-листа в Markdown. "
            "По умолчанию — tests/ai-docs/<feature>-checklist.md."
        ),
    ),
    no_checklist_descriptions: bool = typer.Option(
        False,
        "--no-checklist-descriptions",
        help="Не включать описания тест-кейсов в сгенерированный чек-лист.",
    ),
    no_checklist_tags: bool = typer.Option(
        False,
        "--no-checklist-tags",
        help="Не включать теги в сгенерированный чек-лист.",
    ),
) -> None:
    try:
        cfg = load_config()
    except RuntimeError as exc:
        print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)

    if source is not None:
        text = source.read_text(encoding="utf-8")
    else:
        print(
            "[cyan]Введите описание фичи из stdin. "
            "Завершите ввод Ctrl+D (Linux/macOS) или Ctrl+Z (Windows).[/cyan]"
        )
        text = typer.get_text_stream("stdin").read()

    if not text.strip():
        raise typer.BadParameter("Текст описания фичи пуст.")

    print("[cyan]Генерация набора тестов через LLM...[/cyan]")
    suite: TestSuite = llm_agent.generate_suite_from_text(text, feature=feature, config=cfg.llm)

    docs_dir = cfg.docs_dir
    docs_dir.mkdir(parents=True, exist_ok=True)

    if output is None:
        output = docs_dir / f"{feature}.yaml"

    import yaml

    output.write_text(
        yaml.safe_dump(
            suite.model_dump(mode="python"),
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    if checklist_md is None:
        checklist_md = docs_dir / f"{feature}-checklist.md"

    checklist = docs_module.checklist_from_suite(suite)
    md = docs_module.checklist_to_markdown(
        checklist,
        include_descriptions=not no_checklist_descriptions,
        include_tags=not no_checklist_tags,
    )
    checklist_md.write_text(md, encoding="utf-8")

    print(f"[green]Набор тестов сохранён в:[/green] {output}")
    print(f"[green]Чек-лист сохранён в:[/green] {checklist_md}")


@app.command(
    help=(
        "Сгенерировать только чек-лист Markdown из существующего TestSuite "
        "(без обращения к LLM)."
    )
)
def docs_checklist(
    suite_path: Path = typer.Argument(
        ..., help="Путь к JSON/YAML-файлу с TestSuite."
    ),
    checklist_md: Optional[Path] = typer.Option(
        None,
        "--out",
        "-o",
        help=(
            "Путь для сохранения чек-листа в Markdown. "
            "По умолчанию — <suite>-checklist.md в docs_dir из конфигурации."
        ),
    ),
    no_descriptions: bool = typer.Option(
        False,
        "--no-descriptions",
        help="Не включать описания тест-кейсов.",
    ),
    no_tags: bool = typer.Option(
        False,
        "--no-tags",
        help="Не включать теги тест-кейсов.",
    ),
) -> None:
    try:
        cfg = load_config()
    except RuntimeError as exc:
        print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)

    suite = load_suite(suite_path)

    if checklist_md is None:
        checklist_md = cfg.docs_dir / f"{suite.suite}-checklist.md"

    checklist = docs_module.checklist_from_suite(suite)
    md = docs_module.checklist_to_markdown(
        checklist,
        include_descriptions=not no_descriptions,
        include_tags=not no_tags,
    )
    checklist_md.write_text(md, encoding="utf-8")
    print(f"[green]Чек-лист сохранён в:[/green] {checklist_md}")


@app.command(
    help=(
        "Запустить полу-автоматический прогон набора тестов "
        "с поддержкой фильтрации по тегам."
    )
)
def run(
    suite_path: Path = typer.Argument(..., help="╨Я╤Г╤В╤М ╨║ JSON/YAML-╤Д╨░╨╣╨╗╤Г ╤Б TestSuite."),
    env: Optional[str] = typer.Option(
        None,
        "--env",
        "-e",
        help="╨Ш╨╝╤П ╨╛╨║╤А╤Г╨╢╨╡╨╜╨╕╤П ╨╕╨╖ ai-tester.config.yaml (dev/stage/prod ╨╕ ╤В.╨┐.).",
    ),
    out: Optional[Path] = typer.Option(
        None,
        "--out",
        "-o",
        help=(
            "Путь для сохранения JSON-отчёта о прогоне. "
            "По умолчанию — tests/ai-sessions/run-<ts>.json."
        ),
    ),
    only_tags: Optional[str] = typer.Option(
        None,
        "--only-tags",
        help="Запускать только кейсы, содержащие хотя бы один из указанных тегов (через запятую).",
    ),
    exclude_tags: Optional[str] = typer.Option(
        None,
        "--exclude-tags",
        help="Исключить кейсы, содержащие хотя бы один из указанных тегов (через запятую).",
    ),
    max_concurrent: int = typer.Option(
        3,
        "--max-concurrent",
        help="Максимальное количество тест-кейсов, запускаемых параллельно.",
    ),
) -> None:
    try:
        cfg = load_config()
    except RuntimeError as exc:
        print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)
    suite = load_suite(suite_path)

    suite = filter_suite_by_tags(
        suite,
        only_tags=only_tags.split(",") if only_tags else None,
        exclude_tags=exclude_tags.split(",") if exclude_tags else None,
    )

    if not suite.cases:
        print("[yellow]После применения фильтров по тегам не осталось ни одного кейса.[/yellow]")
        raise typer.Exit(code=0)

    env_cfg = _select_env(cfg, env)

    print("[cyan]Запуск набора тестов...[/cyan]")

    result: TestRunResult = runner_module.run_suite_sync(
        suite=suite,
        env_name=env_cfg.name if env_cfg else None,
        base_url=env_cfg.base_url if env_cfg else None,
        api_base_url=env_cfg.api_base_url if env_cfg else None,
        max_concurrent=max_concurrent,
    )

    sessions_dir = cfg.sessions_dir
    sessions_dir.mkdir(parents=True, exist_ok=True)

    if out is None:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        out = sessions_dir / f"run-{timestamp}.json"

    save_run_result(result, out)
    print(f"[green]JSON-отчёт о прогоне сохранён в:[/green] {out}")

    summary_md = llm_agent.summarize_run_to_markdown(result)
    summary_path = out.with_suffix(".md")
    summary_path.write_text(summary_md, encoding="utf-8")
    print(f"[green]Сводка по прогону сохранена в:[/green] {summary_path}")


@app.command(
    help=(
        "Интерактивная сессия ручного прогона набора тестов "
        "с возможностью автоматизации UI/API-шагов."
    )
)
def session(
    suite_path: Path = typer.Argument(..., help="╨Я╤Г╤В╤М ╨║ JSON/YAML-╤Д╨░╨╣╨╗╤Г ╤Б TestSuite."),
    env: Optional[str] = typer.Option(
        None,
        "--env",
        "-e",
        help="Имя окружения из ai-tester.config.yaml.",
    ),
    only_tags: Optional[str] = typer.Option(
        None,
        "--only-tags",
        help="Пускать в сессию только кейсы с указанными тегами (через запятую).",
    ),
    exclude_tags: Optional[str] = typer.Option(
        None,
        "--exclude-tags",
        help="Исключить из сессии кейсы с указанными тегами (через запятую).",
    ),
) -> None:
    try:
        cfg = load_config()
    except RuntimeError as exc:
        print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)

    suite = load_suite(suite_path)

    suite = filter_suite_by_tags(
        suite,
        only_tags=only_tags.split(",") if only_tags else None,
        exclude_tags=exclude_tags.split(",") if exclude_tags else None,
    )

    if not suite.cases:
        print("[yellow]После применения фильтров по тегам не осталось ни одного кейса.[/yellow]")
        raise typer.Exit(code=0)

    env_cfg = _select_env(cfg, env)

    print(f"[bold]Интерактивная сессия по набору тестов:[/bold] {suite.suite}")
    print(
        "[cyan]По очереди просматривайте кейсы и выполняйте шаги. "
        "Для manual-шагов потребуется подтверждение и комментарий.[/cyan]"
    )

    manual_notes = []

    for case in suite.cases:
        print()
        print(f"[bold]Кейс:[/bold] {case.id} – {case.title}")
        if not Confirm.ask("Выполнить этот кейс?", default=True):
            continue

        auto = Confirm.ask(
            "Автоматически выполнять ui/api шаги, где это возможно?", default=True
        )

        if auto:
            case_result = runner_module.run_single_case_sync(
                case=case,
                env_name=env_cfg.name if env_cfg else None,
                base_url=env_cfg.base_url if env_cfg else None,
                api_base_url=env_cfg.api_base_url if env_cfg else None,
            )
        else:
            case_result = runner_module.create_empty_case_result(case)

        for step in case.steps:
            print(f"- Шаг {step.id}: {step.description}")
            if step.type.name.lower() == "manual":
                passed = Confirm.ask("Шаг выполнен успешно?", default=True)
                note = typer.prompt(
                    "Комментарий/замечания по шагу (можно оставить пустым)", default=""
                )
                manual_notes.append((case.id, step.id, note))
                runner_module.mark_manual_step(case_result, step_id=step.id, passed=passed, note=note)

        print(f"[green]Кейс {case.id} завершён со статусом {case_result.status}.[/green]")

    print("[bold green]Интерактивная сессия завершена.[/bold green]")
    if manual_notes:
        print(
            "[cyan]Вы можете сохранить заметки по manual-шагам в отдельный документ "
            "или перенести их в систему отслеживания дефектов.[/cyan]"
        )


@app.command(help="Создать базовый ai-tester.config.yaml и пример TestSuite.")
def init(
    force: bool = typer.Option(
        False,
        "--force",
        help="Перезаписать файлы, если они уже существуют.",
    )
) -> None:
    cfg_path = Path("ai-tester.config.yaml")
    docs_dir = Path("tests/ai-docs")
    docs_dir.mkdir(parents=True, exist_ok=True)
    example_suite_path = docs_dir / "Example.yaml"

    if cfg_path.exists() and not force:
        print(f"[yellow]{cfg_path} уже существует, используйте --force для перезаписи.[/yellow]")
    else:
        from .templates import load_text

        cfg_path.write_text(load_text("config_default.yaml"), encoding="utf-8")
        print(f"[green]Создан {cfg_path}[/green]")

    if example_suite_path.exists() and not force:
        print(f"[yellow]{example_suite_path} уже существует, используйте --force для перезаписи.[/yellow]")
    else:
        from .templates import load_text

        example_suite_path.write_text(
            load_text("example_suite.yaml"),
            encoding="utf-8",
        )
        print(f"[green]Создан {example_suite_path}[/green]")


@app.command(
    help=(
        "Интерактивный мастер создания минимального YAML-сценария без использования LLM."
    )
)
def wizard(
    feature: str = typer.Option(
        ...,
        "--feature",
        "-f",
        help="Название фичи для нового набора тестов.",
    ),
    out: Optional[Path] = typer.Option(
        None,
        "--out",
        "-o",
        help=(
            "Путь к YAML-файлу. По умолчанию — tests/ai-docs/<feature>-wizard.yaml "
            "(директория будет создана при необходимости)."
        ),
    ),
) -> None:
    try:
        cfg = AIConfig.load()
    except RuntimeError as exc:
        print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)

    title = typer.prompt("Название тест-кейса")
    expected = typer.prompt("Ожидаемый результат")
    step_desc = typer.prompt("Описание первого шага")
    step_type = typer.prompt("Тип шага (ui/api/manual)", default="manual")

    suite = {
        "suite": feature,
        "description": f"Создано через ai_tester wizard для фичи {feature}",
        "cases": [
            {
                "id": "WIZ-001",
                "title": title,
                "preconditions": [],
                "steps": [
                    {
                        "id": 1,
                        "description": step_desc,
                        "type": step_type,
                    }
                ],
                "expected_result": expected,
                "priority": "medium",
                "tags": [],
            }
        ],
    }

    if out is None:
        out = cfg.docs_dir / f"{feature}-wizard.yaml"
    out.parent.mkdir(parents=True, exist_ok=True)

    import yaml

    out.write_text(
        yaml.safe_dump(suite, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    print(f"[green]Сценарий сохранён в:[/green] {out}")


def run_cli() -> None:
    app()


if __name__ == "__main__":
    run_cli()

