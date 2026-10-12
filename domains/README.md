# domains（行业域）— 行业方法论与知识库架构

> **文档类型**：Reference（参考资料 — 行业域导航）
> **更新频率**：行业域结构变更时
> **维护者**：AI 自动维护 + 用户审核

> **分工**：`domains/` = 行业方法论、知识库架构与建包纪律（设计/调研侧）；**知识成品**在 `library/05_knowledge/<行业>/`（数据层）。行业提取维度模板另见技能 `multiplatform-media-fetch/references/domain-plugins/`。

---

## 三域现状关系

| 域 | 状态 | 说明 |
|------|------|------|
| `jewelry` | **过渡保留** | 原珠宝域，已并入 `heritage/01_jewelry`（鉴藏总域，见本目录 `jewelry/README.md` 过渡说明）。目录保留用于过渡期导航；采集配置与知识库成品仍在 `library/05_knowledge/jewelry/`（765 篇 OKF 原子笔记口径），知识库架构在 `jewelry/knowledge_base/`。 |
| `stock` | **旧域（仍活跃，是否归档待用户拍板）** | 股票投资知识库（A 股为主，2026-09-11 建）：来源含顶底之王公众号 277 篇、交易的游戏视频号 340 短 + 29 回放、转写 369、知识提取 340（明细以 `stock/knowledge_base/README.md` 与 `library/00_manifest/` 台账为准）。采集与知识链路仍在持续使用；去留由用户拍板，本表在拍板前注明"仍活跃"。 |
| `heritage` | **鉴藏总域（当前主域）** | 鉴宝 + 收藏（appraisal & collection）知识总域，6 子域独立建包：01_jewelry（✅ 已有）/ 02_jadeite（✅ 调研技能已建）/ 03_antiques / 04_furniture / 05_eastern-heritage / 06_western-heritage（🔶 方法论已备待细建）。见 `heritage/README.md`。 |

## 维护纪律

1. 新行业域启用顺序：先建调研技能行业包（词库+查询模板）→ 再补监控仓渠道矩阵 → 最后 pipeline 采集配置（`heritage/README.md` 建包纪律）。
2. 域与成品分离：方法论与架构在 `domains/`，知识成品在 `library/05_knowledge/<行业>/`，不混放。
3. 过渡目录（如 `jewelry/`）保留时在 README 写明去向；不再活跃时由用户拍板归档并清导航。
