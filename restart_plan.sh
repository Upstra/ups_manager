#!/bin/bash

# Usage: ./restart_plan.sh

PID=$(ps -ef | grep migration_plan.py | grep -v grep | awk '{print $2}')
if [ -n "$PID" ]; then
    echo "Killing migration_plan.py (PID $PID)…"
    kill "$PID"
fi

if [ ! -f .venv/bin/activate ]; then
    echo "ERROR: Virtual environment not found at .venv/bin/activate"
    exit 1
fi
if ! source .venv/bin/activate; then
    echo "ERROR: Failed to activate virtual environment"
    exit 1
fi

python restart_plan.py
