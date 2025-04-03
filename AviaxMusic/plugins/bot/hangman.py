import asyncio
import random
from typing import Dict, List, Tuple, Union
import re
import time

from pyrogram import filters
from pyrogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    Message, 
    CallbackQuery
)

from AviaxMusic import app
from AviaxMusic.misc import SUDOERS
from config import BANNED_USERS

# Word lists for different difficulty levels
WORD_LISTS = {
    "easy": [
        "cat", "dog", "sun", "moon", "fish", "bird", "tree", "road", 
        "book", "king", "water", "fire", "earth", "wind", "heart", 
        "smile", "cloud", "rain", "star", "light", "chair", "table",
        "paper", "green", "happy", "sweet", "juice", "apple", "house",
        "mouse", "clock", "bread", "music", "river", "beach", "sleep"
    ],
    "medium": [
        "rocket", "banana", "planet", "garden", "bottle", "window", 
        "flower", "picture", "umbrella", "keyboard", "treasure", 
        "diamond", "chocolate", "butterfly", "telephone", "mountain", 
        "elephant", "restaurant", "birthday", "computer", "vacation", 
        "adventure", "community", "beautiful", "technology", "playground",
        "festival", "friendship", "professor", "happiness", "universe"
    ],
    "hard": [
        "extraordinary", "congratulation", "investigation", "revolutionary", 
        "biodiversity", "encyclopedia", "determination", "international", 
        "environmental", "civilization", "responsibility", "sophisticated", 
        "collaboration", "comprehension", "identification", "qualification", 
        "consciousness", "entertainment", "distinguished", "conversation"
    ],
}

# Hangman ASCII art states
HANGMAN_STATES = [
    """
```
  +---+
  |   |
      |
      |
      |
      |
=========
```""",
    """
```
  +---+
  |   |
  O   |
      |
      |
      |
=========
```""",
    """
```
  +---+
  |   |
  O   |
  |   |
      |
      |
=========
```""",
    """
```
  +---+
  |   |
  O   |
 /|   |
      |
      |
=========
```""",
    """
```
  +---+
  |   |
  O   |
 /|\\  |
      |
      |
=========
```""",
    """
```
  +---+
  |   |
  O   |
 /|\\  |
 /    |
      |
=========
```""",
    """
```
  +---+
  |   |
  O   |
 /|\\  |
 / \\  |
      |
=========
```"""
]

# Active games dictionary
# Structure: {chat_id: {"word": str, "guessed": list, "misses": int, "players": {user_id: score}}}
active_hangman_games = {}

# Function to display current game state
def get_current_state(chat_id: int) -> Tuple[str, InlineKeyboardMarkup]:
    game = active_hangman_games.get(chat_id)
    if not game:
        return "No active game.", InlineKeyboardMarkup([[
            InlineKeyboardButton("Start New Game", callback_data="hangman_start")
        ]])
    
    # Update last activity timestamp for the cleanup task
    game["last_activity"] = time.time()
    
    word = game["word"]
    guessed = game["guessed"]
    misses = game["misses"]
    
    # Create display word with guessed letters shown
    display_word = ""
    for letter in word:
        if letter in guessed:
            display_word += letter + " "
        else:
            display_word += "_ "
    
    # Create display for guessed letters
    guessed_letters = ", ".join(sorted(guessed)) if guessed else "None"
    
    # Create game message
    message = f"{HANGMAN_STATES[misses]}\n"
    message += f"**Word:** `{display_word.strip()}`\n"
    message += f"**Guessed Letters:** {guessed_letters}\n"
    message += f"**Misses:** {misses}/6\n\n"
    
    # Create keyboard for letter selection
    keyboard = []
    row = []
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    
    for i, letter in enumerate(alphabet):
        if letter in guessed:
            # Add already guessed letter as a disabled button
            row.append(InlineKeyboardButton(
                "✓" if letter in word else "✗", 
                callback_data=f"hangman_guessed"
            ))
        else:
            # Add available letter button
            row.append(InlineKeyboardButton(
                letter.upper(), 
                callback_data=f"hangman_guess_{letter}"
            ))
        
        # Break after 7 buttons per row
        if (i + 1) % 7 == 0 or i == len(alphabet) - 1:
            keyboard.append(row)
            row = []
    
    # Add control buttons
    keyboard.append([
        InlineKeyboardButton("❌ End Game", callback_data="hangman_end"),
        InlineKeyboardButton("💡 Hint", callback_data="hangman_hint")
    ])
    
    return message, InlineKeyboardMarkup(keyboard)

# Function to check if game is won or lost
def check_game_status(chat_id: int) -> str:
    game = active_hangman_games.get(chat_id)
    if not game:
        return "no_game"
    
    word = game["word"]
    guessed = game["guessed"]
    misses = game["misses"]
    
    # Check if all letters in word are guessed
    if all(letter in guessed for letter in word):
        return "won"
    
    # Check if max misses reached
    if misses >= 6:
        return "lost"
    
    # Game is still active
    return "active"

# Function to give a hint (reveal one letter)
def get_hint(chat_id: int) -> str:
    game = active_hangman_games.get(chat_id)
    if not game:
        return "No active game."
    
    word = game["word"]
    guessed = game["guessed"]
    
    # Find unguessed letters
    unguessed = [letter for letter in word if letter not in guessed]
    if not unguessed:
        return "All letters already revealed!"
    
    # Pick a random unguessed letter
    hint_letter = random.choice(unguessed)
    
    # Add the hint letter to guessed letters
    game["guessed"].append(hint_letter)
    
    return f"Hint: The word contains the letter '{hint_letter.upper()}'."

# Command to start a new Hangman game
@app.on_message(filters.command("hangman") & filters.group & ~BANNED_USERS)
async def start_hangman_game(_, message: Message):
    chat_id = message.chat.id
    
    # Check if there's already an active game
    if chat_id in active_hangman_games:
        state_message, markup = get_current_state(chat_id)
        await message.reply_text(
            f"A game is already in progress!\n\n{state_message}",
            reply_markup=markup
        )
        return
    
    # Determine difficulty
    difficulty = "medium"  # Default difficulty
    if len(message.command) > 1:
        arg = message.command[1].lower()
        if arg in ["easy", "medium", "hard"]:
            difficulty = arg
    
    # Select a random word based on difficulty
    word = random.choice(WORD_LISTS[difficulty])
    
    # Initialize the game
    active_hangman_games[chat_id] = {
        "word": word,
        "guessed": [],
        "misses": 0,
        "players": {message.from_user.id: 0},
        "difficulty": difficulty
    }
    
    # Get the current game state
    state_message, markup = get_current_state(chat_id)
    
    # Send the initial game message
    await message.reply_text(
        f"🎮 New Hangman game started! Difficulty: {difficulty.title()}\n\n{state_message}",
        reply_markup=markup
    )

# Command to guess a letter via text
@app.on_message(filters.command("guess") & filters.group & ~BANNED_USERS)
async def guess_letter_command(_, message: Message):
    chat_id = message.chat.id
    
    # Check if there's an active game
    if chat_id not in active_hangman_games:
        await message.reply_text(
            "No active Hangman game! Start with /hangman",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Start New Game", callback_data="hangman_start")
            ]])
        )
        return
    
    # Check if argument provided
    if len(message.command) < 2:
        await message.reply_text("Please provide a letter to guess!\n\nUsage: `/guess a`")
        return
    
    # Get the guessed letter
    guess = message.command[1].lower()
    
    # Validate the guess
    if not re.match(r'^[a-z]$', guess):
        await message.reply_text("Please guess a single letter (a-z).")
        return
    
    # Process the guess
    game = active_hangman_games[chat_id]
    
    # Check if letter already guessed
    if guess in game["guessed"]:
        await message.reply_text(f"Letter '{guess.upper()}' already guessed!")
        return
    
    # Add to guessed letters
    game["guessed"].append(guess)
    
    # Add player if not already in game
    if message.from_user.id not in game["players"]:
        game["players"][message.from_user.id] = 0
    
    # Check if guess is correct
    if guess in game["word"]:
        # Correct guess awards points
        game["players"][message.from_user.id] += 1
    else:
        # Incorrect guess increases miss counter
        game["misses"] += 1
    
    # Check game status
    status = check_game_status(chat_id)
    
    # Get current state
    state_message, markup = get_current_state(chat_id)
    
    # Handle game end conditions
    if status == "won":
        # Get winner (player with most correct guesses)
        winner_id, winner_score = max(game["players"].items(), key=lambda x: x[1])
        try:
            winner = await app.get_chat_member(chat_id, winner_id)
            winner_name = winner.user.first_name
        except:
            winner_name = "Player"
        
        # End message
        end_message = (
            f"🎮 Hangman: {game['word'].upper()}\n\n"
            f"You won! 🎉\n"
            f"Top player: {winner_name} with {winner_score} points"
        )
        
        # Clear the game
        del active_hangman_games[chat_id]
        
        await message.reply_text(
            end_message,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Play Again", callback_data="hangman_start")
            ]])
        )
    elif status == "lost":
        # End message
        end_message = (
            f"🎮 Hangman: Game Over!\n\n"
            f"{HANGMAN_STATES[6]}\n"
            f"The word was: {game['word'].upper()}\n"
            f"Better luck next time! 🥲"
        )
        
        # Clear the game
        del active_hangman_games[chat_id]
        
        await message.reply_text(
            end_message,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Play Again", callback_data="hangman_start")
            ]])
        )
    else:
        # Game continues
        await message.reply_text(state_message, reply_markup=markup)

# Callback handler for Hangman game actions
@app.on_callback_query(filters.regex("^hangman_"))
async def hangman_callback_handler(_, query: CallbackQuery):
    chat_id = query.message.chat.id
    user_id = query.from_user.id
    
    # Extract the action from the callback data
    action = query.data.split("_")[1]
    
    # Show current game state for an active game
    if action == "show":
        if chat_id not in active_hangman_games:
            await query.answer("No active game found!")
            await query.message.edit_text(
                "No active Hangman game found. Start a new one?",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Start New Game", callback_data="hangman_start")
                ]])
            )
            return
            
        state_message, markup = get_current_state(chat_id)
        await query.message.edit_text(state_message, reply_markup=markup)
        await query.answer("Game state refreshed")
        return
        
    # Start a new game
    if action == "start":
        # Check if there's already an active game
        if chat_id in active_hangman_games:
            state_message, markup = get_current_state(chat_id)
            await query.message.edit_text(
                f"A game is already in progress!\n\n{state_message}",
                reply_markup=markup
            )
            await query.answer("Game already active!")
            return
        
        # Select a random word with medium difficulty
        word = random.choice(WORD_LISTS["medium"])
        
        # Initialize the game
        active_hangman_games[chat_id] = {
            "word": word,
            "guessed": [],
            "misses": 0,
            "players": {user_id: 0}
        }
        
        # Display initial game state
        state_message, markup = get_current_state(chat_id)
        await query.message.edit_text(
            f"🎮 New Hangman game started! Guess the word:\n\n{state_message}",
            reply_markup=markup
        )
        await query.answer("Game started!")
        return
    
    # Handle end game action
    elif action == "end":
        # Check if there's an active game
        if chat_id not in active_hangman_games:
            await query.answer("No active game to end!")
            return
        
        # Get the word
        word = active_hangman_games[chat_id]["word"]
        
        # Clear the game
        del active_hangman_games[chat_id]
        
        # End message
        end_message = (
            f"🎮 Hangman: Game Ended!\n\n"
            f"The word was: {word.upper()}\n"
            f"Game ended by: {query.from_user.first_name}"
        )
        
        await query.message.edit_text(
            end_message,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Start New Game", callback_data="hangman_start")
            ]])
        )
        await query.answer("Game ended!")
    
    # Handle hint action
    elif action == "hint":
        # Check if there's an active game
        if chat_id not in active_hangman_games:
            await query.answer("No active game to give a hint for!")
            return
        
        # Get the hint
        hint_message = get_hint(chat_id)
        await query.answer(hint_message, show_alert=True)
        
        # Update the game state
        state_message, markup = get_current_state(chat_id)
        await query.message.edit_text(state_message, reply_markup=markup)
    
    # Handle guessed letter action (no action needed)
    elif action == "guessed":
        await query.answer("This letter has already been guessed!")
    
    # Handle guess action
    elif action.startswith("guess_"):
        # Check if there's an active game
        if chat_id not in active_hangman_games:
            await query.answer("No active game!")
            return
        
        # Get the guessed letter
        guess = action.split("_")[1]
        
        # Process the guess
        game = active_hangman_games[chat_id]
        
        # Check if letter already guessed
        if guess in game["guessed"]:
            await query.answer(f"Letter '{guess.upper()}' already guessed!")
            return
        
        # Add to guessed letters
        game["guessed"].append(guess)
        
        # Add player if not already in game
        if user_id not in game["players"]:
            game["players"][user_id] = 0
        
        # Check if guess is correct
        if guess in game["word"]:
            # Correct guess
            game["players"][user_id] += 1
            await query.answer(f"Good guess! '{guess.upper()}' is in the word.")
        else:
            # Incorrect guess
            game["misses"] += 1
            await query.answer(f"Sorry, '{guess.upper()}' is not in the word.")
        
        # Check game status
        status = check_game_status(chat_id)
        
        # Get current state
        state_message, markup = get_current_state(chat_id)
        
        # Handle game end conditions
        if status == "won":
            # Get winner (player with most correct guesses)
            winner_id, winner_score = max(game["players"].items(), key=lambda x: x[1])
            try:
                winner = await app.get_chat_member(chat_id, winner_id)
                winner_name = winner.user.first_name
            except:
                winner_name = "Player"
            
            # End message
            end_message = (
                f"🎮 Hangman: {game['word'].upper()}\n\n"
                f"You won! 🎉\n"
                f"Top player: {winner_name} with {winner_score} points"
            )
            
            # Clear the game
            del active_hangman_games[chat_id]
            
            await query.message.edit_text(
                end_message,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Play Again", callback_data="hangman_start")
                ]])
            )
        elif status == "lost":
            # End message
            end_message = (
                f"🎮 Hangman: Game Over!\n\n"
                f"{HANGMAN_STATES[6]}\n"
                f"The word was: {game['word'].upper()}\n"
                f"Better luck next time! 🥲"
            )
            
            # Clear the game
            del active_hangman_games[chat_id]
            
            await query.message.edit_text(
                end_message,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Play Again", callback_data="hangman_start")
                ]])
            )
        else:
            # Game continues
            await query.message.edit_text(state_message, reply_markup=markup)

# Help command for Hangman
@app.on_message(filters.command("hangmanhelp") & ~BANNED_USERS)
async def hangman_help(_, message: Message):
    help_text = """
🎮 **Hangman Game Help**

**Commands:**
• `/hangman [easy|medium|hard]` - Start a new game with optional difficulty
• `/guess [letter]` - Guess a letter

**How to Play:**
• Guess letters to uncover the hidden word
• Each incorrect guess adds a part to the hangman
• 6 incorrect guesses and you lose!

**Difficulty Levels:**
• Easy: Short, simple words
• Medium: Average length, moderately common words
• Hard: Longer, more challenging words

You can also use the buttons to select letters directly!
"""
    await message.reply_text(
        help_text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Start Game", callback_data="hangman_start")
        ]])
    ) 