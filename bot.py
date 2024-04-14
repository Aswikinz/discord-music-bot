import discord
from discord.ext import commands
from discord import app_commands
from yt_dlp import YoutubeDL
from youtubesearchpython import VideosSearch
import asyncio

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)

# Music queue
music_queue = []

# YoutubeDL options
ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}

# FFmpeg options
ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 10',
    'options': '-vn -filter:a "volume=0.25"'
}

# Function to search and retrieve video information
async def search_video(query):
    if query.startswith("http"):
        # Play a YouTube video directly from the URL
        video_url = query
        video_title = query
    else:
        # Search for the video on YouTube
        video_search = VideosSearch(query, limit=1)
        video_result = video_search.result()['result'][0]
        video_url = video_result['link']
        video_title = video_result['title']

    return video_url, video_title

# Function to play the next song in the queue
async def play_next(interaction):
    if len(music_queue) > 0:
        url, title = music_queue.pop(0)
        voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                audio_url = info['url']
                voice_client.play(discord.FFmpegPCMAudio(audio_url, **ffmpeg_options), after=lambda e: bot.loop.create_task(play_next(interaction)))
                await interaction.edit_original_response(content=f"Now playing: {title}")
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            await interaction.edit_original_response(content="An error occurred while trying to play the music. Please try again.")
            await reconnect_voice(interaction)
    else:
        await interaction.edit_original_response(content="The music queue is empty.")

# Function to reconnect to voice channel with exponential backoff
async def reconnect_voice(interaction):
    voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    if voice_client and not voice_client.is_connected():
        delay = 1
        while True:
            try:
                await voice_client.connect(reconnect=True)
                print(f"Reconnected to voice channel after {delay} seconds.")
                break
            except discord.errors.ConnectionClosed:
                print(f"Failed to reconnect to voice channel. Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
                delay *= 2  # Exponential backoff

# Slash command to play music
@bot.tree.command(name="play", description="Play a song from YouTube")
@app_commands.describe(query="The YouTube video URL or search query")
async def play(interaction: discord.Interaction, query: str):
    await interaction.response.defer()

    voice_channel = interaction.user.voice.channel
    if voice_channel is None:
        await interaction.followup.send("You need to be in a voice channel to use this command.")
        return

    voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    if voice_client is None:
        voice_client = await voice_channel.connect()
    else:
        await voice_client.move_to(voice_channel)

    video_url, video_title = await search_video(query)
    music_queue.append((video_url, video_title))

    if not voice_client.is_playing():
        await play_next(interaction)
    else:
        await interaction.followup.send(f"Added to the queue: {video_title}")

# Slash command to pause music
@bot.tree.command(name="pause", description="Pause the currently playing music")
async def pause(interaction: discord.Interaction):
    voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await interaction.response.send_message("Music paused.")
    else:
        await interaction.response.send_message("No music is currently playing.")

# Slash command to resume music
@bot.tree.command(name="resume", description="Resume the paused music")
async def resume(interaction: discord.Interaction):
    voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await interaction.response.send_message("Music resumed.")
    else:
        await interaction.response.send_message("No music is currently paused.")

# Slash command to stop music and disconnect the bot
@bot.tree.command(name="stop", description="Stop the music and disconnect the bot from the voice channel")
async def stop(interaction: discord.Interaction):
    voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    if voice_client:
        music_queue.clear()
        await voice_client.disconnect()
        await interaction.response.send_message("Music stopped and bot disconnected from the voice channel.")
    else:
        await interaction.response.send_message("The bot is not currently in a voice channel.")

# Slash command to display the music queue
@bot.tree.command(name="queue", description="Display the current music queue")
async def queue(interaction: discord.Interaction):
    if len(music_queue) > 0:
        queue_message = "Current music queue:\n"
        for i, (url, title) in enumerate(music_queue, start=1):
            queue_message += f"{i}. {title}\n"
        await interaction.response.send_message(queue_message)
    else:
        await interaction.response.send_message("The music queue is empty.")

# Slash command to skip the current song
@bot.tree.command(name="skip", description="Skip the currently playing song")
async def skip(interaction: discord.Interaction):
    voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await interaction.response.send_message("Skipped the current song.")
    else:
        await interaction.response.send_message("No music is currently playing.")

# Slash command to display the bot's available commands
@bot.tree.command(name="help", description="Display the available commands")
async def help(interaction: discord.Interaction):
    help_message = """
Available commands:
/play [query] - Play a song from YouTube
/pause - Pause the currently playing music
/resume - Resume the paused music
/stop - Stop the music and disconnect the bot from the voice channel
/queue - Display the current music queue
/skip - Skip the currently playing song
/help - Display the available commands
"""
    await interaction.response.send_message(help_message)

# Event listener for when the bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)
