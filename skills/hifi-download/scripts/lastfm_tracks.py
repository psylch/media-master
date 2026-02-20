#!/usr/bin/env python3
"""Find similar tracks using Last.fm."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.config import Config
from lib.lastfm import LastfmService


def main():
    parser = argparse.ArgumentParser(description="Find tracks similar to a given track")
    parser.add_argument("track", help="Track name")
    parser.add_argument("artist", help="Artist name")
    parser.add_argument("-l", "--limit", type=int, default=10, help="Number of results (default: 10)")
    parser.add_argument("--detailed", action="store_true", help="Show detailed output")
    args = parser.parse_args()

    try:
        config = Config.load()
        if not config.lastfm.is_configured():
            print("Error: Last.fm API key not configured. Set LASTFM_API_KEY.", file=sys.stderr)
            sys.exit(1)

        service = LastfmService(config.lastfm.api_key)
        mode = "detailed" if args.detailed else "concise"
        result = service.get_similar_tracks(args.track, args.artist, args.limit, mode)
        print(result)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
