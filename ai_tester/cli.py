from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich import print
from rich.prompt import Confirm

from . import __version__
from .config import AIConfig
from .models import TestRunResult, TestSuite
from . import llm_agent  # type: ignore[reportMissingImports]
from . import docs as docs_module  # type: ignore[reportMissingImports]
from . import runner as runner_module  # type: ignore[reportMissingImports]


app = typer.Typer(help="AI-╨░╨│╨╡╨╜╤В ╨┤╨╗╤П ╤В╨╡╤Б╤В╨╛╨▓╨╛╨╣ ╨┤╨╛╨║╤Г╨╝╨╡╨╜╤В╨░╤Ж╨╕╨╕ ╨╕ ╤А╤Г╤З╨╜╨╛╨│╨╛ ╤В╨╡╤Б╤В╨╕╤А╨╛╨▓╨░╨╜╨╕╤П.")


def _load_suite(path: Path) -> TestSuite:
    if not path.exists():
        raise typer.BadParameter(f"╨д╨░╨╣╨╗ ╤Б ╤В╨╡╤Б╤В-╨║╨╡╨╣╤Б╨░╨╝╨╕ ╨╜╨╡ ╨╜╨░╨╣╨┤╨╡╨╜: {path}")

    import json
    import yaml

    text = path.read_text(encoding="utf-8")

    if path.suffix.lower() in {".yml", ".yaml"}:
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)

    return TestSuite.model_validate(data)


def _save_run_result(result: TestRunResult, path: Path) -> None:
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="╨Я╨╛╨║╨░╨╖╨░╤В╤М ╨▓╨╡╤А╤Б╨╕╤О ╨╕ ╨▓╤Л╨╣╤В╨╕.",
    ),
) -> None:
    if version:
        print(f"[bold]ai-tester[/bold] v{__version__}")
        raise typer.Exit()


@app.command(help="╨б╨│╨╡╨╜╨╡╤А╨╕╤А╨╛╨▓╨░╤В╤М ╤В╨╡╤Б╤В╨╛╨▓╤Г╤О ╨┤╨╛╨║╤Г╨╝╨╡╨╜╤В╨░╤Ж╨╕╤О (╨║╨╡╨╣╤Б╤Л + ╤З╨╡╨║-╨╗╨╕╤Б╤В) ╨╕╨╖ ╨╛╨┐╨╕╤Б╨░╨╜╨╕╤П ╤Д╨╕╤З╨╕.")
def docs(
    feature: str = typer.Argument(..., help="╨Э╨░╨╖╨▓╨░╨╜╨╕╨╡ ╤Д╨╕╤З╨╕/╨╛╨▒╨╗╨░╤Б╤В╨╕ ╤В╨╡╤Б╤В╨╕╤А╨╛╨▓╨░╨╜╨╕╤П."),
    source: Optional[Path] = typer.Option(
        None,
        "--source",
        "-s",
        help="╨д╨░╨╣╨╗ ╤Б ╨╛╨┐╨╕╤Б╨░╨╜╨╕╨╡╨╝ ╤В╤А╨╡╨▒╨╛╨▓╨░╨╜╨╕╨╣/╤В╨╕╨║╨╡╤В╨░. ╨Х╤Б╨╗╨╕ ╨╜╨╡ ╤Г╨║╨░╨╖╨░╨╜ тАФ ╤З╨╕╤В╨░╨╡╨╝ stdin.",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--out",
        "-o",
        help="╨Я╤Г╤В╤М ╨┤╨╗╤П ╤Б╨╛╤Е╤А╨░╨╜╨╡╨╜╨╕╤П JSON/YAML ╤Б ╤В╨╡╤Б╤В╨░╨╝╨╕. ╨Я╨╛ ╤Г╨╝╨╛╨╗╤З╨░╨╜╨╕╤О тАФ tests/ai-docs/<feature>.yaml.",
    ),
    checklist_md: Optional[Path] = typer.Option(
        None,
        "--checklist-md",
        help="╨Я╤Г╤В╤М ╨┤╨╗╤П ╤Б╨╛╤Е╤А╨░╨╜╨╡╨╜╨╕╤П ╤З╨╡╨║-╨╗╨╕╤Б╤В╨░ ╨▓ Markdown. ╨Я╨╛ ╤Г╨╝╨╛╨╗╤З╨░╨╜╨╕╤О тАФ tests/ai-docs/<feature>-checklist.md.",
    ),
) -> None:
    cfg = AIConfig.load()

    if source is not None:
        text = source.read_text(encoding="utf-8")
    else:
        print("[cyan]╨з╨╕╤В╨░╤О ╨╛╨┐╨╕╤Б╨░╨╜╨╕╨╡ ╤Д╨╕╤З╨╕ ╨╕╨╖ stdin. ╨Ч╨░╨▓╨╡╤А╤И╨╕╤В╨╡ ╨▓╨▓╨╛╨┤ Ctrl+D (Linux/macOS) ╨╕╨╗╨╕ Ctrl+Z (Windows).[/cyan]")
        text = typer.get_text_stream("stdin").read()

    if not text.strip():
        raise typer.BadParameter("╨Ю╨┐╨╕╤Б╨░╨╜╨╕╨╡ ╤Д╨╕╤З╨╕ ╨┐╤Г╤Б╤В╨╛╨╡.")

    print("[cyan]╨У╨╡╨╜╨╡╤А╨╕╤А╤Г╤О ╤В╨╡╤Б╤В-╨║╨╡╨╣╤Б╤Л ╤Б ╨┐╨╛╨╝╨╛╤Й╤М╤О LLM...[/cyan]")
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
    md = docs_module.checklist_to_markdown(checklist)
    checklist_md.write_text(md, encoding="utf-8")

    print(f"[green]╨в╨╡╤Б╤В-╨║╨╡╨╣╤Б╤Л ╤Б╨╛╤Е╤А╨░╨╜╨╡╨╜╤Л ╨▓:[/green] {output}")
    print(f"[green]╨з╨╡╨║-╨╗╨╕╤Б╤В ╤Б╨╛╤Е╤А╨░╨╜╤С╨╜ ╨▓:[/green] {checklist_md}")


@app.command(help="╨Я╨╛╨╗╤Г-╨░╨▓╤В╨╛╨╝╨░╤В╨╕╤З╨╡╤Б╨║╨╕╨╣ ╨┐╤А╨╛╨│╨╛╨╜ ╨╖╨░╤А╨░╨╜╨╡╨╡ ╨╛╨┐╨╕╤Б╨░╨╜╨╜╤Л╤Е ╤Б╤Ж╨╡╨╜╨░╤А╨╕╨╡╨▓.")
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
        help="╨Я╤Г╤В╤М ╨┤╨╗╤П ╤Б╨╛╤Е╤А╨░╨╜╨╡╨╜╨╕╤П JSON-╨╛╤В╤З╤С╤В╨░ ╨╛ ╨┐╤А╨╛╨│╨╛╨╜╨╡. ╨Я╨╛ ╤Г╨╝╨╛╨╗╤З╨░╨╜╨╕╤О тАФ tests/ai-sessions/run-<ts>.json.",
    ),
) -> None:
    cfg = AIConfig.load()
    suite = _load_suite(suite_path)

    env_cfg = None
    if env is not None:
        env_cfg = next((e for e in cfg.envs if e.name == env), None)
        if env_cfg is None:
            raise typer.BadParameter(f"╨Ю╨║╤А╤Г╨╢╨╡╨╜╨╕╨╡ '{env}' ╨╜╨╡ ╨╜╨░╨╣╨┤╨╡╨╜╨╛ ╨▓ ai-tester.config.yaml")

    print("[cyan]╨Ч╨░╨┐╤Г╤Б╨║╨░╤О ╨┐╤А╨╛╨│╨╛╨╜ ╤Б╤Ж╨╡╨╜╨░╤А╨╕╨╡╨▓...[/cyan]")

    result: TestRunResult = asyncio.run(
        runner_module.run_suite(
            suite=suite,
            env_name=env_cfg.name if env_cfg else None,
            base_url=env_cfg.base_url if env_cfg else None,
            api_base_url=env_cfg.api_base_url if env_cfg else None,
        )
    )

    sessions_dir = cfg.sessions_dir
    sessions_dir.mkdir(parents=True, exist_ok=True)

    if out is None:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        out = sessions_dir / f"run-{timestamp}.json"

    _save_run_result(result, out)
    print(f"[green]JSON-╨╛╤В╤З╤С╤В ╨╛ ╨┐╤А╨╛╨│╨╛╨╜╨╡ ╤Б╨╛╤Е╤А╨░╨╜╤С╨╜ ╨▓:[/green] {out}")

    summary_md = llm_agent.summarize_run_to_markdown(result)
    summary_path = out.with_suffix(".md")
    summary_path.write_text(summary_md, encoding="utf-8")
    print(f"[green]╨а╨╡╨╖╤О╨╝╨╡ ╨┐╤А╨╛╨│╨╛╨╜╨░ ╤Б╨╛╤Е╤А╨░╨╜╨╡╨╜╨╛ ╨▓:[/green] {summary_path}")


@app.command(help="╨Ш╨╜╤В╨╡╤А╨░╨║╤В╨╕╨▓╨╜╨░╤П ╤Б╨╡╤Б╤Б╨╕╤П ╤А╤Г╤З╨╜╨╛╨│╨╛ ╤В╨╡╤Б╤В╨╕╤А╨╛╨▓╨░╨╜╨╕╤П ╤Б ╨┐╨╛╨┤╨┤╨╡╤А╨╢╨║╨╛╨╣ ╨░╨▓╤В╨╛╤И╨░╨│╨╛╨▓ UI/API.")
def session(
    suite_path: Path = typer.Argument(..., help="╨Я╤Г╤В╤М ╨║ JSON/YAML-╤Д╨░╨╣╨╗╤Г ╤Б TestSuite."),
    env: Optional[str] = typer.Option(
        None,
        "--env",
        "-e",
        help="╨Ш╨╝╤П ╨╛╨║╤А╤Г╨╢╨╡╨╜╨╕╤П ╨╕╨╖ ai-tester.config.yaml.",
    ),
) -> None:
    cfg = AIConfig.load()
    suite = _load_suite(suite_path)

    env_cfg = None
    if env is not None:
        env_cfg = next((e for e in cfg.envs if e.name == env), None)
        if env_cfg is None:
            raise typer.BadParameter(f"╨Ю╨║╤А╤Г╨╢╨╡╨╜╨╕╨╡ '{env}' ╨╜╨╡ ╨╜╨░╨╣╨┤╨╡╨╜╨╛ ╨▓ ai-tester.config.yaml")

    print(f"[bold]╨Ш╨╜╤В╨╡╤А╨░╨║╤В╨╕╨▓╨╜╨░╤П ╤Б╨╡╤Б╤Б╨╕╤П ╨┤╨╗╤П ╤Д╨╕╤З╨╕:[/bold] {suite.suite}")
    print("[cyan]╨С╤Г╨┤╤Г ╨┐╤А╨╡╨┤╨╗╨░╨│╨░╤В╤М ╤В╨╡╤Б╤В-╨║╨╡╨╣╤Б╤Л ╨┐╨╛ ╨╛╤З╨╡╤А╨╡╨┤╨╕. ╨Ь╨╛╨╢╨╜╨╛ ╨▓╨║╨╗╤О╤З╨░╤В╤М ╨░╨▓╤В╨╛╤И╨░╨│╨╕ ╨╕╨╗╨╕ ╨┐╤А╨╛╤Е╨╛╨┤╨╕╤В╤М ╨║╨╡╨╣╤Б╤Л ╤А╤Г╨║╨░╨╝╨╕.[/cyan]")

    manual_notes = []

    for case in suite.cases:
        print()
        print(f"[bold]╨Ъ╨╡╨╣╤Б:[/bold] {case.id} тАФ {case.title}")
        if not Confirm.ask("╨Ч╨░╨┐╤Г╤Б╨║╨░╤В╤М ╤Н╤В╨╛╤В ╨║╨╡╨╣╤Б?", default=True):
            continue

        auto = Confirm.ask("╨Я╤А╨╛╨▒╨╛╨▓╨░╤В╤М ╨░╨▓╤В╨╛╨╝╨░╤В╨╕╤З╨╡╤Б╨║╨╕ ╨▓╤Л╨┐╨╛╨╗╨╜╤П╤В╤М ui/api ╤И╨░╨│╨╕?", default=True)

        if auto:
            case_result = asyncio.run(
                runner_module.run_single_case(
                    case=case,
                    env_name=env_cfg.name if env_cfg else None,
                    base_url=env_cfg.base_url if env_cfg else None,
                    api_base_url=env_cfg.api_base_url if env_cfg else None,
                )
            )
        else:
            case_result = runner_module.create_empty_case_result(case)

        for step in case.steps:
            print(f"- ╨и╨░╨│ {step.id}: {step.description}")
            if step.type.name.lower() == "manual":
                passed = Confirm.ask("╨и╨░╨│ ╨▓╤Л╨┐╨╛╨╗╨╜╨╡╨╜ ╤Г╤Б╨┐╨╡╤И╨╜╨╛?", default=True)
                note = typer.prompt("╨Ч╨░╨╝╨╡╤З╨░╨╜╨╕╤П/╤Д╨░╨║╤В╨╕╤З╨╡╤Б╨║╨╕╨╣ ╤А╨╡╨╖╤Г╨╗╤М╤В╨░╤В (╨╛╨┐╤Ж╨╕╨╛╨╜╨░╨╗╤М╨╜╨╛)", default="")
                manual_notes.append((case.id, step.id, note))
                runner_module.mark_manual_step(case_result, step_id=step.id, passed=passed, note=note)

        print(f"[green]╨Ъ╨╡╨╣╤Б {case.id} ╨╖╨░╨▓╨╡╤А╤И╤С╨╜ ╤Б╨╛ ╤Б╤В╨░╤В╤Г╤Б╨╛╨╝ {case_result.status}.[/green]")

    print("[bold green]╨б╨╡╤Б╤Б╨╕╤П ╨╖╨░╨▓╨╡╤А╤И╨╡╨╜╨░.[/bold green]")
    if manual_notes:
        print("[cyan]╨б╨╛╨▒╤А╨░╨╜╤Л ╨╖╨░╨╝╨╡╤В╨║╨╕ ╨┐╨╛ ╤А╤Г╤З╨╜╤Л╨╝ ╤И╨░╨│╨░╨╝, ╨╕╤Е ╨╝╨╛╨╢╨╜╨╛ ╨╕╤Б╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╤М ╨┤╨╗╤П ╨▒╨░╨│-╤А╨╡╨┐╨╛╤А╤В╨╛╨▓.[/cyan]")


def run_cli() -> None:
    app()


if __name__ == "__main__":
    run_cli()

