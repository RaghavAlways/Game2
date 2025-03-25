import uvloop
from typing import Union

uvloop.install()

from pyrogram import Client, errors
from pyrogram.enums import ChatMemberStatus, ParseMode
from pyrogram.types import Message, User
from pyrogram.errors import ChatAdminRequired, ChatWriteForbidden

import config
from ..logging import LOGGER


class Aviax(Client):
    def __init__(self):
        LOGGER(__name__).info(f"Starting Bot...")
        super().__init__(
            name="AviaxMusic",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            in_memory=True,
            parse_mode=ParseMode.HTML,
            max_concurrent_transmissions=7,
        )

    async def start(self):
        await super().start()
        self.id = self.me.id
        self.name = self.me.first_name + " " + (self.me.last_name or "")
        self.username = self.me.username
        self.mention = self.me.mention

        try:
            await self.send_message(
                chat_id=config.LOG_GROUP_ID,
                text=f"<b>🤖 Bot Started!</b>\n\n├ Name: {self.name}\n├ ID: {self.id}\n└ Username: @{self.username}",
            )
            LOGGER(__name__).info(f"Bot Started as {self.name}")
        except (ChatAdminRequired, ChatWriteForbidden):
            LOGGER(__name__).error(f"Bot doesn't have access to LOG_GROUP_ID!")
            exit()
        except Exception as e:
            LOGGER(__name__).error(f"Error in LOG_GROUP_ID: {e}")
            exit()

        a = await self.get_chat_member(config.LOG_GROUP_ID, self.id)
        if a.status != ChatMemberStatus.ADMINISTRATOR:
            LOGGER(__name__).error(
                "Please promote your bot as an admin in your log group/channel."
            )
            exit()
        LOGGER(__name__).info(f"Music Bot Started as {self.name}")

    async def stop(self):
        await super().stop()

    async def iter_messages(
        self,
        chat_id: Union[int, str],
        limit: int,
        offset: int = 0,
    ):
        return [
            m
            async for m in self.get_chat_history(
                chat_id, limit=limit, offset=offset
            )
        ]

    async def on_chat_member_updated(self, chat_member_updated):
        """Handle chat member updates"""
        try:
            # Check if this is about our bot
            if chat_member_updated.new_chat_member.user.id == self.id:
                # Check if bot was removed
                if chat_member_updated.new_chat_member.status == ChatMemberStatus.LEFT:
                    LOGGER(__name__).info(f"Bot was removed from {chat_member_updated.chat.title} ({chat_member_updated.chat.id})")
                    try:
                        # Get user info who removed the bot
                        user = chat_member_updated.from_user
                        user_info = ""
                        if user:
                            user_info = (
                                f"👤 <b>Removed By:</b> {user.mention}\n"
                                f"🆔 <b>User ID:</b> <code>{user.id}</code>\n"
                                f"📝 <b>Username:</b> @{user.username or 'None'}\n"
                                f"📱 <b>First Name:</b> {user.first_name}\n"
                                f"📱 <b>Last Name:</b> {user.last_name or 'None'}"
                            )
                        else:
                            user_info = "👤 <b>Removed By:</b> Unknown User"

                        # Get group info
                        group_info = (
                            f"📮 <b>Group:</b> {chat_member_updated.chat.title}\n"
                            f"🆔 <b>Group ID:</b> <code>{chat_member_updated.chat.id}</code>\n"
                            f"🔗 <b>Username:</b> @{chat_member_updated.chat.username or 'Private Group'}\n"
                            f"👥 <b>Total Members:</b> {await self.get_chat_members_count(chat_member_updated.chat.id)}"
                        )

                        log_message = (
                            "❌ <b>Bot Removed from Group</b>\n\n"
                            f"{group_info}\n\n"
                            f"{user_info}"
                        )

                        # Send log message
                        try:
                            await self.send_message(
                                chat_id=config.LOG_GROUP_ID,
                                text=log_message,
                                disable_web_page_preview=True
                            )
                            LOGGER(__name__).info(f"Successfully sent removal log message for group {chat_member_updated.chat.id}")
                        except Exception as e:
                            LOGGER(__name__).error(f"Failed to send removal log message: {str(e)}")
                            # Try alternative method if the first one fails
                            try:
                                await self.send_message(
                                    chat_id=config.LOG_GROUP_ID,
                                    text=f"❌ Bot was removed from group {chat_member_updated.chat.title} by {user.mention if user else 'Unknown User'}",
                                    disable_web_page_preview=True
                                )
                            except Exception as e2:
                                LOGGER(__name__).error(f"Failed to send alternative log message: {str(e2)}")

                    except Exception as e:
                        LOGGER(__name__).error(f"Error processing removal log: {str(e)}")
        except Exception as e:
            LOGGER(__name__).error(f"Error in chat member update handler: {str(e)}")

app = Aviax()
