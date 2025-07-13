#!/bin/bash

# Usage: ./migration_plan.sh

if [ ! -f .venv/bin/activate ]; then
    echo "ERROR: Virtual environment not found at .venv/bin/activate"
    exit 1
fi
source .venv/bin/activate
if [ -z "$VIRTUAL_ENV" ]; then
    echo "ERROR: Failed to activate virtual environment"
    exit 1
fi

if ! python migration_plan.py; then
  echo "ERROR: Failed to start migration_plan.py"
  exit 1
fi
