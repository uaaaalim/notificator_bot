# bfit_bot

`bfit_bot` — шаблон Telegram-бота на **aiogram 3** с:
- автозагрузкой хендлеров из директорий,
- ожиданием действий пользователя (сообщение/кнопка) с таймером,
- асинхронной работой с PostgreSQL через SQLAlchemy,
- миграциями через Alembic,
- управлением зависимостями через Poetry.

## Стек

- Python `>=3.13,<3.15`
- aiogram `>=3.26.0,<4.0.0`
- sqlalchemy `>=2.0.48,<3.0.0`
- asyncpg `>=0.31.0,<0.32.0`
- alembic `>=1.18.4,<2.0.0`
- python-dotenv `>=1.2.2,<2.0.0`
- colorlog `>=6.10.1,<7.0.0`

---

## Установка зависимостей (Poetry)

```bash
poetry env use 3.13
poetry install
```

Проверить, что окружение поднято:

```bash
poetry run python --version
```

---

## Настройка

Создайте `.env` в корне проекта:

```env
BOT_TOKEN=ваш_токен_бота
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/bfit_bot
LOG_LEVEL=INFO
```

> `BOT_TOKEN` обязателен. Если `DATABASE_URL` не указан, используется значение по умолчанию из `core/config.py`.

---

## Запуск бота

### Вариант 1 (рекомендуется)
```bash
poetry run python app.py
```

### Вариант 2
```bash
poetry run python run.py
```

При старте выводятся данные о проекте, версиях библиотек и подключенных хендлерах.

---

## Как устроена автозагрузка

Бот автоматически сканирует директории:
- `commands/`
- `buttons/`
- `messages/`
- `schedules/`

и поднимает все классы-наследники базовых реализаций.

Чтобы добавить новый хендлер, достаточно создать `.py` файл с классом нужного типа в соответствующей директории.

---

## Примеры из проекта

## 1) Команда (`/start`)

Файл: `commands/start.py`

```python
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from core.implementations.command import BaseCommand


class StartCommand(BaseCommand):
    name = "start"
    description = "Запуск бота"

    async def execute(self, message: Message) -> None:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Ping", callback_data="ping")],
                [InlineKeyboardButton(text="Ждать кнопку 10 сек", callback_data="demo_wait_button")],
            ]
        )
        await message.answer(
            "Привет! Доступно:\n"
            "/wait_message - ждать сообщение 10 сек\n"
            "/db_demo - создать/получить пользователя\n"
            "Или нажми кнопку ниже.",
            reply_markup=keyboard,
        )
```

Минимальный шаблон своей команды:

```python
from aiogram.types import Message
from core.implementations.command import BaseCommand


class MyCommand(BaseCommand):
    name = "my_command"
    description = "Моя команда"

    async def execute(self, message: Message) -> None:
        await message.answer("Команда сработала")
```

---

## 2) Листенер кнопки (callback)

Файл: `buttons/ping.py`

```python
from aiogram.types import CallbackQuery
from core.implementations.button import BaseButton


class PingButton(BaseButton):
    callback_data = "ping"

    async def execute(self, callback: CallbackQuery) -> None:
        await callback.answer("pong")
        await callback.message.answer("Кнопка Ping обработана ✅")
```

Минимальный шаблон своей кнопки:

```python
from aiogram.types import CallbackQuery
from core.implementations.button import BaseButton


class MyButton(BaseButton):
    callback_data = "my_button"

    async def execute(self, callback: CallbackQuery) -> None:
        await callback.answer("Нажато")
```

---

## 3) Листенер сообщений

Файл: `messages/echo.py`

```python
from aiogram.types import Message
from core.implementations.message import BaseMessage


class EchoMessage(BaseMessage):
    trigger = "*"

    async def execute(self, message: Message) -> None:
        if message.text and not message.text.startswith("/"):
            await message.answer(f"Эхо: {message.text}")
```

Минимальный шаблон своего листенера:

```python
from aiogram.types import Message
from core.implementations.message import BaseMessage


class MyMessageListener(BaseMessage):
    trigger = "*"

    async def execute(self, message: Message) -> None:
        await message.answer("Сообщение получено")
```

---

## 4) Кнопка + таймер ожидания

Файл: `buttons/demo_wait_button.py`

```python
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from core.implementations.button import BaseButton


class DemoWaitButton(BaseButton):
    callback_data = "demo_wait_button"

    async def execute(self, callback: CallbackQuery) -> None:
        if not callback.message:
            await callback.answer("Нет исходного сообщения", show_alert=True)
            return

        await callback.answer()
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Подтвердить", callback_data="confirm_action")]]
        )
        prompt = await callback.message.answer("Нажми 'Подтвердить' за 10 секунд", reply_markup=keyboard)

        async def on_timeout() -> None:
            await prompt.edit_text("⏰ Таймер истек. Кнопка не нажата")

        waited = await self.client.wait_for_button(
            chat_id=callback.message.chat.id,
            user_id=callback.from_user.id,
            timeout=10,
            on_timeout=on_timeout,
        )
        if waited and waited.data == "confirm_action":
            await waited.answer("Подтверждено")
            await prompt.edit_text("✅ Действие подтверждено")
```

Пример с таймером для ожидания **сообщения**: `commands/wait_message.py`.

---

## Работа с БД: entity + repository + использование

## 1) Создать entity

Пример существующей entity: `database/entities/user.py`

```python
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from core.database.base import BaseEntity


class User(BaseEntity):
    __tablename__ = "users"

    tg_id: Mapped[int] = mapped_column(unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
```

Шаблон новой entity:

```python
from sqlalchemy.orm import Mapped, mapped_column

from core.database.base import BaseEntity


class Workout(BaseEntity):
    __tablename__ = "workouts"

    title: Mapped[str] = mapped_column(nullable=False)
    user_tg_id: Mapped[int] = mapped_column(index=True)
```

## 2) Создать database service

Пример: `database/services/subscribers.py`

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.interfaces import ORMOption

from database.entities.subscribers import SubscriberEntity


async def get_subscriber(
    session: AsyncSession,
    tg_id: int,
    *,
    options: tuple[ORMOption, ...] = (),
) -> SubscriberEntity | None:
    query = select(SubscriberEntity).where(SubscriberEntity.tg_id == tg_id)
    if options:
        query = query.options(*options)
    return await session.scalar(query)
```

> Важно: внутри `database/services` не делайте `session.commit()`. Управляйте транзакцией снаружи через `async with session.begin():`.

Шаблон для новой entity:

```python
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.entities.workout import Workout


async def get_workouts(session: AsyncSession) -> Sequence[Workout]:
    result = await session.scalars(select(Workout))
    return result.all()
```

## 3) Пример использования в команде

Файл: `commands/db_demo.py`

```python
from aiogram.types import Message

from sqlalchemy import select

from core.implementations.command import BaseCommand
from database.entities.user import User


class DbDemoCommand(BaseCommand):
    name = "db_demo"
    description = "Пример работы с БД"

    async def execute(self, message: Message) -> None:
        async with self.client.db.session() as session:
            user = await session.scalar(
                select(User).where(User.tg_id == message.from_user.id)
            )
            if not user:
                user = User(tg_id=message.from_user.id, username=message.from_user.username)
                session.add(user)
                await session.commit()
                await session.refresh(user)
                await message.answer(f"Создан пользователь с id={user.id}")
                return

            await message.answer(f"Пользователь найден: id={user.id}, username={user.username}")
```

---

## Alembic: миграции БД

## Применить миграции

```bash
poetry run alembic upgrade head
```

## Откатить последнюю миграцию

```bash
poetry run alembic downgrade -1
```

## Создать новую миграцию

```bash
poetry run alembic revision -m "create workouts"
```

или автогенерацией:

```bash
poetry run alembic revision --autogenerate -m "add workouts table"
```

## Важно для autogenerate

В проекте настроен авто-импорт всех модулей из `database/entities/` внутри `alembic/env.py`, поэтому вручную добавлять импорт каждой новой модели не нужно.

Также `alembic/env.py` читает `.env` через `python-dotenv` и, если задан `DATABASE_URL`, подставляет его в `sqlalchemy.url` (поверх значения из `alembic.ini`).

После генерации проверьте содержимое файла в `alembic/versions/` и примените:

```bash
poetry run alembic upgrade head
```

---

## Полезные команды

```bash
# установить зависимости
poetry install

# запустить бота
poetry run python app.py

# применить миграции
poetry run alembic upgrade head
```
