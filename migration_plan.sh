#!/bin/bash

# Usage: ./migration_plan.sh

if [ ! -f .venv/bin/activate ]; then
    echo "ERROR: Virtual environment not found at .venv/bin/activate"
    exit 1
fi
if ! source .venv/bin/activate; then
    echo "ERROR: Failed to activate virtual environment"
    exit 1
fi

python migration_plan.py
