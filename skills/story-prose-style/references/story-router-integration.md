# story 路由集成

以下能力已收编进 OH STORY fork。为让 `$story` 处理模糊意图时能稳定发现它们，主入口的路由表应保留：

```markdown
| 文风与角色声纹 | 按我的文风、统一文风、文风校准、对白说人话、文风漂移 | `$story-prose-style` |
| 读者盲读 | 读者视角、盲读、哪里看不懂、弃读点 | `$story-reader-cold-read` |
| 中文终校 | 校对、错别字、病句、标点、专名统一 | `$story-chinese-proofreading` |
| 原创性审计 | 洗稿、撞梗、抄袭自查、同人转原创、改编距离 | `$story-originality-audit` |
| 番茄发布合规 | 番茄审核、推荐被拒、发布前检查、平台规范、恶意水文 | `$story-fanqie-compliance` |
| 发布后复盘 | 掉量、追读下降、完读、章留、评论数据 | `$story-serial-performance-diagnostics` |
```

fork 更新可能调整主入口。每次更新和部署后：

1. 检查上述六行是否仍在路由表。
2. 缺失时在 fork 权威源修复，再重新部署；不要直接修改 `.agents`、`.claude` 或 `.codex` 副本。
3. 确认 fork 的 22 个 Skill 已完整部署到目标 Skill 根。
4. 重新打开任务，使技能清单和路由稳定刷新。

职责分工：

- `$story-prose-style`：建立、应用和校准项目文风。
- `$story-deslop`：清除AI痕迹，不负责定义项目文风。
- `$story-review`：审查结构、逻辑、人物和一致性。
- `$story-reader-cold-read`：隔离作者资料复原真实读者体验。
- `$story-chinese-proofreading`：做字词句、标点和专名终校。
- `$story-originality-audit`：逐来源审查表达与结构距离。
- `$story-fanqie-compliance`：执行番茄发布合规和反水文门禁。
- `$story-serial-performance-diagnostics`：分析发布后真实数据和反馈。

完整流水线、降级与交接协议由 `$story-workflow` 统一维护。
