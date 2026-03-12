# ai_tester

AI-агент для тестовой документации и ручного тестирования: генерация тест-кейсов и чек-листов, полу-автоматический прогон сценариев, интерактивные сессии с поддержкой UI/API-шагов.

## Установка

```bash
git clone https://github.com/q1nn2/ai_tester.git
cd ai_tester

pip install -r requirements.txt
playwright install
```

## Конфигурация

Создайте файл `ai-tester.config.yaml` в корне проекта:

```yaml
llm:
  base_url: "https://api.openai.com/v1"
  model: "gpt-4.1-mini"
  api_key_env: "OPENAI_API_KEY"
  temperature: 0.2

docs_dir: "tests/ai-docs"
sessions_dir: "tests/ai-sessions"

envs:
  - name: "dev"
    base_url: "http://localhost:3000"
    api_base_url: "http://localhost:8000"
  - name: "stage"
    base_url: "https://stage.example.com"
    api_base_url: "https://api-stage.example.com"
```

Ключ LLM берётся из переменной окружения:

```bash
export OPENAI_API_KEY="sk-..."
# Windows PowerShell:
# $Env:OPENAI_API_KEY="sk-..."
```

## CLI

```bash
python -m ai_tester.cli --help
```

### Типичный сценарий

1. Напишите описание фичи в `feature_auth.txt`.
2. Сгенерируйте тесты и чек-лист:

   ```bash
   python -m ai_tester.cli docs "Авторизация" --source feature_auth.txt
   ```

   Появятся:

   - `tests/ai-docs/Авторизация.yaml`
   - `tests/ai-docs/Авторизация-checklist.md`

3. При необходимости отредактируйте `tests/ai-docs/Авторизация.yaml`
   (добавьте/измените шаги `ui/api/manual`).

4. Запустите полу-автоматический прогон:

   ```bash
   python -m ai_tester.cli run tests/ai-docs/Авторизация.yaml --env dev
   ```

   Результаты будут в `tests/ai-sessions` (`run-*.json` и `run-*.md`).

5. Для интерактивной ручной сессии:

   ```bash
   python -m ai_tester.cli session tests/ai-docs/Авторизация.yaml --env dev
   ```

## Стек

- Typer, Rich — CLI
- Pydantic — модели тест-кейсов и чек-листов
- LLM (опционально) — генерация документации
- Playwright, httpx — автоматизация UI и API-шагов

## Интеграция в процесс тестирования

- Храните `tests/ai-docs/*.yaml` в репозитории приложения.
- Разделяйте сценарии по тегам (`smoke`, `regression`, `ui`, `api` и т.п.).

Пример использования в CI (GitHub Actions):

```yaml
jobs:
  ai-tester-smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install deps
        run: |
          pip install -r requirements.txt
          playwright install
      - name: Run auth smoke
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          python -m ai_tester.cli run tests/ai-docs/Авторизация.yaml --env stage
```
