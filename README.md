# Бот приёма заявок для малого бизнеса

Telegram-бот на **aiogram 3.x** (async) с записью по дате, напоминаниями и портфолио.

## Возможности
- 📝 **Запись**: услуга → дата → свободный слот. Занятое время не предлагается, гонки двух клиентов защищены повторной проверкой.
- 🔔 **Напоминания**: APScheduler за N часов до визита (по умолчанию 2 ч).
- 🖼 **Портфолио**: фото-галерея из БД с листанием ← →.
- 🧑‍💼 **Админ**: новые заявки приходят в чат админа с кнопками «Подтвердить/Отклонить». Отправленное админом фото добавляется в портфолио.

## Стек
aiogram 3.x · SQLAlchemy 2.0 (async) · SQLite (aiosqlite) · APScheduler · pydantic-settings · FSM (MemoryStorage).

## Архитектура
Роутеры per-feature, тонкие хендлеры, вся логика — в сервисах и репозиториях.

```
bot.py                  entrypoint (DI, планировщик, polling)
config.py               настройки из .env
states.py               FSM (BookingSG)
db/
  base.py               engine + фабрика сессий
  models.py             Service, Booking, PortfolioItem
  repositories/         доступ к БД (booking, service, portfolio)
handlers/               start(+cancel), booking, portfolio, admin, errors
keyboards/              common, booking, portfolio, admin, callbacks
services/               booking_service (слоты), reminder, notifications
middlewares/db.py       async-сессия на апдейт + commit/rollback
seed.py                 демо-услуги
```

## Запуск
> Нужен **Python 3.11–3.13** (под 3.14 пока нет готовых wheel для pydantic-core).

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env      # впишите BOT_TOKEN и ADMIN_ID
python seed.py            # демо-услуги (опционально)
python bot.py             # polling
```

## Демонстрация диалога
```
Клиент: /start
  Бот → 👋 Здравствуйте! [📝 Записаться] [🖼 Портфолио]
Клиент: 📝 Записаться → Стрижка → Сб 04.07 → 10:00
  Бот → Оставьте номер телефона [📱 Поделиться контактом]
Клиент: (контакт)
  Бот → Проверьте заявку: 🗓 04.07.2026 10:00  📱 +7999…  [✅ Отправить заявку]
Клиент: ✅ Отправить заявку
  Бот → клиенту:  ✅ Заявка отправлена!
  Бот → админу:   🆕 Новая заявка …  [✅ Подтвердить] [❌ Отклонить]
Админ:  ✅ Подтвердить
  Бот → клиенту:  ✅ Ваша запись на 04.07 10:00 подтверждена!
  (за 2 часа до визита) 🔔 Напоминание о записи
```

## Настройки (.env)
| Переменная | По умолчанию | Назначение |
|---|---|---|
| `BOT_TOKEN` | — | токен от @BotFather (обязательно) |
| `ADMIN_ID` | — | id админа для заявок (обязательно) |
| `DATABASE_URL` | `sqlite+aiosqlite:///bot.db` | строка подключения |
| `WORK_START_HOUR` / `WORK_END_HOUR` | `10` / `19` | рабочие часы |
| `BOOKING_HORIZON_DAYS` | `14` | горизонт записи |
| `REMINDER_BEFORE_HOURS` | `2` | за сколько часов напоминать |
| `TZ` | `Europe/Moscow` | часовой пояс бизнеса |

## Наполнение портфолио
Отправьте боту фото (с подписью — станет подписью работы) от аккаунта с `ADMIN_ID`.
Бот сохранит его и вернёт `file_id`. Клиенты увидят работу в разделе «Портфолио».

## Заметки
- Секретов в коде нет — всё из `.env`.
- Таблицы создаются автоматически (`create_all`) для dev; для прод — Alembic.
- `/cancel` прерывает любой сценарий и чистит состояние.

## Автор
**Michael Nikolaev** · Лицензия [MIT](LICENSE)
