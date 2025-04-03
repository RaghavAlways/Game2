import random
import asyncio
import re
import time
from typing import Dict, List, Set
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import UserNotParticipant, FloodWait, MessageNotModified
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

# List to track message IDs for cleanup
game_messages = {}  # {chat_id: [message_ids]}

# Function to handle message cleanup
async def cleanup_messages(chat_id, delay=20):
    """Delete old game messages after a delay"""
    await asyncio.sleep(delay)
    if chat_id in game_messages and len(game_messages[chat_id]) > 1:
        # Keep the most recent message
        messages_to_delete = game_messages[chat_id][:-1]
        for msg_id in messages_to_delete:
            try:
                await app.delete_messages(chat_id, msg_id)
            except Exception as e:
                print(f"Error deleting message {msg_id}: {e}")
        
        # Update the list to only include the latest message
        game_messages[chat_id] = game_messages[chat_id][-1:]

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
    """Create a concise game status message"""
    game_data = active_games.get(chat_id, {})
    
    # Update last activity timestamp
    game_data["last_activity"] = time.time()
    
    if not game_data:
        return None
    
    word = game_data.get("word", "")
    attempts = game_data.get("attempts", [])
    players = game_data.get("players", {})
    
    if not available_letters:
        available_letters = sorted(list(set("ABCDEFGHIJKLMNOPQRSTUVWXYZ") - set(
            letter for attempt in attempts for letter in attempt
        )))
    
    # Format available letters compactly
    letters_display = ""
    for i, chunk in enumerate([available_letters[i:i+7] for i in range(0, len(available_letters), 7)]):
        letters_display += "".join(chunk)
        if i < (len(available_letters) - 1) // 7:
            letters_display += " "
    
    # Format the word display compactly
    correct_letters = game_data.get("correct_letters", set())
    displayed_word = "".join([char.upper() if char.upper() in correct_letters else "_" for char in word])
    
    # Create the concise game status message with blockquote formatting
    message = (
        "<blockquote>\n"
        f"🎮 WORDLE\n"
        f"Word: `{displayed_word}`\n"
        f"Tries: {len(attempts)}/6 • Players: {len(players)}"
    )
    
    if hints_used > 0:
        message += f"\nHints: {hints_used}/3"
    
    if extra_text:
        message += f"\n{extra_text}"
    
    if letters_display:
        message += f"\nLetters: `{letters_display}`"
    
    message += "\n</blockquote>"
    
    # Create compact markup with consistent callback data
    markup = [
        [
            InlineKeyboardButton("Join", callback_data="wordle_join"),
            InlineKeyboardButton("Hint", callback_data="wordle_hint"),
            InlineKeyboardButton("Reset", callback_data="game_error_recovery")
        ]
    ]
    
    return message, InlineKeyboardMarkup(markup)

def check_word(guess: str, word: str) -> str:
    """Check guess against the word and return formatted result"""
    result = ""
    correct_positions = set()  # Track positions of correct letters
    
    for i, letter in enumerate(guess):
        if letter == word[i]:
            result += "🟩"  # Correct position
            correct_positions.add(i)  # Record correct position
        elif letter in word:
            result += "🟨"  # In word but wrong position
        else:
            result += "🟥"  # Not in word
    
    return result, correct_positions

@app.on_message(filters.command("wordle") & filters.group)
async def start_wordle(_, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Check if there's already a game in this chat
    if chat_id in active_games:
        reply = await message.reply_text(
            "<blockquote>❗ Game already in progress!</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Show Game", callback_data="wordle_show")]
            ])
        )
        # Add to cleanup list
        if chat_id not in game_messages:
            game_messages[chat_id] = []
        game_messages[chat_id].append(reply.id)
        # Schedule cleanup
        asyncio.create_task(cleanup_messages(chat_id))
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
        "start_time": int(time.time()),  # Track game start time
        "correct_letters": set()  # Track correctly guessed letters
    }
    
    # Send concise initial game message
    game_message = """<blockquote>
🎮 Wordle Game Started!
• Guess the 5-letter word
• 🟩 Right letter, right spot
• 🟨 Right letter, wrong spot
• 🟥 Letter not in word
Use: `/guess WORD`
</blockquote>"""
    
    reply = await message.reply_text(
        game_message,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Join", callback_data="wordle_join"),
                InlineKeyboardButton("Hint", callback_data="wordle_hint")
            ]
        ])
    )
    
    # Start tracking messages for this chat
    if chat_id not in game_messages:
        game_messages[chat_id] = []
    
    # Add this message to the list
    game_messages[chat_id].append(reply.id)
    
    # Store the message ID for updates
    active_games[chat_id]["message_id"] = reply.id

@app.on_message(filters.command("guess") & filters.group)
async def make_guess(_, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Check for other active games
    try:
        from AviaxMusic.plugins.bot.hangman import active_hangman_games
        hangman_active = chat_id in active_hangman_games
    except ImportError:
        hangman_active = False
        
    try:
        from AviaxMusic.plugins.bot.guess import active_guess_games
        numguess_active = chat_id in active_guess_games
    except ImportError:
        numguess_active = False
    
    # Detect specific Wordle guess
    wordle_active = chat_id in active_games
    is_word_guess = False
    
    if len(message.command) > 1:
        guess = message.command[1].upper()
        # Wordle guesses are typically 5-letter words
        if len(guess) >= 4 and guess.isalpha():
            is_word_guess = True
    
    # Handle conflicts
    multiple_games = sum([wordle_active, hangman_active, numguess_active]) > 1
    
    if multiple_games:
        # If it's clearly a word guess, proceed with Wordle
        if is_word_guess and wordle_active:
            pass  # Continue with Wordle handling
        # If it's not a word guess and other games are active, let them handle it
        elif not is_word_guess and (hangman_active or numguess_active):
            return  # Let the other handler process it
        # If it's ambiguous, provide guidance
        else:
            reply = await message.reply_text(
                "<blockquote>Multiple games are active. Specify which game:\n"
                "• For Wordle: `/guess APPLE` (a word)\n"
                "• For Hangman: `/guess a` (a single letter)\n"
                "• For Number Guess: `/guess 42` (a number)</blockquote>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Games Menu", callback_data="game_menu")]
                ])
            )
            if chat_id not in game_messages:
                game_messages[chat_id] = []
            game_messages[chat_id].append(reply.id)
            asyncio.create_task(cleanup_messages(chat_id))
            return
    
    # No Wordle game active
    if not wordle_active:
        # If it's clearly a Wordle-style guess but other games are active
        if is_word_guess and (hangman_active or numguess_active):
            reply = await message.reply_text(
                "<blockquote>No active Wordle game. Start with /wordle</blockquote>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Start Wordle", callback_data="start_wordle")]
                ])
            )
            if chat_id not in game_messages:
                game_messages[chat_id] = []
            game_messages[chat_id].append(reply.id)
            asyncio.create_task(cleanup_messages(chat_id))
            return
        # If it's not clearly a Wordle guess and other games are active, let them handle it
        elif not is_word_guess and (hangman_active or numguess_active):
            return
        # If no games are active
        else:
            reply = await message.reply_text("<blockquote>❌ No active game. Start with /wordle</blockquote>")
            if chat_id not in game_messages:
                game_messages[chat_id] = []
            game_messages[chat_id].append(reply.id)
            asyncio.create_task(cleanup_messages(chat_id))
            return
    
    # Check if user is a player
    if user_id not in active_games[chat_id]["players"]:
        reply = await message.reply_text(
            "<blockquote>❌ Join the game first</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Join Game", callback_data="wordle_join")]
            ])
        )
        # Add to cleanup list
        if chat_id not in game_messages:
            game_messages[chat_id] = []
        game_messages[chat_id].append(reply.id)
        # Schedule cleanup
        asyncio.create_task(cleanup_messages(chat_id))
        return
    
    # Check if it's the user's turn
    if user_id != active_games[chat_id]["current_player"]:
        current_player_name = await get_user_name(chat_id, active_games[chat_id]["current_player"])
        reply = await message.reply_text(f"<blockquote>❌ Not your turn. Wait for {current_player_name}.</blockquote>")
        # Add to cleanup list
        if chat_id not in game_messages:
            game_messages[chat_id] = []
        game_messages[chat_id].append(reply.id)
        # Schedule cleanup
        asyncio.create_task(cleanup_messages(chat_id))
        return
    
    # Get the guess
    if len(message.command) < 2:
        reply = await message.reply_text("<blockquote>❗ Provide a word: `/guess WORD`</blockquote>")
        # Add to cleanup list
        if chat_id not in game_messages:
            game_messages[chat_id] = []
        game_messages[chat_id].append(reply.id)
        # Schedule cleanup
        asyncio.create_task(cleanup_messages(chat_id))
        return
    
    guess = message.command[1].upper()
    
    # Validate guess is only letters
    if not re.match(r'^[A-Za-z]+$', guess):
        reply = await message.reply_text("<blockquote>❗ Only letters allowed</blockquote>")
        # Add to cleanup list
        if chat_id not in game_messages:
            game_messages[chat_id] = []
        game_messages[chat_id].append(reply.id)
        # Schedule cleanup
        asyncio.create_task(cleanup_messages(chat_id))
        return
    
    # Validate guess length
    word = active_games[chat_id]["word"]
    if len(guess) != len(word):
        reply = await message.reply_text("<blockquote>❗ Must be 5 letters</blockquote>")
        # Add to cleanup list
        if chat_id not in game_messages:
            game_messages[chat_id] = []
        game_messages[chat_id].append(reply.id)
        # Schedule cleanup
        asyncio.create_task(cleanup_messages(chat_id))
        return
    
    # Add the guess to attempts
    active_games[chat_id]["attempts"].append(guess)
    
    # Update correctly guessed letters and positions
    result, correct_positions = check_word(guess, word)
    
    # Initialize correct_letters set if it doesn't exist
    if "correct_letters" not in active_games[chat_id]:
        active_games[chat_id]["correct_letters"] = set()
    
    # Update correct letters for display
    for pos in correct_positions:
        active_games[chat_id]["correct_letters"].add(word[pos])
    
    # Check if the guess is correct
    if guess == word:
        # Update player's score
        active_games[chat_id]["players"][user_id] += 10
        
        # Get attempt count
        attempts_count = len(active_games[chat_id]["attempts"])
        
        # Create winner message with blockquote
        winner_message = f"""<blockquote>
🎉 {message.from_user.first_name} guessed: {word}!
✅ Solved in {attempts_count} attempts
</blockquote>"""
        
        # Send the winner message and clean up
        reply = await message.reply_text(
            winner_message,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("New Game", callback_data="wordle_start")]
            ])
        )
        
        # Add to cleanup list but with longer delay for winning message
        if chat_id not in game_messages:
            game_messages[chat_id] = []
        game_messages[chat_id].append(reply.id)
        
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
        # Game over - no one guessed correctly (simplified)
        game_over_message = "<blockquote>❌ Game over! Word was: {word}</blockquote>"
        
        reply = await message.reply_text(
            game_over_message,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("New Game", callback_data="wordle_start")]
            ])
        )
        
        # Add to cleanup list
        if chat_id not in game_messages:
            game_messages[chat_id] = []
        game_messages[chat_id].append(reply.id)
        
        # Delete the game
        try:
            del active_games[chat_id]
        except KeyError:
            pass
            
        return
    
    # Show updated game status with blockquote
    next_player = await get_user_name(chat_id, active_games[chat_id]["current_player"])
    
    # Get remaining letters
    used_letters = set()
    for attempt in active_games[chat_id]["attempts"]:
        for letter in attempt:
            used_letters.add(letter)
    remaining_letters = "".join(sorted([l for l in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if l not in used_letters]))
    
    # Format remaining letters in chunks of 7
    formatted_letters = ""
    for i in range(0, len(remaining_letters), 7):
        formatted_letters += remaining_letters[i:i+7] + " "
    
    # Create compact progress display with blockquote
    masked_word = "".join([letter if letter in active_games[chat_id]["correct_letters"] else "_" for letter in word.upper()])
    
    game_message = f"""<blockquote>
🎲 {message.from_user.first_name}: {guess}
{result}

🎯 Word: `{masked_word}` ({len(active_games[chat_id]["attempts"])}/30)
👤 Next: {next_player}
🔤 Available: `{formatted_letters.strip()}`
</blockquote>"""
    
    reply = await message.reply_text(
        game_message,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Join", callback_data="wordle_join"),
                InlineKeyboardButton("Hint", callback_data="wordle_hint")
            ]
        ])
    )
    
    # Add to cleanup list
    if chat_id not in game_messages:
        game_messages[chat_id] = []
    game_messages[chat_id].append(reply.id)
    # Schedule cleanup
    asyncio.create_task(cleanup_messages(chat_id))

@app.on_callback_query(filters.regex("^wordle_"))
async def wordle_callback(_, query: CallbackQuery):
    chat_id = query.message.chat.id
    user_id = query.from_user.id
    data = query.data.split("_")[1]
    
    # Show game
    if data == "show":
        if chat_id not in active_games:
            await query.answer("Game has ended or doesn't exist.", show_alert=True)
            return
        
        try:
            message, markup = await create_game_message(chat_id)
            await query.message.reply_text(message, reply_markup=markup)
            await query.answer()
        except Exception as e:
            print(f"Error showing game: {e}")
            await query.answer("Error showing game. Try again.", show_alert=True)
    
    # Join game
    elif data == "join":
        if chat_id not in active_games:
            await query.answer("Game has ended or doesn't exist.", show_alert=True)
            return
        
        # Add user to players if not already in
        if user_id not in active_games[chat_id]["players"]:
            active_games[chat_id]["players"][user_id] = 0
            
            # If there's no current player, make this user the current player
            if not active_games[chat_id].get("current_player"):
                active_games[chat_id]["current_player"] = user_id
            
            try:
                # Get updated game message
                message, markup = await create_game_message(chat_id, extra_text=f"✅ {query.from_user.first_name} joined!")
                
                # Edit message
                await query.message.edit_text(message, reply_markup=markup)
                await query.answer("You joined! Use /guess WORD to play.")
            except Exception as e:
                print(f"Error joining game: {e}")
                await query.answer("Error joining. Try again.", show_alert=True)
        else:
            await query.answer("You're already in the game!", show_alert=True)
    
    # End game
    elif data == "end":
        if chat_id not in active_games:
            await query.answer("Game already ended.", show_alert=True)
            return
        
        # Check if user is in the game
        if user_id not in active_games[chat_id]["players"] and user_id not in SUDOERS:
            await query.answer("Only players or admins can end the game!", show_alert=True)
            return
        
        word = active_games[chat_id]["word"]
        
        # Simplified end message with blockquote
        await query.message.edit_text(
            f"<blockquote>🎮 Game Ended!\nWord was: {word}\nEnded by: {query.from_user.first_name}</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("New Game", callback_data="wordle_start")]
            ])
        )
        
        # Delete the game
        try:
            del active_games[chat_id]
            await query.answer("Game ended!")
        except Exception as e:
            print(f"Error ending game: {e}")
            await query.answer("Error ending game. Try again.", show_alert=True)
    
    # Handle hint button
    elif data == "hint":
        # Forward to the hint handler
        await wordle_hint_callback(_, query)
    
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
            await query.answer("Error starting game. Try /wordle instead.", show_alert=True)
    
    else:
        await query.answer()

@app.on_message(filters.command("wordlehelp"))
async def wordle_help(_, message: Message):
    help_text = """<blockquote>
🎮 **Wordle Help**

**Commands:**
• /wordle - Start a new game
• /guess WORD - Make a guess
• /wordlehelp - This help

**How to Play:**
• Guess the 5-letter word
• 🟩 Right letter, right spot
• 🟨 Right letter, wrong spot
• 🟥 Letter not in word
• 6 attempts maximum
</blockquote>"""
    await message.reply_text(
        help_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Start Game", callback_data="wordle_start")]
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
            await query.answer("No active game. Start with /wordle", show_alert=True)
            return
        
        # Check if user is already a player
        if user_id in active_games[chat_id]["players"]:
            await query.answer("You're already in this game!", show_alert=True)
            return
        
        # Add user to players
        active_games[chat_id]["players"][user_id] = 0
        player_name = query.from_user.first_name
        
        # Update game message
        try:
            # Get updated game message
            message, markup = await create_game_message(
                chat_id, 
                extra_text=f"✅ {player_name} joined the game!"
            )
            
            # Edit the message
            await query.message.edit_text(message, reply_markup=markup)
            await query.answer("Joined! Use /guess WORD to play")
            
            # Message updated, add to tracking
            if chat_id not in game_messages:
                game_messages[chat_id] = []
            game_messages[chat_id].append(query.message.id)
            
        except MessageNotModified:
            # Message content was not modified, ignore this error
            pass
        except Exception as e:
            print(f"Error updating game message: {e}")
            await query.answer("Joined, but couldn't update message", show_alert=True)
            
    except Exception as e:
        print(f"Error in join callback: {e}")
        await query.answer("Error joining. Try again.", show_alert=True)

@app.on_callback_query(filters.regex("wordle_show"))
async def show_wordle_callback(_, query: CallbackQuery):
    """Handler for showing the current Wordle game status"""
    try:
        chat_id = query.message.chat.id
        
        # Check if there's a game in progress
        if chat_id not in active_games:
            await query.answer("No game in progress", show_alert=True)
            return
        
        # Get updated game message
        message, markup = await create_game_message(chat_id)
        
        # Send as new message to avoid editing limitations
        await query.message.reply_text(message, reply_markup=markup)
        await query.answer("Game status updated!")
    except Exception as e:
        print(f"Error in show callback: {e}")
        await query.answer("Error showing game", show_alert=True)

@app.on_callback_query(filters.regex("join_wordle"))
async def join_wordle_alternate_callback(_, query: CallbackQuery):
    """Alternate handler for joining via the join_wordle callback data"""
    # Forward to the main join handler
    await join_wordle_callback(_, query)

@app.on_callback_query(filters.regex("game_error_recovery"))
async def game_error_recovery_callback(_, query: CallbackQuery):
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
            await query.answer("Only admins or game creators can reset", show_alert=True)
            return
            
        # Clear any existing game state
        if chat_id in active_games:
            del active_games[chat_id]
            
        # Simplified reset message with blockquote
        await query.message.edit_text(
            "<blockquote>🎮 Game Reset\n\nThe game has been reset due to an error.</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("New Game", callback_data="wordle_start")]
            ])
        )
        await query.answer("Game reset successful!")
        
    except Exception as e:
        print(f"Error in game recovery: {e}")
        await query.answer("Could not reset. Try /wordle instead", show_alert=True)

@app.on_callback_query(filters.regex("wordle_hint"))
async def wordle_hint_callback(_, query: CallbackQuery):
    """Provide a hint for the current Wordle game"""
    try:
        chat_id = query.message.chat.id
        user_id = query.from_user.id
        
        # Check if there's a game in progress
        if chat_id not in active_games:
            await query.answer("No active game found. Start with /wordle", show_alert=True)
            return
        
        # Auto-join the user when they request a hint
        if user_id not in active_games[chat_id]["players"]:
            active_games[chat_id]["players"][user_id] = 0
            await query.answer("You've been added to the game!", show_alert=True)
        
        # Limit hints to 3 per game
        if active_games[chat_id].get("hints_used", 0) >= 3:
            await query.answer("Maximum hints (3) already used!", show_alert=True)
            return
        
        # Get the current word
        word = active_games[chat_id]["word"]
        attempts = active_games[chat_id]["attempts"]
        
        # Choose hint type based on hints used so far
        hints_used = active_games[chat_id].get("hints_used", 0)
        
        if hints_used == 0:
            # First hint - reveal the first letter
            hint = f"The word starts with '{word[0]}'"
        elif hints_used == 1:
            # Second hint - letter position hint
            letter_pos = random.randint(1, len(word)-1)  # Not the first letter
            hint = f"Letter at position {letter_pos+1} is '{word[letter_pos]}'"
        else:
            # Third hint - more substantial
            # If there are attempts, find an unused correct letter
            if len(attempts) > 0:
                # Find a position not yet guessed correctly
                correct_letters = active_games[chat_id].get("correct_letters", set())
                unused_letters = [letter for letter in word if letter not in correct_letters]
                
                if unused_letters:
                    letter = random.choice(unused_letters)
                    pos = word.index(letter)
                    hint = f"Letter at position {pos+1} is '{letter}'"
                else:
                    # All letters have been guessed at some point
                    hint = f"The word has these letters: {', '.join(sorted(set(word)))}"
            else:
                # No attempts yet, give the first two letters
                hint = f"The word starts with '{word[0:2]}'"
        
        # Increment hints used
        active_games[chat_id]["hints_used"] = hints_used + 1
        
        # Send the hint
        await query.answer(f"HINT: {hint}", show_alert=True)
        
        # Update the game message
        try:
            message, markup = await create_game_message(
                chat_id, 
                hints_used=active_games[chat_id]["hints_used"],
                extra_text=f"💡 {query.from_user.first_name} used a hint!"
            )
            
            await query.message.edit_text(message, reply_markup=markup)
            
            # Add to cleanup list
            if chat_id not in game_messages:
                game_messages[chat_id] = []
            game_messages[chat_id].append(query.message.id)
            
        except MessageNotModified:
            # Message content was not modified, ignore this error
            pass
        except Exception as e:
            print(f"Error updating hint message: {e}")
            # Try sending a new message if editing fails
            new_message = await query.message.reply_text(
                f"<blockquote>💡 {query.from_user.first_name} used a hint ({active_games[chat_id]['hints_used']}/3)!</blockquote>",
                reply_markup=markup
            )
            # Add to cleanup list
            if chat_id not in game_messages:
                game_messages[chat_id] = []
            game_messages[chat_id].append(new_message.id)
        
    except Exception as e:
        print(f"Error in hint callback: {e}")
        await query.answer("Error providing hint. Try again.", show_alert=True) 