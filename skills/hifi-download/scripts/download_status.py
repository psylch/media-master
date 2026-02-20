#!/usr/bin/env python3
"""Check download progress by reading shared state."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.download_state import DownloadStatus, get_task, load_state

ACTIVE_STATUSES = {DownloadStatus.PENDING, DownloadStatus.IN_PROGRESS}


def format_single(task):
    """Format a single download task for human-readable output."""
    lines = [
        f"Download: {task.id}",
        f"Status:   {task.status.value}",
        f"Platform: {task.platform}",
        f"Type:     {task.item_type}",
    ]
    if task.artist:
        lines.append(f"Artist:   {task.artist}")
    if task.album_title:
        lines.append(f"Album:    {task.album_title}")
    if task.track_title:
        lines.append(f"Track:    {task.track_title}")
    if task.progress:
        lines.append(f"Progress: {task.progress}%")
    if task.total_items is not None and task.downloaded_items is not None:
        lines.append(f"Items:    {task.downloaded_items}/{task.total_items}")
    lines.append(f"Started:  {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Updated:  {task.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
    if task.error:
        lines.append(f"Error:    {task.error}")
    if task.file_path:
        lines.append(f"File:     {task.file_path}")
    return "\n".join(lines)


def format_table(tasks):
    """Format multiple tasks as a table."""
    lines = [f"{'ID':<12}{'Status':<14}{'Platform':<10}{'Type':<7}{'Started'}"]
    for t in tasks:
        started = t.created_at.strftime("%Y-%m-%d %H:%M")
        short_id = t.id[:10] if len(t.id) > 10 else t.id
        lines.append(f"{short_id:<12}{t.status.value:<14}{t.platform:<10}{t.item_type:<7}{started}")

    active = sum(1 for t in tasks if t.status in ACTIVE_STATUSES)
    completed = sum(1 for t in tasks if t.status == DownloadStatus.COMPLETED)
    failed = sum(1 for t in tasks if t.status == DownloadStatus.FAILED)

    lines.append("---")
    summary = f"Total: {len(tasks)} | Active: {active} | Completed: {completed}"
    if failed:
        summary += f" | Failed: {failed}"
    lines.append(summary)
    return "\n".join(lines)


def output_json(data):
    print(json.dumps(data, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Check download status")
    parser.add_argument("download_id", nargs="?", help="ID of a specific download")
    parser.add_argument("--all", action="store_true", help="Show all downloads")
    parser.add_argument("--active", action="store_true", help="Show only pending/in_progress downloads")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Output as JSON")
    args = parser.parse_args()

    # Single download lookup
    if args.download_id:
        task = get_task(args.download_id)
        if not task:
            print(f"Download {args.download_id} not found", file=sys.stderr)
            sys.exit(1)
        if args.as_json:
            output_json(task.to_dict())
        else:
            print(format_single(task))
        return

    # List downloads
    if args.all or args.active:
        tasks = list(load_state().values())
        if args.active:
            tasks = [t for t in tasks if t.status in ACTIVE_STATUSES]
        if not tasks:
            print("[]" if args.as_json else "No downloads found.")
            return
        if args.as_json:
            output_json([t.to_dict() for t in tasks])
        else:
            print(format_table(tasks))
        return

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
