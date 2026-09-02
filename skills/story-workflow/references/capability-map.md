# 能力与路由表

## 选择规则

| 目标 | 首选 skill | 最低输入 | 主要交付 | 不可用时 |
|---|---|---|---|---|
| 市场方向 | `story-long-scan` / `story-short-scan` | 平台、篇幅或题材 | 榜单与选题假设 | 使用用户已有数据，标明时效盲区 |
| 对标拆解 | `story-long-analyze` / `story-short-analyze` | 合法可读的原文 | 拆文报告、节点、手法 | 只分析已提供片段 |
| 环境部署 | `story-setup` | 项目目录、运行环境 | 项目规则、agents、hooks | 创建最小目录建议，不伪造部署 |
| 旧稿导入 | `story-import` | 已有正文 | 标准项目与逆向设定 | 先做只读结构盘点 |
| 长篇创作 | `story-long-write` | 项目或明确创作目标 | 大纲、正文、追踪事务 | 仅在聊天中给草案并说明未入库 |
| 短篇创作 | `story-short-write` | 题材、篇幅、目标 | 大纲、正文 | 仅在聊天中给草案 |
| 项目文风 | `story-prose-style` | 稳定样章或风格要求 | 文风规则、声纹、漂移报告 | 人工提取，不生成伪精确指标 |
| 自然成稿预防 | `story-natural-drafting` | 当前细纲、前章、追踪、文风/声纹、读者要求和相关拆文手法卡 | 当前有效的每章写作指令卡、场景重心、信息取舍、句群落点、背景禁写清单、人物能力/物件状态/概念重复/危险余波约束 | 写作 skill 按同一固定模板内联生成完整章卡并标记降级；缺卡仍不得开写 |
| 读者体验 | `story-reader-cold-read` | 发布态正文 | 盲读账本、弃读点 | 主线程严格隔离作者资料后执行 |
| 综合审查 | `story-review` | 正文；最好含设定/大纲 | 结构、人物、逻辑、一致性 findings | 使用 solo rubric 并标注降级 |
| 原创性 | `story-originality-audit` | 稿件和已知来源 | 来源映射、距离风险 | 只给来源登记与待比较计划 |
| 去 AI 味 | `story-deslop` | 待修正文 | 去模板化正文、Gate H 普通读者清楚度/真人因果修复与复检结果 | 主线程语义复核后直接修复，不机械替换 |
| 中文终校 | `story-chinese-proofreading` | 最终版正文/文案 | 明确语言错误与终校稿 | 保守人工校对 |
| 番茄门禁 | `story-fanqie-compliance` | 发布态文本、规则日期 | BLOCK/FIX/REVIEW/PASS | 标记规则未知，不给 PASS |
| 发布后诊断 | `story-serial-performance-diagnostics` | 指标定义、样本、时间窗 | 异常位置、假设、验证 | 生成采集模板，不编数据 |
| 全流程监测 | `story-project-pipeline-monitor` | 工作区、书目录 | 立项到投稿全步骤状态、失效传播、下一步与本地 Dashboard | 输出静态全流程状态表并标明无法实时刷新 |

## 常见最小链

- 开一本长篇：scan（可选）→ analyze（可选）→ setup → prose-style（有样章时）→ natural-drafting → long-write。
- 已有稿续写：setup → import → prose-style（有样章时）→ natural-drafting → long-write。
- 新章交付：natural-drafting → long-write → review → deslop → proofreading。
- 番茄发布前：review → originality（存在参考来源时必选）→ deslop → proofreading → fanqie-compliance。
- 追读下降：serial-performance-diagnostics → cold-read（定位章节）→ review → long-write revision → 受影响门禁重跑。
- 只查错字：proofreading；不要扩张为全流程审稿。

## 边界

- 工作流内所有确认成立且不改变正典的文本问题默认自动修复并复检；报告用于说明已改内容，不是等待用户逐项批准的待办单。
- `story-prose-style` 定义项目声音；`story-deslop` 清除模板痕迹，二者不能互相替代。
- `story-natural-drafting` 在动笔前生成并校验每章写作指令卡，控制重心、视角、留白、拆文写法迁移和清楚度；它不能替代写作 skill，也不能让写后 `story-deslop` 失去必要性。
- 章节指令卡必须全文交给写作模型，不能压缩成“长短句结合、写得自然”一类提示。拆文只迁移句群节奏、信息延迟、紧张升级和笔墨分配，不复制表达、专名、人物关系、罕见场景组合或节点顺序。
- 自然成稿允许省略作者解释和主题总结，不允许省略动作主体、即时目标、陌生词用途和当前危险；不得用含混、错字、乱标点伪装真人。
- `story-reader-cold-read` 第一遍不能读取作者资料；`story-review` 可以读取设定和大纲。
- `story-chinese-proofreading` 不改剧情；剧情修订交回写作 skill。
- `story-fanqie-compliance` 只覆盖其规则日期和受检文本，不代表官方审核。
- 编排 skill 不直接启动浏览器抓榜、写正文或改追踪，它只把任务交给对应能力。
