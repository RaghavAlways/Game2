import asyncio
from typing import Dict, List, Union
import time

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery

from AviaxMusic import app
from AviaxMusic.misc import SUDOERS
from config import BANNED_USERS

# Import games modules to ensure they're loaded
try:
    from AviaxMusic.plugins.bot.wordle import start_wordle, active_games as wordle_games
except ImportError:
    wordle_games = {}
    print("Wordle game module not fully loaded")
    
try:
    from AviaxMusic.plugins.bot.hangman import active_hangman_games
except ImportError:
    active_hangman_games = {}
    print("Hangman game module not fully loaded")
    
try:
    from AviaxMusic.plugins.bot.rps import active_rps_games
except ImportError:
    active_rps_games = {}
    print("RPS game module not fully loaded")
    
try:
    from AviaxMusic.plugins.bot.guess import active_guess_games
except ImportError:
    active_guess_games = {}
    print("Number Guess game module not fully loaded")

# Cleanup utility for abandoned games
async def cleanup_abandoned_games():
    """Check and clean up any abandoned games periodically"""
    # Run cleanup every 30 minutes
    CLEANUP_INTERVAL = 1800
    # Games without activity for 2 hours will be cleaned up
    INACTIVE_THRESHOLD = 7200  # 2 hours in seconds
    
    while True:
        try:
            current_time = time.time()
            cleaned_count = 0
            
            # Check Wordle games
            wordle_to_clean = []
            for chat_id, game_data in wordle_games.items():
                # Check if the game has a last_activity timestamp
                if "last_activity" in game_data:
                    if current_time - game_data["last_activity"] > INACTIVE_THRESHOLD:
                        wordle_to_clean.append(chat_id)
                else:
                    # Add timestamp for games without one
                    game_data["last_activity"] = current_time
            
            # Clean up inactive Wordle games
            for chat_id in wordle_to_clean:
                try:
                    del wordle_games[chat_id]
                    cleaned_count += 1
                    print(f"Cleaned up inactive Wordle game in chat {chat_id}")
                except KeyError:
                    pass
                    
            # Check Hangman games (typically don't have timestamps)
            hangman_to_clean = []
            current_hangman_games = list(active_hangman_games.keys())
            for chat_id in current_hangman_games:
                # We'll add a timestamp if it doesn't exist
                if "last_activity" not in active_hangman_games[chat_id]:
                    active_hangman_games[chat_id]["last_activity"] = current_time
                elif current_time - active_hangman_games[chat_id]["last_activity"] > INACTIVE_THRESHOLD:
                    hangman_to_clean.append(chat_id)
            
            # Clean up inactive Hangman games
            for chat_id in hangman_to_clean:
                try:
                    del active_hangman_games[chat_id]
                    cleaned_count += 1
                    print(f"Cleaned up inactive Hangman game in chat {chat_id}")
                except KeyError:
                    pass
            
            # Check RPS games
            rps_to_clean = []
            current_rps_games = list(active_rps_games.keys())
            for chat_id in current_rps_games:
                # We'll add a timestamp if it doesn't exist
                if "last_activity" not in active_rps_games[chat_id]:
                    active_rps_games[chat_id]["last_activity"] = current_time
                elif current_time - active_rps_games[chat_id]["last_activity"] > INACTIVE_THRESHOLD:
                    rps_to_clean.append(chat_id)
            
            # Clean up inactive RPS games
            for chat_id in rps_to_clean:
                try:
                    del active_rps_games[chat_id]
                    cleaned_count += 1
                    print(f"Cleaned up inactive RPS game in chat {chat_id}")
                except KeyError:
                    pass
            
            # Check Number Guess games
            numguess_to_clean = []
            current_numguess_games = list(active_guess_games.keys())
            for chat_id in current_numguess_games:
                # We'll add a timestamp if it doesn't exist
                if "last_activity" not in active_guess_games[chat_id]:
                    active_guess_games[chat_id]["last_activity"] = current_time
                elif current_time - active_guess_games[chat_id]["last_activity"] > INACTIVE_THRESHOLD:
                    numguess_to_clean.append(chat_id)
            
            # Clean up inactive Number Guess games
            for chat_id in numguess_to_clean:
                try:
                    del active_guess_games[chat_id]
                    cleaned_count += 1
                    print(f"Cleaned up inactive Number Guess game in chat {chat_id}")
                except KeyError:
                    pass
            
            if cleaned_count > 0:
                print(f"Game cleanup task: Cleaned up {cleaned_count} inactive games")
                
        except Exception as e:
            print(f"Error in game cleanup task: {e}")
        
        # Wait for next cleanup interval
        await asyncio.sleep(CLEANUP_INTERVAL)

# Start cleanup task when bot starts
asyncio.create_task(cleanup_abandoned_games())

# Game config with metadata
GAME_CONFIG = [
    {
        "name": "🔤 Wordle",
        "description": "Guess the hidden word with letter hints",
        "callback": "start_wordle",
        "command": "/wordle",
        "help_command": "/wordlehelp"
    },
    {
        "name": "🎯 Hangman",
        "description": "Guess letters to reveal the hidden word",
        "callback": "hangman_start",
        "command": "/hangman",
        "help_command": "/hangmanhelp"
    },
    {
        "name": "👊 Rock-Paper-Scissors",
        "description": "Classic game of chance and strategy",
        "callback": "rps_new_game",
        "command": "/rps",
        "help_command": "/rpshelp"
    },
    {
        "name": "🤖 Play RPS with Bot",
        "description": "Quick Rock-Paper-Scissors vs AI",
        "callback": "rpsbot_play_again",
        "command": "/rpsbot",
        "help_command": "/rpshelp"
    },
    {
        "name": "🔢 Number Guess",
        "description": "Guess the secret number with hints",
        "callback": "numguess_start",
        "command": "/numguess",
        "help_command": "/numguesshelp"
    }
]

# Command to show games menu
@app.on_message(filters.command("games") & ~BANNED_USERS)
async def games_menu_command(_, message: Message):
    await show_games_menu(message)

# Function to show games menu in a message
async def show_games_menu(message: Message):
    # Create buttons grid
    buttons = []
    row = []
    
    for i, game in enumerate(GAME_CONFIG):
        # Add button for each game
        row.append(InlineKeyboardButton(
            game["name"], 
            callback_data=game["callback"]
        ))
        
        # 2 buttons per row
        if len(row) == 2 or i == len(GAME_CONFIG) - 1:
            buttons.append(row)
            row = []
    
    # Add help button
    buttons.append([InlineKeyboardButton("❓ Game Rules", callback_data="games_help")])
    
    # Send menu message
    await message.reply_text(
        "🎮 **Games Menu**\n\n"
        "Choose a game to play from the options below:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# Handler for game button in music player
@app.on_callback_query(filters.regex("^game_menu$"))
async def game_menu_button(_, query: CallbackQuery):
    # Get current game statistics
    active_wordle = len(wordle_games)
    active_hangman = len(active_hangman_games)
    active_rps = len(active_rps_games)
    active_numguess = len(active_guess_games)
    total_active = active_wordle + active_hangman + active_rps + active_numguess
    
    # Create buttons grid
    buttons = []
    row = []
    
    for i, game in enumerate(GAME_CONFIG):
        # Add button for each game
        row.append(InlineKeyboardButton(
            game["name"], 
            callback_data=game["callback"]
        ))
        
        # 2 buttons per row
        if len(row) == 2 or i == len(GAME_CONFIG) - 1:
            buttons.append(row)
            row = []
    
    # Add help button
    buttons.append([InlineKeyboardButton("❓ Game Rules", callback_data="games_help")])
    
    # Send menu message
    await query.message.reply_text(
        f"🎮 **Games Menu**\n\n"
        f"Choose a game to play from the options below:\n"
        f"Currently active games: {total_active}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    await query.answer()

# Game help menu
@app.on_callback_query(filters.regex("^games_help$"))
async def games_help_menu(_, query: CallbackQuery):
    help_text = "🎮 **Available Games**\n\n"
    
    # Add information for each game
    for game in GAME_CONFIG:
        help_text += f"**{game['name']}**\n"
        help_text += f"{game['description']}\n"
        help_text += f"Start: {game['command']} | Help: {game['help_command']}\n\n"
    
    # Create back button
    buttons = [[InlineKeyboardButton("« Back to Games", callback_data="games_back")]]
    
    await query.message.edit_text(
        help_text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    await query.answer()

# Back to games menu from help
@app.on_callback_query(filters.regex("^games_back$"))
async def games_back_menu(_, query: CallbackQuery):
    # Get current game statistics
    active_wordle = len(wordle_games)
    active_hangman = len(active_hangman_games)
    active_rps = len(active_rps_games)
    active_numguess = len(active_guess_games)
    total_active = active_wordle + active_hangman + active_rps + active_numguess
    
    # Create buttons grid
    buttons = []
    row = []
    
    for i, game in enumerate(GAME_CONFIG):
        # Add button for each game
        row.append(InlineKeyboardButton(
            game["name"], 
            callback_data=game["callback"]
        ))
        
        # 2 buttons per row
        if len(row) == 2 or i == len(GAME_CONFIG) - 1:
            buttons.append(row)
            row = []
    
    # Add help button
    buttons.append([InlineKeyboardButton("❓ Game Rules", callback_data="games_help")])
    
    # Update menu message
    await query.message.edit_text(
        f"🎮 **Games Menu**\n\n"
        f"Choose a game to play from the options below:\n"
        f"Currently active games: {total_active}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    await query.answer()

# Modify the existing start_wordle callback to work with our system
@app.on_callback_query(filters.regex("^start_wordle$"))
async def start_wordle_from_menu(_, query: CallbackQuery):
    try:
        # Create a fake message object to pass to the original handler
        message = query.message
        message.command = ["wordle"]
        message.from_user = query.from_user
        
        # Call the original wordle handler
        from AviaxMusic.plugins.bot.wordle import start_wordle
        await start_wordle(_, message)
        
        await query.answer()
    except Exception as e:
        print(f"Error starting Wordle: {e}")
        await query.answer("Error starting game. Try using /wordle command directly.", show_alert=True)

# Add callback handlers for other games
@app.on_callback_query(filters.regex("^hangman_start$"))
async def start_hangman_from_menu(_, query: CallbackQuery):
    try:
        # Create a fake message object to pass to the original handler
        message = query.message
        message.command = ["hangman"]
        message.from_user = query.from_user
        
        # Ensure message has a chat attribute with id
        if not hasattr(message, 'chat'):
            message.chat = query.message.chat
        
        # Call the original handler
        from AviaxMusic.plugins.bot.hangman import start_hangman_game
        await start_hangman_game(_, message)
        
        await query.answer()
    except Exception as e:
        print(f"Error starting Hangman: {e}")
        await query.answer("Error starting game. Try using /hangman command directly.", show_alert=True)

@app.on_callback_query(filters.regex("^rps_new_game$"))
async def start_rps_from_menu(_, query: CallbackQuery):
    try:
        # Create a fake message object to pass to the original handler
        message = query.message
        message.command = ["rps"]
        message.from_user = query.from_user
        
        # Ensure message has a chat attribute with id
        if not hasattr(message, 'chat'):
            message.chat = query.message.chat
        
        # Call the original handler
        from AviaxMusic.plugins.bot.rps import start_rps_game
        await start_rps_game(_, message)
        
        await query.answer()
    except Exception as e:
        print(f"Error starting RPS: {e}")
        await query.answer("Error starting game. Try using /rps command directly.", show_alert=True)

@app.on_callback_query(filters.regex("^rpsbot_play_again$"))
async def start_rpsbot_from_menu(_, query: CallbackQuery):
    try:
        # Create a fake message object to pass to the original handler
        message = query.message
        message.command = ["rpsbot"]
        message.from_user = query.from_user
        
        # Ensure message has a chat attribute with id
        if not hasattr(message, 'chat'):
            message.chat = query.message.chat
        
        # Call the original handler
        from AviaxMusic.plugins.bot.rps import play_rps_with_bot
        await play_rps_with_bot(_, message)
        
        await query.answer()
    except Exception as e:
        print(f"Error starting RPSBot: {e}")
        await query.answer("Error starting game. Try using /rpsbot command directly.", show_alert=True)

@app.on_callback_query(filters.regex("^numguess_start$"))
async def start_numguess_from_menu(_, query: CallbackQuery):
    try:
        # Create a fake message object to pass to the original handler
        message = query.message
        message.command = ["numguess"]
        message.from_user = query.from_user
        
        # Ensure message has a chat attribute with id
        if not hasattr(message, 'chat'):
            message.chat = query.message.chat
        
        # Call the original handler
        from AviaxMusic.plugins.bot.guess import start_number_guess
        await start_number_guess(_, message)
        
        await query.answer()
    except Exception as e:
        print(f"Error starting Number Guess: {e}")
        await query.answer("Error starting game. Try using /numguess command directly.", show_alert=True) 