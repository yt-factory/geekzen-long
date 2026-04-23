"""
thumbnail.py — 极客禅 YouTube 缩略图生成器

用法：
    python thumbnail.py <card.png> <line1> <line2> <output.jpg>

示例：
    python thumbnail.py ~/Downloads/怕.png "我为什么" "不出镜" episodes/不出镜/output/thumbnail.jpg

输入：
    card.png  — 由 ljg-card -b 生成的 1080×1440 卡片（含印章署名）
输出：
    1280×720 JPG，左侧卡片 + 右侧标题文字
"""

import sys
import os
from PIL import Image, ImageDraw, ImageFont

FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
BG_COLOR  = "#EDE8DC"    # 宣纸底色（与卡片协调）
INK_COLOR = "#2C2826"    # 墨色
TITLE_SIZE = 108
LINE_GAP   = 28


def make_thumbnail(card_path: str, line1: str, line2: str, out_path: str) -> None:
    card_path = os.path.expanduser(card_path)
    out_path  = os.path.expanduser(out_path)

    src = Image.open(card_path).convert("RGB")  # 1080×1440
    card = src.resize((540, 720), Image.LANCZOS)

    # 1280×720 画布
    thumb = Image.new("RGB", (1280, 720), color=BG_COLOR)
    thumb.paste(card, (0, 0))

    draw = ImageDraw.Draw(thumb)
    try:
        font = ImageFont.truetype(FONT_BOLD, TITLE_SIZE, index=0)
    except OSError:
        font = ImageFont.load_default()

    def wh(text):
        bb = draw.textbbox((0, 0), text, font=font)
        return bb[2] - bb[0], bb[3] - bb[1]

    w1, h1 = wh(line1)
    w2, h2 = wh(line2)
    total_h = h1 + LINE_GAP + h2

    right_cx = 540 + 370   # 右侧面板中心 x
    cy = 360

    x1 = right_cx - w1 // 2
    y1 = cy - total_h // 2
    x2 = right_cx - w2 // 2
    y2 = y1 + h1 + LINE_GAP

    draw.text((x1, y1), line1, font=font, fill=INK_COLOR)
    draw.text((x2, y2), line2, font=font, fill=INK_COLOR)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    thumb.save(out_path, "JPEG", quality=95)
    print(f"OK: {out_path}")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("用法: python thumbnail.py <card.png> <line1> <line2> <output.jpg>")
        sys.exit(1)
    make_thumbnail(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
