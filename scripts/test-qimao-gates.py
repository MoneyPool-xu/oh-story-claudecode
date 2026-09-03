#!/usr/bin/env python3
"""Small behavior tests for Qimao evidence-only gates."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).parents[1]


def run(*args: str) -> dict:
    result = subprocess.run(args, cwd=ROOT, check=True, text=True, capture_output=True)
    return json.loads(result.stdout)


with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    chapter = root / "第001章.md"
    chapter.write_text("# 第一章\n" + "危机正在逼近。" * 90 + "门外忽然有人叫出她真正的名字。", encoding="utf-8")
    funnel = run("python3", "skills/story-reader-cold-read/scripts/simulate_qimao_funnel.py", str(chapter), "--json")
    assert funnel["scope"].startswith("evidence extraction only")
    assert len(funnel["chapters"][0]["opening_excerpt"]) == 500
    assert funnel["chapters"][0]["tail_excerpt"].endswith("真正的名字。")

    risky = root / "风险.md"
    risky.write_text("他整理了一份躲避侦查的洗钱教程，旁边却写着反诈教材。", encoding="utf-8")
    lint = run("python3", "skills/story-review/scripts/qimao_compliance_lint.py", str(risky))
    assert lint["finding_count"] == 1
    assert lint["findings"][0]["severity"] == "REVIEW"
    assert "never" in lint["decision_rule"]

print("PASS: Qimao gates extract evidence without inventing platform thresholds")
