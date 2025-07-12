#!/bin/bash

# Usage: ./server_start.sh --ip <IP> --user <USER> --password <PASS>

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --ip) IP="$2"; shift ;;
        --user) USER="$2"; shift ;;
        --password) PASSWORD="$2"; shift ;;
        *) echo "Unknown parameter: $1" ; exit 1 ;;
    esac
    shift
done

if [[ -z "$IP" || -z "$USER" || -z "$PASSWORD" ]]; then
    echo "ERROR : Missing parameter"
    echo "Usage: $0 --ip <IP> --user <USER> --password <PASS>"
    exit 1
fi

if [ ! -f .venv/bin/activate ]; then
    echo "ERROR: Virtual environment not found at .venv/bin/activate"
    exit 1
fi
if ! source .venv/bin/activate; then
    echo "ERROR: Failed to activate virtual environment"
    exit 1
fi

python server_start.py --ip "$IP" --user "$USER" --password "$PASSWORD"
