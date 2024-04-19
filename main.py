import discord
from discord.ext import commands
import config
import youtube
import spotify

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

# Register the YouTube commands
youtube.register_commands(bot)

# Register the Spotify commands
spotify.register_commands(bot)

# Slash command to display the bot's available commands
@bot.tree.command(name="help", description="Display the available commands")
async def help(interaction: discord.Interaction):
    help_message = """
Available commands:
/play [query] - Play a song from YouTube
/spotify [query] - Play a song or playlist from Spotify
/pause - Pause the currently playing music
/resume - Resume the paused music
/stop - Stop the music and disconnect the bot from the voice channel
/queue - Display the current music queue
/skip - Skip the currently playing song
/help - Display the available commands
"""
    await interaction.response.send_message(help_message)

bot.run(config.DISCORD_TOKEN)
