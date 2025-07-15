#!/bin/bash

# Usage: ./restart_plan.sh

PID=$(pgrep -f "python.*restart_plan\.py$")
if [ -n "$PID" ]; then
    echo "restart_plan.py is already running"
    exit 1
fi

CONFIG_FILE="plans/migration.yml"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: Migration plan YAML file ($CONFIG_FILE) not found"
    exit 1
fi

RESTART_GRACE=$(grep -A1 '^ups:' "$CONFIG_FILE" | grep 'restartGrace:' | awk '{print $2}')
if [ -z "$RESTART_GRACE" ]; then
    echo "ERROR: Could not find ups.restartGrace value in $CONFIG_FILE"
    exit 1
fi

echo "Waiting $RESTART_GRACE seconds before restarting..."
sleep "$RESTART_GRACE"

PID=$(pgrep -f "python.*migration_plan\.py$")
if [ -n "$PID" ]; then
    echo "Killing migration_plan.py (PID $PID)..."
    kill "$PID"
fi

if [ ! -f .venv/bin/activate ]; then
    echo "ERROR: Virtual environment not found at .venv/bin/activate"
    exit 1
fi
source .venv/bin/activate || {
    echo "ERROR: Failed to activate virtual environment"
    exit 1
}
if [[ "$VIRTUAL_ENV" != "$(pwd)/.venv"* ]]; then
    echo "ERROR: Activated an unexpected virtual environment ($VIRTUAL_ENV)"
    exit 1
fi

if ! python restart_plan.py; then
  echo "ERROR: Failed to start restart_plan.py"
  exit 1
fi
