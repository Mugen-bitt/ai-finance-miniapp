import os
import hmac
import hashlib
import json
from urllib.parse import parse_qs
from typing import Optional
from fastapi import HTTPException, Header, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import User

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")


def validate_telegram_init_data(init_data: str) -> dict:
    """
    Валидация Telegram WebApp initData.
    https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    if not TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=500, detail="Bot token not configured")

    parsed = parse_qs(init_data)

    # Извлекаем hash
    received_hash = parsed.get("hash", [None])[0]
    if not received_hash:
        raise HTTPException(status_code=401, detail="Hash not found in init_data")

    # Собираем data-check-string
    data_check_arr = []
    for key in sorted(parsed.keys()):
        if key != "hash":
            data_check_arr.append(f"{key}={parsed[key][0]}")
    data_check_string = "\n".join(data_check_arr)

    # Вычисляем secret_key
    secret_key = hmac.new(
        b"WebAppData",
        TELEGRAM_BOT_TOKEN.encode(),
        hashlib.sha256
    ).digest()

    # Вычисляем hash
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    if calculated_hash != received_hash:
        raise HTTPException(status_code=401, detail="Invalid init_data signature")

    # Парсим user из init_data
    user_json = parsed.get("user", [None])[0]
    if not user_json:
        raise HTTPException(status_code=401, detail="User data not found")

    return json.loads(user_json)


def get_or_create_user(telegram_user: dict, db: Session) -> User:
    """Получить или создать пользователя по telegram_id."""
    telegram_id = telegram_user.get("id")
    if not telegram_id:
        raise HTTPException(status_code=400, detail="Invalid telegram user data")

    user = db.query(User).filter(User.telegram_id == telegram_id).first()

    if not user:
        user = User(
            telegram_id=telegram_id,
            first_name=telegram_user.get("first_name"),
            last_name=telegram_user.get("last_name"),
            username=telegram_user.get("username")
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user


async def get_current_user(
    x_telegram_init_data: str = Header(..., alias="X-Telegram-Init-Data"),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency для получения текущего пользователя из Telegram initData.
    Используется в эндпоинтах для аутентификации.
    """
    telegram_user = validate_telegram_init_data(x_telegram_init_data)
    return get_or_create_user(telegram_user, db)


# ============== Dev Mode ==============

DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"


async def get_current_user_dev(
    x_telegram_init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data"),
    db: Session = Depends(get_db)
) -> User:
    """
    Dev-версия авторизации. Если DEV_MODE=true и нет header,
    возвращает тестового пользователя.
    """
    if DEV_MODE and not x_telegram_init_data:
        # Тестовый пользователь для разработки
        test_telegram_id = 123456789
        user = db.query(User).filter(User.telegram_id == test_telegram_id).first()
        if not user:
            user = User(
                telegram_id=test_telegram_id,
                first_name="Test",
                last_name="User",
                username="testuser"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    return await get_current_user(x_telegram_init_data, db)
