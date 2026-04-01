# [PROJECT_NAME]

`[PROJECT_NAME]` — шаблон Telegram-бота на Python с поддержкой:
- aiogram
- SQLAlchemy
- PostgreSQL
- Alembic
- Poetry

Замените `[PROJECT_NAME]` и описание под свой проект.

---

## Возможности

- удобная структура для Telegram-бота;
- работа с PostgreSQL;
- миграции через Alembic;
- управление зависимостями через Poetry;
- поддержка `.env`;
- виртуальное окружение `.venv` создаётся **внутри проекта**.

---

## Стек

- Python `>=3.13,<3.15`
- aiogram
- SQLAlchemy
- asyncpg
- Alembic
- python-dotenv
- colorlog

---

## Что нужно установить заранее

Перед началом установите:

- **Python**: https://www.python.org/downloads/
- **Poetry**: https://python-poetry.org/docs/#installation
- **PostgreSQL**: https://www.postgresql.org/download/

---

# Быстрая установка

## 1. Клонировать проект

```bash
git clone <YOUR_REPOSITORY_URL>
cd <PROJECT_FOLDER>
````

---

## 2. Включить `.venv` внутри проекта

Чтобы Poetry создавал виртуальное окружение **не глобально**, а прямо в папке проекта:

```bash
poetry config virtualenvs.in-project true
```

Проверить можно так:

```bash
poetry config virtualenvs.in-project
```

Должно вернуть `true`.

После этого окружение будет создаваться в папке:

```bash
./.venv
```

---

## 3. Установить зависимости

```bash
poetry env use 3.13
poetry install
```

---

## 4. Создать `.env`

Создайте файл `.env` в корне проекта.

Пример:

```env
BOT_TOKEN=1234567890:your_telegram_bot_token
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/bot_db
LOG_LEVEL=INFO
OWNER_IDS=123456789,987654321
```

### Обязательные переменные

* `BOT_TOKEN`
* `DATABASE_URL`

### Необязательные переменные

* `LOG_LEVEL` — уровень логов (default: INFO)
* `OWNER_IDS` — список Telegram user ID через запятую

> Вы можете добавлять свои переменные, потом только не забудьте отредактировать `core/config.py`

---

## 5. Запуск проекта

```bash
poetry run python run.py
```

---

# Установка на Ubuntu

Ниже максимально простой вариант для Ubuntu 22.04 / 24.04.

## 1. Установить системные пакеты

```bash
sudo apt update
sudo apt install -y curl git software-properties-common
```

---

## 2. Установить Python

Сначала проверьте, есть ли нужная версия:

```bash
python3 --version
```

Если нужной версии нет, можно поставить через `deadsnakes`:

```bash
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.13 python3.13-venv python3.13-dev
```

Проверка:

```bash
python3.13 --version
```

---

## 3. Установить Poetry

Официальный способ:

```bash
curl -sSL https://install.python-poetry.org | python3.13 -
```

Добавьте Poetry в PATH:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

Проверка:

```bash
poetry --version
```

---

## 4. Клонировать проект

```bash
git clone <YOUR_REPOSITORY_URL>
cd <PROJECT_FOLDER>
```

---

## 5. Настроить Poetry так, чтобы `.venv` был внутри проекта

```bash
poetry config virtualenvs.in-project true
```

---

## 6. Установить зависимости

```bash
poetry env use 3.13
poetry install
```

---

## 7. Создать `.env`

```bash
nano .env
```

Минимум:

```env
BOT_TOKEN=...
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/bot_db
```

---

## 8. Запуск

```bash
poetry run python app.py
```

---

# Установка на Windows

## 1. Установить Python

Скачайте и установите Python:
[https://www.python.org/downloads/](https://www.python.org/downloads/)

Во время установки **обязательно включите**:

* `Add python.exe to PATH`

Проверка в PowerShell или CMD:

```powershell
python --version
```

---

## 2. Установить PostgreSQL

Скачайте PostgreSQL:
[https://www.postgresql.org/download/windows/](https://www.postgresql.org/download/windows/)

После установки запомните:

* пользователя
* пароль
* порт
* имя базы данных

---

## 3. Установить Poetry

Официальная инструкция:
[https://python-poetry.org/docs/#installation](https://python-poetry.org/docs/#installation)

Обычно для PowerShell:

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

Проверка:

```powershell
poetry --version
```

Если команда не найдена, перезапустите терминал.

---

## 4. Клонировать проект

```powershell
git clone <YOUR_REPOSITORY_URL>
cd <PROJECT_FOLDER>
```

Если Git не установлен:
[https://git-scm.com/download/win](https://git-scm.com/download/win)

---

## 5. Настроить Poetry на `.venv` внутри проекта

```powershell
poetry config virtualenvs.in-project true
```

---

## 6. Установить зависимости

```powershell
poetry env use 3.13
poetry install
```

---

## 7. Создать `.env`

Создайте файл `.env` в корне проекта, например:

```env
BOT_TOKEN=...
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/bot_db
```

---

## 8. Запуск

```powershell
poetry run python app.py
```

---

# Настройка PostgreSQL

## Пример строки подключения

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/bot_db
```

Где:

* `postgres` — пользователь БД
* `password` — пароль
* `localhost` — хост
* `5432` — порт PostgreSQL
* `bot_db` — имя базы данных

---

## Создание базы данных вручную

Через `psql`:

```sql
CREATE DATABASE bot_db;
```

Если нужно сразу указать владельца:

```sql
CREATE DATABASE bot_db OWNER postgres;
```

---

# Миграции Alembic

## Создать миграцию

```bash
poetry run alembic revision -m "create table"
```

или с автогенерацией:

```bash
poetry run alembic revision --autogenerate -m "update models"
```

## Применить миграции

```bash
poetry run alembic upgrade head
```

## Откатить последнюю миграцию

```bash
poetry run alembic downgrade -1
```

---

# Структура проекта

Пример структуры:

```text
.
├── commands/
├── buttons/
├── messages/
├── schedules/
├── database/
│   ├── entities/
│   └── services/
├── core/
├── alembic/
├── app.py
├── run.py
├── pyproject.toml
├── .env
└── README.md
```

---

# Логика проекта

При запуске проект может автоматически загружать модули из папок:

* `commands/` — Telegram-команды
* `buttons/` — callback-кнопки
* `messages/` — обработчики сообщений
* `schedules/` — фоновые задачи

---

# Пример команды

```python
from aiogram.types import Message
from core.implementations.command import BaseCommand


class PingCommand(BaseCommand):
    name = "ping"
    description = "Проверка работы бота"

    async def execute(self, message: Message) -> None:
        await message.answer("pong")
```

---

# Пример кнопки

```python
from aiogram.types import CallbackQuery
from core.implementations.button import BaseButton


class PingButton(BaseButton):
    callback_data = "ping_button"

    async def execute(self, callback: CallbackQuery) -> None:
        await callback.answer("Нажато")
```

---

# Пример entity

```python
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from core.database.base import BaseEntity


class ExampleEntity(BaseEntity):
    __tablename__ = "examples"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
```

---

# Пример service

```python
from collections.abc import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.entities.example import ExampleEntity


async def get_examples(session: AsyncSession) -> Sequence[ExampleEntity]:
    result = await session.scalars(select(ExampleEntity))
    return result.all()
```

---

# Полезные команды

## Установка зависимостей

```bash
poetry install
```

## Запуск бота

```bash
poetry run python app.py
```

## Создание миграции

```bash
poetry run alembic revision -m "message"
```

## Применение миграций

```bash
poetry run alembic upgrade head
```

---

# Деплой через systemd (Ubuntu)

Если бот запускается на сервере, можно сделать сервис.

Создайте файл:

```bash
/etc/systemd/system/bot.service
```

Пример:

```ini
[Unit]
Description=Telegram bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/<PROJECT_FOLDER>
Environment=PATH=/opt/<PROJECT_FOLDER>/.venv/bin:/usr/bin:/bin
ExecStart=/opt/<PROJECT_FOLDER>/.venv/bin/python app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Дальше:

```bash
sudo systemctl daemon-reload
sudo systemctl enable bot
sudo systemctl start bot
sudo systemctl status bot
```

Логи:

```bash
journalctl -u bot -f
```

---

# Что заменить в этом шаблоне

Перед использованием README замените:

* `[PROJECT_NAME]`
* `<YOUR_REPOSITORY_URL>`
* `<PROJECT_FOLDER>`
* список переменных `.env`
* описание проекта
* примеры команд и модулей, если они отличаются

---

# Рекомендации

* держите `.venv` внутри проекта для предсказуемости;
* не храните `.env` в git;
* используйте Alembic для всех изменений БД;
* разделяйте entities, services и handlers;
* не перегружайте README деталями, которые относятся только к одному конкретному боту.

---

* Alim Mun (MIT License &copy; 2026) with love from Kazakhstan