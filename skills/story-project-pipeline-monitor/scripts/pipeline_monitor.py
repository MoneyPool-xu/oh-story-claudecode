#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

STATUSES = {"COMPLETED", "IN_PROGRESS", "NOT_STARTED", "BLOCKED", "STALE", "CONDITIONAL", "SKIPPED"}

STEPS = [
    ("setup", "环境部署", "环境", "story-setup", []),
    ("market-scan", "目标平台扫榜", "市场", "story-long-scan / story-short-scan", []),
    ("benchmark-analysis", "对标作品拆解", "市场", "story-long-analyze / story-short-analyze", ["market-scan"]),
    ("positioning", "平台、题材与受众定位", "立项", "story-long-write / story-short-write", []),
    ("premise", "核心卖点与读者承诺", "立项", "story-long-write / story-short-write", ["positioning"]),
    ("characters", "人物、关系与声纹", "设定", "story-long-write / story-short-write", ["premise"]),
    ("world", "世界观、金手指与边界", "设定", "story-long-write / story-short-write", ["premise"]),
    ("outline", "总纲、分卷与主线", "大纲", "story-long-write / story-short-write", ["characters", "world"]),
    ("golden-three", "黄金三章细纲", "大纲", "story-long-write", ["outline"]),
    ("title-synopsis", "书名、简介与标签", "物料", "story-reader-cold-read + proofreading", ["positioning"]),
    ("prose-style", "项目文风与角色声纹校准", "文风", "story-prose-style", ["characters"]),
    ("platform-rules", "平台规则前置", "写前", "story-fanqie-compliance / story-review 七猫平台层（写作前约束）", ["positioning"]),
    ("voiceprint", "角色声纹卡", "写前", "story-prose-style", ["characters", "prose-style"]),
    ("source-inventory", "原创性来源清单", "写前", "story-originality-audit（建立来源清单）", ["benchmark-analysis"]),
    ("chapter-directive", "自然成稿指令卡", "写前", "story-natural-drafting", ["outline", "prose-style", "platform-rules", "voiceprint"]),
    ("drafting", "正文写作与改稿", "写作", "story-long-write / story-short-write", ["chapter-directive"]),
    ("tracking", "人物、时间线与伏笔同步", "写作", "story-long-write + tracking transaction", ["drafting"]),
    ("review", "综合审查", "写后", "story-review", ["drafting", "tracking"]),
    ("style-review", "文风反向审核", "写后", "story-prose-style", ["review"]),
    ("deslop", "去AI味与 Gate H", "写后", "story-deslop", ["style-review"]),
    ("proofreading", "中文终校", "写后", "story-chinese-proofreading", ["deslop"]),
    ("cold-read", "隔离冷读", "读者", "story-reader-cold-read", ["proofreading"]),
    ("originality", "原创性审计", "来源", "story-originality-audit", ["drafting"]),
    ("compliance", "目标平台规则门禁", "平台", "平台专用合规 skill", ["proofreading"]),
    ("cover", "封面制作与尺寸复核", "物料", "story-cover", ["title-synopsis"]),
    ("submission-package", "投稿包汇总", "投稿", "story-project-pipeline-monitor", ["title-synopsis", "proofreading", "cover"]),
    ("final-gate", "投稿前总门禁", "投稿", "story-project-pipeline-monitor", ["review", "style-review", "deslop", "proofreading", "cold-read", "submission-package"]),
    ("submitted", "投稿与回执记录", "投稿", "人工记录", ["final-gate"]),
    ("editor-feedback", "编辑退稿反馈复盘", "反馈", "story-review 反馈闭环", ["submitted"]),
]

PATTERNS = {
    # 两层结构（项目根/书目录/设定|大纲|正文）下，设定类产物在子目录里，因此必须递归匹配
    "positioning": ["*书名*定位*.md", "*立项*.md", "**/*题材*定位*.md", "设定/*定位*.md"],
    "premise": ["*书名*定位*.md", "*立项*.md", "*卖点*.md", "**/*题材*定位*.md"],
    "characters": ["*人物*设定*.md", "设定/*人物*.md", "人物/*.md", "设定/角色/*.md", "设定/人物/*.md"],
    "world": ["*世界观*.md", "*金手指*.md", "设定/世界观/*.md", "设定/势力/*.md", "设定/*边界*.md", "设定/*体系*.md"],
    "outline": ["*大纲*.md", "大纲/*.md"],
    "golden-three": ["*黄金三章*.md", "*前三章*细纲*.md"],
    "title-synopsis": ["简介.md", "*投稿简介*.md", "*书名*.md"],
    "prose-style": ["*文风*.md", "设定/文风.md", "*写作规则*.md", "报告/文风/**/*.md"],
    "platform-rules": ["参考资料/*平台*规范*.md", "参考资料/*发布规范*.md", "*平台*内容*规范*.md"],
    "voiceprint": ["设定/*声纹*.md", "*角色声纹*.md", "报告/文风/**/*声纹*.md"],
    "source-inventory": ["参考资料/*来源清单*.md", "*原创性*来源*.md"],
    "chapter-directive": ["报告/自然成稿/*.md", "**/*写作指令*.md"],
    "drafting": ["正文/*.md", "正文.md"],
    "tracking": ["追踪/*.md", "追踪/**/*.md", "追踪/_tracking-state.json"],
    "market-scan": ["**/*扫榜*报告*.md", "**/*市场*报告*.md"],
    "benchmark-analysis": ["拆文库/*/**/*报告*.md", "**/*拆文报告*.md"],
    "review": ["报告/**/*review*.md", "报告/**/*审查*.md", "报告/工作流/*post-write-gate*.md", "*审查报告*.md"],
    "style-review": ["报告/文风/**/*反向审核*.md", "报告/文风/**/*文风校准*.md", "报告/**/*style-review*.md", "报告/**/*文风漂移*.md"],
    "deslop": ["报告/**/*deslop*.md", "报告/**/*去AI*.md", "报告/工作流/*post-write-gate*.md", "*去AI*报告*.md"],
    "proofreading": ["报告/**/*proofread*.md", "报告/**/*终校*.md", "报告/**/*校对*.md", "报告/工作流/*post-write-gate*.md"],
    "cold-read": ["*冷读报告*.md", "报告/**/*冷读*.md"],
    "originality": ["报告/**/*originality*.md", "报告/**/*原创性*.md"],
    "compliance": ["报告/**/*compliance*.md", "报告/**/*合规*.md", "报告/**/*门禁*.md"],
    "cover": ["封面/*.png", "封面/*.jpg", "封面/*.webp", "*封面*.png", "*封面*.jpg"],
    "submission-package": ["投稿/**/*", "*投稿包*.md", "*投稿材料*.md"],
    "submitted": ["投稿/*回执*", "投稿/*记录*", "*投稿回执*", "*投稿记录*"],
    "editor-feedback": ["反馈/编辑退稿/*.md", "反馈/_feedback-state.json", "反馈/项目规则.md"],
}

GATE_IDS = {"chapter-directive", "tracking", "review", "style-review", "deslop", "proofreading", "cold-read", "originality", "compliance", "final-gate"}

NEXT_ACTIONS = {
    "setup": "用当前最新版 story-setup 重新部署并验证 agents/references。",
    "market-scan": "确认目标平台和数据日期，生成扫榜报告。",
    "benchmark-analysis": "锁定合法对标原文并完成拆文产物。",
    "positioning": "明确平台、题材、受众和篇幅。",
    "premise": "写定一句话卖点、核心冲突与差异点。",
    "characters": "补齐主配角动机、关系和声纹。",
    "world": "补齐世界规则、能力边界与代价。",
    "outline": "完成可执行总纲、分卷和主线。",
    "golden-three": "完成前三章任务、冲突与章末钩子。",
    "title-synopsis": "对发布态书名、简介和标签完成冷读与终校。",
    "prose-style": "生成当前项目文风与角色声纹规则。",
    "platform-rules": "把目标平台红线落成本书的写作边界文件，写作前加载，不留到写完再查。",
    "voiceprint": "逐角色写定说话目的、句法、回避方式与禁写项，遮住姓名仍可分辨。",
    "source-inventory": "登记对标、素材、真实事件与生成过程，标出借鉴距离与待办。",
    "chapter-directive": "在下一次写作前生成绑定当前输入的完整章卡。",
    "drafting": "按有效章卡完成正文与改稿。",
    "tracking": "提交追踪事务并运行一致性检查。",
    "review": "修复开放 S1/S2 后重跑 story-review。",
    "style-review": "对当前正文运行 story-prose-style 文风反向审核；没有基线时先建立项目文风与稳定样章锚点。",
    "deslop": "对当前正文运行去AI味与 Gate H 复检。",
    "proofreading": "对当前正文和投稿物料运行中文终校。",
    "cold-read": "隔离读取当前发布态材料并生成冷读账本。",
    "originality": "以正文和已使用对标来源运行原创性审计。",
    "compliance": "按目标平台和当前规则日期重跑发布门禁。",
    "cover": "生成并复核目标平台尺寸封面。",
    "submission-package": "汇总书名、简介、封面、标签和投稿正文。",
    "final-gate": "清零全部必需步骤的 BLOCKED/STALE/OPEN。",
    "submitted": "记录平台、投稿时间、版本和回执。",
    "editor-feedback": "保留编辑原话并在被投版本复现；只生成项目规则或带证据的平台候选。",
}


def newest(paths):
    return max((p.stat().st_mtime for p in paths if p.exists()), default=0)


def matches(project: Path, patterns):
    found = []
    for pattern in patterns:
        found.extend(
            p for p in project.glob(pattern)
            if p.is_file()
            and "原稿" not in p.name
            and not any(token in part for part in p.parts for token in ("备份", "归档"))
            and p.suffix.lower() not in {".zip", ".rar", ".7z"}
        )
    return sorted(set(found), key=lambda p: p.stat().st_mtime, reverse=True)


def chapter_commercial_gates(project: Path):
    rows = []
    for gate in sorted((project / "audit_logs").glob("chapter_*_gate.json")):
        try:
            doc = json.loads(gate.read_text(encoding="utf-8"))
            chapter = int(doc.get("chapter"))
            outline = project / doc.get("outline_path", "")
            current_hash = hashlib.sha256(outline.read_bytes()).hexdigest() if outline.is_file() else None
            blockers = doc.get("blockers") if isinstance(doc.get("blockers"), list) else []
            status = "PASS" if doc.get("decision") == "PASS" and not blockers else "BLOCK"
            if not current_hash or current_hash != doc.get("outline_sha256"):
                status = "STALE"
            dims = doc.get("dimensions") if isinstance(doc.get("dimensions"), dict) else {}
            rows.append({"chapter": chapter, "title": doc.get("title", ""), "chapter_type": doc.get("chapter_type", ""),
                         "status": status, "blockers": blockers, "dimensions": dims,
                         "path": str(gate.relative_to(project))})
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            rows.append({"chapter": None, "title": gate.stem, "status": "INVALID", "blockers": [str(exc)], "dimensions": {}, "path": str(gate.relative_to(project))})
    return rows


def find_setup_marker(project: Path, workspace: Path):
    """定位 .story-deployed。

    oh-story 标准结构是两层：项目根放部署标记，书目录放 设定/大纲/正文/追踪。
    扫描根指向书目录时，标记在上一层，因此从 project 向上找到 workspace 为止。
    标记内容只声明 target_cli（claude / codex / opencode ...），不影响"是否已部署"的判断。
    """
    candidates = [project, *project.parents]
    for d in candidates:
        marker = d / ".story-deployed"
        if marker.exists():
            return marker
        if d == workspace:
            break
    return None


def read_overrides(project: Path):
    path = project / ".story-pipeline" / "status.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("steps", {})
    except (OSError, json.JSONDecodeError):
        return {}


def skill_meta(path: Path):
    text = path.read_text(encoding="utf-8", errors="ignore")[:1200]
    name = re.search(r"(?m)^name:\s*[\"']?([^\r\n\"']+)", text)
    version = re.search(r"(?m)^version:\s*[\"']?([^\r\n\"']+)", text)
    version_file = path.parent / "VERSION"
    ver = version.group(1).strip() if version else (version_file.read_text().strip() if version_file.exists() else "未声明")
    return {"name": name.group(1).strip() if name else path.parent.name, "version": ver, "path": str(path), "mtime": path.stat().st_mtime}


def inventory(repo_root: Path):
    roots = [Path.home() / ".agents" / "skills", Path.home() / ".codex" / "skills", repo_root / "skills"]
    grouped = {}
    for root in roots:
        if not root.exists():
            continue
        for skill in root.glob("**/SKILL.md"):
            meta = skill_meta(skill)
            grouped.setdefault(meta["name"], []).append(meta)
    result = []
    for name, copies in grouped.items():
        copies.sort(key=lambda x: (-x["mtime"], 0 if "/.agents/skills/" in x["path"] or "/.codex/skills/" in x["path"] else 1))
        chosen = copies[0]
        result.append({**chosen, "copies": len(copies), "alternates": copies[1:]})
    return sorted(result, key=lambda x: x["name"])


def project_candidates(workspace: Path):
    result = []
    for path in [workspace] + [p for p in workspace.iterdir() if p.is_dir() and not p.name.startswith(".")]:
        if ((path / "正文").is_dir() or (path / "正文.md").is_file()
                or (path / ".active-book").exists() or (path / "_diagnostics.json").is_file()):
            result.append(path)
        if path.name in {"拆文库", "对标"}:
            result.extend(p for p in path.iterdir() if p.is_dir() and (p / "_diagnostics.json").is_file())
    return sorted(set(result), key=lambda p: p.name)


def narrative_diagnostics(project: Path):
    """Read derived Stage 4/5 summaries; never recalculate model-facing metrics here."""
    results = []
    for path in sorted(project.glob("**/_diagnostics.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            reader = payload.get("reader_debt", {}).get("summary")
            candidates = payload.get("skill_candidates", {}).get("summary")
            if not isinstance(reader, dict) or not isinstance(candidates, dict):
                continue
            results.append({"book": payload.get("book") or path.parent.name,
                            "path": str(path.relative_to(project)),
                            "generated_at": payload.get("generated_at"),
                            "reader_debt": reader, "skill_candidates": candidates})
        except (OSError, json.JSONDecodeError, ValueError):
            continue
    return results


def scan(workspace: Path, project: Path, repo_root: Path):
    overrides = read_overrides(project)
    body_files = matches(project, PATTERNS["drafting"])
    content_files = body_files + matches(project, ["简介.md", "*投稿简介*.md", "*书名*.md"])
    body_mtime = newest(body_files)
    body_chapters = [int(m.group(1)) for p in body_files if (m := re.search(r"第(\d+)章", p.name))]
    current_chapter = max(body_chapters, default=None)
    publication_files = matches(project, ["简介.md", "*投稿简介*.md", "*书名*.md"])
    publication_mtime = newest(publication_files)
    setup_file = find_setup_marker(project, workspace)
    rows = []
    status_map = {}

    for step_id, title, phase, skill, deps in STEPS:
        evidence_files = matches(project, PATTERNS.get(step_id, []))
        evidence = [str(p.relative_to(project)) for p in evidence_files[:5]]
        status = "NOT_STARTED"
        reason = "未发现可信完成证据"

        if step_id == "setup" and setup_file:
            status = "COMPLETED"
            evidence = [os.path.relpath(setup_file, project)]
            target = re.search(r"target_cli:\s*(\S+)", setup_file.read_text(encoding="utf-8", errors="ignore"))
            reason = f"发现部署标记（target_cli: {target.group(1)}）" if target else "发现部署标记"
        elif evidence_files:
            status, reason = "COMPLETED", "发现对应产物或报告"
        elif step_id in {"market-scan", "benchmark-analysis", "originality", "compliance", "source-inventory", "editor-feedback"}:
            status, reason = "CONDITIONAL", "需按平台、对标来源或发布阶段决定"

        if step_id == "originality" and matches(project, PATTERNS["benchmark-analysis"]) and not evidence_files:
            status, reason = "NOT_STARTED", "项目存在对标拆解，原创性审计成为必需步骤"

        if step_id == "setup" and setup_file:
            deployed = setup_file.read_text(encoding="utf-8", errors="ignore")
            deployed_setup = re.search(r"setup_skill_version:\s*([0-9.]+)", deployed)
            deployed_agents = re.search(r"agents_version:\s*(\d+)", deployed)
            installed_setup = next((x for x in inventory(repo_root) if x["name"] == "story-setup"), None)
            old_setup = installed_setup and deployed_setup and deployed_setup.group(1) != installed_setup["version"]
            old_agents = deployed_agents and int(deployed_agents.group(1)) < 29
            if old_setup or old_agents:
                status = "STALE"
                bits = []
                if old_setup: bits.append(f"部署 setup {deployed_setup.group(1)}，当前 {installed_setup['version']}")
                if old_agents: bits.append(f"部署 agents {deployed_agents.group(1)}，当前规范 29")
                reason = "；".join(bits) + "，需要重新部署"

        override = overrides.get(step_id)
        if override and override.get("status") in STATUSES:
            status = override["status"]
            reason = override.get("evidence", "人工登记")
            evidence = [reason]

        threshold = body_mtime
        if step_id in {"cold-read", "compliance"}:
            threshold = max(body_mtime, publication_mtime)
        if step_id == "chapter-directive":
            threshold = 0  # 章卡应先于正文；不能因正常写作顺序自动判失效
        if step_id in GATE_IDS and status == "COMPLETED" and threshold and newest(evidence_files) < threshold:
            status = "STALE"
            reason = "正文或发布物料晚于该检查证据，必须重跑"

        if step_id == "review" and status == "COMPLETED" and evidence_files:
            latest_text = evidence_files[0].read_text(encoding="utf-8", errors="ignore")
            if re.search(r"Result:\s*`?FIX|\bOPEN\b|存在一个 S[12]", latest_text):
                status = "IN_PROGRESS"
                reason = "最新审查有开放问题，尚未达到无阻断完成状态"

        if step_id == "title-synopsis" and evidence_files:
            cold_reports = matches(project, PATTERNS["cold-read"])
            proof_reports = matches(project, PATTERNS["proofreading"])
            cold_ok = newest(cold_reports) >= publication_mtime if publication_mtime else False
            proof_ok = any("简介" in p.read_text(encoding="utf-8", errors="ignore") for p in proof_reports if p.stat().st_mtime >= publication_mtime)
            if not (cold_ok and proof_ok):
                status = "IN_PROGRESS"
                reason = "书名/简介文件存在，但缺少绑定当前物料的冷读或终校证据"

        if step_id == "chapter-directive" and evidence_files:
            directive_chapters = {int(m.group(1)) for p in evidence_files if (m := re.search(r"第(\d+)章", p.name))}
            directive_sources = matches(project, PATTERNS["outline"] + PATTERNS["characters"] + PATTERNS["world"] + PATTERNS["prose-style"])
            # 只判「当前正文章节有没有章卡」。提前写好后续章节的章卡是正常预备，
            # 不构成失效——旧判据用 max(章卡章号) != 当前章号，会把预写章卡误判成 STALE。
            if current_chapter is not None and current_chapter not in directive_chapters:
                status = "STALE"
                reason = f"当前正文到第{current_chapter:03d}章，未找到对应的当前章卡"
            elif newest(directive_sources) > newest(evidence_files):
                status = "STALE"
                reason = "大纲、人物、世界观或文风晚于当前章卡，必须重建章卡"

        unmet = [d for d in deps if status_map.get(d) not in {"COMPLETED", "SKIPPED", "CONDITIONAL"}]
        if status == "NOT_STARTED" and unmet:
            status = "BLOCKED"
            reason = "等待前置步骤：" + "、".join(unmet)

        status_map[step_id] = status
        rows.append({"id": step_id, "title": title, "phase": phase, "skill": skill, "dependencies": deps,
                     "status": status, "reason": reason, "evidence": evidence,
                     "next_action": NEXT_ACTIONS[step_id] if status not in {"COMPLETED", "SKIPPED"} else "保持证据；输入变化时按失效规则重跑。"})

    required_ids = {x[0] for x in STEPS} - {"market-scan", "benchmark-analysis", "originality", "compliance", "source-inventory", "submitted", "editor-feedback"}
    if matches(project, PATTERNS["benchmark-analysis"]):
        required_ids.add("originality")
        required_ids.add("source-inventory")  # 用了对标就必须先登记来源，写前生效
    if matches(project, PATTERNS["compliance"]):
        required_ids.add("compliance")
    final_row = next(r for r in rows if r["id"] == "final-gate")
    final_unmet = [r["id"] for r in rows if r["id"] in required_ids - {"final-gate"} and r["status"] != "COMPLETED"]
    if final_unmet:
        final_row["status"] = "BLOCKED"
        final_row["reason"] = "投稿前仍有未完成或失效步骤：" + "、".join(final_unmet)
        final_row["next_action"] = NEXT_ACTIONS["final-gate"]
    completed = sum(1 for r in rows if r["id"] in required_ids and r["status"] == "COMPLETED")
    stale = [r for r in rows if r["status"] == "STALE"]
    blocked = [r for r in rows if r["status"] == "BLOCKED"]
    next_row = next((r for r in rows if r["id"] in required_ids and r["status"] in {"STALE", "IN_PROGRESS", "NOT_STARTED", "BLOCKED"}), None)
    if stale:
        next_row = stale[0]
    active_phase = next_row["phase"] if next_row else "完成"
    diagnostics = narrative_diagnostics(project)
    benchmark_row = next(row for row in rows if row["id"] == "benchmark-analysis")
    if diagnostics:
        latest = diagnostics[0]
        benchmark_row["quality_diagnostics"] = [
            {"stage": 4, "name": "Reader Debt Inflation", **latest["reader_debt"]},
            {"stage": 5, "name": "Skill Candidate Inflation", **latest["skill_candidates"]},
        ]
    return {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "workspace": str(workspace), "project": str(project), "project_name": project.name,
        "summary": {"completed": completed, "required": len(required_ids), "percent": round(completed * 100 / len(required_ids)),
                    "stale": len(stale), "blocked": len(blocked), "active_phase": active_phase,
                    "next": next_row},
        "steps": rows, "skills": inventory(repo_root), "diagnostics": diagnostics,
        "chapter_commercial_gates": chapter_commercial_gates(project),
    }


def write_report(data, project: Path):
    outdir = project / "报告" / "工作流"
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / (datetime.now().strftime("%Y-%m-%d-%H%M") + "-pipeline-monitor.md")
    lines = [f"# 全流程监测：{data['project_name']}", "", f"生成时间：{data['generated_at']}", "",
             f"进度：{data['summary']['completed']}/{data['summary']['required']}（{data['summary']['percent']}%）",
             f"当前阶段：{data['summary']['active_phase']}", "", "| 阶段 | 步骤 | 状态 | 前置依赖 | 负责 skill | 证据 / 原因 | 下一动作 |", "|---|---|---|---|---|---|---|"]
    for row in data["steps"]:
        ev = "；".join(row["evidence"]) or row["reason"]
        lines.append(f"| {row['phase']} | {row['title']} | `{row['status']}` | {', '.join(row['dependencies']) or '无'} | {row['skill']} | {ev} | {row['next_action']} |")
    if data.get("diagnostics"):
        lines.extend(["", "## Narrative Diagnostics", ""])
        for item in data["diagnostics"]:
            debt = item["reader_debt"]
            skill = item["skill_candidates"]
            lines.extend([
                f"### {item['book']}", "",
                f"- Stage 4 Reader Debt Inflation：`{debt.get('diagnosis', 'unknown')}`；活跃债务 {debt.get('active', 0)}，无证据 {debt.get('unsupported', 0)}，非具体等待 {debt.get('non_concrete', 0)}，休眠 {debt.get('dormant', 0)}。",
                f"- Stage 5 Skill Candidate Inflation：`{skill.get('diagnosis', 'unknown')}`；原始 {skill.get('raw_count', 0)}，合并后 {skill.get('merged_count', 0)}，证据覆盖 {skill.get('evidence_coverage', 0):.0%}，边界完整 {skill.get('boundary_completeness', 0):.0%}，重复率 {skill.get('duplication_rate', 0):.0%}。",
                f"- 诊断真源：`{item['path']}`", "",
            ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


class Handler(SimpleHTTPRequestHandler):
    workspace = Path.cwd()
    project = Path.cwd()
    repo_root = Path.cwd()
    assets = Path.cwd()

    def translate_path(self, path):
        clean = urlparse(path).path.lstrip("/") or "index.html"
        clean = {
            "pipeline.html": "index.html",
            "pipeline.css": "styles.css",
            "pipeline.js": "app.js",
        }.get(clean, clean)
        return str(self.assets / clean)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/status":
            query = parse_qs(parsed.query)
            project = Path(query.get("project", [str(self.project)])[0]).resolve()
            allowed = self.workspace.resolve()
            if project != allowed and allowed not in project.parents:
                return self.send_json({"error": "project outside workspace"}, 403)
            return self.send_json(scan(self.workspace, project, self.repo_root))
        if parsed.path == "/api/projects":
            return self.send_json({"projects": [{"name": p.name, "path": str(p)} for p in project_candidates(self.workspace)]})
        return super().do_GET()

    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        sys.stderr.write("[pipeline] " + fmt % args + "\n")


def main():
    parser = argparse.ArgumentParser(description="Monitor story projects from setup to submission")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("scan", "status", "serve"):
        p = sub.add_parser(name)
        p.add_argument("--workspace", required=True, type=Path)
        p.add_argument("--project", required=True, type=Path)
        if name == "serve":
            p.add_argument("--host", default="127.0.0.1")
            p.add_argument("--port", default=43110, type=int)
    mark = sub.add_parser("mark")
    mark.add_argument("--project", required=True, type=Path)
    mark.add_argument("--step", required=True)
    mark.add_argument("--status", required=True, choices=sorted(STATUSES))
    mark.add_argument("--evidence", required=True)
    args = parser.parse_args()

    skill_dir = Path(__file__).resolve().parent.parent
    repo_root = skill_dir.parent.parent
    if args.command == "mark":
        state_dir = args.project / ".story-pipeline"
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file = state_dir / "status.json"
        data = json.loads(state_file.read_text(encoding="utf-8")) if state_file.exists() else {"schema_version": 1, "steps": {}}
        data.setdefault("steps", {})[args.step] = {"status": args.status, "evidence": args.evidence, "updated_at": datetime.now().astimezone().isoformat(timespec="seconds")}
        state_file.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"ok": True, "step": args.step, "status": args.status}, ensure_ascii=False))
        return

    workspace, project = args.workspace.resolve(), args.project.resolve()
    if not workspace.exists() or not project.exists():
        raise SystemExit("workspace/project does not exist")
    if project != workspace and workspace not in project.parents:
        raise SystemExit("project must be inside workspace")
    if args.command in {"scan", "status"}:
        data = scan(workspace, project, repo_root)
        if args.command == "status":
            print(json.dumps(data, ensure_ascii=False))
            return
        report = write_report(data, project)
        print(json.dumps({"status": data, "report": str(report)}, ensure_ascii=False, indent=2))
        return

    Handler.workspace, Handler.project, Handler.repo_root, Handler.assets = workspace, project, repo_root, skill_dir / "assets"
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"本机地址：http://{args.host}:{args.port}/", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
