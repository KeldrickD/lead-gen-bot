#!/bin/bash

echo "==================================="
echo "Lead Generation Bot"
echo "==================================="

if [ -z "$1" ]; then
    echo "Running in schedule mode..."
    python main.py --action schedule
    exit 0
fi

if [ "$1" = "collect" ]; then
    echo "Running lead collection..."
    python main.py --action collect --platform "$2" --max_leads "$3"
    exit 0
fi

if [ "$1" = "message" ]; then
    echo "Sending initial messages..."
    python main.py --action message --platform "$2" --max_leads "$3" --max_dms "$4"
    exit 0
fi

if [ "$1" = "follow_up" ]; then
    echo "Sending follow-up messages..."
    python main.py --action follow_up --platform "$2"
    exit 0
fi

if [ "$1" = "run_all" ]; then
    echo "Running complete workflow..."
    python main.py --action run_all
    exit 0
fi

echo "Unknown command: $1"
echo "Available commands:"
echo "  ./run.sh                - Run in schedule mode"
echo "  ./run.sh collect [platform] [max_leads] - Collect leads"
echo "  ./run.sh message [platform] [max_leads] [max_dms] - Send initial messages"
echo "  ./run.sh follow_up [platform] - Send follow-up messages"
echo "  ./run.sh run_all       - Run complete workflow" 