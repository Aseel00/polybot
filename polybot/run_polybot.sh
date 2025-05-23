#!/bin/bash

# Step 1: Start ngrok in the background on port 8443
echo "Starting ngrok on port 8443..."
export NGROK_AUTHTOKEN=$NGROK_AUTHTOKEN
ngrok http 8443 --authtoken=$NGROK_AUTHTOKEN  > /dev/null &

# Wait a few seconds for ngrok to initialize
sleep 5

# Step 2: Get the public HTTPS URL from ngrok API
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o 'https://[a-zA-Z0-9.-]*ngrok-free.app' | head -n 1)
echo "Ngrok URL: $NGROK_URL"

# Step 3: Export environment variables
export TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN
export YOLO_URL=$YOLO_URL
export BOT_APP_URL=$NGROK_URL

# Step 4: Run the polybot app
echo "Starting polybot app..."
exec /home/ubuntu/polybot/.venv/bin/python -m polybot.app
