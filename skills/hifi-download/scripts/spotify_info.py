#!/usr/bin/env python3
"""Get detailed information about a Spotify item."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.config import Config
from lib.spotify import SpotifyService


def main():
    parser = argparse.ArgumentParser(description="Get Spotify item details")
    parser.add_argument("item_id", help="Spotify item ID")
    parser.add_argument("-t", "--type", choices=["track", "album", "artist"],
                        required=True, help="Item type")
    parser.add_argument("--concise", action="store_true", help="Show concise output")
    args = parser.parse_args()

    try:
        config = Config.load()
        service = SpotifyService(config.spotify)
        mode = "concise" if args.concise else "detailed"
        result = service.get_info(args.item_id, args.type, mode)
        print(result)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
