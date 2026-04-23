# 极客禅 · 长视频工厂

GeekZen long-form YouTube video pipeline — from a one-line topic to a published video.

## What it produces

Each episode generates:
- **Takahashi-style slides** — one word per screen, carved-ink aesthetic
- **TTS audio** — Taiwan Mandarin voice with paragraph-level pacing
- **Bilingual subtitles** — Simplified + Traditional Chinese (SRT + VTT)
- **Final MP4** — slides + audio + soft subtitles, ready to upload
- **YouTube thumbnail** — 1280×720 with seal and title text

## Stack

| Layer | Tool |
|-------|------|
| Content ideation | Claude Code (`ljg-think`, `ljg-writes`) |
| Script → slides | Claude Code (`ljg-present`) |
| Brand card | Claude Code (`ljg-card -b`) |
| TTS + subtitles | `edge-tts` + `opencc-python-reimplemented` |
| Slide rendering | `playwright` (HTML → PNG) |
| Video assembly | `ffmpeg` |
| High-quality render | `Remotion` (optional) |
| Thumbnail | `Pillow` (`tools/thumbnail.py`) |

## Quick start

```bash
# See all available targets
make help

# Full pipeline for a new episode (after Claude Code steps are done)
make TOPIC="不出镜"

# Generate YouTube thumbnail
make thumbnail TOPIC="不出镜" CHAR=怕 LINE1="我为什么" LINE2="不出镜"
```

## Workflow

```
┌─────────────────────────────────────────────────────┐
│  Step A — Claude Code (Max subscription, zero cost)  │
│                                                       │
│  ljg-think  "topic"    → episodes/topic/think.md     │
│  ljg-writes "prompt"   → episodes/topic/script.txt   │
│  ljg-present           → episodes/topic/slides.txt   │
│  ljg-card -b CHAR      → ~/Downloads/CHAR.png        │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│  Step B — Terminal (zero API calls)                  │
│                                                       │
│  make audio      → TTS audio + 4 subtitle files      │
│  make present    → slide PNGs + timing JSON          │
│  make video      → final.mp4                         │
│  make thumbnail  → output/thumbnail.jpg              │
└─────────────────────────────────────────────────────┘
```

See [docs/WORKFLOW.md](docs/WORKFLOW.md) for the full step-by-step guide.

## Directory structure

```
geekzen-long/
├── README.md
├── Makefile               — unified entry point (make help)
├── .gitignore
├── brands/
│   └── geekzen/           — channel identity (brand.json, voice.json)
├── tools/                 — shared scripts, reused across episodes
│   ├── tts.py             — edge-tts wrapper with SSML paragraph breaks
│   ├── subtitles.py       — SRT → VTT, s2twp conversion
│   ├── present.py         — slides_input.txt → PNG + timing JSON
│   ├── video.py           — ffmpeg assembly
│   ├── pipeline.py        — API pipeline (think/write/tts in sequence)
│   ├── thumbnail.py       — card PNG → 1280×720 YouTube thumbnail
│   └── ljg-card-big-template.backup.html  — GeekZen-customized card template
├── remotion/              — Remotion renderer (optional high-quality output)
├── docs/
│   └── WORKFLOW.md        — detailed step-by-step guide
└── episodes/
    └── {topic}/
        ├── script.txt         — narration script (plain text, no markdown)
        ├── think_output.md    — ljg-think philosophical drill-down
        ├── slides_input.txt   — ljg-present JSON (Takahashi slide data)
        └── output/            — generated files (gitignored)
            ├── audio_tw.mp3
            ├── subtitle_zh_hans.srt/vtt
            ├── subtitle_zh_hant.srt/vtt
            ├── slides/slide_NNN.png
            ├── slides_timing.json
            ├── final.mp4
            └── thumbnail.jpg
```

## Episodes

| Episode | Topic | Status |
|---------|-------|--------|
| 不出镜 | Why I never show my face on YouTube | ✅ |
| 项目写不完 | Why projects never get finished | ✅ |

## Brand: GeekZen (极客禅)

- Channel: [@voidmainzen](https://youtube.com/@voidmainzen)
- Aesthetic: ink on washi paper, Takahashi slides, seal stamp
- Voice: `zh-TW-YunJheNeural` (Taiwan Mandarin, male)
- Card signature: 极客禅 + red seal (bottom-right)

## Requirements

```bash
pip install edge-tts opencc-python-reimplemented Pillow
# Playwright (for slide screenshots):
npm install playwright && npx playwright install chromium
# ffmpeg must be installed system-wide
```
