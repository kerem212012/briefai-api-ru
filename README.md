# BriefAI API

API улучшает продуктовый бриф через заменяемый AI-провайдер.

По умолчанию работает детерминированный `demo`-режим без ключа:

```bash
uv sync --frozen --dev
uv run fastapi dev app/main.py
```

Для Gemini добавь ключ только в `.env` и установи `AI_BACKEND=gemini`. Проверка: `uv run pytest`.
