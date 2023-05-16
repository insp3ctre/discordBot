# actiate venv: .\venv\Scripts\activate

# TODO:
	# commands to add:
		# queue (prints queue)
		# pause (pause current audio) (add argument to play to check if pause is true)
		# skip (skip current song and progress in queue)
	# display queue on website (php?) like kevin bacon
		# add option to add songs to queue from site

	
import os
import cv2
import glob
import time
import discord
import asyncio
import mysql.connector
import random as rand
import yt_dlp as youtube_dl
from gtts import gTTS
from mutagen.mp3 import MP3
from discord.ext import commands
from youtube_search import YoutubeSearch
from mysql.connector import errorcode

# not sure if I need this
intents = discord.Intents.all()

TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client(intents = intents)
bot = commands.Bot(command_prefix='!', intents=intents)

bot_role = 'Big Pens'
admin_role = 'Bot Dad'

global queue_length
queue_length = 0

# sql stuff
hostname = "127.0.0.1"
username = "root"
password = "securepswd"
database_name = "harley"

try:
	con = mysql.connector.connect(host=hostname, user=username, password=password, database=database_name)
	print(con)
except mysql.connector.Error as err:
  if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
    print("Something is wrong with your user name or password")
  elif err.errno == errorcode.ER_BAD_DB_ERROR:
    print("Database does not exist")
  else:
    print(err)


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


def ytKeywordSearch(keywords):
	keywords = convertTuple(keywords)
	results = YoutubeSearch(keywords, max_results=1).to_dict()
	url = "https://www.youtube.com" + results[0]['url_suffix'].split("&")[0]
	return url

@bot.command(name='add', help='Add a song to the queue via url or keywords')
@commands.has_role(bot_role)
async def add(ctx, *url):
	# voice_channel = ctx.message.guild.voice_client
	try:
		async with ctx.typing():
			try:
				link = ytKeywordSearch(url) # by keyword
			except:
				link = url[0] # by url
			filename = await YTDLSource.from_url(link, loop=bot.loop)
			# print(f"inserting {filename} and {ctx.author}")
			cursor = con.cursor()
			query = ("INSERT INTO queue "
	    			"(filename, author) "
					"VALUES (%s, %s)")
			query_data = (filename, str(ctx.author))
			cursor.execute(query, query_data)
			con.commit()
			cursor.close()
			await ctx.send(f"{filename} has been added to the queue!")
	except Exception as e:
		await ctx.send(f"An error occurred:\n{e}")

@bot.command(name='play', help='Start playing from the queue')
@commands.has_role(bot_role)
async def play(ctx):
	voice_channel = ctx.message.guild.voice_client
	try:
		cursor = con.cursor()
		query = ("SELECT * FROM queue "
	    		"ORDER BY id ASC")
		cursor.execute(query)
		results = cursor.fetchall()
		cursor.close()
		print(results)
		queue_length = len(results)
		id = results[0][0]
		filename = results[0][1]
		author = results[0][2]
		print(0)
		voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename))
		print(1)
		await ctx.send(f'**Now playing:** {filename} (queued by @{author})')
		print(2)
		cursor = con.cursor()
		query = ("DELETE FROM queue "
				"WHERE id=%(song)s")
		query_data = {
			'song': id
		}
		print(3)
		cursor.execute(query, query_data)
		con.commit()
		cursor.close()
		print(4)
		if queue_length > 1:
			length = webm_length(filename) * 10
			print(length)
			time.sleep(length)
			next = await play(ctx)
	except Exception as e:
		print('no work', e)

@bot.command(name='join', help='Connect to voice chat the user is in')
@commands.has_role(bot_role)
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    else:
        channel = ctx.message.author.voice.channel
    await channel.connect()

@bot.command(name='leave', help='Disconnect from voice chat')
@commands.has_role(bot_role)
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_connected():
        await voice_client.disconnect()
    else:
        await ctx.send("The bot is not connected to a voice channel.")

@bot.command(name='clear', help='Clear the queue')
@commands.has_role(admin_role)
async def clear(ctx):
	cursor = con.cursor()
	query = "truncate queue"
	cursor.execute(query)
	con.commit()
	cursor.close()
	await ctx.send("Queue cleared.")

@bot.command(name='stop', help='Reset the bot in a call')
@commands.has_role(bot_role)
async def stop(ctx):
	voice_client = ctx.message.guild.voice_client
	if not ctx.message.author.voice:
		await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
		return
	else:
		await voice_client.disconnect()
		await ctx.message.author.voice.channel.connect()

@bot.command(name='volume', help=r"Change the volume to between 0% and 200%")
async def volume(ctx, change):
	voice_channel = ctx.message.guild.voice_client
	voice_channel.source = discord.PCMVolumeTransformer(voice_channel.source)
	# try:
	# 	voice_channel.source.volume = change / 100
	# except:
	# 	await ctx.send("Volume change unsuccessful")
	voice_channel.pause()
	voice_channel.source.volume = int(change) / 100
	voice_channel.resume()


@bot.command(name='pause', help='Pause the current song')
@commands.has_role(bot_role)
async def pause(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        await voice_client.pause()
    else:
        await ctx.send("The bot is not playing anything at the moment.")

@bot.command(name='resume', help='Resumes the song')
@commands.has_role(bot_role)
async def resume(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_paused():
        await voice_client.resume()
    else:
        await ctx.send("The bot was not playing anything before this. Use play_song command")

@bot.command(name='tts', help='Uses texts to speech in a text channel')
@commands.has_role(admin_role)
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

	audio = MP3(path)
	length = audio.info.length
	return length

def webm_length(filename):
	video = cv2.VideoCapture(filename)
	frames = video.get(cv2.CAP_PROP_FRAME_COUNT)
	fps = video.get(cv2.CAP_PROP_FPS)
	return round(frames / fps) + 5

# custom tts
@bot.command(name='vtts', help='Uses text to speech in a voice channel')
@commands.has_role(admin_role)
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
@commands.has_role(admin_role)
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
@commands.has_role(admin_role)
async def quit(ctx):
	try:
		await ctx.message.guild.voice_cliennt.disconnect()
		await ctx.send('Goodnight, Sweet Prince')
	except:
		await ctx.send('Goodnight, Sweet Prince')
	finally:
		# clear audio file
		files = glob.glob('audio/*')
		for f in files:
			os.remove(f)

		# clear database
		cursor = con.cursor()
		query = "truncate queue"
		cursor.execute(query)
		con.commit()
		cursor.close()
		con.close()
		print("database cleared")

		exit()
		
	

# for checking when it connects
@bot.event
async def on_ready():
	print('Harley is ready!')		

##### testing
# @bot.command(name='play2', help='Play a video via a url or "keywords"')
# @commands.has_role(bot_role)
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