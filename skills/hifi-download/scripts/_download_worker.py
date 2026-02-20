#!/usr/bin/env python3
"""Background download worker process.

Spawned by platform_download.py as a detached subprocess.
Reads task params from a temp JSON file, performs the download,
and updates task state in ~/.musicmaster/downloads.json.
"""

import json
import signal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.download_state import DownloadStatus, LOG_DIR, ensure_dirs, update_task


def main():
    if len(sys.argv) != 2:
        print("Usage: _download_worker.py <params_json_path>", file=sys.stderr)
        sys.exit(1)

    params_path = Path(sys.argv[1])

    try:
        params = json.loads(params_path.read_text())
    finally:
        params_path.unlink(missing_ok=True)

    task_id = params["task_id"]
    platform = params["platform"]
    item_id = params["item_id"]
    item_type = params["item_type"]
    output_path = params["output_path"]

    ensure_dirs()
    log_path = LOG_DIR / f"{task_id}.log"
    log_file = open(log_path, "w")
    sys.stdout = log_file
    sys.stderr = log_file

    def on_sigterm(signum, frame):
        update_task(task_id, status=DownloadStatus.FAILED, error="Download cancelled (process terminated)")
        log_file.close()
        sys.exit(1)

    signal.signal(signal.SIGTERM, on_sigterm)

    try:
        update_task(task_id, status=DownloadStatus.IN_PROGRESS)

        from lib.config import Config
        from lib.platform import get_platform_service

        config = Config.load()
        service = get_platform_service(platform, config)

        print(f"Starting {platform} download: {item_type} {item_id}")
        result = service.download(item_id, item_type, output_path)
        print(f"Download result: {result}")

        if result.startswith("Error"):
            update_task(task_id, status=DownloadStatus.FAILED, error=result)
        else:
            file_path = None
            for line in result.splitlines():
                if line.startswith("Location:"):
                    file_path = line.split(":", 1)[1].strip()
                    break
            update_task(task_id, status=DownloadStatus.COMPLETED, file_path=file_path, progress=100)

    except Exception as e:
        print(f"Worker exception: {e}")
        update_task(task_id, status=DownloadStatus.FAILED, error=str(e))
    finally:
        log_file.close()


if __name__ == "__main__":
    main()
