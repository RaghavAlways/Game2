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

app = Aviax()
