#!/usr/bin/env python3
"""
tools/subtitles.py — Subtitle processor for geekzen-long factory.

Converts subtitle_raw.srt (edge-tts SubMaker output) into 4 files:
    subtitle_zh_hans.srt   Simplified Chinese SRT
    subtitle_zh_hans.vtt   Simplified Chinese VTT
    subtitle_zh_hant.srt   Traditional Chinese SRT  (OpenCC s2twp)
    subtitle_zh_hant.vtt   Traditional Chinese VTT

Usage:
    python tools/subtitles.py <output_dir>
"""
import os
import re
import shutil
import sys

import opencc


def srt_to_vtt(srt_path: str, vtt_path: str):
    with open(srt_path, encoding="utf-8") as f:
        content = f.read()

    lines = content.strip().splitlines()
    vtt_lines = ["WEBVTT", ""]

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # sequence number
        if re.match(r"^\d+$", line):
            vtt_lines.append(line)
            i += 1
        # timestamp: convert comma → dot
        elif "-->" in line:
            vtt_lines.append(line.replace(",", "."))
            i += 1
        # text or blank
        else:
            vtt_lines.append(line)
            i += 1

    with open(vtt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(vtt_lines) + "\n")


def to_traditional(src: str, dst: str):
    converter = opencc.OpenCC("s2twp")
    with open(src, encoding="utf-8") as f:
        content = f.read()
    with open(dst, "w", encoding="utf-8") as f:
        f.write(converter.convert(content))


def process_all(output_dir: str):
    raw = os.path.join(output_dir, "subtitle_raw.srt")
    if not os.path.exists(raw):
        print(f"❌ {raw} 不存在，请先执行 tts.py")
        sys.exit(1)

    hans_srt = os.path.join(output_dir, "subtitle_zh_hans.srt")
    hans_vtt = os.path.join(output_dir, "subtitle_zh_hans.vtt")
    hant_srt = os.path.join(output_dir, "subtitle_zh_hant.srt")
    hant_vtt = os.path.join(output_dir, "subtitle_zh_hant.vtt")

    shutil.copy(raw, hans_srt)
    print(f"✅ 简体 SRT: {hans_srt}")

    srt_to_vtt(hans_srt, hans_vtt)
    print(f"✅ 简体 VTT: {hans_vtt}")

    to_traditional(hans_srt, hant_srt)
    print(f"✅ 繁體 SRT: {hant_srt}")

    srt_to_vtt(hant_srt, hant_vtt)
    print(f"✅ 繁體 VTT: {hant_vtt}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/subtitles.py <output_dir>")
        sys.exit(1)
    process_all(sys.argv[1])
