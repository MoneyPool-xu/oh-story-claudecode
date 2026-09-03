#!/usr/bin/env python3
"""Locate public-rule compliance signals for contextual review, never auto-convict."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def load_signals(path: Path) -> list[tuple[str, str, str]]:
    signals = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        severity, category, pattern = line.split("\t", 2)
        signals.append((severity, category, pattern))
    return signals


def main() -> None:
    parser = argparse.ArgumentParser(description="扫描七猫公开规则相关风险信号，仅生成语境复核候选。")
    parser.add_argument("manuscript", type=Path)
    parser.add_argument("--signals", type=Path, default=Path(__file__).parents[1] / "references/platforms/qimao-compliance-signals.txt")
    args = parser.parse_args()
    text = args.manuscript.read_text(encoding="utf-8-sig")
    findings = []
    for severity, category, pattern in load_signals(args.signals):
        for match in re.finditer(pattern, text, flags=re.I):
            start = max(0, match.start() - 30)
            end = min(len(text), match.end() + 30)
            findings.append({"severity": severity, "category": category, "match": match.group(0), "context": text[start:end], "offset": match.start()})
    print(json.dumps({
        "scope": "public-rule signal candidates; every match requires contextual review",
        "manuscript": str(args.manuscript),
        "finding_count": len(findings),
        "findings": findings,
        "decision_rule": "A token match alone is never a violation finding or automatic replacement instruction.",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
