import asyncio
import importlib
import time
import traceback

from pyrogram import idle
from pytgcalls.exceptions import NoActiveGroupCall

import config
from AviaxMusic import LOGGER, app, userbot
from AviaxMusic.core.call import Aviax
from AviaxMusic.misc import sudo
from AviaxMusic.plugins import ALL_MODULES
from AviaxMusic.utils.database import get_banned_users, get_gbanned
from config import BANNED_USERS

# Import background tasks from our new modules
from AviaxMusic.utils.thumbnails import cleanup_old_thumbnails, optimize_memory_usage
from AviaxMusic.plugins.bot.game_recovery import detect_and_fix_stuck_games


async def background_task_wrapper(task_func, task_name, retry_interval=300):
    """
    Wrapper that restarts a background task if it crashes
    
    Args:
        task_func: The async function to run as a background task
        task_name: Name of the task for logging
        retry_interval: How long to wait before restarting the task after a crash (in seconds)
    """
    while True:
        try:
            LOGGER("BackgroundTasks").info(f"Starting background task: {task_name}")
            await task_func()
        except Exception as e:
            LOGGER("BackgroundTasks").error(
                f"Error in background task {task_name}: {str(e)}\n{traceback.format_exc()}"
            )
            LOGGER("BackgroundTasks").info(
                f"Restarting {task_name} in {retry_interval} seconds..."
            )
            await asyncio.sleep(retry_interval)


async def init():
    if (
        not config.STRING1
        and not config.STRING2
        and not config.STRING3
        and not config.STRING4
        and not config.STRING5
    ):
        LOGGER(__name__).error("Assistant client variables not defined, exiting...")
        exit()
    await sudo()
    try:
        users = await get_gbanned()
        for user_id in users:
            BANNED_USERS.add(user_id)
        users = await get_banned_users()
        for user_id in users:
            BANNED_USERS.add(user_id)
    except:
        pass
    await app.start()
    for all_module in ALL_MODULES:
        importlib.import_module("AviaxMusic.plugins" + all_module)
    LOGGER("AviaxMusic.plugins").info("Successfully Imported Modules...")
    await userbot.start()
    await Aviax.start()
    try:
        await Aviax.stream_call("https://te.legra.ph/file/29f784eb49d230ab62e9e.mp4")
    except NoActiveGroupCall:
        LOGGER("AviaxMusic").error(
            "Please turn on the videochat of your log group\channel.\n\nStopping Bot..."
        )
        exit()
    except:
        pass
    await Aviax.decorators()
    
    # Start background tasks with wrapper for error handling and auto-restart
    LOGGER("AviaxMusic").info("Starting background maintenance tasks...")
    asyncio.create_task(background_task_wrapper(cleanup_old_thumbnails, "Thumbnail Cleanup"))
    asyncio.create_task(background_task_wrapper(optimize_memory_usage, "Memory Optimization"))
    asyncio.create_task(background_task_wrapper(detect_and_fix_stuck_games, "Game Recovery"))
    
    LOGGER("AviaxMusic").info(
        "\x41\x76\x69\x61\x78\x20\x4d\x75\x73\x69\x63\x20\x53\x74\x61\x72\x74\x65\x64\x20\x53\x75\x63\x63\x65\x73\x73\x66\x75\x6c\x6c\x79\x2e\x0a\x0a\x44\x6f\x6e\x27\x74\x20\x66\x6f\x72\x67\x65\x74\x20\x74\x6f\x20\x76\x69\x73\x69\x74\x20\x40\x41\x76\x69\x61\x78\x4f\x66\x66\x69\x63\x69\x61\x6c"
    )
    await idle()
    await app.stop()
    await userbot.stop()
    LOGGER("AviaxMusic").info("Stopping Aviax Music Bot...")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init())
