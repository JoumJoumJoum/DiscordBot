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
from cogs.scheduler import (
    update_all_prediction_histories,
    update_all_points_histories
)


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
        description="Force the result of a World Cup match"
    )
    @app_commands.describe(
        message_id="Discord message ID of the prediction poll",
        winner="Winning team name or Draw"
    )
    async def force_result(
        self,
        interaction: discord.Interaction,
        message_id: str,
        winner: str
    ):
        if not await self.owner_only(interaction):
            return

        matches = load_json("worldcup_matches.json")
        votes = load_json("votes.json")
        leaderboard = load_json("leaderboard.json")

        match = None

        for match_data in matches.values():
            if match_data.get("message_id") == message_id:
                match = match_data
                break

        if match is None:
            await interaction.response.send_message(
                "Match not found.",
                ephemeral=True
            )
            return

        if match["result_processed"]:
            await interaction.response.send_message(
                "Result already processed.",
                ephemeral=True
            )
            return

        winner = winner.strip()

        if winner.lower() == "draw":
            winner = "Draw"
        elif winner.lower() == match["home"].lower():
            winner = match["home"]
        elif winner.lower() == match["away"].lower():
            winner = match["away"]
        else:
            await interaction.response.send_message(
                f"Winner must be {match['home']}, {match['away']} or Draw.",
                ephemeral=True
            )
            return

        match_votes = votes.get(message_id, {})

        winners = []

        losing_votes = sum(
            1
            for vote in match_votes.values()
            if vote["prediction"] != winner
        )

        points_awarded = max(1, losing_votes)

        update_all_prediction_histories(
            match_votes,
            winner,
            leaderboard
        )
        update_all_points_histories(
            match_votes,
            winner,
            points_awarded,
            leaderboard
        )

        for user_id, vote_data in match_votes.items():

            correct = vote_data["prediction"] == winner

            if correct:

                if user_id not in leaderboard:
                    leaderboard[user_id] = {
                        "username": vote_data["username"],
                        "points": 0
                    }

                leaderboard[user_id]["points"] += points_awarded
                winners.append(vote_data["username"])

        channel = self.bot.get_channel(
            PREDICTION_CHANNEL_ID
        ) or await self.bot.fetch_channel(
            PREDICTION_CHANNEL_ID
        )

        message = await channel.fetch_message(
            int(message_id)
        )

        embed = message.embeds[0]

        view = self.create_prediction_view(
            match["home"],
            match["away"],
            match["stage"] == "GROUP_STAGE"
        )

        view.disable_all_buttons()

        embed.add_field(
            name="🏆 Result",
            value=winner,
            inline=False
        )

        embed.add_field(
            name="✅ Correct Predictions",
            value=", ".join(winners) if winners else "None",
            inline=False
        )

        await message.edit(
            embed=embed,
            view=view
        )

        await channel.send(
            f"🏆 **{match['home']} vs {match['away']}**\n"
            f"Winner: **{winner}**\n"
            f"Points Awarded: **{points_awarded}**\n"
            f"Correct Predictions: "
            f"{', '.join(winners) if winners else 'None'}"
        )

        if message_id in votes:
            del votes[message_id]

        match["result_processed"] = True

        save_json(
            "votes.json",
            votes
        )

        save_json(
            "leaderboard.json",
            leaderboard
        )

        save_json(
            "worldcup_matches.json",
            matches
        )

        await interaction.response.send_message(
            "Result forced successfully.",
            ephemeral=True
        )

    @app_commands.command(
        name="revertmatch",
        description="Revert a match outcome: restores votes, adjusts leaderboard points, and resets history."
    )
    @app_commands.describe(
        message_id="Discord message ID of the prediction poll"
    )
    async def revert_match(
        self,
        interaction: discord.Interaction,
        message_id: str
    ):
        if not await self.owner_only(interaction):
            return

        await interaction.response.defer(ephemeral=True)

        matches = load_json("worldcup_matches.json")
        match = None

        for match_data in matches.values():
            if match_data.get("message_id") == message_id:
                match = match_data
                break

        if match is None:
            await interaction.followup.send(
                "Match not found in database.",
                ephemeral=True
            )
            return

        if not match.get("result_processed"):
            await interaction.followup.send(
                "Match result has not been processed yet.",
                ephemeral=True
            )
            return

        # Fetch the message
        channel = self.bot.get_channel(
            PREDICTION_CHANNEL_ID
        ) or await self.bot.fetch_channel(
            PREDICTION_CHANNEL_ID
        )

        try:
            message = await channel.fetch_message(int(message_id))
        except Exception as e:
            await interaction.followup.send(
                f"Failed to fetch match message from Discord: {e}",
                ephemeral=True
            )
            return

        if not message.embeds:
            await interaction.followup.send(
                "Discord message has no embeds to parse.",
                ephemeral=True
            )
            return

        embed = message.embeds[0]

        # 1. Parse the processed result from the embed
        processed_winner = None
        for field in embed.fields:
            if field.name == "🏆 Result":
                processed_winner = field.value
                break

        if not processed_winner:
            await interaction.followup.send(
                "Could not find processed result field in the message embed.",
                ephemeral=True
            )
            return

        # 2. Parse votes from the embed description
        embed_desc = embed.description or ""
        parsed_votes = {}  # username -> prediction
        current_option = None

        for line in embed_desc.split("\n"):
            line = line.strip()
            if not line:
                continue
            if line.startswith("• "):
                voter_username = line[2:].strip()
                if current_option:
                    parsed_votes[voter_username] = current_option
            else:
                for opt in [match["home"], match["away"], "Draw"]:
                    if line.startswith(opt):
                        current_option = opt
                        break

        # 3. Create map of username (lowercase) to user ID
        leaderboard = load_json("leaderboard.json")
        history = load_json("prediction_history.json")
        points_history = load_json("points_history.json")
        username_to_id = {}

        for uid, udata in leaderboard.items():
            username_to_id[udata["username"].lower()] = uid
        for uid, udata in history.items():
            username_to_id[udata["username"].lower()] = uid

        # Fallback: query guild members
        try:
            async for member in interaction.guild.fetch_members(limit=None):
                username_to_id[member.display_name.lower()] = str(member.id)
                username_to_id[member.name.lower()] = str(member.id)
        except Exception:
            pass

        # 4. Calculate points awarded
        losing_votes = 0
        for voter_username, prediction in parsed_votes.items():
            if prediction != processed_winner:
                losing_votes += 1
        points_awarded = max(1, losing_votes)

        # 5. Revert leaderboard points and history
        reverted_voters = []
        not_found_voters = []

        for voter_username, prediction in parsed_votes.items():
            user_id = username_to_id.get(voter_username.lower())
            if not user_id:
                not_found_voters.append(voter_username)
                continue

            correct = (prediction == processed_winner)
            reverted_voters.append(voter_username)

            # Revert leaderboard points
            if correct and user_id in leaderboard:
                leaderboard[user_id]["points"] = max(0, leaderboard[user_id]["points"] - points_awarded)

            # Revert prediction history
            if user_id in history:
                user_hist = history[user_id]
                if user_hist["history"]:
                    last_result = user_hist["history"].pop()
                    if last_result == "W":
                        user_hist["wins"] = max(0, user_hist["wins"] - 1)
                    elif last_result == "L":
                        user_hist["losses"] = max(0, user_hist["losses"] - 1)
                    
                    # Recalculate streak
                    streak = 0
                    for item in reversed(user_hist["history"]):
                        if item == "W":
                            streak += 1
                        else:
                            break
                    user_hist["streak"] = streak

            # Revert points history
            if user_id in points_history:
                user_pts = points_history[user_id]
                if len(user_pts["points_history"]) > 1:
                    user_pts["points_history"].pop()
                    user_pts["current_points"] = user_pts["points_history"][-1]

        # 6. Rebuild and restore votes.json
        votes = load_json("votes.json")
        votes[message_id] = {}
        for voter_username, prediction in parsed_votes.items():
            user_id = username_to_id.get(voter_username.lower())
            if user_id:
                votes[message_id][user_id] = {
                    "username": voter_username,
                    "prediction": prediction,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

        # 7. Update match status in worldcup_matches.json
        match["result_processed"] = False
        match["poll_closed"] = False

        # Save all files
        save_json("votes.json", votes)
        save_json("leaderboard.json", leaderboard)
        save_json("prediction_history.json", history)
        save_json("points_history.json", points_history)
        save_json("worldcup_matches.json", matches)

        # 8. Reset message embed and view in Discord
        new_fields = []
        for field in embed.fields:
            if field.name not in ["🏆 Result", "✅ Correct Predictions"]:
                new_fields.append(field)
        embed.clear_fields()
        for field in new_fields:
            embed.add_field(name=field.name, value=field.value, inline=field.inline)

        view = self.create_prediction_view(
            match["home"],
            match["away"],
            match["stage"] == "GROUP_STAGE"
        )

        await message.edit(
            embed=embed,
            view=view
        )

        response_msg = (
            f"Successfully reverted match **{match['home']} vs {match['away']}**.\n\n"
            f"✅ **Reverted Status:** `result_processed = False` and `poll_closed = False`.\n"
            f"✅ **Restored Votes:** {len(votes[message_id])} predictions restored to database.\n"
            f"✅ **Adjusted Points:** Deducted **{points_awarded}** points from correct predictors.\n"
            f"✅ **Adjusted History:** Removed last prediction result from player history records."
        )

        if not_found_voters:
            response_msg += f"\n\n⚠️ **Notice:** Could not find user IDs for the following usernames to deduct points/history: {', '.join(not_found_voters)}"

        await interaction.followup.send(
            response_msg,
            ephemeral=True
        )

    @app_commands.command(
        name="help",
        description="Show all available commands and their descriptions"
    )
    async def help_command(
        self,
        interaction: discord.Interaction
    ):
        embed = discord.Embed(
            title="⚽ FIFA Bot Command Help",
            description="Here are all the available slash and prefix commands in this bot:",
            color=0x2B2D31
        )

        embed.add_field(
            name="📊 General Commands",
            value=(
                "**`/leaderboard`** - View the current World Cup standings and points.\n"
                "**`/form [user]`** - View yours or another member's prediction history, streak, and form chart.\n"
                "**`/versus [user1] [user2]`** - Compare the points progress of two users in a graph race.\n"
                "**`/myprediction`** - View your active predictions for upcoming matches.\n"
                "**`/upcoming`** - View matches starting in the next 24 hours with poll links and vote counts."
            ),
            inline=False
        )

        embed.add_field(
            name="🛠️ Admin Commands (Owner Only)",
            value=(
                "**`/forceresult [message_id] [winner]`** - Force a match result (winner team name or Draw) and award points.\n"
                "**`/revertmatch [message_id]`** - Revert a match: deducts points, adjusts streaks/history, restores votes.\n"
                "**`/rebuildhistory`** - Reconstruct prediction history including flatlines (no-votes) from channel logs.\n"
                "**`/createtestmatch [home] [away] [hours]`** - Create a custom match poll for testing.\n"
                "**`/testpoints`** - Give yourself 1 point on the leaderboard for testing.\n"
                "**`!dumpdata`** - (Prefix Command) Dumps the bot's raw database JSON files."
            ),
            inline=False
        )

        embed.add_field(
            name="🤫 DM Features",
            value="Send a Direct Message to the bot with text/images to post anonymously in the confessions channel.",
            inline=False
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

    @app_commands.command(
        name="rebuildhistory",
        description="Reconstruct prediction history (including D for no-votes) from Discord channel messages."
    )
    async def rebuild_history(
        self,
        interaction: discord.Interaction
    ):
        if not await self.owner_only(interaction):
            return

        await interaction.response.defer(ephemeral=True)

        matches = load_json("worldcup_matches.json")
        leaderboard = load_json("leaderboard.json")
        
        # Sort processed matches chronologically by kickoff date
        processed_matches = []
        for match_id, mdata in matches.items():
            if mdata.get("result_processed") and mdata.get("message_id"):
                processed_matches.append((match_id, mdata))
                
        # Sort by kickoff date
        processed_matches.sort(key=lambda x: x[1].get("kickoff", ""))

        channel = interaction.channel

        # Initialize fresh history and points structure for all users in the leaderboard
        reconstructed_history = {}
        reconstructed_points = {}
        for uid, udata in leaderboard.items():
            reconstructed_history[uid] = {
                "username": udata["username"],
                "wins": 0,
                "losses": 0,
                "streak": 0,
                "history": []
            }
            reconstructed_points[uid] = {
                "username": udata["username"],
                "current_points": 0,
                "points_history": [0]
            }

        # Mapping for display names to user ID
        username_to_id = {}
        for uid, udata in leaderboard.items():
            username_to_id[udata["username"].lower()] = uid

        try:
            async for member in interaction.guild.fetch_members(limit=None):
                username_to_id[member.display_name.lower()] = str(member.id)
                username_to_id[member.name.lower()] = str(member.id)
        except Exception:
            pass

        processed_count = 0
        failed_count = 0

        for match_id, mdata in processed_matches:
            message_id = mdata["message_id"]
            try:
                msg = await channel.fetch_message(int(message_id))
            except Exception:
                failed_count += 1
                continue

            if not msg.embeds:
                failed_count += 1
                continue

            embed = msg.embeds[0]

            # Parse processed result from embed
            processed_winner = None
            for field in embed.fields:
                if field.name == "🏆 Result":
                    processed_winner = field.value
                    break

            if not processed_winner:
                failed_count += 1
                continue

            # Parse votes from embed description
            embed_desc = embed.description or ""
            parsed_votes = {}  # username -> prediction
            current_option = None

            for line in embed_desc.split("\n"):
                line = line.strip()
                if not line:
                    continue
                if line.startswith("• "):
                    voter_username = line[2:].strip()
                    if current_option:
                        parsed_votes[voter_username] = current_option
                else:
                    for opt in [mdata["home"], mdata["away"], "Draw"]:
                        if line.startswith(opt):
                            current_option = opt
                            break

            # Update prediction and points history for this match
            losing_votes = 0
            for voter_username, prediction in parsed_votes.items():
                if prediction != processed_winner:
                    losing_votes += 1
            points_awarded = max(1, losing_votes)

            voted_user_ids = set()
            for voter_username, prediction in parsed_votes.items():
                user_id = username_to_id.get(voter_username.lower())
                if user_id:
                    voted_user_ids.add(user_id)
                    # If this user is not in our dict yet, initialize them
                    if user_id not in reconstructed_history:
                        reconstructed_history[user_id] = {
                            "username": voter_username,
                            "wins": 0,
                            "losses": 0,
                            "streak": 0,
                            "history": []
                        }
                    if user_id not in reconstructed_points:
                        reconstructed_points[user_id] = {
                            "username": voter_username,
                            "current_points": 0,
                            "points_history": [0]
                        }
                    
                    correct = (prediction == processed_winner)
                    result = "W" if correct else "L"
                    
                    if result == "W":
                        reconstructed_history[user_id]["wins"] += 1
                        reconstructed_points[user_id]["current_points"] += points_awarded
                    else:
                        reconstructed_history[user_id]["losses"] += 1
                        
                    reconstructed_history[user_id]["history"].append(result)

            # For all other registered users who didn't vote in this match, add "D"
            for user_id in reconstructed_history.keys():
                if user_id not in voted_user_ids:
                    reconstructed_history[user_id]["history"].append("D")

            # Append current points to points history for every user
            for user_id in reconstructed_points.keys():
                reconstructed_points[user_id]["points_history"].append(
                    reconstructed_points[user_id]["current_points"]
                )

            processed_count += 1

        # Finally, recalculate streaks and save history
        for user_id, udata in reconstructed_history.items():
            streak = 0
            for item in reversed(udata["history"]):
                if item == "W":
                    streak += 1
                else:
                    break
            udata["streak"] = streak

        save_json("prediction_history.json", reconstructed_history)
        save_json("points_history.json", reconstructed_points)

        await interaction.followup.send(
            f"Successfully reconstructed prediction histories from Discord messages!\n\n"
            f"✅ **Processed Matches:** {processed_count}\n"
            f"❌ **Failed Matches:** {failed_count}\n"
            f"👥 **Updated Players:** {len(reconstructed_history)}",
            ephemeral=True
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

async def setup(bot):
    await bot.add_cog(Predictions(bot))
