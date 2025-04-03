import asyncio
from datetime import datetime

from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.errors import ChatAdminRequired, ChatWriteForbidden, MessageIdInvalid
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from AviaxMusic import app
from AviaxMusic.misc import SUDOERS
from AviaxMusic.utils.database import is_logger, logger_off, logger_on
from config import LOG_GROUP_ID


# Enable or disable logging
@app.on_message(filters.command(["logger"]) & SUDOERS)
async def logger_command(client, message: Message):
    usage = "**Usage:**\n/logger [enable|disable]"
    if len(message.command) != 2:
        return await message.reply_text(usage)
    state = message.text.split(None, 1)[1].strip().lower()
    if state == "enable":
        await logger_on()
        await message.reply_text("**Enabled logging!**\n\nBot will now log all important activities in the log channel.")
    elif state == "disable":
        await logger_off()
        await message.reply_text("**Disabled logging!**\n\nBot will no longer log activities.")
    else:
        await message.reply_text(usage)


# Log deleted messages, especially when music is playing
@app.on_message(filters.group & filters.command(["play", "vplay", "cplay"]) & ~filters.bot & ~filters.via_bot)
async def log_play_command(client, message: Message):
    if not await is_logger():
        return
    if not LOG_GROUP_ID:
        return
    
    chat_name = message.chat.title
    chat_id = message.chat.id
    user = message.from_user
    
    # Create pretty log message
    log_text = f"""
🎵 **NEW PLAY COMMAND**

**Group:** {chat_name}
**Group ID:** `{chat_id}`
**User:** {user.mention} [`{user.id}`]
**Username:** @{user.username if user.username else "None"}
**Command:** `{message.text}`
**Time:** `{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}`
"""
    
    try:
        await client.send_message(LOG_GROUP_ID, log_text)
    except Exception as e:
        print(f"Error in logging play command: {e}")


# Log errors in the bot
async def log_error(error_message):
    if not LOG_GROUP_ID:
        return
    
    try:
        error_log = f"""
⚠️ **BOT ERROR**

**Error:** `{error_message}`
**Time:** `{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}`
"""
        await app.send_message(LOG_GROUP_ID, error_log)
    except Exception as e:
        print(f"Error sending error log: {e}")


# Log user actions like skips, stops, pauses, etc.
@app.on_message(
    filters.group
    & filters.command(["skip", "stop", "pause", "resume", "end", "loop"])
    & ~filters.bot
    & ~filters.via_bot
)
async def log_player_actions(client, message: Message):
    if not await is_logger():
        return
    if not LOG_GROUP_ID:
        return
    
    chat_name = message.chat.title
    chat_id = message.chat.id
    user = message.from_user
    
    # Get command name
    command = message.command[0]
    
    # Create log message
    log_text = f"""
⚙️ **PLAYER ACTION**

**Action:** `{command}`
**Group:** {chat_name}
**Group ID:** `{chat_id}`
**User:** {user.mention} [`{user.id}`]
**Time:** `{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}`
"""
    
    try:
        await client.send_message(LOG_GROUP_ID, log_text)
    except Exception as e:
        print(f"Error in logging player action: {e}")


# Log new auth users (when someone adds an auth user)
@app.on_message(filters.group & filters.command(["auth", "unauth"]) & ~filters.bot & ~filters.via_bot)
async def log_auth_changes(client, message: Message):
    if not await is_logger():
        return
    if not LOG_GROUP_ID:
        return
    
    chat_name = message.chat.title
    chat_id = message.chat.id
    user = message.from_user
    
    # Get command name
    command = message.command[0]
    
    # Create log message
    log_text = f"""
👮 **AUTH USER CHANGE**

**Action:** `{command}`
**Group:** {chat_name}
**Group ID:** `{chat_id}`
**Admin:** {user.mention} [`{user.id}`]
**Time:** `{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}`
"""
    
    try:
        await client.send_message(LOG_GROUP_ID, log_text)
    except Exception as e:
        print(f"Error in logging auth change: {e}")


# Log when someone blacklists a chat
@app.on_message(filters.command(["blacklistchat", "whitelistchat"]) & SUDOERS)
async def log_blacklist_changes(client, message: Message):
    if not await is_logger():
        return
    if not LOG_GROUP_ID:
        return
    
    user = message.from_user
    command = message.command[0]
    
    # Create log message
    log_text = f"""
🚫 **BLACKLIST CHANGE**

**Action:** `{command}`
**Admin:** {user.mention} [`{user.id}`]
**Command:** `{message.text}`
**Time:** `{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}`
"""
    
    try:
        await client.send_message(LOG_GROUP_ID, log_text)
    except Exception as e:
        print(f"Error in logging blacklist change: {e}")


# Log when someone blocks/unblocks a user
@app.on_message(filters.command(["block", "unblock"]) & SUDOERS)
async def log_block_changes(client, message: Message):
    if not await is_logger():
        return
    if not LOG_GROUP_ID:
        return
    
    user = message.from_user
    command = message.command[0]
    
    # Create log message
    log_text = f"""
🚷 **USER BLOCK/UNBLOCK**

**Action:** `{command}`
**Admin:** {user.mention} [`{user.id}`]
**Command:** `{message.text}`
**Time:** `{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}`
"""
    
    try:
        await client.send_message(LOG_GROUP_ID, log_text)
    except Exception as e:
        print(f"Error in logging block change: {e}")


# Log broadcast commands
@app.on_message(filters.command(["broadcast"]) & SUDOERS)
async def log_broadcast(client, message: Message):
    if not await is_logger():
        return
    if not LOG_GROUP_ID:
        return
    
    user = message.from_user
    
    # Create log message
    log_text = f"""
📣 **BROADCAST INITIATED**

**Admin:** {user.mention} [`{user.id}`]
**Time:** `{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}`
"""
    
    try:
        await client.send_message(LOG_GROUP_ID, log_text)
    except Exception as e:
        print(f"Error in logging broadcast: {e}") 