from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from AviaxMusic import app
from config import BANNED_USERS

# Supported languages with their display names and flags
LANGUAGES = {
    "en": {"name": "English", "flag": "🇬🇧"},
    "hi": {"name": "Hindi", "flag": "🇮🇳"},
    "ar": {"name": "Arabic", "flag": "🇸🇦"},
    "es": {"name": "Spanish", "flag": "🇪🇸"},
    "fr": {"name": "French", "flag": "🇫🇷"}
}

# Default strings for different languages
DEFAULT_STRINGS = {
    "en": {
        "language_changed": "🇬🇧 Language has been changed to English!",
        "select_language": "🌍 Please select your preferred language:",
        "wordle_start": "🎮 New Wordle Game Started!",
        "wordle_guess": "Make a guess with `/guess WORD`",
        "song_playing": "🎵 Now playing: {}",
        "queue_empty": "Queue is empty. Add some songs!",
        "queue_position": "Position in queue: {}",
        "skip_success": "⏭️ Skipped to next track"
    },
    "hi": {
        "language_changed": "🇮🇳 भाषा हिंदी में बदल दी गई है!",
        "select_language": "🌍 कृपया अपनी पसंदीदा भाषा चुनें:",
        "wordle_start": "🎮 नया वर्डल गेम शुरू हुआ!",
        "wordle_guess": "अनुमान लगाने के लिए `/guess WORD` का उपयोग करें",
        "song_playing": "🎵 अभी चल रहा है: {}",
        "queue_empty": "कतार खाली है। कुछ गाने जोड़ें!",
        "queue_position": "कतार में स्थिति: {}",
        "skip_success": "⏭️ अगले ट्रैक पर स्किप किया गया"
    },
    "ar": {
        "language_changed": "🇸🇦 تم تغيير اللغة إلى العربية!",
        "select_language": "🌍 الرجاء اختيار لغتك المفضلة:",
        "wordle_start": "🎮 بدأت لعبة وورديل جديدة!",
        "wordle_guess": "خمن باستخدام `/guess WORD`",
        "song_playing": "🎵 يشغل الآن: {}",
        "queue_empty": "قائمة الانتظار فارغة. أضف بعض الأغاني!",
        "queue_position": "الموقع في قائمة الانتظار: {}",
        "skip_success": "⏭️ تم التخطي إلى المسار التالي"
    },
    "es": {
        "language_changed": "🇪🇸 ¡El idioma ha sido cambiado a Español!",
        "select_language": "🌍 Por favor, selecciona tu idioma preferido:",
        "wordle_start": "🎮 ¡Nuevo juego de Wordle iniciado!",
        "wordle_guess": "Haz una conjetura con `/guess WORD`",
        "song_playing": "🎵 Reproduciendo ahora: {}",
        "queue_empty": "La cola está vacía. ¡Añade algunas canciones!",
        "queue_position": "Posición en la cola: {}",
        "skip_success": "⏭️ Saltado a la siguiente pista"
    },
    "fr": {
        "language_changed": "🇫🇷 La langue a été changée en français!",
        "select_language": "🌍 Veuillez sélectionner votre langue préférée:",
        "wordle_start": "🎮 Nouveau jeu Wordle commencé!",
        "wordle_guess": "Faites une supposition avec `/guess WORD`",
        "song_playing": "🎵 Lecture en cours: {}",
        "queue_empty": "La file d'attente est vide. Ajoutez des chansons!",
        "queue_position": "Position dans la file d'attente: {}",
        "skip_success": "⏭️ Passé à la piste suivante"
    }
}

# Store user language preferences
user_languages = {}

def get_user_language(user_id):
    """Get the language preference for a user"""
    return user_languages.get(str(user_id), "en")

def get_string(lang_code, key):
    """Get a string in the specified language"""
    if lang_code in DEFAULT_STRINGS and key in DEFAULT_STRINGS[lang_code]:
        return DEFAULT_STRINGS[lang_code][key]
    # Fallback to English
    return DEFAULT_STRINGS["en"].get(key, f"String not found: {key}")

async def update_user_language(user_id, lang_code):
    """Update a user's language preference"""
    if lang_code in LANGUAGES:
        user_languages[str(user_id)] = lang_code
        # In a real implementation, save this to a database
        return True
    return False

def get_language_keyboard(current_lang=None):
    """Generate the language selection keyboard"""
    keyboard = []
    row = []
    
    for i, (code, lang_info) in enumerate(LANGUAGES.items()):
        # Create buttons with flag and name
        button_text = f"{lang_info['flag']} {lang_info['name']}"
        
        # Add a marker for the current language
        if current_lang == code:
            button_text += " ✓"
            
        callback_data = f"set_lang_{code}"
        row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
        
        # Create a new row after every 2 buttons
        if len(row) == 2 or i == len(LANGUAGES) - 1:
            keyboard.append(row)
            row = []
    
    return InlineKeyboardMarkup(keyboard)

@app.on_message(filters.command("language") & ~BANNED_USERS)
async def language_command(client, message: Message):
    """Command to change language preference"""
    user_id = message.from_user.id
    current_lang = get_user_language(user_id)
    
    await message.reply_text(
        get_string(current_lang, "select_language"),
        reply_markup=get_language_keyboard(current_lang)
    )

@app.on_callback_query(filters.regex("^set_lang_") & ~BANNED_USERS)
async def language_callback(client, query: CallbackQuery):
    """Handle language selection callback"""
    lang_code = query.data.split("_")[2]
    user_id = query.from_user.id
    
    # Update user's language preference
    success = await update_user_language(user_id, lang_code)
    
    if success:
        # Get language information
        lang_info = LANGUAGES.get(lang_code, {"name": lang_code, "flag": "🌐"})
        
        # Respond to the callback
        await query.answer(f"Language changed to {lang_info['name']}!", show_alert=True)
        
        # Update the message with the new language
        await query.message.edit_text(
            get_string(lang_code, "language_changed"),
            reply_markup=get_language_keyboard(lang_code)
        )
    else:
        await query.answer("Unsupported language code!", show_alert=True)

# Function to translate a string for a specific user
async def translate_for_user(user_id, key, *args):
    """Get a string in the user's preferred language with format arguments"""
    lang = get_user_language(user_id)
    string = get_string(lang, key)
    
    # Apply formatting if arguments are provided
    if args:
        try:
            string = string.format(*args)
        except Exception as e:
            print(f"Error formatting string: {e}")
    
    return string
