#!/usr/bin/env python3
"""Find dialogue runs that may read like efficient notes instead of live speech.

The detector only creates review candidates. It never decides that short dialogue,
rapid commands, arguments, or sparse action beats are automatically bad prose.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path


TEXT_SUFFIXES = {".md", ".txt"}
SKIP_DIRS = {
    ".git", ".story-pipeline", "node_modules", "归档", "追踪", "设定",
    "大纲", "参考资料", "对标", "拆文库",
}
DIALOGUE_RE = re.compile(r"[“\"]([^”\"\n]+)[”\"]")
PARAGRAPH_RE = re.compile(r"(?ms)(?:^|\n\s*\n)(.*?)(?=\n\s*\n|\Z)")
VISIBLE_RE = re.compile(r"[\s\W_]", re.UNICODE)
QUESTION_RE = re.compile(r"[？?]")
SYSTEM_RE = re.compile(r"^【.*】$", re.DOTALL)
FUNCTIONAL_RE = re.compile(
    r"合同|签字|签约|责任|担责|账期|货款|坏账|期限|价格|租金|设备|资源|"
    r"申请|批准|复核|供应|担保|排序|调资|调度|原价|运费|损耗|授权|额度|"
    r"支付|追偿|转售|借用|必须|马上|负责|确认|安排|处理|执行|条件|方案|计划|"
    r"contract|term|approve|resource|responsib|confirm|execute",
    re.IGNORECASE,
)
REVIEW_QUESTIONS = [
    "蒙住姓名后，能否凭关注点、句式和关系姿态辨认说话者？",
    "人物是否准确回答得过头，像在配合作者完成信息交付？",
    "是否存在回避、误解、面子、欲望、亏欠或关系余波？",
    "动作是否改变交流，而非只负责把台词隔开？",
    "改写成会议要点或合同条款后，人物和情绪是否几乎无损？",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Flag mechanically suspicious dialogue runs for semantic review."
    )
    parser.add_argument("targets", nargs="*", help="Prose files or directories")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--fail-on-high-risk", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def canonical_root(path: Path) -> Path:
    if path.is_dir() and (path / "正文").is_dir():
        return path / "正文"
    return path


def collect_files(raw_paths: list[str]) -> list[Path]:
    files: set[Path] = set()
    for raw in raw_paths:
        path = canonical_root(Path(raw).expanduser())
        if not path.exists():
            raise FileNotFoundError(raw)
        if path.is_file():
            if path.suffix.lower() in TEXT_SUFFIXES:
                files.add(path.resolve())
            continue
        for candidate in path.rglob("*"):
            if not candidate.is_file() or candidate.suffix.lower() not in TEXT_SUFFIXES:
                continue
            relative_parts = candidate.relative_to(path).parts[:-1]
            if any(part.startswith(".") or part in SKIP_DIRS for part in relative_parts):
                continue
            files.add(candidate.resolve())
    return sorted(files)


def visible_length(text: str) -> int:
    return len(VISIBLE_RE.sub("", text))


def analyze_run(run: list[dict], file_name: str) -> dict | None:
    if len(run) < 5:
        return None

    lengths = [turn["length"] for turn in run]
    median_length = statistics.median(lengths)
    short_share = sum(length <= 12 for length in lengths) / len(run)
    supportless_share = sum(turn["support_length"] <= 2 for turn in run) / len(run)
    questions = [bool(QUESTION_RE.search(turn["text"])) for turn in run]
    question_count = sum(questions)
    question_alternations = sum(a != b for a, b in zip(questions, questions[1:]))
    functional_count = sum(bool(FUNCTIONAL_RE.search(turn["text"])) for turn in run)
    functional_share = functional_count / len(run)

    signals: list[str] = []
    score = 0
    if len(run) >= 6 and median_length <= 14 and short_share >= 0.65:
        signals.append("连续短答")
        score += 1
    if len(run) >= 5 and supportless_share >= 0.70:
        signals.append("动作承接偏少")
        score += 1
    if len(run) >= 6 and question_count >= 2 and question_alternations >= 3:
        signals.append("乒乓问答")
        score += 1
    if len(run) >= 6 and functional_share >= 0.35 and supportless_share >= 0.45:
        signals.append("任务或事务纪要化")
        score += 2
    if len(run) >= 9 and max(lengths) - min(lengths) <= 15:
        signals.append("轮次长度过齐")
        score += 1

    if score < 2:
        return None
    risk = "HIGH" if score >= 4 and (functional_count or len(run) >= 9) else "REVIEW"
    return {
        "file": file_name,
        "start_line": run[0]["line"],
        "end_line": run[-1]["line"],
        "turns": len(run),
        "median_length": round(float(median_length), 1),
        "short_share": round(short_share, 2),
        "supportless_share": round(supportless_share, 2),
        "functional_share": round(functional_share, 2),
        "risk": risk,
        "signals": signals,
        "preview": " / ".join(turn["text"] for turn in run[:3]),
        "review_questions": REVIEW_QUESTIONS,
    }


def analyze_text(text: str, file_name: str = "<memory>") -> list[dict]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    run: list[dict] = []
    findings: list[dict] = []
    gap_count = 0

    def flush() -> None:
        nonlocal run, gap_count
        finding = analyze_run(run, file_name)
        if finding:
            findings.append(finding)
        run = []
        gap_count = 0

    for paragraph_match in PARAGRAPH_RE.finditer(text):
        paragraph = paragraph_match.group(1).strip()
        if not paragraph:
            continue
        line = text.count("\n", 0, paragraph_match.start(1)) + 1
        quotes = DIALOGUE_RE.findall(paragraph)
        if quotes:
            outside = DIALOGUE_RE.sub("", paragraph)
            support_length = visible_length(outside)
            for spoken in quotes:
                spoken = spoken.strip()
                run.append(
                    {
                        "text": spoken,
                        "length": visible_length(spoken),
                        "support_length": support_length,
                        "line": line,
                    }
                )
            gap_count = 0
            continue

        length = visible_length(paragraph)
        if run and not SYSTEM_RE.match(paragraph) and length <= 42 and gap_count < 1:
            gap_count += 1
            continue
        flush()

    flush()
    return findings


def run_self_test() -> None:
    risky = """“账期呢？”\n\n“二十四小时。”\n\n“太短。”\n\n“改成四十八小时。”\n\n“谁签字？”\n\n“每家自己签。”\n\n“坏账谁负责？”\n\n“按店计算。”"""
    natural = """“今晚还开不开？”\n\n她把保温箱搬上桌，没急着答。\n\n“你问得倒轻巧。锅有，货呢？”\n\n门口的人摸了摸口袋：“那我先去别家看看。”\n\n“去吧。看见便宜的，回来告诉我一声。”"""
    risky_findings = analyze_text(risky, "<risky>")
    natural_findings = analyze_text(natural, "<natural>")
    if not risky_findings or risky_findings[0]["risk"] != "HIGH":
        raise AssertionError("failed to flag a transactional short-answer chain")
    if natural_findings:
        raise AssertionError("falsely flagged a short exchange with relational action")
    print("SELF-TEST PASS: risky note-like dialogue is flagged; natural short dialogue is preserved.")


def main() -> int:
    args = parse_args()
    try:
        if args.self_test:
            run_self_test()
        if not args.targets:
            if args.self_test:
                return 0
            raise ValueError("provide at least one prose file or directory")
        files = collect_files(args.targets)
        if not files:
            raise ValueError("no target .md or .txt prose files found")
        findings: list[dict] = []
        for path in files:
            findings.extend(analyze_text(path.read_text(encoding="utf-8-sig"), str(path)))
    except (OSError, UnicodeError, ValueError, AssertionError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    result = {
        "scanned_files": len(files),
        "findings": findings,
        "automatic_verdict": False,
        "semantic_review_required": bool(findings),
    }
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for finding in findings:
            metrics = (
                f"turns={finding['turns']} median={finding['median_length']} "
                f"short={finding['short_share']} supportless={finding['supportless_share']} "
                f"functional={finding['functional_share']}"
            )
            print(
                f"[{finding['risk']}] {finding['file']}:"
                f"{finding['start_line']}-{finding['end_line']} {metrics}"
            )
            print(f"  signals: {'、'.join(finding['signals'])}")
            print(f"  preview: {finding['preview']}")
        if findings:
            print("Semantic review questions:")
            for index, question in enumerate(REVIEW_QUESTIONS, 1):
                print(f"  {index}. {question}")
        else:
            print("PASS: no mechanical candidates. Manual voice review is still required.")

    if args.fail_on_high_risk and any(item["risk"] == "HIGH" for item in findings):
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

