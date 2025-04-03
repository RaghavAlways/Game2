import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Union

from pyrogram import filters
from pyrogram.errors import ChatAdminRequired, ChannelPrivate, ChatNotModified, UserNotParticipant
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from AviaxMusic import app
from AviaxMusic.misc import SUDOERS
from AviaxMusic.utils.database import get_served_chats
from config import BANNED_USERS


# Dictionary to track last activity in each chat
chat_last_activity = {}

# Dictionary to track if bot has ever been used in a chat
chat_activity_record = {}

# Function to record chat activity
async def record_chat_activity(chat_id):
    current_time = datetime.now()
    chat_last_activity[chat_id] = current_time
    chat_activity_record[chat_id] = True


# Track chat activity for various commands
@app.on_message(filters.command(["play", "skip", "pause", "resume", "stop"]) & filters.group & ~BANNED_USERS)
async def track_chat_activity(_, message: Message):
    chat_id = message.chat.id
    await record_chat_activity(chat_id)


# Command to find inactive chats
@app.on_message(filters.command(["deadchats", "inactive"]) & SUDOERS)
async def find_inactive_chats(client, message: Message):
    # Check command arguments (days of inactivity)
    if len(message.command) > 1:
        try:
            days = int(message.command[1])
            if days < 1:
                days = 7  # Default to 7 days if invalid
        except ValueError:
            days = 7  # Default to 7 days if invalid
    else:
        days = 7  # Default to 7 days
    
    m = await message.reply_text(f"🔍 **Searching for inactive chats (inactive for {days} days)**\n\nThis may take some time...")
    
    # Calculate cutoff date
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # Get all chats where bot is added
    served_chats = await get_served_chats()
    
    # Lists for different categories
    inactive_chats = []
    active_chats = []
    error_chats = []
    never_used = []
    
    # Check each chat
    for chat in served_chats:
        chat_id = chat["chat_id"]
        
        # Skip if chat_id is None or invalid
        if not chat_id or not isinstance(chat_id, int):
            continue
        
        try:
            # Check if the bot is still in the chat
            try:
                await client.get_chat(chat_id)
            except (ChannelPrivate, UserNotParticipant):
                error_chats.append((chat_id, "Bot not in chat or chat not accessible"))
                continue
            
            # Check if bot was ever used in this chat
            if chat_id not in chat_activity_record:
                never_used.append(chat_id)
                continue
            
            # Check last activity time
            last_activity = chat_last_activity.get(chat_id)
            
            if not last_activity or last_activity < cutoff_date:
                # Get chat info
                try:
                    chat_info = await client.get_chat(chat_id)
                    chat_name = chat_info.title
                    member_count = await client.get_chat_members_count(chat_id)
                    inactive_chats.append((chat_id, chat_name, member_count, last_activity))
                except Exception as e:
                    error_chats.append((chat_id, str(e)))
            else:
                active_chats.append(chat_id)
        
        except Exception as e:
            error_chats.append((chat_id, str(e)))
    
    # Generate report
    report = f"""
📊 **Inactive Chats Report**

⏰ **Inactivity period:** {days} days
🔍 **Total chats checked:** {len(served_chats)}
✅ **Active chats:** {len(active_chats)}
❌ **Inactive chats:** {len(inactive_chats)}
🆕 **Never used:** {len(never_used)}
⚠️ **Error chats:** {len(error_chats)}
"""
    
    # Show inactive chats
    if inactive_chats:
        report += "\n**List of Inactive Chats:**\n"
        for i, (chat_id, chat_name, member_count, last_activity) in enumerate(inactive_chats[:10], 1):  # Limit to 10
            last_active = "Never" if not last_activity else last_activity.strftime("%Y-%m-%d")
            report += f"{i}. {chat_name} (`{chat_id}`) - {member_count} members - Last active: {last_active}\n"
        
        if len(inactive_chats) > 10:
            report += f"...and {len(inactive_chats) - 10} more.\n"
    
    # Create buttons for actions
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📤 Full Report", callback_data=f"inactive_full_{days}"),
            InlineKeyboardButton("🔄 Refresh", callback_data=f"inactive_refresh_{days}"),
        ],
        [
            InlineKeyboardButton("🚫 Leave Inactive", callback_data=f"inactive_leave_{days}"),
            InlineKeyboardButton("❌ Cancel", callback_data="inactive_cancel"),
        ]
    ])
    
    await m.edit_text(report, reply_markup=buttons)


# Callback to show full inactive report
@app.on_callback_query(filters.regex(r"^inactive_full_(\d+)$"))
async def inactive_full_callback(client, callback_query):
    if callback_query.from_user.id not in SUDOERS:
        return await callback_query.answer("❌ This action is only for sudo users.", show_alert=True)
    
    days = int(callback_query.data.split("_")[2])
    await callback_query.answer("Generating full report...")
    
    # Calculate cutoff date
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # Get all chats where bot is added
    served_chats = await get_served_chats()
    
    # Lists for different categories
    inactive_chats = []
    never_used = []
    
    # Check each chat
    for chat in served_chats:
        chat_id = chat["chat_id"]
        
        # Skip if chat_id is None or invalid
        if not chat_id or not isinstance(chat_id, int):
            continue
        
        try:
            # Check if bot was ever used in this chat
            if chat_id not in chat_activity_record:
                try:
                    chat_info = await client.get_chat(chat_id)
                    never_used.append((chat_id, chat_info.title))
                except:
                    never_used.append((chat_id, "Unknown"))
                continue
            
            # Check last activity time
            last_activity = chat_last_activity.get(chat_id)
            
            if not last_activity or last_activity < cutoff_date:
                # Get chat info
                try:
                    chat_info = await client.get_chat(chat_id)
                    inactive_chats.append((chat_id, chat_info.title, last_activity))
                except:
                    pass
        
        except Exception:
            continue
    
    # Create detailed report
    report = f"📊 **Full Inactive Chats Report (Inactive for {days} days)**\n\n"
    
    # Inactive chats
    if inactive_chats:
        report += "**Inactive Chats:**\n"
        for i, (chat_id, chat_name, last_activity) in enumerate(inactive_chats, 1):
            last_active = "Never" if not last_activity else last_activity.strftime("%Y-%m-%d")
            report += f"{i}. {chat_name} (`{chat_id}`) - Last active: {last_active}\n"
    
    # Never used
    if never_used:
        report += "\n**Never Used Chats:**\n"
        for i, (chat_id, chat_name) in enumerate(never_used, 1):
            report += f"{i}. {chat_name} (`{chat_id}`)\n"
    
    # Split long message if needed
    if len(report) > 4000:
        parts = [report[i:i+4000] for i in range(0, len(report), 4000)]
        for i, part in enumerate(parts):
            if i == 0:
                await callback_query.message.edit_text(
                    part, 
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data=f"inactive_refresh_{days}")]])
                )
            else:
                await client.send_message(callback_query.message.chat.id, part)
    else:
        await callback_query.message.edit_text(
            report,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data=f"inactive_refresh_{days}")]])
        )


# Callback to refresh inactive list
@app.on_callback_query(filters.regex(r"^inactive_refresh_(\d+)$"))
async def inactive_refresh_callback(client, callback_query):
    if callback_query.from_user.id not in SUDOERS:
        return await callback_query.answer("❌ This action is only for sudo users.", show_alert=True)
    
    days = int(callback_query.data.split("_")[2])
    await callback_query.answer("Refreshing inactive chats list...")
    
    # Recreate the command message
    message = callback_query.message
    message.command = ["deadchats", str(days)]
    message.from_user = callback_query.from_user
    
    # Call the inactive chats function again
    await find_inactive_chats(client, message)


# Callback to leave inactive chats
@app.on_callback_query(filters.regex(r"^inactive_leave_(\d+)$"))
async def inactive_leave_callback(client, callback_query):
    if callback_query.from_user.id not in SUDOERS:
        return await callback_query.answer("❌ This action is only for sudo users.", show_alert=True)
    
    days = int(callback_query.data.split("_")[2])
    
    # Confirmation buttons
    confirm_buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"inactive_leave_confirm_{days}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"inactive_refresh_{days}"),
        ]
    ])
    
    await callback_query.message.edit_text(
        f"⚠️ **Are you sure you want to leave all inactive chats?**\n\n"
        f"The bot will leave all chats that have been inactive for {days} days or more.\n"
        f"This action cannot be undone.",
        reply_markup=confirm_buttons
    )


# Confirm leave inactive chats
@app.on_callback_query(filters.regex(r"^inactive_leave_confirm_(\d+)$"))
async def inactive_leave_confirm_callback(client, callback_query):
    if callback_query.from_user.id not in SUDOERS:
        return await callback_query.answer("❌ This action is only for sudo users.", show_alert=True)
    
    days = int(callback_query.data.split("_")[3])
    await callback_query.answer("Processing...")
    
    await callback_query.message.edit_text("🔄 Processing inactive chats. Please wait...")
    
    # Calculate cutoff date
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # Get all chats where bot is added
    served_chats = await get_served_chats()
    
    # Track results
    left_chats = 0
    failed_chats = 0
    
    # Process each chat
    for chat in served_chats:
        chat_id = chat["chat_id"]
        
        # Skip if chat_id is None or invalid
        if not chat_id or not isinstance(chat_id, int):
            continue
        
        # Check if inactive based on criteria
        if (chat_id not in chat_activity_record) or (
            chat_id in chat_last_activity and 
            chat_last_activity[chat_id] < cutoff_date
        ):
            try:
                # Try to send a message before leaving
                try:
                    await client.send_message(
                        chat_id,
                        "🔴 **Automated Message**\n\n"
                        "I'm leaving this chat due to inactivity. If you need me again, feel free to add me back!"
                    )
                except:
                    pass  # If we can't send a message, still try to leave
                
                # Leave the chat
                await client.leave_chat(chat_id)
                left_chats += 1
                
                # Add a short delay to prevent flood
                await asyncio.sleep(0.5)
                
            except Exception:
                failed_chats += 1
    
    # Report results
    result_text = f"""
✅ **Operation Completed**

🚫 **Left {left_chats} inactive chats**
❌ **Failed to leave {failed_chats} chats**

Chats that were inactive for {days} days or more have been left.
"""
    
    await callback_query.message.edit_text(
        result_text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Refresh", callback_data=f"inactive_refresh_{days}")]])
    )


# Cancel operation
@app.on_callback_query(filters.regex("^inactive_cancel$"))
async def inactive_cancel_callback(client, callback_query):
    if callback_query.from_user.id not in SUDOERS:
        return await callback_query.answer("❌ This action is only for sudo users.", show_alert=True)
    
    await callback_query.answer("Operation cancelled")
    await callback_query.message.edit_text("❌ **Inactive chats operation cancelled.**") 