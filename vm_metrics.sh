#!/bin/bash

# Usage: ./vm_metrics.sh --vm <VM> --datacenter <DATACENTER> --ip <IP> --user <USER> --password <PASS> [--port <PORT>]

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --vm) VM="$2"; shift ;;
        --datacenter) DATACENTER="$2"; shift ;;
        --ip) IP="$2"; shift ;;
        --user) USER="$2"; shift ;;
        --password) PASSWORD="$2"; shift ;;
        --port) PORT="$2"; shift ;;
        *) echo "Unknown parameter: $1" ; exit 1 ;;
    esac
    shift
done

if [[ -z "$VM" || -z "$DATACENTER" || -z "$IP" || -z "$USER" || -z "$PASSWORD" ]]; then
    echo "ERROR : Missing parameter"
    echo "Usage: $0 --vm <VM> --datacenter <DATACENTER> --ip <IP> --user <USER> --password <PASS> [--port <PORT>]"
    exit 1
fi

source .venv/bin/activate

CMD="python vm_metrics.py --vm \"$VM\" --datacenter \"$DATACENTER\" --ip \"$IP\" --user \"$USER\" --password \"$PASSWORD\""
if [[ -n "$PORT" ]]; then
    CMD+=" --port \"$PORT\""
fi
eval "$CMD"
