#!/usr/bin/env python3
"""Download music from TIDAL or Qobuz.

Default: async (spawns background worker, returns download_id immediately).
Use --sync for blocking behavior.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.config import Config
from lib.download_state import (
    DownloadStatus, DownloadTask, TMP_DIR,
    add_task, ensure_dirs, new_download_id,
)
from lib.platform import get_platform_service


def error_exit(error: str, hint: str, recoverable: bool = True, exit_code: int = 1):
    """Print structured JSON error to stderr and exit."""
    print(json.dumps({"error": error, "hint": hint, "recoverable": recoverable}), file=sys.stderr)
    sys.exit(exit_code)


def validate_config(platform: str, config: Config):
    """Exit with an error if the platform is not configured."""
    if platform == "qobuz" and not config.qobuz.is_configured():
        error_exit(
            "qobuz_not_configured",
            "Edit .env: set QOBUZ_EMAIL and QOBUZ_PASSWORD (requires Qobuz Studio/Sublime subscription).",
            recoverable=True,
        )


def progress_callback(done: int, total: int):
    if total > 0:
        pct = int(done / total * 100)
        print(f"Progress: {done}/{total} ({pct}%)")


def run_sync(args):
    """Blocking download (legacy behavior)."""
    config = Config.load()
    validate_config(args.platform, config)

    service = get_platform_service(args.platform, config)
    print(f"Starting download from {args.platform.upper()}...")
    callback = None if args.quiet else progress_callback
    result = service.download(args.item_id, args.type, args.output, callback)
    print(result)


def run_async(args):
    """Non-blocking download (spawn background worker)."""
    config = Config.load()
    validate_config(args.platform, config)

    download_id = new_download_id()
    task = DownloadTask(
        id=download_id,
        platform=args.platform,
        item_id=args.item_id,
        item_type=args.type,
        status=DownloadStatus.PENDING,
        output_path=args.output,
    )
    add_task(task)

    ensure_dirs()
    params_file = TMP_DIR / f"{download_id}.json"
    params_file.write_text(json.dumps({
        "task_id": download_id,
        "platform": args.platform,
        "item_id": args.item_id,
        "item_type": args.type,
        "output_path": args.output,
    }))

    worker_script = Path(__file__).parent / "_download_worker.py"
    subprocess.Popen(
        [sys.executable, str(worker_script), str(params_file)],
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    print(f"Download queued: {download_id}")
    print(f"Platform: {args.platform.upper()} | Type: {args.type} | ID: {args.item_id}")
    print(f"Check status: bash ${{SKILL_PATH}}/run.sh download_status {download_id}")


def main():
    parser = argparse.ArgumentParser(description="Download Hi-Res music from TIDAL or Qobuz")
    parser.add_argument("item_id", help="Item ID from platform search")
    parser.add_argument("-p", "--platform", choices=["qobuz", "tidal"],
                        required=True, help="Platform to download from")
    parser.add_argument("-t", "--type", choices=["track", "album"],
                        default="album", help="Item type (default: album)")
    parser.add_argument("-o", "--output", help="Custom output path")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress progress output")
    parser.add_argument("--sync", action="store_true", help="Block until download completes")
    args = parser.parse_args()

    try:
        if args.sync:
            run_sync(args)
        else:
            run_async(args)
    except Exception as e:
        error_exit(
            str(type(e).__name__),
            str(e),
            recoverable=False,
            exit_code=2,
        )


if __name__ == "__main__":
    main()
