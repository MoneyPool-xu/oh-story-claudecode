import assert from "node:assert/strict";
import { readFile, stat } from "node:fs/promises";
import { dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const repositoryRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const storySkillRoot = join(repositoryRoot, "skills", "story");

async function read(relativePath) {
  return readFile(join(repositoryRoot, relativePath), "utf8");
}

test("Claude Code marketplace exposes the canonical story skill bundle", async () => {
  const marketplace = JSON.parse(await read(".claude-plugin/marketplace.json"));
  const claudeStory = marketplace.plugins.find((plugin) => plugin.name === "story");

  assert.ok(claudeStory, "Claude Code marketplace must publish the story plugin");
  assert.deepEqual(claudeStory.skills, ["./skills/story"]);
  assert.match(claudeStory.description, /\/story dashboard/);

  for (const relativePath of [
    "SKILL.md",
    "scripts/dashboard-server.mjs",
    "assets/index.html",
    "assets/styles.css",
    "assets/app.js",
  ]) {
    const bundled = await stat(join(storySkillRoot, relativePath));
    assert.ok(bundled.isFile(), `${relativePath} must ship inside the canonical story skill`);
  }

  for (const relativePath of [
    "SKILL.md",
    "VERSION",
    "scripts/pipeline_monitor.py",
    "assets/index.html",
    "assets/styles.css",
    "assets/app.js",
  ]) {
    const bundled = await stat(join(repositoryRoot, "skills", "story-project-pipeline-monitor", relativePath));
    assert.ok(bundled.isFile(), `${relativePath} must ship inside the pipeline monitor skill`);
  }
});

test("standalone pipeline dashboard loads the stylesheet it ships", async () => {
  const html = await read("skills/story-project-pipeline-monitor/assets/index.html");
  assert.match(html, /href="\/styles\.css"/);
  assert.doesNotMatch(html, /href="\/pipeline\.css"/);
});
