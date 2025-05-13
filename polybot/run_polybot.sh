#!/bin/bash

# Step 1: Start ngrok in the background on port 8443
echo "Starting ngrok on port 8443..."
ngrok http --url=prepared-ruling-gnat.ngrok-free.app 8443 > /dev/null &

# Wait a few seconds for ngrok to initialize
sleep 5

# Step 2: Get the public HTTPS URL from ngrok API
NGROK_URL="https://prepared-ruling-gnat.ngrok-free.app"
echo "Ngrok URL: $NGROK_URL"

# Step 3: Export environment variables
export TELEGRAM_BOT_TOKEN="8184702002:AAHVhaKcDiRq0PD5MiXhOx6JNZScbjT2dFw"
export YOLO_URL="10.0.1.29"
export BOT_APP_URL=$NGROK_URL

# Step 4: Run the polybot app
echo "Starting polybot app..."
python3 -m polybot.app
