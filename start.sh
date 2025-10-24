#!/bin/bash

# Change the active directory to the one where this script is located.
cd "$(dirname "$0")"

# Check if Python is installed and available in PATH.
if ! command -v python3 &> /dev/null; then
    echo "Python is not found."
    echo "Please install Python 3.10 or higher."
    echo "Download from: https://www.python.org/downloads/"
    echo "Or install via Homebrew: brew install python@3.10"
    exit 1
fi

echo "Python detected."

# Virtual environment directory name
VENV_DIR="venv"

# Check if virtual environment exists, create if not
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment."
        echo "Please make sure python3-venv is installed."
        exit 1
    fi
    echo "Virtual environment created successfully."
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Verify activation
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Failed to activate virtual environment."
    exit 1
fi

echo "Virtual environment activated: $VIRTUAL_ENV"

# Install dependencies from requirements.txt.
echo "Installing dependencies in virtual environment..."
pip install -r requirements.txt

# Start the application in the background.
echo "Starting the application..."
python app.py &
APP_PID=$!

# Wait for the server to start.
echo "Waiting for the server to start..."
sleep 5

# Open the application in the default browser.
echo "Opening the application in your browser at http://127.0.0.1:5000"
open http://127.0.0.1:5000

echo ""
echo "Application is running (PID: $APP_PID)"
echo "Virtual environment: $VIRTUAL_ENV"
echo "Press Ctrl+C to stop the server, or close this terminal window."
echo ""

# Wait for the background process to finish (keeps the script running).
wait $APP_PID

