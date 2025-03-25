from pyrogram import filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from AviaxMusic import app
from AviaxMusic.plugins.bot.wordle import start_wordle
from AviaxMusic.core.call import Aviax
from AviaxMusic.misc import db
from AviaxMusic.utils.database import set_loop
from AviaxMusic.utils.decorators.language import languageCB
from AviaxMusic.utils.inline.play import close_keyboard, stream_markup, telegram_markup
from AviaxMusic.utils.stream.stream import stream
from config import BANNED_USERS

@app.on_callback_query(filters.regex("start_wordle"))
async def start_wordle_from_button(_, query: CallbackQuery):
    try:
        # Simulate /wordle command
        message = query.message
        message.command = ["wordle"]
        message.from_user = query.from_user
        await start_wordle(_, message)
        await query.answer()
    except Exception as e:
        print(e)
        await query.answer("Error starting game! Try using /wordle command.", show_alert=True)

@app.on_callback_query(filters.regex("get_movie"))
async def get_movie_callback(_, query: CallbackQuery):
    try:
        await query.message.reply_text(
            """
🎬 **Movie Zone**

Join our movie channel for:
• Latest Movies
• TV Shows
• Web Series
• Anime
• And much more!

📺 @LB_Movies
""",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🍿 Join Channel 🍿", url="https://t.me/LB_Movies")],
                [InlineKeyboardButton("❌ Close", callback_data="close")]
            ])
        )
        await query.answer()
    except Exception as e:
        print(e)
        await query.answer("Error occurred! Try again later.", show_alert=True)

@app.on_callback_query(filters.regex("LiveAction") & ~BANNED_USERS)
@languageCB
async def stream_menu_cb(client, CallbackQuery, _):
    try:
        callback_data = CallbackQuery.data.strip()
        callback_request = callback_data.split(None, 1)[1]
        vidid, user_id, mode, cplay, fplay = callback_request.split("|")
        chat_id = CallbackQuery.message.chat.id
        if CallbackQuery.from_user.id != int(user_id):
            try:
                return await CallbackQuery.answer(_["playcb_1"], show_alert=True)
            except:
                return
        buttons = telegram_markup(_, chat_id)
        if mode == "Forceplay":
            await CallbackQuery.answer()
            await Aviax.force_stop_stream(chat_id)
            state = await Aviax.force_play_stream(
                client,
                chat_id,
                vidid,
                video=True if mode == "v" else None,
            )
            if state:
                await CallbackQuery.message.reply_text(_["playcb_2"])
            else:
                await CallbackQuery.message.reply_text(_["playcb_3"])
                return
        return await CallbackQuery.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception as e:
        print("Error in LiveAction callback: ", e)
        pass

@app.on_callback_query(filters.regex("wordle_button") & ~BANNED_USERS)
async def wordle_button_callback(client, CallbackQuery):
    try:
        await CallbackQuery.answer()
        message = CallbackQuery.message
        message.command = ["wordle"]
        message.from_user = CallbackQuery.from_user
        
        # Import the wordle module and call start_wordle function
        from AviaxMusic.plugins.bot.wordle import start_wordle
        await start_wordle(client, message)
    except Exception as e:
        print("Error in wordle button callback: ", e)
        await CallbackQuery.answer("Something went wrong while starting Wordle game. Try using /wordle command instead.", show_alert=True) 