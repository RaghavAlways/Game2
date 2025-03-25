import random
import asyncio
import re
from typing import Dict, List, Set
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import UserNotParticipant, FloodWait
from AviaxMusic import app
from AviaxMusic.misc import SUDOERS

# Word list for 5-letter words
WORD_LIST = [
    "APPLE", "BEACH", "BRAIN", "BRAVE", "CLOUD", "DANCE", "EARTH", "FEVER", "FIELD", "FLAME",
    "FRESH", "FROST", "GHOST", "GLORY", "GRASS", "GREAT", "HEART", "HEAVY", "HOUSE", "HAPPY",
    "LIGHT", "LUCKY", "MAGIC", "MAJOR", "MOVIE", "MUSIC", "NIGHT", "OCEAN", "PARTY", "PIANO",
    "PLACE", "PLANT", "POWER", "PRIZE", "QUEEN", "QUICK", "RADIO", "RIVER", "ROBOT", "ROUND",
    "ROYAL", "SMILE", "SPACE", "SPORT", "STORM", "SWEET", "TABLE", "TIGER", "TOWER", "TRAIN",
    "VOICE", "WATER", "WORLD", "YOUTH", "ZEBRA", "ALIVE", "BLEND", "BOOST", "BROOK", "CHARM",
    "CREST", "DREAM", "DRIFT", "FRONT", "GLAZE", "GLEAM", "GLIDE", "GRAFT", "GRAPE", "GRAPH",
    "GRASP", "GRAVE", "GROVE", "HORSE", "IVORY", "JEWEL", "JUICE", "NOVEL", "PLUCK", "PRICE",
    "PRIDE", "PROOF", "QUIET", "RAZOR", "REPLY", "SOLAR", "SPARK", "SPEAK", "STAND", "STONE",
    "STYLE", "SUGAR", "TASTE", "THEME", "THING", "THROW", "TWIST", "VERSE", "WAGON", "WATCH"
]

# Dictionary to store active games: {chat_id: {word: str, attempts: List[str], players: Dict[int, int], current_player: int}}
active_games = {}

async def get_user_name(chat_id: int, user_id: int) -> str:
    """Safely get user name with error handling"""
    try:
        user = await app.get_chat_member(chat_id, user_id)
        return user.user.first_name
    except (UserNotParticipant, FloodWait) as e:
        if isinstance(e, FloodWait):
            await asyncio.sleep(e.x)
            return await get_user_name(chat_id, user_id)
        return "Unknown User"
    except Exception:
        return "Unknown User"

async def create_game_message(chat_id: int) -> str:
    """Create the game status message"""
    game = active_games[chat_id]
    word = game["word"]
    attempts = game["attempts"]
    
    # Format players
    players_list = []
    for user_id, score in sorted(game["players"].items(), key=lambda x: x[1], reverse=True):
        name = await get_user_name(chat_id, user_id)
        # Add crown emoji for current player
        if user_id == game.get("current_player"):
            players_list.append(f"👑 {name}: {score}")
        else:
            players_list.append(f"• {name}: {score}")
    
    players_text = "\n".join(players_list) if players_list else "No players yet"
    
    # Format attempts with colored squares
    attempts_text = ""
    for attempt in attempts:
        attempt_result = ""
        for i, letter in enumerate(attempt):
            if letter == word[i]:
                attempt_result += f"🟩 {letter} "  # Correct position
            elif letter in word:
                attempt_result += f"🟨 {letter} "  # In word but wrong position
            else:
                attempt_result += f"🟥 {letter} "  # Not in word
        attempts_text += f"{attempt_result}\n"
    
    # Calculate remaining guesses
    max_attempts = 30
    remaining = max_attempts - len(attempts)
    
    # Get current player name
    current_player_text = ""
    if game.get("current_player"):
        current_player_name = await get_user_name(chat_id, game["current_player"])
        current_player_text = f"\n🎮 Current Player: {current_player_name}"
    
    # Used letters tracking
    used_letters = set()
    for attempt in attempts:
        for letter in attempt:
            used_letters.add(letter)
            
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    remaining_letters = "".join([letter for letter in alphabet if letter not in used_letters])
    
    return f"""
🎮 **Wordle Game**

Word: `{len(word) * '_ '}` ({len(word)} letters)
Attempts: {len(attempts)}/{max_attempts}
Remaining: {remaining} guesses{current_player_text}

**Previous Attempts:**
{attempts_text if attempts else "No attempts yet"}

**Available Letters:**
`{' '.join(remaining_letters)}`

**Players:**
{players_text}

To guess, use: `/guess WORD`
"""

def check_word(guess: str, word: str) -> str:
    """Check guess against the word and return formatted result"""
    result = ""
    for i, letter in enumerate(guess):
        if letter == word[i]:
            result += "🟩"  # Correct position
        elif letter in word:
            result += "🟨"  # In word but wrong position
        else:
            result += "🟥"  # Not in word
    return result

@app.on_message(filters.command("wordle") & filters.group)
async def start_wordle(_, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Check if there's already a game in this chat
    if chat_id in active_games:
        await message.reply_text(
            "❗ A Wordle game is already in progress in this chat!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➡️ Show Game", callback_data="wordle_show")]
            ])
        )
        return

    # Start new game
    word = random.choice(WORD_LIST)
    
    # Initialize the game
    active_games[chat_id] = {
        "word": word,
        "attempts": [],
        "players": {user_id: 0},  # Initialize with the creator's score
        "current_player": user_id  # First player is the creator
    }
    
    # Send initial game message
    game_message = await message.reply_text(
        f"""
🎮 **New Wordle Game Started!**
Word length: **5 letters**

**How to Play:**
1. You have to guess a random 5-letter word.
2. After each guess, you'll get hints:
   - 🟩 - Correct letter in the right spot.
   - 🟨 - Correct letter in the wrong spot.
   - 🟥 - Letter not in the word.
3. The game will run until the word is found or a maximum of 30 guesses are reached.
4. The first person to guess the word correctly wins.

To make a guess, send: `/guess WORD`
{await create_game_message(chat_id)}
""",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Join Game", callback_data="wordle_join")],
            [InlineKeyboardButton("🚫 End Game", callback_data="wordle_end")]
        ])
    )
    
    # Store the message ID for updates
    active_games[chat_id]["message_id"] = game_message.id

@app.on_message(filters.command("guess") & filters.group)
async def make_guess(_, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Check if there's a game in progress
    if chat_id not in active_games:
        await message.reply_text("❌ No Wordle game in progress. Start one with /wordle")
        return
    
    # Check if user is a player
    if user_id not in active_games[chat_id]["players"]:
        await message.reply_text(
            "❌ You are not part of the game. Click 'Join Game' to participate.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 Join Game", callback_data="wordle_join")]
            ])
        )
        return
    
    # Check if it's the user's turn
    if user_id != active_games[chat_id]["current_player"]:
        current_player_name = await get_user_name(chat_id, active_games[chat_id]["current_player"])
        await message.reply_text(f"❌ It's not your turn. Wait for {current_player_name} to make a guess.")
        return
    
    # Get the guess
    if len(message.command) < 2:
        await message.reply_text("❗ Please provide a word with your guess: `/guess WORD`")
        return
    
    guess = message.command[1].upper()
    
    # Validate guess is only letters
    if not re.match(r'^[A-Za-z]+$', guess):
        await message.reply_text("❗ Your guess must contain only letters.")
        return
    
    # Validate guess length
    word = active_games[chat_id]["word"]
    if len(guess) != len(word):
        await message.reply_text(f"❗ Your guess must be {len(word)} letters long.")
        return
    
    # Add the guess to attempts
    active_games[chat_id]["attempts"].append(guess)
    
    # Check if the guess is correct
    if guess == word:
        # Update player's score
        active_games[chat_id]["players"][user_id] += 10
        
        # Format the final board
        attempts_count = len(active_games[chat_id]["attempts"])
        
        # Sort players by score
        sorted_players = sorted(
            active_games[chat_id]["players"].items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        players_text = []
        for i, (pid, score) in enumerate(sorted_players):
            try:
                player_name = await get_user_name(chat_id, pid)
                medal = '🥇' if i==0 else '🥈' if i==1 else '🥉' if i==2 else '•'
                players_text.append(f"{medal} {player_name}: {score}")
            except Exception:
                continue
        
        players_text_str = "\n".join(players_text)
        
        # Create winner message
        winner_message = f"""
🎮 **Wordle Game Completed!**

🎉 Congratulations! {message.from_user.first_name} guessed the word: **{word}**
✅ Solved in {attempts_count} attempts

**Final Leaderboard:**
{players_text_str}

**Play Again?** Use `/wordle` to start a new game!
"""
        
        # Send the winner message and clean up
        await message.reply_text(
            winner_message,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎮 New Game", callback_data="wordle_start")]
            ])
        )
        
        # Delete the game
        try:
            del active_games[chat_id]
        except KeyError:
            pass
        
        return
    
    # Update game message with the new attempt
    try:
        # Calculate next player (round-robin)
        players = list(active_games[chat_id]["players"].keys())
        current_idx = players.index(user_id)
        next_idx = (current_idx + 1) % len(players)
        active_games[chat_id]["current_player"] = players[next_idx]
    except (ValueError, IndexError):
        # Fallback if there's an issue with player management
        if players:
            active_games[chat_id]["current_player"] = players[0]
    
    # Check if max attempts reached
    if len(active_games[chat_id]["attempts"]) >= 30:
        # Game over - no one guessed correctly
        players_text = []
        for pid, score in active_games[chat_id]["players"].items():
            try:
                player_name = await get_user_name(chat_id, pid)
                players_text.append(f"• {player_name}: {score}")
            except Exception:
                continue
                
        players_text_str = "\n".join(players_text)
        
        game_over_message = f"""
🎮 **Wordle Game Over!**

❌ No one guessed the word: **{word}**
Max attempts (30) reached.

**Players:**
{players_text_str}

**Play Again?** Use `/wordle` to start a new game!
"""
        
        await message.reply_text(
            game_over_message,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎮 New Game", callback_data="wordle_start")]
            ])
        )
        
        # Delete the game
        try:
            del active_games[chat_id]
        except KeyError:
            pass
            
        return
    
    # Show updated game status
    result = check_word(guess, word)
    game_message = f"""
🔤 {message.from_user.first_name} guessed: **{guess}**
{result}

{await create_game_message(chat_id)}
"""
    
    await message.reply_text(
        game_message,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Join Game", callback_data="wordle_join")],
            [InlineKeyboardButton("🚫 End Game", callback_data="wordle_end")]
        ])
    )

@app.on_callback_query(filters.regex("^wordle_"))
async def wordle_callback(_, query: CallbackQuery):
    chat_id = query.message.chat.id
    user_id = query.from_user.id
    data = query.data.split("_")[1]
    
    # Show game
    if data == "show":
        if chat_id not in active_games:
            await query.answer("The game has ended or doesn't exist anymore.", show_alert=True)
            return
        
        try:
            await query.message.reply_text(
                f"**Current Wordle Game:**\n\n{await create_game_message(chat_id)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔍 Join Game", callback_data="wordle_join")],
                    [InlineKeyboardButton("🚫 End Game", callback_data="wordle_end")]
                ])
            )
            await query.answer()
        except Exception as e:
            print(f"Error showing game: {e}")
            await query.answer("Error showing game. Try again.", show_alert=True)
    
    # Join game
    elif data == "join":
        if chat_id not in active_games:
            await query.answer("The game has ended or doesn't exist anymore.", show_alert=True)
            return
        
        # Add user to players if not already in
        if user_id not in active_games[chat_id]["players"]:
            active_games[chat_id]["players"][user_id] = 0
            
            # If there's no current player, make this user the current player
            if not active_games[chat_id].get("current_player"):
                active_games[chat_id]["current_player"] = user_id
            
            try:
                await query.message.reply_text(
                    f"**{query.from_user.first_name}** has joined the Wordle game!\n\n{await create_game_message(chat_id)}",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔍 Join Game", callback_data="wordle_join")],
                        [InlineKeyboardButton("🚫 End Game", callback_data="wordle_end")]
                    ])
                )
                await query.answer(f"You joined the game! When it's your turn, use /guess WORD to play.")
            except Exception as e:
                print(f"Error joining game: {e}")
                await query.answer("Error joining game. Try again.", show_alert=True)
        else:
            await query.answer("You're already in the game!", show_alert=True)
    
    # End game
    elif data == "end":
        if chat_id not in active_games:
            await query.answer("The game has already ended.", show_alert=True)
            return
        
        # Check if user is in the game
        if user_id not in active_games[chat_id]["players"] and user_id not in SUDOERS:
            await query.answer("Only players or admins can end the game!", show_alert=True)
            return
        
        word = active_games[chat_id]["word"]
        
        end_message = f"""
🎮 **Wordle Game Ended!**

The word was: **{word}**

Game ended by: {query.from_user.first_name}
"""
        
        try:
            await query.message.reply_text(
                end_message,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎮 New Game", callback_data="wordle_start")]
                ])
            )
            
            # Delete the game
            try:
                del active_games[chat_id]
            except KeyError:
                pass
                
            await query.answer("Game ended!")
        except Exception as e:
            print(f"Error ending game: {e}")
            await query.answer("Error ending game. Try again.", show_alert=True)
    
    # Handle wordle_start callback
    elif data == "start":
        try:
            # Simulate /wordle command
            message = query.message
            message.command = ["wordle"]
            message.from_user = query.from_user
            await start_wordle(_, message)
            await query.answer()
        except Exception as e:
            print(f"Error starting game: {e}")
            await query.answer("Error starting game. Try again.", show_alert=True)
    
    else:
        await query.answer()

@app.on_message(filters.command("wordlehelp"))
async def wordle_help(_, message: Message):
    help_text = """
🎮 **Wordle Game Help**

**Commands:**
• /wordle - Start a new Wordle game
• /guess WORD - Make a guess in an active game
• /wordlehelp - Show this help message

**How to Play:**
1. You have to guess a random 5-letter word.
2. After each guess, you'll get hints:
   - 🟩 - Correct letter in the right spot.
   - 🟨 - Correct letter in the wrong spot.
   - 🟥 - Letter not in the word.
3. The game will run until the word is found or a maximum of 30 guesses are reached.
4. The first person to guess the word correctly wins.
5. Players take turns making guesses.

**Scoring:**
• +10 points for correctly guessing the word

Have fun playing! 🎯
"""
    await message.reply_text(
        help_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎮 Start Game", callback_data="wordle_start")]
        ])
    )

@app.on_callback_query(filters.regex("^wordle_start$"))
async def start_wordle_callback(_, query: CallbackQuery):
    message = query.message
    message.command = ["wordle"]
    message.from_user = query.from_user
    await start_wordle(_, message)
    await query.answer() 