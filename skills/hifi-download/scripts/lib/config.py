"""Configuration module for MusicMaster."""

import os
from dataclasses import dataclass
from typing import Optional

# Try to load .env from current directory or parent directories
def load_env():
    """Load .env file from current or parent directories."""
    try:
        from dotenv import load_dotenv
        # Try current directory first
        if os.path.exists('.env'):
            load_dotenv('.env')
            return
        # Try parent directories
        cwd = os.getcwd()
        for _ in range(5):  # Check up to 5 levels
            parent = os.path.dirname(cwd)
            env_path = os.path.join(parent, '.env')
            if os.path.exists(env_path):
                load_dotenv(env_path)
                return
            cwd = parent
    except ImportError:
        pass  # dotenv not installed, rely on environment variables

load_env()


@dataclass
class SpotifyConfig:
    """Spotify API configuration."""
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    redirect_uri: str = "http://127.0.0.1:8888/callback"

    @classmethod
    def from_env(cls) -> "SpotifyConfig":
        return cls(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
            redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
        )

    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)


@dataclass
class LastfmConfig:
    """Last.fm configuration."""
    api_key: Optional[str] = None

    @classmethod
    def from_env(cls) -> "LastfmConfig":
        return cls(api_key=os.getenv("LASTFM_API_KEY"))

    def is_configured(self) -> bool:
        return bool(self.api_key)


@dataclass
class QobuzConfig:
    """Qobuz configuration."""
    email: Optional[str] = None
    password: Optional[str] = None
    quality: int = 27  # 5=MP3, 6=FLAC 16bit, 7=FLAC 24bit, 27=Hi-Res
    download_path: str = "./downloads/qobuz"

    @classmethod
    def from_env(cls) -> "QobuzConfig":
        return cls(
            email=os.getenv("QOBUZ_EMAIL"),
            password=os.getenv("QOBUZ_PASSWORD"),
            quality=int(os.getenv("QOBUZ_QUALITY", "27")),
            download_path=os.getenv("QOBUZ_DOWNLOAD_PATH", "./downloads/qobuz")
        )

    def is_configured(self) -> bool:
        return bool(self.email and self.password)


@dataclass
class TidalConfig:
    """TIDAL configuration."""
    quality: str = "HiFi"
    download_path: str = "./downloads/tidal"

    @classmethod
    def from_env(cls) -> "TidalConfig":
        return cls(
            quality=os.getenv("TIDAL_QUALITY", "HiFi"),
            download_path=os.getenv("TIDAL_DOWNLOAD_PATH", "./downloads/tidal")
        )


@dataclass
class Config:
    """Main configuration container."""
    spotify: SpotifyConfig
    lastfm: LastfmConfig
    qobuz: QobuzConfig
    tidal: TidalConfig

    @classmethod
    def load(cls) -> "Config":
        return cls(
            spotify=SpotifyConfig.from_env(),
            lastfm=LastfmConfig.from_env(),
            qobuz=QobuzConfig.from_env(),
            tidal=TidalConfig.from_env()
        )
