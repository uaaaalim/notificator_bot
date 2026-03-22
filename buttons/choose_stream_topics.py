from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from sqlalchemy.orm import selectinload

from core.implementations.button import BaseButton
from database.entities.subscribers import SubscriberEntity
from database.services import stream_topics
from database.services import subscribers
from services.subscribers import get_select_topics


class ChooseStreamTopicsButton(BaseButton):
    callback_data = "choose_stream_topics"

    async def execute(self, callback: CallbackQuery) -> None:
        async with self.client.db.session() as db:
            async with db.begin():
                tg_id = callback.message.chat.id
                await subscribers.ensure_subscriber(db, tg_id)

                subscriber_item = await subscribers.get_subscriber(
                    db,
                    tg_id,
                    options=[selectinload(SubscriberEntity.stream_topics)],
                )
                if not subscriber_item:
                    await callback.answer("Ошибка загрузки подписчика", show_alert=True)
                    return

                topics = await stream_topics.get_stream_topics(db)

                keyboard = InlineKeyboardMarkup(inline_keyboard=get_select_topics(subscriber_item, topics))

        await callback.message.edit_text(
            "📢 Выбор тематик стримов!\n\n"
            "📃 Тут ты можешь выбрать тематики стримов по которым ты хочешь получать уведомления\n\n"
            "⚠️ Ваш выбор сохранится автоматически",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
        await callback.answer()
