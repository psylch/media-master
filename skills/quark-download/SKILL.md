---
name: quark-download
description: Search, validate, and save cloud drive resources via PanSou aggregation API and local Quark desktop APP integration. This skill should be used when the user wants to find and download resources from cloud drives (网盘资源搜索下载), especially when they mention keywords like "搜资源", "找片", "下载", "网盘", "夸克", "quark", "panso", "盘搜". Requires Quark desktop APP running and logged in with membership.
---

# Quark Search — 网盘资源搜索与下载

## Language
**Match user's language**: Respond in the same language the user uses.

Automate the full workflow: search resources → validate links → save to Quark cloud drive → download locally, by combining the PanSou aggregation API with the local Quark desktop APP.

All operations use the CLI script at `${SKILL_PATH}/scripts/quark_search.py`. It outputs JSON to stdout (`{"status": "ok", "results": {...}, "hint": "..."}`) and errors to stderr (`{"error": "code", "message": "...", "hint": "...", "recoverable": true/false}`). Exit codes: 0 = success, 1 = recoverable error, 2 = fatal error.

## Preflight (MUST run first)

**Before any business command** (search, validate, save, etc.), run preflight:

```bash
python3 ${SKILL_PATH}/scripts/quark_search.py preflight
```

**Response:** Standardized JSON with `ready: true/false`, `dependencies`, and `services` status.

- If `ready: true` → proceed to workflow.
- If `ready: false` → follow the Check/Fix table below, then re-run preflight until it passes. **Do NOT proceed to search or save until preflight passes.**

| Check | Fix |
|-------|-----|
| Quark APP not running | Launch Quark desktop APP and wait a few seconds for it to start |
| Quark APP not logged in | Log in with membership account in the Quark APP |

> **Why gate on preflight?** Search itself works without Quark APP (it calls the PanSou web API), but `save` requires a running, logged-in Quark APP. Running preflight first prevents the frustrating experience of finding resources and then discovering you can't save them.

## Workflow — Quick Search (recommended)

**Prerequisite:** Preflight must have returned `ready: true`.

A single command searches PanSou, validates all links in parallel, and fetches file details for the top results:

```bash
python3 ${SKILL_PATH}/scripts/quark_search.py search "KEYWORD" --top 5
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--top N` | `5` | Number of top valid results to return with details |
| `--no-validate` | off | Skip validation (faster, but may include dead links) |
| `--limit N` | `30` | PanSou results per page |
| `--page N` | `1` | PanSou page number |

**Success response:**

```json
{
  "status": "ok",
  "hint": "Found 8 valid Quark links for '三体', returning top 5.",
  "results": {
    "keyword": "三体",
    "total": 1234,
    "valid_count": 8,
    "results": [
      {
        "pwd_id": "abc123def",
        "url": "https://pan.quark.cn/s/abc123def",
        "note": "三体全集 4K",
        "source": "plugin:libvio",
        "datetime": "2025-01-15",
        "stoken": "xxx",
        "detail": {
          "pwd_id": "abc123def",
          "pdir_fid": "0",
          "total": 3,
          "list": [
            {"file_name": "三体S01E01.mkv", "size": 4294967296, "dir": false, "fid": "f1"},
            {"file_name": "Extras", "size": 0, "dir": true, "fid": "f2", "include_items": 5}
          ]
        }
      }
    ]
  }
}
```

**Key fields:**
- `total` — total results across all drive types from PanSou
- `valid_count` — how many quark links passed validation
- `results[].pwd_id` — share ID for save command
- `results[].detail.list[]` — files/folders in the share
- `results[].detail.list[].dir` — `true` if folder (more reliable than file_type)
- `results[].detail.list[].fid` — use with `detail` command to browse subfolders

**No quark results:** When `results` is empty but `total` > 0, the response includes `type_counts` showing available results on other drive types. Report these to the user.

**Priority:** Always prioritize `quark` type results since the user has Quark membership. The script handles this automatically.

## Workflow — Step-by-step

**Prerequisite:** Preflight must have returned `ready: true`.

For granular control, use individual subcommands:

### Validate Links

```bash
python3 ${SKILL_PATH}/scripts/quark_search.py validate PWD_ID_OR_URL [...]
```

Accepts multiple pwd_ids or full share URLs. Returns validation status for each:

| `status` | Meaning | Action |
|----------|---------|--------|
| `valid` | Share is alive | Proceed. Response includes `stoken` for detail query |
| `expired` | Share expired (code 41004) | Skip, mark as expired |
| `not_exist` | Share deleted (code 41006) | Skip, mark as invalid |
| `error` | Other error | Skip |

### Get File Details

```bash
python3 ${SKILL_PATH}/scripts/quark_search.py detail PWD_ID --stoken STOKEN [--fid FID]
```

Fetches the file listing for a share. Use `--fid` to browse into a subfolder (pass the folder's `fid` from a previous detail response).

### Health Check

```bash
python3 ${SKILL_PATH}/scripts/quark_search.py health [--refresh]
```

Shows PanSou API status and the `channels`/`plugins` lists used for search. Health data is cached for 24 hours at `~/.cache/quark-search/health.json`. Use `--refresh` to force a fresh fetch.

## Present Results to User

Format results clearly:

```
搜索 "三体" 找到 X 个有效夸克网盘资源：

1. [有效] 三体全集 4K — 3个文件，来源: plugin:libvio
   https://pan.quark.cn/s/abc123
2. [有效] 三体 第一季 1080P — 1个文件夹(42项)，来源: channel:yunpanx
   https://pan.quark.cn/s/def456
3. [已失效] 三体合集 — 分享已过期
```

Ask the user which one to save.

## Save

**Requires Quark APP running and logged in.** Before attempting save, verify preflight has passed in this session. If unsure, re-run preflight.

When the user selects a resource, trigger the Quark APP to open the share link:

```bash
python3 ${SKILL_PATH}/scripts/quark_search.py save PWD_ID_OR_URL
```

The script tries three methods in order: `desktop_share_visiting` (preferred) → `desktop_caller` deeplink → browser fallback. The response indicates which method succeeded.

After a successful APP save (method `desktop_share_visiting` or `desktop_caller`), inform the user:

> 已在夸克 APP 中打开分享链接窗口。**注意：弹出的窗口可能很小，请留意任务栏/Dock 上的夸克图标。** 在 APP 中点击「保存到网盘」按钮完成保存。保存后文件会出现在你的网盘中，可以直接在 APP 中下载到本地。

If the response method is `browser_fallback`, open the URL in the browser instead and inform the user to save from the web page.

## Batch Processing

When the user wants to search and save multiple resources, loop through the search → present → save workflow for each keyword. Validate all links first via the `search` command, then trigger APP saves sequentially.

## Completion Report

After a successful save, present this summary to the user:

```
[Quark Download] Complete!
Resource: [title]
Share: [URL]
Method: [save method used]
→ Click "保存到网盘" in Quark APP to complete
```

## Error Handling

| Error | Detection | Resolution |
|-------|-----------|------------|
| Quark APP not running | `preflight` returns `ready: false`, service `not_running` | Tell user to launch Quark APP |
| Not logged in | `preflight` returns `ready: false`, hint mentions login | Tell user to log in |
| APP disconnected mid-session | `save` returns `app_not_running` error after preflight passed earlier | Re-run preflight; if it fails, tell user to restart Quark APP and log in again |
| No search results | `search` returns `total: 0` | Suggest different keywords |
| All links invalid | `search` returns `valid_count: 0` | Try alternative keywords or drive types |
| Share has password | `validate` returns password required error | Ask user for the extraction code (提取码) |
| PanSou API error | `search` returns `error: "pansou_error"` | Retry or try later |

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `localhost:9128 refused` | Quark APP not running | Launch Quark desktop APP |
| `preflight` passes but `save` fails | APP window minimized or hidden | Check taskbar/Dock for Quark icon, bring window to front |
| Search returns results but all invalid | Resources expired or removed | Try different keywords or broaden search terms |
| `pansou_error` on every search | PanSou API down or network issue | Wait and retry later; check network connectivity |
| `browser_fallback` method used | Quark APP local API not responding | Restart Quark APP; ensure it's the desktop version (not mobile) |
| Detail returns empty file list | Share requires extraction code (提取码) | Ask user for the code and re-validate with passcode |

## Important Notes

- All share validation APIs are public (no authentication needed)
- The local Quark APP API at `localhost:9128` requires no authentication
- The actual save-to-drive operation happens in the Quark APP UI (user clicks one button)
- Download-to-local is handled by Quark APP's built-in download manager
- Do not attempt to call Quark's authenticated remote APIs directly
