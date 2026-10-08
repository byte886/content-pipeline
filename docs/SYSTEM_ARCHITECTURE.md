# 体系运行机制与路由（SYSTEM ARCHITECTURE）· 薄指针

> **文档类型**：Governance（体系级运行规则）· 薄指针（自 2026-10-08 起）
> **维护者**：AI 自动维护 + 用户审核
> **读者**：AI 代理（跨体系任务路由必读）
> **定位**：本文件是"鉴藏（heritage）体系"的**运行机制层**（驱动/产物/路由），管"系统怎么转"；业务方向与选题策略在运营仓 `self-media-ops/docs/SYSTEM_STRATEGY.md`，管"往哪去"。

---

> **⚠️ 本文件自 2026-10-08 起降级为薄指针**：五仓体系总览 / 职责表 / 调度逻辑（产物驱动对接）/ 任务路由 / 跨仓纪律的**权威正文已迁移至五仓总控仓**，本仓不再单独维护分层表 / 对接表 / 路由表 / 纪律全文，避免双写漂移。历史全文（v1）归档见 `docs/archive/SYSTEM_ARCHITECTURE_v1_full_2026-10-08.md`。

## 1. 五仓分层速记（一行版）

| 层 | 仓库 | 一句话 |
|---|---|---|
| ① 采集底座 | `~/Desktop/multiplatform-content-pipeline`（本仓） | 知识从哪来：给渠道/博主即采集→转写→知识成品 |
| ② 调研方法论 | `~/Doubao/skills/web-research-toolkit` | 外部信息怎么查：行业包/渠道目录/分层路由 |
| ③ 情报雷达 | `~/Desktop/ai-intel-monitor` | 正在发生什么：定时扫描→情报速递（周/双周/月） |
| ④ 生产执行 | `~/Desktop/heritage-ai-video-sop` | 怎么做：接单即产→成片→门禁 G1-G5 |
| ⑤ 运营分发 | `~/Desktop/self-media-ops` | 怎么卖（方向）：人驱动定选题/优先级，不阻塞下游 |

## 2. 权威源指针（正文以此为准）

| 主题 | 权威位置 |
|---|---|
| 五仓总览 / 职责表 / 调度逻辑（产物驱动对接表） | 总控仓 `~/Desktop/multi-repo-orchestration/README.md` |
| 任务路由（接到任务先判断进哪个仓） | 总控仓 `~/Desktop/multi-repo-orchestration/README.md`（路由段） |
| 跨仓纪律（来源四档 / OKF / 建包顺序 / 子模块纪律 / 定时更新等） | 总控仓 `~/Desktop/multi-repo-orchestration/README.md`（纪律段） |
| 逐仓现状总表（各仓当前产物 / 目录 / 对接状态） | 总控仓 `~/Desktop/multi-repo-orchestration/docs/五层现状总表.md` |
| 本仓（①采集底座）内部工作流 | 本仓 `docs/WORKFLOW.md`（四阶段） |

> 详细机制正文以总控仓为准；本文件仅保留定位头注 + 五仓速记 + 指针，不再单独维护。如需查阅降级前的完整分层表 / 产物对接表 / 路由表 / 纪律全文，见归档文件 `docs/archive/SYSTEM_ARCHITECTURE_v1_full_2026-10-08.md`。
