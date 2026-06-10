> [🇨🇳 中文说明](README.zh.md)

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
