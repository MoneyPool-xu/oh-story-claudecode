---
name: story-workflow
description: 编排中文网络小说从选题、拆文、立项、写前自然成稿预防、正文写作、审查、去AI味、校对、原创性检查、平台发布到连载数据复盘的跨 skill 工作流，自动识别 OH STORY 项目阶段，选择最小必要能力链，生成标准交接单，并在正文、设定或平台目标变化后判断哪些检查失效、哪些必须重跑。用户提到全流程、下一步做什么、从开书到发布、发布前整套检查、多项检查一起做、返工后重检或工作流状态时使用。
metadata: {"openclaw":{"source":"https://github.com/zenstory-ai/oh-story-claudecode"}}
---

# story-workflow：网文全流程编排

编排任务，不取代具体能力。把写作、审查和发布变成可恢复的有向流程；默认运行最小必要链，不因“全流程”机械调用所有 skill。

## 识别目标与项目

1. 先解析用户点名的书、文件、章节、平台和交付目标。
2. 项目内优先读取 `.active-book`、`.story-deployed`、正文、大纲、设定、追踪和现有报告；独立稿件不自动绑定当前活跃书。
3. 区分四种目标：创作、专项诊断、发布前门禁、发布后复盘。目标不清但可从文件状态判断时继续，并显式写出假设。
4. 不为已完成且仍有效的步骤重复劳动；不把报告存在等同于检查有效。

需要完整路由和输入条件时读取 `references/capability-map.md`；需要确定失效范围时读取 `references/invalidation-rules.md`；本轮涉及新写、续写或重写正文时读取 `references/post-write-gate.md`，先做写前自然成稿预防，再执行写后门禁。

## 建立最小工作流

按依赖选择步骤：

1. **市场与来源**：`story-long-scan` / `story-short-scan` → `story-long-analyze` / `story-short-analyze`。
2. **项目准备**：`story-setup` / `story-import`。
3. **自然成稿与正文**：`story-prose-style`（有样章或项目文风要求时）→ `story-natural-drafting` 生成并校验每章写作指令卡 → 将完整指令卡交给 `story-long-write` / `story-short-write`。自然成稿 skill 是写作的前置与伴随层，不单独改正典；没有当前有效的指令卡，不得启动正文生成。
4. **读者体验**：`story-reader-cold-read`。
5. **内容质量**：`story-review` → `story-originality-audit` → `story-deslop`。
6. **发布门禁**：`story-chinese-proofreading` → `story-fanqie-compliance`；非番茄平台不得冒用番茄规则。
7. **发布后学习**：`story-serial-performance-diagnostics` → 对应写作 skill 的修订流程。

只保留实现本轮目标所需的节点。例如“终校第 20 章”通常只需校对；“番茄发布前整套检查”才需要内容审查、原创性、去AI味、终校和番茄门禁。若所需 skill 未安装，标记 `UNAVAILABLE`，使用能力表中的降级方案，不伪造调用成功。

## 执行与停靠

1. 先输出一行工作流：`目标 → 步骤 → 交付物`，然后执行第一个可运行节点。
2. 遇到会改变题材、核心设定、主要人物动机、结局、发布平台或覆盖大量正文的选择时停下，请用户决定。
3. 新写、续写或重写正文时，先由 `story-natural-drafting` 读取当前细纲、前章、追踪、文风、角色声纹及本章相关拆文手法，生成固定格式的《第XXX章自然成稿指令卡》，完成版本与必填字段校验，再把整张卡交给写作 skill；不要先批量生成模板稿再只做词语替换。缺卡、卡片过期、占位符未替换或只给写作模型一句风格摘要时，结果记为 `BLOCK`。
4. 对可编辑稿件默认采用“检测即修复”：各节点确认成立的对白活人感、文风、AI模板、错别字、病句、标点、格式、平台表达和明确连续性问题，直接进入对应写作或修订 skill 修改，不等待用户逐项确认。
5. 每次修改后自动重跑本节点及被修改失效的后续节点，直到阻塞项清零；不得把能够安全修复的问题只写进报告交给用户处理。
6. 脚本候选必须语义复核，误报和有明确功能的写法保留；不得为了“自动修复”机械替换或改坏人物声纹。
7. 只有修改会改变题材、核心设定、主要人物动机、人物关系、伏笔答案、结局、发布平台，或数据证据只支持多个相互冲突的假设时才停下请用户裁决。
8. 事实、人物状态、伏笔和章节顺序的修改交给 `story-long-write` / `story-short-write` 并提交相应追踪事务；不要直接手改派生追踪文件。
9. 跨节点传递标准交接单，不让下游从散乱聊天记录猜测。

## 标准交接单

每完成一个节点，输出并在项目允许时保存：

```markdown
## Workflow handoff
- Book / scope:
- Goal / platform:
- Input version: 文件路径 + 修改时间或提交标识
- Chapter directive: 路径 + CURRENT | STALE | BLOCK
- Completed step:
- Result: PASS | FIX | BLOCK | NEEDS-DATA | UNAVAILABLE
- Evidence:
- Changed files:
- Open findings:
- Invalidated checks:
- Next recommended skill:
- Next input:
```

报告默认保存到书目录 `报告/工作流/`；目录不存在且用户只要聊天结果时不强行创建。文件名使用 `YYYY-MM-DD-HHmm-{step}.md`，不覆盖旧报告。

## 维护工作流状态

需要查看“从新立项到投稿”的全部步骤、已完成/未完成/阻塞/失效状态，或启动本地流程看板时，交给 `story-project-pipeline-monitor`。本 skill 继续负责本轮最小必要链的编排；monitor 负责跨轮全局状态、证据与 Dashboard，不得用目录存在替代当前版本门禁。

当项目适合持续连载时，可创建或更新 `报告/工作流/state.json`。它只记录编排状态，不成为剧情事实权威：

```json
{
  "schema_version": 1,
  "book": "",
  "target_platform": "",
  "input_version": "",
  "checks": {
    "story-review": {"status": "PASS", "input_version": "", "report": ""}
  }
}
```

更新前读取现有状态并保留未知字段。正文或设定变化后只把受影响检查标为 `STALE`，不删除历史报告，不声称旧报告从未有效。

## 完成条件

交付时同时说明：已完成节点、仍开放的问题、因材料不足未运行的节点、已失效检查和下一步。发布前只有所有必需门禁均为当前版本的 `PASS`，且不存在 `BLOCK`，才能称为“本工作流通过”；不得承诺平台一定过审、签约或获得推荐。
