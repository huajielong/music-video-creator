#!/usr/bin/env python3
"""
End-to-end pipeline for music video creation.

Usage:
    # Full run (generates music via Tunee, then all downstream steps)
    python scripts/pipeline.py --title "Song" --prompt "pop" --lyrics "..." --model mureka_v9

    # With existing audio (skips generate+download)
    python scripts/pipeline.py --title "Song" --audio path/to/song.mp3 --lyrics "..."

    # Resume from step N
    python scripts/pipeline.py ... --step 6

    # Dry run
    python scripts/pipeline.py ... --dry-run
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

import validate


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def _script_path(name: str) -> str:
    return os.path.join(SCRIPTS_DIR, name)


def _run(cmd: list[str], desc: str, dry_run: bool = False) -> bool:
    """Run command, print output. Returns True on success."""
    print(f"\n=== {desc} ===")
    print(f"  {'[DRY RUN] ' if dry_run else ''}{' '.join(cmd)}")
    if dry_run:
        return True
    result = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True)
    if result.returncode != 0:
        sys.stderr.write(result.stderr or result.stdout or "")
        return False
    return True


def _run_capture(cmd: list[str], desc: str) -> str | None:
    """Run command, return stdout. Returns None on failure."""
    print(f"\n=== {desc} ===")
    print(f"  {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True)
    if result.returncode != 0:
        sys.stderr.write(result.stderr or result.stdout or "")
        return None
    return result.stdout


def _validate_step(name: str, check_fn) -> bool:
    if not check_fn:
        return True
    valid, details = check_fn()
    status = "PASS" if valid else "FAIL"
    print(f"  [{status}] {name}: {json.dumps(details, ensure_ascii=False)}")
    return valid


def main():
    parser = argparse.ArgumentParser(description="Music video creation pipeline")
    parser.add_argument("--title", required=True, help="Song title")
    parser.add_argument("--prompt", default="", help="Music style prompt (needed for step 1)")
    parser.add_argument("--lyrics", default="", help="Lyrics text")
    parser.add_argument("--model", default="", help="Tunee model ID (needed for step 1)")
    parser.add_argument("--step", type=int, default=1, help="Start from step number (default: 1)")
    parser.add_argument("--dry-run", action="store_true", help="Print steps without executing")
    parser.add_argument("--audio", default=None, help="Existing audio file (skips step 1-2)")
    parser.add_argument("--duration", type=float, default=None, help="Audio duration in seconds")
    args = parser.parse_args()

    output_dir = OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)
    title_slug = args.title.replace(" ", "_").replace("/", "_")

    # Resolve audio path
    audio_path: str | None = None
    if args.audio:
        audio_path = os.path.abspath(args.audio)
    else:
        audio_path = os.path.join(output_dir, f"{title_slug}.mp3")

    srt_path = os.path.join(output_dir, f"{title_slug}.srt")
    final_mp4 = os.path.join(output_dir, f"{title_slug}_MV_Final.mp4")

    music_id: str | None = None
    step = args.step

    # Step 1: Generate music (skip if --audio provided)
    if step <= 1 and not args.audio:
        print(f"\n[1] Generating music via Tunee...")
        cmd = [
            "python", _script_path("generate.py"),
            "--title", args.title,
            "--prompt", args.prompt,
            "--lyrics", args.lyrics,
            "--model", args.model,
        ]
        stdout = _run_capture(cmd, "Generate music")
        if stdout is None:
            sys.exit(1)
        # Parse JSON output for music_id
        for line in stdout.strip().split("\n"):
            line = line.strip()
            if line.startswith("["):
                try:
                    data = json.loads(line)
                    if isinstance(data, list) and len(data) > 0:
                        music_id = data[0].get("id")
                        print(f"  Music ID: {music_id}")
                        break
                except json.JSONDecodeError:
                    continue
        if not music_id:
            print(f"Error: Could not extract music_id from generate.py output", file=sys.stderr)
            print(stdout[:500], file=sys.stderr)
            sys.exit(1)
        step = 2

    # Step 2: Download MP3 (skip if --audio provided)
    if step <= 2 and not args.audio:
        if not music_id and not args.dry_run:
            print("Error: No music_id available for download", file=sys.stderr)
            sys.exit(1)
        print(f"\n[2] Downloading MP3...")
        cmd = ["python", _script_path("download.py"), "--id", music_id or title_slug]
        if not _run(cmd, "Download MP3", args.dry_run):
            sys.exit(1)
        # Rename to title-based filename if needed (download saves as {music_id}.mp3)
        if not args.dry_run:
            id_path = os.path.join(output_dir, f"{music_id}.mp3")
            if os.path.exists(id_path) and id_path != audio_path:
                import shutil
                shutil.copy2(id_path, audio_path)
                print(f"  Copied to: {audio_path}")
        step = 3

    # Step 3–12: standard steps
    steps_config = [
        (3, "Validate audio", lambda: _validate_step("Audio", lambda: validate.check_audio(audio_path)) if not args.dry_run else print("  [SKIP] Audio (dry-run)") or True),
        (4, "Generate SRT", lambda: _run(
            ["python", _script_path("gen_srt.py"),
             "--audio", audio_path,
             "--lyrics", args.lyrics.replace("\n", "\\n"),
             "--output", srt_path],
            "Generate SRT", args.dry_run
        )),
        (5, "Validate SRT", lambda: _validate_step("SRT", lambda: validate.check_srt(srt_path)) if not args.dry_run else print("  [SKIP] SRT (dry-run)") or True),
        (6, "Generate storyboard", lambda: _run(
            ["python", _script_path("gen_storyboard.py"),
             "--title", args.title,
             "--style", args.prompt or "cinematic",
             "--lyrics", args.lyrics],
            "Generate storyboard", args.dry_run
        )),
        (7, "Batch generate images", lambda: _run(
            ["python", _script_path("batch_generate_images.py")], "Batch generate images", args.dry_run
        )),
        (8, "Validate images", lambda: _validate_step("Images", lambda: validate.check_dir(
            os.path.join(output_dir, "res", "images"), "shot_*.png"
        )) if not args.dry_run else print("  [SKIP] Images (dry-run)") or True),
        (9, "Batch generate videos", lambda: _run(
            ["python", _script_path("batch_generate_videos.py")], "Batch generate videos", args.dry_run
        )),
        (10, "Validate videos", lambda: _validate_step("Videos", lambda: validate.check_dir(
            os.path.join(output_dir, "res", "videos"), "shot_*.mp4"
        )) if not args.dry_run else print("  [SKIP] Videos (dry-run)") or True),
        (11, "Assemble final MV", lambda: _run(
            ["python", _script_path("assemble.py"),
             "--audio", audio_path,
             "--srt", srt_path,
             "--output", final_mp4],
            "Assemble final MV", args.dry_run
        )),
        (12, "Validate final MP4", lambda: _validate_step("Final MP4", lambda: validate.check_video(final_mp4)) if not args.dry_run else print("  [SKIP] Final MP4 (dry-run)") or True),
    ]

    active = [(n, name, fn) for n, name, fn in steps_config if n >= step]

    if not active:
        print(f"No steps to run (step {step})")
        sys.exit(0)

    print(f"\nPipeline: {args.title}")
    print(f"  Audio: {audio_path}")
    print(f"  Starting from step {step}")
    print(f"  Steps: {', '.join(f'{n}. {name}' for n, name, _ in active)}")
    if args.dry_run:
        print("  ** DRY RUN - no files created **")

    for num, name, fn in active:
        print(f"\n[{num}] {name}...")
        try:
            ok = fn()
            if not ok:
                raise RuntimeError(f"Step {num} failed")
        except Exception as e:
            print(f"  Error: {e}", file=sys.stderr)
            print(f"\nPipeline failed at step [{num}] {name}")
            print(f"Resume with: --step {num}")
            sys.exit(1)

    print(f"\n{'='*50}")
    print(f"Pipeline complete!")
    print(f"  Output: {final_mp4}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
