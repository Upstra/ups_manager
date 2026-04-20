#!/bin/bash
set -euo pipefail

# Usage: ./ups_battery.sh --ip <IP>

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --ip) IP="$2"; shift ;;
        *) echo "Unknown parameter: $1" ; exit 1 ;;
    esac
    shift
done

if [[ -z "$IP" ]]; then
    echo "ERROR : Missing parameter"
    echo "Usage: $0 --ip <IP>"
    exit 1
fi

if [[ "$IP" == http://* ]] || [[ "$IP" == https://* ]]; then
    # Mode démo : endpoint HTTP mock_ups — runtime_remaining en secondes, converti en minutes
    curl -sf "${IP}/battery" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['runtime_remaining']//60)"
else
    # Mode production : UPS réel via SNMP v1
    VALUE=$(/bin/snmpget -O T -m ALL -c public -v1 "$IP" UPS-MIB::upsEstimatedMinutesRemaining.0 | awk -F': ' '{print $2}' | awk '{print $1}')
    echo "$VALUE"
fi
