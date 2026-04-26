#!/usr/bin/env python3
"""Generate a demo preview GIF from generated storyboard images."""
import os
import sys

try:
    from PIL import Image
except ImportError:
    print("Pillow required: pip install Pillow", file=sys.stderr)
    sys.exit(1)

IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", "res", "images")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Key shots that represent different parts of the song
key_shots = [1, 3, 7, 9, 13, 16, 17, 21, 23, 26]

frames = []
for num in key_shots:
    path = os.path.join(IMAGES_DIR, f"shot_{num:03d}.png")
    if not os.path.exists(path):
        print(f"Skip shot_{num:03d}.png (not found)")
        continue
    img = Image.open(path).convert("RGB")
    # Resize to consistent width for GIF
    aspect = img.height / img.width
    new_w = 480
    new_h = int(new_w * aspect)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    # Show each frame for 1.5 seconds (at 100ms = 15 frames each)
    for _ in range(15):
        frames.append(img)

if not frames:
    print("No images found. Run batch_generate_images.py first.", file=sys.stderr)
    sys.exit(1)

gif_path = os.path.join(OUTPUT_DIR, "demo_preview.gif")
frames[0].save(
    gif_path,
    save_all=True,
    append_images=frames[1:],
    duration=100,
    loop=0,
    optimize=True,
)
size_kb = os.path.getsize(gif_path) / 1024
print(f"Demo GIF saved: {gif_path} ({size_kb:.0f} KB, {len(key_shots)} frames)")
