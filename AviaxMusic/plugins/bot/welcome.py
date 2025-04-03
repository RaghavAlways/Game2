from pyrogram import filters, Client
from pyrogram.types import Message
import asyncio
from AviaxMusic import app
from AviaxMusic.misc import SUDOERS
from AviaxMusic.utils.database import get_served_chats
from config import LOG_GROUP_ID


# Welcome message when bot is added to a group
@app.on_message(filters.new_chat_members)
async def welcome(client: Client, message: Message):
    bot_id = (await client.get_me()).id
    for member in message.new_chat_members:
        if member.id == bot_id:
            # Bot was added to a group
            chat_name = message.chat.title
            chat_id = message.chat.id
            
            # Welcome message in the group
            welcome_text = f"""
💫 **Thanks for adding me to {chat_name}!**

🎵 I'm a powerful music player bot with advanced features.

👉 Use /help to see available commands
👉 Use /play [song name] to play music
👉 Use /channelplay to play in linked channels

**Made with ❤️ by @AviaxTeam**
"""
            await message.reply_text(welcome_text)
            
            # Log message to log channel
            if LOG_GROUP_ID:
                try:
                    log_text = f"""
🆕 **NEW GROUP**

**Group:** {chat_name}
**Group ID:** `{chat_id}`
**Added by:** {message.from_user.mention if message.from_user else "Unknown"}
"""
                    await client.send_message(LOG_GROUP_ID, log_text)
                except Exception as e:
                    print(f"Error sending log message: {e}")


# Bot removal handler
@app.on_message(filters.left_chat_member)
async def on_left_chat_member(client: Client, message: Message):
    bot_id = (await client.get_me()).id
    if message.left_chat_member.id == bot_id:
        # Bot was removed from group
        chat_name = message.chat.title
        chat_id = message.chat.id
        
        # Log the removal
        if LOG_GROUP_ID:
            try:
                log_text = f"""
❌ **REMOVED FROM GROUP**

**Group:** {chat_name}
**Group ID:** `{chat_id}`
**Removed by:** {message.from_user.mention if message.from_user else "Unknown"}
"""
                await client.send_message(LOG_GROUP_ID, log_text)
            except Exception as e:
                print(f"Error sending removal log message: {e}")


# Command to show bot stats
@app.on_message(filters.command("stats") & SUDOERS)
async def stats_command(client: Client, message: Message):
    m = await message.reply_text("⚡️ **Fetching stats...**")
    
    try:
        # Get all served chats
        chats = await get_served_chats()
        
        # Count users, chats, and active voice chats
        total_chats = len(chats)
        
        # Format stats message
        text = f"""
📊 **Current Bot Statistics**

👥 **Total Groups:** {total_chats}
📂 **Total Commands:** 40+
⌛️ **Uptime:** Since last restart
🔄 **CPU Usage:** {client.cpu_usage}%
💾 **RAM Usage:** {client.ram_usage}%
"""
        await m.edit_text(text)
    except Exception as e:
        await m.edit_text(f"Error fetching stats: {str(e)}") 