import random
import asyncio
import re
import time
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

# Add more popular 5-letter words that are common and fun to guess
POPULAR_WORDS = [
    "ABOUT", "ABOVE", "ACTOR", "ADAPT", "AFTER", "AGAIN", "AGREE", "ALBUM", 
    "ALONE", "ALONG", "AMONG", "ANGEL", "ANGER", "ANGLE", "ANGRY", "ANIME", 
    "ANKLE", "APART", "APPLE", "ARGUE", "ARISE", "ARROW", "ASSET", "AUDIT", 
    "AVOID", "AWARD", "AWARE", "BACON", "BADGE", "BAGEL", "BAKER", "BASIC", 
    "BEACH", "BEARD", "BEAST", "BEGIN", "BEING", "BELOW", "BENCH", "BIRTH", 
    "BLACK", "BLADE", "BLAME", "BLANK", "BLAST", "BLAZE", "BLEND", "BLESS", 
    "BLIND", "BLOCK", "BLOOD", "BLOOM", "BLUES", "BLUFF", "BLUNT", "BOARD", 
    "BOOST", "BOOTH", "BRAVE", "BREAD", "BREAK", "BRIDE", "BRIEF", "BRING", 
    "BROAD", "BROWN", "BRUSH", "BUILD", "BUNCH", "BURST", "CABIN", "CABLE", 
    "CANDY", "CARGO", "CARRY", "CATCH", "CAUSE", "CHAIN", "CHAIR", "CHALK", 
    "CHARM", "CHART", "CHASE", "CHEAP", "CHECK", "CHEST", "CHIEF", "CHILD", 
    "CHILL", "CHIPS", "CHOIR", "CHORD", "CLAIM", "CLASS", "CLEAN", "CLEAR", 
    "CLIMB", "CLOCK", "CLOSE", "CLOUD", "CLOWN", "COACH", "COAST", "COLOR"
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

async def create_game_message(chat_id, available_letters=None, extra_text="", hints_used=0):
    """Create the game status message with the current game state"""
    game_data = active_games.get(chat_id, {})
    
    # Update last activity timestamp
    game_data["last_activity"] = time.time()
    
    if not game_data:
        return None
    
    word = game_data.get("word", "")
    attempts = game_data.get("attempts", [])
    players = game_data.get("players", {})
    
    if not available_letters:
        available_letters = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    
    # Format the word display with proper spacing - show only guessed letters
    displayed_word = ""
    for char in word:
        if char.upper() in game_data.get("correct_letters", set()):
            displayed_word += f" {char.upper()} "
        else:
            displayed_word += " _ "
    
    # Format available letters with better spacing
    letters_display = ""
    for idx, letter in enumerate(available_letters):
        letters_display += f" {letter} "
        if (idx + 1) % 7 == 0 and idx < len(available_letters) - 1:
            letters_display += "\n"
    
    # Create the game status message
    message = (
        f"🎮 **WORDLE GAME**\n\n"
        f"Word: `{displayed_word.strip()}`\n\n"
        f"Attempts: {len(attempts)}/6\n"
        f"Players: {len(players)}\n"
        f"Hints Used: {hints_used}/3\n\n"
        f"Available Letters:\n`{letters_display}`\n\n"
    )
    
    if extra_text:
        message += f"{extra_text}\n\n"
    
    message += (
        "Make a guess with /guess [word]\n"
        "For example: `/guess hello`"
    )
    
    # Create the markup with join and hint buttons, add recovery button for admins
    markup = [
        [
            InlineKeyboardButton("Join Game", callback_data="join_wordle"),
            InlineKeyboardButton("Hint", callback_data="wordle_hint")
        ]
    ]
    
    # Add the recovery button at the bottom
    markup.append([InlineKeyboardButton("🔄 Reset Game (Admin)", callback_data="game_error_recovery")])
    
    return message, InlineKeyboardMarkup(markup)

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

    # Start new game - use popular words 70% of the time for better gameplay
    if random.random() < 0.7 and POPULAR_WORDS:
        word = random.choice(POPULAR_WORDS)
    else:
        word = random.choice(WORD_LIST)
    
    # Initialize the game
    active_games[chat_id] = {
        "word": word,
        "attempts": [],
        "players": {user_id: 0},  # Initialize with the creator's score
        "current_player": user_id,  # First player is the creator
        "hints_used": 0,  # Track hints usage
        "start_time": int(time.time())  # Track game start time
    }
    
    # Generate game status message first
    status_message = await create_game_message(chat_id)
    
    # Send initial game message with clear separation
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

{status_message}
""",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔍 Join Game", callback_data="wordle_join"),
                InlineKeyboardButton("💡 Hint", callback_data="wordle_hint")
            ],
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

@app.on_callback_query(filters.regex("wordle_start"))
async def start_wordle_callback(_, query: CallbackQuery):
    """Handler for starting a new game via callback button"""
    try:
        # Answer the callback to acknowledge the button press
        await query.answer("Starting a new Wordle game...")
        
        # Create a proper message object for start_wordle
        message = query.message
        message.command = ["wordle"]
        message.from_user = query.from_user
        
        # Log the game start attempt
        print(f"Starting wordle game from callback button. User: {message.from_user.id}, Chat: {message.chat.id}")
        
        # Call the start_wordle function
        await start_wordle(_, message)
    except Exception as e:
        print(f"Error in wordle_start callback: {str(e)}")
        await query.answer(f"Error starting new game: {str(e)[:50]}... Try /wordle command instead.", show_alert=True)

@app.on_callback_query(filters.regex("wordle_join"))
async def join_wordle_callback(_, query: CallbackQuery):
    """Handler for joining a Wordle game"""
    try:
        chat_id = query.message.chat.id
        user_id = query.from_user.id
        
        # Check if there's a game in progress
        if chat_id not in active_games:
            await query.answer("No active game found. Start a new game with /wordle", show_alert=True)
            return
        
        # Check if user is already a player
        if user_id in active_games[chat_id]["players"]:
            await query.answer("You're already part of this game!", show_alert=True)
            return
        
        # Add user to players
        active_games[chat_id]["players"][user_id] = 0
        
        # Get player name
        player_name = query.from_user.first_name
        
        # Update game message
        try:
            # Get updated game status with the new player
            updated_message = await create_game_message(chat_id)
            
            # Edit the message to reflect new player joining
            await query.message.edit_text(
                f"""
🎮 **Wordle Game in Progress**
Word length: **5 letters**

**How to Play:**
1. You have to guess a random 5-letter word.
2. After each guess, you'll get hints:
   - 🟩 - Correct letter in the right spot.
   - 🟨 - Correct letter in the wrong spot.
   - 🟥 - Letter not in the word.
3. The game will run until the word is found or a maximum of 30 guesses are reached.

💡 {player_name} has joined the game!

To make a guess, send: `/guess WORD`

{updated_message}
""",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔍 Join Game", callback_data="wordle_join"),
                        InlineKeyboardButton("💡 Hint", callback_data="wordle_hint")
                    ],
                    [InlineKeyboardButton("🚫 End Game", callback_data="wordle_end")]
                ])
            )
            
            # Show confirmation to user
            await query.answer(f"You've joined the game! When it's your turn, use /guess WORD to play.", show_alert=True)
            
            # Also send a separate notification message for better visibility
            await query.message.reply_text(f"**{player_name}** has joined the Wordle game!")
            
        except Exception as e:
            print(f"Error updating game message after joining: {e}")
            await query.answer("Joined the game, but couldn't update message.", show_alert=True)
            
    except Exception as e:
        print(f"Error in join_wordle callback: {e}")
        await query.answer("Error joining game. Try again.", show_alert=True)

@app.on_callback_query(filters.regex("wordle_show"))
async def show_wordle_callback(_, query: CallbackQuery):
    """Handler for showing the current Wordle game status"""
    try:
        chat_id = query.message.chat.id
        
        # Check if there's a game in progress
        if chat_id not in active_games:
            await query.answer("No game in progress. Start a new game with /wordle", show_alert=True)
            return
        
        # Update game message
        updated_message = await create_game_message(chat_id)
        await query.message.edit_text(
            f"""
🎮 **Wordle Game in Progress**
Word length: **5 letters**

**How to Play:**
1. You have to guess a random 5-letter word.
2. After each guess, you'll get hints:
   - 🟩 - Correct letter in the right spot.
   - 🟨 - Correct letter in the wrong spot.
   - 🟥 - Letter not in the word.
3. The game will run until the word is found or a maximum of 30 guesses are reached.

To make a guess, send: `/guess WORD`
{updated_message}
""",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 Join Game", callback_data="wordle_join")],
                [InlineKeyboardButton("🚫 End Game", callback_data="wordle_end")]
            ])
        )
        
        await query.answer("Game status updated!")
    except Exception as e:
        print(f"Error in show_wordle callback: {e}")
        await query.answer("Error showing game. Try again.", show_alert=True)

@app.on_callback_query(filters.regex("wordle_end"))
async def end_wordle_callback(_, query: CallbackQuery):
    """Handler for ending a Wordle game"""
    try:
        chat_id = query.message.chat.id
        user_id = query.from_user.id
        
        # Check if there's a game in progress
        if chat_id not in active_games:
            await query.answer("No game in progress to end.", show_alert=True)
            return
        
        # Only allow game creator or admins to end the game
        game_creator = list(active_games[chat_id]["players"].keys())[0] if active_games[chat_id]["players"] else None
        
        if user_id != game_creator:
            # Check if user is admin
            try:
                member = await app.get_chat_member(chat_id, user_id)
                is_admin = member.status in ("creator", "administrator")
                if not is_admin:
                    await query.answer("Only the game creator or admins can end the game.", show_alert=True)
                    return
            except Exception:
                await query.answer("Only the game creator or admins can end the game.", show_alert=True)
                return
        
        # Get the word
        word = active_games[chat_id]["word"]
        
        # Format players
        players_text = []
        for pid, score in sorted(active_games[chat_id]["players"].items(), key=lambda x: x[1], reverse=True):
            try:
                player_name = await get_user_name(chat_id, pid)
                players_text.append(f"• {player_name}: {score}")
            except Exception:
                continue
                
        players_text_str = "\n".join(players_text) if players_text else "No players"
        
        # Update game message
        await query.message.edit_text(
            f"""
🎮 **Wordle Game Ended**

The word was: **{word}**

**Final Scores:**
{players_text_str}

Start a new game with /wordle
""",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎮 New Game", callback_data="wordle_start")]
            ])
        )
        
        # Delete the game
        try:
            del active_games[chat_id]
        except KeyError:
            pass
        
        await query.answer("Game ended successfully!", show_alert=True)
    except Exception as e:
        print(f"Error in end_wordle callback: {e}")
        await query.answer("Error ending game. Try again.", show_alert=True)

@app.on_callback_query(filters.regex("wordle_hint"))
async def wordle_hint_callback(_, query: CallbackQuery):
    """Provide a hint for the current Wordle game"""
    try:
        chat_id = query.message.chat.id
        user_id = query.from_user.id
        
        # Check if there's a game in progress
        if chat_id not in active_games:
            await query.answer("No active game found. Start one with /wordle", show_alert=True)
            return
        
        # Allow anyone to use hints without joining first (more user-friendly)
        if user_id not in active_games[chat_id]["players"]:
            # Auto-join the user when they request a hint
            active_games[chat_id]["players"][user_id] = 0
            await query.answer("You've been added to the game!", show_alert=True)
        
        # Limit hints to 3 per game
        if active_games[chat_id].get("hints_used", 0) >= 3:
            await query.answer("Maximum hints (3) already used for this game!", show_alert=True)
            return
        
        # Get the current word and give a hint
        word = active_games[chat_id]["word"]
        attempts = active_games[chat_id]["attempts"]
        
        # Extended hint map with more common words
        hint_map = {
            "APPLE": "A common fruit that keeps the doctor away",
            "EARTH": "The planet we live on",
            "MUSIC": "Something you listen to that has rhythm and melody",
            "WATER": "Essential liquid for life",
            "DANCE": "Moving your body to music",
            "LIGHT": "The opposite of darkness",
            "HOUSE": "A place where people live",
            "DREAM": "What you see when you sleep",
            "HEART": "It pumps blood through your body",
            "BEACH": "Sandy shore by the ocean",
            "MOVIE": "Entertainment on a big screen",
            "SMILE": "Happy facial expression",
            "TIGER": "A large striped wild cat",
            "CLOUD": "White fluffy thing in the sky",
            "BRAIN": "Organ used for thinking",
            "PHONE": "Device used to call people",
            "HAPPY": "Feeling joy or pleasure",
            "GREEN": "The color of grass",
            "WORLD": "The planet we all live on",
            "PLANT": "Living organism that grows in soil",
            "RIVER": "Flowing body of water",
            "TABLE": "Furniture with a flat top and legs",
            "SWEET": "Taste like sugar",
            "BLOOD": "Red fluid in your veins",
            "BREAD": "Baked food made from flour",
            "CHILD": "Young human",
            "SPACE": "Area beyond Earth's atmosphere",
            "GHOST": "Spooky spirit",
            "STORM": "Weather with strong wind and rain",
            "QUEEN": "Female ruler of a kingdom",
            "MAGIC": "Supernatural powers",
            "PAPER": "Material used for writing",
            "METAL": "Strong materials like iron or gold",
            "SHARE": "Give a portion to others",
            "COLOR": "Visual property like red or blue",
            "MONEY": "Currency used to buy things",
        }
        
        # Determine hint type based on hints used so far
        hints_used = active_games[chat_id].get("hints_used", 0)
        
        if hints_used == 0:
            # First hint - reveal the first letter
            hint = f"The word starts with '{word[0]}'"
        elif hints_used == 1:
            # Second hint - give another letter position or definition hint
            if word in hint_map:
                # If we have a definition, use it
                hint = hint_map[word]
            else:
                # Otherwise give a letter position hint
                letter_pos = random.randint(1, len(word)-1)  # Not the first letter
                hint = f"The letter at position {letter_pos+1} is '{word[letter_pos]}'"
        else:
            # Third hint - more substantial 
            if len(attempts) > 0:
                # Analyze incorrect guesses to give more targeted hint
                all_correct_positions = set()
                for attempt in attempts:
                    for i, letter in enumerate(attempt):
                        if letter == word[i]:
                            all_correct_positions.add(i)
                
                # Find a position not yet guessed correctly 
                available_positions = [i for i in range(len(word)) if i not in all_correct_positions]
                
                if available_positions:
                    pos = random.choice(available_positions)
                    hint = f"The letter at position {pos+1} is '{word[pos]}'"
                else:
                    # All positions have been guessed correctly at some point
                    # Give a scrambled version of the word minus any correctly placed letters
                    letters = list(word)
                    random.shuffle(letters)
                    hint = f"The word contains these letters (scrambled): {''.join(letters)}"
            else:
                # No attempts yet, give the first two letters
                hint = f"The word starts with '{word[0:2]}'"
        
        # Increment hints used
        active_games[chat_id]["hints_used"] = hints_used + 1
        
        # Send the hint
        await query.answer(f"HINT: {hint}", show_alert=True)
        
        # Update the game message to show that a hint was used
        try:
            updated_message = await create_game_message(chat_id)
            hints_used = active_games[chat_id]["hints_used"]
            
            await query.message.edit_text(
                f"""
🎮 **Wordle Game in Progress**
Word length: **5 letters**

**How to Play:**
1. You have to guess a random 5-letter word.
2. After each guess, you'll get hints:
   - 🟩 - Correct letter in the right spot.
   - 🟨 - Correct letter in the wrong spot.
   - 🟥 - Letter not in the word.

💡 Hints used: {hints_used}/3 - Last hint: "{hint}"

To make a guess, send: `/guess WORD`

{updated_message}
""",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔍 Join Game", callback_data="wordle_join"),
                        InlineKeyboardButton("💡 Hint", callback_data="wordle_hint")
                    ],
                    [InlineKeyboardButton("🚫 End Game", callback_data="wordle_end")]
                ])
            )
        except Exception as e:
            print(f"Error updating hint message: {e}")
        
    except Exception as e:
        print(f"Error in hint callback: {e}")
        await query.answer("Error providing hint. Try again.", show_alert=True) 