#!/usr/bin/env python3
"""Search for music on TIDAL or Qobuz."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.config import Config
from lib.platform import get_platform_service


def main():
    parser = argparse.ArgumentParser(description="Search TIDAL or Qobuz for Hi-Res music")
    parser.add_argument("query", help="Search query")
    parser.add_argument("-p", "--platform", choices=["qobuz", "tidal"],
                        required=True, help="Platform to search")
    parser.add_argument("-t", "--type", choices=["track", "album", "artist"],
                        default="album", help="Search type (default: album)")
    parser.add_argument("-l", "--limit", type=int, default=10, help="Number of results (default: 10)")
    args = parser.parse_args()

    try:
        config = Config.load()

        # Check platform config
        if args.platform == "qobuz" and not config.qobuz.is_configured():
            print("Error: Qobuz not configured. Set QOBUZ_EMAIL and QOBUZ_PASSWORD.", file=sys.stderr)
            sys.exit(1)

        service = get_platform_service(args.platform, config)
        result = service.search(args.query, args.type, args.limit)
        print(result)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
