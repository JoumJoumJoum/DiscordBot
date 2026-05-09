import os
import random
import discord
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

# ── Config ──────────────────────────────────────────────────────────────────
TOKEN      = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CONFESSIONS_CHANNEL_ID"))

# ── Client ───────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
client  = discord.Client(intents=intents)
tree    = app_commands.CommandTree(client)

# ── /confess ─────────────────────────────────────────────────────────────────
class ConfessModal(discord.ui.Modal, title="Anonymous Confession 🤫"):
    confession = discord.ui.TextInput(
        label="Your confession (completely anonymous)",
        style=discord.TextStyle.paragraph,
        placeholder="Share what's on your mind...",
        min_length=5,
        max_length=1800,
    )

    async def on_submit(self, interaction: discord.Interaction):
        text    = self.confession.value          # text only — user identity ignored
        anon_id = random.randint(1000, 9999)     # random, NOT derived from user

        channel = client.get_channel(CHANNEL_ID)

        embed = (
            discord.Embed(description=text, color=0x2b2d31)
            .set_author(name=f"Anon #{anon_id}")
            .set_footer(text="Use /confess to submit your own")
        )

        await channel.send(embed=embed)
        await interaction.response.send_message(
            "✅ Posted anonymously. Your identity was never stored.", ephemeral=True
        )
        # ── No logging, no DB write, nothing. Identity discarded. ────────────


@tree.command(name="confess", description="Submit an anonymous confession 🤫")
async def confess(interaction: discord.Interaction):
    await interaction.response.send_modal(ConfessModal())


# ── /confessinfo ──────────────────────────────────────────────────────────────
@tree.command(name="confessinfo", description="How your anonymity is protected")
async def confessinfo(interaction: discord.Interaction):
    embed = (
        discord.Embed(
            title="🔒 How Your Anonymity Is Protected",
            description="No one — including the server owner — can link a confession back to you.",
            color=0x5865F2,
        )
        .add_field(name="📭 Zero Storage",   value="Your user ID is never written anywhere.",          inline=False)
        .add_field(name="🗄️ No Database",    value="The bot is stateless. Nothing persists.",          inline=False)
        .add_field(name="🔢 Random IDs",     value="Anon #XXXX is freshly random, not from your ID.", inline=False)
        .add_field(name="📂 Open Source",    value="The full code is public. Anyone can audit it.",    inline=False)
        .add_field(name="⚠️ One caveat",     value="Discord itself always knows who sent what.",       inline=False)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ── Start ─────────────────────────────────────────────────────────────────────
@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ {client.user} is online")

client.run(TOKEN)