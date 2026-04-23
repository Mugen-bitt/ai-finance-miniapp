# TODO — AI Finance Telegram Mini App

## Срочно

### 1. Cloudflare туннель для Mini App (ошибка 530)
- Вариант 1: Постоянный Cloudflare Tunnel с доменом (~$1-2 за .xyz)
- Вариант 2: VPS сервер (~$5/мес)

---

## Этап 3 — Голосовой ввод

### Готово:
- [x] Telegram Bot с long polling (не требует публичный URL!)
- [x] OpenAI Whisper для распознавания речи
- [x] OpenAI GPT-4o-mini для парсинга текста в транзакцию
- [x] Обработка голосовых И текстовых сообщений
- [x] Бот работает в Docker контейнере

### Запуск на Pi:
```bash
cd ~/ai-finance-miniapp
git pull
docker compose up -d --build
```

### Проверка логов бота:
```bash
docker compose logs -f bot
```

### Конфигурация (.env):
```
DATABASE_URL=postgresql://finance_user:finance_pass@db:5432/finance_db
TELEGRAM_BOT_TOKEN=<токен>
OPENAI_API_KEY=<ключ OpenAI>
```

---

## Этап 4 — Аналитика
- [ ] Графики расходов по категориям
- [ ] Бюджеты по категориям
- [ ] Финансовые цели
- [ ] Уведомления о перерасходе

---

## Выполнено

### Этап 1 — Backend Core
- [x] Авторизация через Telegram
- [x] SQLAlchemy модели (User, Transaction, Budget, Goal)
- [x] API транзакций
- [x] Месячный отчёт

### Этап 2 — Mini App UI
- [x] Dashboard с балансом
- [x] Форма добавления операции
- [x] История транзакций
- [x] Telegram WebApp SDK интеграция

### Инфраструктура
- [x] Docker Compose (db, backend, bot, frontend)
- [x] PostgreSQL в контейнере
- [x] Работает на Raspberry Pi
- [x] Telegram Bot создан (@BotFather)
- [x] Menu Button настроена

---

## Известные проблемы

1. **Mini App недоступен** — нужен публичный URL (туннель или VPS)
