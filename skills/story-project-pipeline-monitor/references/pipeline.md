# 从新立项到投稿的标准流程

## 状态证据原则

- `COMPLETED`：存在可定位产物，或存在绑定当前输入版本的技能报告。
- `IN_PROGRESS`：已有部分产物，但本阶段必要组成不全。
- `NOT_STARTED`：无可信证据。
- `BLOCKED`：前置依赖未完成，或当前报告含阻断项。
- `STALE`：曾完成，但输入正文、设定、简介、书名、平台或规则后来变化。
- `CONDITIONAL`：只有使用对标来源、准备特定平台发布、已有真实连载数据等条件成立才运行。
- `SKIPPED`：用户明确决定跳过，必须保存理由；不能等同完成。

## 全流程

| 阶段 | ID | 步骤 | 负责能力 | 完成证据 |
|---|---|---|---|---|
| 环境 | setup | 部署写作环境 | 最新 `story-setup` | `.story-deployed` 且版本/目标端可读 |
| 市场 | market-scan | 目标平台扫榜 | `story-long-scan` / `story-short-scan` | 当前平台扫榜报告及数据日期 |
| 市场 | benchmark-analysis | 对标作品拆解 | `story-long-analyze` / `story-short-analyze` | 拆文报告、节点与手法产物 |
| 立项 | positioning | 平台、题材、受众、篇幅定位 | 写作 skill Phase 1 | 书名与定位/立项文件 |
| 立项 | premise | 核心卖点与读者承诺 | 写作 skill Phase 1 | 一句话卖点、核心冲突、差异点 |
| 设定 | characters | 主配角与关系 | 写作 skill Phase 2 | 人物设定与声纹 |
| 设定 | world | 世界观、金手指与边界 | 写作 skill Phase 2 | 世界观/能力代价文件 |
| 大纲 | outline | 总纲、分卷、主线 | `story-long-write` / `story-short-write` | 可执行大纲 |
| 大纲 | golden-three | 黄金三章细纲 | 写作 skill Phase 3 | 第1—3章逐章任务与钩子 |
| 物料 | title-synopsis | 书名、简介、标签 | 写作 skill + cold-read | 发布态书名与简介；简介冷读有效 |
| 文风 | prose-style | 项目文风与角色声纹 | `story-prose-style` | 文风规则或稳定样章分析 |
| 写前 | platform-rules | 平台规则前置 | `story-fanqie-compliance` / `story-review` 七猫平台层 | 目标平台的风险边界已落成本书写作边界文件（`参考资料/*平台*规范*.md`） |
| 写前 | voiceprint | 角色声纹卡 | `story-prose-style` | 逐角色的说话目的、句法、回避方式与禁写项（`设定/*声纹*.md`） |
| 写前 | source-inventory | 原创性来源清单 | `story-originality-audit` 建立来源清单 | 对标、素材、真实事件与生成过程已登记（`参考资料/*来源清单*.md`）；使用对标来源时必需，否则条件项 |
| 写前 | chapter-directive | 当前章自然成稿指令卡 | `story-natural-drafting` | 当前输入版本的完整章卡；依赖 platform-rules 与 voiceprint |
| 写作 | drafting | 正文写作/改稿 | 最新 `story-long-write` / `story-short-write` | 正文文件与追踪事务 |
| 写作 | tracking | 人物、时间线、伏笔同步 | 写作/review tracking transaction | 追踪检查通过 |
| 写后 | review | 综合审查 | 最新 `story-review` | 当前正文版本 review 报告无阻断项 |
| 写后 | deslop | 去AI味与 Gate H | 最新 `story-deslop` | 当前正文版本报告与复扫结果 |
| 写后 | proofreading | 中文终校 | `story-chinese-proofreading` | 当前正文版本终校报告 |
| 读者 | cold-read | 隔离冷读 | `story-reader-cold-read` | 当前发布态正文冷读报告 |
| 来源 | originality | 原创性审计 | `story-originality-audit` | 使用对标/改编来源时必需；否则条件项 |
| 平台 | compliance | 平台规则门禁 | 对应平台规则 skill | 有当前规则日期的门禁报告；无专用规则时不得伪造 PASS |
| 物料 | cover | 封面 | 最新 `story-cover` | 平台尺寸封面和质量复核 |
| 投稿 | submission-package | 投稿包 | 工作流编排 | 书名、简介、封面、作者信息、正文范围、标签齐全 |
| 投稿 | final-gate | 投稿前总门禁 | 本 skill | 所有必需节点当前有效，无 BLOCKED/STALE |
| 投稿 | submitted | 投稿与回执 | 人工记录 | 平台、时间、版本、回执/状态记录 |
| 反馈 | editor-feedback | 编辑退稿反馈复盘 | `story-review` 反馈闭环 | 原话、被投版本、复现证据与项目级规则；无反馈时为条件项 |

## 失效传播

- 正文任意改写：`review`、`deslop`、`proofreading` 失效；若改变读者信息、场景顺序、钩子或事实，`cold-read` 也失效。
- 书名、简介、标签改变：`title-synopsis` 的冷读、终校和平台门禁失效。
- 设定、动机、事实或伏笔改变：章卡、正文审查、追踪、冷读及全部后置门禁失效。
- 平台改变：定位、简介标签、封面尺寸、平台合规、投稿包和最终门禁失效。
- 对标来源改变：原创性审计失效；若影响正文，所有正文后置门禁同时失效。
- 平台规则更新：只令对应平台门禁、最终门禁失效。

## 投稿完成条件

必需完成：`setup`、`positioning`、`premise`、`characters`、`world`、`outline`、`golden-three`、`title-synopsis`、`prose-style`、`platform-rules`、`voiceprint`、`chapter-directive`、`drafting`、`tracking`、`review`、`deslop`、`proofreading`、`cold-read`、`cover`、`submission-package`、`final-gate`。

条件完成：存在参考来源时 `originality` 与 `source-inventory` 必需；目标平台有专用门禁且准备发布时 `compliance` 必需。`submitted` 只能由实际投稿记录或用户确认完成；`editor-feedback` 仅在收到真实编辑反馈时运行，单次反馈不得自动升级全局规则。

## 写前步骤不按正文时间失效

`platform-rules`、`voiceprint`、`source-inventory` 与 `chapter-directive` 都在正文之前建立，**不纳入 GATE_IDS**，不会因为正文比它们新而自动判 `STALE`。它们的失效由输入变化触发：目标平台变更令 `platform-rules` 失效，角色增删或文风改写令 `voiceprint` 失效，新增对标或素材令 `source-inventory` 失效。

## 扫描根与部署标记

`.story-deployed` 从扫描根**向上查找到 workspace 为止**。oh-story 标准结构是两层（项目根放部署标记，书目录放 `设定/大纲/正文/追踪`），因此扫描根指向书目录时仍能识别部署。标记内的 `target_cli`（`claude` / `codex` / `opencode` 等）只作信息展示，不影响是否已部署的判定。
