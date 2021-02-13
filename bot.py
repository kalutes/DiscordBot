# bot.py
import os
import random
import opuslib
import opuslib.api
import opuslib.api.encoder
import opuslib.api.decoder

import os
from os import path
import discord
import asyncio
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix=commands.when_mentioned_or("8=D "),
                   description='Memes and stuff for Porns server')


@bot.command(name='welcome', help='Welcomes the specified user with the attached MP3 audio')
async def add_welcome(ctx, username):

    if len(ctx.message.attachments) < 1:
        print("Welcome command without mp3 audio")
        await ctx.send("You must attach a .mp3 file")
        return

    filename, file_extension = os.path.splitext(ctx.message.attachments[0].filename)

    if file_extension != '.mp3':
        print("Non .mp3 file attached")
        await ctx.send("Attached file is not a .mp3")
        return
    
    file_name = 'audio/' + username + '.mp3'
    await ctx.message.attachments[0].save(file_name)

    print("Saved audio: " + file_name)

    await ctx.send(username + " will now be welcomed with your audio")
    

@bot.event
async def on_ready():
    print('Logged in as {0} ({0.id})'.format(bot.user))
    print('------')

    for vc in bot.voice_clients:
        await vc.disconnect()

@bot.event
async def on_voice_state_update(member, before, after):

    if member.name == "WelcomeBack!":
        return

    channel = after.channel

    if channel is not None and before.channel != after.channel:

        for vc in bot.voice_clients:
            await vc.disconnect()

        audio_path = 'audio/' + member.name + '.mp3'

        if path.exists(audio_path):
            voice_client = await channel.connect()

            audio_source = discord.FFmpegPCMAudio(audio_path)

            def disconnect(error):
                coro = voice_client.disconnect()
                fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)
                try:
                    fut.result()
                except:
                    # an error happened sending the message
                    pass

            voice_client.play(audio_source, after=disconnect)
        else:
            print("No audio for user " + member.name)  

bot.run(TOKEN)
