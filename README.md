# AI Finance Telegram Mini App

## Overview

Telegram Mini App для голосового финансового учёта и аналитики.
Пользователь диктует расходы → система распознаёт речь → извлекает
структуру → сохраняет в БД → формирует аналитику и отчёты. Сервер
размещается на Raspberry Pi и работает 24/7.

------------------------------------------------------------------------

## Текущий статус (2026-03-01)

### Готово:
- [x] Backend (FastAPI) — API для транзакций, авторизация через Telegram
- [x] PostgreSQL — база данных в Docker
- [x] Frontend (React + Vite) — Dashboard, добавление транзакций, история
- [x] Docker Compose — всё работает на Raspberry Pi
- [x] Telegram Bot создан в @BotFather
- [x] TELEGRAM_BOT_TOKEN добавлен в .env
- [x] Menu Button настроена (открывает Mini App)

### Проблема:
- Cloudflare Quick Tunnel нестабилен — соединение постоянно рвётся (ошибка 530)
- Временные URL (trycloudflare.com) не держат соединение в текущей сети

### Следующие шаги:
- [ ] **Решить проблему с туннелем** (варианты ниже)
- [ ] Добавить голосовой ввод (STT + LLM)
- [ ] Графики и аналитика

### Варианты решения туннеля:
1. **Постоянный Cloudflare Tunnel с доменом** (рекомендуется)
   - Купить домен (~$1-2 за .xyz)
   - Добавить в Cloudflare
   - Создать Named Tunnel — стабильный, постоянный URL
2. **VPS сервер** (~$5/мес)
   - Перенести docker compose на VPS
   - Прямой доступ без туннелей

------------------------------------------------------------------------

## Запуск на Raspberry Pi

### 1. Запуск контейнеров
```bash
cd ~/ai-finance-miniapp
git pull
docker compose up -d --build
```

### 2. Проверка статуса
```bash
docker compose ps
curl http://localhost:8000/health   # Backend
curl http://localhost:3002          # Frontend
```

### 3. Запуск Cloudflare Tunnel (публичный доступ)
```bash
cloudflared tunnel --url http://localhost:3002 --protocol http2
```
**Важно:** Всегда используй `--protocol http2` (QUIC блокируется роутером)

Туннель выдаст URL вида: `https://xxx.trycloudflare.com`

------------------------------------------------------------------------

## Настройка Telegram Mini App

### Выполнено:
1. [x] Создан бот в @BotFather (`/newbot`)
2. [x] Токен добавлен в `.env` на Pi
3. [x] Настроена Menu Button (`/mybots` → Bot Settings → Menu Button)

### Осталось:
- [ ] Настроить стабильный туннель (см. "Варианты решения туннеля" выше)
- [ ] Обновить URL в Menu Button на постоянный

------------------------------------------------------------------------

## Структура проекта

```
ai-finance-miniapp/
├── docker-compose.yml
├── .env                    # Не в git (секреты)
├── .env.example
├── backend/
│   ├── Dockerfile
│   ├── main.py             # FastAPI app
│   ├── database.py         # PostgreSQL connection
│   ├── models.py           # SQLAlchemy models
│   ├── schemas.py          # Pydantic schemas
│   ├── auth.py             # Telegram auth
│   └── routers/
│       └── transactions.py # API endpoints
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── package.json
    └── src/
        ├── App.jsx
        ├── api/client.js
        ├── hooks/useTelegram.js
        └── pages/
            ├── Dashboard.jsx
            ├── AddTransaction.jsx
            └── History.jsx
```

------------------------------------------------------------------------

## API Endpoints

- `GET /health` — проверка здоровья
- `POST /api/transactions/` — создать транзакцию
- `GET /api/transactions/` — список транзакций
- `GET /api/transactions/{id}` — одна транзакция
- `DELETE /api/transactions/{id}` — удалить
- `GET /api/transactions/report/monthly?year=2026&month=2` — месячный отчёт
- `GET /api/transactions/categories/list` — список категорий

------------------------------------------------------------------------

## Порты

| Сервис   | Внутренний | Внешний |
|----------|------------|---------|
| PostgreSQL | 5432     | 5433    |
| Backend  | 8000       | 8000    |
| Frontend | 80         | 3002    |

------------------------------------------------------------------------

## Общая архитектура

```
Telegram → Mini App (React) → Cloudflare Tunnel → Nginx → Backend (FastAPI) → PostgreSQL
```

------------------------------------------------------------------------

## Дорожная карта

### Этап 1 — Backend Core [DONE]
- [x] Авторизация через Telegram
- [x] SQLAlchemy модели (User, Transaction, Budget, Goal)
- [x] API транзакций
- [x] Месячный отчёт

### Этап 2 — Mini App UI [DONE]
- [x] Dashboard с балансом
- [x] Форма добавления операции
- [x] История транзакций
- [x] Telegram WebApp SDK интеграция

### Этап 3 — Голос [TODO]
- [ ] Запись аудио в Mini App
- [ ] Speech-to-Text (OpenAI Whisper)
- [ ] LLM парсинг в JSON
- [ ] Валидация и сохранение

### Этап 4 — Аналитика [TODO]
- [ ] Графики расходов
- [ ] Бюджеты по категориям
- [ ] Финансовые цели
- [ ] Уведомления о перерасходе
