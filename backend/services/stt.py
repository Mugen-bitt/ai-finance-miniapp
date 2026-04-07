"""
Speech-to-Text сервис с использованием Google Cloud Speech-to-Text API.
Telegram отправляет голосовые в формате OGG (Opus codec).
"""

import os
import base64
import httpx
from typing import Optional

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_STT_URL = "https://speech.googleapis.com/v1/speech:recognize"


async def transcribe_audio(audio_data: bytes) -> Optional[str]:
    """
    Распознать речь из аудио файла.

    Args:
        audio_data: Аудио данные в формате OGG/Opus (от Telegram)

    Returns:
        Распознанный текст или None
    """
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not set in environment")

    # Кодируем аудио в base64
    audio_content = base64.b64encode(audio_data).decode("utf-8")

    request_body = {
        "config": {
            "encoding": "OGG_OPUS",
            "sampleRateHertz": 48000,
            "languageCode": "ru-RU",
            "model": "default",
            "enableAutomaticPunctuation": True,
        },
        "audio": {
            "content": audio_content
        }
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{GOOGLE_STT_URL}?key={GOOGLE_API_KEY}",
            json=request_body
        )

        if response.status_code != 200:
            print(f"Google STT error: {response.status_code} - {response.text}")
            return None

        result = response.json()

        # Извлекаем текст из ответа
        results = result.get("results", [])
        if not results:
            return None

        alternatives = results[0].get("alternatives", [])
        if not alternatives:
            return None

        return alternatives[0].get("transcript", "")
