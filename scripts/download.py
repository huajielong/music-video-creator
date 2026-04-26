#!/usr/bin/env python3
"""
Download MP3 from Tunee share page.

Usage:
    python scripts/download.py --id <music_id>
    python scripts/download.py --url https://www.tunee.ai/music/<id>

The generate API returns a share page URL (not a direct audio file).
This script opens that page in Playwright, clicks the download button,
and saves the MP3 to output/<title>.mp3.

Why Playwright: the CDN (media-cdn.tunee.ai) requires browser-level
cookies/headers — direct curl/requests get 403 Forbidden.
"""

import argparse
import os
import re
import sys
import asyncio
from playwright.async_api import async_playwright

BASE_URL = "https://www.tunee.ai/music"


async def download_mp3(music_id: str) -> str | None:
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
            # Sanitize filename for Windows
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
