#!/bin/bash

# Step 1: Start ngrok in the background on port 8443
source /home/ubuntu/polybot/.env

echo "Starting ngrok on port 8443..."

curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
  | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
  && echo "deb https://ngrok-agent.s3.amazonaws.com buster main" \
  | sudo tee /etc/apt/sources.list.d/ngrok.list \
  && sudo apt update \
  && sudo apt install ngrok

ngrok config add-authtoken "$NGROK_AUTHTOKEN"
ngrok http 8443  > /dev/null &


# Wait a few seconds for ngrok to initialize
sleep 5

# Step 2: Get the public HTTPS URL from ngrok API
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o 'https://[a-zA-Z0-9.-]*ngrok-free.app' | head -n 1)
echo "Ngrok URL: $NGROK_URL"

# Step 3: Export environment variables

export TELEGRAM_BOT_TOKEN
export YOLO_URL
export BOT_APP_URL=$NGROK_URL
export REGION
export BUCKET_NAME

# Step 4: Run the polybot app

echo "Starting polybot app..."
exec /home/ubuntu/polybot/.venv/bin/python -m polybot.app
