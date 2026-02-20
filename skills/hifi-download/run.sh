#!/bin/bash
# MusicMaster script runner — activates venv and runs the specified script
# Usage: bash run.sh <script_name> [args...]
# Example: bash run.sh status --json

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
    echo '{"ok": false, "error": "Virtual environment not found. Run: bash scripts/setup.sh install", "code": "venv_missing"}' >&2
    exit 1
fi

source "$VENV_DIR/bin/activate"
cd "$SCRIPT_DIR"
python "scripts/$1.py" "${@:2}"
