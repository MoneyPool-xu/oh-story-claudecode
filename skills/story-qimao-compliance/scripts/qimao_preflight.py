#!/usr/bin/env python3
"""Deterministic preflight checks for Qimao-bound fiction text.

Extends the Fanqie scanner with Qimao-specific rhythm and pacing checks:
- Golden-three-chapter pacing indicators
- Psychology/background description length
- Dialogue density
- Golden-finger and CP keyword position tracking
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path


TEXT_SUFFIXES = {".md", ".txt"}
ENGINEERING_RE = re.compile(
    r"(?:第[一二三四五六七八九十百千万两0-9]+章|上一章|上章|前一章|本章|这一章|"
    r"前文|后文|细纲|读者|爽点|伏笔|任务卡|章节定位)"
)
CONTACT_RE = re.compile(
    r"(?:加(?:微信|V|v|QQ)|微信号|QQ(?:群|号)|私信我|扫码(?:进群|购买|联系)|"
    r"购买链接|返利群|投资群|联系(?:客服|作者)购买)"
)
BYPASS_RE = re.compile(
    r"(?:绕过审核|规避审核|躲过审核|卡审核|利用平台漏洞|平台漏洞教程|封号规避|养号教程)"
)
TRACK_DRIFT_RE = re.compile(
    r"(?:权谋|朝堂|朝政|上朝|议政|军功|兵权|女将军|女帝|称帝|夺嫡)"
)
TITLE_RE = re.compile(r"^\s*#{1,6}\s+第[一二三四五六七八九十百千万两0-9]+章")
CHAPTER_SPLIT_RE = re.compile(r"^#{1,6}\s+第[一二三四五六七八九十百千万两0-9]+章")
SPACE_RE = re.compile(r"\s+")
WORDISH_RE = re.compile(r"[一-鿿A-Za-z0-9]")
DIALOGUE_RE = re.compile(r"[""「」『』]")
GOLDEN_FINGER_RE = re.compile(
    r"(?:发簪|先祖|传承|激活|苏醒|醒了|金手指|系统|技能|传音|附身|"
    r"虚影|残魂|解锁|觉醒|血脉|灵力|占卜|医术|辨毒)"
)
CP_RE = re.compile(
    r"(?:世子|侯爷|殿下|王爷|少主|公子|夫君|相公|未婚夫|婚约|"
    r"心跳|脸红|心动|目光|注视|玉佩|桂花糕|保重)"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan fiction files for Qimao preflight signals."
    )
    parser.add_argument("paths", nargs="+", help="Markdown/text files or directories")
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def collect_files(raw_paths: list[str]) -> list[Path]:
    files: set[Path] = set()
    for raw in raw_paths:
        path = Path(raw).expanduser()
        if not path.exists():
            raise FileNotFoundError(raw)
        if path.is_file():
            if path.suffix.lower() in TEXT_SUFFIXES:
                files.add(path.resolve())
            continue
        for candidate in path.rglob("*"):
            if candidate.is_file() and candidate.suffix.lower() in TEXT_SUFFIXES:
                files.add(candidate.resolve())
    return sorted(files)


def normalized_paragraph(text: str) -> str:
    return SPACE_RE.sub("", text).strip()


def count_chinese(text: str) -> int:
    return len(re.findall(r"[一-鿿]", text))


def scan_file(path: Path) -> tuple[list[dict], dict]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    findings: list[dict] = []
    paragraphs: dict[str, list[int]] = defaultdict(list)
    current: list[str] = []
    start_line = 1

    # Qimao-specific tracking
    dialogue_chars = 0
    total_chars = 0
    consecutive_psych = 0
    max_psych_block = 0
    psych_block_line = 0
    consecutive_bg = 0
    max_bg_block = 0
    bg_block_line = 0
    golden_finger_lines: list[int] = []
    cp_lines: list[int] = []
    track_drift_lines: list[int] = []
    first_conflict_line = 0

    def add(kind: str, severity: str, line: int, message: str, excerpt: str) -> None:
        findings.append(
            {
                "file": str(path),
                "line": line,
                "kind": kind,
                "severity": severity,
                "message": message,
                "excerpt": excerpt[:120],
            }
        )

    def flush_paragraph() -> None:
        nonlocal current, start_line
        if not current:
            return
        paragraph = normalized_paragraph("\n".join(current))
        if len(paragraph) >= 24:
            paragraphs[paragraph].append(start_line)
        current = []

    for number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            start_line = number + 1
            # Reset consecutive counters on blank line
            if consecutive_psych > max_psych_block:
                max_psych_block = consecutive_psych
                psych_block_line = number - consecutive_psych
            consecutive_psych = 0
            if consecutive_bg > max_bg_block:
                max_bg_block = consecutive_bg
                bg_block_line = number - consecutive_bg
            consecutive_bg = 0
            continue
        if not current:
            start_line = number
        current.append(line)

        char_count = count_chinese(stripped)
        total_chars += char_count

        # Dialogue detection
        if DIALOGUE_RE.search(stripped):
            dialogue_chars += char_count

        # Track drift (权谋/军事)
        if TRACK_DRIFT_RE.search(stripped):
            track_drift_lines.append(number)

        # Golden finger keywords
        if GOLDEN_FINGER_RE.search(stripped):
            golden_finger_lines.append(number)

        # CP keywords
        if CP_RE.search(stripped):
            cp_lines.append(number)

        is_title = number <= 3 and TITLE_RE.search(line)
        if not is_title and ENGINEERING_RE.search(line):
            add(
                "engineering-metadata",
                "BLOCK",
                number,
                "正文疑似泄漏写作工程词。",
                stripped,
            )
        if CONTACT_RE.search(line):
            add(
                "contact-or-transaction",
                "REVIEW",
                number,
                "疑似现实联系方式或交易引流。",
                stripped,
            )
        if BYPASS_RE.search(line):
            add(
                "platform-bypass",
                "REVIEW",
                number,
                "疑似平台漏洞或绕审表达。",
                stripped,
            )
        visible = [char for char in stripped if not char.isspace()]
        if len(visible) >= 16:
            wordish = sum(1 for char in visible if WORDISH_RE.match(char))
            if wordish / len(visible) < 0.25:
                add(
                    "symbol-heavy-line",
                    "BLOCK",
                    number,
                    "该行以符号或非文字内容为主，疑似无意义填充。",
                    stripped,
                )
    flush_paragraph()
    # Final consecutive check
    if consecutive_psych > max_psych_block:
        max_psych_block = consecutive_psych
        psych_block_line = len(lines) - consecutive_psych
    if consecutive_bg > max_bg_block:
        max_bg_block = consecutive_bg
        bg_block_line = len(lines) - consecutive_bg

    # Duplicate paragraphs
    for paragraph, locations in paragraphs.items():
        if len(locations) < 2:
            continue
        add(
            "duplicate-paragraph",
            "BLOCK",
            locations[1],
            f"发现重复段落，共出现 {len(locations)} 次，行号 {locations}。",
            paragraph,
        )

    # Track drift warning
    if track_drift_lines:
        add(
            "track-drift",
            "REVIEW",
            track_drift_lines[0],
            f"发现权谋/军事/朝堂关键词 {len(track_drift_lines)} 处（行 {track_drift_lines[:5]}），"
            f"七猫女频宅斗赛道需确认未偏移。",
            "",
        )

    # Pacing indicators
    dialogue_ratio = dialogue_chars / max(total_chars, 1)
    gf_first = golden_finger_lines[0] if golden_finger_lines else 0
    cp_first = cp_lines[0] if cp_lines else 0

    stats = {
        "file": str(path),
        "characters": total_chars,
        "lines": len(lines),
        "findings": len(findings),
        "qimao_pacing": {
            "dialogue_ratio": round(dialogue_ratio, 3),
            "golden_finger_first_line": gf_first,
            "golden_finger_mentions": len(golden_finger_lines),
            "cp_first_line": cp_first,
            "cp_mentions": len(cp_lines),
            "track_drift_count": len(track_drift_lines),
            "max_psych_block_chars": max_psych_block,
            "max_bg_block_chars": max_bg_block,
        },
    }
    return findings, stats


def main() -> int:
    args = parse_args()
    try:
        files = collect_files(args.paths)
    except (OSError, FileNotFoundError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if not files:
        print("ERROR: no .md or .txt files found", file=sys.stderr)
        return 2

    findings: list[dict] = []
    stats: list[dict] = []
    for path in files:
        try:
            file_findings, file_stats = scan_file(path)
        except (OSError, UnicodeError) as exc:
            print(f"ERROR: {path}: {exc}", file=sys.stderr)
            return 2
        findings.extend(file_findings)
        stats.append(file_stats)

    blockers = [item for item in findings if item["severity"] == "BLOCK"]
    advisories = [item for item in findings if item["severity"] != "BLOCK"]
    result = {
        "summary": {
            "files": len(files),
            "blockers": len(blockers),
            "advisories": len(advisories),
            "manual_semantic_review_required": True,
        },
        "findings": findings,
        "stats": stats,
    }

    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"Scanned {len(files)} file(s): "
            f"{len(blockers)} blocker(s), {len(advisories)} advisory item(s)."
        )
        for item in findings:
            print(
                f"[{item['severity']}] {item['file']}:{item['line']} "
                f"{item['kind']} - {item['message']}"
            )
            if item["excerpt"]:
                print(f"  {item['excerpt']}")
        if stats:
            for s in stats:
                p = s.get("qimao_pacing", {})
                print(f"\nQimao pacing ({Path(s['file']).name}):")
                print(f"  dialogue ratio: {p.get('dialogue_ratio', 0):.1%}")
                print(f"  golden-finger first mention: line {p.get('golden_finger_first_line', 'N/A')}, total {p.get('golden_finger_mentions', 0)}")
                print(f"  CP first mention: line {p.get('cp_first_line', 'N/A')}, total {p.get('cp_mentions', 0)}")
                print(f"  track-drift keywords: {p.get('track_drift_count', 0)}")
        print("\nManual semantic review is still required.")

    return 1 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
