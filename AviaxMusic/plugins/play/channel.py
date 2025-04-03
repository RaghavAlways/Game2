from pyrogram import filters
from pyrogram.enums import ChatMembersFilter, ChatMemberStatus, ChatType
from pyrogram.types import Message

from AviaxMusic import app
from AviaxMusic.utils.database import set_cmode
from AviaxMusic.utils.decorators.admins import AdminActual
from config import BANNED_USERS


@app.on_message(filters.command(["channelplay"]) & filters.group & ~BANNED_USERS)
@AdminActual
async def playmode_(client, message: Message, _):
    if len(message.command) < 2:
        # Display usage info when no arguments are provided
        return await message.reply_text(f"**Usage:**\n/channelplay linked - Play music in linked channel\n/channelplay [channel_id|channel_username] - Play music in specific channel\n/channelplay disable - Disable channel playback")
    
    query = message.text.split(None, 2)[1].lower().strip()
    
    if (str(query)).lower() == "disable":
        await set_cmode(message.chat.id, None)
        return await message.reply_text(_["cplay_7"])
    
    elif str(query) == "linked":
        chat = await app.get_chat(message.chat.id)
        if chat.linked_chat:
            chat_id = chat.linked_chat.id
            await set_cmode(message.chat.id, chat_id)
            return await message.reply_text(
                _["cplay_3"].format(chat.linked_chat.title, chat.linked_chat.id)
            )
        else:
            return await message.reply_text(_["cplay_2"])
    else:
        try:
            # Enhanced error handling for channel identification
            # Handle channel usernames that start with @ symbol
            if query.startswith("@"):
                channel_username = query
                try:
                    chat = await app.get_chat(channel_username)
                except Exception:
                    return await message.reply_text(f"Failed to find channel. Make sure the bot is added to the channel as admin.")
            else:
                # Try to use as numeric channel ID
                try:
                    chat_id = int(query)
                    chat = await app.get_chat(chat_id)
                except ValueError:
                    # If not a valid integer, try as channel username without @
                    try:
                        chat = await app.get_chat(query)
                    except Exception:
                        return await message.reply_text(f"Failed to find channel. Make sure the channel ID or username is correct and the bot is added to the channel as admin.")
                except Exception:
                    return await message.reply_text(_["cplay_4"])
        except Exception as e:
            return await message.reply_text(f"Error: {str(e)}\n\nMake sure the bot is added to your channel as admin.")
            
        if chat.type != ChatType.CHANNEL:
            return await message.reply_text(_["cplay_5"])
        
        try:
            channel_owner = None
            async for user in app.get_chat_members(
                chat.id, filter=ChatMembersFilter.ADMINISTRATORS
            ):
                if user.status == ChatMemberStatus.OWNER:
                    channel_owner = user
                    cusn = user.user.username or "No Username"
                    crid = user.user.id
                    break
                    
            if not channel_owner:
                return await message.reply_text("Could not find channel owner. Make sure the bot has correct permissions.")
        except Exception as e:
            return await message.reply_text(f"Error getting channel admins: {str(e)}\n\nMake sure the bot is added to your channel as admin.")
        
        if crid != message.from_user.id:
            return await message.reply_text(_["cplay_6"].format(chat.title, cusn))
        
        await set_cmode(message.chat.id, chat.id)
        return await message.reply_text(_["cplay_3"].format(chat.title, chat.id))
