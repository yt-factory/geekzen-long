# Workflow Guide

## Overview

Each episode goes through two phases:

- **Phase A** — Creative work inside Claude Code (uses Max subscription, no extra API cost)
- **Phase B** — Mechanical production in the terminal (zero API calls)

---

## Phase A: Claude Code

### 1. Think (`ljg-think`)

Drill down on a topic — from surface observation to bedrock insight.

```
ljg-think "youtube 不出镜"
```

Output: `episodes/{topic}/think_output.md`

### 2. Write (`ljg-writes`)

Turn the philosophical drill-down into a narration script for video.

```
ljg-writes "指令：把以下内容改写为适合朗读的中文视频脚本..."
```

Output: `episodes/{topic}/script.txt` (plain text, no markdown)

### 3. Present (`ljg-present`)

Extract Takahashi-style slide data from the script.

```
ljg-present using file "episodes/{topic}/script.txt",
            保存输出到 episodes/{topic}/slides_input.txt
```

Output: `episodes/{topic}/slides_input.txt` — JSON array of slide objects:

```json
[
  {"text": "怕", "emphasis": false},
  {"text": "外面没有别人", "emphasis": false},
  {"text": "这把声音\n是真实的", "emphasis": true}
]
```

`emphasis: true` renders in seal red (#C03C28). Use for the closing slide only.

### 4. Card (`ljg-card -b`)

Generate the brand card — ink on washi paper with GeekZen seal.

```
ljg-card -b 怕
```

Output: `~/Downloads/怕.png` (1080×1440)

Card layout:
- Bottom-left: `极客禅` text signature
- Bottom-right: red seal stamp (rotated -2°)

---

## Phase B: Terminal

All commands run from `geekzen-long/`.

### 5. Audio + Subtitles

```bash
make audio TOPIC="不出镜"
```

Runs `tools/tts.py` → `output/audio_tw.mp3` + `subtitle_raw.srt`  
Then `tools/subtitles.py` → 4 subtitle files:

| File | Description |
|------|-------------|
| `subtitle_zh_hans.srt` | Simplified Chinese SRT |
| `subtitle_zh_hans.vtt` | Simplified Chinese VTT |
| `subtitle_zh_hant.srt` | Traditional Chinese SRT |
| `subtitle_zh_hant.vtt` | Traditional Chinese VTT |

Voice: `zh-TW-YunJheNeural` (configurable via `VOICE=` variable)  
Speed: `-10%` (configurable via `RATE=` variable)

### 6. Slides

```bash
make present TOPIC="不出镜"
```

Reads `episodes/{topic}/slides_input.txt` (from step 3).  
If that file doesn't exist, falls back to heuristic extraction from `script.txt`.

Output:
- `output/slides/slide_NNN.png` — one PNG per slide (1080×1440)
- `output/slides_timing.json` — slide → audio timestamp mapping

### 7. Video

```bash
make video TOPIC="不出镜"
```

ffmpeg assembles slides + audio + Traditional Chinese subtitles into `output/final.mp4`.

### 8. Thumbnail

```bash
make thumbnail TOPIC="不出镜" CHAR=怕 LINE1="我为什么" LINE2="不出镜"
```

Pre-requisite: `~/Downloads/怕.png` must exist (from step 4).

Expands the 1080×1440 card to 1280×720 (16:9) and adds two title lines on the right.  
Output: `output/thumbnail.jpg`

---

## One-shot (steps 5–7)

If the Claude Code phase is complete:

```bash
make TOPIC="不出镜"
```

Runs audio → slides → video in sequence.

---

## Optional: Remotion render

Higher-quality video with motion and transitions:

```bash
make remotion TOPIC="不出镜"
# or open Remotion Studio for live preview:
make studio
```

---

## Variables reference

| Variable | Default | Description |
|----------|---------|-------------|
| `TOPIC` | `不出镜` | Episode directory name |
| `VOICE` | `zh-TW-YunJheNeural` | edge-tts voice |
| `RATE` | `-10%` | TTS speaking rate |
| `CHAR` | `怕` | Core character for the brand card |
| `LINE1` | `我为什么` | Thumbnail title line 1 |
| `LINE2` | `不出镜` | Thumbnail title line 2 |

---

## Troubleshooting

**edge-tts SSML issue** — edge-tts 7.x escapes XML internally. The `tts.py` script works around this by pre-escaping text and injecting `<break>` tags directly into `comm.texts`. See `tools/tts.py:build_ssml_chunks()`.

**ljg-card template overwritten by skill update** — restore from backup:
```bash
cp tools/ljg-card-big-template.backup.html \
   ~/.claude/skills/ljg-card/assets/big_template.html
```

**Playwright not found** — run from `~/.claude/skills/ljg-card/`:
```bash
npm install playwright && npx playwright install chromium
```
