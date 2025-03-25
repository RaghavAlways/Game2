@app.on_callback_query(filters.regex("game_mode"))
async def game_mode_callback(_, query: CallbackQuery):
    try:
        await query.message.reply_text(
            """
🎮 **Welcome to Game Mode!**

Available Games:
1. 🎯 **Hangman** - Classic word guessing game
   • Command: /hangman
   • Help: /hangmanhelp

More games coming soon! Choose a game to start playing.
""",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎯 Play Hangman", callback_data="start_hangman")],
                [InlineKeyboardButton("❌ Close", callback_data="close")]
            ])
        )
        await query.answer()
    except Exception as e:
        print(e)
        await query.answer("Error occurred! Try again later.", show_alert=True)

@app.on_callback_query(filters.regex("start_hangman"))
async def start_hangman_callback(_, query: CallbackQuery):
    try:
        # Simulate /hangman command
        message = query.message
        message.command = ["hangman"]
        await start_hangman(_, message)
        await query.answer()
    except Exception as e:
        print(e)
        await query.answer("Error starting game! Try using /hangman command.", show_alert=True) 