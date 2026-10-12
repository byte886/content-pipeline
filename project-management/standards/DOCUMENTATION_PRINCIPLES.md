# 文档治理操作规范（DOCUMENTATION_PRINCIPLES）

> **文档类型**：Standard（规范 — 文档设计与组织）
> **维护者**：AI自动维护 + 用户审核
> **读者**：AI代理 + 人类（写任何文档前必读）
> **关联**：顶层架构决策见 `decisions/ADR-001-项目文档架构与治理规范.md`；本文档是其**操作级落地**（ADR-001 只增不改，操作细则放这里）

> **一句话**：新内容先判类型，再落位，README 只留指针——**禁止把正文塞进 README**。

---

## 1. 文档类型词典（先认识 8 类）

| # | 类型 | 放哪 | 内容 | 何时建 |
|---|------|------|------|--------|
| 1 | **导航/概览** | 各级 `README.md`、`docs/DOCUMENTATION_MAP.md` | 只放指针：去哪找、先读谁；不超过一屏的说明 | 目录建立时 |
| 2 | **决策记录 ADR** | `project-management/decisions/ADR-NNN-*.md` | 为什么这么定：背景/决策/后果/演进注记。**只增不改** | 重要决策拍板时 |
| 3 | **规范 Standard** | `project-management/standards/*.md` | 必须遵循的操作规则（批量执行/文档同步/文档治理…） | 规则成文时 |
| 4 | **SOP/执行** | `docs/guides/`、`docs/workflow/`、技能 references | 怎么做：单点操作 / 端到端流程 / 决策门 | 流程要可复用时 |
| 5 | **设计 Design** | `docs/design/` | 方案设计：架构、结构、权衡（含"为什么选这个方案"） | 方案定稿前 |
| 6 | **研究 Research** | `docs/research/`、技能 references/research | 已验证结论 + 来源；区分"已查证/一方称/待核" | 调研出结论时 |
| 7 | **台账/动态** | `project-management/active/` | 实时状态：TASK_STATUS / ISSUES / 批次计划 | 任务进行中 |
| 8 | **工程记忆** | `project-management/memory/` | 跨会话稳定结论（编译层）：只放结论+指针，不复制原文 | 结论稳定后 |

> 分不清时问自己：**"这内容是'为什么'（决策）、'怎么做'（SOP/规范）、'现状'（台账）、还是'在哪找'（导航）？"**

---

## 2. 新增内容落位决策表（写任何新内容前查这张表）

| 你手头的新内容 | 落位（禁止） | 落位（正确） | 附带动作 |
|---|---|---|---|
| 一个设计决定（如"文稿分四型"） | ❌ 写进 README / 只写进执行文档 | ✅ 新建 ADR + 执行文档引用 | 执行文档加"决策见 ADR-NNN"指针 |
| 一段操作流程 | ❌ 塞进 README / 新建独立 md 乱放 | ✅ `docs/guides/` 或 `docs/workflow/`（按主流程/SOP） | README/DOCUMENTATION_MAP 加一行指针 |
| 一条规则（必须遵守） | ❌ 写在对话里 / 塞 ADR 正文 | ✅ `project-management/standards/` | 关联文档引用 |
| 一段探索结论/调研 | ❌ 丢进 library 成品 | ✅ `docs/research/` 或技能 research（带来源/分级） | 结论稳定后编译进 memory |
| 一个待办/进度 | ❌ 写在规划文档正文里不更新 | ✅ `project-management/active/TASK_STATUS.md` | 完成后回写 |
| 一条 README 补充说明 | ❌ 直接扩写 README 正文 | ✅ 判断内容类型 → 落对应文档 → README 只加指针 | README 保持导航 |

---

## 3. README 防则（本规范最重要的三条）

1. **README 只导航，不承载正文**：正文（决策/流程/规则/结论）一律落对应类型文档，README 只写"去哪找、先读谁"。
2. **层 README 是例外但不是借口**：子目录/知识库层的 README 可以写"该层放什么 + 维护规则"（这是导航性说明），但**不得**展开正文细节（决策理由、完整步骤、结论论证）。
3. **每次改完检查**：新增/改文档后必须同步 `docs/DOCUMENTATION_MAP.md`；README 出现"正文化"倾向（超过导航需要的细节）时，立即拆到对应类型文档。

---

## 4. 更新流程（文档变更后必走）

1. 定位类型 → 按 §2 落位；
2. 更新 `docs/DOCUMENTATION_MAP.md`（新增/移动/删除必须登记）；
3. 若涉及决策，检查 `decisions/` 是否需新建 ADR 或演进注记；
4. 提交前跑 `python3 scripts/doc_health_check.py`，0 ERROR 才提交；
5. 提交信息按 `docs/CHANGELOG.md` 约定写。

---

## 5. 与本仓库其他规范的关系

| 文档 | 关系 |
|---|---|
| `decisions/ADR-001` | 顶层架构决策（分层/五原则）——本文档是其操作细则 |
| `standards/BATCH_TASK_EXECUTION.md` | 批量任务执行时的状态记录规范（与本文档互补） |
| `standards/DOC_SYNC_CHECKLIST.md` | 文档同步检查清单（本文档 §4 是其源头） |
| `docs/DIRECTORY_STRUCTURE.md` | 目录结构说明（本文档讲"内容往哪放"，它讲"目录里有什么"） |

---

*变更记录：2026-10-12 初建（由"文稿分型误入 README"事件驱动，见 ADR-006 背景）。*
