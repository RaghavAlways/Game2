from pyrogram import filters
from pyrogram.types import Message
from pyrogram.errors import ChatWriteForbidden, ChatAdminRequired, UserNotParticipant, FloodWait, PeerIdInvalid

import asyncio
from AviaxMusic import app
from AviaxMusic.misc import SUDOERS
from AviaxMusic.utils.database import get_cmode
from config import LOG_GROUP_ID

async def send_to_logger(message: str, alert_type: str = "INFO") -> None:
    """Send messages to the logger group"""
    if not LOG_GROUP_ID:
        return
    
    try:
        # Fix: Escape HTML characters that might cause rendering issues
        message = message.replace("<", "&lt;").replace(">", "&gt;")
        
        # Simplify the message format to avoid HTML parsing issues
        text = f"""🔔 {alert_type} ALERT

{message}"""
        
        await app.send_message(
            chat_id=int(LOG_GROUP_ID),
            text=text,
            disable_web_page_preview=True
        )
        print(f"Successfully sent log message to LOG_GROUP_ID: {LOG_GROUP_ID}")
    except (ChatWriteForbidden, ChatAdminRequired):
        print(f"Error: Bot doesn't have permission to write in LOG_GROUP_ID ({LOG_GROUP_ID})")
    except FloodWait as e:
        print(f"FloodWait: Sleeping for {e.x} seconds")
        await asyncio.sleep(e.x)
        return await send_to_logger(message, alert_type)
    except PeerIdInvalid:
        print(f"Error: Invalid LOG_GROUP_ID ({LOG_GROUP_ID}). Make sure the bot is in this group.")
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
                chat_title = chat.title.replace("<", "&lt;").replace(">", "&gt;")  # Escape HTML
                chat_username = f"@{chat.username}" if chat.username else "Private Group"
                
                try:
                    member_count = await app.get_chat_members_count(chat_id)
                except Exception:
                    member_count = "Unknown"
                
                # Get who added the bot
                added_by = message.from_user
                if added_by:
                    added_by_name = added_by.first_name.replace("<", "&lt;").replace(">", "&gt;")  # Escape HTML
                    added_by_mention = f"@{added_by.username}" if added_by.username else added_by_name
                    added_by_id = added_by.id
                else:
                    added_by_name = "Unknown"
                    added_by_mention = "Unknown"
                    added_by_id = "Unknown"
                
                # Send welcome message
                welcome_text = f"""👋 Thanks for adding me!

• Group: {chat_title}
• Link: {chat_username}
• Members: {member_count}

✅ Use /help to see available commands"""
                try:
                    await message.reply_text(welcome_text)
                except ChatWriteForbidden:
                    print(f"Can't send welcome message in {chat_id}")
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                except Exception as e:
                    print(f"Error sending welcome: {str(e)}")
                
                # Log to logger group
                log_message = f"""🤖 Bot Added to New Group

• Group: {chat_title}
• ID: {chat_id}
• Link: {chat_username}
• Members: {member_count}

👤 Added by: {added_by_mention} (ID: {added_by_id})"""
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
    if message.left_chat_member and message.left_chat_member.id == app.id:
        try:
            # Get chat details
            chat = message.chat
            chat_title = chat.title.replace("<", "&lt;").replace(">", "&gt;")  # Escape HTML
            chat_username = f"@{chat.username}" if chat.username else "Private Group"
            
            try:
                member_count = await app.get_chat_members_count(chat_id)
            except (UserNotParticipant, PeerIdInvalid):
                member_count = "Unknown (Bot removed)"
            except Exception:
                member_count = "Unknown"
            
            # Get who removed the bot
            removed_by = message.from_user
            if removed_by:
                removed_by_name = removed_by.first_name.replace("<", "&lt;").replace(">", "&gt;")  # Escape HTML
                removed_by_mention = f"@{removed_by.username}" if removed_by.username else removed_by_name
                removed_by_id = removed_by.id
            else:
                removed_by_name = "Unknown"
                removed_by_mention = "Unknown"
                removed_by_id = "Unknown"
            
            # Log to logger group
            log_message = f"""🤖 Bot Removed from Group

• Group: {chat_title}
• ID: {chat_id}
• Link: {chat_username}
• Members: {member_count}

👤 Removed by: {removed_by_mention} (ID: {removed_by_id})"""
            await send_to_logger(log_message, "REMOVED")
            
        except Exception as e:
            print(f"Error in on_left_chat_member: {str(e)}")
            try:
                await send_to_logger(
                    f"⚠️ Error in on_left_chat_member for {chat_id}: {str(e)}",
                    "ERROR"
                )
            except Exception as e:
                print(f"Failed to send error log: {str(e)}")

@app.on_message(filters.command("logger") & SUDOERS)
async def logger_info(_, message: Message):
    """Command to check logger status and ID"""
    if not LOG_GROUP_ID:
        await message.reply_text("❌ No LOG_GROUP_ID configured in config.")
        return
        
    try:
        chat_id = int(LOG_GROUP_ID)
        chat = await app.get_chat(chat_id)
        
        # Check if bot can send messages
        try:
            permissions = await app.get_chat_member(chat_id, app.id)
            can_send = not permissions.permissions or permissions.permissions.can_send_messages
        except Exception:
            can_send = "Unknown"
        
        await message.reply_text(f"""
<b>✅ Logger Information</b>

<b>Chat Details:</b>
• <b>Title:</b> {chat.title}
• <b>ID:</b> <code>{chat.id}</code>
• <b>Type:</b> {chat.type}
• <b>Username:</b> @{chat.username if chat.username else 'None'}

<b>Bot's Permissions:</b>
• <b>Can Send Messages:</b> {"✅" if can_send is True else "❌" if can_send is False else "⚠️ Unknown"}
""", parse_mode="HTML")
    except PeerIdInvalid:
        await message.reply_text(f"""
<b>⚠️ Logger Error</b>

Invalid LOG_GROUP_ID: <code>{LOG_GROUP_ID}</code>.
The bot is not in this group. Add the bot to the group and try again.
""", parse_mode="HTML")
    except ChatAdminRequired:
        await message.reply_text(f"""
<b>⚠️ Logger Error</b>

The bot is not admin in the logger group (ID: <code>{LOG_GROUP_ID}</code>).
Please add the bot as admin with permission to send messages.
""", parse_mode="HTML")
    except Exception as e:
        await message.reply_text(f"""
<b>❌ Logger Error</b>

Failed to get logger group info:
<code>{str(e)}</code>

Current LOG_GROUP_ID: <code>{LOG_GROUP_ID}</code>
""", parse_mode="HTML") 