#!/usr/bin/env python3
"""
Download MP3 from Tunee share page.

Usage:
    python scripts/download.py --id <music_id>
    python scripts/download.py --url https://www.tunee.ai/music/<id>

Strategy (automatic):
1. Direct URL extraction via requests (fast, no browser needed)
2. Fallback: Playwright browser automation (handles CDN 403)

The CDN (media-cdn.tunee.ai) may require browser-level cookies.
"""

import argparse
import os
import re
import sys
import asyncio
import time

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from playwright.async_api import async_playwright

BASE_URL = "https://www.tunee.ai/music"


def _extract_audio_url(music_id: str) -> str | None:
    """Extract direct audio URL from Tunee share page HTML. Polls until available."""
    share_url = f"{BASE_URL}/{music_id}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    for attempt in range(12):  # up to ~60s wait
        try:
            resp = requests.get(share_url, headers=headers, timeout=15)
            if resp.status_code != 200:
                time.sleep(5)
                continue
            # Match audioUrl in Next.js RSC payload (backslash-escaped)
            match = re.search(r'\\"audioUrl\\":\\"(https://[^\\]+?)\\"', resp.text)
            if match:
                url = match.group(1)
                if url != "null" and not url.endswith(".null"):
                    return url
            time.sleep(5)
        except Exception:
            time.sleep(5)
    return None


def _try_direct_download(music_id: str) -> str | None:
    """Download MP3 directly via extracted audio URL. Returns path or None."""
    if not HAS_REQUESTS:
        return None
    audio_url = _extract_audio_url(music_id)
    if not audio_url:
        return None
    output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{music_id}.mp3")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        resp = requests.get(audio_url, headers=headers, stream=True, timeout=60)
        if resp.status_code != 200:
            print(f"  Direct download returned {resp.status_code}", file=sys.stderr)
            return None
        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        size = os.path.getsize(output_path)
        print(f"Downloaded: {output_path} ({size} bytes)")
        return output_path
    except Exception as e:
        print(f"  Direct download failed: {e}", file=sys.stderr)
        return None


async def _download_with_playwright(music_id: str) -> str | None:
    """Fallback: use Playwright to click download on the share page."""
    share_url = f"{BASE_URL}/{music_id}"
    output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    os.makedirs(output_dir, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        print(f"Opening share page: {share_url}")
        await page.goto(share_url, wait_until="networkidle")
        await page.wait_for_timeout(3000)

        buttons = await page.query_selector_all("button")
        if not buttons:
            print("Error: No buttons found on page", file=sys.stderr)
            await browser.close()
            return None

        print(f"Clicking download button...")
        try:
            async with page.expect_download(timeout=15000) as download_info:
                await buttons[0].click()
            download = await download_info.value

            suggested = download.suggested_filename or f"{music_id}.mp3"
            safe_name = re.sub(r'[<>:"/\\|?*]', '_', suggested)
            output_path = os.path.join(output_dir, safe_name)

            await download.save_as(output_path)
            size = os.path.getsize(output_path)
            print(f"Downloaded: {output_path} ({size} bytes)")
            await browser.close()
            return output_path
        except Exception as e:
            print(f"Download failed: {e}", file=sys.stderr)
            await browser.close()
            return None


async def download_mp3(music_id: str) -> str | None:
    """Download MP3 from Tunee. Tries direct URL extraction first, falls back to Playwright."""
    result = _try_direct_download(music_id)
    if result:
        return result
    print("  Direct download unavailable, falling back to Playwright...")
    return await _download_with_playwright(music_id)


def main():
    parser = argparse.ArgumentParser(description="Download MP3 from Tunee")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--id", help="Music ID (from generate output)")
    group.add_argument("--url", help="Full Tunee share URL")
    args = parser.parse_args()

    music_id = args.id or args.url.rstrip("/").split("/")[-1]
    result = asyncio.run(download_mp3(music_id))
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
