from pyrogram import filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from AviaxMusic import app
from AviaxMusic.core.call import Aviax
from AviaxMusic.misc import db
from AviaxMusic.utils.database import set_loop
from AviaxMusic.utils.decorators.language import languageCB
from AviaxMusic.utils.inline.play import close_keyboard, stream_markup, telegram_markup
from AviaxMusic.utils.stream.stream import stream
from config import BANNED_USERS

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

@app.on_callback_query(filters.regex("wordle_button|start_wordle") & ~BANNED_USERS)
async def wordle_button_callback(client, CallbackQuery):
    """Handle Wordle game start from music player interface"""
    try:
        # Better user feedback
        await CallbackQuery.answer("Starting Wordle game...")
        
        # Fix: Create proper message attributes
        message = CallbackQuery.message
        message.command = ["wordle"]
        message.from_user = CallbackQuery.from_user
        
        # Log the attempt for debugging
        print(f"Starting Wordle game from button. User: {CallbackQuery.from_user.id}, Chat: {CallbackQuery.message.chat.id}")
        
        # Import directly to ensure we get the latest version
        from AviaxMusic.plugins.bot.wordle import start_wordle
        
        # Start the game
        await start_wordle(client, message)
        
    except Exception as e:
        # Detailed error logging
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in wordle_button_callback: {str(e)}\n{error_trace}")
        
        # More helpful error message to user
        await CallbackQuery.answer(
            "Could not start game. Try using /wordle command directly.", 
            show_alert=True
        ) 