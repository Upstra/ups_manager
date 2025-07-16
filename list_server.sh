#!/bin/bash

# Usage: ./list_server.sh --ip <IP> --user <USER> --password <PASS> [--port <PORT>]

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --ip) IP="$2"; shift ;;
        --user) USER="$2"; shift ;;
        --password) PASSWORD="$2"; shift ;;
        --port) PORT="$2"; shift ;;
        *) echo "Unknown parameter: $1" ; exit 1 ;;
    esac
    shift
done

if [[ -z "$IP" || -z "$USER" || -z "$PASSWORD" ]]; then
    echo "ERROR : Missing parameter"
    echo "Usage: $0 --ip <IP> --user <USER> --password <PASS> [--port <PORT>]"
    exit 1
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

CMD="python list_server.py --ip \"$IP\" --user \"$USER\" --password \"$PASSWORD\""
if [[ -n "$PORT" ]]; then
    CMD+=" --port \"$PORT\""
fi
eval "$CMD"
