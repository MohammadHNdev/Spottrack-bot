import os
from dotenv import load_dotenv

# Load environment variables from .env file (recommended for security)
# Although values are hardcoded below as requested, keeping this line
# allows you to easily switch back to using a .env file later.
load_dotenv()

# Telegram Bot Settings
BOT_TOKEN = ""

# Spotify API Credentials
SPOTIPY_CLIENT_ID = ""
SPOTIPY_CLIENT_SECRET = ""

# MongoDB Database Settings
MONGO_URI = ""
MONGO_DB_NAME = ""

# Archive Channel ID
STORAGE_CHANNEL_ID = ""

# Payment Gateway URL (Optional)
PAYMENT_GATEWAY_URL = ""

# Bot Specific Settings
DOWNLOAD_LIMIT_PER_USER = 5
DEFAULT_LANGUAGE = "fa"

# Temporary directory for downloads
TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp_downloads")
os.makedirs(TEMP_DIR, exist_ok=True)

# --- Security Warning ---
# Hardcoding sensitive information like API keys and database credentials
# directly in the code is NOT recommended for production environments.
# It is a security risk. Consider using environment variables or a .env file
# to manage these secrets.
# ------------------------