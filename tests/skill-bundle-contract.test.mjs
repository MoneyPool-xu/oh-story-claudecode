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
