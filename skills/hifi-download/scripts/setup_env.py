#!/usr/bin/env python3
"""
Install MusicMaster dependencies.

Usage:
    python scripts/setup_env.py [--with-qobuz] [--with-tidal]

Creates virtual environment and installs required packages.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def get_skill_dir():
    return Path(__file__).parent.parent.absolute()


def get_venv_dir():
    return get_skill_dir() / ".venv"


def main():
    parser = argparse.ArgumentParser(description="Install MusicMaster dependencies")
    parser.add_argument("--with-qobuz", action="store_true", help="Install qobuz-dl")
    parser.add_argument("--with-tidal", action="store_true", help="Install tidal-dl")
    parser.add_argument("--force", action="store_true", help="Recreate venv if exists")
    args = parser.parse_args()

    venv_dir = get_venv_dir()
    skill_dir = get_skill_dir()

    # Handle existing venv
    if venv_dir.exists():
        if args.force:
            print(f"Removing existing venv: {venv_dir}")
            import shutil
            shutil.rmtree(venv_dir)
        else:
            print(f"Virtual environment already exists: {venv_dir}")
            print("Use --force to recreate")

    # Create venv if needed
    if not venv_dir.exists():
        print(f"Creating virtual environment: {venv_dir}")
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)

    # Get pip path
    pip_path = venv_dir / "bin" / "pip"
    if sys.platform == "win32":
        pip_path = venv_dir / "Scripts" / "pip.exe"

    # Install core dependencies
    core_deps = ["spotipy", "pylast", "requests", "python-dotenv"]
    print(f"Installing core dependencies: {', '.join(core_deps)}")
    subprocess.run([str(pip_path), "install", "-q"] + core_deps, check=True)

    # Optional: Qobuz
    if args.with_qobuz:
        print("Installing qobuz-dl...")
        subprocess.run([str(pip_path), "install", "-q", "qobuz-dl"], check=True)

    # Optional: TIDAL (uses tiddl - modern alternative to tidal-dl)
    if args.with_tidal:
        print("Installing tiddl...")
        subprocess.run([str(pip_path), "install", "-q", "tiddl"], check=True)

    # Create run helper scripts
    run_sh = skill_dir / "run.sh"
    with open(run_sh, 'w') as f:
        f.write(f'''#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/.venv/bin/activate"
cd "$SCRIPT_DIR"
python "scripts/$1.py" "${{@:2}}"
''')
    run_sh.chmod(0o755)

    run_bat = skill_dir / "run.bat"
    with open(run_bat, 'w') as f:
        f.write('''@echo off
set SCRIPT_DIR=%~dp0
call "%SCRIPT_DIR%.venv\\Scripts\\activate.bat"
cd /d "%SCRIPT_DIR%"
python "scripts\\%1.py" %*
''')

    print()
    print("Environment setup complete!")
    print(f"  Virtual environment: {venv_dir}")
    print(f"  Run helper: {run_sh}")
    print()
    print("Next step: Configure credentials with setup_config.py")


if __name__ == "__main__":
    main()
