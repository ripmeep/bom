from discord.ext import commands
from utils.config import OWNER_IDS


def is_owner():
  async def predicate(ctx):
    status = ctx.author.id in OWNER_IDS
    if not status:
      await ctx.message.add_reaction("🖕")
    return status
  return commands.check(predicate)

