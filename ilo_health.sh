#!/bin/bash

# Usage: ./ilo_health.sh --ip <IP> --user <USER> --password <PASS> [--timeout 15] [--verify-ssl]

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

python ilo_health.py "$@"
