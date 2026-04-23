"""
Speech-to-Text сервис с использованием OpenAI Whisper API.
Telegram отправляет голосовые в формате OGG (Opus codec).
"""

import os
import tempfile
import httpx
from typing import Optional

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_STT_URL = "https://api.openai.com/v1/audio/transcriptions"
PROXY_URL = os.getenv("PROXY_URL", "http://127.0.0.1:10808")


async def transcribe_audio(audio_data: bytes) -> Optional[str]:
    """
    Распознать речь из аудио файла с помощью OpenAI Whisper.

    Args:
        audio_data: Аудио данные в формате OGG/Opus (от Telegram)

    Returns:
        Распознанный текст или None
    """
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not set in environment")

    # Сохраняем во временный файл (Whisper API требует файл)
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp_file:
        tmp_file.write(audio_data)
        tmp_path = tmp_file.name

    try:
        async with httpx.AsyncClient(timeout=60.0, proxy=PROXY_URL) as client:
            with open(tmp_path, "rb") as audio_file:
                response = await client.post(
                    OPENAI_STT_URL,
                    headers={
                        "Authorization": f"Bearer {OPENAI_API_KEY}"
                    },
                    files={
                        "file": ("voice.ogg", audio_file, "audio/ogg")
                    },
                    data={
                        "model": "whisper-1",
                        "language": "ru"
                    }
                )

            if response.status_code != 200:
                print(f"OpenAI Whisper error: {response.status_code} - {response.text}")
                return None

            result = response.json()
            return result.get("text", "")

    finally:
        # Удаляем временный файл
        os.unlink(tmp_path)
