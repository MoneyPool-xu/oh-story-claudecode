#!/usr/bin/env python3
"""Validate and derive Stage 4/5 narrative diagnostics from item-level evidence."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


def ratio(part: int, total: int) -> float:
    return round(part / total, 4) if total else 0.0


def debt_summary(section: dict) -> dict:
    debts = section.get("debts", [])
    units = section.get("story_units", 0)
    unsupported = [d for d in debts if not d.get("created_ref") or not d.get("evidence_refs")]
    non_concrete = [d for d in debts if not d.get("reader_waiting_for") or d.get("concrete_wait") is not True]
    dormant = [d for d in debts if d.get("status") == "dormant"]
    active = [d for d in debts if d.get("status") == "active"]
    anomaly_kinds = sum(bool(items) for items in (unsupported, non_concrete, dormant))
    diagnosis = "high_risk" if anomaly_kinds >= 2 else "warning" if anomaly_kinds == 1 else "normal"
    return {
        "total": len(debts),
        "active": len(active),
        "unsupported": len(unsupported),
        "non_concrete": len(non_concrete),
        "dormant": len(dormant),
        "debt_density": round(len(active) / units, 4) if units else None,
        "unsupported_rate": ratio(len(unsupported), len(debts)),
        "concrete_wait_ratio": ratio(len(debts) - len(non_concrete), len(debts)),
        "dormant_rate": ratio(len(dormant), len(debts)),
        "diagnosis": diagnosis,
        "review_ids": sorted({str(d.get("id", "unknown")) for group in (unsupported, non_concrete, dormant) for d in group}),
    }


def candidate_summary(section: dict, single_book: bool) -> dict:
    candidates = section.get("candidates", [])
    levels = {level: [c for c in candidates if c.get("evidence_level") == level] for level in ("L1", "L2", "L3")}
    evidence_missing = [c for c in candidates if not c.get("evidence_refs")]
    boundary_missing = [c for c in candidates if not c.get("boundary") or not c.get("counterexample") or not c.get("failure_condition")]
    non_portable = [c for c in candidates if c.get("portable") is not True]
    duplicates = [c for c in candidates if c.get("merged_into")]
    level_errors = levels["L2"] + levels["L3"] if single_book else []
    anomaly_kinds = sum(bool(items) for items in (evidence_missing, boundary_missing, non_portable, duplicates, level_errors))
    diagnosis = "high_risk" if anomaly_kinds >= 2 else "warning" if anomaly_kinds == 1 else "normal"
    total = len(candidates)
    return {
        "raw_count": total,
        "merged_count": total - len(duplicates),
        "l1": len(levels["L1"]),
        "l2": len(levels["L2"]),
        "l3": len(levels["L3"]),
        "evidence_coverage": ratio(total - len(evidence_missing), total),
        "boundary_completeness": ratio(total - len(boundary_missing), total),
        "portable_rate": ratio(total - len(non_portable), total),
        "duplication_rate": ratio(len(duplicates), total),
        "single_book_level_errors": len(level_errors),
        "diagnosis": diagnosis,
        "review_ids": sorted({str(c.get("id", "unknown")) for group in (evidence_missing, boundary_missing, non_portable, duplicates, level_errors) for c in group}),
    }


def validate(data: dict) -> None:
    if data.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")
    if not isinstance(data.get("reader_debt", {}).get("debts", []), list):
        raise ValueError("reader_debt.debts must be a list")
    if not isinstance(data.get("skill_candidates", {}).get("candidates", []), list):
        raise ValueError("skill_candidates.candidates must be a list")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    data = json.loads(args.path.read_text(encoding="utf-8"))
    validate(data)
    data["generated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    data["reader_debt"]["summary"] = debt_summary(data["reader_debt"])
    data["skill_candidates"]["summary"] = candidate_summary(
        data["skill_candidates"], bool(data.get("single_book", True))
    )
    args.path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "path": str(args.path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
