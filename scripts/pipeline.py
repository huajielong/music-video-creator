#!/usr/bin/env python3
"""
End-to-end pipeline for music video creation.

Runs all steps sequentially: generate → download → align → storyboard → images → videos → assemble.
Supports --step N to resume from a specific step.

Usage:
    # Full run
    python scripts/pipeline.py --title "Song" --prompt "pop" --lyrics "..." --model mureka_v9

    # Resume from step 6 (SRT generation)
    python scripts/pipeline.py ... --step 6

    # Dry run (print steps without executing)
    python scripts/pipeline.py ... --dry-run

    # Skip validation checks
    python scripts/pipeline.py ... --skip-validation
"""

import argparse
import json
import os
import subprocess
import sys

import validate


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def _script_path(name: str) -> str:
    return os.path.join(SCRIPTS_DIR, name)


def _run(cmd: list[str], desc: str, dry_run: bool = False) -> bool:
    print(f"\n=== {desc} ===")
    print(f"  {'[DRY RUN]' if dry_run else ''} {' '.join(cmd)}")
    if dry_run:
        return True
    result = subprocess.run(cmd, cwd=BASE_DIR)
    return result.returncode == 0


def _get_output_dir() -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return OUTPUT_DIR


def main():
    parser = argparse.ArgumentParser(description="Music video creation pipeline")
    parser.add_argument("--title", required=True, help="Song title")
    parser.add_argument("--prompt", required=True, help="Music style prompt")
    parser.add_argument("--lyrics", default="", help="Lyrics text")
    parser.add_argument("--model", required=True, help="Tunee model ID")
    parser.add_argument("--step", type=int, default=1,
                        help="Start from step number (1-14, default: 1)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print steps without executing")
    parser.add_argument("--skip-validation", action="store_true",
                        help="Skip validation checks")
    parser.add_argument("--audio", default=None,
                        help="Audio file path (skip generate+download if provided)")
    parser.add_argument("--duration", type=float, default=None,
                        help="Audio duration in seconds (needed without --audio)")
    args = parser.parse_args()

    step = args.step

    # Resolve output paths
    output_dir = _get_output_dir()
    title_slug = args.title.replace(" ", "_")
    audio_path = args.audio or os.path.join(output_dir, f"{title_slug}.mp3")
    srt_path = os.path.join(output_dir, f"{title_slug}.srt")

    steps_config = [
        (1, "Generate music", lambda: _run(
            ["python", _script_path("generate.py"),
             "--title", args.title,
             "--prompt", args.prompt,
             "--lyrics", args.lyrics,
             "--model", args.model],
            "Generate music", args.dry_run
        )),
        (2, "Parse generate output & download MP3", lambda: _run(
            ["python", _script_path("download.py"), "--id", args.title],
            "Download MP3", args.dry_run
        )),
        (3, "Validate audio", lambda: _validate_step(
            "Audio", lambda: validate.check_audio(audio_path)
        )),
        (4, "Generate SRT", lambda: _run(
            ["python", _script_path("gen_srt.py"),
             "--audio", audio_path,
             "--lyrics", args.lyrics.replace("\n", "\\n"),
             "--output", srt_path],
            "Generate SRT", args.dry_run
        )),
        (5, "Validate SRT", lambda: _validate_step(
            "SRT", lambda: validate.check_srt(srt_path)
        )),
        (6, "Generate storyboard", lambda: _run(
            ["python", _script_path("gen_storyboard.py")],
            "Generate storyboard", args.dry_run
        )),
        (7, "Batch generate images", lambda: _run(
            ["python", _script_path("batch_generate_images.py")],
            "Batch generate images", args.dry_run
        )),
        (8, "Validate images", lambda: _validate_step(
            "Images", lambda: validate.check_dir(
                os.path.join(output_dir, "res", "images"), "shot_*.png"
            )
        )),
        (9, "Batch generate videos", lambda: _run(
            ["python", _script_path("batch_generate_videos.py")],
            "Batch generate videos", args.dry_run
        )),
        (10, "Validate videos", lambda: _validate_step(
            "Videos", lambda: validate.check_dir(
                os.path.join(output_dir, "res", "videos"), "shot_*.mp4"
            )
        )),
        (11, "Assemble final MV", lambda: _run(
            ["python", _script_path("assemble.py"),
             "--audio", audio_path,
             "--srt", srt_path,
             "--output", os.path.join(output_dir, f"{title_slug}_final.mp4")],
            "Assemble final MV", args.dry_run
        )),
        (12, "Validate final MP4", lambda: _validate_step(
            "Final MP4", lambda: validate.check_video(
                os.path.join(output_dir, f"{title_slug}_final.mp4")
            )
        )),
    ]

    # Filter by --step
    active_steps = [(num, name, fn) for num, name, fn in steps_config if num >= step]

    if not active_steps:
        print(f"No steps to run (step {step} is out of range)")
        sys.exit(1)

    print(f"Pipeline: {args.title}")
    print(f"  Model: {args.model}")
    print(f"  Starting from step {step}")
    print(f"  Steps: {', '.join(f'{n}. {name}' for n, name, _ in active_steps)}")
    if args.dry_run:
        print("  ** DRY RUN - no files will be created **")

    for num, name, fn in active_steps:
        print(f"\n[{num}] {name}...")
        try:
            ok = fn()
        except Exception as e:
            print(f"  Error: {e}", file=sys.stderr)
            ok = False

        if not ok:
            print(f"\nPipeline failed at step [{num}] {name}")
            print(f"Resume with: --step {num}")
            sys.exit(1)

    print(f"\nPipeline complete! Final output: {os.path.join(output_dir, f'{title_slug}_final.mp4')}")


def _validate_step(name: str, check_fn) -> bool:
    """Run a validation check, print result. Returns True if valid or skipped."""
    if not check_fn:
        return True
    valid, details = check_fn()
    status = "PASS" if valid else "FAIL"
    print(f"  [{status}] {name}: {json.dumps(details, ensure_ascii=False)}")
    return valid


if __name__ == "__main__":
    main()
