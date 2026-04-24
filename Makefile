# ─────────────────────────────────────────────────────────────────────────────
#  极客禅 · 长视频工厂
#
#  用法：make TOPIC="不出镜"
#        make TOPIC="拖延症" ENTRY="我有三个烂尾项目"
#        make think TOPIC="拖延症"
#        make present TOPIC="项目写不完"
#        make video TOPIC="项目写不完"
# ─────────────────────────────────────────────────────────────────────────────

PY      := $(shell command -v python3.12 2>/dev/null || command -v python3 2>/dev/null || echo python3)
TOOLS   := tools

TOPIC   ?= 不出镜
ENTRY   ?=
CLOSING ?=
VOICE   ?= zh-TW-YunJheNeural
RATE    ?= -10%

# 缩略图参数（make thumbnail CHAR=怕 LINE1="我为什么" LINE2="不出镜"）
CHAR    ?= 怕
LINE1   ?= 我为什么
LINE2   ?= 不出镜

EP      := episodes/$(TOPIC)
OUT     := $(EP)/output

THINK   := $(EP)/think_output.md
WRITE   := $(EP)/write_output.md
SCRIPT  := $(EP)/script.txt
AUDIO   := $(OUT)/audio_tw.mp3
SRT_S   := $(OUT)/subtitle_zh_hans.srt
SRT_T   := $(OUT)/subtitle_zh_hant.srt
HTML    := $(OUT)/slides.html
TIMING  := $(OUT)/slides_timing.json
VIDEO   := $(OUT)/final.mp4
REMOTION_VIDEO := $(OUT)/final_remotion.mp4
THUMB   := $(OUT)/thumbnail.jpg
CARD    := $(HOME)/Downloads/$(CHAR).png

# ── 主目标 ───────────────────────────────────────────────────────────────────

.PHONY: all think write audio subtitles present video remotion thumbnail studio remix preview \
        clean-output clean help

## 默认目标：假设 Claude Code 已完成 think/write/present，只跑命令行部分
all: $(AUDIO) $(TIMING) $(VIDEO)
	@echo ""
	@echo "╔══════════════════════════════════════════╗"
	@echo "║  ✅  极客禅视频生成完成                   ║"
	@echo "║  📁  $(VIDEO)"
	@echo "╚══════════════════════════════════════════╝"

## API 生成（可选，需要 ANTHROPIC_API_KEY；用 Claude Code Max 订阅可跳过）
think:
	@echo "━━━ Think（API）━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	mkdir -p $(EP)
	$(PY) $(TOOLS)/pipeline.py "$(TOPIC)" \
		--entry "$(ENTRY)" \
		--closing "$(CLOSING)" \
		--voice "$(VOICE)" \
		--rate="$(RATE)" \
		--only-think

write:
	@[ -f "$(THINK)" ] || (echo "❌ 找不到 $(THINK)，请先运行 make think 或在 Claude Code 里生成"; exit 1)
	@echo "━━━ Write（API）━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	$(PY) $(TOOLS)/pipeline.py "$(TOPIC)" \
		--entry "$(ENTRY)" \
		--closing "$(CLOSING)" \
		--skip-think \
		--only-write

## 命令行目标（零 API 调用，script.txt 须已存在）
audio:     $(AUDIO)
subtitles: $(SRT_T)
present:   $(TIMING)
video:     $(VIDEO)
remotion:  $(REMOTION_VIDEO)
# 前置：先在 Claude Code 里运行 ljg-card -b CHAR，生成 ~/Downloads/CHAR.png
thumbnail: $(THUMB)

# ── 规则 ────────────────────────────────────────────────────────────────────

$(EP):
	mkdir -p $(EP)

$(OUT): $(EP)
	mkdir -p $(OUT)

# Step 3: Audio + Subtitles（script.txt 须已存在，不自动调用 API）
$(AUDIO) $(SRT_S) $(SRT_T) &: $(SCRIPT) $(OUT)
	@echo ""
	@echo "━━━ Step 3/5: Audio + Subtitles ━━━━━━━━━━━━"
	$(PY) $(TOOLS)/pipeline.py "$(TOPIC)" \
		--skip-think \
		--skip-write \
		--only-tts
	@echo ""

# Step 4: 幻灯片
# 读取 episodes/$(TOPIC)/slides_input.txt（由 Claude Code 里的 ljg-present 生成）
# 如果不存在，自动 fallback 到启发式算法
$(TIMING) $(HTML) &: $(SCRIPT) $(SRT_S) $(OUT)
	@echo ""
	@echo "━━━ Step 4/5: Present（高桥流幻灯片）━━━━━━━"
	$(PY) $(TOOLS)/present.py \
		$(SCRIPT) \
		$(OUT) \
		$(SRT_S)
	@echo ""

# Step 5: Video（依赖 timing + audio + 字幕）
$(VIDEO): $(TIMING) $(AUDIO) $(SRT_T)
	@echo ""
	@echo "━━━ Step 5/5: Video（最终合成）━━━━━━━━━━━━━"
	$(PY) $(TOOLS)/video.py $(OUT)
	@echo ""

# Step 5b: Remotion Video（可选，高质量渲染）
$(REMOTION_VIDEO): $(TIMING) $(AUDIO) $(SRT_S)
	@echo ""
	@echo "━━━ Step 5b: Remotion Render ━━━━━━━━━━━━━━"
	cd remotion && node render.mjs ../$(OUT)
	@echo ""

# Thumbnail: 需先在 Claude Code 里运行 `ljg-card -b CHAR`
# 生成 ~/Downloads/CHAR.png，再执行 make thumbnail
$(THUMB): $(OUT)
	@test -f "$(CARD)" || (echo "❌ 找不到 $(CARD)，请先在 Claude Code 里运行 ljg-card -b $(CHAR)"; exit 1)
	@echo ""
	@echo "━━━ Thumbnail（YouTube 缩略图 1280×720）━━━"
	$(PY) $(TOOLS)/thumbnail.py "$(CARD)" "$(LINE1)" "$(LINE2)" "$(THUMB)"
	@echo ""

# ── 辅助目标 ────────────────────────────────────────────────────────────────

## Remotion Studio 实时预览
studio:
	cd remotion && npx remotion studio

## 只重新合成视频（不重新截图/音频）
remix:
	@echo "重新合成视频（复用现有幻灯片和音频）..."
	$(PY) $(TOOLS)/video.py $(OUT)

## 在浏览器预览幻灯片 HTML
preview:
	@echo "打开幻灯片预览：$(HTML)"
	xdg-open $(HTML) 2>/dev/null || open $(HTML) 2>/dev/null || echo "请手动打开 $(HTML)"

## 清理 output/（保留 think/write/script）
clean-output:
	rm -rf $(OUT)
	@echo "已清理：$(OUT)"

## 完全重置该 episode
clean:
	rm -rf $(EP)
	@echo "已清理：$(EP)"

## 显示帮助
help:
	@echo ""
	@echo "极客禅长视频工厂"
	@echo ""
	@echo "工作流："
	@echo "  Step A（Claude Code 里完成，用 Max 订阅）："
	@echo "    ljg-think   → episodes/主题/think_output.md"
	@echo "    ljg-write   → episodes/主题/script.txt"
	@echo "    ljg-present → episodes/主题/slides_input.txt"
	@echo ""
	@echo "  Step B（终端，零 API 调用）："
	@echo "    make TOPIC=\"主题\"     # audio + present + video"
	@echo ""
	@echo "分步执行："
	@echo "  make audio    TOPIC=\"主题\"   # TTS 音频 + 字幕"
	@echo "  make present  TOPIC=\"主题\"   # 幻灯片（读 slides_input.txt）"
	@echo "  make video    TOPIC=\"主题\"   # 最终合成（ffmpeg）"
	@echo "  make remotion   TOPIC=\"主题\"                  # Remotion 渲染最终视频"
	@echo "  make thumbnail  TOPIC=\"主题\" CHAR=怕 LINE1=\"我为什么\" LINE2=\"不出镜\""
	@echo "                                               # YouTube 缩略图（需先 ljg-card -b CHAR）"
	@echo ""
	@echo "其他："
	@echo "  make studio   TOPIC=\"主题\"   # Remotion Studio 实时预览"
	@echo "  make remix    TOPIC=\"主题\"   # 只重新渲染（不重跑 audio/present）"
	@echo "  make preview  TOPIC=\"主题\"   # 浏览器预览幻灯片 HTML"
	@echo "  make clean    TOPIC=\"主题\"   # 删除该 episode"
	@echo ""
	@echo "可用变量："
	@echo "  TOPIC    主题词（必填）"
	@echo "  VOICE    TTS 声音（默认 zh-TW-YunJheNeural）"
	@echo "  RATE     语速（默认 -10%）"
	@echo "  CHAR     缩略图核心字（默认 怕）"
	@echo "  LINE1    缩略图标题第一行（默认 我为什么）"
	@echo "  LINE2    缩略图标题第二行（默认 不出镜）"
	@echo ""
