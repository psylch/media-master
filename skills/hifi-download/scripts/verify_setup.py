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
        from TIDALDL.tidal import TidalAPI
        api = TidalAPI()
        if api.isLogin():
            return True, f"Connected (quality: {config.tidal.quality})"
        return False, "Not logged in. Run 'tidal-dl' to authenticate."
    except ImportError:
        return False, "tidal-dl not installed (pip install tidal-dl)"
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
    required_ok = True

    for name, checker in services:
        ok, message = checker(config)
        status = "OK" if ok else "FAIL"
        icon = "+" if ok else "-"
        print(f"[{icon}] {name}: {status}")
        print(f"    {message}")

        if not ok:
            all_ok = False
            if name in ["Spotify", "Last.fm"]:
                required_ok = False

    print("=" * 50)

    if all_ok:
        print("\nAll services configured and connected!")
    elif required_ok:
        print("\nRequired services (Spotify, Last.fm) are working.")
        print("Download services (Qobuz/TIDAL) are optional.")
    else:
        print("\nRequired services not configured.")
        print("Please configure Spotify and Last.fm to use MusicMaster.")
        print("\nSee setup guide for configuration instructions.")
        sys.exit(1)


if __name__ == "__main__":
    main()
