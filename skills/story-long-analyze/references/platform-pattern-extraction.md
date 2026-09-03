# Platform Pattern Extraction

本文件是 Stage 5 内的平台映射子层，不新增另一套 Stage 编号。它把单书机制映射到“特定平台 + 特定赛道”，不把单本爆款写法冒充平台铁律。

## 输入与输出

- 输入：Stage 3 事实索引、Stage 4 机制文件、Stage 5 已归并的 Observation，以及书目平台、赛道、样本日期。
- 输出：`提炼/平台规律.md`。平台或赛道未知时写“证据不足，未形成平台判断”，不得猜测。

每条记录包含：平台、赛道、样本日期、机制描述、功能解释、`evidence_books`、`evidence_refs`、反例、失效条件、当前等级和与 Core/Genre/Author 的关系。

## 升级规则

1. 单书只记 `Platform Observation`。
2. 至少 3 本不同作者、同平台、同赛道重复出现，且近义规则完成归并，才可升为 `Platform Pattern`。
3. 跨至少 2 个平台、2 个题材仍成立，才可提议进入 `Core Universal`；升级前仍需保留反例和失效条件。
4. “前三章连续高兑现”等频率只能先作为观察。必须解释它解决了什么读者问题，不能直接转成固定章数或字数公式。
5. 平台 Pattern 只供 Planner/Reviewer；Writer 只能接收为当前章编译后的短 `platform_constraints`，不能看到榜单统计、审稿术语和模板桥段。

跨书验证时复用各书已有 Stage 3–5 产物，不重读全书。平台样本应记录时间窗口；平台生态变化后旧结论降为待复核，不声称永久有效。
