#!/usr/bin/env python3
"""
Batch generate storyboard images via Doubao Seedream API.

Usage:
    python scripts/batch_generate_images.py --watermark false

Args:
    --watermark   Add watermark to images (default: false)
    --api-key     ARK API key (default: from .env or ARK_API_KEY env)
    --model       Model ID (default: doubao-seedream-x2)
    --size        Image size (default: 1024x576)
    --output      Output directory (default: output/res/images/)
    --prompts     Prompts file (default: scripts/image_prompts.py)
    --start       Start shot number (1-based, default: 1)
    --end         End shot number (default: all)
    --interval    Seconds between requests (default: 3)
"""

import argparse
import json
import os
import sys
import time
import requests

ARK_BASE = "https://ark.cn-beijing.volces.com"


def resolve_api_key(cli_key: str | None) -> str:
    for key in (cli_key, os.environ.get("ARK_API_KEY")):
        if key and key.strip() and key.strip() != "your-api-key-here":
            return key.strip()
    # Try .env file
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
    """Load PROMPTS list from a Python file."""
    ns = {}
    with open(path, encoding="utf-8") as f:
        code = f.read()
    exec(code, ns)
    return ns.get("PROMPTS", [])


def generate_image(prompt: str, api_key: str, output_path: str,
                   model: str, size: str, watermark: bool) -> bool:
    """Call Doubao Seedream API to generate one image."""
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

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=120)
        if resp.status_code != 200:
            print(f"  API error {resp.status_code}: {resp.text[:200]}", file=sys.stderr)
            return False

        data = resp.json()
        # OpenAI-compatible response: data[0].b64_json or url
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
        print("  Timeout (120s)", file=sys.stderr)
        return False
    except Exception as e:
        print(f"  Error: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Batch generate storyboard images")
    parser.add_argument("--watermark", default="false", choices=["true", "false"],
                        help="Add watermark to images (default: false)")
    parser.add_argument("--api-key", default=None, help="ARK API key")
    parser.add_argument("--model", default="doubao-seedream-5-0-260128", help="Model ID")
    parser.add_argument("--size", default="2560x1440", help="Image size (min 3686400 pixels, default: 2560x1440 16:9)")
    parser.add_argument("--output", default=None, help="Output directory")
    parser.add_argument("--prompts", default=None, help="Prompts Python file")
    parser.add_argument("--start", type=int, default=1, help="Start shot number (1-based)")
    parser.add_argument("--end", type=int, default=0, help="End shot number (0 = all)")
    args = parser.parse_args()

    api_key = resolve_api_key(args.api_key)
    watermark = args.watermark.lower() == "true"

    # Resolve paths
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompts_file = args.prompts or os.path.join(base, "scripts", "image_prompts.py")
    output_dir = args.output or os.path.join(base, "output", "res", "images")

    prompts = load_prompts(prompts_file)
    if not prompts:
        print(f"Error: No prompts found in {prompts_file}", file=sys.stderr)
        sys.exit(1)

    total = len(prompts)
    start_idx = max(0, args.start - 1)
    end_idx = args.end if args.end > 0 else total
    batch = prompts[start_idx:end_idx]

    print(f"Generating {len(batch)}/{total} images")
    print(f"  Model: {args.model}")
    print(f"  Size: {args.size}")
    print(f"  Watermark: {watermark}")
    print(f"  Output: {output_dir}")
    print()

    success = 0
    for i, prompt in enumerate(batch):
        shot_num = start_idx + i + 1
        fname = f"shot_{shot_num:03d}.png"
        fpath = os.path.join(output_dir, fname)

        if os.path.exists(fpath):
            print(f"[{shot_num:03d}] Skip (exists): {prompt[:40]}...")
            success += 1
            continue

        print(f"[{shot_num:03d}] {prompt[:60]}...")
        ok = generate_image(prompt, api_key, fpath, args.model, args.size, watermark)
        if ok:
            success += 1
        time.sleep(3)  # rate limit

    print(f"\nDone: {success}/{len(batch)} images generated ({output_dir})")


if __name__ == "__main__":
    main()
