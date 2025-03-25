from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from AviaxMusic import app
from config import BANNED_USERS
import logging

# Import the game-related modules
try:
    from AviaxMusic.plugins.bot.wordle import active_games, create_game_message, start_wordle
except ImportError:
    active_games = {}
    logging.warning("Could not import Wordle game modules")

@app.on_callback_query(filters.regex("game_error_recovery") & ~BANNED_USERS)
async def game_recovery_handler(client, query: CallbackQuery):
    """Handle recovery from game errors"""
    try:
        chat_id = query.message.chat.id
        user_id = query.from_user.id
        
        # Check if user is admin or game creator
        is_admin = False
        try:
            member = await app.get_chat_member(chat_id, user_id)
            is_admin = member.status in ("creator", "administrator")
        except Exception:
            pass
            
        # If there's an active game, check if user is the creator
        is_creator = False
        if chat_id in active_games and active_games[chat_id].get("players"):
            # First player is usually the creator
            players = list(active_games[chat_id]["players"].keys())
            if players and players[0] == user_id:
                is_creator = True
        
        if not (is_admin or is_creator):
            await query.answer("Only admins or game creators can reset the game.", show_alert=True)
            return
            
        # Clear any existing game state
        if chat_id in active_games:
            del active_games[chat_id]
            
        await query.message.reply_text(
            "🎮 **Game Reset Successful**\n\n"
            "The game state has been reset due to an error. "
            "You can start a new game with /wordle",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Start New Game", callback_data="start_wordle")]
            ])
        )
        await query.answer("Game reset successful!")
        
    except Exception as e:
        print(f"Error in game recovery: {e}")
        await query.answer("Could not reset game. Try /wordle command instead.", show_alert=True)

@app.on_message(filters.command("fixgame") & filters.group)
async def fix_game_command(client, message: Message):
    """Command to fix stuck games"""
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Check if user is admin
        try:
            member = await app.get_chat_member(chat_id, user_id)
            is_admin = member.status in ("creator", "administrator")
            if not is_admin:
                await message.reply_text("❌ Only admins can use this command.")
                return
        except Exception:
            await message.reply_text("❌ Failed to verify admin status.")
            return
            
        # Check if there's an active game
        if chat_id not in active_games:
            await message.reply_text(
                "No active game found in this chat. Start a new game with /wordle"
            )
            return
            
        # Get current game info for reporting
        word = active_games[chat_id].get("word", "unknown")
        players_count = len(active_games[chat_id].get("players", {}))
        attempts = len(active_games[chat_id].get("attempts", []))
        
        # Reset the game
        del active_games[chat_id]
        
        await message.reply_text(
            f"🎮 **Game Reset Successful**\n\n"
            f"📊 **Game Stats Before Reset:**\n"
            f"• Word: `{word}`\n"
            f"• Players: {players_count}\n"
            f"• Attempts: {attempts}\n\n"
            f"The game has been reset. You can start a new one with /wordle",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Start New Game", callback_data="start_wordle")]
            ])
        )
        
    except Exception as e:
        print(f"Error in fix_game command: {e}")
        await message.reply_text(
            f"❌ Error occurred while resetting the game: {str(e)}\n"
            f"Try again or contact the bot developer."
        )

# Error detection for ongoing games
async def detect_and_fix_stuck_games():
    """Periodically check for and fix stuck games"""
    import time
    import asyncio
    
    while True:
        try:
            current_time = time.time()
            chats_to_reset = []
            
            # Check all active games
            for chat_id, game_data in active_games.items():
                # Check if game has been inactive for too long (3 hours)
                if "last_activity" in game_data:
                    if current_time - game_data["last_activity"] > 10800:  # 3 hours
                        chats_to_reset.append(chat_id)
                # Games without last_activity are likely stuck
                else:
                    # Add last_activity timestamp
                    active_games[chat_id]["last_activity"] = current_time
            
            # Reset stuck games
            for chat_id in chats_to_reset:
                try:
                    # Try to notify the chat
                    await app.send_message(
                        chat_id,
                        "🎮 **Inactive Game Detected**\n\n"
                        "A Wordle game in this chat has been inactive for 3 hours and was automatically reset.\n"
                        "Start a new game with /wordle if you want to play.",
                    )
                    # Remove the game
                    if chat_id in active_games:
                        del active_games[chat_id]
                        print(f"Auto-reset inactive game in chat {chat_id}")
                except Exception as e:
                    print(f"Error notifying chat {chat_id} about game reset: {e}")
                    # Still remove the game even if notification fails
                    if chat_id in active_games:
                        del active_games[chat_id]
            
        except Exception as e:
            print(f"Error in game monitoring: {e}")
            
        # Run check every 30 minutes
        await asyncio.sleep(1800) 