#!/usr/bin/env python3
"""
Generate SRT subtitles from lyrics with timing estimation.

Three modes (automatic preference order):
1. Whisper alignment (--audio with whisper installed): most accurate, uses ML model
2. RMS waveform analysis (--audio, no whisper): estimates vocal regions from energy
3. Character-count proportion (no --audio): last resort, evenly distributes by text length
"""
import argparse
import math
import os
import re
import struct
import subprocess
import sys

try:
    import whisper as _whisper
    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False
    _whisper = None


def parse_lyrics(text: str) -> list[dict[str, str]]:
    """Parse lyrics text into sections and lines."""
    sections = re.split(r'\[([\w\s-]+)\]', text)
    result = []
    current_section = "verse"
    for i, part in enumerate(sections):
        part = part.strip()
        if not part:
            continue
        if i % 2 == 1:
            current_section = part.lower().replace(" ", "_")
        else:
            for line in part.split("\n"):
                line = line.strip()
                if line:
                    result.append({"section": current_section, "line": line})
    return result


def _match_segments(segments: list[dict], parsed_lines: list[dict]) -> list[dict] | None:
    """Merge or split whisper segments to match the number of lyric lines."""
    num_seg = len(segments)
    num_lines = len(parsed_lines)

    if num_seg == num_lines or num_seg == 0 or num_lines == 0:
        return None
    if num_seg > num_lines * 3 or num_lines > num_seg * 3:
        return None

    working = []
    base = num_lines // num_seg
    extra = num_lines % num_seg
    cur = 0
    for i, seg in enumerate(segments):
        next_cur = cur + base + (1 if i < extra else 0)
        working.append({
            "start": seg["start"],
            "end": seg["end"],
            "duration": seg["end"] - seg["start"],
            "line_start": cur,
            "line_end": next_cur,
        })
        cur = next_cur

    if num_seg > num_lines:
        while len(working) > num_lines:
            pair_idx = min(
                range(len(working) - 1),
                key=lambda i: working[i]["duration"] + working[i + 1]["duration"]
            )
            merged = {
                "start": working[pair_idx]["start"],
                "end": working[pair_idx + 1]["end"],
                "duration": working[pair_idx]["duration"] + working[pair_idx + 1]["duration"],
                "line_start": working[pair_idx]["line_start"],
                "line_end": working[pair_idx + 1]["line_end"],
            }
            working[pair_idx] = merged
            del working[pair_idx + 1]

    elif num_seg < num_lines:
        while len(working) < num_lines:
            candidates = [
                (i, w) for i, w in enumerate(working)
                if w["line_end"] - w["line_start"] > 1
            ]
            if not candidates:
                return None
            split_idx = max(candidates, key=lambda x: x[1]["line_end"] - x[1]["line_start"])[0]
            to_split = working[split_idx]

            l_start, l_end = to_split["line_start"], to_split["line_end"]
            mid_line = l_start + (l_end - l_start) // 2

            chars_left = sum(len(parsed_lines[i]["line"]) for i in range(l_start, mid_line))
            chars_right = sum(len(parsed_lines[i]["line"]) for i in range(mid_line, l_end))
            total_chars = chars_left + chars_right
            ratio = chars_left / total_chars if total_chars > 0 else 0.5

            split_time = to_split["start"] + to_split["duration"] * ratio

            working[split_idx] = {
                "start": to_split["start"],
                "end": split_time,
                "duration": split_time - to_split["start"],
                "line_start": l_start,
                "line_end": mid_line,
            }
            working.insert(split_idx + 1, {
                "start": split_time,
                "end": to_split["end"],
                "duration": to_split["end"] - split_time,
                "line_start": mid_line,
                "line_end": l_end,
            })

    if len(working) == num_lines:
        for i, seg in enumerate(working):
            parsed_lines[i]["start"] = seg["start"]
            parsed_lines[i]["end"] = seg["end"]
        return parsed_lines
    return None


def align_with_whisper(audio_path: str, parsed: list[dict], total_duration: float) -> list[dict] | None:
    """
    Use Whisper to get actual vocal timestamps.
    Maps transcribed segments to known lyrics by count or merge/split.
    """
    try:
        print(f"  Transcribing with Whisper (small model)...")
        model = _whisper.load_model('small')
        result = model.transcribe(audio_path)

        segments = [s for s in result['segments'] if len(s['text'].strip()) > 2]
        print(f"  Whisper detected {len(segments)} vocal segments, expected {len(parsed)}")

        if len(segments) == len(parsed):
            for i, seg in enumerate(segments):
                parsed[i]["start"] = seg["start"]
                parsed[i]["end"] = seg["end"]
            return parsed

        # Try merge/split matching before falling back
        matched = _match_segments(segments, parsed)
        if matched:
            return matched
        print(f"  Could not match {len(segments)} segments to {len(parsed)} lines, falling back to waveform analysis")
        return None

    except Exception as e:
        print(f"  Whisper failed: {e}, falling back", file=sys.stderr)
        return None


def analyze_audio_regions(audio_path: str, total_duration: float) -> dict:
    """Analyze audio RMS energy to find vocal regions. Used as fallback."""
    cmd = ["ffmpeg", "-i", audio_path, "-ac", "1", "-ar", "44100", "-f", "s16le", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    raw = proc.stdout.read()
    proc.wait()

    samples = struct.unpack(f"<{len(raw)//2}h", raw)
    samples = [s / 32768 for s in samples]

    window = 4410
    num_windows = len(samples) // window
    rms = []
    for i in range(num_windows):
        chunk = samples[i * window : (i + 1) * window]
        power = sum(s * s for s in chunk) / window
        rms_val = 20 * math.log10(math.sqrt(power) + 1e-10)
        rms.append(rms_val)

    peak = max(rms)
    threshold = peak - 20

    regions = []
    in_region = False
    start = 0
    for i, v in enumerate(rms):
        if v > threshold and not in_region:
            start = i
            in_region = True
        elif v <= threshold and in_region:
            dur = (i - start) * 0.1
            if dur > 1.0:
                regions.append((start * 0.1, i * 0.1))
            in_region = False
    if in_region:
        dur = (num_windows - start) * 0.1
        if dur > 1.0:
            regions.append((start * 0.1, num_windows * 0.1))

    if not regions:
        return {"intro_silence": 2.0, "outro_silence": 2.0,
                "regions": [(2.0, total_duration - 2.0)], "gaps": []}

    intro_silence = regions[0][0] if regions else 0
    outro_silence = max(0, total_duration - regions[-1][1]) if regions else 0
    gaps = []
    for i in range(1, len(regions)):
        gap = regions[i][0] - regions[i - 1][1]
        if gap > 0.15:
            gaps.append({"start": round(regions[i - 1][1], 1),
                         "end": round(regions[i][0], 1), "dur": round(gap, 1)})

    return {"intro_silence": round(intro_silence, 1), "outro_silence": round(outro_silence, 1),
            "regions": [(round(s, 1), round(e, 1)) for s, e in regions], "gaps": gaps}


def estimate_timings(parsed: list[dict], total_duration: float,
                     audio_analysis: dict | None = None) -> list[dict]:
    """Assign start/end times using audio analysis + character proportion."""
    if audio_analysis:
        intro = audio_analysis["intro_silence"]
        regions = audio_analysis["regions"]
    else:
        intro = 2.0
        regions = [(intro, total_duration - 2.0)]

    for item in parsed:
        item["chars"] = len(item["line"])
    total_chars = sum(item["chars"] for item in parsed)

    active_duration = sum(e - s for s, e in regions)
    if active_duration <= 0 or total_chars <= 0:
        for item in parsed:
            item["chars"] = item.get("chars", 1) or 1
        total_chars = sum(item["chars"] for item in parsed)
        active_duration = max(total_duration - intro - 2, 10)

    # Single-region: distribute all lines proportionally (avoids multi-region split issues)
    current_time = intro
    for item in parsed:
        duration = active_duration * item["chars"] / total_chars if total_chars else active_duration / len(parsed)
        duration = max(1.5, duration)
        item["start"] = current_time
        item["end"] = min(current_time + duration, total_duration)
        current_time = item["end"]

    return parsed


def to_srt_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def generate_srt(parsed: list[dict]) -> str:
    lines = []
    for i, item in enumerate(parsed, 1):
        lines.append(str(i))
        lines.append(f"{to_srt_timestamp(item['start'])} --> {to_srt_timestamp(item['end'])}")
        lines.append(item["line"])
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate SRT subtitles with audio-aware timing")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input", help="Lyrics text file path")
    group.add_argument("--lyrics", help="Lyrics text inline (use \\n for newlines)")
    parser.add_argument("--duration", type=float, default=None,
                        help="Audio duration in seconds (required for fallback mode)")
    parser.add_argument("--audio", default=None, help="Audio file path for timing analysis")
    parser.add_argument("--output", default=None, help="Output SRT file path")
    args = parser.parse_args()

    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            lyrics_text = f.read()
    else:
        lyrics_text = args.lyrics.replace("\\n", "\n")

    parsed = parse_lyrics(lyrics_text)
    if not parsed:
        print("Error: No lyrics lines found", file=sys.stderr)
        sys.exit(1)

    print(f"Parsed {len(parsed)} lyric lines")

    # Priority 1: Whisper alignment (most accurate)
    aligned = None
    if args.audio and os.path.exists(args.audio) and HAS_WHISPER:
        aligned = align_with_whisper(args.audio, parsed, args.duration or 0)

    # Priority 2: RMS waveform analysis
    if not aligned and args.audio and os.path.exists(args.audio):
        if not args.duration:
            # Get duration from ffprobe
            cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                   "-of", "csv=p=0", args.audio]
            result = subprocess.run(cmd, capture_output=True, text=True)
            try:
                args.duration = float(result.stdout.strip())
            except (ValueError, TypeError):
                print("Error: Could not determine audio duration. Provide --duration", file=sys.stderr)
                sys.exit(1)

        print(f"Analyzing audio waveform: {args.audio}")
        audio_analysis = analyze_audio_regions(args.audio, args.duration)
        print(f"  Duration: {args.duration:.1f}s")
        print(f"  Intro: {audio_analysis['intro_silence']}s, Outro: {audio_analysis['outro_silence']}s")
        print(f"  Active regions: {len(audio_analysis['regions'])}")
        parsed = estimate_timings(parsed, args.duration, audio_analysis)

    # Priority 3: Character-count estimation
    elif not aligned:
        if not args.duration:
            print("Error: --duration required when no audio file provided", file=sys.stderr)
            sys.exit(1)
        print("No audio file, using character-count estimation")
        parsed = estimate_timings(parsed, args.duration)

    srt_content = generate_srt(parsed)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(srt_content)
        print(f"\nSRT saved: {args.output}")
    else:
        print(srt_content)


if __name__ == "__main__":
    main()
