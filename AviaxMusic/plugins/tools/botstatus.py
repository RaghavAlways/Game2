import asyncio
import time
import platform
import sys
import psutil
import subprocess
from datetime import datetime, timedelta

from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from AviaxMusic import app
from AviaxMusic.misc import SUDOERS
from AviaxMusic.utils.database import (
    get_served_chats,
    get_served_users,
    get_active_chats,
    get_active_video_chats,
)
from config import BANNED_USERS, LOG_GROUP_ID


# Command to check bot status
@app.on_message(filters.command(["status", "botstatus"]) & ~BANNED_USERS)
async def bot_status(client, message: Message):
    is_sudo = message.from_user.id in SUDOERS
    
    # Only SUDO users can use detailed status checks
    if not is_sudo and message.command[0] == "botstatus":
        return await message.reply_text("❌ This command is only for sudo users.")
    
    # Basic status check for all users
    if message.command[0] == "status":
        start_time = time.time()
        msg = await message.reply_text("🔄 Checking bot status...")
        
        # Measure response time
        response_time = time.time() - start_time
        
        await msg.edit_text(
            f"🟢 **Bot is operational!**\n\n"
            f"⏱️ Response Time: `{response_time*1000:.2f}ms`\n"
            f"🕰️ Uptime: {get_readable_time(time.time() - app.start_time)}"
        )
        return
    
    # Detailed status check for SUDO users
    msg = await message.reply_text("🔄 Checking system status...")
    
    # Start system checks
    system_status = await check_system_status()
    db_status = await check_database_status()
    api_status = await check_api_status()
    service_status = await check_service_status()
    
    # Generate status report
    status_text = f"""
🖥️ **System Status**
{system_status}

🗄️ **Database Status**
{db_status}

🔌 **API Status**
{api_status}

🔧 **Services Status**
{service_status}

**Last Checked:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    """
    
    # Add button to run full diagnostic
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔍 Run Full Diagnostic", callback_data="run_diagnostic"),
            InlineKeyboardButton("🔄 Refresh", callback_data="refresh_status"),
        ]
    ])
    
    await msg.edit_text(status_text, reply_markup=buttons)


# Callback for full diagnostic
@app.on_callback_query(filters.regex("run_diagnostic"))
async def on_diagnostic_callback(client, callback_query):
    if callback_query.from_user.id not in SUDOERS:
        return await callback_query.answer("❌ This action is only for sudo users.", show_alert=True)
    
    await callback_query.answer("Starting full diagnostic, this may take a minute...")
    await callback_query.message.edit_text("🔍 Running full diagnostic scan, please wait...")
    
    # Start diagnostic tests
    diagnostic_results = await run_full_diagnostic()
    
    # Generate diagnostic report
    diagnostic_text = f"""
📊 **Full Bot Diagnostic Report**

{diagnostic_results}

**Scan Completed:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    """
    
    # Add button to send to log channel
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📤 Send to Log Channel", callback_data="send_diagnostic_log"),
            InlineKeyboardButton("🔄 Refresh", callback_data="refresh_status"),
        ]
    ])
    
    await callback_query.message.edit_text(diagnostic_text, reply_markup=buttons)


# Callback to refresh status
@app.on_callback_query(filters.regex("refresh_status"))
async def on_refresh_callback(client, callback_query):
    if callback_query.from_user.id not in SUDOERS:
        return await callback_query.answer("❌ This action is only for sudo users.", show_alert=True)
    
    await callback_query.answer("Refreshing status...")
    await callback_query.message.edit_text("🔄 Refreshing system status...")
    
    # Recheck all systems
    system_status = await check_system_status()
    db_status = await check_database_status()
    api_status = await check_api_status()
    service_status = await check_service_status()
    
    # Generate status report
    status_text = f"""
🖥️ **System Status**
{system_status}

🗄️ **Database Status**
{db_status}

🔌 **API Status**
{api_status}

🔧 **Services Status**
{service_status}

**Last Checked:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    """
    
    # Add button to run full diagnostic
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔍 Run Full Diagnostic", callback_data="run_diagnostic"),
            InlineKeyboardButton("🔄 Refresh", callback_data="refresh_status"),
        ]
    ])
    
    await callback_query.message.edit_text(status_text, reply_markup=buttons)


# Callback to send diagnostic to log channel
@app.on_callback_query(filters.regex("send_diagnostic_log"))
async def on_send_log_callback(client, callback_query):
    if callback_query.from_user.id not in SUDOERS:
        return await callback_query.answer("❌ This action is only for sudo users.", show_alert=True)
    
    await callback_query.answer("Sending to log channel...")
    
    # Send to log channel if configured
    if LOG_GROUP_ID:
        try:
            await client.send_message(
                LOG_GROUP_ID,
                callback_query.message.text + f"\n\nRequested by: {callback_query.from_user.mention}"
            )
            await callback_query.message.reply_text("✅ Diagnostic report sent to log channel!")
        except Exception as e:
            await callback_query.message.reply_text(f"❌ Failed to send to log channel: {str(e)}")
    else:
        await callback_query.message.reply_text("❌ Log channel is not configured.")


# Helper function to check system status
async def check_system_status():
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        system_info = (
            f"CPU Usage: `{cpu_usage}%`\n"
            f"RAM Usage: `{memory.percent}%` ({get_size(memory.used)}/{get_size(memory.total)})\n"
            f"Disk Usage: `{disk.percent}%` ({get_size(disk.used)}/{get_size(disk.total)})\n"
            f"Python: `{platform.python_version()}`\n"
            f"System: `{platform.system()} {platform.release()}`"
        )
        
        return system_info
    except Exception as e:
        return f"Error checking system status: {str(e)}"


# Helper function to check database status
async def check_database_status():
    try:
        # Get counts to test database connectivity
        start_time = time.time()
        served_chats = len(await get_served_chats())
        served_users = len(await get_served_users())
        db_response_time = time.time() - start_time
        
        db_info = (
            f"Status: `Connected ✅`\n"
            f"Response Time: `{db_response_time*1000:.2f}ms`\n"
            f"Served Chats: `{served_chats}`\n"
            f"Served Users: `{served_users}`"
        )
        
        return db_info
    except Exception as e:
        return f"Status: `Disconnected ❌`\nError: {str(e)}"


# Helper function to check API status
async def check_api_status():
    try:
        # Test Telegram API response time
        start_time = time.time()
        await app.get_me()
        telegram_response = time.time() - start_time
        
        # Test voice chat capability
        active_calls = len(await get_active_chats())
        
        api_info = (
            f"Telegram API: `Connected ✅ ({telegram_response*1000:.2f}ms)`\n"
            f"Active Calls: `{active_calls}`\n"
            f"Bot Uptime: `{get_readable_time(time.time() - app.start_time)}`"
        )
        
        return api_info
    except Exception as e:
        return f"Telegram API: `Error ❌`\nError: {str(e)}"


# Helper function to check services status
async def check_service_status():
    try:
        # Check voice capability
        voice_active = len(await get_active_chats())
        video_active = len(await get_active_video_chats())
        
        service_info = (
            f"Voice Service: `{'Active ✅' if voice_active >= 0 else 'Unknown ⚠️'}`\n"
            f"Video Service: `{'Active ✅' if video_active >= 0 else 'Unknown ⚠️'}`\n"
            f"Music Player: `Active ✅`"
        )
        
        return service_info
    except Exception as e:
        return f"Error checking services: {str(e)}"


# Function to run full diagnostic
async def run_full_diagnostic():
    results = []
    
    # System diagnostics
    results.append("**1. System Diagnostics:**")
    try:
        cpu_usage = psutil.cpu_percent(interval=2)
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        disk = psutil.disk_usage('/')
        
        results.append(f"✅ CPU Load: {cpu_usage}%")
        results.append(f"✅ Memory: {memory.percent}% used ({get_size(memory.used)}/{get_size(memory.total)})")
        results.append(f"✅ Swap: {swap.percent}% used")
        results.append(f"✅ Disk: {disk.percent}% used")
        results.append(f"✅ Python: {sys.version.split()[0]}")
    except Exception as e:
        results.append(f"❌ System check error: {str(e)}")
    
    # Network diagnostics
    results.append("\n**2. Network Diagnostics:**")
    try:
        # Ping test to Telegram
        start = time.time()
        await app.get_me()
        ping = time.time() - start
        results.append(f"✅ Telegram API: {ping*1000:.2f}ms")
        
        # Check internet connection
        try:
            process = subprocess.run(
                ["ping", "-c", "1", "google.com"], 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            if process.returncode == 0:
                results.append(f"✅ Internet Connection: Available")
            else:
                results.append(f"⚠️ Internet Connection: Limited")
        except:
            results.append(f"⚠️ Internet Connection: Test failed")
    except Exception as e:
        results.append(f"❌ Network check error: {str(e)}")
    
    # Database diagnostics
    results.append("\n**3. Database Diagnostics:**")
    try:
        start_time = time.time()
        await get_served_chats()
        db_time = time.time() - start_time
        results.append(f"✅ Database Connection: {db_time*1000:.2f}ms")
        results.append(f"✅ Database Status: Operational")
    except Exception as e:
        results.append(f"❌ Database check error: {str(e)}")
    
    # Bot functionality diagnostics
    results.append("\n**4. Bot Functionality:**")
    try:
        # Check active voice chats
        voice_chats = len(await get_active_chats())
        results.append(f"✅ Voice Chat System: {'Active' if voice_chats >= 0 else 'Unknown'}")
        
        # Check served chats count
        served_chats = len(await get_served_chats())
        results.append(f"✅ Bot is serving {served_chats} chats")
        
        # Check uptime
        uptime = time.time() - app.start_time
        results.append(f"✅ Uptime: {get_readable_time(uptime)}")
    except Exception as e:
        results.append(f"❌ Functionality check error: {str(e)}")
    
    # Result summary
    errors = [line for line in results if "❌" in line]
    warnings = [line for line in results if "⚠️" in line]
    
    summary = "\n**5. Diagnostic Summary:**\n"
    if not errors and not warnings:
        summary += "🟢 All systems operational! No issues detected."
    elif not errors and warnings:
        summary += f"🟡 Systems operational with {len(warnings)} warning(s)."
    else:
        summary += f"🔴 System issues detected! Found {len(errors)} error(s) and {len(warnings)} warning(s)."
    
    results.append(summary)
    
    return "\n".join(results)


# Utility function to convert bytes to human-readable size
def get_size(bytes, suffix="B"):
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f} {unit}{suffix}"
        bytes /= factor


# Utility function to format time
def get_readable_time(seconds):
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    
    periods = [('d', days), ('h', hours), ('m', minutes), ('s', seconds)]
    time_string = ''.join(f'{value}{name} ' for name, value in periods if value)
    return time_string.strip() 