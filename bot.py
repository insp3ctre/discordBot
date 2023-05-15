# TODO:
	# volumne control
	# queue for songs
		# connect to AWS database!
			# command to add songs to queue
				# song name, url, and who queued into database
			# play command checks database for fiso song
			# display queue on website (php?) like kevin bacon
	# type in 1 channel, output in another
	# change bot to 'function(variable, string*)' to get entire rest of inputs

	# add youtube_dl, gtts, pytube to PATH
	

import os
import discord
from discord.ext import commands, tasks
import asyncio

import yt_dlp as youtube_dl

from connection import DISCORD_TOKEN, account_sid, auth_token

# custom tts
from gtts import gTTS
# from pygame import mixer
from mutagen.mp3 import MP3
import time
import random as rand

from pytube import YouTube, Search

# not sure if I need this
intents = discord.Intents.all()

TOKEN = DISCORD_TOKEN

client = discord.Client(intents = intents)
bot = commands.Bot(command_prefix='!', intents=intents)

# for custom tts

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
    'source_address': '0.0.0.0', # bind to ipv4 since ipv6 addresses cause issues sometimes
    'outtmpl': 'audio/%(title)s.%(ext)s'
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


@bot.command(name='play', help='Play a video via a url or "keywords"')
@commands.has_role('Big Pens')
async def play(ctx,url):
	voice_client = ctx.message.guild.voice_client
	if not voice_client.is_playing():
		try :
			server = ctx.message.guild
			voice_channel = server.voice_client
			async with ctx.typing():
				filename = await YTDLSource.from_url(url, loop=bot.loop)
				voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename))
				await ctx.send('**Now playing:** {}'.format(filename))
		except:
			await ctx.send("The bot is not connected to a voice channel.")
	else:
		await voice_client.disconnect()
		await ctx.message.author.voice.channel.connect()
		try :
			server = ctx.message.guild
			voice_channel = server.voice_client
			async with ctx.typing():
				filename = await YTDLSource.from_url(url, loop=bot.loop)
				voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename))
				await ctx.send('**Now playing:** {}'.format(filename))
		except:
			await ctx.send("The bot is not connected to a voice channel.")

@bot.command(name='join', help='Connect to voice chat the user is in')
@commands.has_role('Big Pens')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    else:
        channel = ctx.message.author.voice.channel
    await channel.connect()

@bot.command(name='leave', help='Disconnect from voice chat')
@commands.has_role('Big Pens')
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_connected():
        await voice_client.disconnect()
    else:
        await ctx.send("The bot is not connected to a voice channel.")


@bot.command(name='stop', help='Reset the bot in a call')
@commands.has_role('Big Pens')
async def stop(ctx):
	voice_client = ctx.message.guild.voice_client
	if not ctx.message.author.voice:
		await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
		return
	else:
		await voice_client.disconnect()
		await ctx.message.author.voice.channel.connect()



@bot.command(name='pause', help='Pause the current song')
@commands.has_role('Big Pens')
async def pause(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        await voice_client.pause()
    else:
        await ctx.send("The bot is not playing anything at the moment.")

@bot.command(name='resume', help='Resumes the song')
@commands.has_role('Big Pens')
async def resume(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_paused():
        await voice_client.resume()
    else:
        await ctx.send("The bot was not playing anything before this. Use play_song command")

@bot.command(name='tts', help='Uses texts to speech in a text channel')
@commands.has_role('Bot Dad')
async def tts(ctx, *tss):
	if tss is not None:
		tss = convertTuple(tss)
		await ctx.send(tss, tts=True)
	else:
		await ctx.send('https://media1.giphy.com/media/8TweEdaxxfuElKkRxz/200w.gif?cid=6c09b952y6xf7pm52yi2j8h1z7fjsbi13l2zsaz2jtyq6uka&rid=200w.gif&ct=g')
######################


def convertTuple(tup):
        # initialize an empty string
    str = ''
    for item in tup:
        str = str + ' ' + item
    return str

def mutagen_length(path):
	try:
		audio = MP3(path)
		length = audio.info.length
		return length
	except:
		return None


# custom tts
@bot.command(name='vtts', help='Uses text to speech in a voice channel')
@commands.has_role('Bot Dad')
async def vtts(ctx, *tss):
	server = ctx.message.guild
	voice_channel = server.voice_client
	if tss is not None:
		tss = convertTuple(tss)
		audio = gTTS(text=tss, lang='en')
		file = f'{rand.randint(1, 70)}.mp3'
		audio.save(file)
		voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=file))
		length = mutagen_length(file)
		time.sleep(length)
		os.remove(file)
	else:
		await ctx.send('You did not include a message')



######
# test
@bot.command(name='test')
@commands.has_role('Bot Dad')
async def say(ctx):
	await ctx.send("howdy")

@bot.command(name='echo', help='Echo a message')
async def echo(ctx, *eeko):
	if eeko is not None:
		eeko = convertTuple(eeko)
		await ctx.send(eeko)
	else:
		await ctx.send('Echo!')



@bot.command(name='quit', help='Kill the bot')
@commands.has_role('Bot Dad')
async def quit(ctx):
	try:
		await ctx.message.guild.voice_cliennt.disconnect()
		await ctx.send('Goodnight, Sweet Prince')
		exit()
	except:
		await ctx.send('Goodnight, Sweet Prince')
		exit()
	

# for checking when it connects
@bot.event
async def on_ready():
	print('Harley is ready!')		

##### testing
# @bot.command(name='play2', help='Play a video via a url or "keywords"')
# @commands.has_role('Big Pens')
# async def play2(ctx, *url):
# 	voice_client = ctx.message.guild.voice_client
# 	if not voice_client.is_playing():
# 		try :
# 			server = ctx.message.guild
# 			voice_channel = server.voice_client
# 			async with ctx.typing():
# 				yt = YouTube(url)
# 				video = yt.streams.filter(only_audio=True).first()
# 				destination = 'audio/'
# 				out_file = video.download(output_path=destination)
# 				base, ext = os.path.splitext(out_file)
# 				new_file = base + '.mp3'
# 				os.rename(out_file, new_file)
# 				voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=new_file))
# 				await ctx.send('**Now playing:** {}'.format(yt.title))
# 		except:
# 			await ctx.send("The bot is not connected to a voice channel.")
# 	else:
# 		await voice_client.disconnect()
# 		await ctx.message.author.voice.channel.connect()
# 		try :
# 			server = ctx.message.guild
# 			voice_channel = server.voice_client
# 			async with ctx.typing():
# 				yt = YouTube(url)
# 				video = yt.streams.filter(only_audio=True).first()
# 				destination = '.'
# 				out_file = video.download(output_path=destination)
# 				base, ext = os.path.splitext(out_file)
# 				new_file = base + '.mp3'
# 				os.rename(out_file, new_file)
# 				voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=new_file))
# 				await ctx.send('**Now playing:** {}'.format(new_file))
# 		except:
# 			await ctx.send("The bot is not connected to a voice channel.")
#################


if __name__ == "__main__" :
	bot.run(TOKEN)
	# client.run(TOKEN)