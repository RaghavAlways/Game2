import random
import asyncio
from typing import Dict, List, Set
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

# Store active games: {chat_id: {word: str, guessed: set, mistakes: int, message_id: int, players: Set[int], current_player: int}}
active_games: Dict[int, dict] = {}
player_scores: Dict[int, Dict[int, int]] = {}  # {chat_id: {user_id: score}}

def create_word_display(word: str, guessed: set) -> str:
    """Create the word display with guessed letters filled in"""
    return " ".join(letter if letter in guessed else "_" for letter in word)

def create_game_message(chat_id: int) -> str:
    """Create the game status message"""
    game = active_games[chat_id]
    word_display = create_word_display(game["word"], game["guessed"])
    players_text = "\n".join([f"• {app.get_chat_member(chat_id, user_id).user.first_name}" for user_id in game["players"]])
    current_player = app.get_chat_member(chat_id, game["current_player"]).user.first_name
    
    return f"""
🎮 **Hangman Game**
{HANGMAN_STAGES[game["mistakes"]]}
📝 Word: `{word_display}`
❌ Mistakes: {game["mistakes"]}/6
🔤 Guessed Letters: {", ".join(sorted(game["guessed"])) or "None"}

👥 Players:
{players_text}

🎯 Current Turn: {current_player}
"""

def create_keyboard(chat_id: int) -> InlineKeyboardMarkup:
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
        InlineKeyboardButton("👥 Join Game", callback_data="hangman_join"),
        InlineKeyboardButton("🔄 New Game", callback_data="hangman_new"),
        InlineKeyboardButton("❌ End Game", callback_data="hangman_end")
    ])
    
    # Add scores button if there are scores
    if chat_id in player_scores:
        keyboard.append([InlineKeyboardButton("🏆 Scores", callback_data="hangman_scores")])
    
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
        "category": category,
        "players": set(),
        "current_player": None
    }
    
    game_message = await message.reply_text(
        f"""
🎮 **New Hangman Game Started!**
📑 Category: {category.title()}

👥 Players: None
Click "Join Game" to participate!

{create_game_message(chat_id)}
""",
        reply_markup=create_keyboard(chat_id)
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
    
    if data == "join":
        if user_id in game["players"]:
            await query.answer("You're already in the game!", show_alert=True)
            return
        
        game["players"].add(user_id)
        if not game["current_player"]:
            game["current_player"] = user_id
        
        await query.message.edit_text(
            f"""
🎮 **Hangman Game**
📑 Category: {game["category"].title()}
{create_game_message(chat_id)}
""",
            reply_markup=create_keyboard(chat_id)
        )
        await query.answer(f"Welcome to the game, {query.from_user.first_name}!")
    
    elif data == "new":
        # Start new game
        category = random.choice(list(WORD_CATEGORIES.keys()))
        word = random.choice(WORD_CATEGORIES[category])
        active_games[chat_id] = {
            "word": word,
            "guessed": set(),
            "mistakes": 0,
            "message_id": game["message_id"],
            "category": category,
            "players": set(),
            "current_player": None
        }
        await query.message.edit_text(
            f"""
🎮 **New Hangman Game Started!**
📑 Category: {category.title()}

👥 Players: None
Click "Join Game" to participate!

{create_game_message(chat_id)}
""",
            reply_markup=create_keyboard(chat_id)
        )
        await query.answer("New game started!")
    
    elif data == "end":
        # End the game and show scores
        word = game["word"]
        scores_text = ""
        if chat_id in player_scores:
            scores = sorted(player_scores[chat_id].items(), key=lambda x: x[1], reverse=True)
            scores_text = "\n".join([f"• {app.get_chat_member(chat_id, user_id).user.first_name}: {score}" for user_id, score in scores])
        
        await query.message.edit_text(
            f"""
❌ **Game Ended!**
The word was: **{word}**

🏆 **Final Scores:**
{scores_text if scores_text else "No scores yet"}
""",
            reply_markup=None
        )
        del active_games[chat_id]
        await query.answer("Game ended!")
    
    elif data == "scores":
        if chat_id not in player_scores:
            await query.answer("No scores yet!", show_alert=True)
            return
        
        scores = sorted(player_scores[chat_id].items(), key=lambda x: x[1], reverse=True)
        scores_text = "\n".join([f"• {app.get_chat_member(chat_id, user_id).user.first_name}: {score}" for user_id, score in scores])
        
        await query.message.reply_text(
            f"""
🏆 **Current Scores:**
{scores_text}
""",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back to Game", callback_data="hangman_back")]])
        )
        await query.answer()
    
    elif data == "back":
        await query.message.delete()
        await query.answer()
    
    elif data.startswith("letter_"):
        if user_id != game["current_player"]:
            await query.answer("It's not your turn!", show_alert=True)
            return
        
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
            # Update scores
            if chat_id not in player_scores:
                player_scores[chat_id] = {}
            if user_id not in player_scores[chat_id]:
                player_scores[chat_id][user_id] = 0
            
            if word_completed:
                player_scores[chat_id][user_id] += 10
                result_message = f"""
🎮 **Game Over!**
🎉 {query.from_user.first_name} won!
The word was: **{game["word"]}**
Category: {game["category"].title()}

🏆 **Current Scores:**
{chr(10).join([f"• {app.get_chat_member(chat_id, uid).user.first_name}: {score}" for uid, score in player_scores[chat_id].items()])}
"""
            else:
                player_scores[chat_id][user_id] -= 5
                result_message = f"""
🎮 **Game Over!**
😔 {query.from_user.first_name} lost!
The word was: **{game["word"]}**
Category: {game["category"].title()}

🏆 **Current Scores:**
{chr(10).join([f"• {app.get_chat_member(chat_id, uid).user.first_name}: {score}" for uid, score in player_scores[chat_id].items()])}
"""
            await query.message.edit_text(result_message, reply_markup=create_keyboard(chat_id))
        else:
            # Move to next player
            players_list = list(game["players"])
            current_index = players_list.index(user_id)
            next_index = (current_index + 1) % len(players_list)
            game["current_player"] = players_list[next_index]
            
            await query.message.edit_text(
                f"""
🎮 **Hangman Game**
📑 Category: {game["category"].title()}
{create_game_message(chat_id)}
""",
                reply_markup=create_keyboard(chat_id)
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
2. Players must click "Join Game" to participate
3. A random word will be chosen from a category
4. Players take turns clicking letters to guess the word
5. You can make 6 mistakes before losing
6. Guess the word before the hangman is complete!

**Scoring:**
• +10 points for correctly guessing the word
• -5 points for losing the game

**Game Controls:**
• Click letters to make guesses
• Use '🔄 New Game' to start over
• Use '❌ End Game' to stop playing
• Use '🏆 Scores' to view current scores

Have fun playing! 🎯
"""
    await message.reply_text(help_text) 