# ai_tester

AI-агент для тестовой документации и ручного тестирования: генерация тест-кейсов и чек-листов, полу-автоматический прогон сценариев, интерактивные сессии с поддержкой UI/API-шагов.

> English short README: _coming soon_ (`README.en.md`).

## Почему ai_tester

- **Живые требования → формальные сценарии.** Из текстового описания фичи LLM генерирует `TestSuite` + чек-лист, которые вы храните в репозитории.
- **Единый формат сценариев.** YAML/JSON, валидируемый через Pydantic-модели.
- **UI + API + manual в одном месте.** Один набор сценариев описывает и браузерные шаги (Playwright), и API-вызовы (httpx), и ручные проверки.
- **Полу-автоматический и интерактивный прогон.** Можно гонять регрессию в CI и проводить живые ручные сессии с подсказками шагов.

## Установка

```bash
git clone https://github.com/q1nn2/ai_tester.git
cd ai_tester

pip install -r requirements.txt
playwright install
```

После публикации в PyPI (roadmap) можно будет устанавливать так:

```bash
pip install ai-tester
ai-tester --help
```

## Быстрый старт

### 1. Инициализировать конфиг и примеры

```bash
python -m ai_tester.cli init
```

Будет создан:

- `ai-tester.config.yaml` — конфигурация LLM и окружений;
- `tests/ai-docs/Example.yaml` — пример `TestSuite`.

### 2. Настроить окружения в конфиге

Отредактируйте `ai-tester.config.yaml` под ваш стенд:

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
```

Ключ LLM берётся из переменной окружения:

```bash
export OPENAI_API_KEY="sk-..."
# Windows PowerShell:
# $Env:OPENAI_API_KEY="sk-..."
```

### 3. От требований к сценариям

1. Напишите текстовое описание фичи, например `docs/ai-features/feature_auth.md`.
2. Сгенерируйте сценарии и чек-лист:

   ```bash
   python -m ai_tester.cli docs "Авторизация" --source docs/ai-features/feature_auth.md
   ```

   Появятся:

   - `tests/ai-docs/Авторизация.yaml` — набор тест-кейсов (`TestSuite`);
   - `tests/ai-docs/Авторизация-checklist.md` — чек-лист для ручного прогона.

3. При необходимости отредактируйте `tests/ai-docs/Авторизация.yaml`
   (добавьте/измените шаги `ui/api/manual`, теги `smoke/regression/...`).

### 4. Полу-автоматический прогон

```bash
python -m ai_tester.cli run tests/ai-docs/Авторизация.yaml --env dev
```

Результаты будут в `tests/ai-sessions`:

- `run-*.json` — машинно-читабельный отчёт;
- `run-*.md` — человекочитаемая сводка.

### 5. Интерактивная ручная сессия

```bash
python -m ai_tester.cli session tests/ai-docs/Авторизация.yaml --env dev
```

CLI поочерёдно покажет кейсы и шаги, спросит, какие `manual`-шаги прошли и соберёт комментарии.

## Структура YAML-сценария

Сценарии (`TestSuite`) по умолчанию хранятся в `tests/ai-docs/*.yaml`.

Упрощённый пример:

```yaml
suite: "Авторизация"
description: "Сценарии авторизации пользователя"
cases:
  - id: "AUTH-UI-001"
    title: "Успешный логин через форму"
    preconditions: []
    steps:
      - id: 1
        description: "Открыть страницу логина"
        type: "ui"
        action:
          kind: "open_url"
          url: "/login"
      - id: 2
        description: "Ввести валидные логин и пароль и нажать Войти"
        type: "ui"
        action:
          kind: "fill"
          selector: "#login-form"
          text: "user@example.com / secret"
      - id: 3
        description: "Проверить успешный редирект в профиль"
        type: "manual"
        expected: "Пользователь видит страницу профиля без ошибок"
    expected_result: "Пользователь успешно входит в систему"
    priority: "high"
    tags: ["ui", "smoke", "auth"]
```

Ключевые сущности:

- `suite` — название набора тестов.
- `cases[]` — список тест-кейсов.
- `steps[]` — шаги внутри кейса:
  - `type: "ui" | "api" | "manual"`;
  - `action` — параметры для автоматизации (UI/API);
  - `expected` / `expected_result` — ожидаемый результат.

## CLI

```bash
python -m ai_tester.cli --help
```

Основные команды:

- `validate` — проверить, что YAML/JSON с `TestSuite` валиден.
- `docs` — сгенерировать `TestSuite` + чек-лист из текстовых требований.
- `docs_checklist` — построить чек-лист по уже существующему `TestSuite`.
- `run` — полу-автоматический прогон сценариев (UI+API).
- `session` — интерактивная ручная сессия по набору тестов.
- `init` — создать базовый конфиг и пример сценария.
- `wizard` — простой мастер создания минимального YAML-сценария без LLM.

## Примеры

В планах — добавить папку `examples/`:

- `examples/features/*.md` — примеры требований;
- `examples/tests/*.yaml` — соответствующие наборы тестов;
- `examples/tests/*-checklist.md` — чек-листы.

После появления `examples/` в репозитории README будет дополнен конкретными командами запуска примеров.

## Стек

- Typer, Rich — CLI.
- Pydantic — модели тест-кейсов и чек-листов.
- LLM (опционально) — генерация документации.
- Playwright, httpx — автоматизация UI и API-шагов.

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
