# bot.py
import os
import random
import opuslib
import opuslib.api
import opuslib.api.encoder
import opuslib.api.decoder

import discord
import asyncio
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!')

@bot.event
async def on_voice_state_update(member, before, after):
    channel = after.channel

    if member.name == "honey boy":
        if channel is not None:
            voice_client = await channel.connect()
            audio_source = discord.FFmpegPCMAudio('bigmama.mp3')

            def disconnect(error):
                coro = voice_client.disconnect()
                fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)
                try:
                    fut.result()
                except:
                    # an error happened sending the message
                    pass

            if not voice_client.is_playing():
                voice_client.play(audio_source, after=disconnect)

bot.run(TOKEN)