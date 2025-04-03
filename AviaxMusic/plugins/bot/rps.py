import asyncio
import random
from typing import Dict, List, Union
import time

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery

from AviaxMusic import app
from AviaxMusic.misc import SUDOERS
from config import BANNED_USERS

# Game choices with emojis and win conditions
RPS_CHOICES = {
    "rock": {"emoji": "🪨", "beats": "scissors"},
    "paper": {"emoji": "📄", "beats": "rock"},
    "scissors": {"emoji": "✂️", "beats": "paper"}
}

# Active games dictionary
# Structure: {chat_id: {"players": {user_id: {"name": str, "choice": str}}, "round": int, "scores": {user_id: int}}}
active_rps_games = {}

# Function to create game buttons
def get_rps_buttons():
    buttons = []
    for choice, data in RPS_CHOICES.items():
        buttons.append(
            InlineKeyboardButton(
                f"{data['emoji']} {choice.title()}", 
                callback_data=f"rps_choose_{choice}"
            )
        )
    return [buttons]

# Start or join an RPS game
@app.on_message(filters.command("rps") & filters.group & ~BANNED_USERS)
async def start_rps_game(_, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    # Check if already a game in this chat
    if chat_id in active_rps_games:
        game = active_rps_games[chat_id]
        
        # Update last activity timestamp
        game["last_activity"] = time.time()
        
        # Game already has 2 players
        if len(game["players"]) >= 2:
            player_names = [player["name"] for player in game["players"].values()]
            await message.reply_text(
                f"🎮 A game is already in progress between {player_names[0]} and {player_names[1]}!\n\n"
                f"Please wait for it to finish or start a new game in another chat."
            )
            return
        
        # Join the game as second player
        if user_id not in game["players"]:
            game["players"][user_id] = {"name": user_name, "choice": None}
            game["scores"][user_id] = 0
            
            # Both players are ready, start the round
            await message.reply_text(
                f"🎮 {user_name} has joined the Rock-Paper-Scissors game!\n\n"
                f"Round {game['round']} - Choose your move:",
                reply_markup=InlineKeyboardMarkup(get_rps_buttons())
            )
            return
        
        # User is already in the game
        await message.reply_text(
            f"You're already in this game! Waiting for another player to join."
        )
        return
    
    # Create a new game
    active_rps_games[chat_id] = {
        "players": {user_id: {"name": user_name, "choice": None}},
        "round": 1,
        "scores": {user_id: 0},
        "last_activity": time.time()  # Add timestamp
    }
    
    await message.reply_text(
        f"🎮 {user_name} has started a Rock-Paper-Scissors game!\n\n"
        f"Waiting for another player to join...\n"
        f"Join with /rps command.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Cancel Game", callback_data="rps_cancel")
        ]])
    )

# Cancel an RPS game
@app.on_callback_query(filters.regex("^rps_cancel$"))
async def cancel_rps_game(_, query: CallbackQuery):
    chat_id = query.message.chat.id
    user_id = query.from_user.id
    
    # Check if there's a game
    if chat_id not in active_rps_games:
        await query.answer("No active game to cancel.")
        return
    
    # Check if user is in the game
    if user_id not in active_rps_games[chat_id]["players"]:
        await query.answer("You're not part of this game.", show_alert=True)
        return
    
    # Cancel the game
    del active_rps_games[chat_id]
    
    await query.message.edit_text(
        f"🎮 Rock-Paper-Scissors game cancelled by {query.from_user.first_name}."
    )
    await query.answer("Game cancelled!")

# Handle player choice
@app.on_callback_query(filters.regex("^rps_choose_"))
async def handle_rps_choice(_, query: CallbackQuery):
    chat_id = query.message.chat.id
    user_id = query.from_user.id
    choice = query.data.split("_")[2]  # Extract the choice (rock, paper, scissors)
    
    # Check if there's a game
    if chat_id not in active_rps_games:
        await query.answer("No active game found.", show_alert=True)
        return
    
    # Update activity timestamp
    active_rps_games[chat_id]["last_activity"] = time.time()
    
    # Check if user is in the game
    if user_id not in active_rps_games[chat_id]["players"]:
        await query.answer("You're not part of this game.", show_alert=True)
        return
    
    # Save the player's choice
    active_rps_games[chat_id]["players"][user_id]["choice"] = choice
    await query.answer(f"You chose {choice}!")
    
    # Check if both players have made their choices
    game = active_rps_games[chat_id]
    players = list(game["players"].keys())
    
    # Make sure there are 2 players
    if len(players) < 2:
        await query.answer("Still waiting for another player to join!")
        return
    
    # Check if both players have chosen
    if all(game["players"][player]["choice"] for player in players):
        # Both players have chosen, determine the winner
        choices = [game["players"][player]["choice"] for player in players]
        names = [game["players"][player]["name"] for player in players]
        
        result_text = (
            f"🎮 **Round {game['round']} Results:**\n\n"
            f"{names[0]} chose {RPS_CHOICES[choices[0]]['emoji']} {choices[0].title()}\n"
            f"{names[1]} chose {RPS_CHOICES[choices[1]]['emoji']} {choices[1].title()}\n\n"
        )
        
        # Determine winner
        if choices[0] == choices[1]:
            # It's a tie
            result_text += "It's a tie! No points awarded."
        else:
            winner_idx = 0 if RPS_CHOICES[choices[0]]["beats"] == choices[1] else 1
            loser_idx = 1 - winner_idx
            
            # Update score
            game["scores"][players[winner_idx]] += 1
            
            result_text += f"{names[winner_idx]} wins this round! 🏆\n"
        
        # Show current scores
        result_text += f"\n**Current Score:**\n"
        result_text += f"{names[0]}: {game['scores'][players[0]]}\n"
        result_text += f"{names[1]}: {game['scores'][players[1]]}\n"
        
        # Prepare for next round
        game["round"] += 1
        for player in players:
            game["players"][player]["choice"] = None
        
        # Check if game should end (best of 5)
        if game["scores"][players[0]] >= 3 or game["scores"][players[1]] >= 3:
            # Game over
            winner = players[0] if game["scores"][players[0]] > game["scores"][players[1]] else players[1]
            
            result_text += f"\n🎉 **{game['players'][winner]['name']} wins the game!**"
            
            # Delete the game
            del active_rps_games[chat_id]
            
            await query.message.edit_text(
                result_text,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Play Again", callback_data="rps_new_game")
                ]])
            )
        else:
            # Continue to next round
            result_text += f"\n**Round {game['round']} - Choose your move:**"
            
            await query.message.edit_text(
                result_text,
                reply_markup=InlineKeyboardMarkup(get_rps_buttons())
            )
    else:
        # Still waiting for the other player
        await query.message.edit_text(
            f"🎮 Rock-Paper-Scissors - Round {game['round']}\n\n"
            f"Waiting for both players to choose...\n\n"
            f"{game['players'][players[0]]['name']}: {'✅ Ready' if game['players'][players[0]]['choice'] else '❌ Not Ready'}\n"
            f"{game['players'][players[1]]['name']}: {'✅ Ready' if game['players'][players[1]]['choice'] else '❌ Not Ready'}\n\n"
            f"Choose your move:",
            reply_markup=InlineKeyboardMarkup(get_rps_buttons())
        )

# Start a new game after one ends
@app.on_callback_query(filters.regex("^rps_new_game$"))
async def start_new_rps_game(_, query: CallbackQuery):
    chat_id = query.message.chat.id
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    
    # Check if already a game in this chat
    if chat_id in active_rps_games:
        await query.answer("A game is already in progress in this chat!")
        return
    
    # Create a new game
    active_rps_games[chat_id] = {
        "players": {user_id: {"name": user_name, "choice": None}},
        "round": 1,
        "scores": {user_id: 0},
        "last_activity": time.time()  # Add timestamp
    }
    
    await query.message.edit_text(
        f"🎮 {user_name} has started a new Rock-Paper-Scissors game!\n\n"
        f"Waiting for another player to join...\n"
        f"Join with /rps command.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Cancel Game", callback_data="rps_cancel")
        ]])
    )
    await query.answer("New game started!")

# Play against the bot
@app.on_message(filters.command("rpsbot") & ~BANNED_USERS)
async def play_rps_with_bot(_, message: Message):
    user_name = message.from_user.first_name
    
    await message.reply_text(
        f"🎮 {user_name}, let's play Rock-Paper-Scissors!\n\n"
        f"Choose your move:",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🪨 Rock", callback_data="rpsbot_rock"),
                InlineKeyboardButton("📄 Paper", callback_data="rpsbot_paper"),
                InlineKeyboardButton("✂️ Scissors", callback_data="rpsbot_scissors")
            ]
        ])
    )

# Handle bot game choice
@app.on_callback_query(filters.regex("^rpsbot_"))
async def handle_rpsbot_choice(_, query: CallbackQuery):
    user_choice = query.data.split("_")[1]
    user_name = query.from_user.first_name
    
    # Bot makes a random choice
    bot_choice = random.choice(list(RPS_CHOICES.keys()))
    
    # Prepare result message
    result_text = (
        f"🎮 **Rock-Paper-Scissors Results:**\n\n"
        f"{user_name} chose {RPS_CHOICES[user_choice]['emoji']} {user_choice.title()}\n"
        f"Bot chose {RPS_CHOICES[bot_choice]['emoji']} {bot_choice.title()}\n\n"
    )
    
    # Determine winner
    if user_choice == bot_choice:
        # It's a tie
        result_text += "It's a tie! 🤝"
    elif RPS_CHOICES[user_choice]["beats"] == bot_choice:
        # User wins
        result_text += f"{user_name} wins! 🏆"
    else:
        # Bot wins
        result_text += "Bot wins! 🤖"
    
    # Show play again button
    await query.message.edit_text(
        result_text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Play Again", callback_data="rpsbot_play_again")
        ]])
    )
    await query.answer()

# Handle play again with bot
@app.on_callback_query(filters.regex("^rpsbot_play_again$"))
async def rpsbot_play_again(_, query: CallbackQuery):
    user_name = query.from_user.first_name
    
    await query.message.edit_text(
        f"🎮 {user_name}, let's play Rock-Paper-Scissors again!\n\n"
        f"Choose your move:",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🪨 Rock", callback_data="rpsbot_rock"),
                InlineKeyboardButton("📄 Paper", callback_data="rpsbot_paper"),
                InlineKeyboardButton("✂️ Scissors", callback_data="rpsbot_scissors")
            ]
        ])
    )
    await query.answer("New game started!")

# Help command for RPS game
@app.on_message(filters.command("rpshelp") & ~BANNED_USERS)
async def rps_help(_, message: Message):
    help_text = """
🎮 **Rock-Paper-Scissors Help**

**Commands:**
• `/rps` - Start a multiplayer game or join an existing one
• `/rpsbot` - Play against the bot

**How to Play:**
• Rock beats Scissors ✂️
• Scissors beats Paper 📄
• Paper beats Rock 🪨

**Multiplayer Mode:**
• First player to win 3 rounds wins the game
• Both players must choose before results are shown

Have fun playing! 🎮
"""
    await message.reply_text(
        help_text,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Play with Bot", callback_data="rpsbot_play_again"),
                InlineKeyboardButton("Multiplayer", callback_data="rps_new_game")
            ]
        ])
    ) 