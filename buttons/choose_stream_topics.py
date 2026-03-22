from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from core.implementations.button import BaseButton
from database.repos import Repositories
from services.subscribers import get_subscriber, get_select_topics


class ChooseStreamTopicsButton(BaseButton):
    callback_data = "choose_stream_topics"

    async def execute(self, callback: CallbackQuery) -> None:
        async with self.client.db.session() as db:
            repos = Repositories(db)

            subscriber = await get_subscriber(db, callback.message.chat.id) # Register subscriber
            topics = await repos.stream_topics.get_all()

            keyboard = InlineKeyboardMarkup(inline_keyboard=get_select_topics(subscriber, topics))

        await callback.message.edit_text(
            "📢 Выбор тематик стримов!\n\n"
            "📃 Тут ты можешь выбрать тематики стримов по которым ты хочешь получать уведомления\n\n"
            "⚠️ Ваш выбор сохранится автоматически",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
        await callback.answer()