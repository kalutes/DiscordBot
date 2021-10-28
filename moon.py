# moon.py

import os
import requests
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord.ext import tasks
from gtts import gTTS

load_dotenv()
TOKEN = os.getenv('MOON_TOKEN')
PREFIX = os.getenv('MOON_PREFIX')

print("Initializing bot with prefix")
print(PREFIX)

def shib_price():
    page = requests.get("https://finance.yahoo.com/quote/SHIB-USD/")
    x = page.text.find("Trsdu(0.3s) Fw(b) Fz(36px) Mb(-4px) D(ib)")
    num = page.text[x+61:x+69]
    return(num)

async def say_shib(the_bot, channel):
    price = shib_price()
    tts = gTTS(text='the price of shiba is {}. To the moon!'.format(price), lang='en', slow=False)
    tts.save("/media/audio/shib.mp3")

    for vc in the_bot.voice_clients:
        await vc.disconnect()

    voiceClient = await channel.connect()

    # Audio choices are stored as a list where the first index is the actual file name in the audio path
    audioSource = discord.FFmpegPCMAudio('/media/audio/shib.mp3')

    voiceClient.play(audioSource)

class ShibSayer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.try_say_shib.start()

    @commands.command(name='shib', help='Prints the current SHIB price')
    async def shib_price(self, ctx):
        channel = ctx.author.voice.channel
        if channel is not None:
            await say_shib(self.bot, channel)

    @commands.command(name='leave', help='Disconnects')
    async def leave_voice(self, ctx):
        for vc in self.bot.voice_clients:
            await vc.disconnect()

    @commands.Cog.listener()
    async def on_ready(self):
        print('Welcome Logged in as {0} ({0.id})'.format(self.bot.user))
        print('------')

        for vc in self.bot.voice_clients:
            await vc.disconnect()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if len(self.bot.voice_clients) == 0:
            return

        # Hardcode this since this bot is only used in one server currently
        current_channel = self.bot.voice_clients[0].channel

        # If the user wasn't originally in the channel with the bot, or if the user didn't move channels, don't do anything
        if before.channel != current_channel or before.channel == after.channel:
            return

        # Only the bot is connected, cleanup
        if len(before.channel.members) == 1:
            # Leave
            await self.bot.voice_clients[0].disconnect()

    @tasks.loop(seconds=30.0)
    async def try_say_shib(self):
        print("running say loop")
        if len(self.bot.voice_clients) == 0:
            return

        await say_shib(self.bot, self.bot.voice_clients[0].channel)

bot = commands.Bot(command_prefix=commands.when_mentioned_or(PREFIX),
                   description='Welcomes users')
bot.add_cog(ShibSayer(bot))
bot.run(TOKEN)
