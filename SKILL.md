---
name: music-video-creator
description: |
  AI music and video creation — generate vocals/instrumentals, create storyboards, batch generate images/videos, assemble MV with whisper-synced subtitles.
  Triggers: generate music, song, BGM, MV, storyboard, compose, write lyrics.
  Languages: 15+ including Chinese/English/Japanese/Korean.
  Key rule: style integration in prompts (never separate sections).
metadata:
  {
    "openclaw": {
      "emoji": "🎬",
      "homepage": "https://www.tunee.ai",
      "primaryEnv": "TUNEE_API_KEY",
      "requires": { "env": ["TUNEE_API_KEY", "ARK_API_KEY"] }
    },
    "capabilities": [
      "music_generation",
      "storyboard_creation",
      "batch_image_generation",
      "batch_video_generation",
      "video_assembly",
      "audio_alignment"
    ]
  }
---

# Music Video Creator

Generate music and create complete music videos with AI.

## Quick Start

```bash
# Install
pip install requests playwright openai-whisper
playwright install chromium

# Generate music
python scripts/generate.py --title "Song" --prompt "pop, female vocal" --lyrics "[Verse]\nlyrics..." --model mureka_v9

# Download & align subtitles (Whisper extracts real vocal timings)
python scripts/download.py --id <music_id>
python scripts/gen_srt.py --audio output/title.mp3 --lyrics "[Verse]\nlyrics..." --output output/title.srt

# Create storyboard -> batch images -> batch videos -> assemble
python scripts/gen_storyboard.py ...
python scripts/batch_generate_images.py
python scripts/batch_generate_videos.py --shots 1-30
python scripts/assemble.py --shots 1-30 --audio output/title.mp3 --srt output/title.srt --output final.mp4
```

## Workflow

```
生成音乐 → 下载MP3 → Whisper对齐字幕 → 生成分镜
   → 批量出图 → 批量出视频 → FFmpeg合成MV
```

## Core Rules

### Style Integration (MANDATORY)

**NEVER** create separate "style" sections. **ALWAYS** integrate into each prompt:

```
[Subject] + [Scene] + [Style] + [Aspect Ratio] + [Shot Size]
```

### Lyrics Structure

| Section | Lines | Notes |
|---------|-------|-------|
| Verse | 2, 4, or 8 | **Must be these counts** |
| Pre-Chorus | 2-4 | Build-up |
| Chorus | 4-8 | Hook, repeated |
| Bridge | 2-4 | Once, before final Chorus |
| Intro/Inst/Outro | — | Empty body, tag only |

**No numbers, no music terms, no direct emotions — express through concrete scenes.**

### Music Prompt

```
Format: genre, vocal, mood, tempo, instruments, production
```

---

## Subtitle-Audio Alignment

This is the **most critical quality step**. Wrong alignment = subtitles out of sync with vocals.

### Default: `gen_srt.py --audio` (recommended, uses Whisper)

```bash
python scripts/gen_srt.py --audio output/song.mp3 --lyrics "..." --duration 155 --output output/song.srt
```

- Pass `--audio` to trigger Whisper transcription
- Extracts **actual vocal start/end times** per lyric line (~1-8s precision)
- Handles intro silence, instrumental interludes, and outro automatically
- Falls back to character-count proportion if Whisper fails

### ⚠️ When estimation fails (and you need this)

**Never use character-count proportion as the default.** It produces wrong pacing because:
- Verses are sung fast (2-4s/line), pre-choruses draw out (5-7s/line)
- Repeated choruses may have different pacing
- Instrumental sections get falsely detected as "silence"
- Multi-region waveform splitting creates uneven distributions

**Symptoms of broken timings**: subtitles jump mid-song, first half flies by, second half drags.

### Tunee API limitation

Tunee returns `{musicId, title, duration, lyrics (plain text)}`. **No per-line timing data.** The share page displays lyrics as static text only. Always use Whisper for alignment.

### Implementation notes

- First run downloads the `small` Whisper model (~460MB, cached after first use)
- `gen_srt.py` maps whisper segments (26 segments = 2 instrumental + 26 lyric lines in typical songs) to known lyrics using segment count
- If segment count ≠ line count, falls back to proportional split
- Works with Chinese/English/Japanese/Korean

---

## Scripts

| Script | Purpose |
|--------|---------|
| `generate.py` | Generate music via Tunee API (lyrics or instrumental) |
| `list_models.py` | List available models (cached 24h) |
| `credits.py` | Check Tunee balance |
| `download.py` | Download MP3 via Playwright (handles CDN 403) |
| `gen_srt.py` | **Generate SRT with Whisper alignment** (`--audio`) or fallback estimation |
| `gen_storyboard.py` | Storyboard markdown + image prompts from lyrics |
| `batch_generate_images.py` | Batch images via Doubao Seedream |
| `batch_generate_videos.py` | Batch videos via Doubao Seedance |
| `assemble.py` | Final MV: concat videos + audio + burn subtitles (FFmpeg) |

## Downloading Music

Tunee returns a share page URL (not direct audio). The CDN requires browser-level cookies.

```bash
python scripts/download.py --id <music_id>   # One command: opens share page, clicks download
```

**Troubleshooting**: If download fails, the share page `https://www.tunee.ai/music/<id>` contains an `audioUrl` field in the page data. Open it in a browser to download manually (you must be logged in).

---

## API Keys

| Service | Env Key | Purpose |
|---------|---------|---------|
| Tunee | `TUNEE_API_KEY` | Music generation |
| Doubao | `ARK_API_KEY` | Seedream (image) + Seedance (video) |
