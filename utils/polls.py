import discord

from cogs.predictions import PredictionView


async def create_match_poll(
    bot,
    channel,
    match
):
    home = match["home"]
    away = match["away"]

    embed = discord.Embed(
        title="World Cup Prediction",
        color=0x2B2D31
    )

    embed.description = (
        f"**{home} vs {away}**\n\n"
        "Voting is open."
    )

    message = await channel.send(
        embed=embed,
        view=PredictionView(bot)
    )

    return message