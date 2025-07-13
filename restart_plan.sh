#!/bin/bash

# Usage: ./restart_plan.sh

PID=$(pgrep -f "python.*migration_plan\.py$")
if [ -n "$PID" ]; then
    echo "Killing migration_plan.py (PID $PID)…"
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
