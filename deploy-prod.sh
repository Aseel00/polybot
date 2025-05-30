#!/bin/bash

set -e  # Exit on any error

PROJECT_DIR="/home/ubuntu/polybot"
VENV_DIR="$PROJECT_DIR/.venv"
SERVICE_NAME="polybot-prod.service"

echo "🐍 Detecting Python version..."
PYTHON_VERSION=$(python3 -c "import sys; print(f'python{sys.version_info.major}.{sys.version_info.minor}')")
VENV_PACKAGE="${PYTHON_VERSION}-venv"

echo "🧪 Ensuring $VENV_PACKAGE is installed..."
sudo apt-get update
sudo apt-get install -y "$VENV_PACKAGE"

echo "📁 Navigating to project directory: $PROJECT_DIR"
cd "$PROJECT_DIR"


# Step 1: Set up virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
  echo "🐍 Creating virtual environment..."
  python3 -m venv "$VENV_DIR"

  if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "❌ Failed to create virtual environment. Exiting."
    exit 1
  fi
else
  echo "📦 Existing virtual environment found, reusing it."
fi



echo "🔌 Activating virtual environment..."
source "$VENV_DIR/bin/activate"


# Step 3: Check if dependencies are installed (change PACKAGE_TO_CHECK if needed)
PACKAGE_TO_CHECK="loguru"  # Example core dependency
if ! pip show "$PACKAGE_TO_CHECK" > /dev/null 2>&1; then
  echo "📦 Installing Python dependencies..."
  pip install --upgrade pip
  pip install -r polybot/requirements.txt
else
  echo "✅ Dependencies already installed, skipping pip install."
fi

sudo apt install python3-pip
pip install boto3

# Step 4: Copy the systemd service file
echo "🛠️  Setting up systemd service..."
sudo cp "$PROJECT_DIR/$SERVICE_NAME" /etc/systemd/system/$SERVICE_NAME

# Step 5: Reload systemd and restart the service
echo "🔄 Reloading systemd and restarting $SERVICE_NAME..."
sudo systemctl daemon-reload
sudo systemctl restart $SERVICE_NAME
sudo systemctl enable $SERVICE_NAME

# Step 6: Check service status
echo "🔍 Checking $SERVICE_NAME status..."
if systemctl is-active --quiet $SERVICE_NAME; then
  echo "✅ $SERVICE_NAME is running."
else
  echo "❌ $SERVICE_NAME failed to start."
  sudo systemctl status $SERVICE_NAME --no-pager
  exit 1
fi
