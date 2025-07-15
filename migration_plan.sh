#!/bin/bash

# Usage: ./migration_plan.sh

PID=$(pgrep -f "python.*migration_plan\.py$")
if [ -n "$PID" ]; then
    echo "ERROR: migration_plan.py is already running"
    exit 1
fi

PID=$(pgrep -f "python.*restart_plan\.py$")
if [ -n "$PID" ]; then
    echo "Killing restart_plan.py (PID $PID)..."
    kill "$PID"
fi
PID=$(pgrep -f ".*restart_plan\.sh$")
if [ -n "$PID" ]; then
    echo "Killing restart_plan.sh (PID $PID)..."
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

if ! python migration_plan.py; then
  echo "ERROR: Failed to start migration_plan.py"
  exit 1
fi
