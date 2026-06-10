import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

@bot.event
async def on_ready():
    guild = discord.Object(id=781139841445658624)

    bot.tree.copy_global_to(guild=guild)

    synced = await bot.tree.sync(guild=guild)

    print("Commands:")
    for cmd in synced:
        print(f"- {cmd.name}")

    print(f"Synced {len(synced)} guild commands")
    print(f"Logged in as {bot.user}")


@bot.tree.error
async def on_app_command_error(interaction, error):
    print("APP COMMAND ERROR:")
    print(repr(error))

    try:
        if not interaction.response.is_done():
            await interaction.response.send_message(
                str(error),
                ephemeral=True
            )
    except Exception:
        pass

@bot.command()
async def dumpdata(ctx):
    OWNER_ID = 310433679342043136

    if ctx.author.id != OWNER_ID:
        return

    files = []

    try:
        files.append(discord.File("data/worldcup_matches.json"))
    except FileNotFoundError:
        pass

    try:
        files.append(discord.File("data/leaderboard.json"))
    except FileNotFoundError:
        pass

    try:
        files.append(discord.File("data/votes.json"))
    except FileNotFoundError:
        pass

    if not files:
        await ctx.send("No data files found.")
        return

    await ctx.send(
        "Here are the data files:",
        files=files
    )

async def load_extensions():
    await bot.load_extension("cogs.confessions")
    await bot.load_extension("cogs.predictions")
    await bot.load_extension("cogs.leaderboard")
    await bot.load_extension("cogs.scheduler")

async def main():
    from utils.config import TOKEN

    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())