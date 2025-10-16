# Telegram Auto Post Bot

## Overview
This is a Telegram bot for scheduling posts to a Telegram channel. The bot allows you to schedule posts with flexible time formats, view scheduled posts, check statistics, and delete posts.

## Current Status
✅ **Fully configured and running on Replit**

## Recent Changes (October 16, 2025)
- Installed Python 3.11 environment
- Installed dependencies: pyTelegramBotAPI==4.19.2, python-dotenv==1.0.0
- Configured environment secrets: BOT_TOKEN, CHANNEL_ID, ADMIN_ID
- Set up "Telegram Bot" workflow to run the bot automatically
- Bot is running successfully and waiting for Telegram commands

## Project Architecture

### Technology Stack
- **Language**: Python 3.11
- **Framework**: pyTelegramBotAPI (Telegram Bot API wrapper)
- **Database**: SQLite (posts.db)
- **Environment Management**: python-dotenv

### File Structure
```
.
├── bot.py              # Main bot application
├── requirements.txt    # Python dependencies
├── posts.db           # SQLite database (created at runtime)
├── .env               # Environment variables (gitignored)
├── .gitignore         # Git ignore rules
├── Procfile           # Railway deployment config (not used in Replit)
├── railway.toml       # Railway config (not used in Replit)
└── README.md          # Project documentation
```

### Key Features
1. **Schedule Posts**: Flexible time formats
   - Relative: `+10` (10 minutes), `+1h` (1 hour), `+1d` (1 day)
   - Today: `18:00` (today at 18:00)
   - Specific: `14:30 25.12.2024`

2. **Post Management**: View scheduled posts, check statistics, delete posts
3. **Background Scheduler**: Checks every 30 seconds for posts to publish
4. **Admin Only**: Bot only responds to the configured ADMIN_ID

### Database Schema
```sql
posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  text TEXT NOT NULL,
  time DATETIME NOT NULL,
  status TEXT DEFAULT 'scheduled'  -- 'scheduled' or 'sent'
)
```

## Environment Variables
- `BOT_TOKEN`: Telegram Bot API token from @BotFather
- `CHANNEL_ID`: Target channel ID (e.g., @severitynotfound)
- `ADMIN_ID`: Telegram user ID of the admin

## How to Use
1. Open Telegram and find your bot
2. Send `/start` to begin
3. Use the menu buttons to schedule posts, view posts, or check statistics

## Deployment
The bot runs continuously in the Replit environment via the "Telegram Bot" workflow configured to execute `python bot.py`.
