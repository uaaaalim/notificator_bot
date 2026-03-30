from aiogram.enums import ParseMode, MessageEntityType
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from core.implementations.command import BaseCommand, CommandPermissionLevel
from database.entities.stream_topic import StreamTopicEntity
from database.services import stream_topics
from database.services.stream_topics import create_stream_topic
from services.emojis import YOUTUBE_EMOJI_ID, TWITCH_EMOJI_ID, STAR_EMOJI_ID, MOON_EMOJI_ID, is_custom_emoji


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
        await self.client.bot.delete_message(chat_id=message.chat.id, message_id=prompt_message_id)

        while True:
            topics_text = await self._build_topics_text()
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="➕ Добавить тематику", callback_data="admin:topics:add")],
                    [InlineKeyboardButton(text="➖ Удалить тематику по ID", callback_data="admin:topics:delete")],
                    [InlineKeyboardButton(text="⬅️ На главную", callback_data="admin:home")]
                ]
            )

            prompt = await self.client.bot.send_message(
                chat_id=message.chat.id,
                text=topics_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )

            callback = await self.client.wait_for_button(
                message.chat.id,
                message.from_user.id,
                120,
                prompt.message_id,
            )

            if not callback:
                await self.client.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=prompt.message_id,
                    text="⏰ Время ожидания истекло. Запустите /admin снова.",
                )
                return

            if callback.data == "admin:topics:add":
                await callback.answer()
                await self._create_topic_flow(message, prompt.message_id)
                continue

            if callback.data == "admin:topics:delete":
                await callback.answer()
                await self._delete_topic_flow(message, prompt.message_id)
                continue

            if callback.data == "admin:home":
                await callback.answer()
                await self.client.bot.delete_message(message.chat.id, prompt.message_id)
                await self._show_main_menu(message)
                return

    async def _create_topic_flow(self, message: Message, prompt_message_id: int) -> None:
        await self.client.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=prompt_message_id,
            parse_mode=ParseMode.HTML,
            text=(
                "➕ <b>Добавление тематики</b>\n\n"
                "Отправьте сообщение в формате:\n"
                "<code>Название; эмодзи; триггер1, триггер2</code>\n\n"
                "Эмодзи можно не указывать:\n"
                "<code>Название; триггер1, триггер2</code>\n\n"
                "Пример:\n"
                "<code>Just Chatting; 🔥; общение, чат</code>\n\n"
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
        emoji = None
        if len(parts) >= 3:
            emoji = self._resolve_topic_emoji(reply)
            triggers = ";".join(parts[2:]).strip() or None
        else:
            triggers = parts[1] or None

        async with self.client.db.session() as db:
            async with db.begin():
                topic = await stream_topics.create_stream_topic(
                    db,
                    name=name,
                    emoji=emoji,
                    triggers=triggers,
                    enabled=True,
                    is_youtube=False,
                    is_twitch=False
                )

        await reply.reply(f"✅ Тематика добавлена. ID: {topic.id}")

    @staticmethod
    def _resolve_topic_emoji(reply: Message) -> str | None:
        if not reply.text:
            return None

        first_delimiter = reply.text.find(";")
        second_delimiter = reply.text.find(";", first_delimiter + 1)

        if first_delimiter == -1 or second_delimiter == -1:
            return None

        start = first_delimiter + 1
        end = second_delimiter

        while start < end and reply.text[start].isspace():
            start += 1
        while end > start and reply.text[end - 1].isspace():
            end -= 1

        emoji = reply.text[start:end]
        if not emoji:
            return None

        if is_custom_emoji(emoji):
            return emoji

        for entity in reply.entities or []:
            if entity.type != MessageEntityType.CUSTOM_EMOJI:
                continue

            entity_start = entity.offset
            entity_end = entity.offset + entity.length
            if entity_start >= start and entity_end <= end and entity.custom_emoji_id:
                return entity.custom_emoji_id

        return emoji

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
                        StreamTopicEntity(name="YouTube", is_youtube=True, emoji=YOUTUBE_EMOJI_ID),
                        StreamTopicEntity(name="Twitch", is_twitch=True, emoji=TWITCH_EMOJI_ID),
                        StreamTopicEntity(name="Основной стрим", is_main=True, emoji=STAR_EMOJI_ID),
                        StreamTopicEntity(name="Ночной стрим", is_night=True, emoji=MOON_EMOJI_ID)
                    ]

                    topics = []

                    for topic in _new_topics:
                        t = await create_stream_topic(
                            db,
                            name=topic.name,
                            emoji=topic.emoji,
                            triggers=topic.triggers,
                            is_youtube=topic.is_youtube,
                            is_twitch=topic.is_twitch,
                            is_main=topic.is_main,
                            is_night=topic.is_night,
                            enabled=topic.enabled,
                        )
                        topics.append(t)

        lines = ["📃 <b>Управление тематиками стримов</b>\n\nАктуальный список тематик:"]
        for topic in topics:
            lines.extend([
                "",
                f"• <b>ID:</b> {topic.id}",
                f"  <b>Название:</b> {topic.name}",
                f"  <b>Эмодзи:</b> {topic.get_emoji() or '—'}",
                f"  <b>Триггеры:</b> {topic.triggers or '—'}",
            ])

        return "\n".join(lines)
