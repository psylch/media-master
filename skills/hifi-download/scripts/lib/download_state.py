"""Shared download state management via JSON file.

Provides process-safe read/write to ~/.musicmaster/downloads.json,
compatible with the MusicMaster MCP's state format.
"""

import fcntl
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Optional


STATE_DIR = Path.home() / ".musicmaster"
STATE_FILE = STATE_DIR / "downloads.json"
TMP_DIR = STATE_DIR / "tmp"
LOG_DIR = STATE_DIR / "logs"


class DownloadStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


def _parse_datetime(value: str) -> datetime:
    """Parse an ISO datetime string, falling back to now() on missing/invalid input."""
    if value:
        return datetime.fromisoformat(value)
    return datetime.now()


@dataclass
class DownloadTask:
    id: str
    platform: str
    item_id: str
    item_type: str
    status: DownloadStatus
    output_path: Optional[str] = None
    progress: int = 0
    file_path: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    artist: Optional[str] = None
    album_title: Optional[str] = None
    track_title: Optional[str] = None
    total_items: Optional[int] = None
    downloaded_items: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "platform": self.platform,
            "item_id": self.item_id,
            "item_type": self.item_type,
            "status": self.status.value,
            "output_path": self.output_path,
            "progress": self.progress,
            "file_path": self.file_path,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "artist": self.artist,
            "album_title": self.album_title,
            "track_title": self.track_title,
            "total_items": self.total_items,
            "downloaded_items": self.downloaded_items,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DownloadTask":
        return cls(
            id=data["id"],
            platform=data["platform"],
            item_id=data["item_id"],
            item_type=data["item_type"],
            status=DownloadStatus(data["status"]),
            output_path=data.get("output_path"),
            progress=data.get("progress", 0),
            file_path=data.get("file_path"),
            error=data.get("error"),
            created_at=_parse_datetime(data.get("created_at")),
            updated_at=_parse_datetime(data.get("updated_at")),
            artist=data.get("artist"),
            album_title=data.get("album_title"),
            track_title=data.get("track_title"),
            total_items=data.get("total_items"),
            downloaded_items=data.get("downloaded_items"),
        )


def ensure_dirs():
    """Create all required state directories."""
    for d in (STATE_DIR, TMP_DIR, LOG_DIR):
        d.mkdir(parents=True, exist_ok=True)


def load_state() -> Dict[str, DownloadTask]:
    """Load all download tasks from state file."""
    if not STATE_FILE.exists():
        return {}
    try:
        with open(STATE_FILE, "r") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            try:
                data = json.load(f)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
    except Exception:
        return {}

    result = {}
    for task_data in data.get("downloads", []):
        try:
            task = DownloadTask.from_dict(task_data)
            result[task.id] = task
        except Exception:
            pass
    return result


def save_state(downloads: Dict[str, DownloadTask]):
    """Atomically save all download tasks to state file."""
    ensure_dirs()
    data = {"downloads": [t.to_dict() for t in downloads.values()]}
    temp_file = STATE_FILE.with_suffix(".tmp")
    with open(temp_file, "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            json.dump(data, f, indent=2)
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)
    temp_file.replace(STATE_FILE)


def add_task(task: DownloadTask):
    """Add a new task to the state file."""
    downloads = load_state()
    downloads[task.id] = task
    save_state(downloads)


def update_task(task_id: str, **updates) -> Optional[DownloadTask]:
    """Update a single task's fields and save. Returns updated task or None."""
    downloads = load_state()
    task = downloads.get(task_id)
    if not task:
        return None
    for key, value in updates.items():
        if key == "status" and isinstance(value, str):
            value = DownloadStatus(value)
        setattr(task, key, value)
    task.updated_at = datetime.now()
    save_state(downloads)
    return task


def get_task(task_id: str) -> Optional[DownloadTask]:
    """Get a single task by ID."""
    return load_state().get(task_id)


def new_download_id() -> str:
    """Generate a new download ID."""
    return str(uuid.uuid4())[:8]
