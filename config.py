import re
from os import getenv

from dotenv import load_dotenv
from pyrogram import filters

load_dotenv()

API_ID = int(getenv("API_ID", "28580773"))
API_HASH = getenv("API_HASH", "f80e465a8805bee5c6bf29fa12d6cc0c")

# Get your token from @BotFather on Telegram.
BOT_TOKEN = getenv("BOT_TOKEN", "5759235328:AAEOSsYK13hbdSaNLfwj5yfanqWa9TiKXdE")

# Get your mongo url from cloud.mongodb.com
MONGO_DB_URI = getenv("MONGO_DB_URI", "mongodb+srv://Visionbot:Visionbot@visionbot.bhbwcls.mongodb.net/?retryWrites=true&w=majority&appName=Visionbot")

DURATION_LIMIT_MIN = int(getenv("DURATION_LIMIT", 600))

# Chat id of a group for logging bot's activities
LOG_GROUP_ID = int(getenv("LOG_GROUP_ID", -1002430579671))

# Get this value from @MissRose_Bot on Telegram by /id
OWNER_ID = int(getenv("OWNER_ID", 5016109398))

## Fill these variables if you're deploying on heroku.
# Your heroku app name
HEROKU_APP_NAME = getenv("HEROKU_APP_NAME")
# Get it from http://dashboard.heroku.com/account
HEROKU_API_KEY = getenv("HEROKU_API_KEY")

UPSTREAM_REPO = getenv(
    "UPSTREAM_REPO",
    "https://github.com/mrhoneyxd07/VAMPIRE_CREW_MUSIC",
)
UPSTREAM_BRANCH = getenv("UPSTREAM_BRANCH", "master")
GIT_TOKEN = getenv(
    "GIT_TOKEN", None
)  # Fill this variable if your upstream repository is private

SUPPORT_CHANNEL = getenv("SUPPORT_CHANNEL", "https://t.me/learningbots79")
SUPPORT_GROUP = getenv("SUPPORT_GROUP", "https://t.me/learning_bots")

# Set this to True if you want the assistant to automatically leave chats after an interval
AUTO_LEAVING_ASSISTANT = bool(getenv("AUTO_LEAVING_ASSISTANT", False))

# make your bots privacy from telegra.ph and put your url here 
PRIVACY_LINK = getenv("PRIVACY_LINK", "https://telegra.ph/Privacy-Policy-for-AviaxMusic-08-14")

# Start Image URL for the bot
START_IMG_URL = getenv("START_IMG_URL", "https://files.catbox.moe/juqfrb.jpg")

# Get this credentials from https://developer.spotify.com/dashboard
SPOTIFY_CLIENT_ID = getenv("SPOTIFY_CLIENT_ID", "1c21247d714244ddbb09925dac565aed")
SPOTIFY_CLIENT_SECRET = getenv("SPOTIFY_CLIENT_SECRET", "709e1a2969664491b58200860623ef19")


# Maximum limit for fetching playlist's track from youtube, spotify, apple links.
PLAYLIST_FETCH_LIMIT = int(getenv("PLAYLIST_FETCH_LIMIT", 25))


# Telegram audio and video file size limit (in bytes)
TG_AUDIO_FILESIZE_LIMIT = int(getenv("TG_AUDIO_FILESIZE_LIMIT", 104857600))
TG_VIDEO_FILESIZE_LIMIT = int(getenv("TG_VIDEO_FILESIZE_LIMIT", 2145386496))
# Checkout https://www.gbmb.org/mb-to-bytes for converting mb to bytes


# Get your pyrogram v2 session from Replit
STRING1 = getenv("STRING_SESSION", "BQAf70YAXJRuHI2FxTs0IXpl4oZUCxkcrk2Y9HB9v3iZzmqVPrOr8K2FQD7MIqO3x6TBMAiMqhCHr1-LmzpprJWOPgIoAWldrMCFGY4cBKRZeQOVhrD6t1o9nTstkst3WphbKmv61pCiWrCzywRXOiD82WcTUWmoWQtKvrr8FGBOwy94onotZ71Ja6EaFgWLOfoXPf_mHD3-eQDo-2Bfaq0VKH8ghfzqiWtaVI8zj-rNkLHdwFPJgxxDF2H1F6USjNIWcvWnKNMozKM5qtr0UXJHIpNh_V-MseszHxfwfQUAhsotlEgrxEHGY-q8YuDzli4q1ljChJmnYzxizlW58-DGzBW7WQAAAAHnKAsqAA")
STRING2 = getenv("STRING_SESSION2", None)
STRING3 = getenv("STRING_SESSION3", None)
STRING4 = getenv("STRING_SESSION4", None)
STRING5 = getenv("STRING_SESSION5", None)


BANNED_USERS = filters.user()
adminlist = {}
lyrical = {}
votemode = {}
autoclean = []
confirmer = {}


PING_IMG_URL = getenv(
    "PING_IMG_URL", "https://files.catbox.moe/juqfrb.jpg"
)
PLAYLIST_IMG_URL = "https://files.catbox.moe/juqfrb.jpg"
STATS_IMG_URL = "https://files.catbox.moe/juqfrb.jpg"
TELEGRAM_AUDIO_URL = "https://files.catbox.moe/juqfrb.jpg"
TELEGRAM_VIDEO_URL = "https://files.catbox.moe/juqfrb.jpg"
STREAM_IMG_URL = "https://files.catbox.moe/juqfrb.jpg"
SOUNCLOUD_IMG_URL = "https://files.catbox.moe/juqfrb.jpg"
YOUTUBE_IMG_URL = "https://files.catbox.moe/juqfrb.jpg"
SPOTIFY_ARTIST_IMG_URL = "https://files.catbox.moe/juqfrb.jpg"
SPOTIFY_ALBUM_IMG_URL = "https://files.catbox.moe/juqfrb.jpg"
SPOTIFY_PLAYLIST_IMG_URL = "https://files.catbox.moe/juqfrb.jpg"


def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60**i for i, x in enumerate(reversed(stringt.split(":"))))


DURATION_LIMIT = int(time_to_seconds(f"{DURATION_LIMIT_MIN}:00"))


if SUPPORT_CHANNEL:
    if not re.match("(?:http|https)://", SUPPORT_CHANNEL):
        raise SystemExit(
            "[ERROR] - Your SUPPORT_CHANNEL url is wrong. Please ensure that it starts with https://"
        )

if SUPPORT_GROUP:
    if not re.match("(?:http|https)://", SUPPORT_GROUP):
        raise SystemExit(
            "[ERROR] - Your SUPPORT_GROUP url is wrong. Please ensure that it starts with https://"
        )
