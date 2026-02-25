#!/usr/bin/env python3
"""
Complete Spotify OAuth authorization.

Usage:
    python scripts/spotify_auth.py [--no-browser]

Opens browser for Spotify login. After authorization, prints user info.
Use --no-browser to only print the authorization URL.
"""

import argparse
import sys
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.config import Config


def main():
    parser = argparse.ArgumentParser(description="Complete Spotify OAuth authorization")
    parser.add_argument("--no-browser", action="store_true",
                        help="Don't open browser, just print authorization URL")
    args = parser.parse_args()

    try:
        config = Config.load()

        if not config.spotify.is_configured():
            print("Error: Spotify credentials not configured.")
            print("Edit .env: set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET first.")
            sys.exit(1)

        import spotipy
        from spotipy.oauth2 import SpotifyOAuth

        # Create auth manager
        auth = SpotifyOAuth(
            client_id=config.spotify.client_id,
            client_secret=config.spotify.client_secret,
            redirect_uri=config.spotify.redirect_uri,
            scope="user-library-read user-top-read",
            open_browser=not args.no_browser
        )

        # Get authorization URL
        auth_url = auth.get_authorize_url()

        if args.no_browser:
            print("Authorization URL:")
            print(auth_url)
            print()
            print("Open this URL in a browser, log in, and authorize the app.")
            print("After authorization, you'll be redirected to a URL like:")
            print("  http://127.0.0.1:8888/callback?code=XXXXX")
            print()
            print("Copy that full URL and run:")
            print("  python scripts/spotify_auth.py --callback-url='<URL>'")
            return

        # Try to get token (this will open browser if needed)
        print("Opening browser for Spotify authorization...")
        print("Please log in and authorize the app.")
        print()

        try:
            sp = spotipy.Spotify(auth_manager=auth)
            user = sp.current_user()

            print("Authorization successful!")
            print(f"  User: {user['display_name']}")
            print(f"  ID: {user['id']}")
            print(f"  Country: {user.get('country', 'N/A')}")
            print()
            print("Spotify OAuth token has been cached.")
            print("You can now use spotify_user.py and lastfm_taste.py")

        except spotipy.SpotifyException as e:
            print(f"Spotify API error: {e}")
            sys.exit(1)

    except ImportError:
        print("Error: spotipy not installed.")
        print("Run setup_env.py first.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
