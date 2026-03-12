## Contributing to ai_tester

Thanks for your interest in contributing!

### Local development

1. Clone the repo:

```bash
git clone https://github.com/q1nn2/ai_tester.git
cd ai_tester
```

2. Install dependencies:

```bash
pip install -r requirements.txt
pip install pytest
```

3. Run tests:

```bash
pytest
```

### Code style

- Target Python 3.11+.
- Use type hints everywhere where it makes sense.
- Recommended tools (optional, but helpful):
  - `black` for formatting;
  - `ruff` for linting.

Example:

```bash
black ai_tester tests
ruff check ai_tester tests
```

### Project structure

- `ai_tester/config.py` — configuration model and loader.
- `ai_tester/models.py` — Pydantic models for test suites, cases, steps and results.
- `ai_tester/suites.py` — utilities for loading/saving/filtering `TestSuite`.
- `ai_tester/runner.py` — async core for running suites and sync wrappers.
- `ai_tester/step_executors.py` — registry of step executors (UI/API, future plugins).
- `ai_tester/docs.py` — conversion between `TestSuite` and checklists.
- `ai_tester/llm_agent.py` — interaction with LLM and markdown summaries.
- `ai_tester/cli.py` — Typer-based CLI entrypoint.

### Feature / bug reports

- When opening an issue, please:
  - describe your environment (Python version, OS);
  - provide minimal reproducible examples (YAML/JSON and commands you ran);
  - include relevant logs or stack traces where possible.

