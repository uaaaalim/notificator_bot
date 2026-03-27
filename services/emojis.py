LIVE_IDS = [
    ("5381850182327483534", "🐙"),
    ("5379705666501888185", "🐙"),
    ("5382016247237986047", "🐙"),
    ("5381959987461373635", "🐙"),
    ("5382189493333803958", "🐙"),
    ("5382270582316353332", "🐙"),
    ("5381896185722193847", "🐙"),
]

def live_emojis() -> str:
    pattern = "<tg-emoji emoji-id=\"{id}\">{emoji}</tg-emoji>"

    return ''.join([pattern.replace("{id}", emoji_id).replace("{emoji}", emoji) for emoji_id, emoji in LIVE_IDS])

YOUTUBE_EMOJI = "<tg-emoji emoji-id=\"5334681713316479679\">📱</tg-emoji>"
YOUTUBE_EMOJI_ID = '5334681713316479679'
TWITCH_EMOJI = "<tg-emoji emoji-id=\"5334678011054669335\">📱</tg-emoji>"
TWITCH_EMOJI_ID = '5334678011054669335'

LIGHTENING_EMOJI = "<tg-emoji emoji-id=\"5456140674028019486\">⚡️</tg-emoji>"
LIGHTENING_EMOJI_ID = "5456140674028019486"

HONEYLAND_EMOJI = "<tg-emoji emoji-id=\"5233415653016239891\">🐝</tg-emoji>"