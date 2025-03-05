# config\bot_config.py
import os
import logging
from dotenv import load_dotenv

load_dotenv()

class BotConfig:
    TOKEN = os.getenv("Token_Discord_Bot")
    if not TOKEN:
        raise ValueError("❌ Discord токен не найден в .env файле!")
    else:
        logging.info("✅ Токен соответствует")
    OWNER_ID = int(os.getenv('OwnerID', 0))
    DATABASE_NAME = "game.db"
    LOG_FILE = 'bot.log'

    # Интенты
    INTENTS_CONFIG = {
        'messages': True,
        'guilds': True,
        'message_content': True,
        'members': True
    }
