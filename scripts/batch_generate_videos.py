#!/usr/bin/env python3
"""
Batch generate storyboard videos via Doubao Seedance API.

Features: retry with backoff, resume (skip existing), parallel execution, error summary.

Usage:
    python scripts/batch_generate_videos.py --shots 1-30 --workers 3
"""

import argparse
import base64
import concurrent.futures
import os
import sys
import threading
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
                resolution: str, duration: int, watermark: bool,
                max_retries: int = 3) -> str | None:
    """Submit a video generation task. Returns task_id (with retry)."""
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

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(TASK_ENDPOINT, json=payload, headers=headers, timeout=60)
            if resp.status_code != 200:
                is_retryable = 500 <= resp.status_code < 600
                if is_retryable and attempt < max_retries:
                    wait = 5 * (2 ** (attempt - 1))
                    print(f"  [Retry {attempt}/{max_retries}] Submit {resp.status_code}, waiting {wait}s...")
                    time.sleep(wait)
                    continue
                print(f"  Submit failed ({resp.status_code}): {resp.text[:200]}", file=sys.stderr)
                return None
            return resp.json().get("id")
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt < max_retries:
                wait = 5 * (2 ** (attempt - 1))
                print(f"  [Retry {attempt}/{max_retries}] {e}, waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"  Submit failed after {max_retries} retries: {e}", file=sys.stderr)
                return None

    return None


def poll_task(api_key: str, task_id: str, interval: int = 10, timeout: int = 300) -> dict | None:
    """Poll task until completion. Returns the result data."""
    headers = {"Authorization": f"Bearer {api_key}"}
    start = time.time()

    while time.time() - start < timeout:
        try:
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
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            # Transient network error during poll — keep trying
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
    shots = []
    for part in text.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            shots.extend(range(int(a.strip()), int(b.strip()) + 1))
        else:
            shots.append(int(part))
    return shots


_print_lock = threading.Lock()


def _wait_interval(interval: float):
    time.sleep(interval)


def process_one_shot(shot_num: int, api_key: str, model: str, resolution: str,
                     duration: int, watermark: bool, default_prompt: str,
                     images_dir: str, output_dir: str, all_prompts: list[str],
                     poll_interval: int, interval: float) -> tuple[int, bool, str]:
    """Process a single shot. Returns (shot_num, success, status_label)."""
    image_path = os.path.join(images_dir, f"shot_{shot_num:03d}.png")
    if not os.path.exists(image_path):
        with _print_lock:
            print(f"[{shot_num:03d}] image not found, skipping")
        return shot_num, False, "no_image"

    video_path = os.path.join(output_dir, f"shot_{shot_num:03d}.mp4")
    if os.path.exists(video_path):
        with _print_lock:
            print(f"[{shot_num:03d}] already exists, skipping")
        return shot_num, True, "skipped"

    shot_prompt = all_prompts[shot_num - 1] if shot_num <= len(all_prompts) else ""
    motion = f"{default_prompt}，{shot_prompt[:60]}" if shot_prompt else default_prompt

    with _print_lock:
        print(f"[{shot_num:03d}] submitting...")
    start_t = time.time()
    ok = generate_video(api_key, model, image_path, motion,
                        resolution, duration, watermark,
                        video_path, poll_interval)
    elapsed = time.time() - start_t
    with _print_lock:
        label = "done" if ok else "failed"
        print(f"[{shot_num:03d}] {label} ({elapsed:.0f}s)")

    _wait_interval(interval)
    return shot_num, ok, "done" if ok else "failed"


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
    parser.add_argument("--workers", type=int, default=3, help="Parallel workers (default: 3)")
    parser.add_argument("--interval", type=float, default=3.0,
                        help="Seconds between requests per worker (default: 3)")
    args = parser.parse_args()

    api_key = resolve_api_key(args.api_key)
    watermark = args.watermark.lower() == "true"

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    images_dir = os.path.join(base_dir, "output", "res", "images")
    output_dir = args.output or os.path.join(base_dir, "output", "res", "videos")
    os.makedirs(output_dir, exist_ok=True)

    prompts_file = os.path.join(base_dir, "scripts", "image_prompts.py")
    all_prompts = load_prompts(prompts_file) if os.path.exists(prompts_file) else []

    shot_numbers = parse_shot_range(args.shots)
    default_prompt = args.prompt or "动态画面，缓慢推镜头， cinematic camera movement"

    print(f"Generating {len(shot_numbers)} video(s)")
    print(f"  Model: {args.model}")
    print(f"  Resolution: {args.resolution}")
    print(f"  Duration: {args.duration}s")
    print(f"  Watermark: {watermark}")
    print(f"  Workers: {args.workers}")
    print()

    succeeded = 0
    failed = 0
    skipped = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = []
        for shot_num in shot_numbers:
            future = executor.submit(
                process_one_shot, shot_num, api_key, args.model, args.resolution,
                args.duration, watermark, default_prompt, images_dir, output_dir,
                all_prompts, args.poll_interval, args.interval
            )
            futures.append(future)

        for future in concurrent.futures.as_completed(futures):
            _, ok, label = future.result()
            if label == "skipped":
                skipped += 1
            elif label == "no_image":
                failed += 1
            elif ok:
                succeeded += 1
            else:
                failed += 1

    print(f"\nDone: {succeeded} succeeded, {failed} failed, {skipped} skipped")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
