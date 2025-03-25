import random
import asyncio
import time
from typing import Dict, List, Set
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from AviaxMusic import app
from AviaxMusic.misc import SUDOERS
from AviaxMusic.utils.database import get_lang
from strings import get_string

# Word categories and their corresponding words
WORD_CATEGORIES = {
    "animals": ["ELEPHANT", "GIRAFFE", "PENGUIN", "DOLPHIN", "KANGAROO", "ZEBRA", "TIGER", "LION", "MONKEY", "PANDA", "KOALA", "CHEETAH", "WOLF"],
    "fruits": ["APPLE", "BANANA", "ORANGE", "MANGO", "GRAPE", "PINEAPPLE", "STRAWBERRY", "KIWI", "WATERMELON", "PEACH", "CHERRY", "BLUEBERRY"],
    "countries": ["INDIA", "JAPAN", "BRAZIL", "FRANCE", "AUSTRALIA", "CANADA", "EGYPT", "MEXICO", "ITALY", "SPAIN", "GERMANY", "RUSSIA", "CHINA"],
    "sports": ["FOOTBALL", "CRICKET", "BASKETBALL", "TENNIS", "SWIMMING", "HOCKEY", "VOLLEYBALL", "BOXING", "GOLF", "RUGBY", "BASEBALL"],
    "movies": ["AVATAR", "TITANIC", "INCEPTION", "JOKER", "AVENGERS", "MATRIX", "INTERSTELLAR", "PARASITE", "FROZEN", "GLADIATOR"],
    "colors": ["RED", "BLUE", "GREEN", "YELLOW", "PURPLE", "ORANGE", "BLACK", "WHITE", "BROWN", "PINK", "VIOLET", "INDIGO", "GRAY"],
}

# Modern hangman stages with emoji
HANGMAN_STAGES = [
    """
    🏗️
    
    
    
    
    
    """,
    """
    🏗️
    😟
    
    
    
    
    """,
    """
    🏗️
    😟
    👕
    
    
    
    """,
    """
    🏗️
    😟
    👕
    👖
    
    
    """,
    """
    🏗️
    😨
    👕
    👖
    👞
    
    """,
    """
    🏗️
    😱
    👕
    👖
    👞👞
    
    """,
    """
    🏗️
    😵
    👕
    👖
    👞👞
    GAME OVER
    """
]

# Store active games: {chat_id: {word: str, guessed: set, mistakes: int, message_id: int, players: Set[int], current_player: int, start_time: float}}
active_games: Dict[int, dict] = {}
player_scores: Dict[int, Dict[int, int]] = {}  # {chat_id: {user_id: score}}

def create_word_display(word: str, guessed: set) -> str:
    """Create the word display with guessed letters filled in"""
    return " ".join(letter if letter in guessed else "▪️" for letter in word)

def create_game_message(chat_id: int) -> str:
    """Create the game status message"""
    game = active_games[chat_id]
    word_display = create_word_display(game["word"], game["guessed"])
    
    # Format player list
    players_list = []
    for user_id in game["players"]:
        member = app.get_chat_member(chat_id, user_id)
        name = member.user.first_name
        # Add crown emoji for current player
        if user_id == game["current_player"]:
            players_list.append(f"👑 {name}")
        else:
            players_list.append(f"• {name}")
    
    players_text = "\n".join(players_list) if players_list else "No players yet"
    
    # Get current player name
    if game["current_player"]:
        member = app.get_chat_member(chat_id, game["current_player"])
        current_player = f"👑 {member.user.first_name}'s turn"
    else:
        current_player = "Waiting for players to join"
    
    # Calculate game time
    game_time = time.time() - game["start_time"]
    minutes = int(game_time // 60)
    seconds = int(game_time % 60)
    
    return f"""
🎮 **Hangman Game**

{HANGMAN_STAGES[game["mistakes"]]}
📝 Word: `{word_display}`
📊 Category: **{game["category"].title()}**
⏱️ Time: {minutes:02d}:{seconds:02d}
❌ Mistakes: {game["mistakes"]}/6
🔤 Guessed: {", ".join(sorted(game["guessed"])) or "None"}

{current_player}

👥 **Players:**
{players_text}
"""

def create_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    """Create the letter selection keyboard"""
    game = active_games[chat_id]
    keyboard = []
    
    # First row - Game info and controls
    keyboard.append([
        InlineKeyboardButton("👥 Join Game", callback_data="hangman_join"),
        InlineKeyboardButton("🔄 New Game", callback_data="hangman_new"),
        InlineKeyboardButton("❌ End Game", callback_data="hangman_end")
    ])
    
    # Letter rows - 7 letters per row
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    row = []
    
    for i, letter in enumerate(letters):
        # Gray out already guessed letters
        if letter in game["guessed"]:
            btn_text = f"✓ {letter}" if letter in game["word"] else f"✗ {letter}"
            row.append(InlineKeyboardButton(btn_text, callback_data=f"hangman_guessed"))
        else:
            row.append(InlineKeyboardButton(letter, callback_data=f"hangman_letter_{letter}"))
        
        if len(row) == 7:  # 7 letters per row
            keyboard.append(row)
            row = []
    
    if row:  # Add any remaining letters
        keyboard.append(row)
    
    # Add scores button
    if chat_id in player_scores and player_scores[chat_id]:
        keyboard.append([InlineKeyboardButton("🏆 Leaderboard", callback_data="hangman_scores")])
    
    return InlineKeyboardMarkup(keyboard)

@app.on_message(filters.command("hangman") & filters.group)
async def start_hangman(_, message: Message):
    chat_id = message.chat.id
    
    # Check if there's already a game in this chat
    if chat_id in active_games:
        await message.reply_text(
            "❗ A game is already in progress in this chat!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➡️ Go to Game", callback_data="hangman_goto")]
            ])
        )
        return

    # Start new game
    category = random.choice(list(WORD_CATEGORIES.keys()))
    word = random.choice(WORD_CATEGORIES[category])
    
    # Initialize the game state
    active_games[chat_id] = {
        "word": word,
        "guessed": set(),
        "mistakes": 0,
        "message_id": None,
        "category": category,
        "players": set(),
        "current_player": None,
        "start_time": time.time()
    }
    
    # Initialize player scores if not exists
    if chat_id not in player_scores:
        player_scores[chat_id] = {}
    
    # Send the initial game message
    game_message = await message.reply_text(
        f"""
🎮 **New Hangman Game Started!**
📊 Category: **{category.title()}**

👥 **Players:** No players yet
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
    
    if chat_id not in active_games and query.data != "hangman_goto":
        await query.answer("No active game in this chat!", show_alert=True)
        return
    
    data = query.data.split("_")[1]
    
    if data == "goto":
        if chat_id in active_games:
            game = active_games[chat_id]
            try:
                # Try to redirect to the game message
                await query.message.delete()
                await app.send_message(
                    chat_id,
                    "Use the buttons below to play the game!",
                    reply_to_message_id=game["message_id"]
                )
            except Exception as e:
                print(f"Error redirecting to game: {e}")
                await query.answer("Couldn't find the game message.", show_alert=True)
        return
    
    game = active_games[chat_id]
    
    if data == "join":
        if user_id in game["players"]:
            await query.answer("You're already in the game!", show_alert=True)
            return
        
        # Add player to the game
        game["players"].add(user_id)
        
        # Set as current player if none
        if not game["current_player"]:
            game["current_player"] = user_id
        
        # Add player to scores if not exists
        if user_id not in player_scores[chat_id]:
            player_scores[chat_id][user_id] = 0
        
        # Update game message
        await query.message.edit_text(
            f"""
🎮 **Hangman Game**
📊 Category: **{game["category"].title()}**
{create_game_message(chat_id)}
""",
            reply_markup=create_keyboard(chat_id)
        )
        
        await query.answer(f"Welcome to the game, {query.from_user.first_name}!")
    
    elif data == "new":
        # Check if user is in current game
        if not game["players"] or user_id in game["players"]:
            # Start new game
            category = random.choice(list(WORD_CATEGORIES.keys()))
            word = random.choice(WORD_CATEGORIES[category])
            
            # Reset game state
            active_games[chat_id] = {
                "word": word,
                "guessed": set(),
                "mistakes": 0,
                "message_id": game["message_id"],
                "category": category,
                "players": set(),
                "current_player": None,
                "start_time": time.time()
            }
            
            # Update game message
            await query.message.edit_text(
                f"""
🎮 **New Hangman Game Started!**
📊 Category: **{category.title()}**

👥 **Players:** No players yet
Click "Join Game" to participate!

{create_game_message(chat_id)}
""",
                reply_markup=create_keyboard(chat_id)
            )
            
            await query.answer("New game started!")
        else:
            await query.answer("Only players in the current game can start a new one!", show_alert=True)
    
    elif data == "end":
        # Check if user is in current game
        if not game["players"] or user_id in game["players"]:
            # End the game and show scores
            word = game["word"]
            
            # Format scores
            scores_text = ""
            if chat_id in player_scores and player_scores[chat_id]:
                scores = sorted(player_scores[chat_id].items(), key=lambda x: x[1], reverse=True)
                scores_text = "\n".join([
                    f"{'🥇' if i==0 else '🥈' if i==1 else '🥉' if i==2 else '•'} {app.get_chat_member(chat_id, uid).user.first_name}: {score}" 
                    for i, (uid, score) in enumerate(scores[:10])  # Show top 10
                ])
            
            # Calculate game duration
            game_duration = time.time() - game["start_time"]
            minutes = int(game_duration // 60)
            seconds = int(game_duration % 60)
            
            await query.message.edit_text(
                f"""
❌ **Game Ended!**
The word was: **{word}**
⏱️ Game duration: {minutes:02d}:{seconds:02d}

🏆 **Final Scores:**
{scores_text if scores_text else "No scores recorded yet"}
""",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 New Game", callback_data="hangman_new")],
                    [InlineKeyboardButton("❌ Close", callback_data="close")]
                ])
            )
            
            # Keep the message_id for reference but remove from active games
            del active_games[chat_id]
            await query.answer("Game ended!")
        else:
            await query.answer("Only players in the current game can end it!", show_alert=True)
    
    elif data == "scores":
        if chat_id not in player_scores or not player_scores[chat_id]:
            await query.answer("No scores yet!", show_alert=True)
            return
        
        # Format scores with medals
        scores = sorted(player_scores[chat_id].items(), key=lambda x: x[1], reverse=True)
        scores_text = "\n".join([
            f"{'🥇' if i==0 else '🥈' if i==1 else '🥉' if i==2 else '•'} {app.get_chat_member(chat_id, uid).user.first_name}: {score}" 
            for i, (uid, score) in enumerate(scores[:10])  # Show top 10
        ])
        
        await query.message.reply_text(
            f"""
🏆 **Hangman Leaderboard**

{scores_text}
""",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Game", callback_data="hangman_back")]
            ])
        )
        
        await query.answer()
    
    elif data == "back":
        await query.message.delete()
        await query.answer()
    
    elif data == "guessed":
        await query.answer("This letter has already been guessed!", show_alert=True)
    
    elif data.startswith("letter_"):
        # Check if it's the player's turn
        if user_id != game["current_player"]:
            await query.answer("It's not your turn!", show_alert=True)
            return
        
        # Get the guessed letter
        letter = data.split("_")[1]
        
        # Check if already guessed
        if letter in game["guessed"]:
            await query.answer("You already guessed that letter!", show_alert=True)
            return
        
        # Add to guessed letters
        game["guessed"].add(letter)
        
        # Check if letter is in the word
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
            
            # Calculate game duration
            game_duration = time.time() - game["start_time"]
            minutes = int(game_duration // 60)
            seconds = int(game_duration % 60)
            
            # Update player score based on result
            if word_completed:
                # Bonus points for fast solving and few mistakes
                time_bonus = max(0, 5 - minutes)
                mistake_bonus = 6 - game["mistakes"]
                total_bonus = 10 + time_bonus + mistake_bonus
                
                player_scores[chat_id][user_id] += total_bonus
                
                result_message = f"""
🎮 **Game Over!**
🎉 {query.from_user.first_name} won!
The word was: **{game["word"]}**
📊 Category: **{game["category"].title()}**
⏱️ Game duration: {minutes:02d}:{seconds:02d}

🎯 +{total_bonus} points awarded!

🏆 **Leaderboard:**
{chr(10).join([f"{'🥇' if i==0 else '🥈' if i==1 else '🥉' if i==2 else '•'} {app.get_chat_member(chat_id, uid).user.first_name}: {score}" for i, (uid, score) in enumerate(sorted(player_scores[chat_id].items(), key=lambda x: x[1], reverse=True)[:5])])}
"""
            else:
                # Smaller penalty for losing
                player_scores[chat_id][user_id] -= 3
                
                result_message = f"""
🎮 **Game Over!**
😵 {query.from_user.first_name} lost!
The word was: **{game["word"]}**
📊 Category: **{game["category"].title()}**
⏱️ Game duration: {minutes:02d}:{seconds:02d}

🎯 -3 points penalty

🏆 **Leaderboard:**
{chr(10).join([f"{'🥇' if i==0 else '🥈' if i==1 else '🥉' if i==2 else '•'} {app.get_chat_member(chat_id, uid).user.first_name}: {score}" for i, (uid, score) in enumerate(sorted(player_scores[chat_id].items(), key=lambda x: x[1], reverse=True)[:5])])}
"""

            # Update message with result
            await query.message.edit_text(
                result_message,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 New Game", callback_data="hangman_new")],
                    [InlineKeyboardButton("❌ Close", callback_data="close")]
                ])
            )
            
            # Remove from active games
            del active_games[chat_id]
        else:
            # Move to next player if there are multiple players
            if len(game["players"]) > 1:
                players_list = list(game["players"])
                current_index = players_list.index(user_id)
                next_index = (current_index + 1) % len(players_list)
                game["current_player"] = players_list[next_index]
            
            # Update game message
            await query.message.edit_text(
                f"""
🎮 **Hangman Game**
📊 Category: **{game["category"].title()}**
{create_game_message(chat_id)}
""",
                reply_markup=create_keyboard(chat_id)
            )
        
        # Acknowledge the action
        if letter in game["word"]:
            await query.answer(f"Good guess! '{letter}' is in the word.")
        else:
            await query.answer(f"Oops! '{letter}' is not in the word.")
    
    else:
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
2. Click "👥 Join Game" to participate
3. Players take turns guessing letters
4. Guess the word before completing the hangman figure

**Scoring System:**
• Win: +10 points (base) + time bonus + mistake bonus
• Lose: -3 points penalty

**Game Features:**
• Multiple players with turn-based gameplay
• Visual letter tracking
• Score leaderboard with medals
• Game timer
• Multiple word categories

**Word Categories:**
• Animals
• Fruits
• Countries
• Sports
• Movies
• Colors

Have fun playing! 🎯
"""
    await message.reply_text(
        help_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎮 Start Game", callback_data="start_hangman")]
        ])
    ) 