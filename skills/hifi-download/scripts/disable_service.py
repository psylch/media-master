#!/usr/bin/env python3
"""
Disable a service explicitly.

Usage:
    python scripts/disable_service.py spotify --reason "No Spotify account"
    python scripts/disable_service.py tidal --reason "No subscription"
    python scripts/disable_service.py qobuz

This records user intent and prevents the agent from repeatedly
trying to use a service the user doesn't want.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.preferences import Preferences


VALID_SERVICES = ['spotify', 'lastfm', 'qobuz', 'tidal']


def main():
    parser = argparse.ArgumentParser(
        description="Disable a MusicMaster service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/disable_service.py spotify --reason "No account"
  python scripts/disable_service.py tidal --reason "No subscription"
  python scripts/disable_service.py qobuz

This prevents the agent from trying to use services you don't want.
The preference is saved and persists across sessions.
"""
    )

    parser.add_argument("service", choices=VALID_SERVICES,
                        help="Service to disable")
    parser.add_argument("--reason", "-r", type=str,
                        help="Reason for disabling (optional, helps agent understand)")

    args = parser.parse_args()

    prefs = Preferences.load()
    prefs.disable_service(args.service, args.reason)

    print(f"Disabled: {args.service}")
    if args.reason:
        print(f"Reason: {args.reason}")
    print()
    print("This preference is saved. The agent will not attempt to use this service.")
    print("To re-enable, run: python scripts/enable_service.py", args.service)


if __name__ == "__main__":
    main()
