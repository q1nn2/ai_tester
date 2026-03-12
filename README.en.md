# ai_tester (short English README)

ai_tester is a CLI tool that helps you turn **plain-text feature descriptions** into **test suites and checklists**, and then run them in a semi-automated way (UI + API + manual steps).

> Main documentation is currently in Russian (`README.md`). This file gives a minimal English overview.

## What it does

- **Generate test suites from feature docs.** You write requirements in a `.md`/`.txt` file, ai_tester uses an LLM to generate a `TestSuite` (YAML/JSON) and a Markdown checklist.
- **Store scenarios as code.** Test suites live in your repo under `tests/ai-docs/*.yaml`, validated by Pydantic models.
- **Run UI + API + manual steps together.** UI steps are executed via Playwright, API steps via httpx, manual steps are confirmed interactively.
- **Support both CI and manual sessions.** You can run smoke/regression in CI and also run interactive sessions for exploratory or manual testing.

## Quick start (very short)

```bash
git clone https://github.com/q1nn2/ai_tester.git
cd ai_tester

pip install -r requirements.txt
playwright install
```

Initialize config and example:

```bash
python -m ai_tester.cli init
```

This creates:

- `ai-tester.config.yaml` — config for LLM and environments;
- `tests/ai-docs/Example.yaml` — example `TestSuite`.

Generate tests from a feature description:

```bash
python -m ai_tester.cli docs "Auth" --source docs/ai-features/feature_auth.md
```

Run the suite:

```bash
python -m ai_tester.cli run tests/ai-docs/Авторизация.yaml --env dev
```

Start an interactive manual session:

```bash
python -m ai_tester.cli session tests/ai-docs/Авторизация.yaml --env dev
```

For full details, see the Russian README: `README.md`.

