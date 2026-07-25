import random
import datetime
import discord
import asyncio
from datetime import datetime, timedelta
from discord.ext import commands, tasks
import utils.config
from utils import *
from utils.bot import *
from utils.db.meeplets import *

class Work(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.active_work = None
    self.work_timeout = None
    self.min_time = 40
    self.max_time = 120
    self.start = 9
    self.finish = 2
    self.open = False
    self.next_work_time = datetime.now() + timedelta(minutes=random.randint(self.min_time, self.max_time))
    self.work_scheduler.start()
    self.active_work_message = None
    self.active_embed = None
    self.expiry = 30
    self.reward = 5

  def cog_unload(self):
    self.work_scheduler.stop()
    if self.work_timeout:
      self.work_timeout.cancel()

  @tasks.loop(minutes=1)
  async def work_scheduler(self):
    if self.active_work is not None:
      return

    if datetime.now() >= self.next_work_time:
      await self.generate_work()

  @work_scheduler.before_loop
  async def before_scheduler(self):
    await self.bot.wait_until_ready()

  async def generate_work(self):
    channel = self.bot.get_channel(utils.config.MEEPVILLE_CHANNEL_ID)
    if not channel:
      return

    hour = datetime.now().hour
    if hour < self.start and hour > self.finish:
      if self.open:
        await channel.send(embed=discord.Embed(title="🏁 Workplace has closed for the day", description="Thank you all for your hard work..."))
        self.open = False
      return
    else:
      self.open = True

    challenge_type = random.choice(['math', 'anagram'])
    title = "⚠️ WORKPLACE CHALLENGE\n\n"
    prefix = ""
    if challenge_type == 'math':
      prefix += "🧮 Maths work: "
      num1 = random.randint(1, 99)
      num2 = random.randint(1, 99)
      num3 = random.randint(1, 99)

      operators = random.sample(['+', '-', '*'], 2)

      challenge = f"{num1} {operators[0]} {num2} {operators[1]} {num3}"
      dchallenge = challenge.replace('*', 'x')
      prefix += f"**{dchallenge}**\n\n"
      answer = str(eval(challenge))
    elif challenge_type == 'anagram':
      prefix += "🔀 Anagram work: "

      with open(utils.config.KEYWORD_WORDLIST_PATH, "r") as f:
        answer = random.choice([x.strip() for x in f.readlines()]).lower()

      challenge = "".join(random.sample(answer, len(answer)))
      while challenge == answer:
        challenge = "".join(random.sample(answer, len(answer)))

      prefix += "Unscramble this word -> " + challenge + "\n"

    self.active_work = answer

    await bom_log(f'New work generated - challenge: {challenge} | answer: {answer}')

    embed=discord.Embed(title=title, description=prefix)
    embed.set_footer(text=f"Expires in {str(self.expiry)} minutes. First correct answer wins")

    self.active_work_message = await channel.send(embed=embed)
    self.active_work_embed = embed

    self.work_timeout = asyncio.create_task(
      self.handle_timeout(channel, answer)
    )

  async def handle_timeout(self, channel, current_answer):
    await asyncio.sleep(self.expiry * 60)

    if self.active_work == current_answer:
      self.active_work = None
      
      self.next_work_time = datetime.now() + timedelta(minutes=random.randint(self.min_time, self.max_time))

      embed = discord.Embed(title="⏰ Work expired", description="Nobody finished the work in time.\nThe answer was: " + current_answer)
      await self.active_work_message.reply(embed=embed)

      self.active_work_message = None
      self.active_work_message_embed = None

  @commands.Cog.listener()
  async def on_message(self, msg):
    if msg.author.bot or self.active_work is None:
      return

    is_reply = msg.reference and msg.reference.message_id == self.active_work_message.id

    if not is_reply:
        return

    if msg.content.strip().lower() == self.active_work.lower():
      if self.work_timeout:
        self.work_timeout.cancel()

      correct_answer_display = self.active_work.title()
      self.active_work = None
      self.active_work_message = None
      self.active_work_embed = None

      self.next_work_time = datetime.now() + timedelta(minutes=random.randint(self.min_time, self.max_time))

      embed = discord.Embed(title="🎉 Work complete!", description=f"{msg.author.display_name} submitted their work correctly.\nAnswer: **{correct_answer_display}**")
      embed.add_field(name="Earnings", value=f"💰 {str(self.reward)} meeplets")

      await msg.add_reaction("✅")
      await msg.reply(embed=embed)
      await bom_add_meeplets(msg.author.name, self.reward)
    else:
      await msg.add_reaction("❌")

  @commands.command(name="work_time")
  @is_owner()
  async def work_time(self, ctx, minutes: int = None):
    if minutes:
      self.next_work_time = self.next_work_time + timedelta(minutes=minutes)

    await ctx.reply(embed=discord.Embed(description=f"⏰ Next work at {str(self.next_work_time)}"))

  @work_time.error
  async def work_time_error(self, ctx, error):
    await bom_log(f'{ctx.author.name} tried work_add without permission: {error}')

async def setup(bot):
  await bot.add_cog(Work(bot))


