import discord
from discord.ext import commands
from discord import app_commands
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from youtubesearchpython import VideosSearch
import config
import youtube

# Set up Spotify authentication
spotify_client_id = config.SPOTIFY_CLIENT_ID
spotify_client_secret = config.SPOTIFY_CLIENT_SECRET
spotify_auth_manager = SpotifyClientCredentials(client_id=spotify_client_id, client_secret=spotify_client_secret)
spotify = spotipy.Spotify(auth_manager=spotify_auth_manager)

# Function to search and retrieve video information from Spotify
async def search_video(query):
    if query.startswith("https://open.spotify.com/track/"):
        # Play a Spotify song
        track_id = query.split("/")[-1].split("?")[0]
        track_info = spotify.track(track_id)
        video_title = f"{track_info['name']} - {track_info['artists'][0]['name']}"
        video_search = VideosSearch(video_title, limit=1)
        video_result = video_search.result()['result'][0]
        video_url = video_result['link']
    elif query.startswith("https://open.spotify.com/playlist/"):
        # Play a Spotify playlist
        playlist_id = query.split("/")[-1].split("?")[0]
        playlist_info = spotify.playlist(playlist_id)
        video_urls = []
        video_titles = []
        for track in playlist_info['tracks']['items']:
            track_name = track['track']['name']
            artist_name = track['track']['artists'][0]['name']
            video_title = f"{track_name} - {artist_name}"
            video_search = VideosSearch(video_title, limit=1)
            video_result = video_search.result()['result'][0]
            video_url = video_result['link']
            video_urls.append(video_url)
            video_titles.append(video_title)
        return video_urls, video_titles
    else:
        return None, None

    return video_url, video_title

# Slash command to play music from Spotify
@app_commands.command(name="spotify", description="Play a song or playlist from Spotify")
@app_commands.describe(query="The Spotify song or playlist URL")
async def spotify_command(interaction: discord.Interaction, query: str):
    await interaction.response.defer()

    voice_state = interaction.user.voice
    if voice_state is None:
        await interaction.followup.send("You need to be connected to a voice channel to use this command.")
        return

    voice_channel = voice_state.channel
    if voice_channel is None:
        await interaction.followup.send("You need to be in a voice channel to use this command.")
        return

    voice_client = discord.utils.get(interaction.client.voice_clients, guild=interaction.guild)
    if voice_client is None:
        voice_client = await voice_channel.connect()
    else:
        await voice_client.move_to(voice_channel)

    video_urls, video_titles = await search_video(query)

    if video_urls:
        if isinstance(video_urls, list):
            for video_url, video_title in zip(video_urls, video_titles):
                youtube.music_queue.append((video_url, video_title))
            await interaction.followup.send("Spotify playlist added to the queue.")
        else:
            youtube.music_queue.append((video_urls, video_titles))
            if not voice_client.is_playing():
                await youtube.play_next(interaction)
            else:
                await interaction.followup.send(f"Added to the queue: {video_titles}")
    else:
        await interaction.followup.send("Invalid Spotify URL.")

def register_commands(bot):
    bot.tree.add_command(spotify_command)
