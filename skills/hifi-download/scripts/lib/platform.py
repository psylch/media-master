"""Platform service for TIDAL and Qobuz downloads."""

from typing import Optional, Literal, Callable
from .config import TidalConfig, QobuzConfig


class QobuzService:
    """Qobuz download service."""

    def __init__(self, config: QobuzConfig):
        self.config = config
        self._qobuz = None

    def _get_client(self):
        """Get Qobuz client (suppresses qobuz-dl's verbose output)."""
        if not self._qobuz:
            if not self.config.is_configured():
                raise ValueError("Qobuz not configured. Set QOBUZ_EMAIL and QOBUZ_PASSWORD.")
            try:
                import sys
                import os
                from io import StringIO
                from qobuz_dl.core import QobuzDL

                # Suppress qobuz-dl's verbose login output
                old_stdout = sys.stdout
                sys.stdout = StringIO()
                try:
                    self._qobuz = QobuzDL(
                        directory=self.config.download_path,
                        quality=self.config.quality
                    )
                    self._qobuz.get_tokens()
                    self._qobuz.initialize_client(
                        self.config.email,
                        self.config.password,
                        self._qobuz.app_id,
                        self._qobuz.secrets
                    )
                finally:
                    sys.stdout = old_stdout
            except ImportError:
                raise ImportError("qobuz-dl not installed. Run: pip install qobuz-dl")
        return self._qobuz

    def search(
        self,
        query: str,
        search_type: Literal["track", "album", "artist"] = "album",
        limit: int = 10
    ) -> str:
        """Search Qobuz (suppresses qobuz-dl's verbose output)."""
        import sys
        import os

        # Suppress ALL output during qobuz-dl calls
        devnull_fd = os.open(os.devnull, os.O_WRONLY)
        old_stdout_fd = os.dup(1)
        old_stderr_fd = os.dup(2)
        os.dup2(devnull_fd, 1)
        os.dup2(devnull_fd, 2)
        try:
            qobuz = self._get_client()
            results = qobuz.search_by_type(query, search_type, limit=limit)
        finally:
            os.dup2(old_stdout_fd, 1)
            os.dup2(old_stderr_fd, 2)
            os.close(devnull_fd)
            os.close(old_stdout_fd)
            os.close(old_stderr_fd)

        if not results:
            return f"No {search_type}s found on Qobuz for '{query}'"

        output = [f"Found {len(results)} Qobuz {search_type}(s) for '{query}':\n"]
        for idx, item in enumerate(results, 1):
            text = item.get('text', 'Unknown')
            url = item.get('url', '')
            qobuz_id = url.split('/')[-1] if url else 'N/A'
            output.append(f"{idx}. {text}")
            output.append(f"   [Qobuz ID: {qobuz_id}]")

        return "\n".join(output)

    def download(
        self,
        item_id: str,
        item_type: Literal["track", "album"] = "album",
        output_path: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> str:
        """Download from Qobuz using CLI for cleaner output."""
        import subprocess
        import sys
        import os
        from pathlib import Path

        download_path = os.path.expanduser(output_path or self.config.download_path)
        quality = self.config.quality or 27

        # Build Qobuz URL
        if item_type == "track":
            url = f"https://play.qobuz.com/track/{item_id}"
        else:
            url = f"https://play.qobuz.com/album/{item_id}"

        try:
            # Record existing folders before download
            dl_path = Path(download_path)
            dl_path.mkdir(parents=True, exist_ok=True)
            folders_before = set(dl_path.iterdir()) if dl_path.exists() else set()

            # Find qobuz-dl executable in same venv
            venv_bin = os.path.dirname(sys.executable)
            qobuz_dl_path = os.path.join(venv_bin, "qobuz-dl")

            # Call qobuz-dl CLI
            cmd = [
                qobuz_dl_path,
                "dl", url,
                "-q", str(quality),
                "-d", download_path,
                "--no-db",  # Don't track downloads in database
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minute timeout for large albums
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Unknown error"
                return f"Error downloading from Qobuz: {error_msg}"

            # Verify download succeeded by checking for new files
            folders_after = set(dl_path.iterdir()) if dl_path.exists() else set()
            new_folders = folders_after - folders_before

            if not new_folders:
                # Check if error in output
                output = result.stdout + result.stderr
                if "not found" in output.lower() or "error" in output.lower():
                    return f"Error: Qobuz {item_type} not found (ID: {item_id}). Please verify the ID is correct."
                return f"Error: Download completed but no files were created. The {item_type} ID '{item_id}' may be invalid."

            if progress_callback:
                progress_callback(1, 1)

            # Report the actual downloaded folder name
            downloaded_name = list(new_folders)[0].name
            return f"Downloaded: {downloaded_name}\nLocation: {download_path}"

        except subprocess.TimeoutExpired:
            return f"Download timed out for Qobuz {item_type}: {item_id}"
        except Exception as e:
            return f"Error downloading from Qobuz: {e}"


class TidalService:
    """TIDAL download service using tiddl library.

    tiddl is a modern TIDAL downloader that properly supports dash+xml streams.
    Config is stored in ~/tiddl.json after running 'tiddl auth login'.
    """

    def __init__(self, config: TidalConfig):
        self.config = config
        self._api = None

    def _get_api(self):
        """Get tiddl TidalApi instance (auto-refreshes expired token)."""
        if self._api:
            return self._api

        try:
            import os
            import time
            import subprocess
            import sys
            from tiddl.api import TidalApi
            from tiddl.config import Config

            config = Config.fromFile()

            if not config.auth.token:
                raise ValueError(
                    "TIDAL not authenticated. Run: tiddl auth login"
                )

            # Check if token is expired and auto-refresh
            if config.auth.expires and time.time() > config.auth.expires:
                venv_bin = os.path.dirname(sys.executable)
                tiddl_path = os.path.join(venv_bin, "tiddl")
                result = subprocess.run(
                    [tiddl_path, "auth", "refresh"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode != 0:
                    raise ValueError(
                        "TIDAL token expired and refresh failed. Run: tiddl auth login"
                    )
                # Reload config after refresh
                config = Config.fromFile()

            self._api = TidalApi(
                token=config.auth.token,
                user_id=config.auth.user_id,
                country_code=config.auth.country_code,
            )
            return self._api

        except ImportError:
            raise ImportError(
                "tiddl not installed. Run: pip install tiddl"
            )

    def search(
        self,
        query: str,
        search_type: Literal["track", "album", "artist"] = "album",
        limit: int = 10
    ) -> str:
        """Search TIDAL using tiddl API. Auto-retries on token expiration."""
        max_retries = 2
        for attempt in range(max_retries):
            try:
                api = self._get_api()
                result = api.getSearch(query)
                break  # Success, exit retry loop
            except Exception as e:
                error_str = str(e).lower()
                if ("expired" in error_str or "401" in error_str) and attempt < max_retries - 1:
                    # Reset cached API and refresh token
                    self._api = None
                    self._refresh_token()
                    continue  # Retry
                raise  # Re-raise if not token error or max retries reached

        if not result:
            return f"No results found on TIDAL for '{query}'"

        # Get items based on search type (result.X is a container with .items list)
        if search_type == "track":
            container = result.tracks
            items = container.items[:limit] if container and container.items else []
        elif search_type == "album":
            container = result.albums
            items = container.items[:limit] if container and container.items else []
        elif search_type == "artist":
            container = result.artists
            items = container.items[:limit] if container and container.items else []
        else:
            raise ValueError(f"Invalid type: {search_type}")

        if not items:
            return f"No {search_type}s found on TIDAL for '{query}'"

        output = [f"Found {len(items)} TIDAL {search_type}(s) for '{query}':\n"]
        for idx, item in enumerate(items, 1):
            if search_type == "track":
                artists = ", ".join([a.name for a in item.artists]) if item.artists else "Unknown"
                dur = item.duration or 0
                output.append(f"{idx}. {item.title} by {artists} ({dur // 60}:{dur % 60:02d}) [ID: {item.id}]")
            elif search_type == "album":
                artists = ", ".join([a.name for a in item.artists]) if item.artists else "Unknown"
                tracks = item.numberOfTracks or 0
                output.append(f"{idx}. {item.title} by {artists} ({tracks} tracks) [ID: {item.id}]")
            elif search_type == "artist":
                output.append(f"{idx}. {item.name} [ID: {item.id}]")

        return "\n".join(output)

    def _refresh_token(self) -> bool:
        """Refresh TIDAL token. Returns True if successful."""
        import subprocess
        import sys
        import os
        venv_bin = os.path.dirname(sys.executable)
        tiddl_path = os.path.join(venv_bin, "tiddl")
        result = subprocess.run(
            [tiddl_path, "auth", "refresh"],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0

    def download(
        self,
        item_id: str,
        item_type: Literal["track", "album"] = "album",
        output_path: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> str:
        """Download from TIDAL using tiddl CLI.

        Auto-refreshes token and retries on expiration - user never sees token errors.
        """
        import subprocess
        import sys
        import os
        from pathlib import Path

        download_path = os.path.expanduser(output_path or self.config.download_path)
        quality = self.config.quality or "high"

        # Map quality names
        quality_map = {
            "Normal": "normal",
            "High": "high",
            "HiFi": "high",
            "Master": "master",
            "normal": "normal",
            "high": "high",
            "master": "master",
        }
        tiddl_quality = quality_map.get(quality, "high")

        # Build TIDAL URL
        if item_type == "track":
            url = f"https://tidal.com/browse/track/{item_id}"
        else:
            url = f"https://tidal.com/browse/album/{item_id}"

        venv_bin = os.path.dirname(sys.executable)
        tiddl_path = os.path.join(venv_bin, "tiddl")

        # Download with auto-retry on token expiration
        max_retries = 2
        for attempt in range(max_retries):
            try:
                # Record existing folders before download
                dl_path = Path(download_path)
                dl_path.mkdir(parents=True, exist_ok=True)
                folders_before = set(dl_path.iterdir()) if dl_path.exists() else set()

                # Call tiddl CLI
                cmd = [
                    tiddl_path,
                    "url", url, "download",
                    "-q", tiddl_quality,
                    "-p", download_path,
                ]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=600,  # 10 minute timeout
                )

                if result.returncode != 0:
                    error_msg = result.stderr or result.stdout or "Unknown error"
                    # Token expired? Auto-refresh and retry
                    if ("expired" in error_msg.lower() or "401" in error_msg) and attempt < max_retries - 1:
                        if self._refresh_token():
                            continue  # Retry download
                    return f"Error downloading from TIDAL: {error_msg}"

                # Verify download succeeded by checking for new files
                folders_after = set(dl_path.iterdir()) if dl_path.exists() else set()
                new_folders = folders_after - folders_before

                if not new_folders:
                    output = result.stdout + result.stderr
                    if "not found" in output.lower() or "error" in output.lower():
                        return f"Error: TIDAL {item_type} not found (ID: {item_id}). Please verify the ID is correct."
                    return f"Error: Download completed but no files were created. The {item_type} ID '{item_id}' may be invalid."

                if progress_callback:
                    progress_callback(1, 1)

                # Report the actual downloaded folder name
                downloaded_name = list(new_folders)[0].name
                return f"Downloaded: {downloaded_name}\nLocation: {download_path}"

            except subprocess.TimeoutExpired:
                return f"Download timed out for TIDAL {item_type}: {item_id}"
            except Exception as e:
                return f"Error downloading from TIDAL: {e}"

        return f"Error downloading from TIDAL: Max retries exceeded"


def get_platform_service(platform: str, config):
    """Get platform service by name."""
    if platform == "qobuz":
        return QobuzService(config.qobuz)
    elif platform == "tidal":
        return TidalService(config.tidal)
    else:
        raise ValueError(f"Unknown platform: {platform}")
