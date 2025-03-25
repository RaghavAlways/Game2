from pyrogram.enums import ParseMode
from typing import Union
from pyrogram.types import Message

from AviaxMusic import app
from AviaxMusic.utils.database import is_on_off
from config import LOG_GROUP_ID


async def play_logs(message, streamtype):
    if await is_on_off(2):
        logger_text = f"""
<b>{app.mention} ᴘʟᴀʏ ʟᴏɢ</b>

<b>ᴄʜᴀᴛ ɪᴅ :</b> <code>{message.chat.id}</code>
<b>ᴄʜᴀᴛ ɴᴀᴍᴇ :</b> {message.chat.title}
<b>ᴄʜᴀᴛ ᴜsᴇʀɴᴀᴍᴇ :</b> @{message.chat.username}

<b>ᴜsᴇʀ ɪᴅ :</b> <code>{message.from_user.id}</code>
<b>ɴᴀᴍᴇ :</b> {message.from_user.mention}
<b>ᴜsᴇʀɴᴀᴍᴇ :</b> @{message.from_user.username}

<b>ǫᴜᴇʀʏ :</b> {message.text.split(None, 1)[1]}
<b>sᴛʀᴇᴀᴍᴛʏᴘᴇ :</b> {streamtype}"""
        if message.chat.id != LOG_GROUP_ID:
            try:
                await app.send_message(
                    chat_id=LOG_GROUP_ID,
                    text=logger_text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                )
            except:
                pass
        return

async def group_logger(message: Message):
    try:
        if message.chat.type in ["group", "supergroup"]:
            chat_title = message.chat.title
            chat_id = message.chat.id
            chat_username = message.chat.username or "Private Group"
            
            # Get member count
            try:
                member_count = await app.get_chat_members_count(chat_id)
            except:
                member_count = "Unable to get member count"
            
            # Get who added the bot
            try:
                added_by = message.from_user
                if added_by:
                    added_by_text = f"Added by: {added_by.mention} (`{added_by.id}`)"
                else:
                    added_by_text = "Added by: Unknown"
            except:
                added_by_text = "Added by: Unknown"
            
            # Create the log message
            log_message = (
                "🤖 <b>Bot Added to New Group!</b>\n\n"
                f"📮 <b>Group:</b> {chat_title}\n"
                f"🆔 <b>Group ID:</b> <code>{chat_id}</code>\n"
                f"🔗 <b>Username:</b> @{chat_username}\n"
                f"👥 <b>Total Members:</b> {member_count}\n"
                f"👤 <b>{added_by_text}</b>"
            )
            
            try:
                # Send log message to LOG_GROUP_ID
                await app.send_message(
                    chat_id=LOG_GROUP_ID,
                    text=log_message,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
            except Exception as e:
                print(f"Failed to send log message: {str(e)}")
                
    except Exception as e:
        print(f"Error in group logger: {str(e)}")
