"""
Telegram Bot с Long Polling.
Не требует публичного URL — работает за NAT.
"""

import os
import asyncio
import httpx
from datetime import date

from dotenv import load_dotenv
load_dotenv()

from database import SessionLocal
from models import User, Transaction, TransactionType
from services.stt import transcribe_audio
from services.llm_parser import parse_transaction_text

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# Timeout для long polling (секунды)
POLLING_TIMEOUT = 30


async def send_message(chat_id: int, text: str, parse_mode: str = "HTML"):
    """Отправить сообщение в Telegram."""
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{TELEGRAM_API_URL}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
        )


async def send_typing(chat_id: int):
    """Отправить статус 'печатает'."""
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{TELEGRAM_API_URL}/sendChatAction",
            json={"chat_id": chat_id, "action": "typing"}
        )


async def download_voice_file(file_id: str) -> bytes:
    """Скачать голосовое сообщение из Telegram."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{TELEGRAM_API_URL}/getFile?file_id={file_id}")
        file_path = response.json()["result"]["file_path"]
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
        file_response = await client.get(file_url)
        return file_response.content


def get_or_create_user(db, telegram_id: int, first_name: str = None, username: str = None) -> User:
    """Получить или создать пользователя."""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        user = User(
            telegram_id=telegram_id,
            first_name=first_name,
            username=username
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


async def handle_start(chat_id: int):
    """Обработка команды /start."""
    await send_message(
        chat_id,
        "👋 <b>Привет!</b>\n\n"
        "Я помогу вести учёт финансов.\n\n"
        "🎤 <b>Отправь голосовое сообщение</b> с описанием расхода или дохода:\n"
        "• «Потратил 500 на продукты»\n"
        "• «Получил зарплату 80 тысяч»\n"
        "• «Такси 350 рублей»\n\n"
        "Или просто напиши текстом — я распознаю и сохраню транзакцию."
    )


async def handle_voice(chat_id: int, user_data: dict, file_id: str):
    """Обработка голосового сообщения."""
    try:
        await send_typing(chat_id)

        # Скачиваем голосовое
        audio_data = await download_voice_file(file_id)

        # Распознаём речь
        text = await transcribe_audio(audio_data)

        if not text:
            await send_message(chat_id, "❌ Не удалось распознать речь. Попробуй ещё раз.")
            return

        # Парсим текст в транзакцию
        await process_transaction_text(chat_id, user_data, text, show_recognized=True)

    except Exception as e:
        print(f"Error processing voice: {e}")
        await send_message(chat_id, f"❌ Ошибка обработки: {str(e)}")


async def process_transaction_text(chat_id: int, user_data: dict, text: str, show_recognized: bool = False):
    """Обработка текста и сохранение транзакции."""
    try:
        parsed = await parse_transaction_text(text)

        if not parsed:
            msg = ""
            if show_recognized:
                msg = f"🎤 Распознано: <i>{text}</i>\n\n"
            msg += "❌ Не удалось определить сумму или тип операции.\n"
            msg += "Попробуй сказать: «Потратил 500 на продукты»"
            await send_message(chat_id, msg)
            return

        # Сохраняем транзакцию
        db = SessionLocal()
        try:
            user = get_or_create_user(
                db,
                telegram_id=user_data.get("id"),
                first_name=user_data.get("first_name"),
                username=user_data.get("username")
            )

            transaction = Transaction(
                user_id=user.id,
                type=TransactionType(parsed["type"]),
                amount=parsed["amount"],
                currency=parsed.get("currency", "RUB"),
                category=parsed["category"],
                description=parsed.get("description"),
                transaction_date=parsed.get("date") or date.today()
            )
            db.add(transaction)
            db.commit()

            # Подтверждение
            emoji = "💸" if parsed["type"] == "expense" else "💰"
            type_text = "Расход" if parsed["type"] == "expense" else "Доход"
            desc_line = f"\n📝 {parsed['description']}" if parsed.get('description') else ""

            msg = ""
            if show_recognized:
                msg = f"🎤 <i>{text}</i>\n\n"
            msg += f"✅ <b>Сохранено!</b>\n\n"
            msg += f"{emoji} {type_text}: <b>{parsed['amount']:.0f} ₽</b>\n"
            msg += f"📁 Категория: {parsed['category']}{desc_line}"

            await send_message(chat_id, msg)

        finally:
            db.close()

    except Exception as e:
        print(f"Error processing text: {e}")
        await send_message(chat_id, f"❌ Ошибка: {str(e)}")


async def handle_text(chat_id: int, user_data: dict, text: str):
    """Обработка текстового сообщения."""
    await send_typing(chat_id)
    await process_transaction_text(chat_id, user_data, text)


async def process_update(update: dict):
    """Обработка одного update от Telegram."""
    message = update.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    user_data = message.get("from", {})

    if not chat_id:
        return

    # Команда /start
    if message.get("text") == "/start":
        await handle_start(chat_id)
        return

    # Голосовое сообщение
    voice = message.get("voice")
    if voice:
        await handle_voice(chat_id, user_data, voice.get("file_id"))
        return

    # Текстовое сообщение (не команда)
    text = message.get("text")
    if text and not text.startswith("/"):
        await handle_text(chat_id, user_data, text)
        return


async def polling_loop():
    """Основной цикл polling."""
    print("🤖 Bot started with long polling...")
    offset = 0

    async with httpx.AsyncClient(timeout=POLLING_TIMEOUT + 10) as client:
        while True:
            try:
                # Long polling запрос
                response = await client.get(
                    f"{TELEGRAM_API_URL}/getUpdates",
                    params={
                        "offset": offset,
                        "timeout": POLLING_TIMEOUT,
                        "allowed_updates": ["message"]
                    }
                )

                data = response.json()

                if not data.get("ok"):
                    print(f"Telegram API error: {data}")
                    await asyncio.sleep(5)
                    continue

                updates = data.get("result", [])

                for update in updates:
                    offset = update["update_id"] + 1
                    try:
                        await process_update(update)
                    except Exception as e:
                        print(f"Error processing update: {e}")

            except httpx.TimeoutException:
                # Таймаут — это нормально для long polling
                continue
            except Exception as e:
                print(f"Polling error: {e}")
                await asyncio.sleep(5)


async def main():
    """Точка входа."""
    # Удаляем webhook если был установлен
    async with httpx.AsyncClient() as client:
        await client.get(f"{TELEGRAM_API_URL}/deleteWebhook")

    await polling_loop()


if __name__ == "__main__":
    asyncio.run(main())
