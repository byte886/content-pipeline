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

## SOP（标准操作流程，guides/）

### 微信相关（按依赖顺序）

| 文件 | 用途 | 依赖 |
|------|------|------|
| [wechat-basic-operations.md](guides/wechat-basic-operations.md) | **微信基本操作**：窗口管理、搜索操作、鼠标控制最佳实践（所有微信采集的前置依赖） | 无 |
| [wechat-channels-capture.md](guides/wechat-channels-capture.md) | 视频号采集：捕获→下载→解密→验证（B方案首选） | 基本操作SOP |
| [wechat-official-article.md](guides/wechat-official-article.md) | 公众号文章采集与 OCR | 基本操作SOP |

### 通用

| 文件 | 用途 |
|------|------|
| [incremental-fetch.md](guides/incremental-fetch.md) | 增量采集：多平台内容更新发现与下载（通用框架） |
| [books-extraction.md](guides/books-extraction.md) | 电子资料采集与转码 |
| [audio-transcription.md](guides/audio-transcription.md) | FunASR 本地离线转文字：环境/批量脚本/输出/空稿判定 |

## 研究记录（research/）

| 文件 | 用途 |
|------|------|
| [video-quality-url.md](research/video-quality-url.md) | 视频号高质量 URL 参数与清晰度对比 |
| [wechat-channels-api.md](research/wechat-channels-api.md) | 视频号 XWEB/Pinia API 与 B方案 action 契约 |
| [wechat-short-video-decryption.md](research/wechat-short-video-decryption.md) | 短视频 Isaac64 流加密解密原理与验证 |

## 设计文档（design/）

| 文件 | 用途 |
|------|------|
| [knowledge-base-organization.md](design/knowledge-base-organization.md) | 知识库架构设计与内容规范 |
