import discord
from discord.ext import commands
from yt_dlp import YoutubeDL
from youtubesearchpython import VideosSearch

# Set your bot token and permission integer as variables
BOT_TOKEN = 'YOUR_BOT_TOKEN'
PERMISSION_INTEGER = 39582455302400

intents = discord.Intents.default()
intents.message_content = True

# Use the PERMISSION_INTEGER variable
permissions = discord.Permissions(permissions=PERMISSION_INTEGER)

bot = commands.Bot(command_prefix='/', intents=intents)

@bot.command()
async def play(ctx, *, query):
    voice_channel = ctx.author.voice.channel
    if voice_channel is None:
        await ctx.send("You need to be in a voice channel to use this command.")
        return

    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client is None:
        voice_client = await voice_channel.connect()
    else:
        await voice_client.move_to(voice_channel)

    if query.startswith("http"):
        # Play a YouTube video directly from the URL
        video_url = query
    else:
        # Search for the video on YouTube
        video_search = VideosSearch(query, limit=1)
        video_result = video_search.result()['result'][0]
        video_url = video_result['link']
        print(f"Video URL: {video_url}")

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                      'options': '-vn -filter:a "volume=0.25"'}

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            audio_url = info['url']
            print(f"Audio URL: {audio_url}")

        voice_client.play(discord.FFmpegPCMAudio(audio_url, **ffmpeg_options))
        print("Audio playback started")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        await ctx.send("An error occurred while trying to play the music. Please try again.")

    if not query.startswith("http"):
        await ctx.send(f"Now playing: {video_result['title']}")
    else:
        await ctx.send(f"Now playing: {video_url}")

@bot.command()
async def pause(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await ctx.send("Music paused.")
    else:
        await ctx.send("No music is currently playing.")

@bot.command()
async def resume(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await ctx.send("Music resumed.")
    else:
        await ctx.send("No music is currently paused.")

@bot.command()
async def stop(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client:
        await voice_client.disconnect()
        await ctx.send("Music stopped and bot disconnected from the voice channel.")
    else:
        await ctx.send("The bot is not currently in a voice channel.")

# Use the BOT_TOKEN variable
bot.run(BOT_TOKEN)
