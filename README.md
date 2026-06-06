<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-blue" alt="v1.0"/>
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT"/>
  <img src="https://img.shields.io/badge/python-3.10+-orange" alt="Python 3.10+"/>
  <img src="https://img.shields.io/github/stars/huajielong/music-video-creator?style=social" alt="Stars"/>
  <img src="https://img.shields.io/badge/AI-Mureka%20%7C%20Seedream%20%7C%20Whisper-purple" alt="AI Stack"/>
  <img src="https://img.shields.io/badge/GPU-Not%20Required-brightgreen" alt="No GPU Required"/>
</p>

<h1 align="center">🎬 Music Video Creator</h1>
<p align="center"><b>AI 驱动的音乐视频创作工具 — 从歌词到 MV 全自动生成</b></p>
<p align="center">
  🎵 AI 作曲 · 🎨 故事板生成 · 🖼️ 批量素材 · 📝 字幕同步
</p>

<p align="center">
  <a href="#-quick-start">🚀 Quick Start</a> •
  <a href="#-step-by-step">📖 Step-by-Step</a> •
  <a href="#-script-overview">🧩 Scripts</a> •
  <a href="#-features">🛠️ Features</a> •
  <a href="#-faq">❓ FAQ</a>
</p>

---

## 🤔 从歌词到 MV 要多少步？

传统 MV 制作需要作曲、录音、拍摄、剪辑、字幕……成本高、流程长：

| 你可能遇到的问题 | Music Video Creator 帮你解决 |
|:-----------------|:---------------------------|
| ❓ 不会作曲编曲 | ✅ **AI 作曲** — Mureka V9 从歌词直接生成歌曲 |
| ❓ 没有拍摄团队 | ✅ **AI 生成画面** — Seedream 5.0 批量生成图片/视频 |
| ❓ 字幕手动卡点太累 | ✅ **Whisper 自动对齐** — 精准匹配歌词到音频 |
| ❓ 素材处理流程繁琐 | ✅ **一键 Pipeline** — 从歌词到成品 MV 全自动 |
| ❓ 没有 GPU 跑不动 | ✅ **纯云端 API** — 笔记本也能跑 |

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
