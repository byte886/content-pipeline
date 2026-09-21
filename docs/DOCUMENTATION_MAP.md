# 文档地图（DOCUMENTATION MAP）

> **文档类型**：Reference（参考资料 — 文档索引）
> **更新频率**：每次新增/删除/移动文档时

> 本文档是项目所有文档的导航入口，告诉AI和人"先读什么、去哪里找什么"。

---

## 快速入口（按场景）

### 开始新任务前
1. 先判冷启动还是续接，按 `AGENTS.md` 第2章读对应文档
2. 当前到哪/下一步：`project-management/active/TASK_STATUS.md` + `active/ISSUES.md`

### 微信基本操作（UI自动化）
1. `docs/guides/wechat-basic-operations.md` — 窗口管理、搜索操作、鼠标控制最佳实践

### 视频号内容采集
1. `docs/guides/wechat-channels-capture.md` — 采集流程（捕获→下载→解密→验证）
2. `docs/research/video-quality-url.md` — X-snsvideoflag参数、6种格式对比
3. `docs/research/wechat-channels-api.md` — 方案B API研究记录

### 公众号文章采集
1. `docs/guides/wechat-official-article.md` — 文章采集流程

### 增量采集
1. `docs/guides/incremental-fetch.md` — 多平台内容更新发现与下载

### 电子资料处理
1. `docs/guides/books-extraction.md` — PDF/PPTX等电子资料转码与精华提取

### 视频转文字 / 图文OCR
1. `docs/guides/audio-transcription.md` — FunASR 本地离线转写：环境搭建、批量脚本用法、输出目录、空稿判定
2. 批量转写脚本：`platforms/wechat_channels/video-transcribe/batch_transcribe.py`（模型只加载一次、断点续跑）
3. OCR工具：`processing/ocr/tools/batch_article_images.py`（macOS Vision）

### 知识提取与知识库
1. `docs/design/knowledge-base-organization.md` — 知识库架构设计+内容规范

### 遇到问题/异常
1. `grep -rn "关键词" docs/` — 搜索相关文档
2. `project-management/active/ISSUES.md` — 已知问题清单

---

## 文档完整清单

### 零、根目录标准文档（大写骨架）

| 文档 | 路径 | 用途 |
|------|------|------|
| 项目介绍 | `README.md` | 项目目标、存储分工、快速开始 |
| AI操作手册 | `AGENTS.md` | 全局执行规则、核心约束、常见问题 |
| 文档地图 | `docs/DOCUMENTATION_MAP.md` | 本文档 |
| 项目需求 | `docs/REQUIREMENTS.md` | 需求与功能范围 |
| 整体工作流 | `docs/WORKFLOW.md` | 四阶段流水线 + 各阶段校验门 |
| 目录结构 | `docs/DIRECTORY_STRUCTURE.md` | 存储分工、目录说明、命名规范 |
| 路线图 | `docs/ROADMAP.md` | 项目长期规划 |

### 一、操作指南（guides/ — 怎么做）

| 文档 | 路径 | 用途 |
|------|------|------|
| 微信基本操作SOP | `docs/guides/wechat-basic-operations.md` | 窗口管理、搜索操作、鼠标控制最佳实践 |
| 视频号采集SOP | `docs/guides/wechat-channels-capture.md` | 捕获→下载→解密→验证全流程 |
| 公众号采集SOP | `docs/guides/wechat-official-article.md` | 文章采集与OCR流程 |
| 增量采集SOP | `docs/guides/incremental-fetch.md` | 多平台内容更新发现与下载 |
| 电子资料转码SOP | `docs/guides/books-extraction.md` | PDF/PPTX等电子资料处理 |
| 视频转写SOP | `docs/guides/audio-transcription.md` | FunASR本地离线转文字：环境/批量脚本/输出/空稿判定 |

### 二、技术研究（research/ — 已验证的结论）

| 文档 | 路径 | 用途 |
|------|------|------|
| 高质量URL研究 | `docs/research/video-quality-url.md` | X-snsvideoflag参数研究 |
| 视频号API研究 | `docs/research/wechat-channels-api.md` | 方案B API研究记录 |

### 三、架构设计（design/ — 方案设计）

| 文档 | 路径 | 用途 |
|------|------|------|
| 知识库组织与规范 | `docs/design/knowledge-base-organization.md` | 知识库架构设计+内容规范+标签体系 |

### 四、项目治理

| 文档 | 路径 | 用途 |
|------|------|------|
| 任务状态 | `project-management/active/TASK_STATUS.md` | 当前进度、下一步（单一进度真相） |
| 问题清单 | `project-management/active/ISSUES.md` | 已知问题、阻塞项 |
| ADR决策 | `project-management/decisions/` | 架构决策记录（只增不改） |
| 工程记忆 | `project-management/memory/` | 跨会话稳定结论编译层 |

---

## 命名规范速查

| 类型 | 命名风格 | 示例 |
|------|---------|------|
| 固定名 | 原样 | README.md、AGENTS.md |
| 治理/规范/骨架 | 大写 UPPER_SNAKE_CASE | WORKFLOW.md、REQUIREMENTS.md、DOCUMENTATION_MAP.md |
| 方法/SOP/操作 | 小写 kebab-case | wechat-basic-operations.md、incremental-fetch.md |
| 脚本 | 小写 snake_case | baidu_upload.py |
| ADR | ADR-NNN-中文 | ADR-001-项目文档架构与治理规范.md |

---

*本文档随项目演进持续更新。新增文档时必须在此登记。*
