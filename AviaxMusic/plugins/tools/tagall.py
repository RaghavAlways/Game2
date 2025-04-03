import asyncio
import random
from typing import List, Union

from pyrogram import filters
from pyrogram.errors import FloodWait
from pyrogram.types import Message, ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton

from AviaxMusic import app
from AviaxMusic.misc import SUDOERS
from config import BANNED_USERS


# Store tag processes per group
active_tags = {}

# Function to generate tag messages with random styles
def get_tag_formats(name, user_id):
    formats = [
        f"[{name}](tg://user?id={user_id})",
        f"[{name}](tg://user?id={user_id}) 👋",
        f"👤 [{name}](tg://user?id={user_id})",
        f"**[{name}](tg://user?id={user_id})**",
        f"🔔 [{name}](tg://user?id={user_id})",
        f"📢 [{name}](tg://user?id={user_id})",
    ]
    return random.choice(formats)


# Check if user is an admin
async def is_admin(message: Message) -> bool:
    if message.chat.type in ["private", "bot"]:
        return True
    
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    check_status = await app.get_chat_member(chat_id, user_id)
    if check_status.status in ["administrator", "creator"]:
        return True
    
    return False


# Tag all command
@app.on_message(filters.command(["tagall", "all", "mentionall"]) & ~BANNED_USERS)
async def tag_all_users(client, message: Message):
    # Check if user is admin
    if not await is_admin(message):
        return await message.reply_text("🚫 This command is only for admins!")
    
    chat_id = message.chat.id
    
    # Check if a tagging process is already active in this chat
    if chat_id in active_tags and active_tags[chat_id]:
        return await message.reply_text("⚠️ A tagging process is already active in this chat. Please wait for it to finish.")
    
    # Extract custom message if provided
    custom_msg = ""
    if len(message.command) > 1:
        custom_msg = message.text.split(None, 1)[1]

    await message.reply_text("⏳ Starting to tag all members...")
    
    # Set active tag for this chat
    active_tags[chat_id] = True
    
    # Get all chat members
    tagged = 0
    async for member in app.get_chat_members(chat_id):
        # Skip bots and deleted accounts
        if member.user.is_bot or member.user.is_deleted:
            continue
        
        # Format the tag message
        tag_format = get_tag_formats(member.user.first_name, member.user.id)
        
        try:
            # Create message with the tag and the custom message
            if custom_msg:
                await app.send_message(
                    chat_id, 
                    f"{tag_format}\n{custom_msg}"
                )
            else:
                await app.send_message(chat_id, tag_format)
            
            tagged += 1
            
            # Sleep to avoid flood
            await asyncio.sleep(0.7)
            
            # Check if tagging process was cancelled
            if chat_id not in active_tags or not active_tags[chat_id]:
                break
                
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception as e:
            print(f"Error tagging user: {e}")
    
    # Reset active tag
    if chat_id in active_tags:
        active_tags[chat_id] = False
    
    await message.reply_text(f"✅ Tagging completed! Tagged {tagged} members.")


# Command to stop an active tagging process
@app.on_message(filters.command(["stoptag", "canceltag"]) & ~BANNED_USERS)
async def stop_tag_process(client, message: Message):
    chat_id = message.chat.id
    
    # Check if user is admin
    if not await is_admin(message):
        return await message.reply_text("🚫 This command is only for admins!")
    
    # Check if there's an active tagging process to stop
    if chat_id not in active_tags or not active_tags[chat_id]:
        return await message.reply_text("❌ There's no active tagging process to stop.")
    
    # Stop the process
    active_tags[chat_id] = False
    await message.reply_text("✅ Tagging process stopped successfully.")


# Tag specific number of members
@app.on_message(filters.command(["tagusers"]) & ~BANNED_USERS)
async def tag_specific_count(client, message: Message):
    # Check if user is admin
    if not await is_admin(message):
        return await message.reply_text("🚫 This command is only for admins!")
    
    chat_id = message.chat.id
    
    # Check if a tagging process is already active in this chat
    if chat_id in active_tags and active_tags[chat_id]:
        return await message.reply_text("⚠️ A tagging process is already active in this chat. Please wait for it to finish.")
    
    # Check command format
    if len(message.command) < 2:
        return await message.reply_text("❓ Please specify the number of members to tag.\n\nUsage: `/tagusers 10 [optional message]`")
    
    try:
        count = int(message.command[1])
        if count <= 0:
            return await message.reply_text("❌ Please provide a positive number.")
    except ValueError:
        return await message.reply_text("❌ Please provide a valid number.")
    
    # Extract custom message if provided
    custom_msg = ""
    if len(message.command) > 2:
        custom_msg = message.text.split(None, 2)[2]
    
    await message.reply_text(f"⏳ Starting to tag {count} members...")
    
    # Set active tag for this chat
    active_tags[chat_id] = True
    
    # Get and tag specified number of members
    tagged = 0
    async for member in app.get_chat_members(chat_id):
        # Stop if we've tagged enough members
        if tagged >= count:
            break
            
        # Skip bots and deleted accounts
        if member.user.is_bot or member.user.is_deleted:
            continue
        
        # Format the tag message
        tag_format = get_tag_formats(member.user.first_name, member.user.id)
        
        try:
            # Create message with the tag and the custom message
            if custom_msg:
                await app.send_message(
                    chat_id, 
                    f"{tag_format}\n{custom_msg}"
                )
            else:
                await app.send_message(chat_id, tag_format)
            
            tagged += 1
            
            # Sleep to avoid flood
            await asyncio.sleep(0.7)
            
            # Check if tagging process was cancelled
            if chat_id not in active_tags or not active_tags[chat_id]:
                break
                
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception as e:
            print(f"Error tagging user: {e}")
    
    # Reset active tag
    if chat_id in active_tags:
        active_tags[chat_id] = False
    
    await message.reply_text(f"✅ Tagging completed! Tagged {tagged} members.")


# Help command for tag module
@app.on_message(filters.command(["taghelp"]) & ~BANNED_USERS)
async def tag_help(client, message: Message):
    help_text = """
🏷️ **Tag Commands**

• `/tagall [message]` - Tag all members in the group with optional message
• `/tagusers 5 [message]` - Tag specific number of members
• `/stoptag` - Stop an active tagging process

🔹 **Note:** Only admins can use these commands
"""
    await message.reply_text(help_text) 