# docs/ — 产品与技术文档

> 项目治理文档在 `../project-management/`，本目录只放产品需求、技术方案、SOP 和研究记录。

## 文档地图

完整文档索引见 [DOCUMENTATION_MAP.md](DOCUMENTATION_MAP.md)。

## 快速入口

| 类别 | 文件 | 说明 |
|------|------|------|
| **需求** | [REQUIREMENTS.md](REQUIREMENTS.md) | 项目目标、功能范围、验收标准 |
| **流程** | [WORKFLOW.md](WORKFLOW.md) | 端到端工作流概览（各环节链接到专项 SOP） |
| **路线图** | [ROADMAP.md](ROADMAP.md) | 里程碑与待办 |
| **目录结构** | [DIRECTORY_STRUCTURE.md](DIRECTORY_STRUCTURE.md) | 仓库目录说明 |
| **文档地图** | [DOCUMENTATION_MAP.md](DOCUMENTATION_MAP.md) | 全部文档索引与分工 |

## SOP（标准操作流程）

### 微信相关（按依赖顺序）

| 文件 | 用途 | 依赖 |
|------|------|------|
| [SOP-wechat-basic-operations.md](SOP-wechat-basic-operations.md) | **微信基本操作**：窗口管理、搜索操作、鼠标控制最佳实践（所有微信采集的前置依赖） | 无 |
| [SOP-wechat-channels-capture.md](SOP-wechat-channels-capture.md) | 视频号采集：捕获→下载→解密→验证 | 基本操作SOP |
| [SOP-wechat-official-article.md](SOP-wechat-official-article.md) | 公众号文章采集与 OCR | 基本操作SOP |

### 通用

| 文件 | 用途 |
|------|------|
| [SOP-incremental-fetch.md](SOP-incremental-fetch.md) | 增量采集：多平台内容更新发现与下载（通用框架） |
| [SOP-books-extraction.md](SOP-books-extraction.md) | 电子资料采集与转码 |

## 研究记录

| 文件 | 用途 |
|------|------|
| [RESEARCH-video-quality-url.md](RESEARCH-video-quality-url.md) | 视频号高质量 URL 参数研究 |
| [RESEARCH-wechat-channels-api.md](RESEARCH-wechat-channels-api.md) | 视频号 API 方案研究 |

## 设计文档

| 文件 | 用途 |
|------|------|
| [DESIGN-knowledge-base-organization.md](DESIGN-knowledge-base-organization.md) | 知识库架构设计与内容规范 |
