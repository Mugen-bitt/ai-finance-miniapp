"""
LLM сервис для парсинга текста транзакции с использованием Google Gemini API.
"""

import os
import json
import httpx
from typing import Optional, Dict, Any
from datetime import date, timedelta

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

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

Верни ТОЛЬКО валидный JSON без дополнительного текста."""


async def parse_transaction_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Парсит текст и извлекает данные транзакции с помощью Gemini.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set in environment")

    today = date.today()
    yesterday = today - timedelta(days=1)
    user_message = f"Сегодня {today.strftime('%Y-%m-%d')}. Вчера было {yesterday.strftime('%Y-%m-%d')}.\n\nТекст: {text}"

    request_body = {
        "contents": [
            {
                "parts": [
                    {"text": SYSTEM_PROMPT + "\n\n" + user_message}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 256
        }
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            json=request_body
        )

        if response.status_code != 200:
            print(f"Gemini API error: {response.status_code} - {response.text}")
            return None

        result = response.json()

        # Извлекаем текст ответа
        try:
            response_text = result["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            print(f"Unexpected Gemini response: {result}")
            return None

        # Парсим JSON из ответа
        try:
            json_text = response_text.strip()
            if json_text.startswith("```"):
                json_text = json_text.split("```")[1]
                if json_text.startswith("json"):
                    json_text = json_text[4:]
            json_text = json_text.strip()

            parsed = json.loads(json_text)

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
