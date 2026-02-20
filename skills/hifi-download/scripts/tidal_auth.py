#!/usr/bin/env python3
"""
TIDAL OAuth device authentication using tiddl.

Usage:
    # Interactive auth (opens browser URL)
    python scripts/tidal_auth.py

    # Get device code URL only (for automation)
    python scripts/tidal_auth.py --get-url

    # Verify existing token
    python scripts/tidal_auth.py --verify

tiddl uses OAuth 2.0 device code flow:
1. Get device code -> returns URL for user to authorize
2. User authorizes in browser
3. Token is saved to ~/tiddl.json
"""

import argparse
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def get_auth_url():
    """Start auth and capture the URL."""
    import re

    # Run tiddl auth login and capture output
    result = subprocess.run(
        [sys.executable, "-m", "tiddl", "auth", "login"],
        capture_output=True,
        text=True,
        timeout=10,
    )

    # Extract URL from output
    output = result.stdout + result.stderr
    url_match = re.search(r'https://link\.tidal\.com/\w+', output)

    if url_match:
        return url_match.group(0)
    return None


def verify_token():
    """Verify existing tiddl token is valid."""
    try:
        from tiddl.config import Config
        from tiddl.api import TidalApi

        config = Config.fromFile()

        if not config.auth.token:
            return False, "No token found in ~/tiddl.json"

        # Try to create API and make a test request
        api = TidalApi(
            token=config.auth.token,
            user_id=config.auth.user_id,
            country_code=config.auth.country_code,
        )

        # Test search
        result = api.getSearch("test")
        if result and result.tracks:
            return True, f"User {config.auth.user_id} ({config.auth.country_code})"
        else:
            return True, f"User {config.auth.user_id} (token valid)"

    except Exception as e:
        return False, str(e)


def run_interactive_auth(timeout=300):
    """Run interactive auth flow."""
    import time

    print("TIDAL Device Authorization (tiddl)")
    print("=" * 40)
    print()

    # Check if already authorized
    valid, msg = verify_token()
    if valid:
        print(f"Already authorized: {msg}")
        return True

    # Run tiddl auth login
    print("Starting authorization...")
    print("A URL will appear - open it in your browser and log in to TIDAL.")
    print()

    try:
        result = subprocess.run(
            [sys.executable, "-m", "tiddl", "auth", "login"],
            timeout=timeout,
        )

        if result.returncode == 0:
            print()
            print("Authorization successful!")
            valid, msg = verify_token()
            if valid:
                print(f"  {msg}")
            return True
        else:
            print()
            print("Authorization failed or was cancelled.")
            return False

    except subprocess.TimeoutExpired:
        print()
        print("Authorization timed out.")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="TIDAL OAuth device authentication using tiddl",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Authentication Flow:
  1. Run without args to start full auth flow
  2. Open the printed URL in browser
  3. Log in to TIDAL and authorize
  4. Token is saved to ~/tiddl.json

For Automation:
  --get-url    Get device code URL (use Playwright to authorize)
  --verify     Check if existing token is valid
"""
    )

    parser.add_argument("--get-url", action="store_true",
                        help="Only get device code URL")
    parser.add_argument("--verify", action="store_true",
                        help="Verify existing token is valid")
    parser.add_argument("--timeout", type=int, default=300,
                        help="Auth timeout in seconds (default: 300)")

    args = parser.parse_args()

    if args.verify:
        valid, msg = verify_token()
        if valid:
            print(f"TIDAL: OK - {msg}")
        else:
            print(f"TIDAL: FAIL - {msg}")
        sys.exit(0 if valid else 1)

    if args.get_url:
        url = get_auth_url()
        if url:
            print(url)
            sys.exit(0)
        else:
            print("Failed to get auth URL", file=sys.stderr)
            sys.exit(1)

    # Full interactive flow
    success = run_interactive_auth(args.timeout)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
