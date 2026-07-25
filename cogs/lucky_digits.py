import asyncio
from discord.ext import commands
from utils import *
from utils.db.meeplets import *

class LuckyDigits(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.reward = 10

  @commands.Cog.listener()
  async def on_message(self, msg):
    if "6969" in str(msg.id):
      await bom_add_meeplets(msg.author.name, self.reward)
      await msg.reply(embed=discord.Embed(description=f"🍀 This message is considered lucky by BoM. Have 💰 {str(self.reward)} meeplets 🍀"))

async def setup(bot):
  await bot.add_cog(LuckyDigits(bot))
