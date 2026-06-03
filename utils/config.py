import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

CONFESSIONS_CHANNEL_ID = int(os.getenv("CONFESSIONS_CHANNEL_ID"))
PREDICTION_CHANNEL_ID = int(os.getenv("PREDICTION_CHANNEL_ID"))
PREDICTION_ROLE_ID = int(os.getenv("PREDICTION_ROLE_ID"))

OWNER_ID = int(os.getenv("OWNER_ID"))

FOOTBALL_DATA_API_KEY = os.getenv(
    "FOOTBALL_DATA_API_KEY"
)