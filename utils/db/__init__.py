import aiosqlite
from utils.config import DB_PATH

async def bom_initialize():
  async with aiosqlite.connect(DB_PATH) as db:
    await db.execute('''
      CREATE TABLE IF NOT EXISTS bom (
        user_id INTEGER PRIMARY KEY,
        username STRING NOT NULL,
        meeplets INTEGER DEFAULT 0
      )
    ''')

    await db.commit()

