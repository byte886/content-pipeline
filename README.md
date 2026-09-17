# 多平台内容流水线（multiplatform-content-pipeline）

> **项目类型**：多平台内容采集 + 知识库生成 + 文稿/视频创作
> **创建时间**：2026-09-11
> **架构重构**：2026-09-15（从微信生态专用项目重构为多平台通用框架）
> **维护者**：AI自动维护 + 用户审核

## 项目目标

构建**多平台内容采集与知识库生成框架**，自动化采集各平台（微信公众号/视频号/B站/抖音/YouTube）的视频和图文，经过转写/OCR/知识提取后形成结构化知识库，并支持按行业（股票/珠宝等）生成文稿和视频。

### 核心能力

1. **多平台采集**：平台插件化，新平台接入只需实现接口
2. **公共处理层**：转写（FunASR）、OCR（Vision）、知识提取，所有平台共用
3. **行业隔离**：股票、珠宝等行业有独立的知识库、文章撰写模板、审稿规则
4. **方法提炼**：分析博主的拍摄技巧、AI使用、内容呈现，提炼可复用的生成方法
5. **增量采集**：水位（watermark）机制，只采集新内容

## 已接入平台

| 平台 | 状态 | 采集方式 | 已采集量 |
|------|------|----------|----------|
| 微信公众号 | ✅ 已接入 | 微信数据库读取 | 277篇文章 |
| 微信视频号 | ✅ 已接入 | MITM代理捕获+解密 | 313短视频+23回放 |
| B站 | ✅ 已接入 | wbi签名+合集采集（从珠宝项目合并） | 743视频+202图文 |
| 抖音 | 🔧 待接入 | yt-dlp（复用multiplatform-media-fetch） | - |
| YouTube | 🔧 待接入 | yt-dlp | - |

## 行业配置

| 行业 | 采集源 | 知识库 | 文章撰写 | 审稿 |
|------|--------|--------|----------|------|
| 股票投资 | 顶底之王（公众号）+ 交易的游戏（视频号） | ✅ 340篇 | ✅ | ✅ |
| 珠宝 | 宝石学家老许（B站UID:1841256325）+ 生财有术珠宝社区 | ✅ 777篇 | ✅ | ✅ |

## 快速导航（AI和人都先看这里）

| 文档 | 用途 |
|------|------|
| [AGENTS.md](AGENTS.md) | AI操作手册（命令式、可执行） |
| [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) | 项目需求与决策溯源 |
| [docs/WORKFLOW.md](docs/WORKFLOW.md) | 整体工作流（五层架构流水线） |
| [docs/DOCUMENTATION_MAP.md](docs/DOCUMENTATION_MAP.md) | **文档地图**（所有文档的快速入口） |
| [docs/DIRECTORY_STRUCTURE.md](docs/DIRECTORY_STRUCTURE.md) | 目录结构与存储分工 |
| [project-management/active/TASK_STATUS.md](project-management/active/TASK_STATUS.md) | 当前进度、下一步 |
| [project-management/active/ISSUES.md](project-management/active/ISSUES.md) | 已知问题、阻塞项 |
| [docs/ROADMAP.md](docs/ROADMAP.md) | 项目路线图 |

## 项目结构

```
multiplatform-content-pipeline/
├── README.md                          # 项目概览（本文档）
├── AGENTS.md                          # AI操作手册
├── config/
│   └── sources.json                   # 采集源配置（平台→账号→行业映射）
├── platforms/                         # 采集层：平台插件
│   ├── base.py                        # 统一接口（PlatformFetcher）
│   ├── wechat_official/               # 公众号采集
│   │   └── article/                   # 文章采集脚本
│   ├── wechat_channels/               # 视频号采集
│   │   ├── video-capture/             # MITM代理捕获工具
│   │   ├── video-downloader/          # 下载+解密
│   │   └── auto-capture/              # 自动化采集
│   ├── bilibili/                      # B站采集（待接入）
│   ├── douyin/                        # 抖音采集（待接入）
│   └── youtube/                       # YouTube采集（待接入）
├── processing/                        # 处理层：公共SOP
│   ├── transcription/                 # FunASR转写
│   ├── ocr/                           # Vision OCR
│   ├── knowledge_extraction/          # 知识提取
│   ├── method_extraction/             # 方法提炼（拍摄技巧/AI使用/风格）
│   └── normalization/                 # 内容标准化/去重
├── core/                              # 核心框架
│   ├── pipeline.py                    # 流水线编排
│   ├── config.py                      # 配置管理
│   └── watermark.py                   # 增量水位机制
├── domains/                           # 行业层（隔离）
│   ├── stock/                         # 股票行业
│   │   ├── knowledge_base/            # 股票知识库
│   │   ├── article_writer/            # 股票文章撰写
│   │   └── article_reviewer/          # 股票文章审稿
│   └── jewelry/                       # 珠宝行业
│       └── ...
├── library/                           # 数据层（按处理阶段编号）
│   ├── 00_manifest/                   # 台账（manifest、水位、队列）
│   ├── 01_video/<平台>/<账号>/        # 原片
│   ├── 02_audio/                      # 音频（过程件）
│   ├── 04_transcript/<平台>/          # 逐字转写（原料，不入库）
│   ├── 05_knowledge/                  # OKF知识成品（入库）
│   │   └── concepts/
│   │       ├── videos/                # 视频笔记（VideoNote）
│   │       ├── articles/              # 图文笔记（ArticleNote）
│   │       ├── books/                 # 书籍笔记（BookNote）
│   │       ├── reports/               # 报告笔记（ReportNote）
│   │       ├── methods/               # 方法笔记（MethodNote）
│   │       └── topics/                # 主题融合页
│   ├── 06_articles/<平台>/            # 图文（原料，不入库）
│   ├── 07_books/                      # 书籍
│   └── 08_sources/<source_id>/        # 平台无关外部源
├── docs/                              # 产品与技术文档
│   ├── README.md                      # 文档入口
│   ├── DOCUMENTATION_MAP.md           # 文档地图
│   ├── DIRECTORY_STRUCTURE.md         # 目录结构说明
│   ├── WORKFLOW.md                    # 工作流
│   ├── REQUIREMENTS.md                # 需求与决策溯源
│   ├── ROADMAP.md                     # 路线图
│   ├── SOP-wechat-channels-capture.md
│   ├── SOP-wechat-official-article.md
│   ├── SOP-books-extraction.md
│   ├── RESEARCH-video-quality-url.md
│   ├── RESEARCH-wechat-channels-api.md
│   └── DESIGN-knowledge-base-organization.md
├── project-management/                # 项目治理体系
│   ├── README.md                      # 治理体系入口
│   ├── active/                        # 活态台账
│   │   ├── TASK_STATUS.md             # 任务状态
│   │   └── ISSUES.md                  # 问题清单
│   ├── decisions/                     # ADR决策记录
│   ├── memory/                        # 工程记忆
│   ├── reviews/                       # 评审报告
│   ├── standards/                     # 执行标准
│   └── legacy/                        # 历史项目存档
├── scripts/                           # 运维脚本
│   └── netdisk/                       # 百度网盘同步
├── workspace/                         # 过程件（不入库）
├── .secrets/                          # 凭证（不入库）
└── data/                              # 旧数据（待迁移到library/）
```

## 五层架构

```
① 来源层（平台插件化，开放扩展）
   微信公众号 / 微信视频号 / B站 / 抖音 / YouTube / 其他
              │
② 加工层（公共SOP）
   下载→解密→FunASR转写｜抓正文→图OCR｜书摘｜PDF抽取
              │
③ 原始层（只读·本地留档·不进公有仓）
   library/01_video  02_audio  04_transcript  06_articles  07_books
              │
④ 知识层（清洗后"自己话重组、带来源"的成品，才入库）
   concepts/videos articles books reports methods → topics/ 主题融合
              │
⑤ 应用层（按行业隔离）
   domains/stock/    股票知识库 + 文章撰写 + 审稿
   domains/jewelry/  珠宝知识库 + 文章撰写 + 审稿
```

## 方法提炼（MethodNote）

除了传统的内容知识库，本项目还支持**方法提炼**：

- **场景**：看到一个博主（如抖音广告博主），拍摄技巧、AI使用效果、内容呈现都很新颖
- **目标**：分析视频的表现效果和风格，提炼出可复用的生成方法
- **过程**：可能需要搜索（如搜索某种AI工具的使用方法）
- **目的**：不是进入该行业，而是提炼方法，方便抄袭风格和生成视频
- **输出**：`library/05_knowledge/concepts/methods/` 下的MethodNote

## 存储分工（硬约束）

| 位置 | 内容 |
|------|------|
| Git公有仓 | 清洗后知识成品（05的stable）、代码、docs/、台账元数据；**不放媒体、逐字转写、原文、凭证、过程件** |
| 本地桌面项目 | 原始资源 + 知识成品，**唯一权威源** |
| 百度网盘 | 成品镜像 |
| 飞书 | 暂缓；将来只发成品 |

## 关键技术

- **视频号采集**：MITM代理捕获URL + 解密（详见 `docs/SOP-wechat-channels-capture.md`）
- **转写**：FunASR（SenseVoiceSmall模型，9.7x实时）
- **OCR**：macOS Vision框架（编译二进制，1.5秒/张）
- **增量采集**：水位（watermark）机制，先成功落地再推进水位
- **知识格式**：OKF v0.2（type区分VideoNote/ArticleNote/BookNote/ReportNote/MethodNote）

## 快速开始

```bash
# 查看配置
cat config/sources.json

# 运行所有采集源（框架已搭好，平台插件待完善）
python3 core/pipeline.py

# 增量更新
python3 -c "from core.watermark import WatermarkManager; wm = WatermarkManager(); print(wm.get_all_sources())"
```

## 下一步

按 [docs/ROADMAP.md](docs/ROADMAP.md)：
1. 阶段1完成：架构重构+代码迁移（commit bd45204）
2. 阶段2：数据迁移到library/新结构
3. 阶段3：接入B站采集（复用珠宝项目脚本）
4. 阶段4：接入抖音/YouTube
5. 阶段5：方法提炼LLM深度分析
