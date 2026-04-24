#!/usr/bin/env python3
"""
tools/tts.py — TTS generator for geekzen-long factory.

Usage:
    python tools/tts.py <script.txt> <output_dir> [voice] [rate]

Note on SSML:
    edge-tts uses the Microsoft Edge browser TTS endpoint, which does NOT
    accept <break> tags in SSML (returns "No audio received").
    Natural pauses at Chinese punctuation (。！？……) combined with rate=-10%
    give sufficient pacing. No explicit SSML breaks needed.
"""
import asyncio
import os
import subprocess
import sys

import edge_tts
from edge_tts import SubMaker

VOICE_TW = "zh-TW-YunJheNeural"
VOICE_CN = "zh-CN-YunxiNeural"
DEFAULT_RATE = "-10%"


async def generate(
    script_path: str,
    output_dir: str,
    voice: str = VOICE_TW,
    rate: str = DEFAULT_RATE,
):
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(script_path):
        print(f"❌ 找不到脚本文件: {script_path}")
        sys.exit(1)

    with open(script_path, encoding="utf-8") as f:
        raw_text = f.read().strip()

    audio_path = os.path.join(output_dir, "audio_tw.mp3")
    srt_path = os.path.join(output_dir, "subtitle_raw.srt")

    # SentenceBoundary gives one subtitle cue per sentence — better for video
    comm = edge_tts.Communicate(
        raw_text,
        voice,
        rate=rate,
        boundary="SentenceBoundary",
    )

    sub = SubMaker()
    audio_bytes = []

    async for chunk in comm.stream():
        if chunk["type"] == "audio":
            audio_bytes.append(chunk["data"])
        elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
            sub.feed(chunk)

    with open(audio_path, "wb") as f:
        f.write(b"".join(audio_bytes))

    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(sub.get_srt())

    print(f"✅ 音频：{audio_path}")
    print(f"✅ 字幕：{srt_path}")
    _print_duration(audio_path)


def _print_duration(audio_path: str):
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        secs = float(result.stdout.strip())
        print(f"📊 时长：{int(secs // 60)}分{int(secs % 60)}秒")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python tools/tts.py <script.txt> <output_dir> [voice] [rate]")
        sys.exit(1)
    script_path = sys.argv[1]
    output_dir = sys.argv[2]
    voice = sys.argv[3] if len(sys.argv) > 3 else VOICE_TW
    rate = sys.argv[4] if len(sys.argv) > 4 else DEFAULT_RATE
    print(f"🎙️  TTS 生成中…  声音={voice}  语速={rate}")
    asyncio.run(generate(script_path, output_dir, voice, rate))
