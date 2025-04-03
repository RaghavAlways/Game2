import asyncio
from datetime import datetime
from typing import Dict, List, Union

from pyrogram import filters
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from AviaxMusic import app
from AviaxMusic.misc import SUDOERS
from AviaxMusic.utils.database import get_served_chats, get_served_users
from config import BANNED_USERS, SUPPORT_CHANNEL


# Dictionary to track which users have seen notifications
notification_seen = {}

# Dictionary to store notification messages
notifications = []


# Command to send a notification to all chats
@app.on_message(filters.command(["notify", "notification"]) & SUDOERS)
async def send_notification_command(_, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "**Usage:**\n/notify [message]"
        )
    
    # Get notification text
    notification = " ".join(message.command[1:])
    
    # Create notification with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    notification_id = len(notifications) + 1
    notification_data = {
        "id": notification_id,
        "text": notification,
        "timestamp": timestamp,
        "sender": message.from_user.id,
        "sender_name": message.from_user.first_name
    }
    
    # Add to notifications list
    notifications.append(notification_data)
    
    # Ask for confirmation
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Send to All Chats", callback_data=f"confirm_notify_{notification_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_notify"),
        ]
    ])
    
    await message.reply_text(
        f"**Notification Preview:**\n\n"
        f"📢 **BOT NOTIFICATION #{notification_id}**\n\n"
        f"{notification}\n\n"
        f"⏰ {timestamp}",
        reply_markup=buttons
    )


# Callback for notification confirmation
@app.on_callback_query(filters.regex(r"^confirm_notify_(\d+)$"))
async def confirm_notification(_, query):
    notification_id = int(query.data.split("_")[2])
    
    # Find notification in the list
    notification_data = None
    for notif in notifications:
        if notif["id"] == notification_id:
            notification_data = notif
            break
    
    if not notification_data:
        return await query.answer("Notification not found.", show_alert=True)
    
    await query.message.edit_text("⏳ **Sending notification to all chats...**")
    
    # Get all chats
    chats = await get_served_chats()
    
    notification_text = (
        f"📢 **BOT NOTIFICATION #{notification_data['id']}**\n\n"
        f"{notification_data['text']}\n\n"
        f"⏰ {notification_data['timestamp']}"
    )
    
    # Create buttons for notification
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📢 Updates Channel", url=f"{SUPPORT_CHANNEL}"),
        ]
    ])
    
    # Track statistics
    sent_count = 0
    failed_count = 0
    
    # Send to all chats
    for chat in chats:
        chat_id = chat["chat_id"]
        try:
            await app.send_message(
                chat_id=chat_id,
                text=notification_text,
                reply_markup=buttons
            )
            sent_count += 1
            await asyncio.sleep(0.1)  # Prevent flood
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await app.send_message(
                chat_id=chat_id,
                text=notification_text,
                reply_markup=buttons
            )
            sent_count += 1
        except Exception:
            failed_count += 1
            continue
    
    await query.message.edit_text(
        f"✅ **Notification sent successfully!**\n\n"
        f"• **Sent to:** {sent_count} chats\n"
        f"• **Failed:** {failed_count} chats"
    )


@app.on_callback_query(filters.regex("^cancel_notify$"))
async def cancel_notification(_, query):
    await query.message.edit_text("❌ **Notification canceled.**")


# Command to view recent notifications
@app.on_message(filters.command("announcements") & ~BANNED_USERS)
async def view_notifications_command(_, message: Message):
    if not notifications:
        return await message.reply_text("No notifications available yet.")
    
    # Display last 5 notifications
    recent_notifs = notifications[-5:]
    
    text = "📢 **Recent Announcements**\n\n"
    
    for i, notif in enumerate(reversed(recent_notifs), 1):
        text += f"**{i}. Announcement #{notif['id']}**\n"
        text += f"{notif['text'][:100]}{'...' if len(notif['text']) > 100 else ''}\n"
        text += f"⏰ {notif['timestamp']}\n\n"
    
    # Mark as seen for this user
    user_id = message.from_user.id
    notification_seen[user_id] = len(notifications)
    
    await message.reply_text(text)


# Notification check on start command
@app.on_message(filters.command("start") & filters.group & ~BANNED_USERS)
async def notify_on_start(_, message: Message):
    if not notifications:
        return
    
    user_id = message.from_user.id
    
    # Check if user hasn't seen latest notifications
    latest_notification_id = len(notifications)
    last_seen = notification_seen.get(user_id, 0)
    
    if latest_notification_id > last_seen:
        # User has unseen notifications
        unseen_count = latest_notification_id - last_seen
        
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(f"📢 View {unseen_count} Announcements", callback_data="view_announcements"),
            ]
        ])
        
        await message.reply_text(
            f"**You have {unseen_count} unread bot announcement{'s' if unseen_count > 1 else ''}!**",
            reply_markup=buttons
        )


@app.on_callback_query(filters.regex("^view_announcements$"))
async def view_announcements_callback(_, query):
    user_id = query.from_user.id
    
    # Get user's last seen notification
    last_seen = notification_seen.get(user_id, 0)
    
    # Get unseen notifications
    unseen_notifs = notifications[last_seen:]
    
    if not unseen_notifs:
        return await query.answer("No new announcements to show.", show_alert=True)
    
    text = "📢 **Unread Announcements**\n\n"
    
    for notif in unseen_notifs:
        text += f"**Announcement #{notif['id']}**\n"
        text += f"{notif['text']}\n"
        text += f"⏰ {notif['timestamp']}\n\n"
    
    # Mark as seen
    notification_seen[user_id] = len(notifications)
    
    # Edit message with notifications
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Mark as Read", callback_data="mark_read"),
        ]
    ])
    
    await query.message.edit_text(text, reply_markup=buttons)


@app.on_callback_query(filters.regex("^mark_read$"))
async def mark_read_callback(_, query):
    await query.message.edit_text("✅ **All announcements marked as read.**") 