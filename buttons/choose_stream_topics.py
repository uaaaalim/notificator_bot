from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from sqlalchemy.orm import selectinload

from core.implementations.button import BaseButton
from database.entities.subscribers import SubscriberEntity
from database.services import stream_topics
from database.services import subscribers
from services.streams import get_select_topic_keyboard
from services.streams import get_select_topics


class ChooseStreamTopicsButton(BaseButton):
    callback_data = "choose_stream_topics"

    async def execute(self, callback: CallbackQuery) -> None:
        tg_id = callback.message.chat.id

        async with self.client.db.session() as db:
            async with db.begin():
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

                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=get_select_topics(subscriber_item, topics)
                )

        prompt = await callback.message.edit_text(
            "📢 Выбор тематик стримов!\n\n"
            "📃 Тут ты можешь выбрать тематики стримов по которым ты хочешь получать уведомления\n\n"
            "⚠️ Ваш выбор сохранится автоматически",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
        await callback.answer()

        async def on_timeout():
            await prompt.edit_text(
                "✅ Выбор любимых тематик был <b>сохранен автоматически</b>.\n\n"
                "📃 Нажмите кнопку ниже, чтобы изменить выбор снова.",
                reply_markup=get_select_topic_keyboard(),
                parse_mode=ParseMode.HTML
            )

        while True:
            cb = await self.client.wait_for_button(
                callback.message.chat.id,
                callback.from_user.id,
                timeout=15,
                message_id=prompt.message_id,
                on_timeout=on_timeout
            )

            if not cb or not cb.data.startswith("stream_topic:"):
                return

            data = cb.data.split(":")[1]

            if data == "save":
                await on_timeout()
                return

            async with self.client.db.session() as db:
                async with db.begin():
                    subscriber_item = await subscribers.get_subscriber(
                        db,
                        tg_id,
                        options=[selectinload(SubscriberEntity.stream_topics)],
                    )
                    if not subscriber_item:
                        await cb.answer("Ошибка загрузки подписчика", show_alert=True)
                        return

                    topics = await stream_topics.get_stream_topics(db)

                    if data == "all":
                        subscriber_item.stream_topics = list(topics)

                    elif data == "none":
                        subscriber_item.stream_topics.clear()

                    else:
                        topic_id = int(data)
                        for topic in topics:
                            if topic.id == topic_id:
                                if topic in subscriber_item.stream_topics:
                                    subscriber_item.stream_topics.remove(topic)
                                else:
                                    subscriber_item.stream_topics.append(topic)
                                break

                    keyboard = InlineKeyboardMarkup(
                        inline_keyboard=get_select_topics(subscriber_item, topics)
                    )

            await prompt.edit_reply_markup(reply_markup=keyboard)
            await cb.answer()
