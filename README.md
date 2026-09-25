# BriefAI API

Учебный API для улучшения продуктового брифа через заменяемый AI-провайдер.

## Результат урока

- `BriefRequest` валидирует продукт, аудиторию и цель.
- `BriefResponse` возвращает улучшенный текст и имя провайдера.
- `demo` работает детерминированно без API-ключа и сети.
- `gemini` подключается через `google-genai` и `client.aio`.
- Таймауты возвращают `504`, ошибки провайдера и пустые ответы — `502`.

## Установка

Требуется Python 3.12+ и установленный [uv](https://docs.astral.sh/uv/).

```bash
uv sync --frozen --dev
```

Для локального demo-режима создай `.env` из примера:

```bash
cp .env.example .env
```

В PowerShell:

```powershell
Copy-Item .env.example .env
```

## Запуск

По умолчанию работает детерминированный `demo`-режим без ключа:

```bash
uv run fastapi dev app/main.py
```

После запуска:

- Swagger UI: <http://127.0.0.1:8000/docs>
- Health check: <http://127.0.0.1:8000/health>

Для Gemini укажи только в `.env`:

```dotenv
AI_BACKEND=gemini
GOOGLE_API_KEY=your-key-here
```

Реальный ключ нельзя добавлять в код, `.env.example` или репозиторий.

## Тестирование

```bash
uv run pytest
```
