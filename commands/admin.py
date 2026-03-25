from aiogram.enums import ParseMode
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from core.implementations.command import BaseCommand, CommandPermissionLevel
from database.entities.stream_topic import StreamTopicEntity
from database.services import stream_topics
from database.services.stream_topics import create_stream_topic


class AdminCommand(BaseCommand):
    name = 'admin'
    description = 'Центральное управление ботом'
    permission_level = CommandPermissionLevel.OWNER

    async def execute(self, message: Message) -> None:
        await self._show_main_menu(message)

    async def _show_main_menu(self, message: Message) -> None:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📃 Тематики стримов", callback_data="admin:topics")],
                [InlineKeyboardButton(text="📢 Оповещение подписчиков", callback_data="admin:announcements")]
            ]
        )

        prompt = await message.reply(
            "🧑‍💻 Настройка компонентов бота. Выберите, какую часть вы именно хотите настроить:",
            parse_mode='HTML',
            reply_markup=keyboard
        )

        async def on_timeout() -> None:
            await prompt.edit_text("⏰ Время ожидания истекло, вы не успели нажать на кнопку.")

        callback = await self.client.wait_for_button(
            message.chat.id,
            message.from_user.id,
            10,
            prompt.message_id,
            on_timeout=on_timeout
        )

        if not callback:
            return

        if callback.data == "admin:topics":
            await callback.answer()
            await self._show_topics_menu(message, prompt.message_id)

        elif callback.data == "admin:announcements":
            await callback.answer()
            await prompt.edit_text("announcements") # todo: finish

    async def _show_topics_menu(self, message: Message, prompt_message_id: int) -> None:
        while True:
            topics_text = await self._build_topics_text()
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="➕ Добавить тематику", callback_data="admin:topics:add")],
                    [InlineKeyboardButton(text="➖ Удалить тематику по ID", callback_data="admin:topics:delete")],
                    [InlineKeyboardButton(text="⬅️ На главную", callback_data="admin:home")]
                ]
            )

            await self.client.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=prompt_message_id,
                text=topics_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )

            callback = await self.client.wait_for_button(
                message.chat.id,
                message.from_user.id,
                120,
                prompt_message_id,
            )

            if not callback:
                await self.client.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=prompt_message_id,
                    text="⏰ Время ожидания истекло. Запустите /admin снова.",
                )
                return

            if callback.data == "admin:topics:add":
                await callback.answer()
                await self._create_topic_flow(message, prompt_message_id)
                continue

            if callback.data == "admin:topics:delete":
                await callback.answer()
                await self._delete_topic_flow(message, prompt_message_id)
                continue

            if callback.data == "admin:home":
                await callback.answer()
                await self.client.bot.delete_message(message.chat.id, prompt_message_id)
                await self._show_main_menu(message)
                return

            await callback.answer("Неизвестное действие", show_alert=True)

    async def _create_topic_flow(self, message: Message, prompt_message_id: int) -> None:
        await self.client.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=prompt_message_id,
            parse_mode=ParseMode.HTML,
            text=(
                "➕ <b>Добавление тематики</b>\n\n"
                "Отправьте сообщение в формате:\n"
                "<code>Название; триггер1, триггер2</code>\n\n"
                "Пример:\n"
                "<code>Just Chatting; общение, чат</code>\n\n"
            ),
        )

        reply = await self.client.wait_for_message(message.chat.id, message.from_user.id, 180)
        if not reply:
            return

        parts = [part.strip() for part in reply.text.split(";")]
        if len(parts) < 2:
            await reply.reply("❌ Неверный формат. Нужно минимум 2 поля, разделённых ';'")
            return

        name = parts[0]
        triggers = parts[1] or None

        async with self.client.db.session() as db:
            async with db.begin():
                topic = await stream_topics.create_stream_topic(
                    db,
                    name=name,
                    triggers=triggers,
                    enabled=True,
                    is_youtube=False,
                    is_twitch=False
                )

        await reply.reply(f"✅ Тематика добавлена. ID: {topic.id}")

    async def _delete_topic_flow(self, message: Message, prompt_message_id: int) -> None:
        await self.client.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=prompt_message_id,
            parse_mode=ParseMode.HTML,
            text=(
                "➖ <b>Удаление тематики</b>\n\n"
                "Отправьте ID тематики, которую нужно удалить."
            ),
        )

        reply = await self.client.wait_for_message(message.chat.id, message.from_user.id, 120)
        if not reply:
            return

        if not reply.text.isdigit():
            await reply.reply("❌ ID должен быть целым числом.")
            return

        topic_id = int(reply.text)
        async with self.client.db.session() as db:
            async with db.begin():
                deleted = await stream_topics.delete_stream_topic_by_id(db, topic_id)

        if not deleted:
            await reply.reply(f"⚠️ Тематика с ID {topic_id} не найдена.")
            return

        await reply.reply(f"✅ Тематика с ID {topic_id} удалена.")

    async def _build_topics_text(self) -> str:
        async with self.client.db.session() as db:
            async with db.begin():
                topics = await stream_topics.get_stream_topics(db)

                if len(topics) == 0:
                    _new_topics = [
                        StreamTopicEntity(name="📺 YouTube",is_youtube=True),
                        StreamTopicEntity(name="💜 Twitch", is_twitch=True),
                        StreamTopicEntity(name="🎯 Основной стрим", is_main=True),
                        StreamTopicEntity(name="🌙 Ночной стрим", is_night=True)
                    ]

                    topics = []

                    for topic in _new_topics:
                        t = await create_stream_topic(
                            db,
                            name=topic.name,
                            triggers=topic.triggers,
                            is_youtube=topic.is_youtube,
                            is_twitch=topic.is_twitch,
                            enabled=topic.enabled
                        )
                        topics.append(t)

        lines = ["📃 <b>Управление тематиками стримов</b>\n\nАктуальный список тематик:"]
        for topic in topics:
            lines.extend([
                "",
                f"• <b>ID:</b> {topic.id}",
                f"  <b>Название:</b> {topic.name}",
                f"  <b>Триггеры:</b> {topic.triggers or '—'}",
            ])

        return "\n".join(lines)
