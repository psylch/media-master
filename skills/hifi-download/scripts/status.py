#!/usr/bin/env python3
"""
Check MusicMaster service status.

Usage:
    python scripts/status.py [--json]

Returns current status of all services, combining:
- User preferences (enabled/disabled/not_configured)
- Actual configuration status (credentials present)
- Service availability (API reachable)

This script should be called at the start of each session
to understand what services are available.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.config import Config
from lib.preferences import Preferences


def get_service_status(config: Config, prefs: Preferences) -> dict:
    """Get comprehensive status of all services."""
    status = {
        "discovery": {},
        "downloads": {},
        "summary": {
            "available_discovery": [],
            "available_downloads": [],
            "disabled_services": [],
            "needs_setup": []
        }
    }

    # === Spotify ===
    if prefs.spotify.is_disabled():
        status["discovery"]["spotify"] = {
            "status": "disabled",
            "reason": prefs.spotify.reason or "user choice",
            "available": False
        }
        status["summary"]["disabled_services"].append("spotify")
    elif config.spotify.is_configured():
        status["discovery"]["spotify"] = {
            "status": "ready",
            "available": True
        }
        status["summary"]["available_discovery"].append("spotify")
        # Auto-enable if configured but not explicitly set
        if prefs.spotify.is_not_configured():
            prefs.enable_service("spotify")
    else:
        status["discovery"]["spotify"] = {
            "status": "not_configured",
            "available": False,
            "setup_hint": "Run setup_config.py with --spotify-id and --spotify-secret"
        }
        if not prefs.spotify.is_disabled():
            status["summary"]["needs_setup"].append("spotify")

    # === Last.fm ===
    if prefs.lastfm.is_disabled():
        status["discovery"]["lastfm"] = {
            "status": "disabled",
            "reason": prefs.lastfm.reason or "user choice",
            "available": False
        }
        status["summary"]["disabled_services"].append("lastfm")
    elif config.lastfm.is_configured():
        status["discovery"]["lastfm"] = {
            "status": "ready",
            "available": True
        }
        status["summary"]["available_discovery"].append("lastfm")
        if prefs.lastfm.is_not_configured():
            prefs.enable_service("lastfm")
    else:
        status["discovery"]["lastfm"] = {
            "status": "not_configured",
            "available": False,
            "setup_hint": "Run setup_config.py with --lastfm-key"
        }
        if not prefs.lastfm.is_disabled():
            status["summary"]["needs_setup"].append("lastfm")

    # === Qobuz ===
    if prefs.qobuz.is_disabled():
        status["downloads"]["qobuz"] = {
            "status": "disabled",
            "reason": prefs.qobuz.reason or "user choice",
            "available": False
        }
        status["summary"]["disabled_services"].append("qobuz")
    elif config.qobuz.is_configured():
        quality_map = {5: "MP3 320kbps", 6: "FLAC 16-bit", 7: "FLAC 24-bit", 27: "Hi-Res 24-bit"}
        status["downloads"]["qobuz"] = {
            "status": "ready",
            "available": True,
            "quality": quality_map.get(config.qobuz.quality, f"Quality {config.qobuz.quality}"),
            "download_path": config.qobuz.download_path
        }
        status["summary"]["available_downloads"].append("qobuz")
        if prefs.qobuz.is_not_configured():
            prefs.enable_service("qobuz")
    else:
        status["downloads"]["qobuz"] = {
            "status": "not_configured",
            "available": False,
            "setup_hint": "Run setup_config.py with --qobuz-email and --qobuz-password"
        }
        if not prefs.qobuz.is_disabled():
            status["summary"]["needs_setup"].append("qobuz")

    # === TIDAL ===
    if prefs.tidal.is_disabled():
        status["downloads"]["tidal"] = {
            "status": "disabled",
            "reason": prefs.tidal.reason or "user choice",
            "available": False
        }
        status["summary"]["disabled_services"].append("tidal")
    else:
        # TIDAL uses tiddl - check ~/tiddl.json for auth
        import time
        import subprocess
        import os
        tiddl_config_path = Path.home() / "tiddl.json"
        tidal_ready = False
        tidal_user = None
        tidal_quality = config.tidal.quality
        tidal_error = None

        if tiddl_config_path.exists():
            try:
                import json
                with open(tiddl_config_path) as f:
                    tiddl_config = json.load(f)

                auth = tiddl_config.get("auth", {})
                if auth.get("token") and auth.get("user_id"):
                    # Check if token is expired
                    expires = auth.get("expires", 0)
                    if expires and time.time() > expires:
                        # Auto-refresh expired token
                        # scripts/status.py -> scripts/ -> music-master/ -> music-master/.venv/bin
                        venv_bin = Path(__file__).parent.parent / ".venv" / "bin"
                        tiddl_path = venv_bin / "tiddl"
                        if tiddl_path.exists():
                            result = subprocess.run(
                                [str(tiddl_path), "auth", "refresh"],
                                capture_output=True,
                                text=True,
                                timeout=30
                            )
                            if result.returncode == 0:
                                # Re-read config after refresh
                                with open(tiddl_config_path) as f:
                                    tiddl_config = json.load(f)
                                auth = tiddl_config.get("auth", {})
                                tidal_ready = True
                                tidal_user = auth.get("user_id")
                            else:
                                tidal_error = "Token refresh failed. Run: tiddl auth login"
                        else:
                            tidal_error = "tiddl not found. Run: pip install tiddl"
                    else:
                        tidal_ready = True
                        tidal_user = auth.get("user_id")

                    if tidal_ready:
                        download_config = tiddl_config.get("download", {})
                        tidal_quality = download_config.get("quality", "high")
            except Exception as e:
                tidal_error = str(e)

        if tidal_ready:
            status["downloads"]["tidal"] = {
                "status": "ready",
                "available": True,
                "quality": tidal_quality,
                "download_path": config.tidal.download_path,
                "user_id": tidal_user
            }
            status["summary"]["available_downloads"].append("tidal")
            if prefs.tidal.is_not_configured():
                prefs.enable_service("tidal")
        elif tidal_error:
            status["downloads"]["tidal"] = {
                "status": "error",
                "available": False,
                "setup_hint": tidal_error
            }
            if not prefs.tidal.is_disabled():
                status["summary"]["needs_setup"].append("tidal")
        else:
            status["downloads"]["tidal"] = {
                "status": "not_configured",
                "available": False,
                "setup_hint": "Run: tiddl auth login"
            }
            if not prefs.tidal.is_disabled():
                status["summary"]["needs_setup"].append("tidal")

    return status


def format_human_readable(status: dict) -> str:
    """Format status for human/agent reading."""
    lines = []
    lines.append("MusicMaster Status")
    lines.append("=" * 40)
    lines.append("")

    # Discovery services
    lines.append("Discovery Services:")
    for name, info in status["discovery"].items():
        if info["status"] == "ready":
            lines.append(f"  {name.capitalize()}: READY")
        elif info["status"] == "disabled":
            lines.append(f"  {name.capitalize()}: DISABLED ({info.get('reason', 'user choice')})")
        else:
            lines.append(f"  {name.capitalize()}: NOT CONFIGURED")

    lines.append("")

    # Download services
    lines.append("Download Services:")
    for name, info in status["downloads"].items():
        if info["status"] == "ready":
            extra = f" - {info.get('quality', '')}" if info.get('quality') else ""
            lines.append(f"  {name.capitalize()}: READY{extra}")
        elif info["status"] == "disabled":
            lines.append(f"  {name.capitalize()}: DISABLED ({info.get('reason', 'user choice')})")
        elif info["status"] == "error":
            hint = info.get('setup_hint', 'Unknown error')
            lines.append(f"  {name.capitalize()}: ERROR ({hint})")
        else:
            lines.append(f"  {name.capitalize()}: NOT CONFIGURED")

    lines.append("")

    # Summary
    summary = status["summary"]

    if summary["available_discovery"] or summary["available_downloads"]:
        lines.append("Available Features:")
        if summary["available_discovery"]:
            lines.append(f"  Discovery: {', '.join(summary['available_discovery'])}")
        if summary["available_downloads"]:
            lines.append(f"  Downloads: {', '.join(summary['available_downloads'])}")
        lines.append("")

    if summary["disabled_services"]:
        lines.append(f"Disabled by user: {', '.join(summary['disabled_services'])}")
        lines.append("")

    if summary["needs_setup"]:
        lines.append(f"Needs setup: {', '.join(summary['needs_setup'])}")
        lines.append("(Use 'disable' command to skip, or run setup_config.py to configure)")
        lines.append("")

    # Quick command reference based on available services
    lines.append("Available Commands:")
    if "lastfm" in summary["available_discovery"]:
        lines.append("  ./run.sh lastfm_artists \"Artist Name\"")
        lines.append("  ./run.sh lastfm_tracks \"Track Name\"")
        lines.append("  ./run.sh lastfm_taste")
    if "spotify" in summary["available_discovery"]:
        lines.append("  ./run.sh spotify_search \"Query\"")
        lines.append("  ./run.sh spotify_user tracks|artists")
    if summary["available_downloads"]:
        platforms = summary["available_downloads"]
        lines.append(f"  ./run.sh platform_search \"Album\" -p {platforms[0]}")
        lines.append(f"  ./run.sh platform_download ID -p {platforms[0]}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Check MusicMaster service status")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    try:
        config = Config.load()
        prefs = Preferences.load()

        status = get_service_status(config, prefs)

        if args.json:
            print(json.dumps(status, indent=2))
        else:
            print(format_human_readable(status))

    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}))
        else:
            print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
