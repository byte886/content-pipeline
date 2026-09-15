# 文档地图（DOCUMENTATION MAP）

> **文档类型**：Reference（参考资料 — 文档索引）
> **更新频率**：每次新增/删除/移动文档时
> **维护者**：AI自动维护
> **读者**：AI代理（快速定位文档）和人类（查找文档时）

> 本文档是项目所有文档的导航入口，告诉AI和人"先读什么、去哪里找什么"。

---

## 快速入口（按场景）

### 开始新任务前
1. 先判冷启动还是续接，按 `AGENTS.md` 第2章读对应文档
2. 当前到哪/下一步：`project-management/active/TASK_STATUS.md` + `active/ISSUES.md`
3. 跨会话稳定结论：`docs/project-management/memory/index.md`（按需沿concept下钻）

### 视频号内容采集
1. `docs/视频号内容采集SOP.md` — 采集流程（捕获→下载→解密→验证）
2. `docs/高质量URL研究.md` — X-snsvideoflag参数、6种格式对比
3. `docs/视频号API研究.md` — 方案B API研究记录
4. 工具：`tools/video-capture/`（MITM捕获）、`tools/video-downloader/`（下载+解密）

### 公众号文章采集
1. `docs/公众号文章采集SOP.md` — 文章采集流程
2. 工具：`scripts/article/`（待迁移到tools/）

### 视频转文字 / 图文OCR
1. 转写工具：`tools/transcription/batch_transcribe.py`（FunASR本地离线）
2. OCR工具：`tools/ocr/batch_article_images.py`（macOS Vision）
3. 输出：`data/transcripts/短视频/{视频名}/transcript.md`

### 知识提取与知识库
1. `docs/知识库组织方案.md` — 知识库架构设计
2. `docs/知识库规范.md` — 知识库内容规范
3. 工具：`tools/knowledge-extraction/`

### 遇到问题/异常
1. `grep -rn "关键词" docs/` — 搜索相关文档
2. `AGENTS.md` 第3章 — 证书与代理核心规则（多次踩坑）
3. `AGENTS.md` 第5章 — 常见问题
4. `project-management/active/ISSUES.md` — 已知问题清单

### 项目维护/文档更新
1. `docs/DIRECTORY_STRUCTURE.md` — 目录结构与存储分工
2. `docs/project-management/decisions/` — ADR架构决策记录（做重要决策前先查历史）
3. `docs/project-management/memory/` — 工程记忆（稳定结论变化时同步更新）

---

## 文档完整清单

### 零、根目录标准文档

| 文档 | 路径 | 用途 |
|------|------|------|
| 项目介绍 | `README.md` | 项目目标、存储分工、快速开始 |
| AI操作手册 | `AGENTS.md` | 全局执行规则、核心约束、常见问题 |
| 文档地图 | `docs/DOCUMENTATION_MAP.md` | 本文档 |
| 项目需求 | `docs/REQUIREMENTS.md` | 需求与决策溯源、已关闭方案留痕 |
| 整体工作流 | `docs/WORKFLOW.md` | 四阶段流水线 + 各阶段校验门 |
| 目录结构 | `docs/DIRECTORY_STRUCTURE.md` | 四地存储分工、目录说明 |

### 一、操作指南（SOP — 怎么做）

| 文档 | 路径 | 用途 |
|------|------|------|
| 视频号采集SOP | `docs/视频号内容采集SOP.md` | 捕获→下载→解密→验证全流程 |
| 公众号采集SOP | `docs/公众号文章采集SOP.md` | 文章采集与OCR流程 |
| 高质量URL研究 | `docs/高质量URL研究.md` | X-snsvideoflag参数研究 |
| 视频号API研究 | `docs/视频号API研究.md` | 方案B API研究记录 |

### 二、产品与规划（What & Why）

| 文档 | 路径 | 用途 |
|------|------|------|
| PRD | `docs/PRD.md` | 产品需求文档 |
| 技术方案 | `docs/技术方案.md` | 技术架构设计 |
| 执行计划 | `docs/执行计划.md` | 执行计划与里程碑 |
| 路线图 | `docs/ROADMAP.md` | 项目路线图与当前状态 |

### 三、知识库

| 文档 | 路径 | 用途 |
|------|------|------|
| 知识库组织方案 | `docs/知识库组织方案.md` | 知识库架构设计 |
| 知识库规范 | `docs/知识库规范.md` | 知识库内容规范 |

### 四、项目治理

| 文档 | 路径 | 用途 |
|------|------|------|
| 任务状态 | `project-management/active/TASK_STATUS.md` | 当前进度、下一步（单一进度真相） |
| 问题清单 | `project-management/active/ISSUES.md` | 已知问题、阻塞项 |
| ADR决策 | `docs/project-management/decisions/` | 架构决策记录（只增不改，3条） |
| 工程记忆 | `docs/project-management/memory/` | 跨会话稳定结论编译层 |
| 规范文档 | `docs/project-management/standards/` | 文档同步检查清单、批量任务执行规范 |
| 运行时工作区 | `data/_workspace/README.md` | 过程件管理规范（logs/tmp/capture） |

---

## 工具清单（快速索引）

> 完整说明见各工具目录的README或 `AGENTS.md` 第4章

| 任务 | 工具 | 位置 | 运行目录 |
|------|------|------|---------|
| 视频捕获(MITM) | video-capture | `tools/video-capture/` | tools/video-capture/ |
| 视频下载+解密 | batch_download_v4.py | `tools/video-downloader/` | 项目根目录 |
| 自动化采集 | auto_capture.py | `tools/auto-capture/` | 项目根目录 |
| 增量采集 | incremental_collect.py | `tools/auto-capture/` | 项目根目录 |
| 视频转文字 | batch_transcribe.py | `tools/transcription/` | 项目根目录 |
| 图文OCR | batch_article_images.py | `tools/ocr/` | 项目根目录 |
| 知识提取 | extract_knowledge.py | `tools/knowledge-extraction/` | 项目根目录 |
| 知识库查询 | knowledge_base.py | `tools/knowledge-extraction/` | 项目根目录 |
| 文章采集 | fetch_articles_*.py | `scripts/article/`（待迁移） | 项目根目录 |
| 网盘同步 | sync_stock.sh | `scripts/netdisk/` | 项目根目录 |

---

*本文档随项目演进持续更新。新增文档时必须在此登记。*
