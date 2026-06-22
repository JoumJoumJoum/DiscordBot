import discord
from discord.ext import commands
from discord import app_commands

from utils.storage import load_json

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt

from io import BytesIO


class Form(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    def calculate_streak(
        self,
        history
    ):
        streak = 0

        for result in reversed(history):

            if result == "W":
                streak += 1
            else:
                break

        return streak

    def generate_graph(
        self,
        username,
        history
    ):

        cumulative = []
        score = 0

        for result in history:

            if result == "W":
                score += 1
            else:
                score -= 1

            cumulative.append(score)

        plt.style.use("dark_background")

        fig, ax = plt.subplots(
            figsize=(8, 4)
        )

        x = list(
            range(
                1,
                len(cumulative) + 1
            )
        )

        ax.plot(
            x,
            cumulative,
            linewidth=3
        )

        ax.fill_between(
            x,
            cumulative,
            alpha=0.15
        )

        ax.set_title(
            f"{username}'s Form Trend",
            pad=15
        )

        ax.set_xlabel(
            "Predictions"
        )

        ax.set_ylabel(
            "Form Score"
        )

        ax.grid(
            alpha=0.2
        )

        ax.spines["top"].set_visible(
            False
        )

        ax.spines["right"].set_visible(
            False
        )

        buffer = BytesIO()

        plt.tight_layout()

        plt.savefig(
            buffer,
            format="png",
            dpi=150
        )

        plt.close()

        buffer.seek(0)

        return buffer

    @app_commands.command(
        name="form",
        description="View prediction form"
    )
    async def form(
        self,
        interaction: discord.Interaction,
        user: discord.Member = None
    ):

        target = (
            user
            if user
            else interaction.user
        )

        history_data = load_json(
            "prediction_history.json"
        )

        user_id = str(
            target.id
        )

        if user_id not in history_data:

            await interaction.response.send_message(
                "No prediction history found.",
                ephemeral=True
            )

            return

        data = history_data[
            user_id
        ]

        wins = data["wins"]

        losses = data["losses"]

        history = data["history"]

        total = wins + losses

        winrate = (
            round(
                wins / total * 100,
                1
            )
            if total > 0
            else 0
        )

        streak = self.calculate_streak(
            history
        )

        recent = " ".join(
            history[-10:]
        )

        graph = self.generate_graph(
            target.display_name,
            history
        )

        file = discord.File(
            graph,
            filename="form.png"
        )

        embed = discord.Embed(
            title=f"{target.display_name}'s Form",
            color=0x2B2D31
        )

        embed.add_field(
            name="🔥 Streak",
            value=str(streak)
        )

        embed.add_field(
            name="📈 Win Rate",
            value=f"{winrate}%"
        )

        embed.add_field(
            name="🎯 Record",
            value=f"{wins}-{losses}"
        )

        embed.add_field(
            name="Recent Form",
            value=(
                recent
                if recent
                else "No data"
            ),
            inline=False
        )

        embed.set_image(
            url="attachment://form.png"
        )

        await interaction.response.send_message(
            embed=embed,
            file=file
        )


async def setup(bot):
    await bot.add_cog(
        Form(bot)
    )