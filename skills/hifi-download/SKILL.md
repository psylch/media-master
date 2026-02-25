---
name: hifi-download
description: Discover music, get personalized recommendations, and download high-fidelity audio files. Use when user wants to find new music based on their taste, search for songs/albums/artists, get recommendations similar to artists they like, or download lossless audio (FLAC/Hi-Res) from Qobuz or TIDAL. Trigger phrases include "find music like", "recommend songs", "download album", "lossless", "Hi-Res", "FLAC", "music discovery", "similar artists", "setup music".
---

# MusicMaster

Music discovery (Spotify, Last.fm) and Hi-Res audio downloads (Qobuz, TIDAL) through a unified CLI.

## Language
**Match user's language**: Respond in the same language the user uses.

All commands use `bash ${SKILL_PATH}/run.sh <script> [args...]`, which activates the venv and runs the corresponding Python script. Output is human-readable by default; use `--json` where supported for structured output.

## First-Time Setup

### Step 1: Check Dependencies

```bash
bash ${SKILL_PATH}/scripts/setup.sh check
```

Output is key=value pairs. If `VENV=missing`, run install first.

### Step 2: Install

```bash
bash ${SKILL_PATH}/scripts/setup.sh install [--with-qobuz] [--with-tidal]
```

Creates `.venv`, installs core dependencies (`spotipy`, `pylast`, `requests`, `python-dotenv`), and optionally installs download backends.

### Step 3: Configure Credentials

**IMPORTANT**: Do NOT ask the user for credentials in chat. Instead:
1. Create `.env` from template if not exists: `cp ${SKILL_PATH}/.env.example ${SKILL_PATH}/.env`
2. Tell user to edit `${SKILL_PATH}/.env` with their credentials
3. Wait for confirmation, then verify with Step 4

**Where to get credentials:**
- Spotify: https://developer.spotify.com/dashboard (free)
- Last.fm: https://www.last.fm/api/account/create (free)
- Qobuz: Requires Studio/Sublime subscription
- TIDAL: Run `tiddl auth login` in venv for OAuth (no `.env` entry needed)

### Step 4: Verify

```bash
bash ${SKILL_PATH}/run.sh status
```

Shows which services are **READY**, **DISABLED**, or **need setup**. **Only use services marked READY.**

### Preflight Check → Fix Table

| Check | Fix (macOS) | Fix (Linux) |
|-------|-------------|-------------|
| `PYTHON=missing` | `brew install python3` | `sudo apt install python3` |
| `VENV=missing` | `bash ${SKILL_PATH}/scripts/setup.sh install` | Same |
| Core deps missing (SPOTIPY, PYLAST, etc.) | `bash ${SKILL_PATH}/scripts/setup.sh install --force` | Same |
| `ENV_FILE=missing` | `cp ${SKILL_PATH}/.env.example ${SKILL_PATH}/.env` then edit | Same |
| Spotify: NOT CONFIGURED | Edit `.env`: set `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` | Same |
| Last.fm: NOT CONFIGURED | Edit `.env`: set `LASTFM_API_KEY` | Same |
| Qobuz: NOT CONFIGURED | Edit `.env`: set `QOBUZ_EMAIL` and `QOBUZ_PASSWORD` | Same |
| TIDAL: NOT CONFIGURED | Run `tiddl auth login` inside the venv | Same |
| Spotify/Last.fm/Qobuz: ERROR (validation failed) | Check credentials in `.env` are correct, re-obtain from dashboard if needed | Same |
| TIDAL: ERROR (token expired) | Run `tiddl auth refresh` or `tiddl auth login` inside the venv | Same |

## Service Types

| Type | Services | Purpose |
|------|----------|---------|
| Discovery | Spotify, Last.fm | Search, recommendations, similar artists |
| Downloads | Qobuz, TIDAL | High-quality audio (FLAC, Hi-Res) |

## Degradation Strategy

All 4 services (Spotify, Last.fm, Qobuz, TIDAL) are optional. After running `status`, apply this table:

| Scenario | Strategy |
|----------|----------|
| No Last.fm | **Skip & continue** — Use Spotify only for discovery |
| No Spotify | **Skip & continue** — Use Last.fm only for discovery |
| No discovery services at all | **Halt & guide** — Tell user at least one discovery service is needed and guide setup |
| No Qobuz | **Auto-fallback** — Use TIDAL for downloads |
| No TIDAL | **Auto-fallback** — Use Qobuz for downloads |
| No download services at all | **Discovery only** — Inform user that downloads are unavailable, continue with discovery features only |

When a fallback is used, tell the user which service is being used and why.

## Discovery Commands

### Last.fm — Similar Artists

```bash
bash ${SKILL_PATH}/run.sh lastfm_artists "Radiohead"
```

Returns a list of similar artists with match scores.

### Last.fm — Similar Tracks

```bash
bash ${SKILL_PATH}/run.sh lastfm_tracks "Karma Police" "Radiohead"
```

Arguments: track name, then artist name.

### Last.fm — Taste Profile

```bash
bash ${SKILL_PATH}/run.sh lastfm_taste
```

Returns the user's top artists and tracks from listening history.

### Spotify — Search

```bash
bash ${SKILL_PATH}/run.sh spotify_search "OK Computer"
```

Searches Spotify catalog for tracks, albums, and artists.

### Spotify — User Library

```bash
bash ${SKILL_PATH}/run.sh spotify_user tracks|artists
```

Gets the user's saved tracks or followed artists (requires OAuth).

### Spotify — Track/Album Info

```bash
bash ${SKILL_PATH}/run.sh spotify_info SPOTIFY_URI_OR_ID
```

## Download Commands

### Search Platform Catalog

```bash
bash ${SKILL_PATH}/run.sh platform_search "Album Name" -p qobuz|tidal
```

Searches the download platform's catalog. Returns IDs for use with download command.

### Download (async — returns immediately)

```bash
bash ${SKILL_PATH}/run.sh platform_download ID -p qobuz|tidal -t album|track
```

Queues the download in a background process and returns a `download_id` immediately. The agent is free to continue other work. Use `download_status` to poll progress.

To block until the download completes (legacy behavior):

```bash
bash ${SKILL_PATH}/run.sh platform_download ID -p qobuz -t album --sync
```

### Check Download Status

```bash
bash ${SKILL_PATH}/run.sh download_status DOWNLOAD_ID
bash ${SKILL_PATH}/run.sh download_status --all
bash ${SKILL_PATH}/run.sh download_status --active
bash ${SKILL_PATH}/run.sh download_status --json
```

Poll the status of a specific download or list all downloads. Use `--active` to show only pending/in_progress tasks. Use `--json` for structured output.

### Open Download Dashboard

```bash
bash ${SKILL_PATH}/run.sh download_ui
```

Opens a web dashboard at `http://localhost:8765` showing real-time download status with progress bars. Auto-refreshes every 3 seconds.

## Service Management

### Disable a Service

```bash
bash ${SKILL_PATH}/run.sh disable_service spotify --reason "No account"
```

### Enable a Service

```bash
bash ${SKILL_PATH}/run.sh enable_service spotify
```

## Workflow — Music Discovery

1. Run `status` to check available services
2. Use `lastfm_artists` or `lastfm_tracks` to find similar music
3. Use `spotify_search` to look up specific tracks/albums
4. Present results to user in a clear table format
5. If user wants to download, use `platform_search` → `platform_download`

## Workflow — Download Hi-Res Audio

Print this checklist at the start, update as you go:

```
Download Progress:
- [ ] Step 1: Check service status
- [ ] Step 2: Search platform catalog
- [ ] Step 3: Present results to user
- [ ] Step 4: Start download
- [ ] Step 5: Monitor progress
- [ ] Step 6: Verify completion
- [ ] Step 7: Report results
```

1. Run `status` to confirm download service is READY
2. Search: `platform_search "Album Name" -p qobuz`
3. Present results with quality info
4. Download: `platform_download ID -p qobuz -t album` (returns download_id immediately)
5. Tell user download is queued, optionally open `download_ui` for visual monitoring
6. Poll with `download_status DOWNLOAD_ID` until completed
7. Report using the completion report template below

## Completion Report

After a download finishes, present this report to the user:

```
MusicMaster Download Complete!

Input: [album/track] - [title] by [artist]
Platform: [Qobuz/TIDAL]
Quality: [Hi-Res 24-bit / FLAC 16-bit / etc.]

Result:
- Track count: [N tracks]
- Total size: [X MB]
- Download path: [/path/to/files]

Files:
- [file1.flac] (XX MB)
- [file2.flac] (XX MB)
- ...

Next Steps:
- Open folder: open "[download path]"
- Download more: "download [another album]"
```

Gather file paths and sizes from the `download_status` output and by listing the download directory.

## Error Handling

| Error | Detection | Resolution |
|-------|-----------|------------|
| Venv missing | `run.sh` exits with `venv_missing` | Run `bash ${SKILL_PATH}/scripts/setup.sh install` |
| Service not configured | `status` shows `NOT CONFIGURED` | Guide user to edit `${SKILL_PATH}/.env` (see Preflight Check -> Fix Table) |
| Spotify OAuth expired | Spotify commands fail with auth error | Run `bash ${SKILL_PATH}/run.sh spotify_auth` to re-authorize |
| TIDAL token expired | `status` shows `ERROR` for TIDAL | Run `tiddl auth refresh` or `tiddl auth login` in venv |
| Service disabled by user | `status` shows `DISABLED` | Run `enable_service` if user wants to re-enable |
| No results | Search returns empty | Try different keywords or check service availability |

## Important Notes

- Spotify requires OAuth browser flow on first use (`spotify_auth` script handles this)
- TIDAL auth is managed by `tiddl` CLI tool, not stored in `.env`
- Qobuz credentials are stored in `.env` (sensitive — ensure file is in `.gitignore`)
- Download paths default to `~/Music/Qobuz` and `~/Music/TIDAL`
- Quality settings: Qobuz 27=Hi-Res 24-bit (highest), TIDAL HiFi=lossless
