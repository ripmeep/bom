import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

OWNER_IDS = [253283008990150656] # ripmeep
ARCANE_ID = 437808476106784770 # Arcane bot ID for meeplets on level up
MEEPVILLE_CHANNEL_ID = 1558600527116501022
#MEEPVILLE_CHANNEL_ID = 1512822872349868217 # DEBUG

LEADERBOARD_BLACKLIST = [
  'acroes',
  '5tarl3t',
  'ripmeep'
]

DB_PATH = "db/bom.db"
KEYWORD_WORDLIST_PATH = "./keyword.txt"
COGS_DIR = "./cogs"
TRIVIA_URL="https://opentdb.com/api.php?amount=1&type=multiple"
REBUS_DATASET="./rebus_dataset.csv"
REBUS_IMAGE_DIR="./rebus_images"

MEEPLET_SHOP = {
  "meep_backup": {
    "title": "Meep Backup",
    "description": "Meep will back you up in an argument or debate for 24 hours as long as it isn't an offensive point of view.",
    "cost": 10
  },

  "meep_truth": {
    "title": "Meep Truth",
    "description": "You get to ask meep 1 truth question, and he will answer HONESTLY, as long as it doesn't dox him or put him in danger",
    "cost": 5
  },

  "meep_rename": {
    "title": "Meep Rename",
    "description": "You get to change Meep's server name for a FULL 24 hours - nothing offensive to anyone (unless it's meep himself, he can take it).",
    "cost": 15
  },

  "timeout target": {
    "title": "Timeout Target",
    "description": "Timeout anyone in the server for 10 minutes (will need to ask an admin after purchase)",
    "cost": 50
  }
}


