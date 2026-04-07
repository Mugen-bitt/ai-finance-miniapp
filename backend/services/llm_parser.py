"""
LLM сервис для парсинга текста транзакции с использованием Claude API.
"""

import os
import json
import httpx
from typing import Optional, Dict, Any
from datetime import date, timedelta

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

# Доступные категории
EXPENSE_CATEGORIES = ["Продукты", "Транспорт", "Развлечения", "Здоровье", "Одежда", "Рестораны", "Связь", "ЖКХ", "Другое"]
INCOME_CATEGORIES = ["Зарплата", "Подработка", "Подарок", "Возврат", "Инвестиции", "Другое"]

SYSTEM_PROMPT = f"""Ты помощник для учёта финансов. Твоя задача — извлечь из текста информацию о финансовой транзакции.

Верни JSON с полями:
- type: "expense" (расход) или "income" (доход)
- amount: число (сумма в рублях)
- category: категория из списка ниже
- description: краткое описание (опционально)
- date: дата в формате YYYY-MM-DD (если упоминается, иначе null)

Категории расходов: {', '.join(EXPENSE_CATEGORIES)}
Категории доходов: {', '.join(INCOME_CATEGORIES)}

Правила:
1. "Потратил", "купил", "заплатил", "отдал" = expense
2. "Получил", "заработал", "пришла зарплата", "дали" = income
3. Числа: "пятьсот" = 500, "тысяча" = 1000, "полторы тысячи" = 1500, "5к" = 5000, "80к" = 80000
4. "Вчера" = вчерашняя дата, "позавчера" = позавчерашняя дата
5. Выбирай наиболее подходящую категорию
6. Если не можешь определить сумму или тип — верни null

Примеры:
"Потратил 500 на продукты" → {{"type": "expense", "amount": 500, "category": "Продукты", "description": null, "date": null}}
"Получил зарплату 80 тысяч" → {{"type": "income", "amount": 80000, "category": "Зарплата", "description": null, "date": null}}
"Такси 350 рублей" → {{"type": "expense", "amount": 350, "category": "Транспорт", "description": "такси", "date": null}}
"Вчера купил кофе за 200" → {{"type": "expense", "amount": 200, "category": "Рестораны", "description": "кофе", "date": "<вчерашняя дата>"}}

Верни ТОЛЬКО валидный JSON без дополнительного текста."""


async def parse_transaction_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Парсит текст и извлекает данные транзакции с помощью Claude.

    Args:
        text: Текст с описанием транзакции

    Returns:
        Словарь с данными транзакции или None
    """
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not set in environment")

    # Добавляем контекст текущей даты
    today = date.today()
    yesterday = today - timedelta(days=1)
    user_message = f"Сегодня {today.strftime('%Y-%m-%d')}. Вчера было {yesterday.strftime('%Y-%m-%d')}.\n\nТекст: {text}"

    request_body = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 256,
        "system": SYSTEM_PROMPT,
        "messages": [
            {"role": "user", "content": user_message}
        ]
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            ANTHROPIC_API_URL,
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json=request_body
        )

        if response.status_code != 200:
            print(f"Claude API error: {response.status_code} - {response.text}")
            return None

        result = response.json()

        # Извлекаем текст ответа
        content = result.get("content", [])
        if not content:
            return None

        response_text = content[0].get("text", "")

        # Парсим JSON из ответа
        try:
            # Убираем возможные markdown блоки
            json_text = response_text.strip()
            if json_text.startswith("```"):
                json_text = json_text.split("```")[1]
                if json_text.startswith("json"):
                    json_text = json_text[4:]
            json_text = json_text.strip()

            parsed = json.loads(json_text)

            # Валидация обязательных полей
            if parsed is None:
                return None
            if not isinstance(parsed.get("amount"), (int, float)):
                return None
            if parsed.get("type") not in ["expense", "income"]:
                return None
            if not parsed.get("category"):
                return None

            return parsed

        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}, response: {response_text}")
            return None
