# CHANGELOG（编年体 · 只增不改）

> 格式：`YYYY-MM-DD ［类型］一句话（+影响/依据）`；类型 = 新增/变更/修复/废弃/移除。倒序编年（最新在上）。
> 历史说明：本仓此前无根级 CHANGELOG，变更记录由 `docs/HANDOFF.md`（倒序活日志）承担；自 2026-10-08 起以本文件为根级显著变更台账（HANDOFF 偏接手上下文，职能不同）。

## 2026-10-09

- ［变更］仓库改名 `multiplatform-content-pipeline → content-pipeline`（用户拍板：原名过长；content-pipeline 为英文标准术语、砍掉 multiplatform 隐含属性、与体系 2 词命名风格统一）。GitHub rename + 本地目录 mv + remote set-url + 全链指针同步（含 we-media-ops 子模块 URL）。

## 2026-10-08

- ［变更］`docs/SYSTEM_ARCHITECTURE.md` 降级为薄指针：五仓体系总览 / 职责表 / 产物驱动对接 / 任务路由 / 跨仓纪律的权威正文迁移至五仓总控仓 `~/Desktop/system-architecture/`（`README.md` + `docs/五层现状总表.md`），本仓不再单独维护以避免双写漂移；降级前 v1 全文归档至 `docs/archive/SYSTEM_ARCHITECTURE_v1_full_2026-10-08.md`（头部注明归档日期/降级原因/新权威源路径）
- ［新增］根目录 `CHANGELOG.md`（本文件）：此前本仓无根级变更日志，由 `docs/HANDOFF.md` 倒序活日志替代，自今日起显著变更在本文件登记
- ［变更］`README.md` 快速导航表总控仓那行措辞微调：反映"体系架构正文以总控仓为准、本仓 SYSTEM_ARCHITECTURE.md 为薄指针"
- ［备注］既有 9 个未提交文件（本次**不代提交**，待该仓维护时处理）：
  - Modified：`AGENTS.md`、`docs/DOCUMENTATION_MAP.md`、`docs/WORKFLOW.md`、`domains/jewelry/README.md`、`platforms/douyin/README.md`
  - Untracked：`library/05_knowledge/jewelry/郭颖/`、`library/jewelry/`、`platforms/douyin/COLLECT_SOP.md`、`platforms/douyin/scripts/`
