#!/usr/bin/env python3
"""
Assemble final MV: concatenate video clips + overlay audio + burn subtitles.

Usage:
    python scripts/assemble.py --shots 1-30 --audio output/笑傲江湖.mp3 --srt output/笑傲江湖.srt --output final.mp4

Requires: ffmpeg (install via `winget install ffmpeg` or `brew install ffmpeg`)
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile


def parse_shot_range(text: str) -> list[int]:
    shots = []
    for part in text.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            shots.extend(range(int(a.strip()), int(b.strip()) + 1))
        else:
            shots.append(int(part))
    return shots


def main():
    parser = argparse.ArgumentParser(
        description="Assemble final MV: concat video clips + overlay audio + burn subtitles (FFmpeg)",
        epilog="Examples:\n"
               "  %(prog)s --audio output/song.mp3 --srt output/song.srt --output final.mp4\n"
               "  %(prog)s --audio song.mp3 --srt song.srt --shots 1-30 --fps 30\n"
               "Requires FFmpeg: https://ffmpeg.org/download.html",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--shots", default="1-30", help="Shot range, e.g. 1-30 or 1,3,5")
    parser.add_argument("--audio", required=True, help="Audio file path (MP3/WAV)")
    parser.add_argument("--srt", default=None, help="Subtitle file path (SRT) — optional")
    parser.add_argument("--output", default="output/MV_Final.mp4", help="Output MP4 path")
    parser.add_argument("--fps", type=int, default=24, help="Output frame rate (default: 24)")
    parser.add_argument("--videos-dir", default=None, help="Video clips directory (default: output/res/videos)")
    args = parser.parse_args()

    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    videos_dir = args.videos_dir or os.path.join(base, "output", "res", "videos")
    audio_path = os.path.join(base, args.audio) if not os.path.isabs(args.audio) else args.audio
    output_path = os.path.join(base, args.output) if not os.path.isabs(args.output) else args.output

    if not os.path.exists(audio_path):
        print(f"Error: Audio not found: {audio_path}", file=sys.stderr)
        sys.exit(1)

    shot_numbers = parse_shot_range(args.shots)

    # Verify all video files exist
    video_paths = []
    for sn in shot_numbers:
        vp = os.path.join(videos_dir, f"shot_{sn:03d}.mp4")
        if not os.path.exists(vp):
            print(f"Error: Video not found: {vp}", file=sys.stderr)
            sys.exit(1)
        video_paths.append(vp)

    print(f"Assembling {len(video_paths)} clips + audio + subtitles -> {output_path}")
    print(f"  Audio: {audio_path}")
    if args.srt:
        srt_path = os.path.join(base, args.srt) if not os.path.isabs(args.srt) else args.srt
        if os.path.exists(srt_path):
            print(f"  Subtitles: {srt_path}")
        else:
            print(f"  Warning: SRT not found, skipping subtitles")
            srt_path = None
    else:
        srt_path = None

    # Create concat file list
    concat_file = os.path.join(tempfile.gettempdir(), "mv_concat.txt")
    with open(concat_file, "w", encoding="utf-8") as f:
        for vp in video_paths:
            f.write(f"file '{vp}'\n")

    # Build FFmpeg command
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_file,
        "-i", audio_path,
    ]

    # Map video from concat, audio from MP3
    map_flags = ["-map", "0:v:0", "-map", "1:a:0"]

    # Burn subtitles. On Windows, 'subtitles=path' breaks on drive-letter colons.
    # Workaround: copy to project root and use relative path with explicit original_size.
    srt_filter = None
    tmp_srt = None
    if srt_path:
        tmp_srt = os.path.join(base, "_temp_subs.srt")
        shutil.copy2(srt_path, tmp_srt)
        # Use relative filename + f= named param to avoid ':' parsing in Windows paths
        srt_rel = "_temp_subs.srt"
        srt_filter = f"subtitles=f={srt_rel}:original_size=1280x720"

    cmd.extend(map_flags)
    if srt_filter:
        cmd.extend(["-vf", srt_filter])

    cmd.extend([
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_path,
    ])

    print(f"\nRunning: {' '.join(cmd[:4])} ...")
    if srt_filter:
        print(f"  Filter: {srt_filter}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FFmpeg error:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    size = os.path.getsize(output_path)
    print(f"\nDone: {output_path} ({size / 1024 / 1024:.1f} MB)")

    # Clean up
    os.unlink(concat_file)
    if tmp_srt and os.path.exists(tmp_srt):
        os.unlink(tmp_srt)


if __name__ == "__main__":
    main()
