import random
import discord
import datetime
from discord.ext import commands, tasks
import utils.config
from utils import *
from utils.bot import *
from utils.db.meeplets import *

LOCAL_TZ = datetime.datetime.now().astimezone().tzinfo

class Keyword(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.current_keyword = None

    with open(utils.config.KEYWORD_WORDLIST_PATH, "r") as f:
        self.current_keyword = random.choice([line.strip().lower() for line in f.readlines()])

    self.reward = len(self.current_keyword)
    self.daily_winners = set()
    self.change_keyword_daily.start()

  def cog_unload(self):
    self.change_keyword_daily.stop()

  @tasks.loop(time=datetime.time(hour=0, minute=0, tzinfo=LOCAL_TZ))
  async def change_keyword_daily(self):
    await self.bot.wait_until_ready()
    await self._execute_change_keyword_daily(notify=True)

  async def _execute_change_keyword_daily(self, notify=True):
    with open(utils.config.KEYWORD_WORDLIST_PATH, "r") as f:
      words = [line.strip().lower() for line in f.readlines()]

    if words:
      if notify:
        channel = self.bot.get_channel(utils.config.MEEPVILLE_CHANNEL_ID)
        notification = await channel.send(embed=discord.Embed(title=f"✅ Today\'s keyword was **{self.current_keyword}**", description="People who found it:\n" + cb_wrap("\n".join(self.daily_winners)) if len(self.daily_winners) > 0 else "No winners today..."))

      self.current_keyword = random.choice(words)
      self.daily_winners.clear()

      if notify:
        await notification.reply(embed=discord.Embed(description="📝 A new keyword has been chosen... Good luck, Meepolians..."))
        await bom_log(f'New keyword is "{self.current_keyword}"')

      self.reward = len(self.current_keyword)

  @commands.Cog.listener()
  async def on_message(self, msg):
    if msg.author.bot or not self.current_keyword or msg.author.name in self.daily_winners:
      return

    if self.current_keyword.lower() in msg.content.lower() and msg.author.id not in utils.config.OWNER_IDS:
      await bom_log(msg.author.name + " found the keyword")
      await bom_add_meeplets(msg.author.name, self.reward)
      self.daily_winners.add(msg.author.name)

  @commands.command(name="keyword_reset")
  @is_owner()
  async def keyword_set(self, ctx, keyword: str=None):
    if keyword:
      self.current_keyword = keyword
      self.daily_winners.clear()
      self.reward = len(keyword)
    else:
      await self._execute_change_keyword_daily(notify=False)
    await bom_log(f'Keyword reset to "{self.current_keyword}"')

  @keyword_set.error
  async def keyword_set_error(self, ctx, error):
    await bom_log(f'{ctx.author.name} tried to use keyword_set without permission: {error}')

async def setup(bot):
    kw = Keyword(bot)
    await bom_log(f'Initialized Keyword with "{kw.current_keyword}"')
    await bot.add_cog(kw)
