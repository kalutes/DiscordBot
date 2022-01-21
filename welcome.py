# bot.py
import os
import random
import opuslib
import opuslib.api
import opuslib.api.encoder
import opuslib.api.decoder
import glob
import ast
import re
import uuid
import json

import os
from os import path
import discord
import asyncio
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('WELCOME_TOKEN')
PREFIX = os.getenv('WELCOME_PREFIX')
WORKING_DIR = os.getenv('WELCOME_DIR')
AUDIO_DIR = WORKING_DIR + "/audio/"
DB_FILE = WORKING_DIR + "/db.json"

def loadWelcomeMappings():
    dictionary = {'active': {}, 'removed': {}}
    try:
        file = open(DB_FILE, "r")
    except OSError:
        return dictionary
    with file:
        contents = file.read()
        try:
            dictionary = ast.literal_eval(contents)
        except SyntaxError:
            print("Dictionary syntax error. Overwriting")
        file.close()
        return dictionary

def dumpDbFile(db):
    # Dump the db to the db file
    with open(DB_FILE, 'w') as dbFile:
        dbFile.write(json.dumps(userMappings))
    print("Updated db")

def getActiveTracks(db, userId):
    activeTracks = []

    if userId in db['active']:
        activeTracks = db['active'][userId]

    return activeTracks

def getRemovedTracks(db, userId):

    removedTracks = []

    if userId in db['removed']:
        removedTracks = db['removed'][userId]

    return removedTracks

async def addUserTrack(db, userid, attachment):

    # Save the attachment as a uinque filename
    newfilename = str(uuid.uuid4()) + ".mp3"
    userspecifiedname = attachment.filename

    # Check if the audio directory exists and create it if necessary
    if not os.path.exists(AUDIO_DIR):
        os.makedirs(AUDIO_DIR)

    await attachment.save(AUDIO_DIR + newfilename)
    print("Saved audio: {}, {}".format(newfilename, userspecifiedname))

    # Add this file to the db for the specified user
    if userid not in db['active']:
        db['active'][userid] = []
    db['active'][userid].append([newfilename, userspecifiedname])

    dumpDbFile(db)

def removeUserTrack(db, userId, trackIndex):

    if userId not in db['active'] or trackIndex <= 0 or trackIndex > len(db['active'][userId]):
        return 0

    removedTrack = db['active'][userId][trackIndex - 1]

    if userId not in db['removed']:
        db['removed'][userId] = []

    db['removed'][userId].append(removedTrack)

    del db['active'][userId][trackIndex - 1]

    dumpDbFile(db)

    return 1

def restoreUserTrack(db, userId, trackIndex):

    if userId not in db['removed'] or trackIndex <= 0 or trackIndex > len(db['removed'][userId]):
        return 0

    restoredTrack = db['removed'][userId][trackIndex - 1]

    if userId not in db['active']:
        db['active'][userId] = []

    db['active'][userId].append(restoredTrack)

    del db['removed'][userId][trackIndex - 1]

    dumpDbFile(db)

    return 1

def isValidMention(msg):
    match = re.search("<@![0-9]+>", msg)

    if match is None:
        return 0
    
    return 1

def getIdFromMention(mention):
    # Trim off the leading '<@!' and trailing '>' from the mention
    return mention[3:len(mention) - 1]

print("Initializing bot with prefix")
print(PREFIX)

# Load the audio mappings from the db file
userMappings = loadWelcomeMappings()

bot = commands.Bot(command_prefix=commands.when_mentioned_or(PREFIX),
                   description='Welcomes users')

@bot.command(name='welcome', help='Welcomes the specified user with the attached MP3 audio')
async def add_welcome(ctx, usermention):

    if not isValidMention(usermention):
        await ctx.send("You must @ mention the user who you wish to welcome")
        return

    if len(ctx.message.attachments) < 1:
        await ctx.send("You must attach a .mp3 file")
        return

    filename, file_extension = os.path.splitext(ctx.message.attachments[0].filename)

    if file_extension != '.mp3':
        await ctx.send("Attached file is not a .mp3")
        return

    userid = getIdFromMention(usermention)

    print("Requesting welcome for user {}".format(userid))

    await addUserTrack(userMappings, userid, ctx.message.attachments[0])

    await ctx.send("The user will now be welcomed with your audio")

@bot.command(name='list', help='Lists the welcome clips for the mentioned user')
async def list_welcomes(ctx, userMention):

    if not isValidMention(userMention):
        await ctx.send("You must @ mention the user who you wish to list")
        return

    userId = getIdFromMention(userMention)

    userFiles = getActiveTracks(userMappings, userId)

    if len(userFiles) == 0:
        await ctx.send("There are no welcome clips for that user")
        return

    openedFiles = []

    i = 1
    for userFile in userFiles:
        openedFiles.append(discord.File(AUDIO_DIR + userFile[0], filename="({})-{}".format(i, userFile[1])))
        i += 1
    
    await ctx.send("The user has the following welcome clips:", files=openedFiles)
    await ctx.send("You may remove a clip by using the command: {}remove @User <Clip Index>".format(PREFIX))

@bot.command(name='remove', help='Removes the specified clip for the given user')
async def remove_clip(ctx, userMention, clipIndexStr):

    if not isValidMention(userMention):
        await ctx.send("You must @ mention the user who you wish to list")
        return

    userId = getIdFromMention(userMention)

    if not removeUserTrack(userMappings, userId, int(clipIndexStr)):
        await ctx.send("Invalid clip index")
        return
    
    await ctx.send("The clip has been removed")

@bot.command(name='listRemoved', help='Lists the tracks that have been removed for the mentioned user')
async def list_removed(ctx, userMention):

    if not isValidMention(userMention):
        await ctx.send("You must @ mention the user who you wish to list")
        return

    userId = getIdFromMention(userMention)

    userFiles = getRemovedTracks(userMappings, userId)

    if len(userFiles) == 0:
        await ctx.send("There are no removed clips for that user")
        return

    openedFiles = []

    i = 1
    for userFile in userFiles:
        openedFiles.append(discord.File(AUDIO_DIR + userFile[0], filename="({})-{}".format(i, userFile[1])))
        i += 1
    
    await ctx.send("The user has the following removed clips:", files=openedFiles)
    await ctx.send("You may restore a clip by using the command: {}restore @User <Clip Index>".format(PREFIX))

@bot.command(name='restore', help='Restores the specified clip for the given user')
async def restore_clip(ctx, userMention, clipIndexStr):

    if not isValidMention(userMention):
        await ctx.send("You must @ mention the user who you wish to list")
        return

    userId = getIdFromMention(userMention)

    if not restoreUserTrack(userMappings, userId, int(clipIndexStr)):
        await ctx.send("Invalid clip index")
        return
    
    await ctx.send("The clip has been restored")

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

    # Special case for MEE6 bot
    if channel is None or before.channel == after.channel or channel.name == "💢 Join to create VC 💢":
        return

    for vc in bot.voice_clients:
        await vc.disconnect()

    userFiles = []

    if str(member.id) in userMappings['active']:
        userFiles = userMappings['active'][str(member.id)]

    if len(userFiles) == 0:
        print("No audio for user " + member.name)
        return

    audioChoice = random.choice(userFiles)
    voiceClient = await channel.connect()

    # Audio choices are stored as a list where the first index is the actual file name in the audio path
    audioSource = discord.FFmpegPCMAudio(AUDIO_DIR + audioChoice[0])

    def disconnect(error):
        coro = voiceClient.disconnect()
        fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)
        try:
            fut.result()
        except:
            # an error happened sending the message
            pass

    voiceClient.play(audioSource, after=disconnect)
 
bot.run(TOKEN)
