# 多平台内容流水线（multiplatform-content-pipeline）

> **项目类型**：多平台内容采集 + 知识库生成 + 文稿/视频创作
> **维护者**：AI自动维护 + 用户审核
> **仓库**：`~/Desktop/multiplatform-content-pipeline/` ｜ GitHub `github.com/byte886/multiplatform-content-pipeline`（public，master）

---

## 🚑 新会话快速恢复（先读这里）

**目标：只要知道仓库位置，新窗口不翻旧聊天即可接手。**

1. 新建任务窗口时，项目文件夹选 `~/Desktop/multiplatform-content-pipeline`（不要用 `~/Doubao/chats` 临时目录）。
2. 直接发标准句：

   ```
   接手这个项目，按 AGENTS.md §1.1 冷启动，先把 docs/项目维护SOP.md §5 的冷启动六问答给我听，再等我派活。
   ```

3. 冷启动阅读顺序与**冷启动六问**：见 [`AGENTS.md`](AGENTS.md) §1.1 与 [`docs/项目维护SOP.md`](docs/项目维护SOP.md) §5；
   开窗/交接固定动作见 [`docs/新窗口接手开场白.md`](docs/新窗口接手开场白.md)；
   最近怎么讨论过来的、现在卡在哪见 [`docs/HANDOFF.md`](docs/HANDOFF.md)。
4. 提交前必跑体检（0 ERROR 才提交）：`python3 scripts/doc_health_check.py`。

---

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

| 平台 | 状态 | 说明（采集量为易变数字，统一以 `library/00_manifest/` 台账与 TASK_STATUS 为准，此处不写死） |
|------|------|---------|
| 微信视频号 | ✅ 已端到端跑通 | Pinia action 直枚举全量，一键 `collect_channels.py`（人工只开一次窗）；「交易的游戏」已全量下载+转写+台账对账（具体数以 `library/00_manifest/` 台账为准） |
| 微信公众号 | 🔧 全量方案待实测 | 本地库仅得最近几篇；HTTP `getmsg` 方案待人工激活一次凭证后跑通 |
| B站 | ✅ 已接入（珠宝源） | 采集量以台账为准；subprocess 环境走代理会 412，须直连 |
| 抖音 | ⏸ 暂缓 | 网页反爬 403，指定博主任务待用户手动提供视频 |
| YouTube | 🔧 待接入 | 复用 multiplatform-media-fetch，需代理 |

---

## 快速导航

| 文档 | 用途 |
|------|------|
| [AGENTS.md](AGENTS.md) | AI操作手册（命令式、可执行，含冷启动恢复顺序） |
| [docs/新窗口接手开场白.md](docs/新窗口接手开场白.md) | **开新窗口固定 SOP + 标准句** |
| [docs/项目维护SOP.md](docs/项目维护SOP.md) | 单一真相源路由、维护节奏、冷启动六问、提交前体检 |
| [docs/HANDOFF.md](docs/HANDOFF.md) | 活的项目日志（倒序）+ 当前纠结 |
| [docs/DOCUMENTATION_MAP.md](docs/DOCUMENTATION_MAP.md) | **文档地图**（所有文档的快速入口） |
| [docs/WORKFLOW.md](docs/WORKFLOW.md) | 整体工作流（四阶段流水线） |
| [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) | 项目需求与功能范围 |
| [docs/ROADMAP.md](docs/ROADMAP.md) | 项目长期规划 |
| [docs/guides/codex-dev-environment.md](docs/guides/codex-dev-environment.md) | **Codex 环境、模型选型(GPT-5.6 Sol)、算力购买与操作步骤** |
| [project-management/active/TASK_STATUS.md](project-management/active/TASK_STATUS.md) | 当前进度、下一步（单一进度真相） |

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
# 文档体检（提交前必跑，0 ERROR）
python3 scripts/doc_health_check.py

# 查看采集源配置
cat config/sources.json

# 视频号一键采集（人工只在微信搜索→点「视频号」行进入主页，约15秒；其余全自动）
# 首次=全量，之后=只下新增；自动完成 捕获→解密→转写→台账→对账
python3 platforms/wechat_channels/collect_channels.py "交易的游戏" --domain stock --quality min
# 一步一步 SOP：docs/guides/wechat-channels-collect-sop.md

# 运行增量采集（dry-run，多平台调度）
python3 scripts/incremental/fetch_new.py --all --dry-run
```

---

*详细说明见各专项文档，本README只保留概览。*
