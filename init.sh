#!/bin/bash

set -e

REQ_FILE="requirements.txt"
if [[ ! -f "$REQ_FILE" ]]; then
    echo "ERROR : file $REQ_FILE not found"
    exit 1
fi

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r "$REQ_FILE"
