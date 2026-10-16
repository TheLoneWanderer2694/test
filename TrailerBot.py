import os
import json
import discord
from discord.ext import commands, tasks
import feedparser
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# ID of the Discord channel where videos should be posted
TRAILER_CHANNEL_ID = 1560749797806182410  

# YouTube Channel RSS Feeds
RSS_FEEDS = {
    "Dead Meat": "https://www.youtube.com/feeds/videos.xml?channel_id=UC2IYWWifoIht9T47z1Z5lJw",
    "Tokyo Lens": "https://www.youtube.com/feeds/videos.xml?channel_id=UCnrVURWNd7VYjlQQ0UDpOQQ",
    "Night Mind": "https://www.youtube.com/feeds/videos.xml?channel_id=UC5VOefoxvDB2GeW9U6unl7Q"
}

POSTED_VIDEOS_FILE = "posted_videos.json"

def load_posted_videos():
    if os.path.exists(POSTED_VIDEOS_FILE):
        try:
            with open(POSTED_VIDEOS_FILE, "r") as f:
                content = f.read()
                if not content.strip():
                    return set()
                return set(json.loads(content))
        except json.JSONDecodeError:
            # If the file is corrupted or empty, return an empty set
            return set()
    return set()

def save_posted_videos(posted_set):
    with open(POSTED_VIDEOS_FILE, "w") as f:
        json.dump(list(posted_set), f)

posted_videos = load_posted_videos()

# Set up bot intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")
    
    if not check_for_new_videos.is_running():
        check_for_new_videos.start()

# Background task checking YouTube feeds every 15 minutes
@tasks.loop(minutes=15)
async def check_for_new_videos():
    print("Checking YouTube feeds for new uploads...")
    try:
        channel = await bot.fetch_channel(TRAILER_CHANNEL_ID)
    except discord.NotFound:
        print(f"Error: Channel with ID {TRAILER_CHANNEL_ID} was not found.")
        return
    except discord.Forbidden:
        print(f"Error: Bot does not have permission to view/send messages in channel {TRAILER_CHANNEL_ID}.")
        return
    except Exception as e:
        print(f"Error fetching channel: {e}")
        return

    for source_name, feed_url in RSS_FEEDS.items():
        feed = feedparser.parse(feed_url)
        
        for entry in feed.entries[:3]:
            video_id = entry.yt_videoid
            
            if video_id not in posted_videos:
                video_url = entry.link
                
                message = f"🚨 **New Video Drop!** [{source_name}]\n**{entry.title}**\n{video_url}"
                
                try:
                    await channel.send(message)
                    print(f"Successfully posted video: {entry.title}")
                    
                    posted_videos.add(video_id)
                    save_posted_videos(posted_videos)
                except Exception as e:
                    print(f"Failed to send message: {e}")

@check_for_new_videos.before_loop
async def before_check():
    await bot.wait_until_ready()

if __name__ == "__main__":
    if not TOKEN:
        print("Error: DISCORD_TOKEN not found in environment variables or .env file.")
    else:
        bot.run(TOKEN)