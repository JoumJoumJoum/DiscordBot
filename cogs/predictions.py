
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta, timezone
from utils.worldcup import (
    import_world_cup_matches
)

from utils.config import (
    PREDICTION_CHANNEL_ID,
    PREDICTION_ROLE_ID,
    OWNER_ID
)

from utils.worldcup import fetch_world_cup_matches

from utils.storage import load_json, save_json


def build_vote_description(
    votes,
    home_team,
    away_team,
    allow_draw=True
):
    sections = {
        home_team: [],
        away_team: []
    }

    if allow_draw:
        sections["Draw"] = []

    for vote in votes.values():

        prediction = vote["prediction"]

        if prediction in sections:
            sections[prediction].append(
                vote["username"]
            )

    output = []

    for option, voters in sections.items():

        output.append(
            f"{option} ({len(voters)})"
        )

        for voter in voters:
            output.append(
                f"• {voter}"
            )

        output.append("")

    return "\n".join(output)


class TeamButton(discord.ui.Button):

    def __init__(
        self,
        label,
        style
    ):
        super().__init__(
            label=label,
            style=style
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        await self.view.handle_vote(
            interaction,
            self.label
        )

class PredictionView(discord.ui.View):
    def __init__(
        self,
        bot,
        home_team,
        away_team,
        allow_draw=True
    ):
        super().__init__(timeout=None)

        self.bot = bot
        self.home_team = home_team
        self.away_team = away_team
        self.allow_draw = allow_draw

        self.add_item(
            TeamButton(
                home_team,
                discord.ButtonStyle.green
            )
        )

        if allow_draw:
            self.add_item(
                TeamButton(
                    "Draw",
                    discord.ButtonStyle.gray
                )
            )

        self.add_item(
            TeamButton(
                away_team,
                discord.ButtonStyle.red
            )
        )
    def disable_all_buttons(self):
        for item in self.children:
            item.disabled = True

    async def handle_vote(
        self,
        interaction: discord.Interaction,
        prediction: str
    ):
        await interaction.response.defer(ephemeral=True)
        role_ids = [role.id for role in interaction.user.roles]

        if PREDICTION_ROLE_ID not in role_ids:
            await interaction.followup.send(
                "You do not have permission to participate.",
                ephemeral=True
            )
            return

        votes = load_json("votes.json")

        message_id = str(interaction.message.id)
        user_id = str(interaction.user.id)

        if message_id not in votes:
            votes[message_id] = {}

        if user_id in votes[message_id]:
            await interaction.followup.send(
                "You have already voted.",
                ephemeral=True
            )
            return

        votes[message_id][user_id] = {
            "username": interaction.user.display_name,
            "prediction": prediction,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        save_json("votes.json", votes)

        embed = interaction.message.embeds[0]

        embed.description = (
            f"**{self.home_team} vs "
            f"{self.away_team}**\n\n"
            + build_vote_description(
                votes[message_id],
                self.home_team,
                self.away_team,
                self.allow_draw
            )
        )

        await interaction.message.edit(embed=embed)

        owner = await self.bot.fetch_user(OWNER_ID)

        await owner.send(
            f"NEW VOTE\n\n"
            f"User: {interaction.user}\n"
            f"User ID: {interaction.user.id}\n"
            f"Prediction: {prediction}\n"
            f"Message ID: {message_id}"
        )

        await interaction.followup.send(
            f"Vote recorded: {prediction}",
            ephemeral=True
        )



class Predictions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def owner_only(
        self,
        interaction: discord.Interaction
    ):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message(
                "Owner only.",
                ephemeral=True
            )
            return False

        return True

    def create_prediction_view(
        self,
        home,
        away,
        allow_draw=True
    ):
        return PredictionView(
            self.bot,
            home,
            away,
            allow_draw
        )

    async def create_match_poll(
        self,
        match
    ):
        channel = self.bot.get_channel(
            PREDICTION_CHANNEL_ID
        )

        home = match["home"]
        away = match["away"]

        allow_draw = (
            match["stage"] == "GROUP_STAGE"
        )

        kickoff = datetime.fromisoformat(
            match["kickoff"].replace(
                "Z",
                "+00:00"
            )
        )

        voting_close = kickoff - timedelta(hours=2)

        embed = discord.Embed(
            title="World Cup Prediction",
            color=0x2B2D31
        )

        description = (
            f"**{home} vs {away}**\n\n"
            f"Kickoff\n"
            f"<t:{int(kickoff.timestamp())}:F>\n\n"
            f"Voting closes\n"
            f"<t:{int(voting_close.timestamp())}:F>\n\n"
        )

        description += build_vote_description(
            {},
            home,
            away,
            allow_draw
        )

        embed.description = description

        message = await channel.send(
            embed=embed,
            view=PredictionView(
                self.bot,
                home,
                away,
                allow_draw
            )
        )

        return message
    @app_commands.command(
        name="myprediction",
        description="View your active predictions"
    )
    async def my_prediction(
        self,
        interaction: discord.Interaction
    ):
        votes = load_json("votes.json")
        matches = load_json("worldcup_matches.json")
        user_id = str(interaction.user.id)

        predictions = []

        for message_id, match_votes in votes.items():
            if user_id in match_votes:
                vote = match_votes[user_id]

                
                match = matches.get(message_id)
                if match:
                    predictions.append(
                        f"{match['home']} vs {match['away']}\n"
                        f"Prediction: {vote['prediction']}"
                    )

        if not predictions:
            await interaction.response.send_message(
                "You have no active predictions.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="Your Active Predictions",
            description="\n\n".join(predictions),
            color=0x2B2D31
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

    @app_commands.command(
        name="worldcuptest",
        description="Test World Cup API"
    )
    async def world_cup_test(
        self,
        interaction: discord.Interaction
    ):
        if not await self.owner_only(interaction):
            return
        matches = await fetch_world_cup_matches()

        if not matches:
            await interaction.response.send_message(
                "No matches returned.",
                ephemeral=True
            )
            return

        first_match = matches[0]

        home = first_match["homeTeam"]["name"]
        away = first_match["awayTeam"]["name"]
        kickoff = first_match["utcDate"]

        await interaction.response.send_message(
            f"{home} vs {away}\n{kickoff}",
            ephemeral=True
        )

    @app_commands.command(
        name="apitest",
        description="Test API Football"
    )
    async def api_test(
        self,
        interaction: discord.Interaction
    ):
        if not await self.owner_only(interaction):
            return
        data = await get_world_cup_fixtures()

        print(data)

        await interaction.response.send_message(
            f"Fixtures returned: {len(data['response'])}",
            ephemeral=True
        )

    @app_commands.command(
        name="testpoints",
        description="Give yourself a point for testing"
    )
    async def test_points(
        self,
        interaction: discord.Interaction
    ):
        if not await self.owner_only(interaction):
            return

        leaderboard = load_json("leaderboard.json")

        user_id = str(interaction.user.id)

        if user_id not in leaderboard:
            leaderboard[user_id] = {
                "username": interaction.user.display_name,
                "points": 0
            }

        leaderboard[user_id]["points"] += 1

        save_json("leaderboard.json", leaderboard)

        await interaction.response.send_message(
            "Point added.",
            ephemeral=True
        )

    @app_commands.command(
        name="forceresult",
        description="Resolve latest open match"
    )
    @app_commands.describe(
        winner="Brazil, Germany or Draw"
    )
    async def force_result(
        self,
        interaction: discord.Interaction,
        winner: str
    ):
        winner = winner.title()

        if not await self.owner_only(interaction):
            return

        if winner not in ["Brazil", "Germany", "Draw"]:
            await interaction.response.send_message(
                "Winner must be Brazil, Germany or Draw.",
                ephemeral=True
            )
            return
        
        votes = load_json("votes.json")
        leaderboard = load_json("leaderboard.json")

        open_match_id = None
        open_match = None

        for match_id, match_data in matches.items():
            if (
                match_data["status"] == "open"
                and not match_data.get("points_awarded", False)
            ):
                open_match_id = match_id
                open_match = match_data

        if open_match is None:
            await interaction.response.send_message(
                "No open matches found.",
                ephemeral=True
            )
            return

        match_votes = votes.get(open_match_id, {})

        correct_users = []
        incorrect_users = []

        for user_id, vote in match_votes.items():
            prediction = vote["prediction"]

            if prediction == winner:
                if user_id not in leaderboard:
                    leaderboard[user_id] = {
                        "username": vote["username"],
                        "points": 0
                    }

                leaderboard[user_id]["points"] += 1
                correct_users.append(vote["username"])
            else:
                incorrect_users.append(vote["username"])

        open_match["result"] = winner
        open_match["status"] = "finished"
        open_match["points_awarded"] = True

        save_json("worldcup_matches.json", matches)
        save_json("leaderboard.json", leaderboard)

        correct_text = (
            "\n".join(f"• {user}" for user in correct_users)
            if correct_users else
            "None"
        )

        incorrect_text = (
            "\n".join(f"• {user}" for user in incorrect_users)
            if incorrect_users else
            "None"
        )

        embed = discord.Embed(
            title="Match Resolved",
            color=0x2B2D31
        )

        embed.description = (
            f"**{open_match['home']} vs "
            f"{open_match['away']}**\n\n"
            f"Winner: **{winner}**\n\n"
            f"Correct\n"
            f"{correct_text}\n\n"
            f"Incorrect\n"
            f"{incorrect_text}"
        )

        owner = await self.bot.fetch_user(OWNER_ID)

        await owner.send(
            f"MATCH RESOLVED\n\n"
            f"{open_match['home']} vs "
            f"{open_match['away']}\n"
            f"Winner: {winner}\n"
            f"Correct: {len(correct_users)}\n"
            f"Incorrect: {len(incorrect_users)}"
        )

        await interaction.response.send_message(
            embed=embed
        )

    @app_commands.command(
        name="createtestmatch",
        description="Create a test prediction poll"
    )
    async def create_test_match(
        self,
        interaction: discord.Interaction
    ):
        channel = self.bot.get_channel(PREDICTION_CHANNEL_ID)

        if not await self.owner_only(interaction):
            return

        if channel is None:
            await interaction.response.send_message(
                "Prediction channel not found.",
                ephemeral=True
            )
            return

        kickoff = datetime.now(timezone.utc) + timedelta(minutes=10)
        voting_close = datetime.now(timezone.utc) + timedelta(minutes=5)

        embed = discord.Embed(
            title="World Cup Prediction",
            color=0x2B2D31
        )

        embed.description = (
            "**Mexico vs South Africa**\n\n"
            f"Kickoff\n<t:{int(kickoff.timestamp())}:F>\n\n"
            f"Voting closes\n<t:{int(voting_close.timestamp())}:F>\n\n"
            "Mexico (0)\n\n"
            "Draw (0)\n\n"
            "South Africa (0)"
        )

        poll_message = await channel.send(
            embed=embed,
            view=PredictionView(
                self.bot,
                "Mexico",
                "South Africa",
                True
            )
        )

        
        matches = load_json("worldcup_matches.json")
        matches[str(poll_message.id)] = {
            "home": "Mexico",
            "away": "South Africa",
            "kickoff": kickoff.isoformat(),
            "voting_close": voting_close.isoformat(),
            "status": "open",
            "result": None,
            "points_awarded": False
        }

        save_json("worldcup_matches.json", matches)

        await interaction.response.send_message(
            "Test match created.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Predictions(bot))

