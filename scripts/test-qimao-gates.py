#!/usr/bin/env python3
"""Small behavior tests for Qimao evidence-only gates."""

from __future__ import annotations

import json
import hashlib
import importlib.util
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

with tempfile.TemporaryDirectory() as directory:
    book = Path(directory)
    outline = book / "大纲" / "细纲_第001章.md"
    outline.parent.mkdir()
    outline.write_text("- 商业价值门禁：启用\n- 主角目标/关键选择：查清真相\n", encoding="utf-8")
    core = ROOT / "skills/story-setup/references/templates/hooks/story_hook_core.js"
    js = subprocess.run(["node", "-e", "const c=require(process.argv[1]);const x=c.chapterCommercialGateIssue(process.argv[2],1,process.argv[3]);process.stdout.write(x||'PASS')", str(core), str(book), str(outline)], check=True, text=True, capture_output=True)
    assert "缺少 audit_logs" in js.stdout

    gate_dir = book / "audit_logs"
    gate_dir.mkdir()
    dimensions = {
        "state_change": {"status": "present", "evidence": "证词公开"},
        "core_advantage": {"status": "not_applicable", "evidence": "关系回收章"},
        "contested_value": {"status": "present", "evidence": "争夺证词控制权"},
        "visible_gain_or_payment": {"status": "present", "evidence": "获得关键证词"},
        "next_question": {"status": "present", "evidence": "谁先拿走原件？", "concrete": True},
        "protagonist_action": {"status": "present", "evidence": "主角主动公开副本"},
    }
    (gate_dir / "chapter_1_gate.json").write_text(json.dumps({
        "schema_version": 1, "chapter": 1,
        "outline_sha256": hashlib.sha256(outline.read_bytes()).hexdigest(),
        "dimensions": dimensions, "decision": "PASS", "blockers": [],
    }, ensure_ascii=False), encoding="utf-8")
    js = subprocess.run(["node", "-e", "const c=require(process.argv[1]);const x=c.chapterCommercialGateIssue(process.argv[2],1,process.argv[3]);process.stdout.write(x||'PASS')", str(core), str(book), str(outline)], check=True, text=True, capture_output=True)
    assert js.stdout == "PASS"

    codex_hook = ROOT / "skills/story-setup/references/codex/hooks/story_codex_hook.py"
    spec = importlib.util.spec_from_file_location("story_codex_gate_test", codex_hook)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    assert module.chapter_commercial_gate_issue(book, 1, outline) is None

print("PASS: chapter commercial gate is hash-bound and parity-checked")
