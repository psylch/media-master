"""Spotify service for music search and user data."""

from typing import Optional, Literal
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from .config import SpotifyConfig


class SpotifyService:
    """Service for Spotify API."""

    def __init__(self, config: SpotifyConfig):
        self.config = config
        self._client: Optional[spotipy.Spotify] = None
        self._auth_client: Optional[spotipy.Spotify] = None

    def _get_client(self) -> spotipy.Spotify:
        """Get public data client."""
        if not self._client:
            if not self.config.is_configured():
                raise ValueError("Spotify not configured. Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET.")
            auth = SpotifyClientCredentials(
                client_id=self.config.client_id,
                client_secret=self.config.client_secret
            )
            self._client = spotipy.Spotify(auth_manager=auth)
        return self._client

    def _get_auth_client(self) -> spotipy.Spotify:
        """Get authenticated client for user data."""
        if not self._auth_client:
            if not self.config.is_configured():
                raise ValueError("Spotify not configured.")
            auth = SpotifyOAuth(
                client_id=self.config.client_id,
                client_secret=self.config.client_secret,
                redirect_uri=self.config.redirect_uri,
                scope="user-library-read user-top-read"
            )
            self._auth_client = spotipy.Spotify(auth_manager=auth)
        return self._auth_client

    def search(
        self,
        query: str,
        search_type: str = "track",
        limit: int = 10,
        market: str = "US",
        mode: Literal["concise", "detailed"] = "concise"
    ) -> str:
        """Search Spotify."""
        client = self._get_client()
        results = client.search(q=query, type=search_type, limit=limit, market=market)

        key = f"{search_type}s"
        items = results.get(key, {}).get("items", [])

        if not items:
            return f"No {search_type}s found for '{query}'"

        output = [f"Found {len(items)} {search_type}(s) for '{query}':\n"]

        for idx, item in enumerate(items, 1):
            if search_type == "track":
                artists = ", ".join([a["name"] for a in item["artists"]])
                duration = f"{item['duration_ms'] // 60000}:{(item['duration_ms'] % 60000) // 1000:02d}"
                if mode == "concise":
                    output.append(f"{idx}. {item['name']} by {artists} (ID: {item['id']})")
                else:
                    output.append(f"{idx}. {item['name']}")
                    output.append(f"   Artist(s): {artists}")
                    output.append(f"   Album: {item['album']['name']}")
                    output.append(f"   Duration: {duration}")
                    output.append(f"   Spotify ID: {item['id']}")
                    output.append(f"   URL: {item['external_urls']['spotify']}\n")

            elif search_type == "album":
                artists = ", ".join([a["name"] for a in item["artists"]])
                if mode == "concise":
                    output.append(f"{idx}. {item['name']} by {artists} (ID: {item['id']})")
                else:
                    output.append(f"{idx}. {item['name']}")
                    output.append(f"   Artist(s): {artists}")
                    output.append(f"   Release: {item['release_date']}")
                    output.append(f"   Tracks: {item['total_tracks']}")
                    output.append(f"   Spotify ID: {item['id']}")
                    output.append(f"   URL: {item['external_urls']['spotify']}\n")

            elif search_type == "artist":
                genres = ", ".join(item.get("genres", [])) or "No genres"
                if mode == "concise":
                    output.append(f"{idx}. {item['name']} (ID: {item['id']})")
                else:
                    output.append(f"{idx}. {item['name']}")
                    output.append(f"   Genres: {genres}")
                    output.append(f"   Popularity: {item.get('popularity', 0)}/100")
                    output.append(f"   Spotify ID: {item['id']}")
                    output.append(f"   URL: {item['external_urls']['spotify']}\n")

        return "\n".join(output)

    def get_info(
        self,
        item_id: str,
        item_type: Literal["track", "album", "artist"],
        mode: Literal["concise", "detailed"] = "detailed"
    ) -> str:
        """Get item details."""
        client = self._get_client()

        if item_type == "track":
            track = client.track(item_id)
            artists = ", ".join([a["name"] for a in track["artists"]])
            duration = f"{track['duration_ms'] // 60000}:{(track['duration_ms'] % 60000) // 1000:02d}"
            if mode == "concise":
                return f"{track['name']} by {artists} ({duration})"
            return f"""Track: {track['name']}
Artist(s): {artists}
Album: {track['album']['name']} ({track['album']['release_date']})
Duration: {duration}
Popularity: {track.get('popularity', 0)}/100
Spotify ID: {track['id']}
URL: {track['external_urls']['spotify']}"""

        elif item_type == "album":
            album = client.album(item_id)
            artists = ", ".join([a["name"] for a in album["artists"]])
            genres = ", ".join(album.get("genres", [])) or "No genres"
            if mode == "concise":
                return f"{album['name']} by {artists} ({album['total_tracks']} tracks)"
            tracks = []
            for i, t in enumerate(album["tracks"]["items"], 1):
                dur = f"{t['duration_ms'] // 60000}:{(t['duration_ms'] % 60000) // 1000:02d}"
                tracks.append(f"  {i}. {t['name']} ({dur}) [ID: {t['id']}]")
            return f"""Album: {album['name']}
Artist(s): {artists}
Release: {album['release_date']}
Tracks: {album['total_tracks']}
Genres: {genres}
Spotify ID: {album['id']}
URL: {album['external_urls']['spotify']}

Tracklist:
{chr(10).join(tracks)}"""

        elif item_type == "artist":
            artist = client.artist(item_id)
            top = client.artist_top_tracks(item_id)
            genres = ", ".join(artist.get("genres", [])) or "No genres"
            followers = f"{artist['followers']['total']:,}"
            if mode == "concise":
                return f"{artist['name']} - {genres} ({followers} followers)"
            top_tracks = []
            for i, t in enumerate(top["tracks"][:10], 1):
                top_tracks.append(f"  {i}. {t['name']} (from {t['album']['name']}) [ID: {t['id']}]")
            return f"""Artist: {artist['name']}
Genres: {genres}
Popularity: {artist.get('popularity', 0)}/100
Followers: {followers}
Spotify ID: {artist['id']}
URL: {artist['external_urls']['spotify']}

Top Tracks:
{chr(10).join(top_tracks)}"""

    def get_user_data(
        self,
        data_type: Literal["tracks", "artists"],
        time_range: str = "medium_term",
        limit: int = 20,
        mode: Literal["concise", "detailed"] = "concise"
    ) -> str:
        """Get user's top tracks or artists."""
        client = self._get_auth_client()

        time_desc = {
            "short_term": "last 4 weeks",
            "medium_term": "last 6 months",
            "long_term": "all time"
        }.get(time_range, time_range)

        if data_type == "tracks":
            results = client.current_user_top_tracks(time_range=time_range, limit=limit)
            items = results.get("items", [])
            if not items:
                return "No top tracks found"
            output = [f"Your top {len(items)} tracks from {time_desc}:\n"]
            for idx, track in enumerate(items, 1):
                artists = ", ".join([a["name"] for a in track["artists"]])
                if mode == "concise":
                    output.append(f"{idx}. {track['name']} by {artists} (ID: {track['id']})")
                else:
                    output.append(f"{idx}. {track['name']}")
                    output.append(f"   Artist(s): {artists}")
                    output.append(f"   Album: {track['album']['name']}")
                    output.append(f"   Spotify ID: {track['id']}\n")

        elif data_type == "artists":
            results = client.current_user_top_artists(time_range=time_range, limit=limit)
            items = results.get("items", [])
            if not items:
                return "No top artists found"
            output = [f"Your top {len(items)} artists from {time_desc}:\n"]
            for idx, artist in enumerate(items, 1):
                genres = ", ".join(artist.get("genres", [])) or "No genres"
                if mode == "concise":
                    output.append(f"{idx}. {artist['name']} (ID: {artist['id']})")
                else:
                    output.append(f"{idx}. {artist['name']}")
                    output.append(f"   Genres: {genres}")
                    output.append(f"   Popularity: {artist.get('popularity', 0)}/100\n")

        return "\n".join(output)
