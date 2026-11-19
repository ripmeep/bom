import asyncio
import discord
from discord.ext import commands
from utils import *
from utils.db.meeplets import *
from utils.bot import *

class BoM(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.command(name="balance")
  async def balance(self, ctx, username: str = None):
    username = username or ctx.author.name
    user_meeplets = await bom_get_meeplets(username)
    await ctx.reply(embed=discord.Embed(title=f"**{username}** Balance", description=f"💰 {user_meeplets} meeplets"))

  @commands.command(name="transfer")
  async def transfer(self, ctx, username: str = None, meeplets = 0):
    if meeplets <= 0 or username is None:
      return

    from_username = ctx.author.name
    if username == from_username:
      return

    from_balance = await bom_get_meeplets(from_username)

    if (from_balance < meeplets):
      await ctx.reply(embed=discord.Embed(description="🍃 You don't have enough meeplets for that transfer"))
      return

    new_from_balance = from_balance - meeplets
    to_balance = await bom_get_meeplets(username)
    new_to_balance = to_balance + meeplets

    await bom_set_meeplets(from_username, new_from_balance)
    await bom_set_meeplets(username, new_to_balance)
    await ctx.reply(embed=discord.Embed(description=f"🔁 Transferred 💰 {str(meeplets)} meeplets to **{username}**"))

  @commands.command(name="shop")
  async def shop(self, ctx):
    builder = []
    for item in dict(sorted(utils.config.MEEPLET_SHOP.items(), key=lambda x: x[1]['cost'])):
      i = utils.config.MEEPLET_SHOP[item]
      builder.append(f"**Name**: {i['title']}\n**Description**: {i['description']}\n**Cost**: 💰 {i['cost']} meeplets\n") 
    embed = discord.Embed(title="Meeplet Shop", description='\n'.join(builder))
    await ctx.reply(embed=embed)

  @commands.command(name="award")
  @is_owner()
  async def award(self, ctx, username: str, amount: int):
    status = await bom_add_meeplets(username, amount)

    if status:
      await ctx.reply(embed=discord.Embed(description=f"Awarded 💰 {amount} meeplets to {username}"))

  @award.error
  async def award_error(self, ctx, error):
    await bom_log(f'{ctx.author.name} tried to award meeplets without permission: {error}')

  @commands.command(name="buy")
  async def buy(self, ctx, *args):
    item_title = " ".join(args)

    try:
      item = utils.config.MEEPLET_SHOP[list(filter(lambda x: utils.config.MEEPLET_SHOP[x]['title'].lower() == item_title.lower(), list(utils.config.MEEPLET_SHOP.keys())))[0]]
    except:
      await ctx.reply(embed=discord.Embed(description=f"I don't sell **{item_title}**, silly"))
      return

    username = ctx.author.name
    cost = item['cost']
    user_meeplets = await bom_get_meeplets(username)

    if cost > user_meeplets:
      await ctx.reply(embed=discord.Embed(description=f"You don't have enough meeplets for a **{item_title}**"))
      return

    new_meeplets = user_meeplets - cost
    status = await bom_set_meeplets(username, new_meeplets)

    if status:
      await ctx.reply(embed=discord.Embed(description=f"💰 Cha-ching, you bough a **{item_title}** - make sure meep is aware..."))

    try:
      meep = await self.bot.fetch_user(utils.config.OWNER_IDS[0])
      embed = discord.Embed(title="New Purchase", description=f"**User**: {username}\n**Server**: {ctx.guild.name}\n**Cost**: 💰 {cost} meeplets")
      await meep.send(embed=embed)
    except Exception as e:
      await bom_log('Error in buy during noticiation: ' + str(e))

  @commands.command(name="leaderboard")
  async def leaderboard(self, ctx, *args):
    try:
      rows = await bom_get_top(10)
      embed = discord.Embed(title="🏆 Top 10 Meeplet Leaderboard")
      builder = []
      i = 0

      for u, m in rows:
        if u in utils.config.LEADERBOARD_BLACKLIST:
          continue
        builder.append("%2d. %s (💰 %s meeplets)"%(i + 1, u.ljust(16), str(m).ljust(3)))
        i += 1

      embed.description = cb_wrap('\n'.join(builder))
      await ctx.reply(embed=embed)
    except Exception as e:
      await bom_log('Error in leaderboard command: ' + str(e))

  @commands.command(name="message")
  @is_owner()
  async def message(self, ctx, channel_id: int, *args):
    channel = self.bot.get_channel(channel_id)
    content = ' '.join(args)

    async with ctx.typing():
      await asyncio.sleep(0.1 * len(args))
    await channel.send(' '.join(args))

  @message.error
  async def message_error(self, ctx, error):
    await bom_log(f'{ctx.author.name} tried to use message command without permission: {error}')

async def setup(bot):
  await bot.add_cog(BoM(bot))

