# Music Video Creator

End-to-end pipeline: generate music (Tunee) → subtitles → storyboard → images → videos → assemble MV.

## Commands

- `/music-video-creator --title "..." --prompt "..." --lyrics "..." --model mureka_v9` — Full pipeline
- `/music-video-creator --title "..." --audio path/to/song.mp3 --lyrics "..."` — With existing audio
- `/music-video-creator --title "..." --audio path/to/song.mp3 --lyrics "..." --step 6` — Resume from step N

## Pipeline Steps

1. **generate.py** — Call Tunee API to generate music (returns music_id)
2. **download.py** — Download MP3 from Tunee share page (polls for async URL, fallback to Playwright)
3. **validate.py:check_audio()** — Verify audio file integrity
4. **gen_srt.py** — Generate SRT subtitles (Whisper alignment, boosted for music mixes)
5. **validate.py:check_srt()** — Verify SRT format and overlap detection
6. **gen_storyboard.py** — Generate shot-by-shot storyboard from lyrics
7. **batch_generate_images.py** — Parallel Doubao Seedream image generation with retry
8. **validate.py:check_images()** — Verify output images
9. **batch_generate_videos.py** — Parallel Seedance video generation with retry
10. **validate.py:check_videos()** — Verify output videos
11. **assemble.py** — FFmpeg concat + audio + subtitle burn → final MP4
12. **validate.py:check_video()** — Verify final MP4

## Technical Notes

### Whisper Alignment for Music (gen_srt.py)
- Boost audio 3x when RMS < -15dB (vocals buried in mix)
- Filter segments by CJK range `一..鿿` to exclude instrumental noise
- When segments > expected lines: truncate from end (not merge)
- Three-tier fallback: Whisper → RMS waveform → character-count proportion

### Tunee Download (download.py)
- Poll share page 12×5s for async URL availability
- Regex `\\"audioUrl\\":\\"(https://[^\\\\]+?)\\"` for Next.js RSC payload
- Fallback to Playwright browser automation

### Batch Generation
- ThreadPoolExecutor (`--workers N`, default 3)
- Exponential backoff retry (5s → 10s → 20s, max 3)
- Skip existing files for resume

### Doubao/Seedream API
- `DOUBAO_SEEDREAM_API_KEY` from ARK API
- Sensitive content moderation may reject certain prompts (no workaround — regenerate)

## Output Structure
- `output/{title}.mp3` — Generated/downloaded music
- `output/{title}.srt` — Whisper-aligned subtitles
- `output/storyboard_{title}.json` — Shot descriptions
- `output/res/images/shot_XXX.png` — Generated images
- `output/res/videos/shot_XXX.mp4` — Generated videos
- `output/{title}_MV_Final.mp4` — Final assembled music video
