import time
import asyncio
import re
import os

from pyrogram import filters, Client
from pyrogram.enums import ChatType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from youtubesearchpython.__future__ import VideosSearch

import config
from AviaxMusic import app
from AviaxMusic.misc import _boot_
from AviaxMusic.plugins.sudo.sudoers import sudoers_list
from AviaxMusic.utils.database import (
    add_served_chat,
    add_served_user,
    blacklisted_chats,
    get_lang,
    is_banned_user,
    is_on_off,
)
from AviaxMusic.utils import bot_sys_stats
from AviaxMusic.utils.decorators.language import LanguageStart
from AviaxMusic.utils.formatters import get_readable_time
from AviaxMusic.utils.inline import help_pannel, private_panel, start_panel
from config import BANNED_USERS, SUPPORT_CHANNEL, SUPPORT_GROUP
from strings import get_string


# Regex pattern for YouTube links
YOUTUBE_REGEX = r"(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})"

@app.on_message(filters.command(["start"]) & filters.private & ~BANNED_USERS)
async def start_private_command(client: Client, message: Message):
    # Get or extract arguments if any
    if len(message.command) > 1:
        query = message.text.split(None, 1)[1].lower().strip()
        
        # Handle YouTube URL start arguments
        if re.search(YOUTUBE_REGEX, query):
            # Redirecting to play command
            return await message.reply_text(
                f"🎵 **Processing YouTube link**\n\nUse this link in a group where I'm admin using the /play command."
            )
    
    # User's first name
    first_name = message.from_user.first_name
    
    # Animated welcome (typing effect)
    welcome_msg = await message.reply_text("Welcome! Starting my engines...")
    
    # Create an animated typing effect
    welcome_text = f"Hello {first_name}! 👋\n\nI'm Aviax Music Bot"
    for i in range(len(welcome_text) + 1):
        await welcome_msg.edit_text(
            welcome_text[:i] + "▒" + welcome_text[i:],
        )
        await asyncio.sleep(0.05)  # Adjust speed as needed
    
    # Delete the animation message
    await welcome_msg.delete()
    
    # Main welcome message with buttons
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{app.username}?startgroup=true"),
        ],
        [
            InlineKeyboardButton("🔍 Commands", callback_data="command_list"),
            InlineKeyboardButton("⚙️ Settings", callback_data="settings_menu")
        ],
        [
            InlineKeyboardButton("📢 Updates", url=f"{SUPPORT_CHANNEL}"),
            InlineKeyboardButton("💬 Support", url=f"{SUPPORT_GROUP}")
        ]
    ])
    
    # Greeting message with user's photo if available
    if message.from_user.photo:
        try:
            user_profile = await client.download_media(message.from_user.photo.big_file_id)
            await message.reply_photo(
                photo=user_profile,
                caption=f"""
✨ **Welcome, {message.from_user.mention}!** ✨

🎵 I'm a feature-rich music player bot with advanced features like:
  • Channel playback
  • High quality audio streaming
  • Multiple language support
  • Custom playlists and queues

👉 Add me to your group and make me admin to get started!
""",
                reply_markup=buttons
            )
            # Remove the downloaded file
            try:
                os.remove(user_profile)
            except:
                pass
        except Exception as e:
            print(f"Error processing user profile: {e}")
            # Fallback to regular message
            await send_default_welcome(message, buttons)
    else:
        await send_default_welcome(message, buttons)


async def send_default_welcome(message, buttons):
    await message.reply_photo(
        photo="https://telegra.ph/file/76df753c1cde9dd3f8a6b.jpg",  # Default image
        caption=f"""
✨ **Welcome, {message.from_user.mention}!** ✨

🎵 I'm a feature-rich music player bot with advanced features like:
  • Channel playback
  • High quality audio streaming
  • Multiple language support
  • Custom playlists and queues

👉 Add me to your group and make me admin to get started!
""",
        reply_markup=buttons
    )


@app.on_message(filters.command(["start"]) & filters.group & ~BANNED_USERS)
async def start_group_command(client: Client, message: Message):
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💬 Support", url=f"{SUPPORT_GROUP}"),
            InlineKeyboardButton("🔍 Commands", callback_data="command_list")
        ]
    ])
    
    await message.reply_photo(
        photo="https://telegra.ph/file/76df753c1cde9dd3f8a6b.jpg",
        caption=f"""
👋 **Hi there!**

I'm ready to play some music for you! Use /help to see available commands.

🎵 `/play [song name]` - Play a song
⏭️ `/skip` - Skip current song
⏹️ `/stop` - Stop playback
🔄 `/reload` - Refresh admin cache
""",
        reply_markup=buttons
    )
