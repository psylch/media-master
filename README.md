# media-master

[中文文档](README.zh.md)

All-in-one media acquisition toolkit for [Claude Code](https://docs.anthropic.com/en/docs/claude-code). Bundles three specialized download skills into a single install.

| Skill | What It Does | Services |
|-------|-------------|----------|
| **hifi-download** | Music discovery & Hi-Res audio downloads | Spotify, Last.fm, Qobuz, TIDAL |
| **quark-download** | Cloud drive resource search & save | PanSou, Quark APP |
| **zlib-download** | Book search & download | Z-Library, Anna's Archive |

## Installation

### Via skills.sh (recommended)

```bash
# Install all three skills at once
npx skills add psylch/media-master -g -y
```

### Via Claude Code Plugin Marketplace

```shell
/plugin marketplace add psylch/media-master
/plugin install media-master@psylch-media-master
```

### Install individually

Each skill can also be installed standalone:

```bash
npx skills add psylch/hifi-download-skill -g -y
npx skills add psylch/quark-download-skill -g -y
npx skills add psylch/zlib-download-skill -g -y
```

Restart Claude Code after installation.

## Usage

After installation, the skills activate automatically based on your prompts:

```
# Music
find music like Radiohead
download album in Hi-Res FLAC

# Cloud drive resources
搜资源 星际穿越
帮我找片 4K

# Books
find book "Deep Learning"
搜书 三体
```

## Architecture

This repo uses **git submodules** to bundle three independent skill repos:

```
media-master/
├── hifi-download-skill/    → github.com/psylch/hifi-download-skill
├── quark-download-skill/   → github.com/psylch/quark-download-skill
├── zlib-download-skill/    → github.com/psylch/zlib-download-skill
└── skills/                 → symlinks to submodule skills
```

Each skill is maintained independently and can be installed/updated separately.

## License

MIT
