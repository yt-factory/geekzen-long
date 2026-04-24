#!/usr/bin/env python3
"""
极客禅长视频全流程 Pipeline

用法：
  python tools/pipeline.py <主题词> [选项]

例：
  python tools/pipeline.py "拖延症"
  python tools/pipeline.py "拖延症" --entry "我有三个未完成的项目..."
  python tools/pipeline.py "拖延症" --skip-think      # 复用已有 think_output.md
  python tools/pipeline.py "拖延症" --skip-write      # 复用已有 script.txt
  python tools/pipeline.py "拖延症" --skip-think --skip-write  # 只跑 TTS + 字幕
"""
import argparse
import asyncio
import os
import re
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).parent
EPISODES_DIR = TOOLS_DIR.parent / "episodes"

sys.path.insert(0, str(TOOLS_DIR))

from think import run_think
from write import run_write, clean_for_tts
from tts import generate
from subtitles import process_all


def slugify(text: str) -> str:
    return re.sub(r'[<>:"/\\|?*\s]+', "-", text).strip("-")


def setup_dirs(topic: str) -> tuple[Path, Path]:
    episode_dir = EPISODES_DIR / topic.replace("/", "-")
    output_dir = episode_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return episode_dir, output_dir


def banner(step: int, title: str):
    print(f"\n{'─'*52}")
    print(f"  Step {step}  {title}")
    print(f"{'─'*52}")


async def run_pipeline(
    topic: str,
    entry: str = "",
    closing: str = "",
    skip_think: bool = False,
    skip_write: bool = False,
    voice: str = "zh-TW-YunJheNeural",
    rate: str = "-10%",
    only_think: bool = False,
    only_write: bool = False,
    only_tts: bool = False,
):
    _check_api_key(skip_think, skip_write, only_tts)

    episode_dir, output_dir = setup_dirs(topic)
    think_path = episode_dir / "think_output.md"
    write_path = episode_dir / "write_output.md"
    script_path = episode_dir / "script.txt"

    print(f"\n🚀  极客禅 Pipeline")
    print(f"    主题：{topic}")
    print(f"    目录：{episode_dir}")

    # ── Step 1: Think ──────────────────────────────────────────────────
    banner(1, "追本之箭（Think）")
    if skip_think:
        if not think_path.exists():
            _die(f"--skip-think 指定了跳过，但找不到 {think_path}")
        think_content = think_path.read_text(encoding="utf-8")
        print(f"  复用 {think_path}")
    else:
        think_content = run_think(topic, str(think_path))

    _preview("Think 预览", think_content, 280)
    if only_think:
        return

    # ── Step 2: Write ──────────────────────────────────────────────────
    banner(2, "写作引擎（Write）")
    if skip_write:
        if not script_path.exists():
            _die(f"--skip-write 指定了跳过，但找不到 {script_path}")
        print(f"  复用 {script_path}")
    else:
        write_content = run_write(think_content, entry, closing, str(write_path))
        script = clean_for_tts(write_content)
        script_path.write_text(script, encoding="utf-8")
        print(f"  script.txt 已生成（{len(script)} 字）")
        _preview("脚本预览", script, 200)
    if only_write:
        return

    # ── Step 3: TTS ────────────────────────────────────────────────────
    banner(3, "TTS 生成音频")
    await generate(str(script_path), str(output_dir), voice=voice, rate=rate)

    # ── Step 4: Subtitles ──────────────────────────────────────────────
    banner(4, "字幕处理（简体 / 繁体）")
    process_all(str(output_dir))
    if only_tts:
        return

    # ── Done ───────────────────────────────────────────────────────────
    print(f"\n{'═'*52}")
    print(f"  ✅  全流程完成！")
    print(f"{'═'*52}")
    print(f"\n输出目录：{output_dir}\n")
    for f in sorted(output_dir.iterdir()):
        kb = f.stat().st_size / 1024
        print(f"  {f.name:<38} {kb:6.1f} KB")

    print(f"""
ffmpeg 合成参考：
  ffmpeg -i slides.mp4 \\
         -i {output_dir}/audio_tw.mp3 \\
         -vf "subtitles={output_dir}/subtitle_zh_hant.srt" \\
         -c:v libx264 -c:a aac \\
         {output_dir}/final.mp4
""")


# ── helpers ────────────────────────────────────────────────────────────

def _check_api_key(skip_think: bool, skip_write: bool, only_tts: bool = False):
    # only_tts bypasses both think and write unconditionally
    will_use_api = not only_tts and (not skip_think or not skip_write)
    if will_use_api and not os.environ.get("ANTHROPIC_API_KEY"):
            print("❌  ANTHROPIC_API_KEY 未设置。")
            print("   请先执行：export ANTHROPIC_API_KEY='sk-ant-...'")
            sys.exit(1)


def _preview(label: str, text: str, chars: int):
    print(f"\n── {label} ──")
    print(text[:chars].rstrip())
    if len(text) > chars:
        print("  …")


def _die(msg: str):
    print(f"❌  {msg}")
    sys.exit(1)


# ── CLI ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="极客禅长视频全流程 Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("topic", help="视频主题词，如：拖延症、为什么你的项目永远写不完")
    parser.add_argument("--entry", default="", help="入口段落（个人经历，约 100 字）")
    parser.add_argument("--closing", default="", help="结尾段落（个人化收尾，约 50 字）")
    parser.add_argument("--skip-think", action="store_true",
                        help="跳过 Think，复用已有 think_output.md")
    parser.add_argument("--skip-write", action="store_true",
                        help="跳过 Write，复用已有 script.txt")
    parser.add_argument("--voice", default="zh-TW-YunJheNeural", help="TTS 声音")
    parser.add_argument("--rate", default="-10%", help="语速调整（如 -10%%、-20%%）")
    parser.add_argument("--only-think", action="store_true", help="只运行 think，然后退出")
    parser.add_argument("--only-write", action="store_true", help="只运行 write，然后退出")
    parser.add_argument("--only-tts",   action="store_true", help="只运行 tts + subtitles，然后退出")

    args = parser.parse_args()
    asyncio.run(run_pipeline(
        topic=args.topic,
        entry=args.entry,
        closing=args.closing,
        skip_think=args.skip_think,
        skip_write=args.skip_write,
        voice=args.voice,
        rate=args.rate,
        only_think=args.only_think,
        only_write=args.only_write,
        only_tts=args.only_tts,
    ))
