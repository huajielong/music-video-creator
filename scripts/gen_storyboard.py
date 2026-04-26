#!/usr/bin/env python3
"""
Generate storyboard markdown from lyrics sections.

Usage:
    python scripts/gen_storyboard.py --title "Song Title" --style "visual style" --output output/storyboard.md
    python scripts/gen_storyboard.py --title "笑傲江湖" --style "国风武侠" --output output/storyboard.md

Then review and edit the prompts before batch-generating images.
"""

import argparse
import os


def generate_storyboard(title: str, style: str, lyrics_structure: list[dict]) -> list[dict]:
    """Generate shot list from lyrics sections. Returns list of {section, shot_num, prompt}."""
    shots = []

    # Intro (2 shots, music intro before vocals)
    shots.append({
        "section": "intro",
        "prompt": f"云海翻涌中的巍峨山巅，朝阳初升金光破云，{style}，电影质感，16:9，大远景"
    })
    shots.append({
        "section": "intro",
        "prompt": f"佩剑少年立于山巅俯视云海，衣袂飘动，剪影，{style}，电影感，16:9，全景"
    })

    for section in lyrics_structure:
        name = section["name"]
        lines = section["lines"]
        count = len(lines)

        if name.startswith("verse"):
            for line in lines:
                shots.append(verse_shot(line, style))
        elif name.startswith("pre-chorus") or name.startswith("pre_chorus"):
            for line in lines:
                shots.append(pre_chorus_shot(line, style))
        elif name.startswith("chorus"):
            for line in lines:
                shots.append(chorus_shot(line, style))
        elif name.startswith("bridge"):
            for line in lines:
                shots.append(bridge_shot(line, style))

    # Outro (2 shots)
    shots.append({
        "section": "outro",
        "prompt": f"孤帆远影消失在天际尽头，暮色苍茫，{style}，电影感，16:9，大远景"
    })
    shots.append({
        "section": "outro",
        "prompt": f"云海翻涌山巅空无一人，只余剑痕一道，余韵悠长，{style}，电影感，16:9，大远景"
    })

    # Assign shot numbers
    for i, shot in enumerate(shots, 1):
        shot["shot_num"] = i

    return shots


def verse_shot(line: str, style: str) -> dict:
    """Map a verse lyric line to a visual shot."""
    mappings = [
        (["踏遍千山", "暮雪朝霜"], "身披斗笠的侠客踏雪行于山径，雪花纷飞，远山连绵，国风武侠，写实电影感，冷蓝与雪白对比，16:9，全景"),
        (["一剑轻挥", "斩断多少过往"], "古剑出鞘寒光一闪，剑刃映出过往幻影，特写，金属质感，国风武侠，光影对比，16:9，特写"),
        (["风起云涌", "谁在主沉浮"], "峡谷间风云突变，乌云翻滚笼罩群峰，气势磅礴，国风武侠，电影感，明暗对比，16:9，大远景"),
        (["回首天涯", "灯火已黄昏"], "侠客回望远方天涯，山脚下村落灯火初上，暮色暖光，国风武侠，温情与苍凉对比，16:9，远景"),
        (["孤帆远影", "碧空尽处"], "一叶孤舟顺江而下，碧空万里水天一色，写实电影感，国风水墨意境，16:9，大远景"),
        (["一曲长歌", "吹散多少迷雾"], "侠客临江吹笛/长歌，江面薄雾被声浪荡开，艺术感，国风武侠，诗意朦胧，16:9，中景"),
        (["刀光剑影", "不过一场梦"], "刀剑交错的残影在暮色中消散，如梦境幻影，写实电影感，动态模糊，16:9，中景"),
        (["举杯邀月", "对影成三人"], "月下独酌，酒杯倒映明月，侠客身影在月光下拉长，写实电影感，孤寂诗意，16:9，中景"),
    ]
    for keywords, prompt in mappings:
        if any(k in line for k in keywords):
            return {"section": "verse", "prompt": f"{prompt}"}
    return {"section": "verse", "prompt": f"山野之间侠客独行，{line}的意境，国风武侠，写实电影感，16:9，中景"}


def pre_chorus_shot(line: str, style: str) -> dict:
    mappings = [
        (["红尘滚滚", "把酒当歌"], "酒碗高举仰头痛饮，背景红尘飞扬，豪迈洒脱，国风武侠，暖色调，电影感，16:9，中近景"),
        (["醉卧沙场", "谁人笑我"], "战后沙场醉卧于旗下，斜阳映照身影，放浪不羁，国风武侠，金黄暖调，16:9，全景"),
    ]
    for keywords, prompt in mappings:
        if any(k in line for k in keywords):
            return {"section": "pre-chorus", "prompt": f"{prompt}"}
    return {"section": "pre-chorus", "prompt": f"豪迈洒脱的国风场景，{line}的意境，国风武侠，暖色调，电影感，16:9，中景"}


def chorus_shot(line: str, style: str) -> dict:
    mappings = [
        (["一笑江湖", "恩怨随风"], "骏马奔驰于草原/山间，侠客策马扬鞭，意气风发，国风武侠，暖金调，动感，16:9，大远景"),
        (["策马奔腾", "天地任我游"], "万马奔腾或单人纵马于天地之间，广阔无垠，自由豪迈，国风武侠，电影感，16:9，大远景"),
        (["一笑江湖", "爱恨入酒"], "酒碗中倒映着江湖风云变幻，仰头饮尽，潇洒不羁，国风武侠，特写抒情，16:9，特写"),
        (["山河万里", "逍遥到白头"], "侠客与马立于山河之巅眺望远方，万里江山尽收眼底，国风武侠，史诗感，16:9，大远景"),
    ]
    for keywords, prompt in mappings:
        if any(k in line for k in keywords):
            return {"section": "chorus", "prompt": f"{prompt}"}
    return {"section": "chorus", "prompt": f"豪迈壮阔的武侠场景，{line}的意境，国风武侠，电影感，16:9，全景"}


def bridge_shot(line: str, style: str) -> dict:
    mappings = [
        (["江山如画", "不及你回眸"], "一幅水墨江山画卷前，佳人回眸的幻影浮现又消散，国风武侠，写实电影感，诗意淡彩，16:9，中景"),
        (["一曲终了", "人已在天涯"], "笛声落下最后一音，余音中身影渐行渐远，国风武侠，电影感，暮色渐变，16:9，远景"),
    ]
    for keywords, prompt in mappings:
        if any(k in line for k in keywords):
            return {"section": "bridge", "prompt": f"{prompt}"}
    return {"section": "bridge", "prompt": f"诗意悠远的国风场景，{line}的意境，国风武侠，淡雅色调，16:9，中景"}


def lyrics_structure_from_text(text: str) -> list[dict]:
    """Parse lyrics text into sections with their lines."""
    import re
    sections = re.split(r'\[([\w\s-]+)\]', text)
    result = []
    for i, part in enumerate(sections):
        part = part.strip()
        if not part:
            continue
        if i % 2 == 1:
            name = part.lower().replace(" ", "_")
            lines = []
            # Next element (i+1) has the lines
            if i + 1 < len(sections):
                lines = [l.strip() for l in sections[i + 1].strip().split("\n") if l.strip()]
            result.append({"name": name, "lines": lines})
    return result


def to_markdown(title: str, style: str, shots: list[dict]) -> str:
    """Convert shot list to markdown storyboard."""
    mood_map = {
        "intro": "意境铺陈",
        "verse": "叙事展开",
        "pre-chorus": "情绪递进",
        "chorus": "高潮释放",
        "bridge": "情感转折",
        "outro": "余韵收束",
    }

    lines = [f"# {title} - 分镜脚本\n"]
    lines.append("## 视觉风格")
    lines.append(f"- **风格**: {style}")
    lines.append("- **色调**: 暖金与冷蓝对比，夕阳金与暮光紫")
    lines.append("- **比例**: 16:9")
    lines.append("- **节奏**: 快慢交替，与歌曲段落同步\n")

    # Group by section
    # Group by base section type (verse_1 and verse_2 both → verse)
    def base_section(name: str) -> str:
        name = name.lower().replace("_", "-")
        for base in ["pre-chorus", "intro", "verse", "chorus", "bridge", "outro"]:
            if name.startswith(base):
                return base
        return name

    current_section = None
    for shot in shots:
        section = base_section(shot["section"])
        section = shot["section"]
        if section != current_section:
            current_section = section
            mood = mood_map.get(section, "")
            lines.append(f"### {section.capitalize()} ({mood})")

        lines.append(f"- Shot {shot['shot_num']:03d}: {shot['prompt']}")

    lines.append("")
    lines.append("## 技术要求")
    lines.append("- 每个镜头时长: 3-5秒")
    lines.append("- 图片分辨率: 1024×576 (16:9)")
    lines.append("- 视频时长: 3-4秒/片段")
    lines.append("- 过渡效果: 淡入淡出")

    return "\n".join(lines)


def extract_prompts(shots: list[dict]) -> list[str]:
    """Extract just the image generation prompts as a list."""
    return [shot["prompt"] for shot in shots]


def main():
    parser = argparse.ArgumentParser(
        description="Generate shot-by-shot storyboard from lyrics",
        epilog="Examples:\n"
               "  %(prog)s --title \"My Song\" --style \"cinematic, wuxia\" --lyrics \"[Verse]...\"\n"
               "  %(prog)s --title \"Song\" --style \"sci-fi\" --input lyrics.txt --output storyboard.md --prompts image_prompts.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--title", required=True, help="Song title")
    parser.add_argument("--style", default="国风武侠，写实电影感，中国古典美学", help="Visual style description for all shots")
    parser.add_argument("--lyrics", help="Lyrics with [Section] tags, use \\n for newlines")
    parser.add_argument("--input", help="Lyrics text file path (alternative to --lyrics)")
    parser.add_argument("--output", default=None, help="Output storyboard markdown path")
    parser.add_argument("--prompts", default=None, help="Output prompts Python file path (used by batch_generate_images.py)")
    args = parser.parse_args()

    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            lyrics_text = f.read()
    elif args.lyrics:
        lyrics_text = args.lyrics.replace("\\n", "\n")
    else:
        print("Error: Provide --lyrics or --input", file=sys.stderr)
        sys.exit(1)

    structure = lyrics_structure_from_text(lyrics_text)
    shots = generate_storyboard(args.title, args.style, structure)
    markdown = to_markdown(args.title, args.style, shots)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(markdown)
        print(f"Storyboard saved: {args.output}")

    if args.prompts:
        prompts = extract_prompts(shots)
        os.makedirs(os.path.dirname(args.prompts) or ".", exist_ok=True)
        with open(args.prompts, "w", encoding="utf-8") as f:
            f.write("# Auto-generated image prompts for batch_generate_images.py\n")
            f.write(f"# Song: {args.title}\n")
            f.write(f"# Total: {len(prompts)} shots\n\n")
            f.write("PROMPTS = [\n")
            for p in prompts:
                f.write(f"    {json.dumps(p, ensure_ascii=False)},\n")
            f.write("]\n")
        print(f"Prompts saved: {args.prompts}")

    if not args.output:
        print(markdown)


if __name__ == "__main__":
    import json
    import sys
    main()
