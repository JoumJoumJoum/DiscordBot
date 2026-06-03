import random
import discord
from discord.ext import commands

from utils.config import CONFESSIONS_CHANNEL_ID


class Confessions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignore bots
        if message.author.bot:
            return

        # Only process DMs
        if not isinstance(message.channel, discord.DMChannel):
            return

        confession_channel = self.bot.get_channel(CONFESSIONS_CHANNEL_ID)

        if confession_channel is None:
            await message.channel.send(
                "The confession channel could not be found."
            )
            return

        if not message.content and not message.attachments:
            await message.channel.send(
                "Please send a message or attachment."
            )
            return

        anon_id = random.randint(100000, 999999)

        embed = discord.Embed(
            description=message.content if message.content else "*Attachment only*",
            color=0x2B2D31
        )

        embed.set_author(name=f"Anon #{anon_id}")

        files = [
            await attachment.to_file()
            for attachment in message.attachments
        ]

        await confession_channel.send(
            embed=embed,
            files=files
        )

        await message.channel.send(
            "Your confession has been posted anonymously."
        )


async def setup(bot):
    await bot.add_cog(Confessions(bot))