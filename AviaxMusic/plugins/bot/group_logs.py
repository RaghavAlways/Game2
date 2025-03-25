from pyrogram import filters
from pyrogram.types import Message
from pyrogram.errors import ChatWriteForbidden

import config
from AviaxMusic import app
from AviaxMusic.logging import LOGGER

@app.on_message(filters.new_chat_members, group=5)
async def on_new_chat_members(_, message: Message):
    """Handler for when bot is added to a new group"""
    try:
        # Check if the bot was added
        if message.new_chat_members:
            for member in message.new_chat_members:
                if member.id == app.id:
                    LOGGER(__name__).info(f"Bot added to {message.chat.title} ({message.chat.id})")
                    # Log the event to LOG_GROUP_ID
                    try:
                        log_message = (
                            "✨ <b>Bot Added to New Group</b>\n\n"
                            f"📮 <b>Group:</b> {message.chat.title}\n"
                            f"🆔 <b>Group ID:</b> <code>{message.chat.id}</code>\n"
                            f"🔗 <b>Username:</b> @{message.chat.username or 'Private Group'}\n"
                            f"👥 <b>Total Members:</b> {await app.get_chat_members_count(message.chat.id)}\n"
                            f"🧑‍💼 <b>Added By:</b> {message.from_user.mention if message.from_user else 'Unknown'}"
                        )
                        await app.send_message(
                            chat_id=config.LOG_GROUP_ID,
                            text=log_message,
                            disable_web_page_preview=True
                        )
                    except Exception as e:
                        LOGGER(__name__).error(f"Failed to send log message: {str(e)}")
                    
                    # Send welcome message in the group
                    welcome_message = (
                        "👋 Thanks for adding me!\n\n"
                        "🎵 I'm a powerful music bot with many features.\n"
                        "🔰 To see my commands, type /help\n\n"
                        "⚡️ Make me admin to use my full potential!"
                    )
                    try:
                        await message.reply_text(welcome_message)
                    except ChatWriteForbidden:
                        LOGGER(__name__).warning(f"Can't send welcome message in {message.chat.id}")
                    except Exception as e:
                        LOGGER(__name__).error(f"Error sending welcome message: {str(e)}")
                    break
    except Exception as e:
        LOGGER(__name__).error(f"Error in new chat members handler: {str(e)}")

# Log when bot is removed from a group
@app.on_message(filters.left_chat_member, group=5)
async def on_left_chat_member(_, message: Message):
    """Handler for when bot is removed from a group"""
    try:
        if message.left_chat_member and message.left_chat_member.id == app.id:
            LOGGER(__name__).info(f"Bot removed from {message.chat.title} ({message.chat.id})")
            try:
                log_message = (
                    "❌ <b>Bot Removed from Group</b>\n\n"
                    f"📮 <b>Group:</b> {message.chat.title}\n"
                    f"🆔 <b>Group ID:</b> <code>{message.chat.id}</code>\n"
                    f"🔗 <b>Username:</b> @{message.chat.username or 'Private Group'}\n"
                    f"👥 <b>Total Members:</b> {await app.get_chat_members_count(message.chat.id)}\n"
                    f"🧑‍💼 <b>Removed By:</b> {message.from_user.mention if message.from_user else 'Unknown'}"
                )
                await app.send_message(
                    chat_id=config.LOG_GROUP_ID,
                    text=log_message,
                    disable_web_page_preview=True
                )
            except Exception as e:
                LOGGER(__name__).error(f"Failed to send removal log message: {str(e)}")
    except Exception as e:
        LOGGER(__name__).error(f"Error in left chat member handler: {str(e)}") 