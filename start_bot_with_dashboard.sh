#!/bin/bash
echo "Starting LeadGen Bot with Dashboard..."

# Activate virtual environment
source venv/bin/activate

# Install required packages if needed
pip install -r requirements.txt

# Start the bot with dashboard
python main.py --action dashboard &
DASHBOARD_PID=$!

# Start the scheduler in the background
python main.py --action schedule &
SCHEDULER_PID=$!

echo "Bot started with dashboard. You can access it at http://localhost:5000"
echo "Press Ctrl+C to stop all processes"

# Function to handle shutdown
function cleanup {
  echo "Stopping bot processes..."
  kill $DASHBOARD_PID
  kill $SCHEDULER_PID
  exit 0
}

# Register the cleanup function for SIGINT and SIGTERM
trap cleanup SIGINT SIGTERM

# Keep the script running until Ctrl+C
while true; do
  sleep 1
done 