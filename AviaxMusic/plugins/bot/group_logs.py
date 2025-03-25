from pyrogram import filters
from pyrogram.types import Message

from AviaxMusic import app
from AviaxMusic.utils.logger import group_logger

@app.on_message(filters.new_chat_members)
async def on_new_chat_members(_, message: Message):
    """Handler for when bot is added to a new group"""
    try:
        # Check if the bot was added
        if message.new_chat_members:
            for member in message.new_chat_members:
                if member.id == app.id:
                    # Log the event
                    await group_logger(message)
                    
                    # Send welcome message in the group
                    welcome_message = (
                        "👋 Thanks for adding me!\n\n"
                        "🎵 I'm a powerful music bot with many features.\n"
                        "🔰 To see my commands, type /help\n\n"
                        "⚡️ Make me admin to use my full potential!"
                    )
                    try:
                        await message.reply_text(welcome_message)
                    except:
                        pass  # If can't send message, just continue
                    break
    except Exception as e:
        print(f"Error in new chat members handler: {str(e)}") 