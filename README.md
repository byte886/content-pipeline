# A股投资知识库

> **项目类型**：知识库建设 + 自动化采集
> **创建时间**：2026-09-11
> **维护者**：AI自动维护 + 用户审核

## 项目目标

构建A股投资知识库，自动化采集公众号「顶底之王」和关联视频号「交易的游戏」的全部内容，为后续量化系统和内容生成提供数据基础。

## 目标账号

| 平台 | 名称 | 认证 | 说明 |
|------|------|------|------|
| 公众号 | 顶底之王 | - | 图文文章 |
| 视频号 | 交易的游戏 | 证券投资顾问（刘广义，执业编号A0630624060004） | 短视频 + 直播回放 |

## 快速导航（AI和人都先看这里）

| 文档 | 用途 |
|------|------|
| [AGENTS.md](AGENTS.md) | AI操作手册（命令式、可执行） |
| [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) | 项目需求与决策溯源 |
| [docs/WORKFLOW.md](docs/WORKFLOW.md) | 整体工作流（四阶段流水线） |
| [docs/DOCUMENTATION_MAP.md](docs/DOCUMENTATION_MAP.md) | **文档地图**（所有文档的快速入口） |
| [docs/DIRECTORY_STRUCTURE.md](docs/DIRECTORY_STRUCTURE.md) | 目录结构与存储分工 |
| [project-management/active/TASK_STATUS.md](project-management/active/TASK_STATUS.md) | 当前进度、下一步 |
| [project-management/active/ISSUES.md](project-management/active/ISSUES.md) | 已知问题、阻塞项 |
| [docs/ROADMAP.md](docs/ROADMAP.md) | 项目路线图 |

## 项目结构

```
stock-knowledge-base/
├── README.md                          # 项目概览（本文档）
├── AGENTS.md                          # AI操作手册
├── docs/                              # 工程文档
│   ├── DOCUMENTATION_MAP.md           # 文档地图（先读这个）
│   ├── DIRECTORY_STRUCTURE.md         # 目录结构说明
│   ├── PRD.md / 技术方案.md / 执行计划.md
│   ├── ROADMAP.md                     # 路线图
│   ├── 视频号内容采集SOP.md
│   ├── 公众号文章采集SOP.md
│   ├── 高质量URL研究.md
│   ├── 视频号API研究.md
│   ├── 知识库组织方案.md / 知识库规范.md
│   └── project-management/
│       ├── decisions/                 # ADR决策记录（只增不改）
│       └── memory/                    # 工程记忆（跨会话稳定结论）
├── project-management/
│   └── active/                        # 活跃任务台账（动态）
│       ├── TASK_STATUS.md             # 当前进度
│       └── ISSUES.md                  # 已知问题
├── tools/                             # 工具脚本（按功能分目录）
│   ├── video-capture/                 # 视频捕获（MITM代理）
│   ├── video-downloader/              # 视频下载+解密
│   ├── auto-capture/                  # 自动化采集
│   ├── transcription/                 # 视频转文字（FunASR）
│   ├── ocr/                           # 图文OCR（macOS Vision）
│   └── knowledge-extraction/          # 知识提取与查询
├── scripts/                           # 其他脚本（待整理迁移）
├── data/                              # 本地运行数据（gitignore）
│   ├── videos/                        # 视频原始文件
│   └── transcripts/                   # 转写稿
└── knowledge-base/                    # 知识库成品
    ├── 01-视频号内容/
    ├── 02-公众号文章/
    ├── 03-书籍精华/
    ├── 04-知识点图谱/
    └── 05-文案素材库/
```

## 核心技术

### 视频采集
- **代理捕获**：MITM代理 + JS注入Hook，捕获视频号视频URL
- **自动代理**：启动时自动设置系统代理（所有活动网络服务），退出时自动清除
- **上游代理**：支持ClashX上游代理，国内直连/国外自动VPN
- **视频解密**：ISAAC64伪随机数生成器 + XOR解密（前128KB）
- **批量下载**：支持短视频（需解密）和直播回放（无需解密）
- **高质量URL**：X-snsvideoflag=xWT111（比默认大69%）

### 文章采集
- 微信本地数据库读取
- 公众号文章正文提取
- 图片OCR（macOS Vision，编译二进制提速10倍）

### 知识处理
- **视频转文字**：FunASR本地离线转写（9.7x实时）
- **图文OCR**：macOS Vision框架
- **知识提取**：基于规则的市场观点/技术点位/板块机会提取

## 数据统计（截至2026-09-15）

| 类型 | 数量 | 状态 |
|------|------|------|
| 短视频 | 313个 | ✅ 已下载 + 已转写 |
| 直播回放 | 23个 | ✅ 已下载，⏳ 待转写 |
| 公众号文章 | 277篇 | ✅ 已下载（275篇有正文，910张图片已OCR） |

## 快速开始

### 捕获视频URL
```bash
# 可以从任意目录运行（证书路径已修复为相对于可执行文件）
./tools/video-capture/video-capture -port 8899 -output videos.json
# 在微信中打开视频号，滚动列表
# Ctrl+C 停止（自动清除代理）
```

### 下载视频
```bash
# 短视频（自动解密）
python3 tools/video-downloader/batch_download_v4.py videos.json output/ short 1

# 直播回放
python3 tools/video-downloader/batch_download_v4.py live.json output/ live 1
```

### 视频转文字
```bash
python3 tools/transcription/batch_transcribe.py data/videos/短视频 data/transcripts/短视频
```

### 图文OCR
```bash
python3 tools/ocr/batch_article_images.py
```

## 存储分工

| 位置 | 内容 | 说明 |
|------|------|------|
| GitHub仓库 | 代码+文档 | 禁止放视频等大文件 |
| 本地 data/ | 视频、转写稿 | 主存储 |
| 本地 knowledge-base/ | 结构化知识 | 部分入库 |
| U盘 | 视频存档 | 备份 |
| 百度网盘 | 与本地镜像 | 跨设备访问 |

## 后续计划

- [ ] 直播回放23个转写
- [ ] 知识提取批量运行
- [ ] 增量采集机制完善
- [ ] 知识库汇总生成
- [ ] 高质量URL原始版本（48.5MB）继续研究
- [ ] 知识提取接入LLM深度提取
- [ ] 量化系统对接
- [ ] 内容创作工具（公众号文案/短视频脚本生成）

## 相关文档

- [视频号内容采集SOP](docs/视频号内容采集SOP.md)
- [公众号文章采集SOP](docs/公众号文章采集SOP.md)
- [高质量URL研究](docs/高质量URL研究.md)
- [视频号API研究](docs/视频号API研究.md)
- [知识库组织方案](docs/知识库组织方案.md)
