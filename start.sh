#!/bin/sh
# =============================================================
# Anime RPG Bot — Startup Script
# =============================================================

cd "$(dirname "$0")" || exit 1

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ No .env file found."
    echo "Create one by running: cp .env.example .env"
    echo "Then edit it with: nano .env"
    exit 1
fi

# Load environment variables from .env
set -a
. ./.env
set +a

# Verify BOT_TOKEN is set
if [ -z "$BOT_TOKEN" ]; then
    echo "❌ BOT_TOKEN is not set in .env"
    exit 1
fi

# Check for required Python files
MISSING=""
for f in bot.py game_data.py db.py combat.py clans.py; do
    [ ! -f "$f" ] && MISSING="$MISSING $f"
done

if [ -n "$MISSING" ]; then
    echo "❌ Missing required files:$MISSING"
    exit 1
fi

# Start the bot
echo "🚀 Starting Anime RPG Bot..."
python bot.py
