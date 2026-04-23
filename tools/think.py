#!/usr/bin/env python3
"""
tools/think.py — 追本之箭：给定主题词，纵向下钻6层到达本质。

Usage:
    python tools/think.py <主题词> <output_path.md>
"""
import os
import sys

import anthropic

THINK_SYSTEM_PROMPT = """\
你是一个追本溯源的思考引擎。

你的任务：给定一个主题词或现象，像钻头一样纵向下钻，每一层都找到\
表层答案里隐藏的新问题，直到抵达不可再分的本质。

格式要求：
- 起点：1-2 句话描述这个主题表面看起来是什么
- 第一层到第六层：每层一个简短小标题（2-4 字），内容 100-200 字
  * 每层结尾必须有一个"裂缝"——下一层要钻的新问题
  * 格式：裂缝：[新问题]
- 终点：最终抵达的本质，不超过 200 字，不给答案，给方向

风格：
- 克制，不煽情
- 有哲学深度，但不用学术术语
- 像一把手术刀，不像一篇散文
- 结尾是开放的，不是闭合的"""


def run_think(topic: str, output_path: str) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    message = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=2000,
        system=THINK_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"请对以下主题进行追本溯源：{topic}"}],
    )

    result = message.content[0].text

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# 追本之箭：{topic}\n\n")
        f.write(result)

    print(f"✅ think 完成：{output_path}")
    return result


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python tools/think.py <主题词> <output_path.md>")
        sys.exit(1)
    run_think(sys.argv[1], sys.argv[2])
