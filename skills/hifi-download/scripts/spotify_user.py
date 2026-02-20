#!/usr/bin/env python3
"""Get user's top tracks or artists from Spotify."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.config import Config
from lib.spotify import SpotifyService


def main():
    parser = argparse.ArgumentParser(description="Get your Spotify listening history")
    parser.add_argument("data_type", choices=["tracks", "artists"],
                        help="Type of data to retrieve")
    parser.add_argument("-r", "--range", dest="time_range",
                        choices=["short_term", "medium_term", "long_term"],
                        default="medium_term",
                        help="Time range: short_term (~4 weeks), medium_term (~6 months), long_term (years)")
    parser.add_argument("-l", "--limit", type=int, default=20, help="Number of results (default: 20)")
    parser.add_argument("--detailed", action="store_true", help="Show detailed output")
    args = parser.parse_args()

    try:
        config = Config.load()
        service = SpotifyService(config.spotify)
        mode = "detailed" if args.detailed else "concise"
        result = service.get_user_data(args.data_type, args.time_range, args.limit, mode)
        print(result)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
