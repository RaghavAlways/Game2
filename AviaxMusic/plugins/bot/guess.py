import asyncio
import random
from typing import Dict, List, Union

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery

from AviaxMusic import app
from AviaxMusic.misc import SUDOERS
from config import BANNED_USERS

# Active games dictionary 
# Structure: {chat_id: {"number": int, "attempts": int, "players": {user_id: int}, "max_number": int, "hints_used": int}}
active_guess_games = {}

# Start a number guessing game
@app.on_message(filters.command("numguess") & ~BANNED_USERS)
async def start_number_guess(_, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Check if a game is already active
    if chat_id in active_guess_games:
        game = active_guess_games[chat_id]
        # Update last activity timestamp
        import time
        game["last_activity"] = time.time()
        
        await message.reply_text(
            f"🎮 A Number Guessing game is already active!\n\n"
            f"Guess a number between 1 and {game['max_number']}\n"
            f"Attempts so far: {game['attempts']}\n\n"
            f"Use `/guess [number]` to make a guess."
        )
        return
    
    # Determine max number (default: 100)
    max_number = 100
    if len(message.command) > 1:
        try:
            requested_max = int(message.command[1])
            if 10 <= requested_max <= 1000:
                max_number = requested_max
        except ValueError:
            pass
    
    # Generate a random number
    secret_number = random.randint(1, max_number)
    
    # Create new game
    import time
    active_guess_games[chat_id] = {
        "number": secret_number,
        "attempts": 0,
        "players": {user_id: 0},
        "max_number": max_number,
        "hints_used": 0,
        "last_activity": time.time()  # Add timestamp
    }
    
    # Make difficulty message
    difficulty = "Easy 😃" if max_number <= 50 else "Medium 😐" if max_number <= 200 else "Hard 😱"
    
    await message.reply_text(
        f"🎮 New Number Guessing game started!\n\n"
        f"I'm thinking of a number between 1 and {max_number}. ({difficulty})\n"
        f"Use `/guess [number]` to make a guess.\n\n"
        f"Good luck!",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("💡 Hint", callback_data="numguess_hint"),
                InlineKeyboardButton("❌ End Game", callback_data="numguess_end")
            ]
        ])
    )

# Make a guess
@app.on_message(filters.command("guess") & ~BANNED_USERS)
async def make_guess(_, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Check if there's a hangman game active
    try:
        from AviaxMusic.plugins.bot.hangman import active_hangman_games
        hangman_active = chat_id in active_hangman_games
    except ImportError:
        hangman_active = False
    
    # Check if there's a number guessing game active
    number_guess_active = chat_id in active_guess_games
    
    # If number guessing game is active, update its timestamp
    if number_guess_active:
        import time
        active_guess_games[chat_id]["last_activity"] = time.time()
    
    # If both games are active or no games are active, we need to disambiguate
    if (hangman_active and number_guess_active) or (not hangman_active and not number_guess_active):
        # Check command context to determine intent
        if len(message.command) > 1:
            guess = message.command[1]
            # If guess is a single letter, likely for hangman
            if len(guess) == 1 and guess.isalpha():
                if hangman_active:
                    # Let hangman handle it
                    return
                else:
                    await message.reply_text(
                        "No active Hangman game! Start one with /hangman",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("Start Hangman", callback_data="hangman_start")
                        ]])
                    )
                    return
            # If guess is a number, likely for number guess
            elif guess.isdigit():
                if not number_guess_active:
                    await message.reply_text(
                        "No active Number Guessing game! Start one with /numguess",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("Start Number Guess", callback_data="numguess_start")
                        ]])
                    )
                    return
            else:
                # If we can't determine, ask the user
                if hangman_active and number_guess_active:
                    await message.reply_text(
                        "Multiple games are active. Which one are you playing?\n\n"
                        "For Hangman, use: `/guess a` (a single letter)\n"
                        "For Number Guess, use: `/guess 42` (a number)",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("Hangman Game", callback_data="hangman_show")],
                            [InlineKeyboardButton("Number Guess Game", callback_data="numguess_show")]
                        ])
                    )
                    return
                elif not hangman_active and not number_guess_active:
                    await message.reply_text(
                        "No active games found! Start one first:\n\n"
                        "/hangman - Start a Hangman game\n"
                        "/numguess - Start a Number Guessing game",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("Games Menu", callback_data="game_menu")]
                        ])
                    )
                    return
        else:
            # No guess provided
            if hangman_active and number_guess_active:
                await message.reply_text(
                    "Multiple games are active. Which one are you playing?\n\n"
                    "For Hangman, use: `/guess a` (a single letter)\n"
                    "For Number Guess, use: `/guess 42` (a number)"
                )
                return
            elif hangman_active:
                await message.reply_text("Please provide a letter to guess!\n\nUsage: `/guess a`")
                return
            elif number_guess_active:
                await message.reply_text("Please provide a number to guess!\n\nUsage: `/guess 42`")
                return
            else:
                await message.reply_text(
                    "No active games found! Start one first:\n\n"
                    "/hangman - Start a Hangman game\n"
                    "/numguess - Start a Number Guessing game",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Games Menu", callback_data="game_menu")]
                    ])
                )
                return
    
    # If only Hangman is active, let it handle the command
    if hangman_active and not number_guess_active:
        # Let the hangman game handle this
        return
    
    # At this point, we know we're handling a number guess game
    
    # Check for valid guess
    if len(message.command) < 2:
        await message.reply_text("Please provide your guess!\n\nUsage: `/guess 42`")
        return
    
    try:
        guess = int(message.command[1])
    except ValueError:
        await message.reply_text("Please enter a valid number!")
        return
    
    # Get game data
    game = active_guess_games[chat_id]
    secret_number = game["number"]
    max_number = game["max_number"]
    
    # Make sure guess is in range
    if guess < 1 or guess > max_number:
        await message.reply_text(f"Please guess a number between 1 and {max_number}!")
        return
    
    # Add player if not already in game
    if user_id not in game["players"]:
        game["players"][user_id] = 0
    
    # Increment attempts
    game["attempts"] += 1
    game["players"][user_id] += 1
    
    # Check guess
    if guess == secret_number:
        # Winner!
        attempts = game["attempts"]
        player_attempts = game["players"][user_id]
        hints = game["hints_used"]
        
        try:
            player = await app.get_chat_member(chat_id, user_id)
            player_name = player.user.first_name
        except:
            player_name = "Player"
        
        # Rating based on attempts and max number
        max_attempts = max(10, max_number // 10)
        if attempts <= max_attempts * 0.3:
            rating = "🌟🌟🌟 Amazing!"
        elif attempts <= max_attempts * 0.6:
            rating = "🌟🌟 Great job!"
        else:
            rating = "🌟 Good effort!"
        
        # If hints were used, downgrade rating
        if hints > 0:
            rating += f" (with {hints} hints)"
        
        # Send win message
        win_message = (
            f"🎮 **CORRECT!** 🎉\n\n"
            f"The number was indeed **{secret_number}**!\n"
            f"{player_name} got it in {attempts} attempts. {rating}\n\n"
            f"Your personal attempts: {player_attempts}"
        )
        
        # Delete game
        del active_guess_games[chat_id]
        
        await message.reply_text(
            win_message,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Play Again", callback_data="numguess_start")
            ]])
        )
        
    else:
        # Incorrect - give hint
        if guess < secret_number:
            hint = f"Higher than {guess}! ⬆️"
        else:
            hint = f"Lower than {guess}! ⬇️"
        
        # Create message showing game progress
        progress_text = (
            f"🎮 **Not quite!** {hint}\n\n"
            f"Guess a number between 1 and {max_number}\n"
            f"Attempts so far: {game['attempts']}\n"
            f"Your attempts: {game['players'][user_id]}"
        )
        
        await message.reply_text(
            progress_text,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("💡 Hint", callback_data="numguess_hint"),
                    InlineKeyboardButton("❌ End Game", callback_data="numguess_end")
                ]
            ])
        )

# Handle game callbacks
@app.on_callback_query(filters.regex("^numguess_"))
async def numguess_callback(_, query: CallbackQuery):
    chat_id = query.message.chat.id
    user_id = query.from_user.id
    action = query.data.split("_")[1]
    
    # Start new game
    if action == "start":
        # Check if a game is already active
        if chat_id in active_guess_games:
            await query.answer("A game is already active!")
            return
        
        # Generate a random number
        max_number = 100
        secret_number = random.randint(1, max_number)
        
        # Create new game
        active_guess_games[chat_id] = {
            "number": secret_number,
            "attempts": 0,
            "players": {user_id: 0},
            "max_number": max_number,
            "hints_used": 0
        }
        
        await query.message.edit_text(
            f"🎮 New Number Guessing game started!\n\n"
            f"I'm thinking of a number between 1 and {max_number}.\n"
            f"Use `/guess [number]` to make a guess.\n\n"
            f"Good luck!",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("💡 Hint", callback_data="numguess_hint"),
                    InlineKeyboardButton("❌ End Game", callback_data="numguess_end")
                ]
            ])
        )
        await query.answer("Game started!")
    
    # Show current game status
    elif action == "show":
        # Check if a game is active
        if chat_id not in active_guess_games:
            await query.answer("No active Number Guessing game!")
            await query.message.edit_text(
                "No active Number Guessing game! Start one with /numguess",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Start Game", callback_data="numguess_start")
                ]])
            )
            return
        
        game = active_guess_games[chat_id]
        max_number = game["max_number"]
        attempts = game["attempts"]
        
        await query.message.edit_text(
            f"🎮 Number Guessing Game\n\n"
            f"I'm thinking of a number between 1 and {max_number}.\n"
            f"Attempts so far: {attempts}\n\n"
            f"Use `/guess [number]` to make a guess.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("💡 Hint", callback_data="numguess_hint"),
                    InlineKeyboardButton("❌ End Game", callback_data="numguess_end")
                ]
            ])
        )
        await query.answer("Game status shown")
        
    # Give a hint
    elif action == "hint":
        # Check if a game is active
        if chat_id not in active_guess_games:
            await query.answer("No active game to give a hint for!")
            return
        
        game = active_guess_games[chat_id]
        secret_number = game["number"]
        max_number = game["max_number"]
        
        # Increment hint counter
        game["hints_used"] += 1
        
        # Generate range hint
        hint_range = max(max_number // 10, 5)
        lower_bound = max(1, secret_number - hint_range)
        upper_bound = min(max_number, secret_number + hint_range)
        
        await query.answer(
            f"Hint: The number is between {lower_bound} and {upper_bound}",
            show_alert=True
        )
        
    # End game
    elif action == "end":
        # Check if a game is active
        if chat_id not in active_guess_games:
            await query.answer("No active game to end!")
            return
        
        game = active_guess_games[chat_id]
        secret_number = game["number"]
        
        # Delete game
        del active_guess_games[chat_id]
        
        await query.message.edit_text(
            f"🎮 Game Ended!\n\n"
            f"The number was: {secret_number}\n"
            f"Ended by: {query.from_user.first_name}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Play Again", callback_data="numguess_start")
            ]])
        )
        await query.answer("Game ended!")

# Help command for number guessing game
@app.on_message(filters.command("numguesshelp") & ~BANNED_USERS)
async def numguess_help(_, message: Message):
    help_text = """
🎮 **Number Guessing Game Help**

**Commands:**
• `/numguess [max]` - Start a game with optional max number
• `/guess [number]` - Make a guess

**How to Play:**
• I'll think of a number between 1 and the max (default: 100)
• You try to guess it in as few attempts as possible
• I'll tell you if your guess is too high or too low
• You can use the hint button for a narrow range, but it counts against your score

**Tips:**
• Start with a number in the middle (like 50 for range 1-100)
• Narrow your range with each guess
• The fewer attempts, the better your score!

Have fun! 🎲
"""
    await message.reply_text(
        help_text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Start Game", callback_data="numguess_start")
        ]])
    ) 