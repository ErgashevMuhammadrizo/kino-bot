import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
DB_CHANNEL_ID = int(os.getenv("DB_CHANNEL_ID", "0"))        # Baza kanali (video saqlash)
MAIN_CHANNEL_ID = int(os.getenv("MAIN_CHANNEL_ID", "0"))    # Rasmiy kanal (post e'lon)
