#!/usr/bin/env python3
"""
Re-enable a previously disabled service.

Usage:
    python scripts/enable_service.py spotify
    python scripts/enable_service.py tidal

This reverses the effect of disable_service.py.
Note: You still need to configure the service credentials.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.preferences import Preferences
from lib.config import Config


VALID_SERVICES = ['spotify', 'lastfm', 'qobuz', 'tidal']


def main():
    parser = argparse.ArgumentParser(
        description="Re-enable a MusicMaster service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/enable_service.py spotify
  python scripts/enable_service.py tidal

After enabling, you may still need to configure credentials
by editing .env if not already done.
"""
    )

    parser.add_argument("service", choices=VALID_SERVICES,
                        help="Service to enable")

    args = parser.parse_args()

    prefs = Preferences.load()
    config = Config.load()

    prefs.enable_service(args.service)

    print(f"Enabled: {args.service}")
    print()

    # Check if configuration is needed
    needs_config = False
    if args.service == "spotify" and not config.spotify.is_configured():
        needs_config = True
        print("Note: Spotify credentials not configured yet.")
        print("Edit .env: set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET")
    elif args.service == "lastfm" and not config.lastfm.is_configured():
        needs_config = True
        print("Note: Last.fm API key not configured yet.")
        print("Edit .env: set LASTFM_API_KEY")
    elif args.service == "qobuz" and not config.qobuz.is_configured():
        needs_config = True
        print("Note: Qobuz credentials not configured yet.")
        print("Edit .env: set QOBUZ_EMAIL and QOBUZ_PASSWORD")
    elif args.service == "tidal":
        tidal_config = Path.home() / "tiddl.json"
        if not tidal_config.exists():
            needs_config = True
            print("Note: TIDAL not logged in yet.")
            print("Run: tiddl auth login")

    if not needs_config:
        print("Service is ready to use.")


if __name__ == "__main__":
    main()
