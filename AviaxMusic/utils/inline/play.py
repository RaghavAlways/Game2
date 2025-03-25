import math
import random

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from AviaxMusic.utils.formatters import time_to_seconds


def close_keyboard():
    """Close keyboard markup buttons"""
    buttons = [
        [
            InlineKeyboardButton(
                text="🗑 Close",
                callback_data=f"close",
            ),
        ]
    ]
    return InlineKeyboardMarkup(buttons)


def track_markup(_, videoid, user_id, channel, fplay):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="Play Game",
                callback_data="start_wordle",
            ),
            InlineKeyboardButton(
                text="🎬 Get Direct Movie 🎬",
                url="https://t.me/LB_Movies"
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
            )
        ],
    ]
    return buttons


def stream_markup_timer(_, videoid, chat_id, played, dur):
    played_sec = time_to_seconds(played)
    duration_sec = time_to_seconds(dur)
    percentage = (played_sec / duration_sec) * 100
    anon = math.floor(percentage)
    if 0 < anon <= 10:
        bar = "⬤─────────"
    elif 10 < anon < 20:
        bar = "━⬤────────"
    elif 20 <= anon < 30:
        bar = "━━⬤───────"
    elif 30 <= anon < 40:
        bar = "━━━⬤──────"
    elif 40 <= anon < 50:
        bar = "━━━━⬤─────"
    elif 50 <= anon < 60:
        bar = "━━━━━⬤────"
    elif 60 <= anon < 70:
        bar = "━━━━━━⬤───"
    elif 70 <= anon < 80:
        bar = "━━━━━━━⬤──"
    elif 80 <= anon < 95:
        bar = "━━━━━━━━⬤─"
    else:
        bar = "━━━━━━━━━⬤"

    buttons = [
        [
            InlineKeyboardButton(
                text=f"{played} {bar} {dur}",
                callback_data="GetTimer",
            )
        ],
        [
            InlineKeyboardButton(
                text="▷",
                callback_data=f"ADMIN Resume|{chat_id}",
            ),
            InlineKeyboardButton(
                text="II", callback_data=f"ADMIN Pause|{chat_id}"
            ),
            InlineKeyboardButton(
                text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}"
            ),
            InlineKeyboardButton(
                text="▢", callback_data=f"ADMIN Stop|{chat_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🍿 Movie",
                url="https://t.me/LB_Movies"
            ),
            InlineKeyboardButton(
                text="🎮 Game",
                callback_data="start_wordle",
            ),
        ],
    ]
    return buttons


def telegram_markup_timer(_, chat_id, played, dur):
    played_sec = time_to_seconds(played)
    duration_sec = time_to_seconds(dur)
    percentage = (played_sec / duration_sec) * 100
    anon = math.floor(percentage)
    if 0 < anon <= 10:
        bar = "⬤─────────"
    elif 10 < anon < 20:
        bar = "━⬤────────"
    elif 20 <= anon < 30:
        bar = "━━⬤───────"
    elif 30 <= anon < 40:
        bar = "━━━⬤──────"
    elif 40 <= anon < 50:
        bar = "━━━━⬤─────"
    elif 50 <= anon < 60:
        bar = "━━━━━⬤────"
    elif 60 <= anon < 70:
        bar = "━━━━━━⬤───"
    elif 70 <= anon < 80:
        bar = "━━━━━━━⬤──"
    elif 80 <= anon < 95:
        bar = "━━━━━━━━⬤─"
    else:
        bar = "━━━━━━━━━⬤"

    buttons = [
        [
            InlineKeyboardButton(
                text=f"{played} {bar} {dur}",
                callback_data="GetTimer",
            )
        ],
        [
            InlineKeyboardButton(
                text="▷",
                callback_data=f"ADMIN Resume|{chat_id}",
            ),
            InlineKeyboardButton(
                text="II", callback_data=f"ADMIN Pause|{chat_id}"
            ),
            InlineKeyboardButton(
                text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}"
            ),
            InlineKeyboardButton(
                text="▢", callback_data=f"ADMIN Stop|{chat_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🍿 Movie",
                url="https://t.me/LB_Movies"
            ),
            InlineKeyboardButton(
                text="🎮 Game",
                callback_data="start_wordle",
            ),
        ],
    ]
    return buttons


def stream_markup(_, videoid=None, chat_id=None):
    """Stream markup buttons
    
    In most places this function is called with just _ and chat_id
    but in some places it's called with _, videoid, chat_id
    This modification allows both usages.
    """
    if chat_id is None and videoid is not None:
        # For backward compatibility with code that calls stream_markup(_, chat_id)
        chat_id = videoid
        videoid = None
        
    buttons = [
        [
            InlineKeyboardButton(
                text="▷",
                callback_data=f"ADMIN Resume|{chat_id}",
            ),
            InlineKeyboardButton(
                text="II", callback_data=f"ADMIN Pause|{chat_id}"
            ),
            InlineKeyboardButton(
                text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}"
            ),
            InlineKeyboardButton(
                text="▢", callback_data=f"ADMIN Stop|{chat_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🍿 Movie",
                url="https://t.me/LB_Movies"
            ),
            InlineKeyboardButton(
                text="🎮 Game",
                callback_data="start_wordle",
            ),
        ],
    ]
    
    return buttons


def telegram_markup(_, chat_id):
    buttons = [
        [
            InlineKeyboardButton(
                text="▷",
                callback_data=f"ADMIN Resume|{chat_id}",
            ),
            InlineKeyboardButton(
                text="II", callback_data=f"ADMIN Pause|{chat_id}"
            ),
            InlineKeyboardButton(
                text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}"
            ),
            InlineKeyboardButton(
                text="▢", callback_data=f"ADMIN Stop|{chat_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🍿 Movie",
                url="https://t.me/LB_Movies"
            ),
            InlineKeyboardButton(
                text="🎮 Game",
                callback_data="start_wordle",
            ),
        ],
    ]
    return buttons


def playlist_markup(_, videoid, user_id, ptype, channel, fplay):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"AviaxPlaylists {videoid}|{user_id}|{ptype}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"AviaxPlaylists {videoid}|{user_id}|{ptype}|v|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🎮 Game",
                callback_data="start_wordle",
            ),
            InlineKeyboardButton(
                text="🍿 Movie",
                url="https://t.me/LB_Movies"
            ),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
            ),
        ],
    ]
    return buttons


def livestream_markup(_, videoid, user_id, mode, channel, fplay):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_3"],
                callback_data=f"LiveStream {videoid}|{user_id}|{mode}|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🎮 Game",
                callback_data="start_wordle",
            ),
            InlineKeyboardButton(
                text="🍿 Movie",
                url="https://t.me/LB_Movies"
            ),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
            ),
        ],
    ]
    return buttons


def slider_markup(_, videoid, user_id, query, query_type, channel, fplay):
    query = f"{query[:20]}"
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="◁",
                callback_data=f"slider B|{query_type}|{query}|{user_id}|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {query}|{user_id}",
            ),
            InlineKeyboardButton(
                text="▷",
                callback_data=f"slider F|{query_type}|{query}|{user_id}|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🍿 Movie",
                url="https://t.me/LB_Movies"
            ),
            InlineKeyboardButton(
                text="🎮 Game",
                callback_data="start_wordle",
            ),
        ],
    ]
    return buttons
