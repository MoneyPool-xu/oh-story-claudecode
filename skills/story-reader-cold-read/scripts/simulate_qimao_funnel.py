#!/usr/bin/env python3
"""Build an evidence packet for a Qimao-oriented opening cold read.

This tool extracts checkpoints; it does not predict real completion or retention.
Semantic PASS/RISK/BLOCK decisions remain a cold-reader judgment tied to the text.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def visible_text(raw: str) -> str:
    raw = re.sub(r"\A\ufeff?---\s*\n.*?\n---\s*\n", "", raw, flags=re.S)
    raw = re.sub(r"(?m)^#{1,6}\s+.*$", "", raw)
    return re.sub(r"\s+", "", raw)


def main() -> None:
    parser = argparse.ArgumentParser(description="提取七猫开篇漏斗冷读证据，不预测真实完读率。")
    parser.add_argument("chapters", nargs="+", type=Path)
    parser.add_argument("--opening", type=int, default=500)
    parser.add_argument("--tail", type=int, default=200)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.opening < 100 or args.tail < 50:
        raise SystemExit("opening 不应小于 100，tail 不应小于 50")

    chapters = []
    for path in args.chapters:
        text = visible_text(path.read_text(encoding="utf-8-sig"))
        chapters.append({
            "path": str(path),
            "visible_chars": len(text),
            "opening_checkpoint_chars": min(args.opening, len(text)),
            "opening_excerpt": text[: args.opening],
            "tail_checkpoint_chars": min(args.tail, len(text)),
            "tail_excerpt": text[-args.tail :],
        })
    result = {
        "scope": "evidence extraction only; not a real completion-rate or retention prediction",
        "opening_checkpoint": args.opening,
        "tail_checkpoint": args.tail,
        "chapters": chapters,
        "required_semantic_questions": [
            "前置片段是否已让读者感知人物当前问题或核心承诺？",
            "每章尾段能否用一句具体问题表达下一步等待？",
            "章尾动力来自行动、风险、选择、信息、关系变化或兑现后果中的哪一类？",
        ],
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
