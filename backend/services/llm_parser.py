"""
LLM сервис для парсинга текста транзакции с использованием OpenAI GPT API.
"""

import os
import json
import httpx
from typing import Optional, Dict, Any
from datetime import date, timedelta

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
PROXY_URL = os.getenv("PROXY_URL", "http://127.0.0.1:10808")

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
    Парсит текст и извлекает данные транзакции с помощью OpenAI GPT.
    """
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not set in environment")

    today = date.today()
    yesterday = today - timedelta(days=1)
    user_message = f"Сегодня {today.strftime('%Y-%m-%d')}. Вчера было {yesterday.strftime('%Y-%m-%d')}.\n\nТекст: {text}"

    request_body = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.1,
        "max_tokens": 256
    }

    async with httpx.AsyncClient(timeout=30.0, proxy=PROXY_URL) as client:
        response = await client.post(
            OPENAI_CHAT_URL,
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json=request_body
        )

        if response.status_code != 200:
            print(f"OpenAI API error: {response.status_code} - {response.text}")
            return None

        result = response.json()

        # Извлекаем текст ответа
        try:
            response_text = result["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            print(f"Unexpected OpenAI response: {result}")
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
