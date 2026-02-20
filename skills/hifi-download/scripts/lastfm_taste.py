#!/usr/bin/env python3
"""Get personalized music recommendations based on Spotify listening history."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.config import Config
from lib.spotify import SpotifyService
from lib.lastfm import LastfmService


def main():
    parser = argparse.ArgumentParser(
        description="Get personalized recommendations based on your listening history"
    )
    parser.add_argument("-r", "--range", dest="time_range",
                        choices=["short_term", "medium_term", "long_term"],
                        default="medium_term",
                        help="Time range for listening history")
    parser.add_argument("-n", "--per-item", type=int, default=5,
                        help="Recommendations per seed item (default: 5)")
    args = parser.parse_args()

    try:
        config = Config.load()

        # Check configs
        if not config.spotify.is_configured():
            print("Error: Spotify not configured.", file=sys.stderr)
            sys.exit(1)
        if not config.lastfm.is_configured():
            print("Error: Last.fm API key not configured.", file=sys.stderr)
            sys.exit(1)

        # Get user's top items from Spotify
        spotify = SpotifyService(config.spotify)

        print("Fetching your Spotify listening history...\n")

        # Get top artists
        top_artists_result = spotify.get_user_data("artists", args.time_range, 5, "concise")
        top_artists = []
        for line in top_artists_result.split('\n'):
            if line and line[0].isdigit():
                # Extract artist name: "1. Artist Name (ID: xxx)"
                parts = line.split('. ', 1)
                if len(parts) > 1:
                    name = parts[1].split(' (ID:')[0]
                    top_artists.append(name)

        # Get top tracks
        top_tracks_result = spotify.get_user_data("tracks", args.time_range, 5, "concise")
        top_tracks = []
        for line in top_tracks_result.split('\n'):
            if line and line[0].isdigit():
                # Extract: "1. Track Name by Artist (ID: xxx)"
                parts = line.split('. ', 1)
                if len(parts) > 1:
                    rest = parts[1].split(' (ID:')[0]
                    if ' by ' in rest:
                        track, artist = rest.rsplit(' by ', 1)
                        top_tracks.append((track, artist))

        if not top_artists and not top_tracks:
            print("No listening history found. Listen to more music on Spotify first!")
            sys.exit(0)

        print(f"Found {len(top_artists)} top artists and {len(top_tracks)} top tracks.\n")

        # Get recommendations from Last.fm
        lastfm = LastfmService(config.lastfm.api_key)
        result = lastfm.discover_from_taste(top_artists, top_tracks, args.per_item)
        print(result)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
