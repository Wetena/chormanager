#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

find_python() {
    for cmd in python3.13 python3.12 python3.11 python3.10 python3.9 python3 python; do
        if command -v "$cmd" &>/dev/null; then
            echo "$cmd"
            return 0
        fi
    done
    echo "ERROR: Kein Python3 interpreter gefunden." >&2
    echo "Installiere Python3: sudo apt install python3 python3-venv" >&2
    exit 1
}

PYTHON=$(find_python)
echo "Verwende: $PYTHON ($($PYTHON --version 2>&1))"

if [ ! -d ".venv" ]; then
    echo "Erstelle Virtual Environment..."
    "$PYTHON" -m venv .venv
fi

if [ ! -f ".venv/bin/pip" ]; then
    echo "Fehler: .venv/bin/pip nicht gefunden." >&2
    exit 1
fi

if ! "$PYTHON" -c "import PyQt6" 2>/dev/null; then
    echo "Installiere Dependencies..."
    .venv/bin/pip install -r requirements.txt
fi

source .venv/bin/activate
exec python -m chormanager "$@"
