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

        scores = [0]
        score = 0

        for result in history:

            if result == "W":
                score += 1
            elif result == "L":
                score -= 1

            scores.append(score)

        x = list(
            range(
                len(scores)
            )
        )

        fig, ax = plt.subplots(
            figsize=(8, 4)
        )

        bg = "#1A1B26"
        grid = "#2D3142"
        text = "#A9B1D6"

        green = "#4ADE80"
        red = "#F87171"
        grey = "#808080"

        fig.patch.set_facecolor(bg)
        ax.set_facecolor(bg)

        for i in range(
            len(scores) - 1
        ):

            if scores[i + 1] > scores[i]:
                color = green
            elif scores[i + 1] < scores[i]:
                color = red
            else:
                color = grey

            ax.plot(
                [x[i], x[i + 1]],
                [scores[i], scores[i + 1]],
                color=color,
                linewidth=3,
                solid_capstyle="round"
            )

        ax.scatter(
            x[1:],
            scores[1:],
            c=[
                green if r == "W"
                else (red if r == "L" else grey)
                for r in history
            ],
            s=35,
            zorder=5
        )

        ax.text(
            0.01,
            1.03,
            f"{username}'s Form",
            transform=ax.transAxes,
            color=text,
            fontsize=15,
            fontweight="bold",
            ha="left"
        )

        ax.grid(
            True,
            color=grid,
            alpha=0.45,
            linewidth=0.8
        )

        ax.spines["top"].set_visible(
            False
        )

        ax.spines["right"].set_visible(
            False
        )

        ax.spines["left"].set_color(
            grid
        )

        ax.spines["bottom"].set_color(
            grid
        )

        ax.tick_params(
            colors=text,
            labelsize=9
        )

        ax.set_xlabel(
            "Predictions",
            color=text
        )

        ax.set_ylabel(
            "Form",
            color=text
        )

        plt.tight_layout()

        buffer = BytesIO()

        plt.savefig(
            buffer,
            format="png",
            dpi=150,
            facecolor=bg
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