#!/usr/bin/env python3
"""Standalone web dashboard for monitoring HiFi downloads.

Reads download state from ~/.musicmaster/downloads.json and serves
an HTML dashboard with polling-based auto-refresh. No external
dependencies required.
"""

import argparse
import json
import signal
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent))

from lib.download_state import STATE_FILE

EMPTY_STATE = {"total": 0, "downloads": []}


def read_downloads_from_file() -> dict:
    """Read download state directly from shared JSON file."""
    try:
        if not STATE_FILE.exists():
            return EMPTY_STATE
        data = json.loads(STATE_FILE.read_text())
        downloads = data.get("downloads", [])
        return {"total": len(downloads), "downloads": downloads}
    except Exception:
        return EMPTY_STATE


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>HiFi Downloads</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            padding: 20px;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 30px;
        }
        h1 {
            color: #1db954;
            margin-bottom: 10px;
            font-size: 32px;
        }
        .subtitle {
            color: #888;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stat-card.pending { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
        .stat-card.in_progress { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
        .stat-card.completed { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
        .stat-card.failed { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
        .stat-label {
            font-size: 12px;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .stat-value {
            font-size: 36px;
            font-weight: bold;
            margin-top: 5px;
        }
        .downloads {
            margin-top: 20px;
        }
        .download-item {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
            transition: all 0.3s ease;
        }
        .download-item:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }
        .download-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .title-line {
            font-weight: 600;
            font-size: 15px;
            color: #222;
        }
        .download-id {
            font-family: 'Courier New', monospace;
            font-size: 12px;
            color: #666;
        }
        .download-info {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 10px;
        }
        .info-item {
            display: flex;
            flex-direction: column;
        }
        .info-label {
            font-size: 11px;
            color: #888;
            text-transform: uppercase;
            margin-bottom: 5px;
            letter-spacing: 0.5px;
        }
        .info-value {
            font-size: 14px;
            font-weight: 500;
            color: #333;
        }
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .status-pending { background: #fff3cd; color: #856404; }
        .status-in_progress { background: #d1ecf1; color: #0c5460; }
        .status-completed { background: #d4edda; color: #155724; }
        .status-failed { background: #f8d7da; color: #721c24; }
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #e0e0e0;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 10px;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s ease;
        }
        .progress-fill.progress-animated {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #667eea 100%);
            background-size: 200% 100%;
            animation: progress-animation 1.5s ease-in-out infinite;
        }
        @keyframes progress-animation {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }
        .progress-row {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        .progress-text {
            font-size: 12px;
            color: #666;
            min-width: 40px;
            text-align: right;
        }
        .error-message {
            margin-top: 10px;
            padding: 10px;
            background: #f8d7da;
            color: #721c24;
            border-radius: 4px;
            border-left: 4px solid #f5c6cb;
            font-size: 13px;
        }
        .file-path {
            margin-top: 10px;
            padding: 10px;
            background: #e7f3ff;
            color: #004085;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            word-break: break-all;
        }
        .no-downloads {
            text-align: center;
            padding: 60px 20px;
            color: #888;
        }
        .no-downloads-icon {
            font-size: 64px;
            margin-bottom: 20px;
            opacity: 0.3;
        }
        .refresh-btn {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #1db954;
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 50px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(29, 185, 84, 0.4);
            transition: all 0.3s ease;
        }
        .refresh-btn:hover {
            background: #1ed760;
            transform: scale(1.05);
        }
        .auto-refresh {
            font-size: 11px;
            opacity: 0.8;
            display: block;
            margin-top: 3px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>HiFi Downloads</h1>
        <p class="subtitle">Download queue monitoring &mdash; auto-refresh every 3s</p>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">Total Downloads</div>
                <div class="stat-value" id="total-count">0</div>
            </div>
            <div class="stat-card pending">
                <div class="stat-label">Pending</div>
                <div class="stat-value" id="pending-count">0</div>
            </div>
            <div class="stat-card in_progress">
                <div class="stat-label">In Progress</div>
                <div class="stat-value" id="in-progress-count">0</div>
            </div>
            <div class="stat-card completed">
                <div class="stat-label">Completed</div>
                <div class="stat-value" id="completed-count">0</div>
            </div>
            <div class="stat-card failed">
                <div class="stat-label">Failed</div>
                <div class="stat-value" id="failed-count">0</div>
            </div>
        </div>

        <div class="downloads" id="downloads-container">
            <div class="no-downloads">
                <div class="no-downloads-icon">...</div>
                <h3>No downloads yet</h3>
                <p>Downloads will appear here when you start a download</p>
            </div>
        </div>
    </div>

    <button class="refresh-btn" onclick="loadDownloads()">
        Refresh
        <span class="auto-refresh">Auto-refresh: 3s</span>
    </button>

    <script>
        function formatDate(isoString) {
            const date = new Date(isoString);
            return date.toLocaleString();
        }

        function formatDuration(created, updated) {
            const start = new Date(created);
            const end = new Date(updated);
            const seconds = Math.floor((end - start) / 1000);
            if (seconds < 60) return seconds + 's';
            const minutes = Math.floor(seconds / 60);
            if (minutes < 60) return minutes + 'm ' + (seconds % 60) + 's';
            const hours = Math.floor(minutes / 60);
            return hours + 'h ' + (minutes % 60) + 'm';
        }

        function renderDownloads(data) {
            document.getElementById('total-count').textContent = data.total || 0;

            var stats = { pending: 0, in_progress: 0, completed: 0, failed: 0 };
            (data.downloads || []).forEach(function(d) {
                stats[d.status] = (stats[d.status] || 0) + 1;
            });

            document.getElementById('pending-count').textContent = stats.pending;
            document.getElementById('in-progress-count').textContent = stats.in_progress;
            document.getElementById('completed-count').textContent = stats.completed;
            document.getElementById('failed-count').textContent = stats.failed;

            var container = document.getElementById('downloads-container');

            if (!data.downloads || data.downloads.length === 0) {
                container.innerHTML =
                    '<div class="no-downloads">' +
                    '<div class="no-downloads-icon">...</div>' +
                    '<h3>No downloads yet</h3>' +
                    '<p>Downloads will appear here when you start a download</p>' +
                    '</div>';
                return;
            }

            var downloads = data.downloads.slice().sort(function(a, b) {
                return new Date(b.created_at) - new Date(a.created_at);
            });

            container.innerHTML = downloads.map(function(download) {
                var plat = (download.platform || '').toUpperCase();
                var type = download.item_type || '';
                var artist = download.artist || '';
                var album = download.album_title || '';
                var track = download.track_title || '';
                var titleLine;
                if (type === 'album') {
                    var main = (artist && album) ? (artist + ' — ' + album) : (album || track || download.item_id);
                    titleLine = plat + ' • Album • ' + main;
                } else if (type === 'track') {
                    var main2 = (artist && track) ? (artist + ' — ' + track) : (track || download.item_id);
                    titleLine = plat + ' • Track • ' + main2;
                } else {
                    titleLine = plat + ' • ' + type + ' • ' + download.item_id;
                }

                var progressHtml = '';
                if (download.status === 'in_progress') {
                    var progressText;
                    var downloaded = download.downloaded_items;
                    var total = download.total_items;
                    if (total && total > 1) {
                        if (downloaded !== null && downloaded !== undefined) {
                            progressText = downloaded + '/' + total + ' tracks';
                        } else {
                            progressText = '0/' + total + ' tracks';
                        }
                    } else {
                        progressText = 'Downloading...';
                    }
                    progressHtml =
                        '<div class="progress-row">' +
                        '<div class="progress-bar" style="flex: 1;">' +
                        '<div class="progress-fill progress-animated" style="width: 100%"></div>' +
                        '</div>' +
                        '<div class="progress-text">' + progressText + '</div>' +
                        '</div>';
                }

                var errorHtml = '';
                if (download.error) {
                    errorHtml =
                        '<div class="error-message">' +
                        '<strong>Error:</strong> ' + download.error +
                        '</div>';
                }

                var fileHtml = '';
                if (download.file_path) {
                    fileHtml =
                        '<div class="file-path">' + download.file_path + '</div>';
                }

                var totalItemsHtml = '';
                if (download.total_items) {
                    totalItemsHtml =
                        '<div class="info-item">' +
                        '<div class="info-label">Total Items</div>' +
                        '<div class="info-value">' + download.total_items + '</div>' +
                        '</div>';
                }

                return (
                    '<div class="download-item">' +
                    '<div class="download-header">' +
                    '<div><div class="title-line">' + titleLine + '</div></div>' +
                    '<span class="status-badge status-' + download.status + '">' +
                    download.status.replace('_', ' ') +
                    '</span>' +
                    '</div>' +
                    '<div class="download-info">' +
                    '<div class="info-item">' +
                    '<div class="info-label">Download ID</div>' +
                    '<div class="info-value download-id">' + download.id + '</div>' +
                    '</div>' +
                    '<div class="info-item">' +
                    '<div class="info-label">Item ID</div>' +
                    '<div class="info-value">' + download.item_id + '</div>' +
                    '</div>' +
                    totalItemsHtml +
                    '<div class="info-item">' +
                    '<div class="info-label">Created</div>' +
                    '<div class="info-value">' + formatDate(download.created_at) + '</div>' +
                    '</div>' +
                    '<div class="info-item">' +
                    '<div class="info-label">Duration</div>' +
                    '<div class="info-value">' + formatDuration(download.created_at, download.updated_at) + '</div>' +
                    '</div>' +
                    '</div>' +
                    progressHtml +
                    errorHtml +
                    fileHtml +
                    '</div>'
                );
            }).join('');
        }

        async function loadDownloads() {
            try {
                var response = await fetch('/api/downloads');
                var data = await response.json();
                renderDownloads(data);
            } catch (error) {
                console.error('Failed to load downloads:', error);
            }
        }

        loadDownloads();
        setInterval(loadDownloads, 3000);
    </script>
</body>
</html>
"""


class DownloadStatusHandler(BaseHTTPRequestHandler):
    """HTTP request handler for download status UI."""

    def log_message(self, format, *args):
        pass

    def _send(self, code: int, content_type: str, body: bytes, no_cache: bool = False):
        """Send a complete HTTP response."""
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        if no_cache:
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path

        if path in ("/", "/downloads"):
            self._send(200, "text/html; charset=utf-8", HTML_TEMPLATE.encode("utf-8"), no_cache=True)

        elif path == "/api/downloads":
            try:
                data = read_downloads_from_file()
                self._send(200, "application/json", json.dumps(data).encode("utf-8"), no_cache=True)
            except Exception as e:
                self._send(500, "application/json", json.dumps({"error": str(e)}).encode("utf-8"))

        else:
            self._send(404, "text/plain", b"Not Found")


def main():
    parser = argparse.ArgumentParser(description="HiFi Download Dashboard")
    parser.add_argument("--port", type=int, default=8765, help="Port to listen on (default: 8765)")
    parser.add_argument("--no-open", action="store_true", help="Do not auto-open browser")
    args = parser.parse_args()

    host = "127.0.0.1"
    port = args.port
    server = None
    for attempt in range(10):
        try:
            server = ThreadingHTTPServer((host, port), DownloadStatusHandler)
            break
        except OSError:
            port += 1
    if server is None:
        print(f"Error: could not find an available port (tried {args.port}-{port})", file=sys.stderr)
        sys.exit(1)
    url = f"http://{host}:{port}"

    def shutdown_handler(sig, frame):
        print("\nShutting down...")
        server.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    print(f"HiFi Download Dashboard running at {url}")
    print(f"State file: {STATE_FILE}")
    print("Press Ctrl+C to stop")
    sys.stdout.flush()

    if not args.no_open:
        # Open browser in a thread so it doesn't block server startup
        from threading import Timer
        Timer(0.5, webbrowser.open, args=[url]).start()

    server.serve_forever()


if __name__ == "__main__":
    main()
