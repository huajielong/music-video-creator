<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-blue" alt="v1.0"/>
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT"/>
  <img src="https://img.shields.io/badge/python-3.10+-orange" alt="Python 3.10+"/>
  <img src="https://img.shields.io/github/stars/huajielong/music-video-creator?style=social" alt="Stars"/>
  <img src="https://img.shields.io/badge/AI-Mureka%20%7C%20Seedream%20%7C%20Whisper-purple" alt="AI Stack"/>
  <img src="https://img.shields.io/badge/GPU-Not%20Required-brightgreen" alt="No GPU Required"/>
</p>

<h1 align="center">🎬 Music Video Creator</h1>
<p align="center"><b>AI-Powered Music Video Creation Tool — Fully Automatic from Lyrics to MV</b></p>
<p align="center">
  🎵 AI Composition · 🎨 Storyboard Generation · 🖼️ Batch Media · 📝 Subtitle Sync
</p>

<p align="center">
  <a href="#-quick-start">🚀 Quick Start</a> •
  <a href="#-step-by-step">📖 Step-by-Step</a> •
  <a href="#-script-overview">🧩 Scripts</a> •
  <a href="#-features">🛠️ Features</a> •
  <a href="#-faq">❓ FAQ</a>
</p>

---

## 🤔 From Lyrics to MV: How Many Steps?

Traditional MV production requires composition, recording, filming, editing, subtitles... It's costly and time-consuming:

| Challenges You May Face | Music Video Creator Solves It |
|:------------------------|:------------------------------|
| ❓ Can't compose music | ✅ **AI Composition** — Mureka V9 generates songs directly from lyrics |
| ❓ No filming crew | ✅ **AI Visual Generation** — Seedream 5.0 batch generates images/videos |
| ❓ Manual subtitle timing is tedious | ✅ **Whisper Auto-Alignment** — Precisely matches lyrics to audio |
| ❓ Media processing workflow is cumbersome | ✅ **One-Click Pipeline** — From lyrics to finished MV, fully automatic |
| ❓ No GPU to run | ✅ **Pure Cloud APIs** — Runs on any laptop |

---

## 🚀 Quick Start

```bash
# 1. Clone and install
git clone https://github.com/huajielong/music-video-creator.git
cd music-video-creator
pip install -r requirements.txt
playwright install chromium

# 2. Set API keys
cp .env.example .env

# 3. Generate a full music video
python scripts/pipeline.py \
  --title "My Song" \
  --prompt "pop, female vocal, energetic" \
  --lyrics "[Verse 1]\nYour lyrics here..." \
  --model mureka_v9
```

> **No GPU required.** Everything runs via cloud APIs. A laptop is enough.

### Prerequisites

| Requirement | Why |
|------------|-----|
| **Python 3.10+** | Scripts require 3.10+ type hints |
| **FFmpeg** | Video assembly and audio analysis |
| **Tunee API key** | Music generation |
| **ARK API key** | Image/video generation |

---

## ✨ The Pipeline

```
Lyrics → Song → Storyboard → 30 Images → 30 Video Clips → Final MV with Subtitles
```

| Step | What happens | Time |
|:-----|:-------------|:----:|
| 1. ✍️ **Write lyrics** | Verse, Chorus, Bridge structure | 5 min |
| 2. ⚡ **pip install && setup** | One-command install | 2 min |
| 3. 🤖 **`python scripts/pipeline.py`** | Full auto pipeline | ~30 min |
| 4. ✅ **Get your MV** | MP4 with audio + subtitles | — |

---

## 📖 Step-by-Step

```bash
# 1. Generate music (Tunee API)
python scripts/generate.py --title "Song" --prompt "pop, female vocal" \
  --lyrics "[Verse]\nlyrics..." --model mureka_v9

# 2. Download MP3
python scripts/download.py --id <music_id>

# 3. Generate subtitles with Whisper alignment
python scripts/gen_srt.py --audio output/song.mp3 \
  --lyrics "[Verse]\nlyrics..." --output output/song.srt

# 4. Create storyboard
python scripts/gen_storyboard.py --title "Song" --style "cinematic, wuxia" \
  --output output/storyboard.md

# 5. Batch generate images (no watermark)
python scripts/batch_generate_images.py --watermark false

# 6. Batch generate videos
python scripts/batch_generate_videos.py --shots 1-30

# 7. Assemble final MV
python scripts/assemble.py --audio output/song.mp3 \
  --srt output/song.srt --output output/final.mp4
```

---

## 🧩 Scripts Overview

| Script | Purpose |
|:-------|:--------|
| `pipeline.py` | **End-to-end**: run all steps in sequence |
| `generate.py` | Generate music via Tunee API |
| `download.py` | Download MP3 from Tunee share page |
| `gen_srt.py` | **Generate SRT with Whisper-aligned subtitles** |
| `gen_storyboard.py` | Storyboard markdown + image prompts |
| `batch_generate_images.py` | Parallel image gen via Doubao Seedream |
| `batch_generate_videos.py` | Parallel video gen via Doubao Seedance |
| `assemble.py` | FFmpeg: concat videos + audio + burn subtitles |
| `validate.py` | Validate outputs: audio, images, videos, SRT |
| `list_models.py` | List available music models (cached 24h) |
| `credits.py` | Check Tunee account balance |

---

## 🛠️ Key Features

| Feature | Description |
|:--------|:------------|
| 🎵 **AI Music Generation** | Mureka V9 — compose songs from lyrics |
| 🖼️ **AI Image/Video** | Doubao Seedream 5.0 / Seedance 1.6 |
| 📝 **Whisper-aligned Subtitles** | Detects actual vocal timing in music mixes |
| 🔄 **Resume Support** | Skip existing files on re-run |
| ⚡ **Parallel Generation** | ThreadPoolExecutor for images/videos |
| 🔁 **Exponential Backoff** | Retries on timeout/server errors (5s → 10s → 20s) |
| 🛡️ **Content Moderation** | Auto-retry with safe prompts on rejection |

---

## ❓ FAQ

<details>
<summary><b>Need a GPU?</b></summary>
No! Everything runs via cloud APIs (Tunee, ARK/Doubao). A standard laptop is sufficient.
</details>

<details>
<summary><b>How long does it take?</b></summary>
A typical pipeline run (~30 image/video shots) completes in about 30 minutes, mostly waiting for cloud API responses.
</details>

<details>
<summary><b>What AI models are used?</b></summary>
Music: Mureka V9 via Tunee API. Images: Doubao Seedream 5.0 via ARK API. Videos: Doubao Seedance 1.6. Subtitles: Whisper (local).
</details>

<details>
<summary><b>Can I resume a failed run?</b></summary>
Yes. All scripts check for existing outputs and skip completed steps. Just re-run the same command.
</details>

---

## 🤝 Contributing

Contributions welcome — submit Issues, PRs, or improve documentation.

## 📄 License

MIT © [huajielong](https://github.com/huajielong)

---

<p align="center">
  ⭐ Star if this helps you create amazing MVs!
</p>

---

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-blue" alt="v1.0"/>
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT"/>
  <img src="https://img.shields.io/badge/python-3.10+-orange" alt="Python 3.10+"/>
  <img src="https://img.shields.io/github/stars/huajielong/music-video-creator?style=social" alt="Stars"/>
  <img src="https://img.shields.io/badge/AI-Mureka%20%7C%20Seedream%20%7C%20Whisper-purple" alt="AI Stack"/>
  <img src="https://img.shields.io/badge/GPU-Not%20Required-brightgreen" alt="No GPU Required"/>
</p>

<h1 align="center">🎵 Music Video Creator — AI驱动音乐视频创作</h1>
<p align="center"><b>从歌词到MV全自动生成，集成Mureka作曲/Seedream生图/Whisper字幕同步</b></p>
<p align="center">
  🎵 AI 作曲 · 🎨 故事板生成 · 🖼️ 批量素材 · 📝 字幕同步
</p>

<p align="center">
  <a href="#-快速开始">🚀 快速开始</a> •
  <a href="#-分步指南">📖 分步指南</a> •
  <a href="#-脚本说明">🧩 脚本说明</a> •
  <a href="#-核心功能">🛠️ 核心功能</a> •
  <a href="#-常见问题">❓ 常见问题</a>
</p>

---

## 🤔 从歌词到MV要多少步？

传统MV制作需要作曲、录音、拍摄、剪辑、字幕……成本高、流程长：

| 你可能遇到的问题 | Music Video Creator 帮你解决 |
|:-----------------|:---------------------------|
| ❓ 不会作曲编曲 | ✅ **AI 作曲** — Mureka V9 从歌词直接生成歌曲 |
| ❓ 没有拍摄团队 | ✅ **AI 生成画面** — Seedream 5.0 批量生成图片/视频 |
| ❓ 字幕手动卡点太累 | ✅ **Whisper 自动对齐** — 精准匹配歌词到音频 |
| ❓ 素材处理流程繁琐 | ✅ **一键 Pipeline** — 从歌词到成品 MV 全自动 |
| ❓ 没有 GPU 跑不动 | ✅ **纯云端 API** — 笔记本也能跑 |

---

## 🚀 快速开始

```bash
# 1. 克隆并安装
git clone https://github.com/huajielong/music-video-creator.git
cd music-video-creator
pip install -r requirements.txt
playwright install chromium

# 2. 设置 API 密钥
cp .env.example .env

# 3. 一键生成完整 MV
python scripts/pipeline.py \
  --title "我的歌曲" \
  --prompt "流行, 女声, 充满活力" \
  --lyrics "[主歌]\n你的歌词..." \
  --model mureka_v9
```

> **无需 GPU。** 所有流程通过云端 API 运行，普通笔记本电脑即可。

### 环境要求

| 依赖 | 说明 |
|:----|:-----|
| **Python 3.10+** | 脚本需要 3.10+ 类型注解支持 |
| **FFmpeg** | 视频合成和音频分析 |
| **Tunee API 密钥** | 音乐生成 |
| **ARK API 密钥** | 图片/视频生成 |

---

## ✨ 完整流程

```
歌词 → 歌曲 → 故事板 → 30张图片 → 30个视频片段 → 带字幕的最终MV
```

| 步骤 | 说明 | 耗时 |
|:----|:----|:----:|
| 1. ✍️ **写歌词** | 主歌、副歌、桥段结构 | 5 分钟 |
| 2. ⚡ **pip install && setup** | 一键安装 | 2 分钟 |
| 3. 🤖 **`python scripts/pipeline.py`** | 全自动流水线 | ~30 分钟 |
| 4. ✅ **获取你的 MV** | 带音频和字幕的 MP4 | — |

---

## 📖 分步指南

```bash
# 1. 生成音乐（Tunee API）
python scripts/generate.py --title "歌曲" --prompt "流行, 女声" \
  --lyrics "[主歌]\n歌词..." --model mureka_v9

# 2. 下载 MP3
python scripts/download.py --id <音乐ID>

# 3. 使用 Whisper 生成字幕
python scripts/gen_srt.py --audio output/song.mp3 \
  --lyrics "[主歌]\n歌词..." --output output/song.srt

# 4. 创建故事板
python scripts/gen_storyboard.py --title "歌曲" --style "电影感, 武侠" \
  --output output/storyboard.md

# 5. 批量生成图片（无水印）
python scripts/batch_generate_images.py --watermark false

# 6. 批量生成视频
python scripts/batch_generate_videos.py --shots 1-30

# 7. 合成最终 MV
python scripts/assemble.py --audio output/song.mp3 \
  --srt output/song.srt --output output/final.mp4
```

---

## 🧩 脚本说明

| 脚本 | 用途 |
|:----|:-----|
| `pipeline.py` | **一站式执行**：按顺序运行所有步骤 |
| `generate.py` | 通过 Tunee API 生成音乐 |
| `download.py` | 从 Tunee 分享页面下载 MP3 |
| `gen_srt.py` | **生成 Whisper 对齐字幕（SRT 格式）** |
| `gen_storyboard.py` | 生成故事板 Markdown 和图片提示词 |
| `batch_generate_images.py` | 通过豆包 Seedream 并行生成图片 |
| `batch_generate_videos.py` | 通过豆包 Seedance 并行生成视频 |
| `assemble.py` | FFmpeg：拼接视频 + 音频 + 硬字幕 |
| `validate.py` | 校验输出：音频、图片、视频、字幕 |
| `list_models.py` | 列出可用音乐模型（24小时缓存） |
| `credits.py` | 查询 Tunee 账户余额 |

---

## 🛠️ 核心功能

| 功能 | 说明 |
|:----|:-----|
| 🎵 **AI 音乐生成** | Mureka V9 — 从歌词直接创作歌曲 |
| 🖼️ **AI 图片/视频** | 豆包 Seedream 5.0 / Seedance 1.6 |
| 📝 **Whisper 对齐字幕** | 检测音乐混音中实际人声时机 |
| 🔄 **断点续传** | 重新运行时跳过已有文件 |
| ⚡ **并行生成** | 使用 ThreadPoolExecutor 并行处理图片/视频 |
| 🔁 **指数退避重试** | 超时/服务器错误自动重试（5秒 → 10秒 → 20秒） |
| 🛡️ **内容审核** | 被拒时自动以安全提示词重试 |

---

## ❓ 常见问题

<details>
<summary><b>需要 GPU 吗？</b></summary>
不需要！所有流程通过云端 API 运行（Tunee、ARK/豆包）。普通笔记本电脑即可。
</details>

<details>
<summary><b>需要多长时间？</b></summary>
一次典型的流水线运行（约30个图片/视频镜头）大约需要30分钟，主要是等待云端 API 响应。
</details>

<details>
<summary><b>使用了哪些 AI 模型？</b></summary>
音乐：通过 Tunee API 调用 Mureka V9。图片：通过 ARK API 调用豆包 Seedream 5.0。视频：豆包 Seedance 1.6。字幕：Whisper（本地运行）。
</details>

<details>
<summary><b>运行失败后可以继续吗？</b></summary>
可以。所有脚本会检查已有输出并跳过已完成步骤，只需重新运行相同命令即可。
</details>

---

## 🤝 贡献指南

欢迎贡献 —— 提交 Issue、PR 或改进文档。

## 📄 许可证

MIT © [huajielong](https://github.com/huajielong)

---

<p align="center">
  ⭐ 如果这个工具帮助你创作了精彩的 MV，请点个 Star！
</p>
