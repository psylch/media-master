#!/usr/bin/env python3
"""Download music from TIDAL or Qobuz."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.config import Config
from lib.platform import get_platform_service


def progress_callback(done: int, total: int):
    """Print download progress."""
    if total > 0:
        pct = int(done / total * 100)
        print(f"Progress: {done}/{total} ({pct}%)")


def main():
    parser = argparse.ArgumentParser(description="Download Hi-Res music from TIDAL or Qobuz")
    parser.add_argument("item_id", help="Item ID from platform search")
    parser.add_argument("-p", "--platform", choices=["qobuz", "tidal"],
                        required=True, help="Platform to download from")
    parser.add_argument("-t", "--type", choices=["track", "album"],
                        default="album", help="Item type (default: album)")
    parser.add_argument("-o", "--output", help="Custom output path")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress progress output")
    args = parser.parse_args()

    try:
        config = Config.load()

        # Check platform config
        if args.platform == "qobuz" and not config.qobuz.is_configured():
            print("Error: Qobuz not configured. Set QOBUZ_EMAIL and QOBUZ_PASSWORD.", file=sys.stderr)
            sys.exit(1)

        service = get_platform_service(args.platform, config)

        print(f"Starting download from {args.platform.upper()}...")
        callback = None if args.quiet else progress_callback
        result = service.download(args.item_id, args.type, args.output, callback)
        print(result)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
