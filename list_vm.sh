#!/bin/bash

# Usage: ./list_vm.sh --ip <IP> --user <USER> --password <PASS> [--port <PORT>]

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

if ! docker ps --format '{{.Names}}' | grep -q '^python_app$'; then
    docker-compose up --build -d
    sleep 3
fi

CMD="docker exec -i python_app python vm.py --ip \"$IP\" --user \"$USER\" --password \"$PASSWORD\""
if [[ -n "$PORT" ]]; then
    CMD+=" --port \"$PORT\""
fi

echo ">$CMD"
eval "$CMD"
