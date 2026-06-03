from discord.ext import commands
from discord import app_commands

from utils.storage import load_json


class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="leaderboard",
        description="View World Cup standings"
    )
    async def leaderboard(
        self,
        interaction
    ):
        leaderboard_data = load_json("leaderboard.json")

        if not leaderboard_data:
            await interaction.response.send_message(
                "No points have been awarded yet."
            )
            return

        sorted_users = sorted(
            leaderboard_data.items(),
            key=lambda x: x[1]["points"],
            reverse=True
        )

        lines = []

        for position, (_, user_data) in enumerate(
            sorted_users,
            start=1
        ):
            lines.append(
                f"{position}. {user_data['username']} - {user_data['points']} pts"
            )

        embed = discord.Embed(
            title="World Cup Standings",
            description="\n".join(lines),
            color=0x2B2D31
        )

        await interaction.response.send_message(
            embed=embed
        )


async def setup(bot):
    await bot.add_cog(Leaderboard(bot))