#!/bin/bash
# MusicMaster setup script
# Usage: bash setup.sh check|install [--with-qobuz] [--with-tidal] [--force]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$SKILL_DIR/.venv"

check() {
    echo "PYTHON=$(command -v python3 > /dev/null 2>&1 && echo ok || echo missing)"

    if [ -d "$VENV_DIR" ]; then
        echo "VENV=ok"
        PYTHON="$VENV_DIR/bin/python"

        # Check core deps
        $PYTHON -c "import spotipy" 2>/dev/null && echo "SPOTIPY=ok" || echo "SPOTIPY=missing"
        $PYTHON -c "import pylast" 2>/dev/null && echo "PYLAST=ok" || echo "PYLAST=missing"
        $PYTHON -c "import requests" 2>/dev/null && echo "REQUESTS=ok" || echo "REQUESTS=missing"
        $PYTHON -c "import dotenv" 2>/dev/null && echo "DOTENV=ok" || echo "DOTENV=missing"

        # Check optional deps
        $PYTHON -c "import qobuz_dl" 2>/dev/null && echo "QOBUZ_DL=ok" || echo "QOBUZ_DL=not_installed"
        command -v "$VENV_DIR/bin/tiddl" > /dev/null 2>&1 && echo "TIDDL=ok" || echo "TIDDL=not_installed"

        # Check .env
        [ -f "$SKILL_DIR/.env" ] && echo "ENV_FILE=ok" || echo "ENV_FILE=missing"
    else
        echo "VENV=missing"
    fi
}

install() {
    local with_qobuz=false
    local with_tidal=false
    local force=false

    for arg in "$@"; do
        case $arg in
            --with-qobuz) with_qobuz=true ;;
            --with-tidal) with_tidal=true ;;
            --force) force=true ;;
        esac
    done

    # Create venv
    if [ -d "$VENV_DIR" ] && [ "$force" = true ]; then
        echo "Removing existing venv..." >&2
        rm -rf "$VENV_DIR"
    fi

    if [ ! -d "$VENV_DIR" ]; then
        echo "Creating virtual environment..." >&2
        python3 -m venv "$VENV_DIR"
    fi

    PIP="$VENV_DIR/bin/pip"

    # Core deps
    echo "Installing core dependencies..." >&2
    $PIP install -q spotipy pylast requests python-dotenv

    # Optional deps
    if [ "$with_qobuz" = true ]; then
        echo "Installing qobuz-dl..." >&2
        $PIP install -q qobuz-dl
    fi
    if [ "$with_tidal" = true ]; then
        echo "Installing tiddl..." >&2
        $PIP install -q tiddl
    fi

    # Create .env from example if not exists
    if [ ! -f "$SKILL_DIR/.env" ] && [ -f "$SKILL_DIR/.env.example" ]; then
        cp "$SKILL_DIR/.env.example" "$SKILL_DIR/.env"
        echo "Created .env from template — edit with your credentials" >&2
    fi

    echo "Setup complete!" >&2
}

preflight() {
    local ready=true

    # Dependencies
    local python_ok=false venv_ok=false
    command -v python3 > /dev/null 2>&1 && python_ok=true || ready=false
    [ -d "$VENV_DIR" ] && venv_ok=true || ready=false

    # Credentials
    local env_status="not_configured"
    [ -f "$SKILL_DIR/.env" ] && env_status="configured"

    # Optional backends
    local qobuz_status="not_installed" tidal_status="not_installed"
    if $venv_ok; then
        "$VENV_DIR/bin/python" -c "import qobuz_dl" 2>/dev/null && qobuz_status="ok"
        command -v "$VENV_DIR/bin/tiddl" > /dev/null 2>&1 && tidal_status="ok"
    fi

    cat <<EOF
{
    "ready": $ready,
    "dependencies": {
        "python3": {"status": "$(if $python_ok; then echo ok; else echo missing; fi)", "hint": "Install Python 3: brew install python3"},
        "venv": {"status": "$(if $venv_ok; then echo ok; else echo missing; fi)", "hint": "Run: bash scripts/setup.sh install"}
    },
    "credentials": {
        "env_file": {"status": "$env_status", "required": true, "hint": "Copy .env.example to .env and fill in credentials"}
    },
    "services": {
        "qobuz": {"status": "$qobuz_status", "hint": "Run: bash scripts/setup.sh install --with-qobuz"},
        "tidal": {"status": "$tidal_status", "hint": "Run: bash scripts/setup.sh install --with-tidal"}
    },
    "hint": "$(if $ready; then echo 'Core dependencies ready'; else echo 'Some dependencies missing, see details'; fi)"
}
EOF

    if ! $ready; then exit 1; fi
}

case "${1:-check}" in
    check) check ;;
    preflight) preflight ;;
    install) shift; install "$@" ;;
    *) echo "Usage: bash setup.sh check|preflight|install [--with-qobuz] [--with-tidal] [--force]" >&2; exit 1 ;;
esac
