#!/usr/bin/env python3
"""
Batch generate storyboard images via Doubao Seedream API.

Features: parallel execution, retry with backoff, resume (skip existing), error summary.

Usage:
    python scripts/batch_generate_images.py --watermark false --workers 3
"""

import argparse
import concurrent.futures
import json
import os
import sys
import threading
import time
import requests

ARK_BASE = "https://ark.cn-beijing.volces.com"


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
    print("Error: No ARK_API_KEY found. Set via --api-key, env var, or .env", file=sys.stderr)
    sys.exit(1)


def load_prompts(path: str) -> list[str]:
    ns = {}
    with open(path, encoding="utf-8") as f:
        exec(f.read(), ns)
    return ns.get("PROMPTS", [])


def _retryable_error(exc: Exception) -> bool:
    """True if the exception is worth retrying (network/server errors)."""
    return isinstance(exc, (requests.exceptions.Timeout, requests.exceptions.ConnectionError))


def _is_retryable_status(status: int) -> bool:
    """Retry on 5xx server errors, not 4xx client errors."""
    return 500 <= status < 600


def generate_image(prompt: str, api_key: str, output_path: str,
                   model: str, size: str, watermark: bool) -> bool:
    """Call Doubao Seedream API to generate one image (with retry)."""
    url = f"{ARK_BASE}/api/v3/images/generations"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "prompt": prompt,
        "n": 1,
        "size": size,
        "watermark": watermark,
    }

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=120)
            if resp.status_code != 200:
                if _is_retryable_status(resp.status_code) and attempt < max_retries:
                    wait = 5 * (2 ** (attempt - 1))
                    print(f"  [Retry {attempt}/{max_retries}] API {resp.status_code}, waiting {wait}s...")
                    time.sleep(wait)
                    continue
                print(f"  API error {resp.status_code}: {resp.text[:200]}", file=sys.stderr)
                return False

            data = resp.json()
            img_data = None
            choices = data.get("data", [])
            if choices:
                b64 = choices[0].get("b64_json")
                if b64:
                    import base64
                    img_data = base64.b64decode(b64)
                else:
                    img_url = choices[0].get("url")
                    if img_url:
                        img_resp = requests.get(img_url, timeout=30)
                        img_resp.raise_for_status()
                        img_data = img_resp.content

            if img_data:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(img_data)
                print(f"  -> {output_path} ({len(img_data)} bytes)")
                return True
            else:
                print(f"  No image data in response: {json.dumps(data, ensure_ascii=False)[:200]}")
                return False

        except requests.exceptions.Timeout:
            if attempt < max_retries:
                wait = 5 * (2 ** (attempt - 1))
                print(f"  [Retry {attempt}/{max_retries}] Timeout, waiting {wait}s...")
                time.sleep(wait)
            else:
                print("  Timeout (120s) after all retries", file=sys.stderr)
                return False
        except Exception as e:
            if _retryable_error(e) and attempt < max_retries:
                wait = 5 * (2 ** (attempt - 1))
                print(f"  [Retry {attempt}/{max_retries}] {e}, waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"  Error: {e}", file=sys.stderr)
                return False

    return False


_print_lock = threading.Lock()


def _wait_interval(interval: float):
    """Per-worker rate-limiting sleep."""
    time.sleep(interval)


def process_one_shot(shot_num: int, prompt: str, api_key: str, model: str,
                     size: str, watermark: bool, output_dir: str,
                     interval: float) -> tuple[int, bool, str]:
    """Process a single shot. Returns (shot_num, success, status_label)."""
    fname = f"shot_{shot_num:03d}.png"
    fpath = os.path.join(output_dir, fname)

    if os.path.exists(fpath):
        with _print_lock:
            print(f"[{shot_num:03d}] already exists, skipping")
        return shot_num, True, "skipped"

    with _print_lock:
        print(f"[{shot_num:03d}] submitting...")
    start_t = time.time()
    ok = generate_image(prompt, api_key, fpath, model, size, watermark)
    elapsed = time.time() - start_t
    with _print_lock:
        label = "done" if ok else "failed"
        print(f"[{shot_num:03d}] {label} ({elapsed:.0f}s)")

    _wait_interval(interval)
    return shot_num, ok, "done" if ok else "failed"


def main():
    parser = argparse.ArgumentParser(description="Batch generate storyboard images")
    parser.add_argument("--watermark", default="false", choices=["true", "false"])
    parser.add_argument("--api-key", default=None, help="ARK API key")
    parser.add_argument("--model", default="doubao-seedream-5-0-260128", help="Model ID")
    parser.add_argument("--size", default="2560x1440", help="Image size")
    parser.add_argument("--output", default=None, help="Output directory")
    parser.add_argument("--prompts", default=None, help="Prompts Python file")
    parser.add_argument("--start", type=int, default=1, help="Start shot number (1-based)")
    parser.add_argument("--end", type=int, default=0, help="End shot number (0 = all)")
    parser.add_argument("--workers", type=int, default=3, help="Parallel workers (default: 3)")
    parser.add_argument("--interval", type=float, default=3.0,
                        help="Seconds between requests per worker (default: 3)")
    args = parser.parse_args()

    api_key = resolve_api_key(args.api_key)
    watermark = args.watermark.lower() == "true"

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompts_file = args.prompts or os.path.join(base_dir, "scripts", "image_prompts.py")
    output_dir = args.output or os.path.join(base_dir, "output", "res", "images")

    prompts = load_prompts(prompts_file)
    if not prompts:
        print(f"Error: No prompts found in {prompts_file}", file=sys.stderr)
        sys.exit(1)

    total = len(prompts)
    start_idx = max(0, args.start - 1)
    end_idx = args.end if args.end > 0 else total
    batch = list(enumerate(prompts[start_idx:end_idx], start=args.start))

    print(f"Generating {len(batch)}/{total} images")
    print(f"  Model: {args.model}")
    print(f"  Size: {args.size}")
    print(f"  Watermark: {watermark}")
    print(f"  Workers: {args.workers}")
    print(f"  Output: {output_dir}")
    print()

    succeeded = 0
    failed = 0
    skipped = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = []
        for shot_num, prompt in batch:
            future = executor.submit(
                process_one_shot, shot_num, prompt, api_key, args.model,
                args.size, watermark, output_dir, args.interval
            )
            futures.append(future)

        for future in concurrent.futures.as_completed(futures):
            _, ok, label = future.result()
            if label == "skipped":
                skipped += 1
            elif ok:
                succeeded += 1
            else:
                failed += 1

    print(f"\nDone: {succeeded} succeeded, {failed} failed, {skipped} skipped ({output_dir})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
