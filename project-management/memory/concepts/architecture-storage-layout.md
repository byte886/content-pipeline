---
concept: architecture-storage-layout
title: 四地存储分工与仓库版图
tags: [architecture, storage]
verified: machine
---

# 四地存储分工与仓库版图

## 结论

| 内容 | Git仓库 | 本地data | 百度网盘 | 飞书知识库 |
|------|:---:|:---:|:---:|:---:|
| 规范/模板/SOP/脚本/ADR | ✅ 唯一源 | — | — | — |
| 原始资源（视频/转写/文章JSON/图片） | ❌ 忽略 | ✅ | ✅ 备份 | ❌ |
| 知识成品（结构化知识点） | 部分入库 | ✅ | ✅ 备份 | ✅ 对外 |
| 加密凭证 | 见.gitignore | ✅ | ❌ | ❌ |

## 关键规则

1. **Git只放"怎么做"的工程资产**：代码、文档、脚本、配置
2. **视频/转写/图片等大文件不入Git**：.gitignore已忽略library/下的原料目录（01_video/02_audio/04_transcript/06_articles/07_books/08_sources）和workspace/过程件
3. **本地是唯一源头**：所有知识成品先在本地完成，再同步网盘/飞书
4. **过程件不入库**：临时文件、日志、缓存只在本地

## 来源与下钻

- 目录结构详情：`docs/DIRECTORY_STRUCTURE.md`
- .gitignore：项目根目录`.gitignore`
- 存储分工决策：`project-management/decisions/ADR-001-项目存储分工.md`
