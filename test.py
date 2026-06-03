import requests

API_KEY = "3f313b060eaf44f39bb3ac2cfbf7414d"

headers = {
    "X-Auth-Token": API_KEY
}

response = requests.get(
    "https://api.football-data.org/v4/competitions/CL/matches",
    headers=headers
)

data = response.json()

for match in data["matches"]:

    if match["status"] == "FINISHED":

        print("=" * 50)

        print(
            match["homeTeam"]["name"],
            "vs",
            match["awayTeam"]["name"]
        )

        print(
            "Status:",
            match["status"]
        )

        print(
            "Winner:",
            match["score"]["winner"]
        )

        print(
            "Duration:",
            match["score"]["duration"]
        )

        print(
            "Full Time:",
            match["score"]["fullTime"]
        )

        break