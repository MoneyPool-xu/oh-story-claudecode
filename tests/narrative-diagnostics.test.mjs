import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { spawn } from "node:child_process";
import test from "node:test";
import { fileURLToPath } from "node:url";

const repositoryRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const script = join(repositoryRoot, "skills", "story-long-analyze", "scripts", "narrative_diagnostics.py");

test("derives evidence-backed Reader Debt and Skill Candidate inflation summaries", async () => {
  const root = await mkdtemp(join(tmpdir(), "oh-story-diagnostics-"));
  const path = join(root, "_diagnostics.json");
  try {
    await writeFile(path, JSON.stringify({
      schema_version: 1,
      book: "测试书",
      single_book: true,
      reader_debt: {
        story_units: 4,
        debts: [
          { id: "D1", created_ref: "第1章/P1", evidence_refs: ["第1章/P1"], reader_waiting_for: "身份何时揭晓", concrete_wait: true, status: "active" },
          { id: "D2", reader_waiting_for: "", concrete_wait: false, status: "dormant" },
        ],
      },
      skill_candidates: {
        candidates: [
          { id: "S1", evidence_level: "L1", evidence_refs: ["第1章/P1"], boundary: ["身份悬念"], counterexample: "读者尚未形成不公平判断", failure_condition: ["长期不支付"], portable: true },
          { id: "S2", evidence_level: "L2", evidence_refs: [], boundary: [], failure_condition: [], portable: false, merged_into: "S1" },
        ],
      },
    }), "utf8");

    const exitCode = await new Promise((accept, reject) => {
      const child = spawn("python3", [script, path], { stdio: "ignore" });
      child.on("error", reject);
      child.on("close", accept);
    });
    assert.equal(exitCode, 0);
    const data = JSON.parse(await readFile(path, "utf8"));
    assert.equal(data.reader_debt.summary.diagnosis, "high_risk");
    assert.deepEqual(data.reader_debt.summary.review_ids, ["D2"]);
    assert.equal(data.skill_candidates.summary.single_book_level_errors, 1);
    assert.equal(data.skill_candidates.summary.duplication_rate, 0.5);
    assert.equal(data.skill_candidates.summary.diagnosis, "high_risk");
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
