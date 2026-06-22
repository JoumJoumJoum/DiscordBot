
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
        style,
        button_type
    ):
        super().__init__(
            label=label,
            style=style,
            custom_id=button_type
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        await self.view.handle_vote(
            interaction,
            self.custom_id
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
                discord.ButtonStyle.green,
                "vote_home"
            )
        )

        if allow_draw:
            self.add_item(
                TeamButton(
                    "Draw",
                    discord.ButtonStyle.gray,
                    "vote_draw"
                )
            )

        self.add_item(
            TeamButton(
                away_team,
                discord.ButtonStyle.red,
                "vote_away"
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
        print("BUTTON CLICKED")
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

        matches = load_json(
            "worldcup_matches.json"
        )

        test_matches = load_json(
            "test_matches.json"
        )

        home_team = None
        away_team = None
        allow_draw = True

        for match in matches.values():

            if message_id == match.get("message_id"):

                home_team = match["home"]
                away_team = match["away"]

                allow_draw = (
                    match["stage"] == "GROUP_STAGE"
                )

                break

        for match in test_matches.values():

            if message_id == match.get("message_id"):

                home_team = match["home"]
                away_team = match["away"]
                allow_draw = True

                break

        if prediction == "vote_home":
            prediction = home_team

        elif prediction == "vote_away":
            prediction = away_team

        elif prediction == "vote_draw":
            prediction = "Draw"

        if message_id not in votes:
            votes[message_id] = {}

        if user_id in votes[message_id]:

            old_prediction = (
                votes[message_id][user_id]
                ["prediction"]
            )

            votes[message_id][user_id] = {
                "username":
                interaction.user.display_name,
                "prediction":
                prediction,
                "timestamp":
                datetime.now(
                    timezone.utc
                ).isoformat()
            }

            save_json(
                "votes.json",
                votes
            )

            await interaction.followup.send(
                f"Vote changed from "
                f"{old_prediction} to "
                f"{prediction}",
                ephemeral=True
            )

        else:

            votes[message_id][user_id] = {
                "username":
                interaction.user.display_name,
                "prediction":
                prediction,
                "timestamp":
                datetime.now(
                    timezone.utc
                ).isoformat()
            }

            save_json(
                "votes.json",
                votes
            )

            await interaction.followup.send(
                f"Vote recorded: "
                f"{prediction}",
                ephemeral=True
            )


        embed = interaction.message.embeds[0]

        kickoff_ts = None
        close_ts = None

        matches = load_json(
            "worldcup_matches.json"
        )

        test_matches = load_json(
            "test_matches.json"
        )



        home_team = None
        away_team = None
        allow_draw = True

        for match in matches.values():

            if (
                str(interaction.message.id)
                == match.get("message_id")
            ):

                kickoff = datetime.fromisoformat(
                    match["kickoff"].replace(
                        "Z",
                        "+00:00"
                    )
                )

                kickoff_ts = int(
                    kickoff.timestamp()
                )

                close_ts = int(
                    (
                        kickoff
                        - timedelta(hours=1.5)
                    ).timestamp()
                )

                home_team = match["home"]
                away_team = match["away"]

                allow_draw = (
                    match["stage"] == "GROUP_STAGE"
                )

                break


        for match in test_matches.values():

            if (
                str(interaction.message.id)
                == match.get("message_id")
            ):


                home_team = match["home"]
                away_team = match["away"]
                allow_draw = True



                kickoff = datetime.fromisoformat(
                    match["kickoff"]
                )

                kickoff_ts = int(
                    kickoff.timestamp()
                )

                close_ts = int(
                    (
                        kickoff
                        - timedelta(hours=1.5)
                    ).timestamp()
                )

                break



        if home_team is None:
            await interaction.followup.send(
                "Match data not found.",
                ephemeral=True
            )
            return

        vote_text = build_vote_description(
            votes[message_id],
            home_team,
            away_team,
            allow_draw
        )

        embed.description = (
            f"**{home_team} vs "
            f"{away_team}**\n\n"
            f"Kickoff\n"
            f"<t:{kickoff_ts}:F>\n\n"
            f"Voting closes\n"
            f"<t:{close_ts}:F>\n\n"
            f"{vote_text}"
        )

        print(vote_text)
        await interaction.message.edit(embed=embed)

        owner = await self.bot.fetch_user(OWNER_ID)

        await owner.send(
            f"NEW VOTE\n\n"
            f"User: {interaction.user}\n"
            f"User ID: {interaction.user.id}\n"
            f"Prediction: {prediction}\n"
            f"Message ID: {message_id}"
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

        voting_close = kickoff - timedelta(hours=1.5)

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
            content="<@&1511316717681246228>",
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
        name="upcoming",
        description="View matches in the next 24 hours"
    )
    async def todays_matches(
        self,
        interaction: discord.Interaction
    ):
        matches = load_json(
            "worldcup_matches.json"
        )

        votes = load_json(
            "votes.json"
        )

        today = datetime.now(
            timezone.utc
        )

        next_24h = today + timedelta(hours=24)

        lines = []

        for match in matches.values():
            
            if match["result_processed"]:
                continue

            kickoff = datetime.fromisoformat(
                match["kickoff"].replace(
                    "Z",
                    "+00:00"
                )
            )

            if kickoff < today or kickoff > next_24h:
                continue

            message_id = match.get(
                "message_id"
            )

            match_votes = votes.get(
                message_id,
                {}
            )

            home = match["home"]
            away = match["away"]

            home_count = 0
            away_count = 0
            draw_count = 0

            for vote in match_votes.values():

                prediction = vote[
                    "prediction"
                ]

                if prediction == home:
                    home_count += 1

                elif prediction == away:
                    away_count += 1

                elif prediction == "Draw":
                    draw_count += 1

            total_votes = len(
                match_votes
            )

            poll_url = (
                f"https://discord.com/channels/"
                f"{interaction.guild.id}/"
                f"{PREDICTION_CHANNEL_ID}/"
                f"{message_id}"
            )

            vote_line = (
                f"{home_count} - "
            )

            if (
                match["stage"]
                == "GROUP_STAGE"
            ):
                vote_line += (
                    f"{draw_count} - "
                )

            vote_line += (
                f"{away_count}"
            )

            lines.append(
                f"**{home} vs {away}**\n"
                f"Starts: <t:{int(kickoff.timestamp())}:R>\n"
                f"Votes: {total_votes}\n"
                f"{vote_line}\n"
                f"[Jump to Poll]({poll_url})"
            )

        if not lines:
            await interaction.response.send_message(
                "No matches in the next 24 hours.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"📅 Upcoming Matches ({len(lines)})",
            description="\n\n".join(lines),
            color=0x2B2D31
        )

        await interaction.response.send_message(
            embed=embed
        )

    @app_commands.command(
        name="createtestmatch",
        description="Create a custom test match"
    )
    @app_commands.describe(
        home="Home team",
        away="Away team",
        hours_until_kickoff="Hours from now"
    )
    async def create_test_match(
        self,
        interaction: discord.Interaction,
        home: str,
        away: str,
        hours_until_kickoff: int
    ):
        if not await self.owner_only(interaction):
            return

        kickoff = (
            datetime.now(timezone.utc)
            + timedelta(hours=hours_until_kickoff)
        )

        match = {
            "home": home,
            "away": away,
            "kickoff": kickoff.isoformat(),
            "stage": "GROUP_STAGE",
            "poll_created": True,
            "poll_closed": False,
            "result_processed": False,
            "is_test_match": True
        }

        message = await self.create_match_poll(
            match
        )

        match["message_id"] = str(
            message.id
        )

        test_matches = load_json(
            "test_matches.json"
        )

        test_matches[str(message.id)] = match

        save_json(
            "test_matches.json",
            test_matches
        )

        await interaction.response.send_message(
            f"Created {home} vs {away}",
            ephemeral=True
        )

    @app_commands.command(
        name="endtestmatch",
        description="End latest test match"
    )
    @app_commands.describe(
        winner="Winner or Draw"
    )
    async def end_test_match(
        self,
        interaction: discord.Interaction,
        winner: str
    ):
        if not await self.owner_only(interaction):
            return

        test_matches = load_json(
            "test_matches.json"
        )

        if not test_matches:
            await interaction.response.send_message(
                "No test matches found.",
                ephemeral=True
            )
            return

        latest_id = list(
            test_matches.keys()
        )[-1]

        match = test_matches[
            latest_id
        ]

        if match["result_processed"]:
            await interaction.response.send_message(
                "Already processed.",
                ephemeral=True
            )
            return

        

        winner = winner.strip().lower()

        home = match["home"].strip().lower()
        away = match["away"].strip().lower()

        if winner not in [
            home,
            away,
            "draw"
        ]:
            await interaction.response.send_message(
                f"Winner must be "
                f"{match['home']}, "
                f"{match['away']} or Draw.",
                ephemeral=True
            )
            return

        if winner == home:
            winner = match["home"]

        elif winner == away:
            winner = match["away"]

        else:
            winner = "Draw"


        votes = load_json(
            "votes.json"
        )

        leaderboard = load_json(
            "leaderboard.json"
        )

        message_id = match[
            "message_id"
        ]

        match_votes = votes.get(
            message_id,
            {}
        )

        winners = []

        losing_votes = 0

        for vote_data in match_votes.values():

            if (
                vote_data["prediction"]
                != winner
            ):
                losing_votes += 1

        points_awarded = max(
            1,
            losing_votes
        )

        for user_id, vote_data in match_votes.items():

            if (
                vote_data["prediction"]
                == winner
            ):

                if user_id not in leaderboard:

                    leaderboard[user_id] = {
                        "username":
                        vote_data["username"],
                        "points": 0
                    }

                leaderboard[user_id][
                    "points"
                ] += points_awarded

                winners.append(
                    vote_data["username"]
                )

        channel = self.bot.get_channel(
            PREDICTION_CHANNEL_ID
        )

        message = await channel.fetch_message(
            int(message_id)
        )

        embed = message.embeds[0]

        view = self.create_prediction_view(
            match["home"],
            match["away"],
            True
        )

        view.disable_all_buttons()

        embed.add_field(
            name="🏆 Result",
            value=winner,
            inline=False
        )

        embed.add_field(
            name="✅ Correct Predictions",
            value=(
                ", ".join(winners)
                if winners
                else "None"
            ),
            inline=False
        )

        await message.edit(
            embed=embed,
            view=view
        )

        await channel.send(
            f"🏆 **{match['home']} vs {match['away']}**\n"
            f"Winner: **{winner}**\n"
            f"Points Awarded: "
            f"**{points_awarded}**\n"
            f"Correct Predictions: "
            f"{', '.join(winners) if winners else 'None'}"
        )

        save_json(
            "leaderboard.json",
            leaderboard
        )

        if message_id in votes:

            del votes[message_id]

            save_json(
                "votes.json",
                votes
            )

        match["result_processed"] = True

        save_json(
            "test_matches.json",
            test_matches
        )

        await interaction.response.send_message(
            "Test match processed.",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Predictions(bot))

