#!/usr/bin/env python3
"""
Batch generate storyboard videos via Doubao Seedance API.

Usage:
    python scripts/batch_generate_videos.py --shots 1-30 --watermark false

Args:
    --shots       Shot range, e.g. 1-30 (default: 1)
    --model       Model ID (default: doubao-seedance-1-5-pro-251215)
    --resolution  Video resolution (default: 720p)
    --duration    Video duration in seconds, 1.5.pro: 2-12 (default: 5)
    --watermark   Add watermark (default: false)
    --prompt      Motion prompt for video (default: auto from storyboard)
    --api-key     ARK API key (default: from .env or env var)
    --poll-interval Seconds between status polls (default: 10)
    --output      Output directory (default: output/res/videos/)
"""

import argparse
import base64
import json
import os
import re
import sys
import time
import requests

ARK_BASE = "https://ark.cn-beijing.volces.com"
TASK_ENDPOINT = f"{ARK_BASE}/api/v3/contents/generations/tasks"


def resolve_api_key(cli_key: str | None) -> str:
    for key in (cli_key, os.environ.get("ARK_API_KEY")):
        if key and key.strip() and key.strip() != "your-api-key-here":
            return key.strip()
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip().replace("\r", "")
                if line.startswith("ARK_API_KEY="):
                    val = line.split("=", 1)[1].strip()
                    if val:
                        return val
    print("Error: No ARK_API_KEY found", file=sys.stderr)
    sys.exit(1)


def load_prompts(path: str) -> list[str]:
    ns = {}
    with open(path, encoding="utf-8") as f:
        exec(f.read(), ns)
    return ns.get("PROMPTS", [])


def submit_task(api_key: str, model: str, image_path: str, prompt: str,
                resolution: str, duration: int, watermark: bool) -> str:
    """Submit a video generation task. Returns task_id."""
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    content = [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}, "role": "first_frame"},
    ]

    payload = {
        "model": model,
        "content": content,
        "resolution": resolution,
        "ratio": "16:9",
        "duration": duration,
        "watermark": watermark,
    }

    resp = requests.post(TASK_ENDPOINT, json=payload, headers=headers, timeout=60)
    if resp.status_code != 200:
        print(f"  Submit failed ({resp.status_code}): {resp.text[:200]}", file=sys.stderr)
        return None

    return resp.json().get("id")


def poll_task(api_key: str, task_id: str, interval: int = 10, timeout: int = 300) -> dict | None:
    """Poll task until completion. Returns the result data."""
    headers = {"Authorization": f"Bearer {api_key}"}
    start = time.time()

    while time.time() - start < timeout:
        resp = requests.get(f"{TASK_ENDPOINT}/{task_id}", headers=headers, timeout=30)
        data = resp.json()
        status = data.get("status", "unknown")

        if status == "succeeded":
            return data
        elif status in ("failed", "expired"):
            err = data.get("error", "unknown error")
            print(f"  Task failed: {err}", file=sys.stderr)
            return None

        time.sleep(interval)

    print(f"  Task timed out after {timeout}s", file=sys.stderr)
    return None


def generate_video(api_key: str, model: str, image_path: str, prompt: str,
                   resolution: str, duration: int, watermark: bool,
                   output_path: str, poll_interval: int) -> bool:
    """Generate one video: submit + poll + download."""
    task_id = submit_task(api_key, model, image_path, prompt, resolution, duration, watermark)
    if not task_id:
        return False

    result = poll_task(api_key, task_id, interval=poll_interval)
    if not result:
        return False

    video_url = result.get("content", {}).get("video_url")
    if not video_url:
        print("  No video_url in result", file=sys.stderr)
        return False

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    video_resp = requests.get(video_url, stream=True, timeout=120)
    with open(output_path, "wb") as f:
        for chunk in video_resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    size = os.path.getsize(output_path)
    print(f"  -> {output_path} ({size} bytes)")
    return True


def parse_shot_range(text: str) -> list[int]:
    """Parse '1-30' or '1,3,5' into list of shot numbers."""
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
    parser = argparse.ArgumentParser(description="Batch generate storyboard videos")
    parser.add_argument("--shots", default="1", help="Shot range, e.g. 1-30 or 1,3,5")
    parser.add_argument("--model", default="doubao-seedance-1-5-pro-251215")
    parser.add_argument("--resolution", default="720p", choices=["480p", "720p", "1080p"])
    parser.add_argument("--duration", type=int, default=5, help="Video duration in seconds")
    parser.add_argument("--watermark", default="false", choices=["true", "false"])
    parser.add_argument("--prompt", default=None, help="Motion prompt (default: from shot content)")
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--poll-interval", type=int, default=10)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    api_key = resolve_api_key(args.api_key)
    watermark = args.watermark.lower() == "true"

    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    images_dir = os.path.join(base, "output", "res", "images")
    output_dir = args.output or os.path.join(base, "output", "res", "videos")
    os.makedirs(output_dir, exist_ok=True)

    # Try to load prompts for context
    prompts_file = os.path.join(base, "scripts", "image_prompts.py")
    all_prompts = load_prompts(prompts_file) if os.path.exists(prompts_file) else []

    shot_numbers = parse_shot_range(args.shots)
    print(f"Generating {len(shot_numbers)} video(s)")
    print(f"  Model: {args.model}")
    print(f"  Resolution: {args.resolution}")
    print(f"  Duration: {args.duration}s")
    print(f"  Watermark: {watermark}")
    print()

    default_prompt = args.prompt or "动态画面，缓慢推镜头， cinematic camera movement"

    success = 0
    for shot_num in shot_numbers:
        image_path = os.path.join(images_dir, f"shot_{shot_num:03d}.png")
        if not os.path.exists(image_path):
            print(f"[{shot_num:03d}] Image not found: {image_path}")
            continue

        video_path = os.path.join(output_dir, f"shot_{shot_num:03d}.mp4")
        if os.path.exists(video_path):
            print(f"[{shot_num:03d}] Skip (exists)")
            success += 1
            continue

        # Use shot prompt as context for the video motion prompt
        shot_prompt = all_prompts[shot_num - 1] if shot_num <= len(all_prompts) else ""
        motion = f"{default_prompt}，{shot_prompt[:60]}" if shot_prompt else default_prompt

        print(f"[{shot_num:03d}] Submitting...")
        ok = generate_video(api_key, args.model, image_path, motion,
                           args.resolution, args.duration, watermark,
                           video_path, args.poll_interval)
        if ok:
            success += 1

    print(f"\nDone: {success}/{len(shot_numbers)} videos")


if __name__ == "__main__":
    main()
