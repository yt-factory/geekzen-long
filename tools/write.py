#!/usr/bin/env python3
"""
tools/write.py — 极客禅写作引擎：把 think 输出改写为 TTS 朗读脚本。

Usage:
    python tools/write.py <think_output.md> <write_output.md> <script.txt> [entry] [closing]
"""
import os
import re
import sys

import anthropic

WRITE_SYSTEM_PROMPT = """\
你是一个视频脚本写作引擎，专门为"极客禅"频道服务。

极客禅的风格：
- 用程序员熟悉的隐喻触碰人生困境
- 不说教，不给答案，只是陪着想
- 克制，留白，有禅意
- 结尾是开放的问题或一片沉默，不是励志总结

你的任务：接收一篇"追本"分析，改写为适合 TTS 朗读的视频脚本。

改写要求：
1. 第一人称，口语化，像在和一个朋友说话
2. 保留所有哲学层次，但去掉学术腔和格式标记
3. 每段不超过 4 行，段落间有自然停顿
4. 总长 1000-1200 字
5. 结构：
   - 开头：具体场景或困境（3-5 句）
   - 中间：think 的各层内容，自然流动
   - 结尾：留白，一个问题或一句话，不总结

输出要求：
- 只输出脚本正文
- 不要标题、不要分隔线、不要任何 markdown 标记
- 不要"第 X 层"这类标题
- 段落之间用空行分隔"""


def run_write(
    think_content: str,
    entry_paragraph: str,
    closing_paragraph: str,
    output_path: str,
) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    entry_block = (
        f"【创作者提供的入口段落（必须保留，放在最开头）】\n{entry_paragraph}"
        if entry_paragraph
        else "【入口段落】（无，请根据 think 内容自行生成一个具体的开场）"
    )
    closing_block = (
        f"【创作者提供的结尾段落（必须保留，放在最结尾）】\n{closing_paragraph}"
        if closing_paragraph
        else "【结尾段落】（无，请根据内容自行生成一个开放式结尾）"
    )

    user_content = f"""\
请将以下"追本"分析改写为极客禅视频脚本。

{entry_block}

【追本分析原文】
{think_content}

{closing_block}"""

    message = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=2500,
        system=WRITE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )

    result = message.content[0].text

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"✅ write 完成：{output_path}")
    return result


def clean_for_tts(write_content: str) -> str:
    """去掉所有 markdown 标记，生成纯净的 TTS 输入文本。"""
    text = write_content
    text = re.sub(r"^#+\s+", "", text, flags=re.MULTILINE)   # 标题
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)             # 粗体
    text = re.sub(r"\*(.+?)\*", r"\1", text)                 # 斜体
    text = re.sub(r"`(.+?)`", r"\1", text)                   # 行内代码
    text = re.sub(r"^-{3,}$", "", text, flags=re.MULTILINE)  # 分隔线
    text = re.sub(r"\n{3,}", "\n\n", text)                   # 多余空行
    return text.strip()


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python tools/write.py <think.md> <write_out.md> <script.txt> [entry] [closing]")
        sys.exit(1)
    think_path = sys.argv[1]
    write_out = sys.argv[2]
    script_out = sys.argv[3]
    entry = sys.argv[4] if len(sys.argv) > 4 else ""
    closing = sys.argv[5] if len(sys.argv) > 5 else ""

    with open(think_path, encoding="utf-8") as f:
        think_content = f.read()

    write_content = run_write(think_content, entry, closing, write_out)
    script = clean_for_tts(write_content)

    with open(script_out, "w", encoding="utf-8") as f:
        f.write(script)

    print(f"✅ script.txt 已生成：{script_out}（{len(script)} 字）")
