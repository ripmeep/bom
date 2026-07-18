#!/usr/bin/env python3

import os
import time
import discord
import aiosqlite
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
DB_PATH = 'db/bom.db'
OWNER_IDS = [
  253283008990150656 # meep
]

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/bom ", intents=intents)

bom_shop = {
  "meep_backup": {
    "title": "Meep Backup",
    "description": "Meep will back you up in an argument or debate for 24 hours as long as it isn't an offensive point of view.",
    "cost": 5
  },

  "meep_truth": {
    "title": "Meep Truth",
    "description": "You get to ask meep 1 truth question, and he will answer HONESTLY, as long as it doesn't dox him or put him in danger",
    "cost": 3
  }
}

async def bom_log(s):
  print(f'[{time.ctime()}] {s}')

@bot.event
async def on_ready():
  await bom_log(f'Activated - {bot.user.name} (ID: {bot.user.id})')

  async with aiosqlite.connect(DB_PATH) as db:
    await db.execute('''
      CREATE TABLE IF NOT EXISTS bom (
        user_id INTEGER PRIMARY KEY,
        username STRING NOT NULL,
        meeplets INTEGER DEFAULT 0
      )
    ''')

    await db.commit()

  await bom_log("BoM database initialized")

@bot.event
async def on_message(msg):
  await bom_log(f'{msg.guild.name}#{msg.channel.name} | {msg.author.name}: {msg.content}')
  await bot.process_commands(msg)

async def bom_get_meeplets(username: str) -> int:
  try:
    async with aiosqlite.connect(DB_PATH) as db:
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

def bom_is_owner():
  async def predicate(ctx):
    return ctx.author.id in OWNER_IDS
  return commands.check(predicate)

def bom_cb_wrap(s):
  return '```\n' + s + '\n```'

async def bom_update_meeplets(username, meeplets):
  try:
    async with aiosqlite.connect(DB_PATH) as db:
      await db.execute('UPDATE bom SET meeplets = ? WHERE username = ?', (meeplets, username))
      await db.commit()
    return True
  except Exception as e:
    await bom_log("Error in bom_update_meeplets: " + str(e))
    return False

@bot.command()
async def balance(ctx, username: str = None):
  username = username or ctx.author.name
  user_meeplets = await bom_get_meeplets(username)
  await ctx.reply(bom_cb_wrap(f'💰 {username} balance: {user_meeplets} meeplets'))

@bot.command()
async def shop(ctx, member: discord.Member = None):
  builder = []
  for item in bom_shop:
    i = bom_shop[item]
    builder.append(bom_cb_wrap(i['title'] + ': ' + i['description'] + '\n(' + str(i['cost']) + ' meeplets 💰)'))
  await ctx.reply('\n'.join(builder))

@bot.command()
@bom_is_owner()
async def award(ctx, username: str, amount: int):
  user_meeplets = await bom_get_meeplets(username)
  new_meeplets = user_meeplets + amount

  status = await bom_update_meeplets(username, new_meeplets)

  if status:
    await ctx.reply(bom_cb_wrap(f'Awarded {amount} meeplets to {username}'))

@award.error
async def award_error(ctx, error):
  await bom_log(f'{ctx.author.name} tried to award meeplets without permission: {error}')

@bot.command()
async def buy(ctx, *args):
  item_title = " ".join(args)
  try:
    item = bom_shop[list(filter(lambda x: bom_shop[x]['title'].lower() == item_title.lower(), list(bom_shop.keys())))[0]]
  except:
    await ctx.reply(bom_cb_wrap(f'I don\'t sell "{item_title}", silly'))
    return

  username = ctx.author.name
  cost = item['cost']
  user_meeplets = await bom_get_meeplets(username)

  if cost > user_meeplets:
    await ctx.reply(bom_cb_wrap(f'You don\'t have enough meeplets for a "{item_title}"'))
    return

  new_meeplets = user_meeplets - cost
  status = await bom_update_meeplets(username, new_meeplets)

  if status:
    await ctx.reply(bom_cb_wrap(f'Cha-ching, you bough a "{item_title}" - make sure meep is aware...'))

  try:
    meep = await bot.fetch_user(OWNER_IDS[0])
    await meep.send(bom_cb_wrap(f'''
NEW PURCHASE:
    {username} bought {item_title} in {ctx.guild.name}!
    {cost} meeplets spent 💰
    New balance: {new_meeplets}
'''))
  except Exception as e:
    await bom_log('Error in buy during notification: ' + str(e))

bot.run(TOKEN)
