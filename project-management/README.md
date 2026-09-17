# Project Management — 项目治理体系

> 本目录是项目的**治理与过程管理层**，与 `docs/`（产品/技术文档）分离。
> 新会话启动时按 AGENTS.md 第2章路径读取本目录对应文件。

## 目录结构

```
project-management/
├── active/           # 活态台账（实时更新）
│   ├── TASK_STATUS.md    # 任务状态：当前做什么、到哪了、下一步
│   └── ISSUES.md         # 开放问题/缺陷清单
├── decisions/        # ADR 架构决策记录（只增不改）
│   ├── ADR-001 ~ ADR-004
│   └── ...
├── memory/           # 工程记忆 bundle（跨会话稳定结论编译层）
│   ├── index.md          # 记忆入口（新会话先读这个定位）
│   └── concepts/         # 各领域 concept（结论+相对指针，不复制正文）
├── reviews/          # 评审报告
│   ├── 2026-09-15-post-refactor-review.md
│   └── REVIEW-governance-summary.md
├── standards/        # 执行标准与规范
│   ├── BATCH_TASK_EXECUTION.md   # 批量任务执行规范
│   └── DOC_SYNC_CHECKLIST.md     # 文档同步检查清单
└── legacy/           # 历史项目文档（珠宝项目合并过来的，仅存档参考）
    └── jewelry-*.md
```

## 读取优先级

| 场景 | 先读 | 再读 |
|------|------|------|
| 新会话冷启动 | `memory/index.md` → `active/TASK_STATUS.md` | 对应 ADR / SOP |
| 续接任务 | `active/TASK_STATUS.md` → `active/ISSUES.md` | 该环节 SOP |
| 做重要决策前 | `decisions/` 查历史 ADR | 避免冲突后再写新 ADR |
| 大任务执行前 | `standards/BATCH_TASK_EXECUTION.md` | 创建执行状态记录 |
| 文档变更后 | `standards/DOC_SYNC_CHECKLIST.md` | 同步相关文档 |

## 维护原则

- **active/** 是唯一进度真相，实时更新，不抄明细
- **decisions/** 只增不改，被取代的决策在新 ADR 中说明
- **memory/** 只放稳定结论，易变值（进度、计数）不进记忆
- **legacy/** 只读存档，不修改、不引用为权威源
