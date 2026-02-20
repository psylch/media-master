# HiFi Download - Script Reference

Complete reference for all scripts. Run with `bash ${SKILL_PATH}/run.sh <script_name> [args]`.

## Contents

- Script Overview
- Spotify Scripts
- Last.fm Scripts
- Platform Scripts
- Utility Scripts
- Workflows

---

## Script Overview

### System Scripts

| Script | Purpose |
|--------|---------|
| `status.py` | Check all service status (run first!) |
| `setup_config.py` | Configure API credentials |
| `disable_service.py` | Disable a service explicitly |
| `enable_service.py` | Re-enable a disabled service |
| `verify_setup.py` | Verify configured services work |
| `spotify_auth.py` | Complete Spotify OAuth |
| `tidal_auth.py` | Complete TIDAL OAuth (uses tiddl) |

### Feature Scripts

| Script | Purpose | Required Config |
|--------|---------|-----------------|
| `spotify_search.py` | Search Spotify | Spotify |
| `spotify_info.py` | Get item details | Spotify |
| `spotify_user.py` | User listening history | Spotify (OAuth) |
| `lastfm_artists.py` | Similar artists | Last.fm |
| `lastfm_tracks.py` | Similar tracks | Last.fm |
| `lastfm_taste.py` | Personalized recommendations | Spotify + Last.fm |
| `platform_search.py` | Search Qobuz/TIDAL | Qobuz or TIDAL |
| `platform_download.py` | Download Hi-Res | Qobuz or TIDAL |

---

## Spotify Scripts

### spotify_search.py

Search for music on Spotify.

```bash
bash ${SKILL_PATH}/run.sh spotify_search "query" [options]
```

**Options:**
- `-t, --type`: track, album, artist, playlist (default: track)
- `-l, --limit`: Number of results (default: 10)
- `-m, --market`: Market code (default: US)
- `--detailed`: Show full details

**Examples:**
```bash
bash ${SKILL_PATH}/run.sh spotify_search "Karma Police"
bash ${SKILL_PATH}/run.sh spotify_search "OK Computer" -t album
bash ${SKILL_PATH}/run.sh spotify_search "Radiohead" -t artist --detailed
```

### spotify_info.py

Get detailed information about a Spotify item.

```bash
bash ${SKILL_PATH}/run.sh spotify_info <item_id> -t <type>
```

**Options:**
- `-t, --type`: track, album, artist (required)
- `--concise`: Show brief output

### spotify_user.py

Get user's listening history. Requires OAuth authorization (browser opens on first use).

```bash
bash ${SKILL_PATH}/run.sh spotify_user <tracks|artists> [options]
```

**Options:**
- `-r, --range`: short_term (~4 weeks), medium_term (~6 months), long_term (years)
- `-l, --limit`: Number of results (default: 20)
- `--detailed`: Show full details

**Examples:**
```bash
bash ${SKILL_PATH}/run.sh spotify_user tracks
bash ${SKILL_PATH}/run.sh spotify_user artists -r short_term
bash ${SKILL_PATH}/run.sh spotify_user tracks -r long_term -l 50
```

---

## Last.fm Scripts

### lastfm_artists.py

Find artists similar to a given artist.

```bash
bash ${SKILL_PATH}/run.sh lastfm_artists "Artist Name" [options]
```

**Options:**
- `-l, --limit`: Number of results (default: 10)
- `--detailed`: Show URLs and MBIDs

### lastfm_tracks.py

Find tracks similar to a given track.

```bash
bash ${SKILL_PATH}/run.sh lastfm_tracks "Track Name" "Artist Name" [options]
```

**Options:**
- `-l, --limit`: Number of results (default: 10)
- `--detailed`: Show full details

### lastfm_taste.py

Get personalized recommendations based on Spotify listening history. This is the most powerful discovery tool — combines Spotify history with Last.fm's global listening data.

```bash
bash ${SKILL_PATH}/run.sh lastfm_taste [options]
```

**Options:**
- `-r, --range`: Time range for history (default: medium_term)
- `-n, --per-item`: Recommendations per seed (default: 5)

---

## Platform Scripts

### platform_search.py

Search for Hi-Res music on Qobuz or TIDAL.

```bash
bash ${SKILL_PATH}/run.sh platform_search "query" -p <platform> [options]
```

**Options:**
- `-p, --platform`: qobuz or tidal (required)
- `-t, --type`: track, album, artist (default: album)
- `-l, --limit`: Number of results (default: 10)

### platform_download.py

Download music from Qobuz or TIDAL in lossless quality.

```bash
bash ${SKILL_PATH}/run.sh platform_download <item_id> -p <platform> [options]
```

**Options:**
- `-p, --platform`: qobuz or tidal (required)
- `-t, --type`: track or album (default: album)
- `-o, --output`: Custom output path
- `-q, --quiet`: Suppress progress output

**Quality:**
- Qobuz: Up to 24-bit/192kHz (configured via QOBUZ_QUALITY)
- TIDAL: Up to 24-bit (configured via TIDAL_QUALITY)

---

## System Scripts

### status.py

**IMPORTANT: Run this at the start of every session.**

```bash
bash ${SKILL_PATH}/run.sh status [--json]
```

The `--json` flag outputs machine-readable JSON for programmatic use.

### disable_service.py / enable_service.py

```bash
bash ${SKILL_PATH}/run.sh disable_service spotify --reason "No account"
bash ${SKILL_PATH}/run.sh enable_service spotify
```

Preferences are persisted in `.preferences.json`.

### verify_setup.py

More thorough than `status.py` — tests actual API connections.

```bash
bash ${SKILL_PATH}/run.sh verify_setup
```

---

## Workflows

### Discover New Music

1. Check your taste: `bash ${SKILL_PATH}/run.sh spotify_user artists -r medium_term`
2. Get recommendations: `bash ${SKILL_PATH}/run.sh lastfm_taste`
3. Explore specific artist: `bash ${SKILL_PATH}/run.sh lastfm_artists "Discovered Artist"`

### Download Hi-Res Album

1. Search: `bash ${SKILL_PATH}/run.sh platform_search "Album Name" -p qobuz`
2. Note the ID from search results
3. Download: `bash ${SKILL_PATH}/run.sh platform_download <ID> -p qobuz -t album`

### Find Similar Music

1. Similar artists: `bash ${SKILL_PATH}/run.sh lastfm_artists "Artist You Like"`
2. Similar tracks: `bash ${SKILL_PATH}/run.sh lastfm_tracks "Song You Like" "Artist"`
3. Preview on Spotify: `bash ${SKILL_PATH}/run.sh spotify_search "Discovered Song" -t track --detailed`
