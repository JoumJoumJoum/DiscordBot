# DiscordBot

A simple discord bot I made for the Fifa World Cup to bet among my friends on matches.

## Setup

### Requirements
- Python 3.8+
- discord.py 2.7.1+

### Installation

1. Clone the repository
   ```bash
   git clone https://github.com/JoumJoumJoum/DiscordBot.git
   cd DiscordBot
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory with:
   ```
   FOOTBALL_DATA_API_KEY=your_football_data_api_key
   OWNER_ID=your_discord_user_id
   PREDICTION_CHANNEL_ID=your_predictions_channel_id
   PREDICTION_ROLE_ID=your_predictions_role_id
   DISCORD_TOKEN=your_discord_bot_token
   CONFESSIONS_CHANNEL_ID=your_confessions_channel_id
   ```

4. Run the bot
   ```bash
   python bot.py
   ```

## Environment Variables

- **FOOTBALL_DATA_API_KEY**: API key from [football-data.org](https://www.football-data.org/)
- **OWNER_ID**: Your Discord user ID
- **PREDICTION_CHANNEL_ID**: Discord channel ID for predictions
- **PREDICTION_ROLE_ID**: Discord role ID for prediction permissions
- **DISCORD_TOKEN**: Your Discord bot token from the [Developer Portal](https://discord.com/developers/applications)
- **CONFESSIONS_CHANNEL_ID**: Discord channel ID for confessions
