from aiogram.enums import ParseMode
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from core.implementations.command import BaseCommand
from database.services.subscribers import ensure_subscriber


class StartCommand(BaseCommand):
    name = 'start'
    description = 'Запустить бота'

    async def execute(self, message: Message) -> None:
        async with self.client.db.session() as db:
            async with db.begin():
                await ensure_subscriber(db, message.chat.id)

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📋 Выбрать тематики стримов", callback_data="choose_stream_topics")]
            ]
        )

        await message.reply(
            "👋 Привет! Я помощник oshuoshu!\n\n"
            "📢 Я помогаю <b>оповещать о новых стримах</b> подписчиков с YouTube и Twitch!\n\n"
            "📋 Ниже ты можешь выбрать тематики стримов, и я буду отправлять тебе уведомление когда стрим начнется!",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )