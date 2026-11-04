#!/bin/bash

# Usage: ./ups_battery.sh --ip <IP> [--format minutes|json] [--source auto|snmp|nut|http] [--ups-name <NAME>] [--community <COMMUNITY>]

if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate || {
        echo "ERROR: Failed to activate virtual environment" >&2
        exit 1
    }
fi

PYTHON_BIN=python3
if [ -n "$VIRTUAL_ENV" ]; then
    PYTHON_BIN=python
fi

"$PYTHON_BIN" ups_battery.py "$@"
