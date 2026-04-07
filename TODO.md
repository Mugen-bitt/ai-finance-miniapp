# TODO — AI Finance Telegram Mini App

## Срочно

### 1. Gemini API — нужно пополнить/получить ключ
- **Статус:** Ошибка 429 (quota exceeded) / 404 (model not found)
- **Проблема:** Бесплатный лимит Gemini API исчерпан
- **Решение:**
  - Создать новый API ключ: https://aistudio.google.com/apikey
  - Или пополнить баланс Google AI
  - Или использовать другой LLM (OpenAI, Claude)

### 2. Cloudflare туннель для Mini App (ошибка 530)
- Вариант 1: Постоянный Cloudflare Tunnel с доменом (~$1-2 за .xyz)
- Вариант 2: VPS сервер (~$5/мес)

---

## Этап 3 — Голосовой ввод

### Готово:
- [x] Telegram Bot с long polling (не требует публичный URL!)
- [x] Google Speech-to-Text интеграция (free tier 60 мин/мес)
- [x] Gemini API парсинг текста в транзакцию (заменён с Claude)
- [x] Обработка голосовых И текстовых сообщений
- [x] Бот работает как systemd сервис (не в Docker из-за проблем с сетью)

### Запуск бота на Pi:
```bash
cd ~/ai-finance-miniapp/backend
source venv/bin/activate
python bot_polling.py
```

### Конфигурация (.env в backend/):
```
DATABASE_URL=postgresql://finance_user:finance_pass@localhost:5433/finance_db
TELEGRAM_BOT_TOKEN=<токен>
GOOGLE_API_KEY=<ключ для STT>
GEMINI_API_KEY=<ключ для LLM парсинга>
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
- [x] Docker Compose (db, backend, frontend)
- [x] PostgreSQL в контейнере
- [x] Работает на Raspberry Pi
- [x] Telegram Bot создан (@BotFather)
- [x] Menu Button настроена

---

## Известные проблемы

1. **Docker на Pi не имеет доступа к интернету** — бот запускается вне Docker через venv
2. **Mini App недоступен** — нужен публичный URL (туннель или VPS)
3. **Gemini API лимиты** — бесплатный тариф быстро заканчивается
