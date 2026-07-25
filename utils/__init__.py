import discord

def cb_wrap(s):
  return '```\n' + s + '\n```'

def embed_wrap(title="", description="", footer=None):
  embed = discord.Embed(title=title, description=description)

  if footer:
      embed.set_footer(text=footer)

  return embed
