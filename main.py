import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import yt_dlp
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
client = commands.Bot(command_prefix="!", intents=intents)

tree = client.tree
looping = False
voice_client = None
current_audio = None

@client.event
async def on_ready():
    print(f"🎵 Bot đang chạy: {client.user}")
    await tree.sync()

@tree.command(name="play", description="Phát nhạc từ YouTube")
async def play(interaction: discord.Interaction, url: str):
    global voice_client, current_audio, looping

    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.response.send_message("❌ Bạn phải vào voice channel trước.", ephemeral=True)
        return

    await interaction.response.send_message(f"🔊 Đang phát: {url}")
    channel = interaction.user.voice.channel

    if not voice_client or not voice_client.is_connected():
        voice_client = await channel.connect()

    # Xóa file cũ nếu có
    if os.path.exists("song.webm"): os.remove("song.webm")
    if os.path.exists("song.mp3"): os.remove("song.mp3")

    ydl_opts = {
        'format': 'bestaudio',
        'noplaylist': 'True',
        'quiet': True,
        'outtmpl': 'song.%(ext)s',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    current_audio = filename
    looping = False  # Reset lại loop khi phát bài mới

    voice_client.stop()  # Dừng nhạc cũ nếu có
    voice_client.play(discord.FFmpegPCMAudio(source=filename), after=lambda e: asyncio.run_coroutine_threadsafe(play_next(interaction), client.loop))

async def play_next(interaction):
    global looping, current_audio
    if looping and current_audio and voice_client:
        voice_client.play(discord.FFmpegPCMAudio(source=current_audio), after=lambda e: asyncio.run_coroutine_threadsafe(play_next(interaction), client.loop))

@tree.command(name="loop", description="Bật/Tắt lặp lại bài hát")
async def loop(interaction: discord.Interaction):
    global looping
    looping = not looping
    status = "Bật 🔁" if looping else "Tắt ⛔"
    await interaction.response.send_message(f"Trạng thái lặp: {status}")

@tree.command(name="stop", description="Dừng nhạc và rời kênh")
async def stop(interaction: discord.Interaction):
    global voice_client, current_audio, looping
    if voice_client and voice_client.is_connected():
        voice_client.stop()
        await voice_client.disconnect()
        voice_client = None
        current_audio = None
        looping = False
        await interaction.response.send_message("⏹️ Đã dừng nhạc, tắt lặp và rời kênh.")
    else:
        await interaction.response.send_message("❌ Bot không ở trong voice channel.")

client.run(TOKEN)




