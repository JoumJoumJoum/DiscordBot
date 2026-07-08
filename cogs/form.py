import discord
from discord.ext import commands
from discord import app_commands

from utils.storage import load_json

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image, ImageOps, ImageDraw
import aiohttp
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
        yellow = "#FBBF24"

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
                color = yellow

            ax.plot(
                [x[i], x[i + 1]],
                [scores[i], scores[i + 1]],
                color=color,
                linewidth=3,
                solid_capstyle="round"
            )

        scatter_x = []
        scatter_y = []
        scatter_colors = []
        scatter_sizes = []

        for idx, r in enumerate(history, start=1):
            if r in ["W", "L"]:
                scatter_x.append(x[idx])
                scatter_y.append(scores[idx])
                scatter_colors.append(green if r == "W" else red)
                scatter_sizes.append(35)
            else:
                scatter_x.append(x[idx])
                scatter_y.append(scores[idx])
                scatter_colors.append(yellow)
                scatter_sizes.append(35)

        ax.scatter(
            scatter_x,
            scatter_y,
            c=scatter_colors,
            s=scatter_sizes,
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

    @app_commands.command(
        name="versus",
        description="Compare the points progress of two users in a graph race"
    )
    @app_commands.describe(
        user1="First user to compare",
        user2="Second user to compare"
    )
    async def versus(
        self,
        interaction: discord.Interaction,
        user1: discord.Member,
        user2: discord.Member
    ):
        await interaction.response.defer()

        points_history_data = load_json("points_history.json")

        user1_id = str(user1.id)
        user2_id = str(user2.id)

        history1 = points_history_data.get(user1_id, {}).get("points_history", [0])
        history2 = points_history_data.get(user2_id, {}).get("points_history", [0])

        if not history1:
            history1 = [0]
        if not history2:
            history2 = [0]

        max_len = max(len(history1), len(history2))
        h1_extended = history1 + [history1[-1]] * (max_len - len(history1))
        h2_extended = history2 + [history2[-1]] * (max_len - len(history2))

        x = list(range(max_len))

        fig, ax = plt.subplots(figsize=(8, 4))

        bg = "#1A1B26"
        grid = "#2D3142"
        text = "#A9B1D6"

        pink = "#FF2E93"
        blue = "#00F0FF"

        fig.patch.set_facecolor(bg)
        ax.set_facecolor(bg)

        ax.plot(
            x,
            h1_extended,
            color=pink,
            linewidth=3,
            label=user1.display_name,
            solid_capstyle="round"
        )

        ax.plot(
            x,
            h2_extended,
            color=blue,
            linewidth=3,
            label=user2.display_name,
            solid_capstyle="round"
        )

        user1_avatar_bytes = None
        user2_avatar_bytes = None

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(str(user1.display_avatar.url)) as r:
                    if r.status == 200:
                        user1_avatar_bytes = await r.read()
            except Exception:
                pass

            try:
                async with session.get(str(user2.display_avatar.url)) as r:
                    if r.status == 200:
                        user2_avatar_bytes = await r.read()
            except Exception:
                pass

        if user1_avatar_bytes:
            try:
                img1 = make_circular_avatar(user1_avatar_bytes, size=32)
                imagebox1 = OffsetImage(img1, zoom=1.0)
                ab1 = AnnotationBbox(imagebox1, (x[-1], h1_extended[-1]), frameon=False)
                ax.add_artist(ab1)
            except Exception as e:
                print(f"Error drawing avatar 1: {e}")

        if user2_avatar_bytes:
            try:
                img2 = make_circular_avatar(user2_avatar_bytes, size=32)
                imagebox2 = OffsetImage(img2, zoom=1.0)
                ab2 = AnnotationBbox(imagebox2, (x[-1], h2_extended[-1]), frameon=False)
                ax.add_artist(ab2)
            except Exception as e:
                print(f"Error drawing avatar 2: {e}")

        ax.text(
            0.01,
            1.05,
            f"⚔️ Prediction Race: {user1.display_name} vs {user2.display_name}",
            transform=ax.transAxes,
            color=text,
            fontsize=14,
            fontweight="bold",
            ha="left"
        )

        ax.grid(True, color=grid, alpha=0.45, linewidth=0.8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(grid)
        ax.spines["bottom"].set_color(grid)

        ax.tick_params(colors=text, labelsize=9)
        ax.set_xlabel("Match Day / Predictions", color=text)
        ax.set_ylabel("Accumulated Points", color=text)

        ax.legend(
            facecolor=bg,
            edgecolor=grid,
            labelcolor=text,
            loc="upper left"
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

        file = discord.File(buffer, filename="versus.png")

        embed = discord.Embed(
            title=f"⚔️ Versus: {user1.display_name} vs {user2.display_name}",
            description=(
                f"**{user1.display_name}**: `{h1_extended[-1]} pts` (Pink Line)\n"
                f"**{user2.display_name}**: `{h2_extended[-1]} pts` (Blue Line)"
            ),
            color=0x2B2D31
        )
        embed.set_image(url="attachment://versus.png")

        await interaction.followup.send(
            embed=embed,
            file=file
        )

def make_circular_avatar(avatar_bytes, size=30):
    img = Image.open(BytesIO(avatar_bytes)).convert("RGBA")
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    
    output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    output.paste(img, (0, 0), mask=mask)
    
    draw_border = ImageDraw.Draw(output)
    draw_border.ellipse((0, 0, size-1, size-1), outline="white", width=2)
    
    return output


async def setup(bot):
    await bot.add_cog(
        Form(bot)
    )