"""Last.fm service for music discovery."""

from typing import List, Literal, Tuple
import requests


class LastfmService:
    """Service for Last.fm API."""

    BASE_URL = "http://ws.audioscrobbler.com/2.0/"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def _request(self, params: dict) -> dict:
        """Make API request."""
        params["api_key"] = self.api_key
        params["format"] = "json"
        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            raise ValueError(f"Last.fm API error: {e}")

    def get_similar_artists(
        self,
        artist: str,
        limit: int = 10,
        mode: Literal["concise", "detailed"] = "concise"
    ) -> str:
        """Get similar artists."""
        data = self._request({
            "method": "artist.getSimilar",
            "artist": artist,
            "limit": min(limit, 100),
            "autocorrect": 1
        })

        if "error" in data:
            return f"Error: {data.get('message', 'Unknown error')}"

        artists = data.get("similarartists", {}).get("artist", [])
        if not artists:
            return f"No similar artists found for '{artist}'"

        output = [f"Artists similar to '{artist}':\n"]
        for idx, a in enumerate(artists, 1):
            match = int(float(a.get("match", 0)) * 100)
            if mode == "concise":
                output.append(f"{idx}. {a['name']} (similarity: {match}%)")
            else:
                output.append(f"{idx}. {a['name']}")
                output.append(f"   Similarity: {match}%")
                if a.get("mbid"):
                    output.append(f"   MBID: {a['mbid']}")
                if a.get("url"):
                    output.append(f"   URL: {a['url']}")
                output.append("")

        return "\n".join(output)

    def get_similar_tracks(
        self,
        track: str,
        artist: str,
        limit: int = 10,
        mode: Literal["concise", "detailed"] = "concise"
    ) -> str:
        """Get similar tracks."""
        data = self._request({
            "method": "track.getSimilar",
            "track": track,
            "artist": artist,
            "limit": min(limit, 100),
            "autocorrect": 1
        })

        if "error" in data:
            return f"Error: {data.get('message', 'Unknown error')}"

        tracks = data.get("similartracks", {}).get("track", [])
        if not tracks:
            return f"No similar tracks found for '{track}' by {artist}"

        output = [f"Tracks similar to '{track}' by {artist}:\n"]
        for idx, t in enumerate(tracks, 1):
            match = int(float(t.get("match", 0)) * 100)
            name = t.get("name", "Unknown")
            artist_name = t.get("artist", {}).get("name", "Unknown")

            if mode == "concise":
                output.append(f"{idx}. {name} by {artist_name} (similarity: {match}%)")
            else:
                output.append(f"{idx}. {name}")
                output.append(f"   Artist: {artist_name}")
                output.append(f"   Similarity: {match}%")
                duration_ms = t.get("duration", 0)
                if duration_ms and int(duration_ms) > 0:
                    secs = int(duration_ms) // 1000
                    output.append(f"   Duration: {secs // 60}:{secs % 60:02d}")
                if t.get("url"):
                    output.append(f"   URL: {t['url']}")
                output.append("")

        return "\n".join(output)

    def discover_from_taste(
        self,
        top_artists: List[str],
        top_tracks: List[Tuple[str, str]],  # (track, artist) pairs
        limit_per_item: int = 5
    ) -> str:
        """Discover music based on user's taste."""
        output = ["Music Discovery based on your taste:\n"]

        # Similar artists
        if top_artists:
            output.append("## Similar Artists")
            for artist in top_artists[:3]:
                try:
                    result = self.get_similar_artists(artist, limit_per_item, "concise")
                    output.append(result)
                    output.append("")
                except Exception as e:
                    output.append(f"Could not get similar artists for {artist}: {e}\n")

        # Similar tracks
        if top_tracks:
            output.append("\n## Similar Tracks")
            for track_name, artist_name in top_tracks[:3]:
                try:
                    result = self.get_similar_tracks(track_name, artist_name, limit_per_item, "concise")
                    output.append(result)
                    output.append("")
                except Exception as e:
                    output.append(f"Could not get similar tracks for '{track_name}': {e}\n")

        return "\n".join(output)
