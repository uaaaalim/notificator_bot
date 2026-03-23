from collections.abc import Sequence

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.entities.stream_topic import StreamTopicEntity
from database.entities.subscribers import SubscriberEntity


def get_select_topic_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Выбрать тематики стримов", callback_data="choose_stream_topics")]
        ]
    )


def get_select_topics(subscriber: SubscriberEntity, topics: Sequence[StreamTopicEntity]):
    buttons = []
    user_topics = [topic.id for topic in subscriber.stream_topics]

    for topic in topics:
        if topic.id in user_topics:
            topic_name = "✅ " + topic.name
        else:
            topic_name = "⬜ " + topic.name

        buttons.append([InlineKeyboardButton(
            text=topic_name,
            callback_data="stream_topic:" + str(topic.id)
        )])

    buttons.append(
        [InlineKeyboardButton(text="✅ Выбрать все тематики", callback_data="stream_topic:all")]
    )
    buttons.append(
        [InlineKeyboardButton(text="❌ Убрать все тематики", callback_data="stream_topic:none")]
    )
    buttons.append(
        [InlineKeyboardButton(text="📁 Сохранить", callback_data="stream_topic:save")]
    )

    return buttons
