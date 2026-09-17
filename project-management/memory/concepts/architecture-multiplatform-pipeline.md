---
concept: architecture-multiplatform-pipeline
title: 多平台内容流水线架构
type: Architecture
status: stable
verified: ai
last_updated: 2026-09-15
sources:
  - {id: ADR-004, resource: "../../decisions/ADR-004-架构重构为多平台内容流水线.md", title: "ADR-004: 架构重构为多平台内容流水线"}
  - {id: DIRECTORY_STRUCTURE, resource: "../../DIRECTORY_STRUCTURE.md", title: "目录结构详细说明"}
  - {id: README, resource: "../../../README.md", title: "项目概览"}
---

# 多平台内容流水线架构

## 核心结论

项目从"A股投资知识库"重构为"多平台内容流水线"（multiplatform-content-pipeline），采用五层架构，支持多平台采集、多行业隔离、方法提炼。

## 五层架构

```
① 来源层 platforms/     平台插件化，统一接口PlatformFetcher
② 加工层 processing/    公共SOP（转写/OCR/知识提取/方法提炼）
③ 原始层 library/01-08  按处理阶段编号，原料不入库
④ 知识层 05_knowledge/  OKF格式，清洗后成品才入库
⑤ 应用层 domains/       行业隔离（stock/jewelry）
```

## 关键设计

### 平台插件化
- 统一接口：`platforms/base.py` 的 `PlatformFetcher` 抽象基类
- 已接入：wechat_official、wechat_channels
- 待接入：bilibili（复用珠宝项目）、douyin、youtube（复用multiplatform-media-fetch）
- 新平台接入只需实现接口，主流程无需修改

### 行业隔离
- `domains/stock/`、`domains/jewelry/` 各有独立知识库/文章撰写/审稿
- 配置驱动：`config/sources.json` 管理平台→账号→行业映射

### 方法提炼（MethodNote）
- 新增维度：分析博主拍摄技巧、AI使用、内容呈现，提炼可复用生成方法
- 位置：`processing/method_extraction/method_extractor.py`
- 输出：`library/05_knowledge/concepts/methods/`
- 目的：不是进入该行业，而是抄袭风格和生成视频

### 数据层编号目录
- 参考珠宝项目成熟架构：library/00_manifest, 01_video, 02_audio, 04_transcript, 05_knowledge, 06_articles, 07_books, 08_sources
- 原料（01/02/04/06/07）不入库，成品（05的stable）才入库

### 增量水位机制
- `core/watermark.py`，参考珠宝项目设计
- 先成功落地、再推进水位（at-least-once）

## 迁移状态

| 阶段 | 内容 | 状态 |
|------|------|:---:|
| 阶段1 | 改名+新目录结构+代码迁移+文档更新 | ✅ 完成（commit bd45204） |
| 阶段2 | 数据迁移到library/新结构 | 待开始 |
| 阶段3 | 接入B站采集 | 待开始 |
| 阶段4 | 接入抖音/YouTube | 待开始 |

## 与旧架构的关键差异

| 维度 | 旧架构 | 新架构 |
|------|--------|--------|
| 项目名 | stock-knowledge-base | multiplatform-content-pipeline |
| 采集层 | tools/（按功能分） | platforms/（按平台分，插件化） |
| 处理层 | 散落在tools/ | processing/（公共SOP） |
| 数据层 | data/ + knowledge-base/ | library/00-08编号 |
| 行业层 | 无 | domains/（隔离） |
| 方法提炼 | 无 | processing/method_extraction/ |
| 配置 | 硬编码 | config/sources.json |

## 来源与下钻

- 完整决策背景与迁移策略 → ADR-004
- 目录结构详细说明与旧数据迁移计划 → DIRECTORY_STRUCTURE.md
- 平台接口定义 → platforms/base.py
- 流水线编排 → core/pipeline.py
