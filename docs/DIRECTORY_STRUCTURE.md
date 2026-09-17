# 目录结构详细说明

> **文档类型**：Reference（参考资料）
> **更新频率**：目录结构变更时
> **维护者**：AI自动维护 + 用户审核
> **读者**：AI代理 + 人类
> **最近更新**：2026-09-15（架构重构：从微信生态专用项目重构为多平台通用框架）

本文档说明四类存储的目录结构与分工：**GitHub仓库（工程）、本地数据（library/）、百度网盘（备份）、飞书知识库（成品知识系统）**。

> README.md 只留摘要与链接，详细内容见本文档。

---

## 〇、四地存储分工总表（先看这张）

| 内容 | Git仓库 | 本地library/ | 百度网盘 | 飞书知识库 |
|------|:---:|:---:|:---:|:---:|
| 规范/模板/SOP/脚本/ADR | ✅ 唯一源 | — | — | — |
| 原始资源（视频/转写/文章JSON/图片） | ❌ 忽略 | ✅ | ✅ 备份 | ❌ |
| 知识成品（结构化知识点/文案素材） | 仅stable入库 | ✅ | ✅ 备份 | ✅ 对外知识系统 |
| 加密凭证 `.secrets/*.enc` | 见.gitignore | ✅ | ❌ | ❌ |
| 过程件（workspace/） | ❌ 忽略 | ✅ | ❌ | ❌ |

**一句话**：Git只放"怎么做"的工程资产+清洗后知识成品；"原料"在本地library/，备份网盘；成品知识最终可同步飞书。

---

## 一、项目仓库目录结构（GitHub）

```
multiplatform-content-pipeline/
├── README.md                          # 项目概览（快速导航）
├── AGENTS.md                          # AI操作手册（命令式、可执行）
├── config/
│   └── sources.json                   # 采集源配置（平台→账号→行业映射）
├── platforms/                         # 采集层：平台插件
│   ├── base.py                        # 统一接口（PlatformFetcher）
│   ├── wechat_official/               # 公众号采集
│   │   └── article/                   # 文章采集脚本
│   ├── wechat_channels/               # 视频号采集
│   │   ├── video-capture/             # MITM代理捕获工具（Go）
│   │   ├── video-downloader/          # 下载+解密（Python+Node）
│   │   └── auto-capture/              # 自动化采集（Python）
│   ├── bilibili/                      # B站采集（待接入）
│   ├── douyin/                        # 抖音采集（待接入）
│   └── youtube/                       # YouTube采集（待接入）
├── processing/                        # 处理层：公共SOP
│   ├── transcription/                 # FunASR转写
│   │   └── tools/
│   ├── ocr/                           # Vision OCR
│   │   └── tools/
│   ├── knowledge_extraction/          # 知识提取
│   │   └── tools/
│   ├── method_extraction/             # 方法提炼（拍摄技巧/AI使用/风格）
│   │   └── method_extractor.py
│   └── normalization/                 # 内容标准化/去重
├── core/                              # 核心框架
│   ├── pipeline.py                    # 流水线编排
│   ├── config.py                      # 配置管理
│   └── watermark.py                   # 增量水位机制
├── domains/                           # 行业层（隔离）
│   ├── stock/                         # 股票行业
│   │   ├── knowledge_base/            # 股票知识库
│   │   ├── article_writer/            # 股票文章撰写模板
│   │   └── article_reviewer/          # 股票文章审稿规则
│   └── jewelry/                       # 珠宝行业
│       └── ...
├── library/                           # 数据层（按处理阶段编号）
│   ├── 00_manifest/                   # 台账（manifest、水位、队列）
│   ├── 01_video/<平台>/<账号>/        # 原片（gitignore）
│   ├── 02_audio/                      # 音频（过程件，gitignore）
│   ├── 04_transcript/<平台>/          # 逐字转写（原料，gitignore）
│   ├── 05_knowledge/                  # OKF知识成品（入库）
│   │   └── concepts/
│   │       ├── videos/                # 视频笔记（VideoNote）
│   │       ├── articles/              # 图文笔记（ArticleNote）
│   │       ├── books/                 # 书籍笔记（BookNote）
│   │       ├── reports/               # 报告笔记（ReportNote）
│   │       ├── methods/               # 方法笔记（MethodNote）
│   │       └── topics/                # 主题融合页
│   ├── 06_articles/<平台>/            # 图文原文（原料，gitignore）
│   ├── 07_books/                      # 书籍
│   └── 08_sources/<source_id>/        # 平台无关外部源
├── docs/                              # 工程文档
│   ├── DOCUMENTATION_MAP.md           # 文档地图（先读这个）
│   ├── DIRECTORY_STRUCTURE.md         # 本文档
│   ├── WORKFLOW.md                    # 工作流（五层架构流水线）
│   ├── REQUIREMENTS.md                # 需求与决策溯源
│   ├── ROADMAP.md                     # 路线图
│   ├── SOP-wechat-channels-capture.md
│   ├── SOP-wechat-official-article.md
│   ├── RESEARCH-video-quality-url.md
│   ├── RESEARCH-wechat-channels-api.md
│   ├── DESIGN-knowledge-base-organization.md
│   └── project-management/
│       ├── decisions/                 # ADR决策记录（只增不改）
│       ├── memory/                    # 工程记忆（跨会话稳定结论）
│       └── standards/                 # 规范文档
├── project-management/
│   └── active/
│       ├── TASK_STATUS.md             # 任务状态（单一进度真相）
│       └── ISSUES.md                  # 问题清单
├── scripts/                           # 运维脚本
│   └── netdisk/                       # 百度网盘同步
├── workspace/                         # 过程件（gitignore）
│   ├── logs/                          # 运行日志
│   ├── tmp/                           # 临时文件
│   └── capture/                       # 采集相关
├── .secrets/                          # 凭证（gitignore）
├── data/                              # 旧数据（待迁移到library/）
└── knowledge-base/                    # 旧知识库（待迁移到library/05_knowledge/）
```

---

## 二、五层架构说明

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

### 各层职责

| 层 | 目录 | 职责 | 入库？ |
|----|------|------|:---:|
| ①来源层 | platforms/ | 平台采集插件，实现统一接口 | ✅ |
| ②加工层 | processing/ | 转写、OCR、知识提取、方法提炼 | ✅ |
| ③原始层 | library/01-04,06-08 | 原始资源、逐字转写、原文 | ❌ |
| ④知识层 | library/05_knowledge/ | 清洗后知识成品（仅stable） | ✅ |
| ⑤应用层 | domains/ | 行业知识库、文章撰写、审稿 | ✅ |

---

## 三、平台插件接口规范

所有平台采集插件必须实现 `platforms/base.py` 中的 `PlatformFetcher` 接口：

```python
class PlatformFetcher(ABC):
    @property
    def platform_id(self) -> str: ...      # 如 'wechat_channels'

    @abstractmethod
    def fetch_urls(self, account: str, **kwargs) -> List[ContentItem]: ...

    @abstractmethod
    def download(self, item: ContentItem, output_dir: str, **kwargs) -> str: ...
```

新平台接入只需：
1. 在 `platforms/` 下创建目录
2. 实现 `PlatformFetcher` 接口
3. 在 `config/sources.json` 中添加采集源
4. 主流程无需修改

---

## 四、方法提炼（MethodNote）

除了传统的内容知识库，本项目还支持**方法提炼**：

- **场景**：看到一个博主（如抖音广告博主），拍摄技巧、AI使用效果、内容呈现都很新颖
- **目标**：分析视频的表现效果和风格，提炼出可复用的生成方法
- **输出**：`library/05_knowledge/concepts/methods/` 下的MethodNote
- **维度**：拍摄技巧、AI工具使用、内容结构、视觉风格、音频风格、节奏控制、分步生成方法

---

## 五、增量采集水位机制

参考珠宝项目的水位（watermark）机制：

- 水位文件：`library/00_manifest/watermarks.json`
- 格式：`{"<platform>:<account>": {"videos": {"last_max_created": ..., "known_count": ...}}}`
- 原则：先成功落地、再推进水位（at-least-once，崩溃不丢，重复可去重）
- 工具：`core/watermark.py`

---

## 六、旧数据迁移计划

当前 `data/` 和 `knowledge-base/` 是旧结构，待迁移到 `library/`：

| 旧路径 | 新路径 | 状态 |
|--------|--------|:---:|
| data/videos/短视频/ | library/01_video/stock/交易的游戏/short/ | 待迁移 |
| data/videos/直播回放/ | library/01_video/stock/交易的游戏/live/ | 待迁移 |
| data/transcripts/短视频/ | library/04_transcript/stock/交易的游戏/ | 待迁移 |
| knowledge-base/02-公众号文章/正文/ | library/06_articles/stock/顶底之王/ | 待迁移 |
| knowledge-base/02-公众号文章/图片/ | library/06_articles/stock/顶底之王/images/ | 待迁移 |
| knowledge-base/01-视频号内容/ | library/05_knowledge/concepts/videos/ | 待迁移 |

迁移原则：复制+验证，不是剪切；验证通过后再清理旧目录。

---

## 七、百度网盘结构

```
百度网盘/
└── 多平台内容流水线/
    ├── 股票知识库/                    # 股票行业成品
    │   ├── 视频号内容/
    │   ├── 公众号文章/
    │   └── 知识点/
    └── 珠宝知识库/                    # 珠宝行业成品（待建）
```

同步脚本：`scripts/netdisk/sync_stock.sh`

---

*本文档随项目演进持续更新。目录结构变更时必须同步更新本文档。*
