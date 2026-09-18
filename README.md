# 多平台内容流水线（multiplatform-content-pipeline）

> **项目类型**：多平台内容采集 + 知识库生成 + 文稿/视频创作
> **维护者**：AI自动维护 + 用户审核

## 项目目标

构建**多平台内容采集与知识库生成框架**，自动化采集各平台的视频和图文，经过转写/OCR/知识提取后形成结构化知识库，支持按行业生成文稿和视频，并支持方法提炼。

---

## 核心特性

1. **多平台采集**：平台插件化，新平台接入只需实现统一接口
2. **公共处理层**：转写（FunASR）、OCR（Vision）、知识提取，所有平台共用
3. **行业隔离**：股票、珠宝等行业有独立的知识库和模板
4. **方法提炼**：分析博主创作方法，提炼可复用的生成技巧
5. **增量采集**：水位（watermark）机制，只采集新内容

---

## 已接入平台

| 平台 | 状态 | 已采集量 |
|------|------|---------|
| 微信公众号 | ✅ 已接入 | 278篇文章 |
| 微信视频号 | ✅ 已接入 | 313短视频 + 23直播回放 |
| B站 | ✅ 已接入 | 743视频 + 202图文 |
| 抖音 | 🔧 待接入 | - |
| YouTube | 🔧 待接入 | - |

---

## 快速导航

| 文档 | 用途 |
|------|------|
| [AGENTS.md](AGENTS.md) | AI操作手册（命令式、可执行） |
| [docs/DOCUMENTATION_MAP.md](docs/DOCUMENTATION_MAP.md) | **文档地图**（所有文档的快速入口） |
| [docs/WORKFLOW.md](docs/WORKFLOW.md) | 整体工作流（四阶段流水线） |
| [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) | 项目需求与功能范围 |
| [docs/ROADMAP.md](docs/ROADMAP.md) | 项目长期规划 |
| [project-management/active/TASK_STATUS.md](project-management/active/TASK_STATUS.md) | 当前进度、下一步 |

---

## 项目结构概览

```
multiplatform-content-pipeline/
├── platforms/          # 采集层：平台插件
├── processing/         # 处理层：转写/OCR/知识提取
├── core/               # 核心框架：流水线编排+水位机制
├── domains/            # 行业层：股票/珠宝（隔离）
├── library/            # 数据层：原始资源+知识成品
├── docs/               # 工程文档
├── project-management/  # 项目治理
├── scripts/            # 运维脚本
└── workspace/          # 过程件（不入库）
```

> 详细目录结构见 [docs/DIRECTORY_STRUCTURE.md](docs/DIRECTORY_STRUCTURE.md)

---

## 快速开始

```bash
# 查看采集源配置
cat config/sources.json

# 运行增量采集（dry-run）
python3 scripts/incremental/fetch_new.py --all --dry-run
```

---

*详细说明见各专项文档，本README只保留概览。*
