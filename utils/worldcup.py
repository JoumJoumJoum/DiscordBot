import aiohttp
from utils.storage import save_json
from utils.config import FOOTBALL_DATA_API_KEY
from utils.storage import (
    load_json,
    save_json
)



BASE_URL = "https://api.football-data.org/v4"


async def fetch_world_cup_matches():
    headers = {
        "X-Auth-Token": FOOTBALL_DATA_API_KEY
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{BASE_URL}/competitions/WC/matches",
            headers=headers
        ) as response:

            data = await response.json()

            return data.get("matches", [])

async def sync_world_cup_matches():

    matches = await fetch_world_cup_matches()

    existing = load_json(
        "worldcup_matches.json"
    )

    for match in matches:

        match_id = str(match["id"])

        if match_id not in existing:

            existing[match_id] = {
                "home": match["homeTeam"]["name"],
                "away": match["awayTeam"]["name"],
                "kickoff": match["utcDate"],
                "stage": match["stage"],
                "status": match["status"],
                "poll_created": False,
                "poll_closed": False,
                "result_processed": False,
                "message_id": None
            }

        else:

            existing[match_id]["home"] = (
                match["homeTeam"]["name"]
            )

            existing[match_id]["away"] = (
                match["awayTeam"]["name"]
            )

            existing[match_id]["kickoff"] = (
                match["utcDate"]
            )

            existing[match_id]["status"] = (
                match["status"]
            )

            existing[match_id]["stage"] = (
                match["stage"]
            )

    save_json(
        "worldcup_matches.json",
        existing
    )

    return len(matches)


async def import_world_cup_matches():
    matches = await fetch_world_cup_matches()

    output = {}

    for match in matches:

        match_id = str(match["id"])

        output[match_id] = {
            "home": match["homeTeam"]["name"],
            "away": match["awayTeam"]["name"],
            "kickoff": match["utcDate"],
            "stage": match["stage"],
            "status": match["status"],
            "poll_created": False,
            "poll_closed": False,
            "result_processed": False,
            "message_id": None
        }

    save_json(
        "worldcup_matches.json",
        output
    )

    return len(output)