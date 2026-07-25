import asyncio
import random
from discord.ext import commands
from utils import *
from utils.bot import *
from utils.logging import *
from utils.db.meeplets import *

class QuickDraw(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.reward = 5
    self.min_countdown = 15
    self.max_countdown = 200
    self.countdown = random.randint(self.min_countdown, self.max_countdown)

  @commands.Cog.listener()
  async def on_message(self, msg):
    if msg.channel.id == utils.config.MEEPVILLE_CHANNEL_ID:
      self.countdown -= 1

      if self.countdown == 0:
        channel = await self.bot.fetch_channel(utils.config.MEEPVILLE_CHANNEL_ID)
        qd_msg = await channel.send(embed=discord.Embed(title='🔫  QUICK DRAW', description=f"First to reply gets 💰 {str(self.reward)} meeplets"))

        def check_winner(msg):
          has_ref = msg.reference is not None

          if has_ref:
            is_reply = msg.reference.message_id == qd_msg.id
          else:
            is_reply = False

          return (msg.channel.id == utils.config.MEEPVILLE_CHANNEL_ID and not msg.author.bot and is_reply)

        try:
          winner = await self.bot.wait_for('message', check=check_winner, timeout=60.0)
          await bom_add_meeplets(winner.author.name, self.reward)
          await winner.reply(embed=discord.Embed(description=f'💥 You have been awarded 💰 {str(self.reward)} meeplets'))
        except asyncio.TimeoutError:
          await channel.send(embed=discord.Embed(description="⏰ Time's up. Quick draw failed"))

        self.countdown = random.randint(self.min_countdown, self.max_countdown)
        await bom_log(f'New quick draw countdown is {str(self.countdown)}')

  @commands.command(name="quickdraw_set")
  @is_owner()
  async def quickdraw_set(self, ctx, countdown: int):
    try:
      self.countdown = countdown
      await ctx.reply(embed=discord.Embed(description=f"🔫  QUICK DRAW set to {str(self.countdown)}"))
    except Exception as e:
      await bom_log('Error in quickdraw_set: ' + str(e))
      pass

  @quickdraw_set.error
  async def quickdraw_set_error(self, ctx, error):
    await bom_log(f'{ctx.author.name} tried to use quickdraw_set without permission: {error}')

async def setup(bot):
    qd = QuickDraw(bot)
    await bom_log(f'Initialized QuickDraw with countdown of {str(qd.countdown)}')
    await bot.add_cog(qd)
