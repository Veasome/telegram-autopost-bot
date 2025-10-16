# Telegram Auto Post Bot

## Overview
This is a Telegram bot for scheduling and auto-posting messages to a Telegram channel. The bot allows an admin user to schedule posts with flexible time formats, view scheduled posts, check statistics, and delete posts.

## Project Information
- **Language**: Python 3.11
- **Main File**: `bot.py`
- **Database**: SQLite (`posts.db`)
- **Framework**: pyTelegramBotAPI (version 4.19.2)

## Features
- **Schedule Posts**: Schedule posts with various time formats:
  - `+10` - in 10 minutes
  - `+1h` - in 1 hour  
  - `+1d` - in 1 day
  - `18:00` - today at 18:00
  - `14:30 25.12.2024` - specific date and time
- **View Posts**: List all scheduled posts
- **Statistics**: View total posts, scheduled posts, and published posts
- **Delete Posts**: Remove scheduled posts before they are published
- **Auto-Publishing**: Background scheduler checks every 30 seconds for posts to publish

## Environment Variables
The following secrets are required and configured in Replit Secrets:
- `BOT_TOKEN`: Telegram Bot API token from @BotFather
- `CHANNEL_ID`: Target Telegram channel ID (e.g., @channelname or -1001234567890)
- `ADMIN_ID`: Telegram user ID of the admin (numeric ID)

## Project Structure
```
.
├── bot.py              # Main bot application
├── requirements.txt    # Python dependencies
├── posts.db           # SQLite database (auto-created)
├── README.md          # Project documentation
├── Procfile           # Process configuration (for Railway deployment)
├── railway.toml       # Railway deployment config
└── .gitignore         # Git ignore rules
```

## How to Use
1. The bot is already running and configured
2. Open Telegram and find your bot
3. Send `/start` to begin
4. Use the menu buttons to:
   - 📅 Create new scheduled posts
   - 📋 View scheduled posts
   - 📊 Check statistics
   - ❌ Delete posts
   - ℹ️ Get help

## Recent Changes
- **2025-10-16**: Imported from GitHub and configured for Replit environment
- Installed Python 3.11 and required dependencies
- Configured environment secrets (BOT_TOKEN, CHANNEL_ID, ADMIN_ID)
- Set up workflow to run the bot continuously

## Technical Details
- **Access Control**: Only the admin user (ADMIN_ID) can interact with the bot
- **Scheduler**: Background thread checks for posts to publish every 30 seconds
- **Database**: SQLite with posts table tracking id, text, time, and status
- **Time Parsing**: Supports relative (+10m, +1h, +1d) and absolute time formats

## Deployment
The bot is currently running in the Replit environment with console output. The workflow "Telegram Bot" executes `python bot.py` and runs continuously.
