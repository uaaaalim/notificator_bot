def is_custom_emoji(emoji: str | None) -> bool:
    return bool(emoji) and emoji.isdigit()


def render_emoji(emoji: str, fallback_unicode_emoji: str) -> str:
    if is_custom_emoji(emoji):
        return f'<tg-emoji emoji-id="{emoji}">{fallback_unicode_emoji}</tg-emoji>'
    return emoji
