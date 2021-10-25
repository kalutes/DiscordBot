# bot.py
import os
import random
import opuslib
import opuslib.api
import opuslib.api.encoder
import opuslib.api.decoder
import glob
import tempfile
import youtube_dl

import os
from os import path
import discord
import asyncio
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('WELCOME_TOKEN')
PREFIX = os.getenv('WELCOME_PREFIX')

print("Initializing bot with prefix")
print(PREFIX)

bot = commands.Bot(command_prefix=commands.when_mentioned_or(PREFIX),
                   description='Memes and stuff')

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
    
    file_expression = '/media/audio/' + username + '*.mp3'

    user_files = glob.glob(file_expression)

    max = 0

    for user_file in user_files:
        last_num_index = user_file.rfind(".")

        first_num_index = last_num_index - 1
        while user_file[first_num_index] >= '0' and user_file[first_num_index] <= '9':
            first_num_index -= 1
        first_num_index += 1

        index_string = user_file[first_num_index:last_num_index]

        num_index_val = int(index_string)

        if num_index_val > max:
            max = num_index_val

    max += 1

    file_name = '/media/audio/' + username + '_' + str(max) + '.mp3'

    await ctx.message.attachments[0].save(file_name)

    print("Saved audio: " + file_name)

    await ctx.send(username + " will now be welcomed with your audio")
    

@bot.event
async def on_ready():
    print('Welcome Logged in as {0} ({0.id})'.format(bot.user))
    print('------')

    for vc in bot.voice_clients:
        await vc.disconnect()

@bot.event
async def on_voice_state_update(member, before, after):

    if member.name == "WelcomeBack!" or member.name == "BotDevelopment":
        return

    channel = after.channel

    if channel is not None and before.channel != after.channel:

        for vc in bot.voice_clients:
            await vc.disconnect()

        file_expression = '/media/audio/' + member.name + '*.mp3'

        user_files = glob.glob(file_expression)

        if len(user_files) > 0:
            audio_path = random.choice(user_files)
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
