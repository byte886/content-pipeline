# 目录结构详细说明

> **文档类型**：Reference（参考资料）
> **更新频率**：目录结构变更时
> **维护者**：AI自动维护 + 用户审核
> **读者**：AI代理 + 人类

本文档说明四类存储的目录结构与分工：**GitHub仓库（工程）、本地数据（data）、百度网盘（备份）、飞书知识库（成品知识系统）**。

> README.md 只留摘要与链接，详细内容见本文档。

---

## 〇、四地存储分工总表（先看这张）

| 内容 | Git仓库 | 本地data | 百度网盘 | 飞书知识库 |
|------|:---:|:---:|:---:|:---:|
| 规范/模板/SOP/脚本/ADR | ✅ 唯一源 | — | — | — |
| 原始资源（视频/转写/文章JSON/图片） | ❌ 忽略 | ✅ | ✅ 备份 | ❌ |
| 知识成品（结构化知识点/文案素材） | 部分入库 | ✅ | ✅ 备份 | ✅ 对外知识系统 |
| 加密凭证 `.secrets/*.enc` | 见.gitignore | ✅ | ❌ | ❌ |

**一句话**：Git只放"怎么做"的工程资产；"原料+成品"在本地data，备份网盘；成品知识最终可同步飞书。

---

## 一、项目仓库目录结构（GitHub，只放工程）

```
stock-knowledge-base/
├── docs/                              # 工程文档
│   ├── DOCUMENTATION_MAP.md           # 文档地图（先读这个）
│   ├── DIRECTORY_STRUCTURE.md         # 本文档
│   ├── WORKFLOW.md                    # 主工作流（待创建）
│   ├── PRD.md                         # 产品需求
│   ├── ROADMAP.md                     # 路线图与当前状态
│   ├── 技术方案.md
│   ├── 执行计划.md
│   ├── 视频号内容采集SOP.md
│   ├── 公众号文章采集SOP.md
│   ├── 高质量URL研究.md
│   ├── 视频号API研究.md
│   ├── 知识库组织方案.md
│   ├── 知识库规范.md
│   └── project-management/
│       ├── decisions/                 # ADR架构决策记录（只增不改）
│       └── memory/                    # 工程记忆（跨会话稳定结论）
├── project-management/
│   └── active/                        # 活跃任务台账
│       ├── TASK_STATUS.md             # 当前进度、下一步
│       └── ISSUES.md                  # 已知问题、阻塞项
├── tools/                             # 工具脚本（按功能分目录）
│   ├── video-capture/                 # 视频捕获（MITM代理）
│   ├── video-downloader/              # 视频下载+解密
│   ├── auto-capture/                  # 自动化采集
│   ├── transcription/                 # 视频转文字（FunASR）
│   ├── ocr/                           # 图文OCR（macOS Vision）
│   └── knowledge-extraction/          # 知识提取与查询
├── scripts/                           # 其他脚本（待整理迁移）
│   ├── article/                       # 文章采集（待迁移到tools/）
│   └── netdisk/                       # 百度网盘同步
├── config/                            # 配置文件
├── .secrets/                          # 加密凭证（*.enc；*.json忽略）
├── data/                              # 本地运行数据，整体gitignore
│   ├── videos/                        # 视频原始文件
│   │   ├── 短视频/
│   │   └── 直播回放/
│   └── transcripts/                   # 转写稿
│       └── 短视频/{视频名}/transcript.md
├── knowledge-base/                    # 知识库成品（部分入库）
│   ├── 01-视频号内容/
│   ├── 02-公众号文章/
│   │   ├── 正文/                      # 文章JSON（含image_ocr）
│   │   └── 图片/                      # 文章图片+映射
│   ├── 03-书籍精华/
│   ├── 04-知识点图谱/
│   └── 05-文案素材库/
└── README.md / AGENTS.md / .gitignore
```

---

## 二、本地运行数据（data，整体gitignore）

```
data/
├── videos/
│   ├── 短视频/        # 313个短视频（mp4，已解密）
│   └── 直播回放/      # 23个直播回放（mp4，无需解密）
├── transcripts/
│   └── 短视频/        # 313个转写稿
│       └── {视频名}/
│           └── transcript.md
├── 股票知识库/        # 旧目录结构（待迁移）
├── articles/          # 旧目录结构（待迁移）
└── _workspace/        # 运行时工作区（过程件，不入库不传网盘）
    ├── logs/          # 运行日志
    ├── tmp/           # 临时文件（用完即清）
    └── capture/       # 采集相关（抓包数据、URL清单、批次状态）
```

**注意**：
- 转写稿是子目录格式（`{视频名}/transcript.md`），不是直接的md文件
- `_workspace/`是过程件存放位置，详见`data/_workspace/README.md`
- 旧目录`股票知识库/`和`articles/`待迁移到统一结构

---

## 三、知识库成品（knowledge-base/）

```
knowledge-base/
├── 01-视频号内容/          # 视频号相关知识
├── 02-公众号文章/
│   ├── 正文/               # 277篇文章JSON（236篇含image_ocr）
│   ├── 图片/               # 910张图片 + image_url_mapping.json
│   ├── 个股点评/
│   ├── 投资理念/
│   └── 板块研究/
├── 03-书籍精华/            # 推荐书籍的精华整理
├── 04-知识点图谱/          # 结构化知识点
│   ├── 交易策略库/
│   ├── 宏观经济/
│   ├── 技术指标库/
│   └── 财务指标库/
└── 05-文案素材库/          # 内容创作素材
    ├── 公众号文案/
    ├── 直播大纲/
    └── 短视频脚本/
```

---

## 四、工具目录说明

### tools/video-capture/（视频捕获）
- `captor.go` — 核心捕获逻辑（MITM代理+JS注入+URL保存+API日志）
- `main.go` — 入口（参数解析、代理健康检查）
- `proxy_darwin.go` — macOS系统代理设置/清除
- `video-capture` — 编译后二进制
- `ca.crt` / `ca.key` — CA证书（已信任，**必须在此目录运行**）
- `start-capture.sh` — 启动脚本

### tools/video-downloader/（视频下载）
- `batch_download_v4.py` — 批量下载（支持quality=default/max/min+自动解密+验证+去重）
- `wechat_decrypt.js` — 视频解密脚本
- `decrypt_node.js` — RES Downloader的decrypt.js（5.2MB WASM）
- `batch_decrypt.js` — 批量解密脚本

### tools/transcription/（转写）
- `batch_transcribe.py` — 批量视频转文字（FunASR本地离线）

### tools/ocr/（OCR）
- `batch_article_images.py` — 公众号图片批量下载+OCR
- `batch_ocr.py` — 通用批量OCR

### tools/knowledge-extraction/（知识提取）
- `extract_knowledge.py` — 基于规则的知识提取
- `knowledge_base.py` — 知识库汇总与查询

---

## 五、命名规范

- 目录：中文语义命名（短视频、直播回放、公众号文章）
- 脚本：snake_case（batch_download_v4.py）
- 文档：中文语义命名（视频号内容采集SOP.md）
- 视频文件：`{序号}_{标题}.mp4`（如 `001_A股快到支撑了.mp4`）
- 转写稿：`{视频名}/transcript.md`（子目录格式）

---

*本文档随项目演进持续更新。目录结构变更时必须同步更新本文档。*
