#!/usr/bin/env python3
"""Verify MusicMaster configuration and test connections."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.config import Config


def check_spotify(config):
    """Check Spotify configuration."""
    if not config.spotify.is_configured():
        return False, "Not configured (missing SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET)"

    try:
        import spotipy
        from spotipy.oauth2 import SpotifyClientCredentials

        auth = SpotifyClientCredentials(
            client_id=config.spotify.client_id,
            client_secret=config.spotify.client_secret
        )
        sp = spotipy.Spotify(auth_manager=auth)
        # Test with a simple search
        sp.search("test", limit=1)
        return True, "Connected"
    except Exception as e:
        return False, f"Connection failed: {e}"


def check_lastfm(config):
    """Check Last.fm configuration."""
    if not config.lastfm.is_configured():
        return False, "Not configured (missing LASTFM_API_KEY)"

    try:
        import requests
        resp = requests.get(
            "http://ws.audioscrobbler.com/2.0/",
            params={
                "method": "artist.getSimilar",
                "artist": "Radiohead",
                "limit": 1,
                "api_key": config.lastfm.api_key,
                "format": "json"
            },
            timeout=10
        )
        data = resp.json()
        if "error" in data:
            return False, f"API error: {data.get('message')}"
        return True, "Connected"
    except Exception as e:
        return False, f"Connection failed: {e}"


def check_qobuz(config):
    """Check Qobuz configuration."""
    if not config.qobuz.is_configured():
        return False, "Not configured (missing QOBUZ_EMAIL or QOBUZ_PASSWORD)"

    try:
        from qobuz_dl.core import QobuzDL
        qobuz = QobuzDL(
            directory=config.qobuz.download_path,
            quality=config.qobuz.quality
        )
        qobuz.get_tokens()
        qobuz.initialize_client(
            config.qobuz.email,
            config.qobuz.password,
            qobuz.app_id,
            qobuz.secrets
        )
        return True, f"Connected (quality: {config.qobuz.quality})"
    except ImportError:
        return False, "qobuz-dl not installed (pip install qobuz-dl)"
    except Exception as e:
        return False, f"Login failed: {e}"


def check_tidal(config):
    """Check TIDAL configuration."""
    try:
        import json
        import time
        tiddl_config_path = Path.home() / "tiddl.json"
        if not tiddl_config_path.exists():
            return False, "Not configured. Run: tiddl auth login"

        with open(tiddl_config_path) as f:
            tiddl_config = json.load(f)

        auth = tiddl_config.get("auth", {})
        if not auth.get("token") or not auth.get("user_id"):
            return False, "No valid token found. Run: tiddl auth login"

        expires = auth.get("expires", 0)
        if expires and time.time() > expires:
            # Attempt auto-refresh before reporting failure
            import subprocess
            venv_bin = Path(__file__).parent.parent / ".venv" / "bin"
            tiddl_path = venv_bin / "tiddl"
            if tiddl_path.exists():
                result = subprocess.run(
                    [str(tiddl_path), "auth", "refresh"],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    # Re-read config after refresh
                    with open(tiddl_config_path) as f2:
                        tiddl_config = json.load(f2)
                    auth = tiddl_config.get("auth", {})
                    return True, f"Token refreshed. Connected as user {auth.get('user_id')} (quality: {config.tidal.quality})"
            return False, "Token expired and refresh failed. Run: tiddl auth login"

        return True, f"Connected as user {auth.get('user_id')} (quality: {config.tidal.quality})"
    except Exception as e:
        return False, f"Error: {e}"


def main():
    print("MusicMaster Setup Verification\n")
    print("=" * 50)

    config = Config.load()

    # Check each service
    services = [
        ("Spotify", check_spotify),
        ("Last.fm", check_lastfm),
        ("Qobuz", check_qobuz),
        ("TIDAL", check_tidal),
    ]

    all_ok = True
    discovery_ok = False
    download_ok = False

    for name, checker in services:
        ok, message = checker(config)
        status = "OK" if ok else "FAIL"
        icon = "+" if ok else "-"
        print(f"[{icon}] {name}: {status}")
        print(f"    {message}")

        if not ok:
            all_ok = False
        if ok and name in ["Spotify", "Last.fm"]:
            discovery_ok = True
        if ok and name in ["Qobuz", "TIDAL"]:
            download_ok = True

    print("=" * 50)

    if all_ok:
        print("\nAll services configured and connected!")
    elif discovery_ok:
        print("\nAt least one discovery service is working.")
        if not download_ok:
            print("No download services configured (optional).")
        print("MusicMaster is ready to use.")
    else:
        print("\nNo discovery services configured.")
        print("At least one of Spotify or Last.fm is needed for music discovery.")
        print("Edit .env to configure credentials (see Preflight Check -> Fix Table).")
        sys.exit(1)


if __name__ == "__main__":
    main()
