from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from core.implementations.command import BaseCommand, CommandPermissionLevel


class AdminCommand(BaseCommand):
    name = 'admin'
    description = 'Центральное управление ботом'
    permission_level = CommandPermissionLevel.OWNER


    async def execute(self, message: Message) -> None:
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
            await prompt.edit_text("topics")

        elif callback.data == "admin:announcements":
            await prompt.edit_text("announcements")
