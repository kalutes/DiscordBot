# moon.py

import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('MOON_TOKEN')
PREFIX = os.getenv('MOON_PREFIX')

print("Initializing bot with prefix")
print(PREFIX)

bot = commands.Bot(command_prefix=commands.when_mentioned_or(PREFIX),
                   description='Welcomes users')

@bot.command(name='shib', help='Prints the current SHIB price')
async def add_welcome(ctx):
    await ctx.send("SHIB TO THE MOON!")

@bot.event
async def on_ready():
    print('Welcome Logged in as {0} ({0.id})'.format(bot.user))
    print('------')

    for vc in bot.voice_clients:
        await vc.disconnect()
 
bot.run(TOKEN)
