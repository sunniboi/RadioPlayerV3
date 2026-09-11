#!/bin/bash
# Jarvis Whisperer starten
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d "venv" ]; then
    echo "Erst install.sh ausführen!"
    exit 1
fi

source venv/bin/activate
python main.py "$@"
