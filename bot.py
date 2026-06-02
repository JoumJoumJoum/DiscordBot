import os
import random
import discord
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CONFESSIONS_CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")


@client.event
async def on_message(message):
    # Ignore bots
    if message.author.bot:
        return

    # Only process DMs
    if not isinstance(message.channel, discord.DMChannel):
        return

    confession_channel = client.get_channel(CHANNEL_ID)

    if confession_channel is None:
        await message.channel.send(
            "The confession channel could not be found."
        )
        return

    # Require either text or attachments
    if not message.content and not message.attachments:
        await message.channel.send(
            "Please send a message or an attachment."
        )
        return

    anon_id = random.randint(1000, 9999)

    embed = discord.Embed(
        description=message.content if message.content else "*Attachment only*",
        color=0x2B2D31
    )

    embed.set_author(name=f"Anon #{anon_id}")

    files = [await attachment.to_file() for attachment in message.attachments]

    await confession_channel.send(
        embed=embed,
        files=files
    )

    await message.channel.send(
        "Your confession has been posted anonymously."
    )


client.run(TOKEN)