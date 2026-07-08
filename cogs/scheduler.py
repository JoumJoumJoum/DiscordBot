from discord.ext import commands, tasks
from datetime import datetime, timedelta, timezone
import asyncio
from utils.storage import load_json, save_json

def update_all_prediction_histories(
    match_votes,
    correct_prediction,
    leaderboard
):
    history = load_json("prediction_history.json")

    registered_users = {}
    for uid, udata in leaderboard.items():
        registered_users[uid] = udata["username"]
    for uid, udata in history.items():
        if uid not in registered_users:
            registered_users[uid] = udata["username"]

    for user_id, username in registered_users.items():
        if user_id not in history:
            history[user_id] = {
                "username": username,
                "wins": 0,
                "losses": 0,
                "streak": 0,
                "history": []
            }

        if user_id in match_votes:
            correct = (
                match_votes[user_id]["prediction"]
                == correct_prediction
            )
            result = "W" if correct else "L"
        else:
            result = "D"

        if result == "W":
            history[user_id]["wins"] += 1
        elif result == "L":
            history[user_id]["losses"] += 1

        history[user_id]["history"].append(result)

        streak = 0
        for item in reversed(history[user_id]["history"]):
            if item == "W":
                streak += 1
            else:
                break
        history[user_id]["streak"] = streak
        history[user_id]["username"] = username

    save_json("prediction_history.json", history)

from utils.worldcup import (
    fetch_world_cup_matches
)

from utils.config import (
    PREDICTION_CHANNEL_ID
)

from utils.worldcup import (
    sync_world_cup_matches
)


class Scheduler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.match_scheduler.start()
        self.result_checker.start()
        self.fixture_sync.start()

    def cog_unload(self):
        self.match_scheduler.cancel()
        self.fixture_sync.cancel()
        self.result_checker.cancel()


    @tasks.loop(hours=24)
    async def fixture_sync(self):

        print("FIXTURE SYNC STARTED")

        count = await sync_world_cup_matches()

        print(
            f"Synced {count} World Cup fixtures"
        )

    @tasks.loop(minutes=15) #fix
    async def result_checker(self):

        matches = load_json(
            "worldcup_matches.json"
        )

        votes = load_json(
            "votes.json"
        )

        leaderboard = load_json(
            "leaderboard.json"
        )

        fixtures = await fetch_world_cup_matches()
        changes_made = False

        for fixture in fixtures:

            print(
                fixture["id"],
                fixture["status"]
            )

            match_id = str(
                fixture["id"]
            )

            if match_id not in matches:
                continue

            if matches[match_id]["result_processed"]:
                continue

            if fixture["status"] != "FINISHED":
                continue

            match = matches[match_id]
            if not match["poll_closed"]:
                continue

            winner = fixture["score"]["winner"]

            if winner == "HOME_TEAM":
                correct_prediction = match["home"]

                print(
                    "CORRECT PREDICTION:",
                    correct_prediction
                )

            elif winner == "AWAY_TEAM":
                correct_prediction = match["away"]

            elif winner == "DRAW":
                correct_prediction = "Draw"

            else:
                continue

            message_id = match["message_id"]

            if message_id not in votes:


                match["result_processed"] = True
                changes_made = True

                continue

            match_votes = votes[message_id]
            winners = []

            losing_votes = 0

            for vote_data in match_votes.values():

                if (
                    vote_data["prediction"]
                    != correct_prediction
                ):
                    losing_votes += 1

            points_awarded = max(
                1,
                losing_votes
            )

            update_all_prediction_histories(
                match_votes,
                correct_prediction,
                leaderboard
            )

            for user_id, vote_data in match_votes.items():

                correct = (
                    vote_data["prediction"]
                    == correct_prediction
                )

                if correct:

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

                print(
                    vote_data["prediction"],
                    correct_prediction
                )


            print(
                f"Processed "
                f"{match['home']} vs "
                f"{match['away']}"
            )
            channel = self.bot.get_channel(
                PREDICTION_CHANNEL_ID
            )

            message = await channel.fetch_message(
                int(match["message_id"])
            )

            embed = message.embeds[0]

            embed.add_field(
                name="🏆 Result",
                value=correct_prediction,
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
                embed=embed
            )

            await channel.send(
                f"🏆 **{match['home']} vs {match['away']}**\n"
                f"Winner: **{correct_prediction}**\n"
                f"Points Awarded: "
                f"**{points_awarded}**\n"
                f"Correct Predictions: "
                f"{', '.join(winners) if winners else 'None'}"
            )
            
            if message_id in votes:

                del votes[message_id]

                save_json(
                    "votes.json",
                    votes
                )
            match["result_processed"] = True
            changes_made = True


        if changes_made:
            save_json(
                "leaderboard.json",
                leaderboard
            )

            save_json(
                "worldcup_matches.json",
                matches
            )

    @result_checker.before_loop
    async def before_result_checker(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=10) ##change this
    async def match_scheduler(self):

        print("MATCH SCHEDULER STARTED")


        matches = load_json(
            "worldcup_matches.json"
        )


        now = datetime.now(timezone.utc)

        for match_id, match in matches.items():
            try:
                kickoff = datetime.fromisoformat(
                    match["kickoff"].replace(
                        "Z",
                        "+00:00"
                    )
                )

                hours_until = (
                    kickoff - now
                ).total_seconds() / 3600


                print(
                    f"{match_id} | "
                    f"{match['home']} vs {match['away']} | "
                    f"{hours_until:.2f}h | "
                    f"created={match['poll_created']} | "
                    f"closed={match['poll_closed']}"
                )

                # CREATE POLL


                if (
                    not match["poll_created"]
                    and 0 < hours_until <= 48
                ):
                    if match["home"] is None or match["away"] is None:
                        print(
                            f"Skipping {match_id}: teams not decided yet."
                        )
                        continue

                    prediction_cog = self.bot.get_cog(
                        "Predictions"
                    )

                    print(
                        f"Creating poll for "
                        f"{match['home']} vs {match['away']}"
                    )

                    message = await prediction_cog.create_match_poll(
                        match
                    )

                    print(
                        f"Poll created: {message.id}"
                    )

                    match["poll_created"] = True

                    match["message_id"] = str(message.id)

                    save_json(
                        "worldcup_matches.json",
                        matches
                    )

                # CLOSE POLL

                if (
                    match["poll_created"]
                    and not match["poll_closed"]
                ):

                    close_time = kickoff - timedelta(hours=1.5)

                    if now >= close_time:

                        channel = self.bot.get_channel(
                            PREDICTION_CHANNEL_ID
                        )

                        message = await channel.fetch_message(
                            int(match["message_id"])
                        )

                        prediction_cog = self.bot.get_cog(
                            "Predictions"
                        )

                        allow_draw = (
                            match["stage"] == "GROUP_STAGE"
                        )

                        view = prediction_cog.create_prediction_view(
                            match["home"],
                            match["away"],
                            allow_draw
                        )

                        view.disable_all_buttons()

                        embed = message.embeds[0]

                        embed.description += (
                            "\n\nVoting Closed"
                        )

                        await message.edit(
                            embed=embed,
                            view=view
                        )

                        match["poll_closed"] = True

                        save_json(
                            "worldcup_matches.json",
                            matches
                        )

            except Exception:
                import traceback
                traceback.print_exc()

            print("MATCH SCHEDULER FINISHED")


    @match_scheduler.before_loop
    async def before_scheduler(self):
        await self.bot.wait_until_ready()

    @fixture_sync.before_loop
    async def before_fixture_sync(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(60)


async def setup(bot):
    await bot.add_cog(
        Scheduler(bot)
    )