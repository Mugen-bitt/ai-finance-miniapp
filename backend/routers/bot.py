import os
import httpx
from datetime import date
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy.orm import Session

from database import SessionLocal
from models import User, Transaction, TransactionType
from services.stt import transcribe_audio
from services.llm_parser import parse_transaction_text

router = APIRouter(prefix="/bot", tags=["telegram-bot"])

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


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


async def download_voice_file(file_id: str) -> bytes:
    """Скачать голосовое сообщение из Telegram."""
    async with httpx.AsyncClient() as client:
        # Получаем путь к файлу
        response = await client.get(f"{TELEGRAM_API_URL}/getFile?file_id={file_id}")
        file_path = response.json()["result"]["file_path"]

        # Скачиваем файл
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
        file_response = await client.get(file_url)
        return file_response.content


def get_or_create_user(db: Session, telegram_id: int, first_name: str = None, username: str = None) -> User:
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


@router.post("/webhook")
async def telegram_webhook(request: Request):
    """Обработчик webhook от Telegram."""
    data = await request.json()

    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    user_data = message.get("from", {})

    if not chat_id:
        return {"ok": True}

    # Обработка команды /start
    if message.get("text") == "/start":
        await send_message(
            chat_id,
            "👋 <b>Привет!</b>\n\n"
            "Я помогу вести учёт финансов.\n\n"
            "🎤 <b>Отправь голосовое сообщение</b> с описанием расхода или дохода:\n"
            "• «Потратил 500 на продукты»\n"
            "• «Получил зарплату 80 тысяч»\n"
            "• «Такси 350 рублей»\n\n"
            "Я распознаю и сохраню транзакцию автоматически."
        )
        return {"ok": True}

    # Обработка голосового сообщения
    voice = message.get("voice")
    if voice:
        file_id = voice.get("file_id")

        try:
            # Отправляем статус "печатает"
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{TELEGRAM_API_URL}/sendChatAction",
                    json={"chat_id": chat_id, "action": "typing"}
                )

            # Скачиваем голосовое
            audio_data = await download_voice_file(file_id)

            # Распознаём речь
            text = await transcribe_audio(audio_data)

            if not text:
                await send_message(chat_id, "❌ Не удалось распознать речь. Попробуй ещё раз.")
                return {"ok": True}

            # Парсим текст в транзакцию через LLM
            parsed = await parse_transaction_text(text)

            if not parsed:
                await send_message(
                    chat_id,
                    f"🎤 Распознано: <i>{text}</i>\n\n"
                    "❌ Не удалось определить сумму или тип операции. "
                    "Попробуй сказать более чётко, например: «Потратил 500 на продукты»"
                )
                return {"ok": True}

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

                # Формируем подтверждение
                emoji = "💸" if parsed["type"] == "expense" else "💰"
                type_text = "Расход" if parsed["type"] == "expense" else "Доход"

                await send_message(
                    chat_id,
                    f"✅ <b>Транзакция сохранена!</b>\n\n"
                    f"{emoji} {type_text}: <b>{parsed['amount']:.0f} ₽</b>\n"
                    f"📁 Категория: {parsed['category']}\n"
                    f"{f'📝 {parsed[\"description\"]}' if parsed.get('description') else ''}"
                )

            finally:
                db.close()

        except Exception as e:
            print(f"Error processing voice: {e}")
            await send_message(chat_id, f"❌ Ошибка обработки: {str(e)}")

        return {"ok": True}

    # Обработка текстового сообщения
    text = message.get("text")
    if text and not text.startswith("/"):
        try:
            parsed = await parse_transaction_text(text)

            if not parsed:
                await send_message(
                    chat_id,
                    "❌ Не удалось определить транзакцию.\n"
                    "Попробуй: «Потратил 500 на продукты» или отправь голосовое."
                )
                return {"ok": True}

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

                emoji = "💸" if parsed["type"] == "expense" else "💰"
                type_text = "Расход" if parsed["type"] == "expense" else "Доход"

                await send_message(
                    chat_id,
                    f"✅ <b>Транзакция сохранена!</b>\n\n"
                    f"{emoji} {type_text}: <b>{parsed['amount']:.0f} ₽</b>\n"
                    f"📁 Категория: {parsed['category']}\n"
                    f"{f'📝 {parsed[\"description\"]}' if parsed.get('description') else ''}"
                )

            finally:
                db.close()

        except Exception as e:
            print(f"Error processing text: {e}")
            await send_message(chat_id, f"❌ Ошибка: {str(e)}")

    return {"ok": True}
