# HiFi Download Setup Guide

## Quick Start

```bash
# 1. Install dependencies (creates .venv automatically)
bash ${SKILL_PATH}/scripts/setup.sh install --with-qobuz --with-tidal

# 2. Configure credentials (edit .env file)
cp ${SKILL_PATH}/.env.example ${SKILL_PATH}/.env
# Then edit .env with your credentials

# 3. Verify
bash ${SKILL_PATH}/run.sh status
```

After setup:
```bash
bash ${SKILL_PATH}/run.sh spotify_search "Radiohead"
bash ${SKILL_PATH}/run.sh lastfm_taste
```

---

## Manual Setup

### Step 1: Create Virtual Environment

```bash
python3 -m venv ${SKILL_PATH}/.venv
source ${SKILL_PATH}/.venv/bin/activate
```

### Step 2: Install Dependencies

```bash
# Core (required)
pip install spotipy pylast requests python-dotenv

# Qobuz downloads (optional)
pip install qobuz-dl

# TIDAL downloads (optional, uses tiddl)
pip install tiddl
```

### Step 3: Configure API Credentials

Copy `.env.example` to `.env` and fill in credentials:

```bash
cp ${SKILL_PATH}/.env.example ${SKILL_PATH}/.env
```

Then edit `${SKILL_PATH}/.env` with your credentials.

### Step 4: Complete Spotify OAuth

```bash
bash ${SKILL_PATH}/run.sh spotify_user tracks
```

A browser window will open. Log in and authorize the app.

### Step 5: Verify

```bash
bash ${SKILL_PATH}/run.sh verify_setup
```

---

## Getting API Credentials

### Spotify (Free account + API credentials)

1. Go to https://developer.spotify.com/dashboard
2. Log in with your Spotify account
3. Click "Create App"
   - App name: anything (e.g., "HiFiDownload")
   - App description: anything
   - Redirect URI: `http://127.0.0.1:8888/callback`
4. After creating, click "Settings"
5. Copy **Client ID** and **Client Secret**

### Last.fm (Free API key)

1. Go to https://www.last.fm/api/account/create
2. Fill in:
   - Application name: anything
   - Application description: anything
   - Application homepage: can leave blank
   - Callback URL: can leave blank
3. Submit and copy the **API Key**

### Qobuz (Requires Studio/Sublime subscription)

Just use your regular Qobuz login email and password.

**Quality options:**
| Value | Format |
|-------|--------|
| 5 | MP3 320kbps |
| 6 | FLAC 16-bit/44.1kHz (CD quality) |
| 7 | FLAC 24-bit up to 96kHz |
| 27 | FLAC 24-bit up to 192kHz (Hi-Res) |

### TIDAL (Requires HiFi+ subscription)

TIDAL uses OAuth device code flow. After installing `tiddl`, run:

```bash
tiddl auth login
```

This shows a URL - open it in browser, log in to TIDAL, and authorize.
Token is saved to `~/tiddl.json`.

**Quality options (set in ~/tiddl.json or via CLI):**
| Value | Format |
|-------|--------|
| low | AAC 96kbps |
| normal | AAC 320kbps |
| high | FLAC 16-bit/44.1kHz (CD quality) |
| master | FLAC 24-bit up to 192kHz (MQA/Hi-Res) |

---

## Troubleshooting

### "No module named 'spotipy'"

Virtual environment not set up. Run:
```bash
bash ${SKILL_PATH}/scripts/setup.sh install
```

### "Spotify not configured"

Missing or incorrect credentials in `.env` file. Check:
- `SPOTIFY_CLIENT_ID` is set
- `SPOTIFY_CLIENT_SECRET` is set
- No extra spaces or quotes around values

### "Last.fm API error"

Check that `LASTFM_API_KEY` is correct (32 characters, no spaces).

### "Qobuz: Free accounts not eligible"

Qobuz downloads require a paid subscription (Studio or Sublime).

### "TIDAL not authenticated"

Run `tiddl auth login` to complete OAuth authentication.
Token is stored in `~/tiddl.json`.

### Spotify OAuth keeps asking for authorization

The token cache may be corrupted. Delete `.cache` file in the skill directory and try again:
```bash
rm ${SKILL_PATH}/.cache
```
