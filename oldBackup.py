import os
import discord
from discord.ext import commands, tasks

import youtube_dl

from testing.scrape import meal
from twilio.rest import Client
from connection import DISCORD_TOKEN, account_sid, auth_token, from_number, to_number

global textMe
textMe = False

# not sure if I need this
intents = discord.Intents.all()

TOKEN = DISCORD_TOKEN

client = discord.Client(intents = intents)
bot = commands.Bot(command_prefix='!', intents=intents)

########### youtube stuff ####
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['title'] if stream else ytdl.prepare_filename(data)
        return filename

##########

@bot.command(name='join', help='Tells the bot to join the voice channel')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    else:
        channel = ctx.message.author.voice.channel
    await channel.connect()
@bot.command(name='leave', help='To make the bot leave the voice channel')
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_connected():
        await voice_client.disconnect()
    else:
        await ctx.send("The bot is not connected to a voice channel.")


# for checking when it connects
@client.event
async def on_ready():
	print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
	global textMe

	# so the bot doesn't respond to itself
	if message.author == client.user:
		return

	if message.content == '!text':
		textMe = not textMe
		if textMe:
			msg = 'Text messages are turned ON.'
		else:
			msg = 'Text messages are turned OFF.'
		print(msg)
		# await message.channel.send(msg)
		await message.channel.send(msg)


	if message.content == '!lunch':
		# response = webscrape
		response = meal(3)
		await message.channel.send(response)
		
		if textMe:
			text = Client(account_sid, auth_token)
			textMessage = text.messages \
				.create(
					body=response,
					from_= from_number,
					to = to_number
				)
			print(f'Lunch sent! Message ID: {textMessage.sid}')

	if message.content == '!dinner':
		# response = webscrape
		response = meal(4)
		await message.channel.send(response)
		
		if textMe:
			text = Client(account_sid, auth_token)
			textMessage = text.messages \
				.create(
					body=response,
					from_= from_number,
					to = to_number
				)
			print(f'Dinner sent! Message ID: {textMessage.sid}')

	if message.content == '!quit':
		await message.channel.send('Goodnight, Sweet Prince 😘')
		quit()

			

if __name__ == "__main__" :
	bot.run(TOKEN)
	client.run(TOKEN)