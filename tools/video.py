#!/usr/bin/env python3
"""
tools/video.py — 最终视频合成

输入（全部来自 output_dir/）：
  slides/slide_*.png       幻灯片 PNG 序列
  slides_timing.json       每张幻灯片的时长
  audio_tw.mp3             音频
  subtitle_zh_hant.srt     字幕（繁体）

输出：
  output_dir/final.mp4

Usage:
  python tools/video.py <output_dir>
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def _build_concat(slides_dir: Path, timing: list[dict], tmp_path: str) -> None:
    lines = []
    last_added: str | None = None
    for i, slide in enumerate(timing):
        png = slides_dir / f"slide_{i:03d}.png"
        if not png.exists():
            print(f"  ⚠ 找不到 {png.name}，跳过")
            continue
        last_added = str(png.absolute())
        lines.append(f"file '{last_added}'")
        lines.append(f"duration {slide.get('duration', 2.0):.3f}")

    # ffmpeg concat demuxer: last successfully added frame must be listed twice
    if last_added:
        lines.append(f"file '{last_added}'")

    with open(tmp_path, "w") as f:
        f.write("\n".join(lines))


def run_video(output_dir: str) -> None:
    output_dir = Path(output_dir)
    slides_dir = output_dir / "slides"
    timing_path = output_dir / "slides_timing.json"
    audio_path = output_dir / "audio_tw.mp3"
    srt_path = output_dir / "subtitle_zh_hant.srt"
    final_path = output_dir / "final.mp4"

    for p, label in [(timing_path, "slides_timing.json"), (audio_path, "audio_tw.mp3"), (srt_path, "subtitle_zh_hant.srt")]:
        if not p.exists():
            print(f"❌ 找不到 {p}，请先运行 present.py / tts.py / subtitles.py")
            sys.exit(1)

    with open(timing_path, encoding="utf-8") as f:
        timing = json.load(f)

    print(f"  → {len(timing)} 张幻灯片 + 音频 → {final_path.name}")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
        concat_path = tmp.name

    _build_concat(slides_dir, timing, concat_path)

    subtitle_style = (
        "FontName=Noto Serif CJK TC,"
        "FontSize=36,"
        "PrimaryColour=&H00F0EBE1,"
        "OutlineColour=&H99000000,"
        "Outline=1.5,"
        "Shadow=0,"
        "Alignment=2,"
        "MarginV=60"
    )

    # Escape path for ffmpeg lavfi filter parser (colons and backslashes are special)
    srt_escaped = str(srt_path).replace("\\", "\\\\").replace(":", "\\:")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_path,
        "-i", str(audio_path),
        "-vf", f"subtitles=filename='{srt_escaped}':force_style='{subtitle_style}',fade=t=in:st=0:d=0.5",
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(final_path),
    ]

    print("  → ffmpeg 合成中（可能需要几分钟）…")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    finally:
        os.unlink(concat_path)

    if result.returncode != 0:
        print("❌ ffmpeg 错误：")
        print(result.stderr[-3000:])
        sys.exit(1)

    mb = final_path.stat().st_size / (1024 * 1024)
    print(f"✅ 视频：{final_path}（{mb:.1f} MB）")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/video.py <output_dir>")
        sys.exit(1)
    run_video(sys.argv[1])
