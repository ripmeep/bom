import random
import datetime
import discord
import asyncio
import aiohttp
import html
import os 
import string
import csv

from enum import Enum
from io import BytesIO
from captcha.image import ImageCaptcha 
from datetime import datetime, timedelta
from discord.ext import commands, tasks

import utils.config
from utils import *
from utils.bot import *
from utils.db.meeplets import *

class Work(commands.Cog):
  class Challenge:
    class Type(Enum):
      MATH = 1
      ANAGRAM = 2
      TRIVIA = 3
      MASTERMIND = 4
      CAPTCHA = 5
      REBUS = 6

    def __init__(self):
      self.type = None
      self.answer = None
      self.case_sensitive = False
      self.description = None
      self.one_shot = False
      self.answered_users = set()
      self.reward = 5
      self.expiry = 5
      self.image = None

    @staticmethod
    async def GenerateWorkMath():
      numbers = [random.randint(1, 99) for _ in range(3)]
      operators = random.sample(["+", "-", "*"], 2)
      description = f"{numbers[0]} {operators[0]} {numbers[1]} {operators[1]} {numbers[2]}"

      challenge = Work.Challenge()
      challenge.type = Work.Challenge.Type.MATH
      challenge.answer = str(eval(description))
      challenge.description = (
        f"🧮 Maths work - Solve the following:\n\n"
        f"**{description.replace('*', 'x')}**\n"
      )

      return challenge

    @staticmethod
    async def GenerateWorkAnagram():
      with open(utils.config.KEYWORD_WORDLIST_PATH, "r") as f:
        word = random.choice(f.readlines()).strip().lower()

      challenge = Work.Challenge()
      challenge.type = Work.Challenge.Type.ANAGRAM
      challenge.answer = word

      tmp = list(word)
      random.shuffle(tmp)
      scrambled = "".join(tmp)

      challenge.description = (
        f"🔀 Anagram work - Unscramble the following:\n\n" 
        f"**{scrambled}**\n"
      )

      challenge.reward = len(word)

      return challenge

    @staticmethod
    async def GenerateWorkTrivia():
      timeout = aiohttp.ClientTimeout(total=15)
      async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(utils.config.TRIVIA_URL) as response:
          if response.status != 200:
            await bom_log(f"Failed to get trivia question from API f{utils.config.TRIVIA_API} ({response.status})")
            return None
          data = await response.json()

      response_code = data.get("response_code", None)
      if response_code is None or not data.get("results"):
        await bom_log(f"Trivia question 'respons_code' was invalid: {response_code}")
        return None

      question_data = data["results"][0]
      category  = html.unescape(question_data["category"])
      question  = html.unescape(question_data["question"])
      correct   = html.unescape(question_data["correct_answer"])
      incorrect = [html.unescape(answer) for answer in question_data["incorrect_answers"]]
      options = incorrect + [correct]
      random.shuffle(options)
      prefixes = ["A", "B", "C", "D"]
      answer = None
      description = f"🧠 Trivia work: **{question}**\n\n"
      
      for index, option in enumerate(options):
        if option == correct:
          answer = prefixes[index]
        description += f"**{prefixes[index]}**: {option}\n"

      description += (
        f"\n**Category**: {category}\n"
        "**Instructions**: Reply with A, B, C, or D (one shot only)"
      )

      challenge = Work.Challenge()
      challenge.type = Work.Challenge.Type.TRIVIA
      challenge.answer = answer
      challenge.description = description
      challenge.one_shot = True

      return challenge

    @staticmethod
    async def GenerateWorkMastermind():
      answer = " ".join(random.sample(string.digits, 4))

      challenge = Work.Challenge()
      challenge.type = Work.Challenge.Type.MASTERMIND
      challenge.answer = answer
      challenge.reward = 15
      challenge.expiry = 9

      challenge.description = (
        "🧠 **Mastermind work!**\n\n"
        "Be the first to crack the four-number combination.\n\n" 
        "**How to play**:\n" 
        "- Reply with a four-number combination (I.E: 1234).\n" 
        "- :white_check_mark: = Correct digit and position.\n" 
        "- :record_button: = Correct digit, wrong position.\n" 
        "- :no_entry: = Incorrect digit.\n\n" 
        "**Unlimited guesses - reply to this message to attempt.**\n" 
        f"First to solve wins 💰 {challenge.reward} meeplets"
      )

      return challenge

    @staticmethod
    async def GenerateWorkCaptcha():
      characters = string.ascii_uppercase + string.digits + string.ascii_lowercase
      challenge = Work.Challenge()
      challenge.type = Work.Challenge.Type.CAPTCHA
      challenge.answer = "".join(random.choices(characters, k=6))
      challenge.case_sensitive = True
      challenge.description = (
        f"🤖 **CAPTCHA work!**\n\n" 
        "Please prove you are not a clanker and type out the CAPTCHA."
        )
    
      buffer = BytesIO()
      c = ImageCaptcha(width=280, height=100)
      i = c.generate_image(challenge.answer)
      i.save(buffer, format="PNG")
      buffer.seek(0)

      challenge.image = buffer

      return challenge

    @staticmethod
    async def GenerateWorkRebus():
      with open(utils.config.REBUS_DATASET, "r") as csvfile:
        rows = list(csv.reader(csvfile))
      image_path, answer = random.choice(rows)
      print(image_path, answer)
      masked = "`" + "".join([char if char in string.punctuation or char.isspace() else '_' for char in answer]) + "`"

      challenge = Work.Challenge()
      challenge.type = Work.Challenge.Type.REBUS
      challenge.reward = 10
      challenge.answer = answer
      challenge.description = (
        f"🖼️ **REBUS work!**\n\n"
        "Can you figure out the meaning/phrase this image is describing?\n"
        "Answer by replying to this message.\n\n"
        f"**Hint**: {masked}"
      )

      with open(os.path.join(utils.config.REBUS_IMAGE_DIR, image_path), "rb") as f:
        buffer = BytesIO(f.read())
      buffer.seek(0)

      challenge.image = buffer

      return challenge

  def __init__(self, bot):
    self.bot = bot

    # Timings
    self.min_time = 10
    self.max_time = 60
    self.next_work_time = datetime.now() + timedelta(minutes=random.randint(self.min_time, self.max_time))
    self.work_timeout = None
    self.work_scheduler.start()

    # Active work
    self.active_work = None
    self.active_work_message = None
    self.active_work_embed = None

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

  def schedule_next_work(self):
    self.next_work_time = datetime.now() + timedelta(minutes=random.randint(self.min_time, self.max_time))

  async def generate_work(self, debug: Challenge.Type=None):
    channel = self.bot.get_channel(utils.config.MEEPVILLE_CHANNEL_ID)
    if not channel:
      return

    title = "⚠️ WORKPLACE CHALLENGE\n\n"
    
    game_modes = [
#      Work.Challenge.GenerateWorkMath,
      Work.Challenge.GenerateWorkAnagram,
      Work.Challenge.GenerateWorkTrivia,
      Work.Challenge.GenerateWorkMastermind,
      Work.Challenge.GenerateWorkCaptcha,
      Work.Challenge.GenerateWorkRebus
    ]

    generator = random.choice(game_modes)

    if debug is not None:
      generator = game_modes[debug.value - 1]

#    try:
    self.active_work = await generator()
    if self.active_work is None:
      self.schedule_next_work()
      return
    #except Exception as e:
    #  await bom_log(f"Failed to generate work: {e}")
    #  self.schedule_next_work()

    self.active_work.answered_users.clear()

    await bom_log(f"New work generated: description={self.active_work.description} | type={self.active_work.type} | answer: {self.active_work.answer}")

    embed = discord.Embed(
      title=title,
      description=self.active_work.description,
    )

    embed.set_footer(
      text=f"Expires in {self.active_work.expiry} minutes. First to answer correctly wins"
    )

    if self.active_work.image:
      self.active_work.image.seek(0)
      file = discord.File(self.active_work.image, filename="captcha.png")
      embed.set_image(url="attachment://captcha.png")
     
      self.active_work_embed = embed
      self.active_work_message = await channel.send(embed=embed, file=file)
    else:
      self.active_work_embed = embed
      self.active_work_message = await channel.send(embed=embed)
    
    self.work_timeout = asyncio.create_task(
      self.handle_timeout(
        self.active_work_message,
        self.active_work.answer
      )
    )

  async def handle_timeout(self, message, current):
    try:
      await asyncio.sleep(self.active_work.expiry * 60)
      if self.active_work.answer != current:
        return

      self.active_work = None
      self.active_work_message = None
      self.active_work_embed = None
      self.work_timeout = None
      self.schedule_next_work()

      embed = discord.Embed(
        title="⏰ Work expired",
        description=(
          "Nobody finished the work in time.\n" 
          f"The answer was: **{current_answer}**"
        ),
      )

      await message.reply(embed=embed)
    except asyncio.CancelledError:
      pass
        

  @commands.Cog.listener()
  async def on_message(self, msg):
    if msg.author.bot or self.active_work is None or self.active_work_message is None:
      return

    is_reply = (msg.reference and self.active_work_message is not None) and msg.reference.message_id == self.active_work_message.id

    if not is_reply:
      return

    if self.active_work.one_shot and msg.author.id in self.active_work.answered_users:
      return

    submitted_answer = msg.content.strip().lower()

    win = False
    if self.active_work.type == Work.Challenge.Type.MASTERMIND:
      win = await self.handle_mastermind(msg) 
    else:
      win = (msg.content.strip() == self.active_work.answer) if self.active_work.case_sensitive else (submitted_answer == self.active_work.answer.lower())

    if win:
      if self.work_timeout:
        self.work_timeout.cancel()
        self.work_timeout = None

      correct_answer = self.active_work.answer.title()
      
      reward = self.active_work.reward
      self.active_work = None
      self.active_work_message = None
      self.active_work_embed = None
      self.schedule_next_work()

      embed = discord.Embed(
        title="🎉 Work complete!",
        description=(
          f"{msg.author.display_name} submitted their work correctly.\n" 
          f"Answer: **{correct_answer}**"
        ),
      )

      embed.add_field(
        name="Earnings",
        value=f"💰 {reward} meeplets",
      )

      await msg.add_reaction("✅")
      await msg.reply(embed=embed)
      await bom_add_meeplets(
        msg.author.name,
        reward
      )

    else:
      if self.active_work.one_shot:
        self.active_work.answered_users.add(msg.author.id)
      await msg.add_reaction("❌")
  
  async def handle_mastermind(self, msg):
    challenge = self.active_work
    guess = list(msg.content.replace(" ", ""))
    answer = list(self.active_work.answer.replace(" ",""))

    if len(guess) != len(answer) or any(c not in string.digits for c in guess):
      await msg.reply(embed=discord.Embed(description="❌ Submit exactly four digits."))
      return

    feedback = []
    accounted = []
    correct = 0

    for i in range(len(answer)):
      if guess[i] == answer[i] and guess[i] not in accounted:
        feedback.append(":white_check_mark:")
        correct += 1
        accounted.append(guess[i])
      elif guess[i] in answer and guess[i] not in accounted:
        feedback.append(":record_button:")
        accounted.append(guess[i])
      else:
        feedback.append(":no_entry:")

    feedback_text = " ".join(feedback)

    if correct == 4:
      return True

    digit_emojis = [':zero:', ':one:', ':two:', ':three:', ':four:', ':five:', ':six:', ':seven:', ':eight:', ':nine:']

    await msg.reply(
      embed=discord.Embed(
        description=(
          f"`Your guess`: {' '.join([digit_emojis[int(g)] for g in guess])}\n" 
          f"`Feedback  `: {feedback_text}"
        )
      )
    )

    return False

  @commands.command(name="work_time")
  @is_owner()
  async def work_time(self, ctx, minutes: int = None):
    if minutes:
      self.next_work_time = self.next_work_time + timedelta(minutes=minutes)

    await ctx.reply(embed=discord.Embed(description=f"⏰ Next work at {str(self.next_work_time)}"))

  @commands.command(name="work_debug")
  @is_owner()
  async def work_debug(self, ctx, type: int = 1):
    type = Work.Challenge.Type(type)
    await self.generate_work(debug=type)

  @work_time.error
  async def work_time_error(self, ctx, error):
    await bom_log(f'{ctx.author.name} tried work_add without permission: {error}')

async def setup(bot):
  await bot.add_cog(Work(bot))
