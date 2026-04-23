#!/usr/bin/env python3
"""
tools/present.py — 高桥流幻灯片生成器

输入：
  script.txt              视频脚本（纯文本）
  output_dir/             输出根目录
  [subtitle_zh_hans.srt]  字幕（用于计算总时长）

输出（全部写入 output_dir/）：
  slides.html             可交互预览版
  slides_timing.json      每张幻灯片的起止时间
  slides/slide_000.png … slide_NNN.png  PNG 序列

Usage:
  python tools/present.py <script.txt> <output_dir> [srt_path]
"""
import asyncio
import json
import re
import sys
from pathlib import Path

# ── 幻灯片提取（无 API，读 slides_input.txt）────────────────────────────

def extract_slides(script_path: str) -> list[dict]:
    """
    优先读取同目录的 slides_input.txt（由 ljg-present 在 Claude Code 里生成）。
    如果不存在，fallback 到启发式算法。
    不再调用 Anthropic API。
    """
    episode_dir = Path(script_path).parent
    slides_input = episode_dir / "slides_input.txt"

    if slides_input.exists():
        return _parse_slides_input(slides_input)
    else:
        print("  ⚠️  slides_input.txt 不存在，使用启发式算法（建议先在 Claude Code 里跑 ljg-present）")
        return _extract_heuristic(script_path)


def _parse_slides_input(slides_input_path: Path) -> list[dict]:
    """
    解析 slides_input.txt，自动检测 JSON 或纯文本格式。

    JSON 格式（ljg-present 输出）：
      [{"text": "怕", "emphasis": false}, ...]

    纯文本格式（手写）：
      怕
      声音是第二张脸
      [PAUSE]
      # 注释行
    """
    with open(slides_input_path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if content.startswith("[") or content.startswith("{"):
        return _parse_json_slides(content)
    else:
        return _parse_text_slides(content)


def _parse_json_slides(content: str) -> list[dict]:
    """解析 JSON 格式（ljg-present 的输出）"""
    data = json.loads(content)
    slides = []
    para_idx = 0

    for item in data:
        text = item.get("text", "").strip()
        emphasis = item.get("emphasis", False)

        if not text:
            if slides and slides[-1]["type"] != "pause":
                slides.append({"text": "", "type": "pause", "paragraph_index": para_idx})
                para_idx += 1
            continue

        clean_text = text.replace("\n", "")
        length = len(clean_text)

        if length <= 2 and "\n" not in text:
            stype = "single_char"
        elif length <= 12:
            stype = "phrase"
        else:
            stype = "sentence"

        if emphasis:
            stype = "sentence"

        slides.append({"text": text, "type": stype, "paragraph_index": para_idx})

    result = []
    for i, slide in enumerate(slides):
        result.append(slide)
        if (i + 1) % 5 == 0 and i < len(slides) - 1:
            if result[-1]["type"] != "pause":
                result.append({"text": "", "type": "pause", "paragraph_index": slide["paragraph_index"]})

    while result and result[0]["type"] == "pause":
        result.pop(0)
    while result and result[-1]["type"] == "pause":
        result.pop()

    print(f"  ✅ 读取 slides_input.txt（JSON）：{len(result)} 张幻灯片")
    return result


def _parse_text_slides(content: str) -> list[dict]:
    """解析纯文本格式（手写）"""
    slides = []
    para_idx = 0

    for line in content.splitlines():
        text = line.strip()

        if text.startswith("#"):
            continue

        if not text or text.upper() == "[PAUSE]":
            if slides and slides[-1]["type"] != "pause":
                slides.append({"text": "", "type": "pause", "paragraph_index": para_idx})
                para_idx += 1
            continue

        if text.startswith("[单字]"):
            t, stype = text[4:].strip(), "single_char"
        elif text.startswith("[短句]"):
            t, stype = text[4:].strip(), "phrase"
        elif text.startswith("[句子]"):
            t, stype = text[4:].strip(), "sentence"
        else:
            t = text
            length = len(t)
            if length <= 2:
                stype = "single_char"
            elif length <= 10:
                stype = "phrase"
            else:
                stype = "sentence"

        if t:
            slides.append({"text": t, "type": stype, "paragraph_index": para_idx})

    while slides and slides[0]["type"] == "pause":
        slides.pop(0)
    while slides and slides[-1]["type"] == "pause":
        slides.pop()

    print(f"  ✅ 读取 slides_input.txt（纯文本）：{len(slides)} 张幻灯片")
    return slides


def _extract_heuristic(script_path: str) -> list[dict]:
    """Fallback：启发式提取，不需要 API。每段取前 1-2 个最短有意义片段。"""
    with open(script_path, "r", encoding="utf-8") as f:
        raw = f.read()

    paragraphs = [p.strip() for p in raw.split("\n\n") if p.strip()]
    slides = []
    para_idx = 0

    for para in paragraphs:
        sentences = re.split(r"[。！？…\n]", para)
        sentences = [s.strip() for s in sentences if s.strip()]
        added = 0

        for sent in sentences:
            if added >= 2:
                break
            length = len(sent)
            if length <= 2:
                slides.append({"text": sent, "type": "single_char", "paragraph_index": para_idx})
                added += 1
            elif 3 <= length <= 10:
                slides.append({"text": sent, "type": "phrase", "paragraph_index": para_idx})
                added += 1
            elif 11 <= length <= 20:
                slides.append({"text": sent, "type": "sentence", "paragraph_index": para_idx})
                added += 1

        if slides and slides[-1]["type"] != "pause":
            slides.append({"text": "", "type": "pause", "paragraph_index": para_idx})
        para_idx += 1

    while slides and slides[0]["type"] == "pause":
        slides.pop(0)
    while slides and slides[-1]["type"] == "pause":
        slides.pop()

    return slides


# ── 时长计算 ────────────────────────────────────────────────────────────

def _srt_total_seconds(srt_path: str) -> float:
    with open(srt_path, encoding="utf-8") as f:
        content = f.read()
    times = re.findall(r"\d{2}:\d{2}:\d{2}[,\.]\d{3}", content)
    if not times:
        return 60.0

    def parse(t: str) -> float:
        t = t.replace(",", ".")
        h, m, s = t.split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)

    return parse(times[-1])


def calculate_timing(slides: list[dict], total_seconds: float) -> list[dict]:
    PAUSE_DUR = 0.8
    weights = {"single_char": 1.5, "phrase": 2.0, "sentence": 2.5}

    pause_total = sum(PAUSE_DUR for s in slides if s.get("type") == "pause")
    remaining = max(total_seconds - pause_total, 1.0)
    non_pause = [s for s in slides if s.get("type") != "pause"]
    total_w = sum(weights.get(s["type"], 2.0) for s in non_pause) or 1.0

    timed, t = [], 0.0
    for slide in slides:
        if slide.get("type") == "pause":
            dur = PAUSE_DUR
        else:
            w = weights.get(slide["type"], 2.0)
            dur = (w / total_w) * remaining
        timed.append({**slide, "start": round(t, 3), "duration": round(dur, 3), "end": round(t + dur, 3)})
        t += dur
    return timed


# ── HTML 生成 ────────────────────────────────────────────────────────────

_CSS = """\
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body {
  width: 1920px; height: 1080px; overflow: hidden;
  background: #080808;
  font-family: 'Noto Serif CJK TC', 'Noto Serif CJK SC', 'SimSun', serif;
}
.slide {
  width: 1920px; height: 1080px;
  display: none; align-items: center; justify-content: center;
  position: relative;
}
.slide.active { display: flex; }
.slide::after {
  content: ''; position: absolute; inset: 48px;
  border: 1px solid rgba(240,235,225,0.06); pointer-events: none;
}
.seal {
  position: absolute; bottom: 72px; right: 96px;
  font-size: 18px; color: rgba(240,235,225,0.22);
  letter-spacing: 0.2em; writing-mode: vertical-rl;
}
.t-single_char {
  font-size: 380px; font-weight: 300; line-height: 1;
  color: #F0EBE1; letter-spacing: -0.02em;
}
.t-phrase {
  font-size: 130px; font-weight: 300; line-height: 1.3;
  color: #F0EBE1; text-align: center;
  max-width: 1600px; letter-spacing: 0.08em;
}
.t-sentence {
  font-size: 72px; font-weight: 300; line-height: 1.6;
  color: rgba(240,235,225,0.9); text-align: center;
  max-width: 1400px; letter-spacing: 0.05em;
}
.t-pause { width: 1px; height: 1px; }
"""


def _html(slides: list[dict], title: str = "极客禅") -> str:
    parts = []
    for i, s in enumerate(slides):
        stype = s.get("type", "phrase")
        text = s.get("text", "")
        if stype == "pause":
            inner = '<div class="t-pause"></div>'
        else:
            inner = f'<div class="t-{stype}">{text}</div>'
        active = " active" if i == 0 else ""
        parts.append(f'<div class="slide{active}" data-i="{i}">{inner}<div class="seal">极客禅</div></div>')

    data_js = json.dumps(
        [{"text": s.get("text", ""), "type": s.get("type", "phrase"), "duration": s.get("duration", 2.0)}
         for s in slides],
        ensure_ascii=False,
    )
    return f"""<!DOCTYPE html>
<html lang="zh"><head>
<meta charset="UTF-8">
<title>{title}</title>
<style>{_CSS}</style>
</head><body>
{''.join(parts)}
<script>
const all = document.querySelectorAll('.slide');
let cur = 0;
function show(n) {{
  all[cur].classList.remove('active');
  cur = n;
  all[cur].classList.add('active');
  document.title = (n+1)+'/'+all.length+' · {title}';
}}
document.addEventListener('keydown', e => {{
  if (e.key==='ArrowRight'||e.key===' ') show(Math.min(cur+1, all.length-1));
  if (e.key==='ArrowLeft') show(Math.max(cur-1,0));
  if (e.key==='f') document.documentElement.requestFullscreen?.();
  if (e.key==='Home') show(0);
  if (e.key==='End') show(all.length-1);
}});
window.__show__ = show;
window.__slides_data__ = {data_js};
</script></body></html>"""


# ── Playwright 截图 ──────────────────────────────────────────────────────

async def _screenshot(html_path: str, count: int, slides_dir: Path) -> None:
    from playwright.async_api import async_playwright

    slides_dir.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox", "--disable-setuid-sandbox"])
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        await page.goto(f"file://{html_path}")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(1500)   # let fonts render

        for i in range(count):
            await page.evaluate(f"window.__show__({i})")
            await page.wait_for_timeout(80)
            await page.screenshot(path=str(slides_dir / f"slide_{i:03d}.png"))
            if i % 10 == 0:
                print(f"  截图 {i+1}/{count}")

        await browser.close()
    print(f"✅ PNG 序列：{slides_dir}（{count} 张）")


# ── 主函数 ───────────────────────────────────────────────────────────────

async def run_present(script_path: str, output_dir: str, srt_path: str | None = None) -> list[dict]:
    output_dir = Path(output_dir)
    slides_dir = output_dir / "slides"

    print("  → 提取高桥流关键词…")
    slides = extract_slides(script_path)
    print(f"  → {len(slides)} 张幻灯片")

    total_secs = _srt_total_seconds(srt_path) if srt_path and Path(srt_path).exists() else 60.0
    print(f"  → 音频时长 {total_secs:.1f}s，分配时长…")
    slides = calculate_timing(slides, total_secs)

    timing_path = output_dir / "slides_timing.json"
    timing_path.write_text(json.dumps(slides, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ timing：{timing_path}")

    html_path = output_dir / "slides.html"
    html_path.write_text(_html(slides), encoding="utf-8")
    print(f"✅ HTML：{html_path}")

    print("  → Playwright 截图…")
    await _screenshot(str(html_path.absolute()), len(slides), slides_dir)

    return slides


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python tools/present.py <script.txt> <output_dir> [srt_path]")
        sys.exit(1)
    srt = sys.argv[3] if len(sys.argv) > 3 else None
    asyncio.run(run_present(sys.argv[1], sys.argv[2], srt))
