#!/bin/bash

# Usage: ./cache_metrics_kill.sh

PID=$(pgrep -f "python.*cache_metrics\.py$")
if [ -n "$PID" ]; then
    echo "Killing cache_metrics.py (PID $PID)..."
    kill "$PID"
    sleep 2
    if kill -0 "$PID" 2>/dev/null; then
        echo "Process $PID still running, forcing termination..."
        kill -9 "$PID"
    fi
fi
