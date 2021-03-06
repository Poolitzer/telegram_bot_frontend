"""
settings for corona-telegram bot
"""

import os
import dotenv
import environ
from pathlib import Path

# (corona/config/settings.py - 2 = corona/)
ROOT_DIR = (environ.Path(__file__) - 2)

# load bot token from .env
env_path = Path(ROOT_DIR) / '.env'
dotenv.load_dotenv(env_path)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Rooms
TELEGRAM_DOCTOR_ROOM = os.getenv("TELEGRAM_DOCTOR_ROOM")
TELEGRAM_PSYCHOLOGIST_ROOM = os.getenv("TELEGRAM_PSYCHOLOGIST_ROOM")
TELEGRAM_NEW_MEMBERS_ROOM = os.getenv("TELEGRAM_NEW_MEMBERS_ROOM")

# Chat settings
CHAT_SOCIAL_ENABLE_GIFS = os.getenv("CHAT_SOCIAL_ENABLE_GIFS", True)
CHAT_SOCIAL_ENABLE_PHOTOS = os.getenv("CHAT_SOCIAL_ENABLE_PHOTOS", True)
CHAT_SOCIAL_ENABLE_VOICE = os.getenv("CHAT_SOCIAL_ENABLE_VOICE", True)

CHAT_MEDICAL_ENABLE_GIFS = os.getenv("CHAT_MEDICAL_ENABLE_GIFS", True)
CHAT_MEDICAL_ENABLE_PHOTOS = os.getenv("CHAT_MEDICAL_ENABLE_PHOTOS", True)
CHAT_MEDICAL_ENABLE_VOICE = os.getenv("CHAT_MEDICAL_ENABLE_VOICE", True)

# Webhook configuration - If set to false we use long polling
USE_WEBHOOK = False
WEBHOOK_PORT = 9001
WEBHOOK_URL = "https://domain.example.com/" + TELEGRAM_BOT_TOKEN
CERTPATH = "/etc/certs/example.com/fullchain.cer"
