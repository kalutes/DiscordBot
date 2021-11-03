# moon.py

import os
import requests
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord.ext import tasks
from gtts import gTTS
from bs4 import BeautifulSoup
import asyncio

load_dotenv()
TOKEN = os.getenv('MOON_TOKEN')
PREFIX = os.getenv('MOON_PREFIX')

print("Initializing bot with prefix")
print(PREFIX)

class Security:
    symbol = ""
    valid = False
    market_hours_price = ""
    market_hours_change = ""
    ah_price = ""
    ah_change = ""
    volume = ""

    def get_yahoo_page(self):
        return requests.get("https://finance.yahoo.com/quote/{}/".format(self.symbol), headers={'Cache-Control': 'no-cache', "Pragma": "no-cache"})

    def is_valid(self, page):
        soup = BeautifulSoup(page.text, 'html.parser')
        div = soup.find("div", {"id": "quote-market-notice"})

        if div is not None:
            return True

        return False

    def has_ah_data(self, page):
        soup = BeautifulSoup(page.text, 'html.parser')
        div = soup.find("div", {"id": "quote-market-notice"})
        
        return len(div.parent.parent.findChildren("div" , recursive=False)) > 1

    def populate_data(self, page):
        soup = BeautifulSoup(page.text, 'html.parser')

        self.volume = soup.find("td", {"data-test": "TD_VOLUME-value"}).findChildren("span" , recursive=False)[0].text
        self.market_hours_price = soup.find("div", {"id": "quote-market-notice"}).parent.findChildren("span" , recursive=False)[0].text
        self.market_hours_change = soup.find("div", {"id": "quote-market-notice"}).parent.findChildren("span" , recursive=False)[1].text

        if self.has_ah_data(page):
            self.ah_price = soup.find("div", {"id": "quote-market-notice"}).parent.parent.findChildren("div" , recursive=False)[1].findChildren("span" , recursive=False)[0].text
            self.ah_change = soup.find("div", {"id": "quote-market-notice"}).parent.parent.findChildren("div" , recursive=False)[1].findChildren("span" , recursive=False)[1].text
        
        return
    
    def __init__(self, symbol):
        self.symbol = symbol

        page = self.get_yahoo_page()

        if self.is_valid(page):
            self.valid = True
            self.populate_data(page)

async def say_price(the_bot, channel, vc, symbol):
    audio_file = "audio.mp3"

    speak_text = "Invalid ticker or security symbol"

    sec_data = Security(symbol)

    if sec_data.valid:
        price_to_read = sec_data.market_hours_price
        change_to_read = sec_data.market_hours_change
        ah_disclaimer = ""

        if sec_data.ah_price != "":
            price_to_read = sec_data.ah_price
            change_to_read = sec_data.ah_change
            ah_disclaimer = "After Hours: "

        speak_text = '{}:{} {}.'.format(sec_data.symbol, ah_disclaimer, price_to_read)

    print(speak_text)

    tts = gTTS(text=speak_text, lang='en', slow=False)
    tts.save(audio_file)

    if vc is None:
        vc = await channel.connect()

    if vc.is_playing():
        return

    # Audio choices are stored as a list where the first index is the actual file name in the audio path
    audioSource = discord.FFmpegPCMAudio(audio_file)

    vc.play(audioSource)

    while vc.is_playing():
        await asyncio.sleep(1)

def is_valid_symbol(symbol):
    sec_data = Security(symbol)
    return sec_data.valid

class PriceSayer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.say_price_interval.start()
        self.symbols = []
        self.channel = None

    async def say_all_prices(self):
        if self.channel is None:
            return

        vc = None

        for symbol in self.symbols:
            if len(self.bot.voice_clients) > 0:
                vc = self.bot.voice_clients[0]
            await say_price(self.bot, self.channel, vc, symbol)

    @commands.command(name='watch', help='Watches the price of the security')
    async def price(self, ctx, symbol):
        if not is_valid_symbol(symbol):
            await ctx.send("Invalid ticker or security symbol")
            return

        self.symbols.append(symbol)
        self.channel = ctx.author.voice.channel
        await ctx.send("{} will be watched".format(symbol))

    @commands.command(name='say', help='Says the prices of the watched symbols')
    async def say_prices(self, ctx):
        await self.say_all_prices()

    @commands.command(name='leave', help='Disconnects')
    async def leave_voice(self, ctx):
        for vc in self.bot.voice_clients:
            await vc.disconnect()

        self.channel = None

    @commands.command(name='join', help='Sets the current channel as the channel to join')
    async def join_channel(self, ctx):
        self.channel = ctx.author.voice.channel
        await self.say_all_prices()

    @commands.command(name='clear', help='Clears the list of symbols to watch')
    async def clear_symbols(self, ctx):
        self.symbols = []

    @commands.command(name='list', help='Lists the watched symbols')
    async def list_symbols(self, ctx):
        if len(self.symbols) == 0:
            await ctx.send("No symbols are being watched.")
            return

        message = "Currently watching:\r\n"

        for symbol in self.symbols:
            message += symbol
            message += "\r\n"

        await ctx.send(message)

    @commands.command(name='remove', help='Removes the specified symbol from the list of watched symbols')
    async def remove_symbols(self, ctx, symbol):
        i = len(self.symbols)
        self.symbols.remove(symbol)

        if len(self.symbols) == i:
            await ctx.send("{} was not in the list of watched symbols.".format(symbol))
            return

        await ctx.send("{} was removed from the list".format(symbol))

    @commands.command(name='interval', help='Sets the speaking interval in minutes')
    async def set_interval(self, ctx, interval):
        try:
            i = int(interval)
            self.say_price_interval.cancel()
            self.say_price_interval.change_interval(minutes=i)
            self.say_price_interval.restart()
            await ctx.send("Prices will be spoken every {} minutes".format(i))
        except ValueError:
            await ctx.send("Please enter a valid interval")

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

    @tasks.loop(minutes=5)
    async def say_price_interval(self):
        await self.say_all_prices()

bot = commands.Bot(command_prefix=commands.when_mentioned_or(PREFIX),
                   description='Prices of Securities and Crypto')
bot.add_cog(PriceSayer(bot))
bot.run(TOKEN)
