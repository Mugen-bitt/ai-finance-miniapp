# TODO — AI Finance Telegram Mini App

## Срочно
- [ ] Решить проблему с Cloudflare туннелем для Mini App (ошибка 530)
  - Вариант 1: Постоянный Cloudflare Tunnel с доменом (~$1-2 за .xyz)
  - Вариант 2: VPS сервер (~$5/мес)

---

## Этап 3 — Голосовой ввод

### Готово:
- [x] Telegram Bot с long polling (не требует публичный URL!)
- [x] Google Speech-to-Text интеграция (free tier 60 мин/мес)
- [x] Claude API парсинг текста в транзакцию
- [x] Обработка голосовых И текстовых сообщений
- [x] Отдельный сервис `bot` в docker-compose

### Для запуска:
```bash
# На Raspberry Pi
cd ~/ai-finance-miniapp
git pull
docker compose up -d --build
docker compose logs -f bot  # проверить логи бота
```

Бот работает автономно через polling — публичный URL не нужен!

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
- [x] Docker Compose настроен
- [x] PostgreSQL в контейнере
- [x] Работает на Raspberry Pi
- [x] Telegram Bot создан (@BotFather)
- [x] Menu Button настроена
