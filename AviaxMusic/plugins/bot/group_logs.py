from pyrogram import filters
from pyrogram.types import Message
from pyrogram.errors import ChatWriteForbidden, ChatAdminRequired

import config
from AviaxMusic import app
from AviaxMusic.logging import LOGGER
from AviaxMusic.misc import SUDOERS
from AviaxMusic.utils.database import get_cmode
from config import LOGGER_ID

async def send_to_logger(message: str, alert_type: str = "INFO") -> None:
    """Send messages to the logger group"""
    if not LOGGER_ID:
        return
    
    try:
        await app.send_message(
            chat_id=LOGGER_ID,
            text=f"""
🔔 **{alert_type} Alert**

{message}
""",
            disable_web_page_preview=True
        )
    except (ChatWriteForbidden, ChatAdminRequired):
        print(f"Error: Bot doesn't have permission to write in LOGGER_ID ({LOGGER_ID})")
    except Exception as e:
        print(f"Error sending to logger: {str(e)}")

@app.on_message(filters.new_chat_members, group=2)
async def welcome_message(_, message: Message):
    chat_id = message.chat.id
    
    # Check if bot was added
    for member in message.new_chat_members:
        if member.id == app.id:
            try:
                # Get chat details
                chat = message.chat
                chat_title = chat.title
                chat_username = f"@{chat.username}" if chat.username else "Private Group"
                member_count = await app.get_chat_members_count(chat_id)
                
                # Get who added the bot
                added_by = message.from_user
                added_by_name = added_by.first_name
                added_by_mention = added_by.mention
                added_by_id = added_by.id
                
                # Send welcome message
                welcome_text = f"""
👋 Thanks for adding me to:
📝 **Group:** {chat_title}
🔗 **Group Link:** {chat_username}
👥 **Members:** {member_count}

Added by:
👤 **Name:** {added_by_name}
🆔 **ID:** `{added_by_id}`
"""
                try:
                    await message.reply_text(welcome_text)
                except ChatWriteForbidden:
                    print(f"Can't send welcome message in {chat_id}")
                
                # Log to logger group
                log_message = f"""
✅ **Bot Added to New Group**

📮 **Group Details:**
• Name: {chat_title}
• ID: `{chat_id}`
• Link: {chat_username}
• Members: {member_count}

👤 **Added By:**
• Name: {added_by_name}
• ID: `{added_by_id}`
• Mention: {added_by_mention}
"""
                await send_to_logger(log_message, "NEW GROUP")
                
            except Exception as e:
                print(f"Error in welcome_message: {str(e)}")
                await send_to_logger(
                    f"⚠️ Error in welcome_message for {chat_id}: {str(e)}",
                    "ERROR"
                )

@app.on_message(filters.left_chat_member, group=2)
async def on_left_chat_member(_, message: Message):
    chat_id = message.chat.id
    
    # Check if bot was removed
    if message.left_chat_member.id == app.id:
        try:
            # Get chat details
            chat = message.chat
            chat_title = chat.title
            chat_username = f"@{chat.username}" if chat.username else "Private Group"
            member_count = await app.get_chat_members_count(chat_id)
            
            # Get who removed the bot
            removed_by = message.from_user
            removed_by_name = removed_by.first_name if removed_by else "Unknown"
            removed_by_mention = removed_by.mention if removed_by else "Unknown"
            removed_by_id = removed_by.id if removed_by else "Unknown"
            
            # Log to logger group
            log_message = f"""
❌ **Bot Removed from Group**

📮 **Group Details:**
• Name: {chat_title}
• ID: `{chat_id}`
• Link: {chat_username}
• Members: {member_count}

👤 **Removed By:**
• Name: {removed_by_name}
• ID: `{removed_by_id}`
• Mention: {removed_by_mention}
"""
            await send_to_logger(log_message, "REMOVED")
            
        except Exception as e:
            print(f"Error in on_left_chat_member: {str(e)}")
            await send_to_logger(
                f"⚠️ Error in on_left_chat_member for {chat_id}: {str(e)}",
                "ERROR"
            )

@app.on_message(filters.command("logger") & SUDOERS)
async def logger_info(_, message: Message):
    """Command to check logger status and ID"""
    if not LOGGER_ID:
        await message.reply_text("❌ No LOGGER_ID configured in config.")
        return
        
    try:
        chat = await app.get_chat(LOGGER_ID)
        await message.reply_text(f"""
✅ **Logger Information**

📮 **Chat Details:**
• Title: {chat.title}
• ID: `{chat.id}`
• Type: {chat.type}
• Username: @{chat.username if chat.username else 'None'}

Bot's Permissions:
• Can Send Messages: ✅
""")
    except ChatAdminRequired:
        await message.reply_text(f"""
⚠️ **Logger Error**

The bot is not admin in the logger group (ID: `{LOGGER_ID}`).
Please add the bot as admin with permission to send messages.
""")
    except Exception as e:
        await message.reply_text(f"""
❌ **Logger Error**

Failed to get logger group info:
`{str(e)}`

Current LOGGER_ID: `{LOGGER_ID}`
""") 