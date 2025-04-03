from datetime import datetime, timedelta
import asyncio
import time
from typing import Dict, List, Union

from pyrogram import filters
from pyrogram.types import Message

from AviaxMusic import app
from AviaxMusic.misc import SUDOERS
from AviaxMusic.utils.database import (
    get_served_chats,
    get_served_users,
    get_active_chats,
    get_active_video_chats,
    add_served_user,
)
from config import BANNED_USERS


# Dictionary to track user command usage (in-memory)
user_commands = {}
user_sessions = {}


# Track command usage for analytics
@app.on_message(filters.command(["play", "skip", "pause", "resume", "stop", "shuffle", "seek"]) & ~BANNED_USERS)
async def track_command_usage(_, message: Message):
    # Only track commands in groups
    if not message.chat or message.chat.type not in ["group", "supergroup"]:
        return
    
    user_id = message.from_user.id
    command = message.command[0]
    
    # Add user to database if not already there
    await add_served_user(user_id)
    
    # Initialize user in tracking dictionary if not present
    if user_id not in user_commands:
        user_commands[user_id] = {"total": 0}
    
    # Increment command count
    user_commands[user_id]["total"] = user_commands[user_id].get("total", 0) + 1
    user_commands[user_id][command] = user_commands[user_id].get(command, 0) + 1
    
    # Track session (when user is actively using the bot)
    current_time = int(time.time())
    user_sessions[user_id] = current_time


# Command to show user stats
@app.on_message(filters.command(["mystats", "me"]) & filters.group & ~BANNED_USERS)
async def user_stats_command(_, message: Message):
    user_id = message.from_user.id
    user_mention = message.from_user.mention
    
    m = await message.reply_text("📊 **Analyzing your stats...**")
    
    # Default stats if user not in tracking
    if user_id not in user_commands:
        stats_text = f"""
📊 **User Stats for {user_mention}**

You haven't used any commands yet.
Try using /play to start listening to music!
"""
        return await m.edit_text(stats_text)
    
    # Get user command stats
    total_commands = user_commands[user_id]["total"]
    play_count = user_commands[user_id].get("play", 0)
    skip_count = user_commands[user_id].get("skip", 0)
    pause_count = user_commands[user_id].get("pause", 0)
    resume_count = user_commands[user_id].get("resume", 0)
    
    # Calculate activity level
    activity_level = "🟢 High" if total_commands > 50 else "🟡 Medium" if total_commands > 20 else "🔴 Low"
    
    # Format stats message
    stats_text = f"""
📊 **User Stats for {user_mention}**

**Total Commands:** {total_commands}
**Play Commands:** {play_count}
**Skip Commands:** {skip_count}
**Pause Commands:** {pause_count}
**Resume Commands:** {resume_count}

**Activity Level:** {activity_level}
"""
    
    await m.edit_text(stats_text)


# Command to show top users (admin only)
@app.on_message(filters.command(["topusers"]) & SUDOERS)
async def top_users_command(_, message: Message):
    m = await message.reply_text("📊 **Fetching top users...**")
    
    if not user_commands:
        return await m.edit_text("No user stats available yet.")
    
    # Get top 10 users by command count
    sorted_users = sorted(user_commands.items(), key=lambda x: x[1]["total"], reverse=True)[:10]
    
    top_users_text = "📊 **Top 10 Active Users**\n\n"
    
    for i, (user_id, stats) in enumerate(sorted_users, start=1):
        try:
            user = await app.get_users(user_id)
            user_mention = user.mention if user else f"User {user_id}"
        except:
            user_mention = f"User {user_id}"
        
        top_users_text += f"{i}. {user_mention} - {stats['total']} commands\n"
    
    await m.edit_text(top_users_text)


# Get overall bot usage stats
@app.on_message(filters.command(["usagestats"]) & SUDOERS)
async def usage_stats_command(_, message: Message):
    m = await message.reply_text("📊 **Fetching usage statistics...**")
    
    # Get counts
    served_chats = len(await get_served_chats())
    served_users = len(await get_served_users())
    active_voice_chats = len(await get_active_chats())
    active_video_chats = len(await get_active_video_chats())
    
    # Get command distribution
    total_commands = sum(user["total"] for user in user_commands.values())
    play_commands = sum(user.get("play", 0) for user in user_commands.values())
    skip_commands = sum(user.get("skip", 0) for user in user_commands.values())
    
    # Active users in last 24 hours
    day_ago = int(time.time()) - 86400  # 24 hours ago
    active_users_24h = sum(1 for last_active in user_sessions.values() if last_active > day_ago)
    
    stats_text = f"""
📊 **Bot Usage Statistics**

**Served Chats:** {served_chats}
**Served Users:** {served_users}
**Active Voice Chats:** {active_voice_chats}
**Active Video Chats:** {active_video_chats}

**Command Usage:**
• Total Commands: {total_commands}
• Play Commands: {play_commands}
• Skip Commands: {skip_commands}

**Active Users (24h):** {active_users_24h}
"""
    
    await m.edit_text(stats_text)


# Reset command stats (useful for long-running bots)
@app.on_message(filters.command(["resetstats"]) & SUDOERS)
async def reset_stats_command(_, message: Message):
    global user_commands, user_sessions
    user_commands = {}
    user_sessions = {}
    
    await message.reply_text("✅ **All usage statistics have been reset.**") 