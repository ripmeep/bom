import aiosqlite
import utils.config
from utils.logging import bom_log

async def bom_get_meeplets(username: str) -> int:
  try:
    async with aiosqlite.connect(utils.config.DB_PATH) as db:
      async with db.execute('SELECT meeplets FROM bom WHERE username = ?', (username,)) as cur:
        row = await cur.fetchone()
        if row:
          return row[0]
        else:
          await db.execute('INSERT INTO bom (username, meeplets) VALUES (?, ?)', (username, 0))
          await db.commit()
          return 0
  except Exception as e:
    await bom_log("Error in bom_get_meeplets: " + str(e))
    pass

async def bom_set_meeplets(username, meeplets):
  try:
    async with aiosqlite.connect(utils.config.DB_PATH) as db:
      await db.execute('UPDATE bom SET meeplets = ? WHERE username = ?', (meeplets, username))
      await db.commit()
    return True
  except Exception as e:
    await bom_log("Error in bom_set_meeplets: " + str(e))
    return False

async def bom_add_meeplets(username, meeplets):
  user_meeplets = await bom_get_meeplets(username)
  new_meeplets = user_meeplets + meeplets
  status = await bom_set_meeplets(username, new_meeplets)

  return status

async def bom_get_top(x):
  async with aiosqlite.connect(utils.config.DB_PATH) as db:
    async with db.execute('SELECT username,meeplets FROM bom ORDER BY meeplets DESC LIMIT ?', ((x + len(utils.config.LEADERBOARD_BLACKLIST)),)) as cur:
      rows = await cur.fetchall()
  return rows

