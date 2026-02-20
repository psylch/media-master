# media-master

[English](README.md)

一站式媒体资源获取工具包，适用于 [Claude Code](https://docs.anthropic.com/en/docs/claude-code)。将三个专用下载技能打包为一次安装。

| 技能 | 功能 | 服务 |
|------|------|------|
| **hifi-download** | 音乐发现 & 无损音频下载 | Spotify, Last.fm, Qobuz, TIDAL |
| **quark-download** | 网盘资源搜索 & 保存 | PanSou 盘搜, 夸克 APP |
| **zlib-download** | 书籍搜索 & 下载 | Z-Library, Anna's Archive |

## 安装

### 通过 skills.sh（推荐）

```bash
# 一次安装全部三个技能
npx skills add psylch/media-master -g -y
```

### 通过 Claude Code Plugin Marketplace

```shell
/plugin marketplace add psylch/media-master
/plugin install media-master@psylch-media-master
```

### 单独安装

每个技能也可以独立安装：

```bash
npx skills add psylch/hifi-download-skill -g -y
npx skills add psylch/quark-download-skill -g -y
npx skills add psylch/zlib-download-skill -g -y
```

安装后需重启 Claude Code。

## 使用方法

安装后，技能会根据你的提示自动激活：

```
# 音乐
帮我找类似 Radiohead 的音乐
下载 Hi-Res FLAC 专辑

# 网盘资源
搜资源 星际穿越
帮我找片 4K

# 书籍
find book "Deep Learning"
搜书 三体
```

## 架构

本 repo 使用 **git submodules** 整合三个独立的技能仓库：

```
media-master/
├── hifi-download-skill/    → github.com/psylch/hifi-download-skill
├── quark-download-skill/   → github.com/psylch/quark-download-skill
├── zlib-download-skill/    → github.com/psylch/zlib-download-skill
└── skills/                 → 指向子模块技能的 symlinks
```

每个技能独立维护，可单独安装/更新。

## 许可证

MIT
