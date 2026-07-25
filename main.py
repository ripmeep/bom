#!/usr/bin/env python3

import os
import discord
from discord.ext import commands

import utils.config
from utils import *
from utils.bot import *
from utils.db import *
from utils.db.meeplets import *
from utils.logging import *

class BoMBot(commands.Bot):
  def __init__(self):
    intents = discord.Intents.default()
    intents.message_content = True

    super().__init__(command_prefix="/bom ", intents=intents)

  async def setup_hook(self):
    for fname in os.listdir(utils.config.COGS_DIR):
      if fname.endswith('.py'):
        await self.load_extension(f'cogs.{fname[:-3]}')
        await bom_log("Loaded extension: " + fname[:-3])

  async def on_ready(self):
    await bom_log(f'Activated - {bot.user.name} (ID: {bot.user.id})')
    await bom_initialize()
    await bom_log("BoM database initialized")

  async def on_message(self, msg):
    if msg.guild:
      await bom_log(f'{msg.id}\t{msg.guild.name}#{msg.channel.name} | {msg.author.name}: {msg.content}')

      if msg.author.id == utils.config.ARCANE_ID and 'has reached level' in msg.content and msg.mentions:
        user = msg.mentions[0]
        await bom_add_meeplets(user.name, 1)
        await bom_log(f'{user.name} levelled up in {msg.guild.name} - awarded 1 meeplet')
    else:
      await bom_log(f'PRIVATE MESSAGE | {msg.author.name}: {msg.content}')

    await self.process_commands(msg)

bot = BoMBot()
bot.run(utils.config.TOKEN)
