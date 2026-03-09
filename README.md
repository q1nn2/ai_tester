# ai_tester

AI-агент для тестовой документации и ручного тестирования: генерация тест-кейсов и чек-листов, полу-автоматический прогон сценариев, интерактивные сессии с поддержкой UI/API-шагов.

## Установка

```bash
pip install -r requirements.txt
playwright install
```

## CLI

```bash
python -m ai_tester.cli --help
```

### Команды

- **docs** — сгенерировать тест-кейсы и чек-лист из описания фичи (с опциональным использованием LLM):

  ```bash
  python -m ai_tester.cli docs "Авторизация" --source feature_auth.txt
  ```

- **run** — полу-автоматический прогон сценариев по YAML/JSON:

  ```bash
  python -m ai_tester.cli run tests/ai-docs/Авторизация.yaml --env dev
  ```

- **session** — интерактивная сессия ручного тестирования:

  ```bash
  python -m ai_tester.cli session tests/ai-docs/Авторизация.yaml --env dev
  ```

## Конфигурация

Настройки и окружения (dev/stage/prod) задаются в `ai-tester.config.yaml` (см. модуль `config`).

## Стек

- Typer, Rich — CLI
- Pydantic — модели тест-кейсов и чек-листов
- LLM (опционально) — генерация документации
- Playwright, httpx — автоматизация UI и API-шагов
