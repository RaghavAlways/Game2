from pyrogram import filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from AviaxMusic import app

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