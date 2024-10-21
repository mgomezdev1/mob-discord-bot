import logging
import asyncio
import time

import discord
from discord.ext import commands

from config import get_config

config = get_config()
logger = logging.Logger(__name__)

intents = discord.Intents.all()
intents.message_content = True

bot = commands.Bot(command_prefix=config.prefix, help_command=commands.MinimalHelpCommand(), intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return
    
    await bot.process_commands(message)

async def load_cogs():
    for cog in config.cogs:
        await bot.load_extension(f"cogs.{cog}")

async def setup():
    await load_cogs()

asyncio.run(setup())
bot.run(config.token)