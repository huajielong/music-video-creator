#!/usr/bin/env python3
"""
Output validation utilities for music-video-creator pipeline.

Each function returns (is_valid: bool, details: dict) — never raises.
"""

import glob as glob_mod
import json
import os
import re
import subprocess
import sys

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def check_audio(path: str) -> tuple[bool, dict]:
    """Verify audio file has a valid audio stream with duration > 0."""
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-show_entries", "stream=codec_type",
            "-of", "json",
            path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return False, {"error": result.stderr.strip()}

        data = json.loads(result.stdout)
        streams = data.get("streams", [])
        has_audio = any(s.get("codec_type") == "audio" for s in streams)
        duration = float(data.get("format", {}).get("duration", 0))
        return has_audio and duration > 0, {"duration": round(duration, 2), "has_audio": has_audio}
    except Exception as e:
        return False, {"error": str(e)}


def check_image(path: str) -> tuple[bool, dict]:
    """Verify image is readable and has valid dimensions."""
    if not HAS_PIL:
        # Check file exists and is non-empty at minimum
        exists = os.path.exists(path) and os.path.getsize(path) > 0
        return exists, {"size": os.path.getsize(path) if exists else 0}
    try:
        with Image.open(path) as img:
            img.verify()
            # Re-open after verify (verify can leave the file in a bad state)
            with Image.open(path) as img2:
                return True, {"width": img2.width, "height": img2.height, "format": img2.format}
    except Exception as e:
        return False, {"error": str(e)}


def check_video(path: str) -> tuple[bool, dict]:
    """Verify video file has video stream, valid duration, and resolution."""
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-show_entries", "stream=codec_type,width,height",
            "-of", "json",
            path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return False, {"error": result.stderr.strip()}

        data = json.loads(result.stdout)
        streams = data.get("streams", [])
        video_streams = [s for s in streams if s.get("codec_type") == "video"]
        has_video = len(video_streams) > 0
        duration = float(data.get("format", {}).get("duration", 0))

        details = {"duration": round(duration, 2), "has_video": has_video}
        if video_streams:
            vs = video_streams[0]
            details["width"] = vs.get("width")
            details["height"] = vs.get("height")

        return has_video and duration > 0, details
    except Exception as e:
        return False, {"error": str(e)}


def check_srt(path: str) -> tuple[bool, dict]:
    """Parse SRT, validate timestamps, no overlaps."""
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()

        # SRT pattern: index, timestamp, text
        block_pattern = re.compile(
            r"(\d+)\s*\n"
            r"(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})\s*\n"
            r"((?:.+\n?)*?)(?=\n\d+\s*\n|\Z)",
            re.MULTILINE,
        )

        def _parse_ts(ts: str) -> float:
            h, m, s_ms = ts.split(":")
            s, ms = s_ms.split(",")
            return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000

        blocks = list(block_pattern.finditer(content))
        if not blocks:
            return False, {"error": "No valid SRT blocks found", "blocks": 0}

        entries = []
        for b in blocks:
            start = _parse_ts(b.group(2))
            end = _parse_ts(b.group(3))
            entries.append({"start": start, "end": end, "text_len": len(b.group(4).strip())})

        # Check for overlapping timestamps
        overlaps = []
        for i in range(1, len(entries)):
            if entries[i]["start"] < entries[i - 1]["end"]:
                overlaps.append({
                    "index": i + 1,
                    "prev_end": entries[i - 1]["end"],
                    "curr_start": entries[i]["start"],
                })

        total_dur = entries[-1]["end"] - entries[0]["start"] if entries else 0
        valid = len(overlaps) == 0 and 10 <= total_dur <= 600

        return valid, {
            "blocks": len(entries),
            "total_duration": round(total_dur, 2),
            "overlaps": overlaps,
        }
    except Exception as e:
        return False, {"error": str(e)}


def check_dir(path: str, pattern: str = "*") -> tuple[bool, dict]:
    """Verify all files matching glob exist and are non-empty."""
    try:
        matching = glob_mod.glob(os.path.join(path, pattern))
        files = []
        empty = []
        for fpath in sorted(matching):
            size = os.path.getsize(fpath)
            files.append({"path": fpath, "size": size})
            if size == 0:
                empty.append(fpath)

        valid = len(empty) == 0 and len(files) > 0
        return valid, {"count": len(files), "empty": len(empty), "files": files}
    except Exception as e:
        return False, {"error": str(e)}


def _print_result(name: str, valid: bool, details: dict):
    status = "PASS" if valid else "FAIL"
    print(f"  [{status}] {name}: {json.dumps(details, ensure_ascii=False)}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python validate.py <check_type> <path> [pattern]")
        print("  check_type: audio, image, video, srt, dir")
        print("  pattern: glob pattern (only for dir check)")
        sys.exit(1)

    check_type = sys.argv[1]
    path = sys.argv[2]

    checks = {
        "audio": lambda: check_audio(path),
        "image": lambda: check_image(path),
        "video": lambda: check_video(path),
        "srt": lambda: check_srt(path),
        "dir": lambda: check_dir(path, sys.argv[3] if len(sys.argv) > 3 else "*"),
    }

    checker = checks.get(check_type)
    if not checker:
        print(f"Unknown check type: {check_type}", file=sys.stderr)
        sys.exit(1)

    valid, details = checker()
    _print_result(check_type, valid, details)
    sys.exit(0 if valid else 1)
