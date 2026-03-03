#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Create virtual environment if needed
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate and install dependencies
source .venv/bin/activate
pip install -q -r requirements.txt

# Check for API key
if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
    if [ -f .env ]; then
        export $(grep -v '^#' .env | xargs)
    fi
    if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
        echo "Error: ANTHROPIC_API_KEY not set. Copy .env.example to .env and add your key."
        exit 1
    fi
fi

# Run the pipeline
python main.py "$@"
