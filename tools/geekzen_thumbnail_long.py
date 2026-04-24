#!/usr/bin/env python3
"""
geekzen_thumbnail_long.py
极客禅长视频 YouTube 缩略图生成器

用法：
  python tools/geekzen_thumbnail_long.py "Git Revert" --subtitle "当你想撤回人生的那个决定" --ep 12
  python tools/geekzen_thumbnail_long.py "Git Revert" --subtitle "..." --ep 12 --seal remotion/public/seal.png
  python tools/geekzen_thumbnail_long.py "不出镜" --output episodes/不出镜/output/thumbnail.jpg
"""

import argparse
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ─── 品牌配置 ──────────────────────────────────────────────────────────────

BRAND = {
    "bg":     (8, 8, 8),        # #080808
    "fg":     (240, 235, 225),  # #F0EBE1
    "accent": (139, 111, 71),   # #8B6F47
}

FONT_PATHS = {
    "regular": "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
    "bold":    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc",
}

CANVAS_W, CANVAS_H = 1280, 720

# ─── 字体加载 ───────────────────────────────────────────────────────────────

def load_font(size: int, weight: str = "regular") -> ImageFont.FreeTypeFont:
    path = FONT_PATHS.get(weight, FONT_PATHS["regular"])
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

# ─── 背景生成 ───────────────────────────────────────────────────────────────

def make_background() -> Image.Image:
    """极客禅深色背景，含水墨晕染效果"""
    bg = Image.new("RGBA", (CANVAS_W, CANVAS_H), (*BRAND["bg"], 255))

    # 晕染层 1：中央偏上，琥珀色
    glow1 = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    d1 = ImageDraw.Draw(glow1)
    cx1, cy1, rx1, ry1 = 640, 280, 500, 300
    for i in range(60):
        alpha = int(10 * (1 - i / 60))
        r = (
            int(cx1 - rx1 * (1 - i / 60)), int(cy1 - ry1 * (1 - i / 60)),
            int(cx1 + rx1 * (1 - i / 60)), int(cy1 + ry1 * (1 - i / 60)),
        )
        d1.ellipse(r, fill=(*BRAND["accent"], alpha))
    glow1 = glow1.filter(ImageFilter.GaussianBlur(60))
    bg = Image.alpha_composite(bg, glow1)

    # 晕染层 2：右下，暖白
    glow2 = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    d2 = ImageDraw.Draw(glow2)
    cx2, cy2, rx2, ry2 = 1050, 580, 400, 250
    for i in range(50):
        alpha = int(8 * (1 - i / 50))
        r = (
            int(cx2 - rx2 * (1 - i / 50)), int(cy2 - ry2 * (1 - i / 50)),
            int(cx2 + rx2 * (1 - i / 50)), int(cy2 + ry2 * (1 - i / 50)),
        )
        d2.ellipse(r, fill=(*BRAND["fg"], alpha))
    glow2 = glow2.filter(ImageFilter.GaussianBlur(80))
    bg = Image.alpha_composite(bg, glow2)

    return bg.convert("RGB")

# ─── 文字工具 ───────────────────────────────────────────────────────────────

def wrap_text(
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
    draw: ImageDraw.ImageDraw,
) -> list[str]:
    """按像素宽度折行"""
    if not text:
        return []
    bbox = draw.textbbox((0, 0), text, font=font)
    if bbox[2] - bbox[0] <= max_width:
        return [text]
    lines = []
    current = ""
    for char in text:
        test = current + char
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > max_width and current:
            lines.append(current)
            current = char
        else:
            current = test
    if current:
        lines.append(current)
    return lines


def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    y: int,
    font: ImageFont.FreeTypeFont,
    color: tuple,
    max_width: int = CANVAS_W - 120,
) -> int:
    """居中绘制文字，返回文字块底部 y 坐标"""
    lines = wrap_text(text, font, max_width, draw)
    line_h = font.size + int(font.size * 0.4)
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (CANVAS_W - tw) // 2
        draw.text((x, y + i * line_h), line, font=font, fill=color)
    return y + len(lines) * line_h

# ─── 装饰元素 ───────────────────────────────────────────────────────────────

def draw_decorations(draw: ImageDraw.ImageDraw):
    """左侧竖线 + 底部分隔线 + 右上角点阵"""
    # 左侧竖线
    draw.line([(64, 220), (64, 420)], fill=(*BRAND["fg"], 25), width=1)

    # 底部分隔线
    sep_y = CANVAS_H - 88
    draw.line([(64, sep_y), (CANVAS_W - 64, sep_y)], fill=(*BRAND["fg"], 20), width=1)

    # 右上角 3×3 点阵
    for row in range(3):
        for col in range(3):
            px = CANVAS_W - 80 + col * 12
            py = 56 + row * 12
            draw.ellipse([(px - 1, py - 1), (px + 1, py + 1)], fill=(*BRAND["fg"], 18))


def draw_brand_bar(draw: ImageDraw.ImageDraw, ep_num: str = ""):
    font_brand = load_font(26, "regular")
    font_ep    = load_font(18, "regular")
    draw.text((72, CANVAS_H - 76), "极客禅", font=font_brand, fill=(*BRAND["fg"], 120))
    if ep_num:
        ep_text = f"EP·{ep_num.zfill(2)}"
        draw.text((72, CANVAS_H - 46), ep_text, font=font_ep, fill=(*BRAND["fg"], 60))


def add_seal(canvas: Image.Image, seal_path: str) -> Image.Image:
    try:
        seal = Image.open(seal_path).convert("RGBA")
    except Exception as e:
        print(f"  ⚠️  印章加载失败：{e}")
        return canvas

    target_h = 72
    target_w = int(seal.width * target_h / seal.height)
    seal = seal.resize((target_w, target_h), Image.LANCZOS)
    seal = seal.rotate(-2, expand=True, resample=Image.BICUBIC)

    r, g, b, a = seal.split()
    a = a.point(lambda x: int(x * 0.85))
    seal = Image.merge("RGBA", (r, g, b, a))

    x = canvas.width - seal.width - 72
    y = canvas.height - seal.height - 48
    base = canvas.convert("RGBA")
    base.paste(seal, (x, y), mask=seal.split()[3])
    return base.convert("RGB")

# ─── 主流程 ─────────────────────────────────────────────────────────────────

def make_thumbnail(
    title: str,
    subtitle: str = "",
    ep_num: str = "",
    output_path: str = None,
    seal_path: str = None,
) -> str:
    canvas = make_background()
    draw = ImageDraw.Draw(canvas)

    draw_decorations(draw)

    # 动态字号：标题越长字越小
    title_font_size = 88 if len(title) <= 8 else 72 if len(title) <= 14 else 60
    title_font = load_font(title_font_size, "regular")
    sub_font   = load_font(34, "regular")
    gap = 32

    # 计算内容总高度用于垂直居中
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    title_lines = wrap_text(title, title_font, CANVAS_W - 160, probe)
    title_block_h = len(title_lines) * (title_font_size + int(title_font_size * 0.4))
    sub_block_h = (sub_font.size + int(sub_font.size * 0.4)) if subtitle else 0
    total_h = title_block_h + (gap + sub_block_h if subtitle else 0)

    content_mid = (140 + 580) // 2
    start_y = content_mid - total_h // 2

    end_y = draw_centered_text(
        draw, title, start_y, title_font, BRAND["fg"], max_width=CANVAS_W - 160
    )

    if subtitle:
        draw_centered_text(
            draw, subtitle, end_y + gap, sub_font,
            (*BRAND["fg"], 110), max_width=CANVAS_W - 200
        )

    draw_brand_bar(draw, ep_num)

    if seal_path and os.path.exists(seal_path):
        canvas = add_seal(canvas, seal_path)

    if output_path is None:
        safe_title = title.replace(" ", "_").replace("/", "_")[:20]
        output_path = f"thumbnail_ep{ep_num or 'XX'}_{safe_title}.jpg"

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    canvas.save(output_path, "JPEG", quality=95)
    size_kb = os.path.getsize(output_path) // 1024
    print(f"  ✅ {output_path}  ({size_kb} KB, {CANVAS_W}×{CANVAS_H})")
    return output_path

# ─── CLI ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="极客禅长视频 YouTube 缩略图生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python tools/geekzen_thumbnail_long.py "Git Revert" \\
    --subtitle "当你想撤回人生的那个决定" \\
    --ep 12 \\
    --seal remotion/public/seal.png

  python tools/geekzen_thumbnail_long.py "不出镜" \\
    --subtitle "声音是第二张脸" \\
    --seal remotion/public/seal.png \\
    --output episodes/不出镜/output/thumbnail.jpg
        """,
    )
    parser.add_argument("title",            help="视频主标题")
    parser.add_argument("--subtitle", "-s", default="",   help="副标题（可选）")
    parser.add_argument("--ep",             default="",   help="期数，如 12")
    parser.add_argument("--output",   "-o", default=None, help="输出路径")
    parser.add_argument("--seal",           default=None, help="印章 PNG 路径")
    args = parser.parse_args()

    print(f"  标题：{args.title}")
    if args.subtitle:
        print(f"  副标：{args.subtitle}")
    if args.ep:
        print(f"  期数：EP{args.ep}")

    make_thumbnail(
        title=args.title,
        subtitle=args.subtitle,
        ep_num=args.ep,
        output_path=args.output,
        seal_path=args.seal,
    )


if __name__ == "__main__":
    main()
