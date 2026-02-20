#!/usr/bin/env python3
"""Search for music on Spotify."""

import argparse
import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.config import Config
from lib.spotify import SpotifyService


def main():
    parser = argparse.ArgumentParser(description="Search Spotify for music")
    parser.add_argument("query", help="Search query")
    parser.add_argument("-t", "--type", choices=["track", "album", "artist", "playlist"],
                        default="track", help="Search type (default: track)")
    parser.add_argument("-l", "--limit", type=int, default=10, help="Number of results (default: 10)")
    parser.add_argument("-m", "--market", default="US", help="Market code (default: US)")
    parser.add_argument("--detailed", action="store_true", help="Show detailed output")
    args = parser.parse_args()

    try:
        config = Config.load()
        service = SpotifyService(config.spotify)
        mode = "detailed" if args.detailed else "concise"
        result = service.search(args.query, args.type, args.limit, args.market, mode)
        print(result)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
