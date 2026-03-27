from typing import Final


def is_custom_emoji(emoji: str | None) -> bool:
    return bool(emoji) and emoji.isdigit()


def render_emoji(emoji: str, fallback_unicode_emoji: str) -> str:
    if is_custom_emoji(emoji):
        return f'<tg-emoji emoji-id="{emoji}">{fallback_unicode_emoji}</tg-emoji>'
    return emoji


LIVE_EMOJI_IDS: Final[list[tuple[str, str]]] = [
    ("5381850182327483534", "🐙"),
    ("5379705666501888185", "🐙"),
    ("5382016247237986047", "🐙"),
    ("5381959987461373635", "🐙"),
    ("5382189493333803958", "🐙"),
    ("5382270582316353332", "🐙"),
    ("5381896185722193847", "🐙"),
]

YOUTUBE_EMOJI_ID = "5334681713316479679"
TWITCH_EMOJI_ID = "5334678011054669335"
LIGHTENING_EMOJI_ID = "5456140674028019486"
HONEYLAND_EMOJI_ID = "5233415653016239891"
STAR_EMOJI_ID = "5438496463044752972"
MOON_EMOJI_ID = "5449569374065152798"

YOUTUBE_EMOJI = render_emoji(YOUTUBE_EMOJI_ID, "📱")
TWITCH_EMOJI = render_emoji(TWITCH_EMOJI_ID, "📱")
LIGHTENING_EMOJI = render_emoji(LIGHTENING_EMOJI_ID, "⚡️")
HONEYLAND_EMOJI = render_emoji(HONEYLAND_EMOJI_ID, "🐝")


def live_emojis() -> str:
    return "".join(render_emoji(emoji_id, emoji) for emoji_id, emoji in LIVE_EMOJI_IDS)
