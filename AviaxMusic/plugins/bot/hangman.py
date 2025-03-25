import random
import asyncio
from typing import Dict, List
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from AviaxMusic import app
from AviaxMusic.misc import SUDOERS
from AviaxMusic.utils.database import get_lang
from strings import get_string

# Word categories and their corresponding words
WORD_CATEGORIES = {
    "animals": ["ELEPHANT", "GIRAFFE", "PENGUIN", "DOLPHIN", "KANGAROO", "ZEBRA", "TIGER", "LION", "MONKEY", "PANDA"],
    "fruits": ["APPLE", "BANANA", "ORANGE", "MANGO", "GRAPE", "PINEAPPLE", "STRAWBERRY", "KIWI", "WATERMELON"],
    "countries": ["INDIA", "JAPAN", "BRAZIL", "FRANCE", "AUSTRALIA", "CANADA", "EGYPT", "MEXICO", "ITALY", "SPAIN"],
}

# Hangman ASCII art stages
HANGMAN_STAGES = [
    """
    --------
    |      |
    |      
    |    
    |     
    |    
    ---------
    """,
    """
    --------
    |      |
    |      O
    |    
    |     
    |    
    ---------
    """,
    """
    --------
    |      |
    |      O
    |      |
    |     
    |    
    ---------
    """,
    """
    --------
    |      |
    |      O
    |     /|
    |     
    |    
    ---------
    """,
    """
    --------
    |      |
    |      O
    |     /|\\
    |     
    |    
    ---------
    """,
    """
    --------
    |      |
    |      O
    |     /|\\
    |     / 
    |    
    ---------
    """,
    """
    --------
    |      |
    |      O
    |     /|\\
    |     / \\
    |    
    ---------
    """
]

# Store active games: {chat_id: {word: str, guessed: set, mistakes: int, message_id: int}}
active_games: Dict[int, dict] = {}

def create_word_display(word: str, guessed: set) -> str:
    """Create the word display with guessed letters filled in"""
    return " ".join(letter if letter in guessed else "_" for letter in word)

def create_game_message(chat_id: int) -> str:
    """Create the game status message"""
    game = active_games[chat_id]
    word_display = create_word_display(game["word"], game["guessed"])
    return f"""
🎮 **Hangman Game**
{HANGMAN_STAGES[game["mistakes"]]}
📝 Word: `{word_display}`
❌ Mistakes: {game["mistakes"]}/6
🔤 Guessed Letters: {", ".join(sorted(game["guessed"])) or "None"}
"""

def create_keyboard() -> InlineKeyboardMarkup:
    """Create the letter selection keyboard"""
    keyboard = []
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    row = []
    for i, letter in enumerate(letters):
        row.append(InlineKeyboardButton(letter, callback_data=f"hangman_letter_{letter}"))
        if len(row) == 7:  # 7 letters per row
            keyboard.append(row)
            row = []
    if row:  # Add any remaining letters
        keyboard.append(row)
    # Add game control buttons
    keyboard.append([
        InlineKeyboardButton("🔄 New Game", callback_data="hangman_new"),
        InlineKeyboardButton("❌ End Game", callback_data="hangman_end")
    ])
    return InlineKeyboardMarkup(keyboard)

@app.on_message(filters.command("hangman") & filters.group)
async def start_hangman(_, message: Message):
    chat_id = message.chat.id
    
    # Check if there's already a game in this chat
    if chat_id in active_games:
        await message.reply_text("❗ A game is already in progress in this chat!")
        return

    # Start new game
    category = random.choice(list(WORD_CATEGORIES.keys()))
    word = random.choice(WORD_CATEGORIES[category])
    active_games[chat_id] = {
        "word": word,
        "guessed": set(),
        "mistakes": 0,
        "message_id": None,
        "category": category
    }
    
    game_message = await message.reply_text(
        f"""
🎮 **New Hangman Game Started!**
📑 Category: {category.title()}
{create_game_message(chat_id)}
""",
        reply_markup=create_keyboard()
    )
    active_games[chat_id]["message_id"] = game_message.id

@app.on_callback_query(filters.regex("^hangman_"))
async def handle_hangman_button(_, query: CallbackQuery):
    chat_id = query.message.chat.id
    user_id = query.from_user.id
    
    if chat_id not in active_games:
        await query.answer("No active game in this chat!", show_alert=True)
        return
    
    data = query.data.split("_")[1]
    game = active_games[chat_id]
    
    if data == "new":
        # Start new game
        category = random.choice(list(WORD_CATEGORIES.keys()))
        word = random.choice(WORD_CATEGORIES[category])
        active_games[chat_id] = {
            "word": word,
            "guessed": set(),
            "mistakes": 0,
            "message_id": game["message_id"],
            "category": category
        }
        await query.message.edit_text(
            f"""
🎮 **New Hangman Game Started!**
📑 Category: {category.title()}
{create_game_message(chat_id)}
""",
            reply_markup=create_keyboard()
        )
    
    elif data == "end":
        # End the game
        word = game["word"]
        await query.message.edit_text(
            f"""
❌ **Game Ended!**
The word was: **{word}**
""",
            reply_markup=None
        )
        del active_games[chat_id]
    
    elif data.startswith("letter_"):
        letter = data.split("_")[1]
        
        if letter in game["guessed"]:
            await query.answer("You already guessed that letter!", show_alert=True)
            return
        
        game["guessed"].add(letter)
        
        if letter not in game["word"]:
            game["mistakes"] += 1
        
        # Check game status
        word_completed = all(letter in game["guessed"] for letter in game["word"])
        game_over = game["mistakes"] >= 6
        
        if word_completed or game_over:
            result_message = f"""
🎮 **Game Over!**
{'🎉 You won!' if word_completed else '😔 You lost!'}
The word was: **{game["word"]}**
Category: {game["category"].title()}
"""
            await query.message.edit_text(result_message, reply_markup=None)
            del active_games[chat_id]
        else:
            await query.message.edit_text(
                f"""
🎮 **Hangman Game**
📑 Category: {game["category"].title()}
{create_game_message(chat_id)}
""",
                reply_markup=create_keyboard()
            )
    
    await query.answer()

# Help command
@app.on_message(filters.command("hangmanhelp"))
async def hangman_help(_, message: Message):
    help_text = """
🎮 **Hangman Game Help**

**Commands:**
• /hangman - Start a new game
• /hangmanhelp - Show this help message

**How to Play:**
1. Use /hangman to start a new game
2. A random word will be chosen from a category
3. Click letters to guess the word
4. You can make 6 mistakes before losing
5. Guess the word before the hangman is complete!

**Game Controls:**
• Click letters to make guesses
• Use '🔄 New Game' to start over
• Use '❌ End Game' to stop playing

Have fun playing! 🎯
"""
    await message.reply_text(help_text) 