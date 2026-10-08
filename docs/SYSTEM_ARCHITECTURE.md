# 采集流水线运行机制（SYSTEM ARCHITECTURE）· 薄指针

> **文档类型**：Governance（本仓运行规则）· 薄指针（自 2026-10-08 起）
> **维护者**：AI 自动维护 + 用户审核
> **读者**：AI 代理（本仓任务路由必读）
> **定位**：本文件描述本仓（content-pipeline，采集底座）的运行机制与内部工作流。

---

> **⚠️ 跨仓体系关系（五仓分层/职责表/任务路由/跨仓纪律）的权威正文在总控仓 `~/Desktop/control-tower/`（README.md + docs/五层现状总表.md）**，本仓不再单独维护分层表 / 对接表 / 路由表 / 纪律全文，避免双写漂移。历史全文（v1）归档见 `docs/archive/SYSTEM_ARCHITECTURE_v1_full_2026-10-08.md`。

## 本仓工作流（正文以此为准）

| 主题 | 权威位置 |
|---|---|
| 本仓（①采集底座）内部工作流 | 本仓 `docs/WORKFLOW.md`（四阶段：采集→处理→提取→交付） |
| 本仓目录结构与存储分工 | 本仓 `docs/DIRECTORY_STRUCTURE.md` |
| 本仓需求与功能范围 | 本仓 `docs/REQUIREMENTS.md` |
| 本仓长期规划 | 本仓 `docs/ROADMAP.md` |

> 本文件仅保留本仓定位头注 + 内部工作流指针，不再维护任何跨仓分层/路由/纪律正文。如需查阅降级前的完整分层表 / 产物对接表 / 路由表 / 纪律全文，见归档文件 `docs/archive/SYSTEM_ARCHITECTURE_v1_full_2026-10-08.md`。
