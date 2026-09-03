import assert from "node:assert/strict";
import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const skillsRoot = path.join(root, "skills");

const expectedSkills = [
  "browser-cdp", "story", "story-chinese-proofreading", "story-cover",
  "story-deslop", "story-fanqie-compliance", "story-import", "story-long-analyze",
  "story-long-scan", "story-long-write", "story-natural-drafting",
  "story-originality-audit", "story-project-pipeline-monitor", "story-prose-style",
  "story-reader-cold-read", "story-review", "story-serial-performance-diagnostics",
  "story-setup", "story-short-analyze", "story-short-scan", "story-short-write",
  "story-workflow",
];

test("fork exposes the complete authoritative 22-skill bundle", async () => {
  const entries = await readdir(skillsRoot, { withFileTypes: true });
  const names = entries.filter((entry) => entry.isDirectory()).map((entry) => entry.name).sort();
  assert.deepEqual(names, expectedSkills);
  for (const name of names) {
    const source = await readFile(path.join(skillsRoot, name, "SKILL.md"), "utf8");
    assert.match(source, /^---\n[\s\S]*?^name:/m, `${name} has frontmatter`);
  }
});

test("natural drafting keeps the three merged anti-template rules", async () => {
  const source = await readFile(path.join(skillsRoot, "story-natural-drafting", "SKILL.md"), "utf8");
  assert.match(source, /并列三个以上结构相同的短语/);
  assert.match(source, /避开“两拍翻转”这个形状本身/);
  assert.match(source, /不直接命名情绪/);
});

test("workflow keeps the pipeline-monitor handoff", async () => {
  const workflow = await readFile(path.join(skillsRoot, "story-workflow", "SKILL.md"), "utf8");
  const capabilities = await readFile(path.join(skillsRoot, "story-workflow", "references", "capability-map.md"), "utf8");
  assert.match(workflow, /交给 `story-project-pipeline-monitor`/);
  assert.match(capabilities, /\| 全流程监测 \| `story-project-pipeline-monitor` \|/);
});

test("post-write style review is distinct from the prose baseline and gates deslop", async () => {
  const workflow = await readFile(path.join(skillsRoot, "story-workflow", "references", "post-write-gate.md"), "utf8");
  const pipeline = await readFile(path.join(skillsRoot, "story-project-pipeline-monitor", "scripts", "pipeline_monitor.py"), "utf8");
  assert.match(workflow, /story-prose-style` 做写后文风反向审核/);
  assert.match(pipeline, /\("style-review", "文风反向审核"/);
  assert.match(pipeline, /\("deslop"[\s\S]*\["style-review"\]\)/);
  assert.match(pipeline, /"style-review": \["报告\/文风\/\*\*\/\*反向审核\*\.md"/);
});

test("platform adaptation stays isolated from the universal prose kernel", async () => {
  const kernel = await readFile(path.join(skillsRoot, "story-long-write", "references", "narrative-kernel.md"), "utf8");
  const qimao = await readFile(path.join(skillsRoot, "story-long-write", "references", "platforms", "qimao-wireless.md"), "utf8");
  const review = await readFile(path.join(skillsRoot, "story-review", "references", "platforms", "qimao-signing-review.md"), "utf8");
  const extraction = await readFile(path.join(skillsRoot, "story-long-analyze", "references", "platform-pattern-extraction.md"), "utf8");
  assert.match(kernel, /platform_constraints/);
  assert.match(qimao, /Promise Visibility/);
  assert.match(review, /编辑第一眼[\s\S]*阅读动力[\s\S]*正文质量/);
  assert.match(extraction, /Platform Observation[\s\S]*Platform Pattern[\s\S]*Core Universal/);
  assert.doesNotMatch(kernel, /800 字|1500 字|男主撑腰/);
});

test("short fiction uses a bounded Fanqie layer and per-scene directive cards", async () => {
  const shortSkill = await readFile(path.join(skillsRoot, "story-short-write", "SKILL.md"), "utf8");
  const fanqie = await readFile(path.join(skillsRoot, "story-short-write", "references", "platforms", "fanqie-short-story.md"), "utf8");
  const drafting = await readFile(path.join(skillsRoot, "story-natural-drafting", "SKILL.md"), "utf8");
  const template = await readFile(path.join(skillsRoot, "story-natural-drafting", "references", "short-scene-directive-template.md"), "utf8");
  assert.doesNotMatch(shortSkill, /否则一律用「我」|占全文 30-40%|不允许连续 2 节无情绪变化/);
  assert.match(shortSkill, /场景价值门禁/);
  assert.match(fanqie, /诊断器，不是目标函数/);
  assert.match(fanqie, /不得冒充番茄官方要求/);
  assert.match(drafting, /short-scene-directive-template\.md/);
  assert.match(template, /第 NN 节写作指令卡/);
});
