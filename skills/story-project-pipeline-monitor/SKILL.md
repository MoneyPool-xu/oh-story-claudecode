---
name: story-project-pipeline-monitor
description: Monitor a Chinese web-fiction project from initial setup and market research through planning, drafting, post-write gates, cover preparation, submission checks, and submission records. Use when the user asks for a full novel workflow, project progress, stale checks after edits, the next required action, or a local OH STORY dashboard with reader-debt and Skill-candidate inflation diagnostics.
metadata: {"openclaw":{"source":"https://github.com/zenstory-ai/oh-story-claudecode"}}
---

# 网文全流程监测

把当前安装的 OH STORY 能力与质量门禁合并成一条可审计流程。不得仅凭“某文件存在”声称对应 skill 已运行；区分内容产物、技能报告和人工确认。

## 真源优先级

1. 扫描当前已安装 skill 根，优先使用实际安装版本：`~/.agents/skills`、`~/.codex/skills`。
2. 仓库能力使用当前 OH STORY 包内 `skills/` 中的文件，不依赖工作区外的个人目录。
3. 同名 skill 多份并存时，优先已安装且修改时间更新的副本，并在报告中列出来源；不要静默复制旧规则覆盖新版。
4. 详细阶段、依赖和证据标准读取 `references/pipeline.md`。
5. Stage 4/5 诊断以拆文产物 `_diagnostics.json` 为唯一事实源；Dashboard 与报告只展示其中的派生摘要，不自行估算分数。

## 每次执行

1. 先运行只读扫描：

   ```bash
   python3 scripts/pipeline_monitor.py status --workspace <工作区> --project <书目录>
   ```

   需要同时把本次快照保存到项目 `报告/工作流/` 时，才把 `status` 换成 `scan`。

2. 输出所有步骤，不隐藏未开始、条件步骤或阻塞步骤。
3. 每步必须包含：状态、依赖、负责 skill、证据、失效原因和下一动作。
4. 若项目中存在 `_diagnostics.json`，同时展示 Reader Debt Inflation 与 Skill Candidate Inflation；异常是复核信号，不是要求模型把数值修到目标区间。
5. 正文、简介、书名、设定、平台或报告输入版本变化时，按 `references/pipeline.md` 标记受影响节点为 `STALE`。
6. 状态只允许：`COMPLETED`、`IN_PROGRESS`、`NOT_STARTED`、`BLOCKED`、`STALE`、`CONDITIONAL`、`SKIPPED`。
7. 报告保存到 `{项目}/报告/工作流/`，保留旧报告。

## 强制写作闭环

每次新写、续写或修改正文必须执行：

`有效章卡 → story-long-write/story-short-write → story-review → story-deslop → story-chinese-proofreading → 触发条件成立时 story-reader-cold-read → 平台门禁`

任何步骤修改正文后，从最早受影响节点向后重跑。旧报告不得继续显示为完成，必须标记 `STALE`。

## Dashboard

优先检查当前 OH STORY Dashboard 的 `/pipeline.html`。若工作台已按本 skill 集成，直接返回：

```text
http://127.0.0.1:43110/pipeline.html
```

没有现成 OH STORY Dashboard、43110 端口空闲时，启动独立只读看板：

```bash
python3 scripts/pipeline_monitor.py serve --workspace <工作区> --project <书目录> --host 127.0.0.1 --port 43110
```

返回 `http://127.0.0.1:43110/`。只监听本机，不主动开放局域网或公网。服务应保持运行，用户可随时刷新查看文件变化后的最新状态。

需要人工登记无法自动识别的步骤时：

```bash
python3 scripts/pipeline_monitor.py mark --project <书目录> --step <步骤ID> --status COMPLETED --evidence <证据说明>
```

不得用人工标记掩盖版本失效；若正文修改时间晚于门禁证据，门禁仍显示 `STALE`。

## 交付

同时提供：

- 总进度与当前阶段；
- 全步骤状态表；
- 阻塞项和失效项；
- 下一步唯一优先动作；
- skill 来源与版本差异；
- Dashboard 地址。

只有投稿前全部必需节点为当前版本 `COMPLETED` 且无 `BLOCKED`/`STALE`，才能称为“投稿流程完成”。
