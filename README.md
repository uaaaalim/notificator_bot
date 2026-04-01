# notificator_bot

`notificator_bot` — шаблон Telegram-бота на **aiogram 3** с автозагрузкой хендлеров, PostgreSQL, SQLAlchemy и Alembic.

## Стек проекта

- Python `>=3.13,<3.15`
- aiogram `>=3.26.0,<4.0.0`
- SQLAlchemy `>=2.0.48,<3.0.0`
- asyncpg `>=0.31.0,<0.32.0`
- Alembic `>=1.18.4,<2.0.0`
- python-dotenv `>=1.2.2,<2.0.0`
- colorlog `>=6.10.1,<7.0.0`

---

## Зависимость от Poetry и быстрая установка

Проект использует **Poetry** для управления зависимостями.

### 1) Установить Poetry

Официальный способ:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Проверка установки:

```bash
poetry --version
```

### 2) Установить зависимости проекта

```bash
poetry env use 3.13
poetry install
```

Проверка окружения:

```bash
poetry run python --version
```

---

## Настройка `.env`

Создайте `.env` в корне репозитория:

```env
BOT_TOKEN=1234567890:your_telegram_bot_token
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/notificator_bot
LOG_LEVEL=INFO
AUTHOR_ID=123456789
AUTHOR_CHANNEL_ID=-1001234567890
OWNER_IDS=123456789,987654321

YOUTUBE_API_KEY=your_google_api_key
YOUTUBE_CHANNEL=@your_channel_or_uc_id
TWITCH_CLIENT_ID=your_twitch_client_id
TWITCH_CLIENT_SECRET=your_twitch_client_secret
TWITCH_CHANNEL_NAME=your_channel_name

DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_POOL_RECYCLE=1800
```

Обязательные переменные для запуска: `BOT_TOKEN`, `DATABASE_URL`, `YOUTUBE_API_KEY`, `YOUTUBE_CHANNEL`,
`TWITCH_CLIENT_ID`, `TWITCH_CLIENT_SECRET`, `TWITCH_CHANNEL_NAME`, `AUTHOR_ID`.

Опциональные переменные:
- `AUTHOR_CHANNEL_ID` — канал автора, куда бот продублирует анонс.
- `OWNER_IDS` — список Telegram user ID через запятую для owner-команд (например `/admin`).
- `LOG_LEVEL`, `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_RECYCLE`.

---

## Запуск проекта

```bash
poetry run python app.py
```

Альтернатива:

```bash
poetry run python run.py
```

---

## Деплой на Ubuntu (Python + Poetry + systemd)

Ниже — базовый сценарий, как поднять бота на сервере Ubuntu 22.04/24.04.

### 1) Установить системные пакеты и Python

```bash
sudo apt update
sudo apt install -y software-properties-common curl git
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.13 python3.13-venv python3.13-distutils
python3.13 --version
```

> Если `python3.13` уже есть в системе, шаг с `deadsnakes` можно пропустить.

### 2) Установить Poetry

```bash
curl -sSL https://install.python-poetry.org | python3.13 -
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
poetry --version
```

### 3) Клонировать проект и установить зависимости

```bash
cd /opt
sudo git clone <YOUR_REPO_URL> notificator_bot
sudo chown -R $USER:$USER /opt/notificator_bot
cd /opt/notificator_bot

# чтобы виртуальное окружение создавалось в проекте: /opt/notificator_bot/.venv
poetry config virtualenvs.in-project true --local
poetry env use 3.13
poetry install --no-interaction --no-ansi
```

### 4) Создать `.env`

```bash
cp .env.example .env  # если есть шаблон
# или создайте файл вручную:
nano .env
```

Заполните минимум: `BOT_TOKEN`, `DATABASE_URL`, `YOUTUBE_API_KEY`, `YOUTUBE_CHANNEL`,
`TWITCH_CLIENT_ID`, `TWITCH_CLIENT_SECRET`, `TWITCH_CHANNEL_NAME`, `AUTHOR_ID`.

### 5) Настроить systemd-сервис

Создайте файл `/etc/systemd/system/notificator-bot.service`:

```ini
[Unit]
Description=Telegram notificator bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/notificator_bot
Environment=PATH=/opt/notificator_bot/.venv/bin:/usr/bin:/bin
ExecStart=/opt/notificator_bot/.venv/bin/python app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

> Замените `ubuntu` на вашего пользователя, если он другой.

Дальше включаем и запускаем:

```bash
sudo systemctl daemon-reload
sudo systemctl enable notificator-bot
sudo systemctl start notificator-bot
sudo systemctl status notificator-bot
```

Логи:

```bash
journalctl -u notificator-bot -f
```

### 6) Обновление бота на сервере

```bash
cd /opt/notificator_bot
git pull
poetry install --no-interaction --no-ansi
sudo systemctl restart notificator-bot
```

---

## Структура и автозагрузка хендлеров

При запуске клиент автоматически сканирует директории:

- `commands/` — команды (`/start`, `/help`, ...)
- `buttons/` — callback-кнопки (inline keyboard)
- `messages/` — обработчики сообщений
- `schedules/` — периодические задачи

Сканирование рекурсивное, поэтому можно хранить файлы в поддиректориях, например:

- `buttons/info/show_profile.py`
- `commands/admin/ban_user.py`
- `messages/moderation/spam.py`

Главное — чтобы в модуле был класс-наследник нужной базовой реализации:

- `BaseCommand` (`core/implementations/command.py`)
- `BaseButton` (`core/implementations/button.py`)
- `BaseMessage` (`core/implementations/message.py`)
- `BaseSchedule` (`core/implementations/schedule.py`)

---

## Как создать команду (`/commands`)

Создайте файл, например `commands/ping.py`:

```python
from aiogram.types import Message

from core.implementations.command import BaseCommand


class PingCommand(BaseCommand):
    name = "ping"
    description = "Проверка, что бот жив"

    async def execute(self, message: Message) -> None:
        await message.answer("pong")
```

После перезапуска бота команда станет доступна как `/ping`.

---

## Как создать кнопку (`/buttons`)

Создайте файл, например `buttons/ping_button.py`:

```python
from aiogram.types import CallbackQuery

from core.implementations.button import BaseButton


class PingButton(BaseButton):
    callback_data = "ping_button"

    async def execute(self, callback: CallbackQuery) -> None:
        await callback.answer("Нажато")
```

Можно располагать в поддиректориях (`buttons/info/ping_button.py`) — загрузка всё равно сработает.

---

## Как создать триггер на сообщения (`/messages`)

Создайте файл, например `messages/echo.py`:

```python
from aiogram.types import Message

from core.implementations.message import BaseMessage


class EchoMessage(BaseMessage):
    trigger = "*"

    async def execute(self, message: Message) -> None:
        if message.text and not message.text.startswith("/"):
            await message.answer(f"Эхо: {message.text}")
```

> `trigger` используется как routing-префикс:
> - `trigger = "*"` — обработчик ловит все сообщения;
> - `trigger = "текст"` — обработчик получает сообщения, которые начинаются с этого текста (без учета регистра).

---

## Ожидание нажатия кнопки и сообщения с таймером

В проекте есть waiter (`core/waiter.py`) и методы в клиенте:

- `self.client.wait_for_button(...)`
- `self.client.wait_for_message(...)`

### Пример: ждать кнопку 10 секунд

```python
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from core.implementations.command import BaseCommand


class ConfirmCommand(BaseCommand):
    name = "confirm"
    description = "Демо ожидания кнопки"

    async def execute(self, message: Message) -> None:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Подтвердить", callback_data="confirm_action")]]
        )
        prompt = await message.answer("Нажми кнопку за 10 секунд", reply_markup=keyboard)

        async def on_timeout() -> None:
            await prompt.edit_text("⏰ Время ожидания истекло")

        callback = await self.client.wait_for_button(
            chat_id=message.chat.id,
            user_id=message.from_user.id,
            timeout=10,
            message_id=prompt.message_id,
            on_timeout=on_timeout,
        )

        if callback and callback.data == "confirm_action":
            await callback.answer("OK")
            await prompt.edit_text("✅ Подтверждено")
```

### Пример: ждать сообщение 15 секунд

```python
from aiogram.types import Message

from core.implementations.command import BaseCommand


class AskNameCommand(BaseCommand):
    name = "ask_name"
    description = "Демо ожидания сообщения"

    async def execute(self, message: Message) -> None:
        prompt = await message.answer("Напиши имя в течение 15 секунд")

        async def on_timeout() -> None:
            await prompt.answer("⏰ Вы не успели ответить")

        result = await self.client.wait_for_message(
            chat_id=message.chat.id,
            user_id=message.from_user.id,
            timeout=15,
            on_timeout=on_timeout,
        )

        if result and result.text:
            await message.answer(f"Принял: {result.text}")
```

---

## Работа с БД: entities и services

### Где создавать entities

Entity-модели находятся в директории:

- `database/entities/`

Создайте новый файл, например `database/entities/notification_rule.py`:

```python
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from core.database.base import BaseEntity


class NotificationRuleEntity(BaseEntity):
    __tablename__ = "notification_rules"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    keyword: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
```

### Где писать сервисы для entities

Сервисы запросов к БД находятся в:

- `database/services/`

Пример файла `database/services/notification_rules.py`:

```python
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.entities.notification_rule import NotificationRuleEntity


async def get_rules(session: AsyncSession) -> Sequence[NotificationRuleEntity]:
    result = await session.scalars(select(NotificationRuleEntity))
    return result.all()
```

Рекомендуемый подход:

- в `database/services/*` держать только запросы и CRUD-логику;
- управление транзакциями (`async with db.begin()`) делать в месте вызова (команда/кнопка/джоба).

---

## Миграции Alembic

### Создать ревизию

```bash
poetry run alembic revision -m "create notification_rules"
```

или с автогенерацией:

```bash
poetry run alembic revision --autogenerate -m "add notification_rules table"
```

### Применить все миграции

```bash
poetry run alembic upgrade head
```

### Откатить последнюю миграцию

```bash
poetry run alembic downgrade -1
```

> `alembic/env.py` автоматически импортирует модели из `database/entities/`, поэтому новые entity будут участвовать в autogenerate.

---

## Небольшие практические рекомендации

- Держите `callback_data` коротким и уникальным.
- Для сложных сценариев кнопок используйте префиксы (`settings:...`, `topic:...`).
- Если команда запускает «мастер» (цепочку шагов), используйте waiter c timeout и `on_timeout`.
- Для модулей лучше нейминг по домену: `commands/subscriptions/...`, `buttons/topics/...`, `database/services/subscribers.py`.
- После добавления новой entity почти всегда нужны:
  1. файл entity;
  2. файл service;
  3. миграция Alembic;
  4. использование в командах/кнопках/джобах.

---

## Часто используемые команды

```bash
# Установка зависимостей
poetry install

# Запуск бота
poetry run python app.py

# Новая миграция
poetry run alembic revision -m "message"

# Применить миграции
poetry run alembic upgrade head
```
