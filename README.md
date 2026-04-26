# 🎬 Music Video Creator

> **AI-powered music video generation** — compose songs, create storyboards, batch-generate images/videos, and assemble a final MV with whisper-synced subtitles. All from a single lyrics file.

<p align="center">
  <img src="assets/demo_preview.gif" width="480" alt="Demo Preview">
  <br>
  <em>Demo: 10 storyboard frames from "笑傲江湖" (Mureka V9 + Doubao Seedream 5.0)</em>
</p>

<details>
<summary>▶️ Watch final MV preview (10s)</summary>

<video src="assets/demo_preview.mp4" controls width="720">
  Your browser does not support the video tag.
</video>
</details>

---

## ✨ What You Can Do

```
Lyrics → Song → Storyboard → 30 Images → 30 Video Clips → Final MV with Subtitles
```

| Step | What happens | Time |
|------|-------------|------|
| 1. Write lyrics | Verse, Chorus, Bridge structure | 5 min |
| 2. `pip install . && setup` | One-command install | 2 min |
| 3. `python scripts/pipeline.py ...` | Full auto pipeline | ~30 min |
| 4. ✅ Get your MV | MP4 with audio + subtitles | — |

---

## 🚀 One-Minute Setup

```bash
# 1. Clone and install
git clone https://github.com/YOUR_USER/music-video-creator.git
cd music-video-creator
pip install -r requirements.txt
playwright install chromium

# 2. Set your API keys
cp .env.example .env    # edit with your keys

# 3. Generate a full music video
python scripts/pipeline.py \
  --title "My Song" \
  --prompt "pop, female vocal, energetic" \
  --lyrics "[Verse 1]\nYour lyrics here..." \
  --model mureka_v9
```

> **No GPU required.** Everything runs via cloud APIs. A laptop is enough.

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
  --lyrics "[Verse]\n..." --output output/storyboard.md

# 5. Batch generate images (no watermark)
python scripts/batch_generate_images.py --watermark false

# 6. Batch generate videos
python scripts/batch_generate_videos.py --shots 1-30

# 7. Assemble final MV
python scripts/assemble.py --audio output/song.mp3 \
  --srt output/song.srt --output output/final.mp4
```

Or run everything at once:

```bash
python scripts/pipeline.py \
  --title "My Song" \
  --prompt "pop, female vocal" \
  --lyrics "$(cat lyrics.txt)" \
  --model mureka_v9
```

---

## 📋 Prerequisites

| Requirement | Why |
|------------|-----|
| **Python 3.10+** | Scripts require 3.10+ type hints |
| **FFmpeg** | Video assembly and audio analysis ([install guide](https://ffmpeg.org/download.html)) |
| **Tunee API key** | Music generation ([get one](https://www.tunee.ai)) |
| **ARK API key** | Image/video generation via Volcengine |

---

## 🔑 API Keys

Create `.env` in the project root:

```env
TUNEE_API_KEY=sk-tunee-xxx
ARK_API_KEY=ark-xxx
```

| Service | Env Key | Used By |
|---------|---------|---------|
| Tunee (music) | `TUNEE_API_KEY` | `generate.py`, `list_models.py`, `credits.py` |
| Doubao (image) | `ARK_API_KEY` | `batch_generate_images.py` |
| Doubao (video) | `ARK_API_KEY` | `batch_generate_videos.py` |

---

## 🎵 Lyrics Structure

| Section | Lines | Example |
|---------|-------|---------|
| Verse | 2, 4, or 8 | Narrative verses |
| Pre-Chorus | 2-4 | Build-up tension |
| Chorus | 4-8 | Hook, repeated |
| Bridge | 2-4 | Climax, once before final Chorus |
| Intro/Outro | — | Instrumental, no lyrics |

---

## 🧩 Scripts Overview

| Script | Purpose |
|--------|---------|
| `generate.py` | Generate music via Tunee API |
| `list_models.py` | List available music models (cached 24h) |
| `credits.py` | Check Tunee account balance |
| `download.py` | Download MP3 from Tunee share page |
| `gen_srt.py` | **Generate SRT with Whisper** or fallback timing |
| `gen_storyboard.py` | Storyboard markdown + image prompts |
| `batch_generate_images.py` | Parallel image gen via Doubao Seedream |
| `batch_generate_videos.py` | Parallel video gen via Doubao Seedance |
| `assemble.py` | FFmpeg: concat videos + audio + burn subtitles |
| `pipeline.py` | **End-to-end**: run all steps in sequence |
| `validate.py` | Validate outputs: audio, images, videos, SRT |

---

## 🛠️ Key Features

- **Whisper-aligned subtitles** — Detects actual vocal timing in music mixes (auto-boosts quiet audio 3x)
- **Content moderation auto-retry** — Detects rejected prompts, strips sensitive terms, retries with safe prompts
- **Resume support** — Skip existing files on re-run, pick up from any pipeline step
- **Parallel generation** — ThreadPoolExecutor for images/videos (default 3 workers)
- **Exponential backoff** — Retries on timeout/server errors (5s → 10s → 20s)

---

## 🗺️ Roadmap

- [x] Video assembly + SRT burn
- [x] Whisper audio alignment
- [x] Retry mechanism (exponential backoff)
- [ ] Prompt style packs (wuxia, sci-fi, romance, horror)
- [ ] Auto-diversify repeated chorus shots
- [ ] Model fallback chain
- [ ] Web UI (Gradio)
- [ ] Multi-song album mode

---

