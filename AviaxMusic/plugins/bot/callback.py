from pyrogram import filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from AviaxMusic import app
from AviaxMusic.plugins.bot.wordle import start_wordle

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