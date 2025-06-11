#!/bin/bash

# Step 1: Start ngrok in the background on port 8443
source /home/ubuntu/polybot/.env


export TELEGRAM_BOT_TOKEN
export YOLO_URL
export BOT_APP_URL
export REGION
export BUCKET_NAME
export POLYBOT_ENV
# Step 4: Run the polybot app

echo "Starting polybot app..."
exec /home/ubuntu/polybot/.venv/bin/python -m polybot.app
